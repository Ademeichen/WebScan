/**
 * AI Agent 工作流测试脚本
 * 
 * 功能：
 * 1. 建立与后端API的连接，正确调用AI Agent服务接口
 * 2. 触发完整的AI Agent工作流程
 * 3. 实现Agent调用机制，包括工具调用、决策过程和结果处理
 * 4. 详细打印工作流中每个节点的调用结果
 * 5. 记录并输出每个节点的执行信息
 * 6. 触发安全漏洞扫描功能
 * 7. 完整打印安全漏洞扫描测试的详细数据结果
 */

// 配置
const CONFIG = {
    BASE_URL: 'http://127.0.0.1:3000',
    API_PREFIX: '/api',
    TIMEOUT: 300000, // 5分钟超时
    POLL_INTERVAL: 2000, // 轮询间隔2秒
    MAX_POLL_COUNT: 150 // 最大轮询次数
};

// 颜色输出
const COLORS = {
    RESET: '\x1b[0m',
    RED: '\x1b[31m',
    GREEN: '\x1b[32m',
    YELLOW: '\x1b[33m',
    BLUE: '\x1b[34m',
    MAGENTA: '\x1b[35m',
    CYAN: '\x1b[36m',
    WHITE: '\x1b[37m'
};

/**
 * 日志工具类
 */
class Logger {
    static info(message, data = null) {
        console.log(`${COLORS.BLUE}[INFO]${COLORS.RESET} ${message}`);
        if (data) {
            console.log(JSON.stringify(data, null, 2));
        }
    }

    static success(message, data = null) {
        console.log(`${COLORS.GREEN}[SUCCESS]${COLORS.RESET} ${message}`);
        if (data) {
            console.log(JSON.stringify(data, null, 2));
        }
    }

    static warning(message, data = null) {
        console.log(`${COLORS.YELLOW}[WARNING]${COLORS.RESET} ${message}`);
        if (data) {
            console.log(JSON.stringify(data, null, 2));
        }
    }

    static error(message, data = null) {
        console.log(`${COLORS.RED}[ERROR]${COLORS.RESET} ${message}`);
        if (data) {
            console.log(JSON.stringify(data, null, 2));
        }
    }

    static node(nodeName, status, data = null) {
        const statusColor = status === 'success' ? COLORS.GREEN : 
                           status === 'running' ? COLORS.YELLOW : COLORS.RED;
        console.log(`\n${COLORS.CYAN}════════════════════════════════════════${COLORS.RESET}`);
        console.log(`${COLORS.MAGENTA}[NODE]${COLORS.RESET} ${nodeName} - ${statusColor}${status}${COLORS.RESET}`);
        if (data) {
            console.log(JSON.stringify(data, null, 2));
        }
        console.log(`${COLORS.CYAN}════════════════════════════════════════${COLORS.RESET}\n`);
    }

    static divider(title) {
        console.log(`\n${COLORS.CYAN}════════════════════════════════════════${COLORS.RESET}`);
        console.log(`${COLORS.WHITE}  ${title}${COLORS.RESET}`);
        console.log(`${COLORS.CYAN}════════════════════════════════════════${COLORS.RESET}\n`);
    }
}

/**
 * API客户端类
 */
class APIClient {
    constructor(baseUrl) {
        this.baseUrl = baseUrl;
    }

    /**
     * 发送HTTP请求
     */
    async request(method, endpoint, data = null, timeout = CONFIG.TIMEOUT) {
        const url = `${this.baseUrl}${endpoint}`;
        const startTime = Date.now();
        
        const options = {
            method: method,
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
        };

        if (data && (method === 'POST' || method === 'PUT' || method === 'PATCH')) {
            options.body = JSON.stringify(data);
        }

        try {
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), timeout);
            options.signal = controller.signal;

            const response = await fetch(url, options);
            clearTimeout(timeoutId);

            const endTime = Date.now();
            const duration = endTime - startTime;

            const result = await response.json();

