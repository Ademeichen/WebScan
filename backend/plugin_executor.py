import os
import sys
import time
import json
import logging
import threading
import requests
import traceback
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

# Try to import Kafka
try:
    from kafka import KafkaProducer
except ImportError:
    KafkaProducer = None

# Import Plugins
from backend.plugins.portscan.portscan import ScanPort
from backend.plugins.infoleak.infoleak import get_infoleak
from backend.plugins.webside.webside import get_side_info
from backend.plugins.baseinfo.baseinfo import getbaseinfo
from backend.plugins.webweight.webweight import get_web_weight
from backend.plugins.iplocating.iplocating import get_locating
from backend.plugins.cdnexist.cdnexist import iscdn
from backend.plugins.waf.waf import getwaf
from backend.plugins.whatcms.whatcms import getwhatcms
from backend.plugins.subdomain.subdomain import get_subdomain

try:
    from dirsearcch.dir_scanner import DirScanner
except ImportError:
    DirScanner = None

# Import POCs
from backend.poc.weblogic.cve_2020_2551_poc import poc as cve_2020_2551_poc
from backend.poc.weblogic.cve_2018_2628_poc import poc as cve_2018_2628_poc
from backend.poc.weblogic.cve_2018_2894_poc import poc as cve_2018_2894_poc
from backend.poc.struts2.struts2_009_poc import poc as struts2_009_poc
from backend.poc.struts2.struts2_032_poc import poc as struts2_032_poc
from backend.poc.tomcat.cve_2017_12615_poc import poc as cve_2017_12615_poc
from backend.poc.jboss.cve_2017_12149_poc import poc as cve_2017_12149_poc
from backend.poc.nexus.cve_2020_10199_poc import poc as cve_2020_10199_poc
from backend.poc.Drupal.cve_2018_7600_poc import poc as cve_2018_7600_poc

POC_FUNCTIONS = {
    "weblogic_cve_2020_2551": cve_2020_2551_poc,
    "weblogic_cve_2018_2628": cve_2018_2628_poc,
    "weblogic_cve_2018_2894": cve_2018_2894_poc,
    "struts2_009": struts2_009_poc,
    "struts2_032": struts2_032_poc,
    "tomcat_cve_2017_12615": cve_2017_12615_poc,
    "jboss_cve_2017_12149": cve_2017_12149_poc,
    "nexus_cve_2020_10199": cve_2020_10199_poc,
    "drupal_cve_2018_7600": cve_2018_7600_poc,
}

class PluginLogHandler(logging.Handler):
    def __init__(self, plugin_type, plugin_name, task_id, kafka_producer=None, kafka_topic=None):
        super().__init__()
        self.plugin_type = plugin_type
        self.plugin_name = plugin_name
        self.task_id = task_id
        self.kafka_producer = kafka_producer
        self.kafka_topic = kafka_topic
        self.formatter = logging.Formatter(
            '[Plugin][%(plugin_type)s][%(plugin_name)s][%(task_id)s] %(levelname)s %(message)s'
        )

    def emit(self, record):
        record.plugin_type = self.plugin_type
        record.plugin_name = self.plugin_name
        record.task_id = self.task_id
        
        msg = self.format(record)
        
        # Write to Kafka if available
        if self.kafka_producer and self.kafka_topic:
            try:
                self.kafka_producer.send(self.kafka_topic, msg.encode('utf-8'))
            except Exception:
                pass # Fail silently for Kafka

