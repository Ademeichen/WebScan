import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from vulnerability_scan_plugins.base import BaseScanner
from vulnerability_scan_plugins.manager import PluginManager


@pytest.fixture
def plugin_manager():
    return PluginManager()


@pytest.fixture
def sample_target():
    return {
        "url": "http://testphp.vulnweb.com",
        "method": "GET",
        "params": {},
        "headers": {}
    }


@pytest.fixture
def sample_target_with_params():
    return {
        "url": "http://testphp.vulnweb.com/search.php",
        "method": "POST",
        "params": {"id": "1", "name": "test"},
        "headers": {"Content-Type": "application/x-www-form-urlencoded"}
    }