            return {
                success: response.ok,
                status: response.status,
                duration: duration,
                data: result
            };
        } catch (error) {
            const endTime = Date.now();
            const duration = endTime - startTime;

            return {
                success: false,
                status: 0,
                duration: duration,
                error: error.message
            };
        }
    }

    /**
     * GET请求
     */
    async get(endpoint) {
        return this.request('GET', endpoint);
    }

    /**
     * POST请求
     */
    async post(endpoint, data) {
        return this.request('POST', endpoint, data);
    }

    /**
     * DELETE请求
     */
    async delete(endpoint) {
        return this.request('DELETE', endpoint);
    }
}

/**
 * AI Agent 工作流测试器
 */
class AIAgentWorkflowTester {
    constructor() {
        this.client = new APIClient(CONFIG.BASE_URL);
        this.taskId = null;
        this.testResults = {
            startTime: null,
            endTime: null,
            nodes: [],
            vulnerabilities: [],
            errors: []
        };
    }

    /**
     * 运行完整测试
     */
    async runFullTest(target) {
        Logger.divider('AI Agent 工作流测试开始');
        this.testResults.startTime = new Date().toISOString();
        
        console.log(`测试目标: ${target}`);
        console.log(`API地址: ${CONFIG.BASE_URL}`);
        console.log(`超时时间: ${CONFIG.TIMEOUT}ms`);

        try {
            // 1. 检查API连接
            await this.testAPIConnection();

            // 2. 获取可用工具列表
            await this.testGetTools();

            // 3. 启动Agent扫描
            const scanStarted = await this.testStartScan(target);
            if (!scanStarted) {
                throw new Error('启动扫描失败');
            }

            // 4. 轮询任务状态
            await this.pollTaskStatus();

            // 5. 获取详细结果
            await this.testGetTaskDetails();

            // 6. 打印漏洞扫描结果
            this.printVulnerabilityResults();

            this.testResults.endTime = new Date().toISOString();
            this.printSummary();

        } catch (error) {
            Logger.error('测试执行失败', {
                error: error.message,
                stack: error.stack
            });
            this.testResults.errors.push({
                stage: 'test_execution',
                error: error.message,
                timestamp: new Date().toISOString()
            });
        }
    }

    /**
     * 测试API连接
     */
    async testAPIConnection() {
        Logger.divider('步骤1: 测试API连接');
        
        const result = await this.client.get('/api/health');
        
        if (result.success) {
            Logger.success('API连接成功', {
                status: result.status,
                duration: `${result.duration}ms`
            });
            return true;
        } else {
            Logger.warning('API连接检查（可能无health端点），继续测试...');
            return true; // 继续测试，因为可能没有health端点
        }
    }

    /**
     * 测试获取工具列表
     */
    async testGetTools() {
        Logger.divider('步骤2: 获取可用工具列表');
        
        const result = await this.client.get('/api/ai_agents/tools');
        
        if (result.success) {
            Logger.success('获取工具列表成功', {
                status: result.status,
                duration: `${result.duration}ms`,
                tools: result.data
            });
            
            this.testResults.tools = result.data;
            return true;
        } else {
            Logger.error('获取工具列表失败', {
                status: result.status,
                error: result.error || result.data
            });
            return false;
        }
    }

    /**
     * 测试启动扫描
     */
    async testStartScan(target) {
        Logger.divider('步骤3: 启动AI Agent扫描');
        
        const requestData = {
            target: target,
            enable_llm_planning: true
        };

        Logger.info('发送扫描请求', requestData);

        const result = await this.client.post('/api/ai_agents/scan', requestData);
        
        if (result.success && result.data.task_id) {
            this.taskId = result.data.task_id;
            
            Logger.success('扫描任务启动成功', {
                status: result.status,
                duration: `${result.duration}ms`,
                taskId: this.taskId,
                message: result.data.message
            });

            this.testResults.nodes.push({
                node: 'scan_start',
                status: 'success',
                startTime: new Date().toISOString(),
                duration: result.duration,
                input: requestData,
                output: result.data
            });

            return true;
        } else {
            Logger.error('启动扫描失败', {
                status: result.status,
                error: result.error || result.data
            });

            this.testResults.errors.push({
                stage: 'start_scan',
                error: result.error || result.data,
                timestamp: new Date().toISOString()
            });

            return false;
        }
    }

