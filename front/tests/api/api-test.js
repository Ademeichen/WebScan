import TEST_CONFIG from './test-config.js'
import { testUtils } from './test-utils.js'
import { testReporter } from './test-reporter.js'
import { api } from './api-client.js'
import AuthTests from './modules/auth-tests.js'
import TaskTests from './modules/task-tests.js'
import ScanTests from './modules/scan-tests.js'
import ReportTests from './modules/report-tests.js'
import AITests from './modules/ai-tests.js'
import VulnerabilityTests from './modules/vulnerability-tests.js'
import { PerformanceTests, BoundaryTests } from './modules/performance-boundary-tests.js'

class APITestRunner {
  constructor(options = {}) {
    this.options = {
      runAuth: true,
      runTasks: true,
      runScans: true,
      runReports: true,
      runAI: true,
      runVulnerabilities: true,
      runPerformance: true,
      runBoundary: true,
      generateReport: true,
      reportFormats: ['text', 'json', 'html'],
      ...options
    }
    
    this.testModules = {
      auth: new AuthTests(),
      tasks: new TaskTests(),
      scans: new ScanTests(),
      reports: new ReportTests(),
      ai: new AITests(),
      vulnerabilities: new VulnerabilityTests(),
      performance: new PerformanceTests(),
      boundary: new BoundaryTests()
    }
  }

  async initialize() {
    testUtils.log('Initializing API Test Runner...', 'info')
    testUtils.log(`API Base URL: ${TEST_CONFIG.API_BASE_URL}`, 'info')
    testUtils.log(`Timeout: ${TEST_CONFIG.TIMEOUT}ms`, 'info')
    
    const healthCheck = await this.checkServerHealth()
    if (!healthCheck) {
      testUtils.log('Warning: Server health check failed. Tests may fail.', 'warning')
    }
    
    return healthCheck
  }

  async checkServerHealth() {
    try {
      const response = await api.settings.getSystemInfo()
      return response.ok
    } catch (error) {
      testUtils.log(`Server health check error: ${error.message}`, 'error')
      return false
    }
  }

  async runAll() {
    testReporter.startSession()
    const totalStartTime = performance.now()

    testUtils.log('\n' + '='.repeat(60), 'info')
    testUtils.log('           STARTING API TEST SUITE', 'info')
    testUtils.log('='.repeat(60) + '\n', 'info')

    try {
      await this.initialize()

      if (this.options.runAuth) {
        await this.runModule('auth', 'Authentication Tests')
      }

      if (this.options.runTasks) {
        await this.runModule('tasks', 'Task Management Tests')
      }

      if (this.options.runScans) {
        await this.runModule('scans', 'Scan API Tests')
      }

      if (this.options.runReports) {
        await this.runModule('reports', 'Report API Tests')
      }

      if (this.options.runAI) {
        await this.runModule('ai', 'AI API Tests')
      }

      if (this.options.runVulnerabilities) {
        await this.runModule('vulnerabilities', 'Vulnerability API Tests')
      }

      if (this.options.runPerformance) {
        await this.runModule('performance', 'Performance Tests')
      }

      if (this.options.runBoundary) {
        await this.runModule('boundary', 'Boundary Condition Tests')
      }

    } catch (error) {
      testUtils.log(`Test execution error: ${error.message}`, 'error')
    }

    const totalDuration = performance.now() - totalStartTime
    testReporter.endSession()

    if (this.options.generateReport) {
      await this.generateReports()
    }

    testReporter.printSummary()

    return testReporter.getSummary()
  }

  async runModule(moduleName, displayName) {
    testUtils.log(`\n${'─'.repeat(50)}`, 'info')
    testUtils.log(`Running: ${displayName}`, 'info')
    testUtils.log('─'.repeat(50), 'info')

    const module = this.testModules[moduleName]
    if (!module) {
      testUtils.log(`Module not found: ${moduleName}`, 'error')
      return
    }

    try {
      await module.runAll()
    } catch (error) {
      testUtils.log(`Module ${moduleName} failed: ${error.message}`, 'error')
    }
  }

  async generateReports() {
    testUtils.log('\nGenerating test reports...', 'info')

    for (const format of this.options.reportFormats) {
      try {
        const report = testReporter.saveReport(format)
        testUtils.log(`Generated ${format.toUpperCase()} report: ${report.filename}`, 'success')
      } catch (error) {
        testUtils.log(`Failed to generate ${format} report: ${error.message}`, 'error')
      }
    }
  }

  async runSpecific(moduleNames) {
    testReporter.startSession()

    for (const name of moduleNames) {
      if (this.testModules[name]) {
        await this.runModule(name, `${name} Tests`)
      } else {
        testUtils.log(`Unknown module: ${name}`, 'warning')
      }
    }

    testReporter.endSession()
    testReporter.printSummary()

    return testReporter.getSummary()
  }

  getAvailableModules() {
    return Object.keys(this.testModules)
  }
}

async function main() {
  const args = process.argv.slice(2)
  const options = {}

  for (const arg of args) {
    if (arg.startsWith('--')) {
      const [key, value] = arg.slice(2).split('=')
      if (key === 'modules') {
        const modules = value.split(',')
        Object.keys(options).forEach(m => {
          if (m.startsWith('run')) {
            options[m] = false
          }
        })
        modules.forEach(m => {
          const optionKey = `run${m.charAt(0).toUpperCase() + m.slice(1)}`
          options[optionKey] = true
        })
      } else if (key === 'format') {
        options.reportFormats = value.split(',')
      } else if (key === 'no-report') {
        options.generateReport = false
      }
    }
  }

  const runner = new APITestRunner(options)
  const results = await runner.runAll()

  const exitCode = results.failedTests > 0 ? 1 : 0
  process.exit(exitCode)
}

export { APITestRunner, main }
export default APITestRunner

if (typeof window !== 'undefined') {
  window.APITestRunner = APITestRunner
  window.runAPITests = async (options = {}) => {
    const runner = new APITestRunner(options)
    return runner.runAll()
  }
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { APITestRunner, main }
}