class PluginExecutor:
    def __init__(self, task_id: int, task_type: str, target: str, config: Dict, agent_url: str):
        self.task_id = task_id
        self.task_type = task_type
        self.target = target
        self.config = config
        self.agent_url = agent_url.rstrip('/')
        self.plugin_name = self._get_plugin_name()
        
        self.stop_event = threading.Event()
        self.logger = None
        self.kafka_producer = None

    def _get_plugin_name(self):
        # Infer plugin name from type or config
        if self.task_type == 'port_scan': return 'PortScan'
        if self.task_type == 'dir_scan': return 'DirScan'
        return self.task_type

    def setup_logging(self):
        # 2.2 Log to local file
        log_dir = Path(f"logs/plugins/{datetime.now().strftime('%Y-%m-%d')}")
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / f"{self.task_id}.log"
        
        # 2.2 Kafka
        try:
            if KafkaProducer:
                self.kafka_producer = KafkaProducer(
                    bootstrap_servers=['localhost:9092'], # Assume localhost for now or env
                    value_serializer=lambda x: x
                )
        except Exception as e:
            print(f"Warning: Kafka setup failed: {e}")

        self.logger = logging.getLogger(f"plugin_{self.task_id}")
        self.logger.setLevel(logging.DEBUG)
        
        # File Handler
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(logging.Formatter(
            '[Plugin][%(plugin_type)s][%(plugin_name)s][%(task_id)s] %(levelname)s %(message)s'
        ))
        # Custom context injection for formatter
        # Actually easier to just use the custom handler for everything or formatting directly
        
        # Using the custom handler for format consistency and Kafka
        plugin_handler = PluginLogHandler(
            self.task_type, self.plugin_name, self.task_id,
            self.kafka_producer, "agent.plugin.log"
        )
        plugin_handler.setFormatter(logging.Formatter(
            '[Plugin][%(plugin_type)s][%(plugin_name)s][%(task_id)s] %(levelname)s %(message)s'
        ))
        
        self.logger.addHandler(file_handler) # Keep file handler simple or use custom?
        # Let's use custom handler for Kafka and File handler for File, but ensure format matches
        
        # To ensure the format matches Requirement 2.1 exactly in file too:
        # We need to inject the extra fields into the record or use an adapter.
        
        self.logger = logging.LoggerAdapter(self.logger, {
            'plugin_type': self.task_type,
            'plugin_name': self.plugin_name,
            'task_id': self.task_id
        })
        
        # Reset handlers to avoid duplication if re-initialized (unlikely in process)
        self.logger.logger.handlers = []
        self.logger.logger.addHandler(file_handler)
        self.logger.logger.addHandler(plugin_handler)

    def heartbeat_loop(self):
        """4.2 Periodic Heartbeat"""
        while not self.stop_event.is_set():
            try:
                url = f"{self.agent_url}/agent/task/{self.task_id}/plugin/{self.task_type}/heartbeat"
                requests.put(url, json={"timestamp": time.time()})
            except Exception as e:
                # self.logger.warning(f"Heartbeat failed: {e}")
                pass
            time.sleep(30)

    def run(self):
        self.setup_logging()
        self.logger.info("Plugin started")
        
        # Start heartbeat thread
        hb_thread = threading.Thread(target=self.heartbeat_loop, daemon=True)
        hb_thread.start()
        
        result = {}
        error = None
        exit_code = 0
        
        try:
            result = self._execute_logic()
            self.logger.info("Plugin finished successfully")
        except Exception as e:
            error = str(e)
            exit_code = 1
            self.logger.error(f"Plugin execution failed: {e}")
            self.logger.error(traceback.format_exc())
            result = {"error": error}
        finally:
            self.stop_event.set()
            # 3.2 Callback Finish
            self._report_finish(exit_code, result, error)

    def _execute_logic(self):
        task_type = self.task_type
        target = self.target
        scan_config = self.config
        
        if task_type == 'port_scan':
            ports = scan_config.get('ports', None)
            scanner = ScanPort(target, ports)
            return scanner.scan()
        elif task_type == 'dir_scan':
            if DirScanner:
                scanner = DirScanner(target, scan_config)
                return scanner.scan()
            else:
                raise ImportError('DirScanner not available')
        elif task_type == 'info_leak':
            return get_infoleak(target)
        elif task_type == 'web_side':
            return get_side_info(target)
        elif task_type == 'base_info':
            return getbaseinfo(target)
        elif task_type == 'web_weight':
            return get_web_weight(target)
        elif task_type == 'ip_locating':
            return get_locating(target)
        elif task_type == 'cdn_check':
            return {'is_cdn': iscdn(target)}
        elif task_type == 'waf_check':
            return {'waf': getwaf(target)}
        elif task_type == 'whatcms':
            return getwhatcms(target)
        elif task_type == 'subdomain':
            return get_subdomain(target)
        # POCs
        elif task_type in POC_FUNCTIONS:
            return POC_FUNCTIONS[task_type](target)
        
        return {"error": f"Unknown task type: {task_type}"}

    def _report_finish(self, exit_code, result, error):
        try:
            url = f"{self.agent_url}/agent/task/{self.task_id}/plugin/{self.task_type}/finish"
            requests.post(url, json={
                "exitCode": exit_code,
                "stdout": json.dumps(result),
                "stderr": error or ""
            })
        except Exception as e:
            self.logger.error(f"Failed to report finish: {e}")

def run_plugin_process(task_id, task_type, target, config, agent_url):
    """Entry point for the separate process"""
    executor = PluginExecutor(task_id, task_type, target, config, agent_url)
    executor.run()