    /**
     * 轮询任务状态
     */
    async pollTaskStatus() {
        Logger.divider('步骤4: 轮询任务状态');
        
        if (!this.taskId) {
            throw new Error('任务ID不存在');
        }

        let pollCount = 0;
        let lastStatus = '';

        while (pollCount < CONFIG.MAX_POLL_COUNT) {
            pollCount++;
            
            const result = await this.client.get(`/api/ai_agents/tasks/${this.taskId}`);
            
            if (result.success) {
                const taskData = result.data;
                const currentStatus = taskData.status;

                // 只在状态变化时打印
                if (currentStatus !== lastStatus) {
                    Logger.info(`任务状态更新 [轮询 #${pollCount}]`, {
                        status: currentStatus,
                        progress: taskData.progress || 'N/A',
                        current_stage: taskData.current_stage || 'N/A'
                    });
                    lastStatus = currentStatus;
                }

                // 打印节点执行信息
                if (taskData.execution_history) {
                    this.processExecutionHistory(taskData.execution_history);
                }

                // 检查是否完成
                if (currentStatus === 'completed' || currentStatus === 'failed') {
                    Logger.success(`任务${currentStatus === 'completed' ? '完成' : '失败'}`, {
                        status: currentStatus,
                        duration: `${pollCount * CONFIG.POLL_INTERVAL / 1000}秒`
                    });
                    return currentStatus === 'completed';
                }
            } else {
                Logger.warning(`轮询失败 [轮询 #${pollCount}]`, {
                    error: result.error || result.data
                });
            }

            // 等待下次轮询
            await this.sleep(CONFIG.POLL_INTERVAL);
        }

        Logger.error('轮询超时', {
            maxPollCount: CONFIG.MAX_POLL_COUNT,
            totalDuration: `${CONFIG.MAX_POLL_COUNT * CONFIG.POLL_INTERVAL / 1000}秒`
        });

        return false;
    }

    /**
     * 处理执行历史
     */
    processExecutionHistory(history) {
        if (!Array.isArray(history)) return;

        history.forEach((step, index) => {
            const existingNode = this.testResults.nodes.find(
                n => n.node === step.step_name && n.startTime === step.start_time
            );

            if (!existingNode) {
                Logger.node(step.step_name, step.status || 'completed', {
                    index: index + 1,
                    startTime: step.start_time,
                    endTime: step.end_time,
                    duration: step.duration ? `${step.duration}ms` : 'N/A',
                    status: step.status,
                    input: step.input_params,
                    output: step.output_data,
                    processingLogic: step.processing_logic
                });

                this.testResults.nodes.push({
                    node: step.step_name,
                    status: step.status,
                    startTime: step.start_time,
                    endTime: step.end_time,
                    duration: step.duration,
                    input: step.input_params,
                    output: step.output_data,
                    processingLogic: step.processing_logic
                });
            }
        });
    }

    /**
     * 获取任务详情
     */
    async testGetTaskDetails() {
        Logger.divider('步骤5: 获取任务详细结果');
        
        if (!this.taskId) {
            throw new Error('任务ID不存在');
        }

        const result = await this.client.get(`/api/ai_agents/tasks/${this.taskId}`);
        
        if (result.success) {
            const taskData = result.data;
            
            Logger.success('获取任务详情成功', {
                status: result.status,
                duration: `${result.duration}ms`
            });

            // 处理最终输出
            if (taskData.final_output) {
                this.processFinalOutput(taskData.final_output);
            }

            // 处理漏洞数据
            if (taskData.vulnerabilities) {
                this.testResults.vulnerabilities = taskData.vulnerabilities;
            }

            return true;
        } else {
            Logger.error('获取任务详情失败', {
                status: result.status,
                error: result.error || result.data
            });
            return false;
        }
    }

    /**
     * 处理最终输出
     */
    processFinalOutput(output) {
        Logger.divider('工作流最终输出');

        // 打印目标信息
        if (output.target) {
            Logger.info('扫描目标', { target: output.target });
        }

        // 打印完成的任务
        if (output.completed_tasks) {
            Logger.info('完成的任务', { tasks: output.completed_tasks });
        }

        // 打印工具结果
        if (output.tool_results) {
            Logger.divider('工具执行结果');
            Object.entries(output.tool_results).forEach(([toolName, result]) => {
                Logger.node(toolName, result.status || 'completed', result);
            });
        }

        // 打印执行轨迹
        if (output.execution_trace_report) {
            Logger.divider('执行轨迹报告');
            Logger.info('执行轨迹', output.execution_trace_report);
        }
    }

    /**
     * 打印漏洞扫描结果
     */
    printVulnerabilityResults() {
        Logger.divider('安全漏洞扫描结果');

        const vulnerabilities = this.testResults.vulnerabilities;

        if (!vulnerabilities || vulnerabilities.length === 0) {
            Logger.info('未发现漏洞');
            return;
        }

        console.log(`\n${COLORS.RED}╔════════════════════════════════════════════════════════════╗${COLORS.RESET}`);
        console.log(`${COLORS.RED}║                    发现 ${vulnerabilities.length} 个漏洞                           ║${COLORS.RESET}`);
        console.log(`${COLORS.RED}╚════════════════════════════════════════════════════════════╝${COLORS.RESET}\n`);

        vulnerabilities.forEach((vuln, index) => {
            const severityColor = this.getSeverityColor(vuln.severity);
            
            console.log(`\n${COLORS.CYAN}┌────────────────────────────────────────────────────────────${COLORS.RESET}`);
            console.log(`${COLORS.WHITE}│ 漏洞 #${index + 1}${COLORS.RESET}`);
            console.log(`${COLORS.CYAN}├────────────────────────────────────────────────────────────${COLORS.RESET}`);
            
            // 漏洞名称
            console.log(`${COLORS.WHITE}│ 名称: ${vuln.name || vuln.title || '未知漏洞'}${COLORS.RESET}`);
            
            // CVE编号
            if (vuln.cve) {
                console.log(`${COLORS.YELLOW}│ CVE: ${vuln.cve}${COLORS.RESET}`);
            }
            
            // 风险等级
            console.log(`${severityColor}│ 风险等级: ${vuln.severity || '未知'}${COLORS.RESET}`);
            
            // 漏洞类型
            if (vuln.vuln_type || vuln.type) {
                console.log(`${COLORS.WHITE}│ 漏洞类型: ${vuln.vuln_type || vuln.type}${COLORS.RESET}`);
            }
            
            // 受影响URL
            if (vuln.url || vuln.target) {
                console.log(`${COLORS.WHITE}│ 受影响URL: ${vuln.url || vuln.target}${COLORS.RESET}`);
            }
            
            // 受影响文件
            if (vuln.affected_file || vuln.file) {
                console.log(`${COLORS.WHITE}│ 受影响文件: ${vuln.affected_file || vuln.file}${COLORS.RESET}`);
            }
            
            // 漏洞位置
            if (vuln.location || vuln.line) {
                console.log(`${COLORS.WHITE}│ 漏洞位置: ${vuln.location || `行 ${vuln.line}`}${COLORS.RESET}`);
            }
            
            // 描述
            if (vuln.description) {
                console.log(`${COLORS.WHITE}│ 描述: ${vuln.description.substring(0, 100)}${vuln.description.length > 100 ? '...' : ''}${COLORS.RESET}`);
            }
            
            // 修复建议
            if (vuln.remediation || vuln.fix_suggestion) {
                console.log(`${COLORS.GREEN}│ 修复建议: ${vuln.remediation || vuln.fix_suggestion}${COLORS.RESET}`);
            }
            
            // CVSS评分
            if (vuln.cvss_score) {
                console.log(`${COLORS.WHITE}│ CVSS评分: ${vuln.cvss_score}${COLORS.RESET}`);
            }
            
            // 置信度
            if (vuln.confidence) {
                console.log(`${COLORS.WHITE}│ 置信度: ${(vuln.confidence * 100).toFixed(1)}%${COLORS.RESET}`);
            }
            
            // 来源
            if (vuln.source) {
                console.log(`${COLORS.WHITE}│ 来源: ${vuln.source}${COLORS.RESET}`);
            }
            
            console.log(`${COLORS.CYAN}└────────────────────────────────────────────────────────────${COLORS.RESET}`);
        });

        // 统计信息
        this.printVulnerabilityStats(vulnerabilities);
    }

    /**
     * 打印漏洞统计信息
     */
    printVulnerabilityStats(vulnerabilities) {
        const stats = {
            critical: 0,
            high: 0,
            medium: 0,
            low: 0,
            info: 0
        };

        vulnerabilities.forEach(vuln => {
            const severity = (vuln.severity || 'info').toLowerCase();
            if (stats.hasOwnProperty(severity)) {
                stats[severity]++;
            }
        });

        console.log(`\n${COLORS.CYAN}╔════════════════════════════════════════════════════════════╗${COLORS.RESET}`);
        console.log(`${COLORS.WHITE}║                      漏洞统计                              ║${COLORS.RESET}`);
        console.log(`${COLORS.CYAN}╠════════════════════════════════════════════════════════════╣${COLORS.RESET}`);
        console.log(`${COLORS.RED}║  Critical: ${stats.critical.toString().padEnd(10)}                              ║${COLORS.RESET}`);
        console.log(`${COLORS.YELLOW}║  High:     ${stats.high.toString().padEnd(10)}                              ║${COLORS.RESET}`);
        console.log(`${COLORS.BLUE}║  Medium:   ${stats.medium.toString().padEnd(10)}                              ║${COLORS.RESET}`);
        console.log(`${COLORS.GREEN}║  Low:      ${stats.low.toString().padEnd(10)}                              ║${COLORS.RESET}`);
        console.log(`${COLORS.WHITE}║  Info:     ${stats.info.toString().padEnd(10)}                              ║${COLORS.RESET}`);
        console.log(`${COLORS.CYAN}╚════════════════════════════════════════════════════════════╝${COLORS.RESET}`);
    }

    /**
     * 获取严重度颜色
     */
    getSeverityColor(severity) {
        const s = (severity || '').toLowerCase();
        switch (s) {
            case 'critical': return COLORS.RED;
            case 'high': return COLORS.YELLOW;
            case 'medium': return COLORS.BLUE;
            case 'low': return COLORS.GREEN;
            default: return COLORS.WHITE;
        }
    }

    /**
     * 打印测试总结
     */
    printSummary() {
        Logger.divider('测试总结');

        const totalDuration = new Date(this.testResults.endTime) - new Date(this.testResults.startTime);
        const nodeCount = this.testResults.nodes.length;
        const vulnCount = this.testResults.vulnerabilities.length;
        const errorCount = this.testResults.errors.length;

        console.log(`\n${COLORS.CYAN}╔════════════════════════════════════════════════════════════╗${COLORS.RESET}`);
        console.log(`${COLORS.WHITE}║                    测试执行总结                             ║${COLORS.RESET}`);
        console.log(`${COLORS.CYAN}╠════════════════════════════════════════════════════════════╣${COLORS.RESET}`);
        console.log(`${COLORS.WHITE}║  开始时间: ${this.testResults.startTime.padEnd(30)}║${COLORS.RESET}`);
        console.log(`${COLORS.WHITE}║  结束时间: ${this.testResults.endTime.padEnd(30)}║${COLORS.RESET}`);
        console.log(`${COLORS.WHITE}║  总耗时:   ${(totalDuration / 1000).toFixed(2)}秒`.padEnd(44) + `║${COLORS.RESET}`);
        console.log(`${COLORS.CYAN}╠════════════════════════════════════════════════════════════╣${COLORS.RESET}`);
        console.log(`${COLORS.GREEN}║  执行节点数: ${nodeCount.toString().padEnd(10)}                          ║${COLORS.RESET}`);
        console.log(`${COLORS.RED}║  发现漏洞数: ${vulnCount.toString().padEnd(10)}                          ║${COLORS.RESET}`);
        console.log(`${COLORS.YELLOW}║  错误数量:   ${errorCount.toString().padEnd(10)}                          ║${COLORS.RESET}`);
        console.log(`${COLORS.CYAN}╚════════════════════════════════════════════════════════════╝${COLORS.RESET}`);

        // 打印节点执行详情
        if (nodeCount > 0) {
            console.log(`\n${COLORS.CYAN}节点执行详情:${COLORS.RESET}`);
            console.log(`${COLORS.CYAN}┌────────────────────────────────────────────────────────────┐${COLORS.RESET}`);
            console.log(`${COLORS.WHITE}│ 节点名称           │ 状态     │ 耗时(ms) │ 时间戳        │${COLORS.RESET}`);
            console.log(`${COLORS.CYAN}├────────────────────────────────────────────────────────────┤${COLORS.RESET}`);
            
            this.testResults.nodes.forEach(node => {
                const statusColor = node.status === 'success' ? COLORS.GREEN : 
                                   node.status === 'running' ? COLORS.YELLOW : COLORS.RED;
                const name = (node.node || 'unknown').substring(0, 18).padEnd(18);
                const status = (node.status || 'unknown').padEnd(8);
                const duration = (node.duration || 0).toString().padEnd(8);
                const time = (node.startTime || '').substring(11, 19);
                
                console.log(`│ ${name}│ ${statusColor}${status}${COLORS.RESET} │ ${duration} │ ${time}      │`);
            });
            
            console.log(`${COLORS.CYAN}└────────────────────────────────────────────────────────────┘${COLORS.RESET}`);
        }

        // 打印错误信息
        if (errorCount > 0) {
            console.log(`\n${COLORS.RED}错误详情:${COLORS.RESET}`);
            this.testResults.errors.forEach((err, index) => {
                console.log(`${COLORS.RED}[${index + 1}] ${err.stage}: ${err.error}${COLORS.RESET}`);
            });
        }
    }

    /**
     * 休眠函数
     */
    sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
}

/**
 * Node.js环境适配
 */
if (typeof fetch === 'undefined') {
    // Node.js环境需要安装node-fetch
    try {
        global.fetch = require('node-fetch');
    } catch (e) {
        console.error('请安装node-fetch: npm install node-fetch');
        process.exit(1);
    }
}

/**
 * 主函数
 */
async function main() {
    const tester = new AIAgentWorkflowTester();
    
    // 测试目标
    const target = process.argv[2] || 'http://testphp.vulnweb.com';
    
    console.log(`
${COLORS.CYAN}
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║              AI Agent 工作流测试脚本                          ║
║                                                               ║
║  功能:                                                        ║
║  1. 建立与后端API的连接                                       ║
║  2. 触发完整的AI Agent工作流程                                ║
║  3. 实现Agent调用机制                                         ║
║  4. 打印每个节点的调用结果                                    ║
║  5. 记录执行信息                                              ║
║  6. 触发安全漏洞扫描功能                                      ║
║  7. 打印漏洞扫描详细结果                                      ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
${COLORS.RESET}
`);

    await tester.runFullTest(target);
}

// 运行测试
main().catch(error => {
    Logger.error('测试脚本执行失败', {
        error: error.message,
        stack: error.stack
    });
    process.exit(1);
});

// 导出模块
module.exports = {
    AIAgentWorkflowTester,
    APIClient,
    Logger,
    CONFIG
};
