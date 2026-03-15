import TEST_CONFIG from './test-config.js'
import { testUtils } from './test-utils.js'
import { testReporter } from './test-reporter.js'
import { api } from './api-client.js'

export class ScanTests {
  constructor() {
    this.createdTargetIds = []
  }

  async runAll() {
    testReporter.startSuite('Scan API Tests')

    await this.runAWVSTests()
    await this.runPOCTests()
    await this.runAgentScanTests()

    await this.cleanup()
    testReporter.endSuite()
  }

  async runAWVSTests() {
    await this.testAWVSHealthCheck()
    await this.testAWVSGetTargets()
    await this.testAWVSCreateTarget()
    await this.testAWVSGetTarget()
    await this.testAWVSStartScan()
    await this.testAWVSGetScans()
    await this.testAWVSGetVulnerabilities()
    await this.testAWVSDeleteTarget()
  }

  async runPOCTests() {
    await this.testPOCGetTypes()
    await this.testPOCRunScan()
    await this.testPOCGetInfo()
    await this.testPOCScanWithInvalidTarget()
  }

  async runAgentScanTests() {
    await this.testAIAgentsGetTools()
    await this.testAIAgentsGetConfig()
    await this.testAIAgentsStartScan()
    await this.testAIAgentsGetTasks()
    await this.testAIAgentsGetTask()
    await this.testAIAgentsCancelTask()
  }

  async testAWVSHealthCheck() {
    testReporter.startTest('AWVS Health Check')
    const startTime = performance.now()

    try {
      const response = await api.awvs.healthCheck()

      testUtils.assertCondition(response.ok, 'AWVS health check should succeed')
      
      if (response.data) {
        testUtils.log(`AWVS Status: ${JSON.stringify(response.data)}`, 'info')
      }

      const duration = performance.now() - startTime
      testReporter.endTest('passed', null, duration)
    } catch (error) {
      const duration = performance.now() - startTime
      testReporter.endTest('failed', error.message, duration)
    }
  }

  async testAWVSGetTargets() {
    testReporter.startTest('AWVS Get Targets')
    const startTime = performance.now()

    try {
      const response = await api.awvs.getTargets()

      testUtils.assertCondition(response.ok, 'Should retrieve AWVS targets')
      
      if (response.data) {
        testUtils.assertArray(response.data.targets || response.data, 'Targets should be an array')
      }

      const duration = performance.now() - startTime
      testReporter.endTest('passed', null, duration)
    } catch (error) {
      const duration = performance.now() - startTime
      testReporter.endTest('failed', error.message, duration)
    }
  }

  async testAWVSCreateTarget() {
    testReporter.startTest('AWVS Create Target')
    const startTime = performance.now()

    try {
      const targetData = {
        address: TEST_CONFIG.TEST_TARGETS.validUrl,
        description: `Test Target ${testUtils.generateRandomString(6)}`
      }

      const response = await api.awvs.createTarget(targetData)

      testUtils.assertCondition(
        response.ok || response.status === 201,
        'Target creation should succeed'
      )

      if (response.data?.target_id || response.data?.id) {
        const targetId = response.data.target_id || response.data.id
        this.createdTargetIds.push(targetId)
        testUtils.log(`AWVS target created: ${targetId}`, 'success')
      }

      const duration = performance.now() - startTime
      testReporter.endTest('passed', null, duration)
    } catch (error) {
      const duration = performance.now() - startTime
      testReporter.endTest('failed', error.message, duration)
    }
  }

  async testAWVSGetTarget() {
    testReporter.startTest('AWVS Get Target By ID')
    const startTime = performance.now()

    try {
      if (this.createdTargetIds.length > 0) {
        const targetId = this.createdTargetIds[0]
        const response = await api.awvs.getTarget(targetId)

        testUtils.assertCondition(response.ok, 'Should retrieve target by ID')
      }

      const duration = performance.now() - startTime
      testReporter.endTest('passed', null, duration)
    } catch (error) {
      const duration = performance.now() - startTime
      testReporter.endTest('failed', error.message, duration)
    }
  }

  async testAWVSStartScan() {
    testReporter.startTest('AWVS Start Scan')
    const startTime = performance.now()

    try {
      const scanData = {
        url: TEST_CONFIG.TEST_TARGETS.validUrl,
        scan_type: 'quick_scan'
      }

      const response = await api.awvs.startScan(scanData)

      testUtils.assertCondition(
        response.ok || response.status === 201,
        'Scan start should succeed'
      )

      const duration = performance.now() - startTime
      testReporter.endTest('passed', null, duration)
    } catch (error) {
      const duration = performance.now() - startTime
      testReporter.endTest('failed', error.message, duration)
    }
  }

  async testAWVSGetScans() {
    testReporter.startTest('AWVS Get Scans')
    const startTime = performance.now()

    try {
      const response = await api.awvs.getScans()

      testUtils.assertCondition(response.ok, 'Should retrieve scans')
      
      if (response.data) {
        testUtils.assertArray(response.data.scans || response.data, 'Scans should be an array')
      }

      const duration = performance.now() - startTime
      testReporter.endTest('passed', null, duration)
    } catch (error) {
      const duration = performance.now() - startTime
      testReporter.endTest('failed', error.message, duration)
    }
  }

  async testAWVSGetVulnerabilities() {
    testReporter.startTest('AWVS Get Vulnerabilities')
    const startTime = performance.now()

    try {
      if (this.createdTargetIds.length > 0) {
        const targetId = this.createdTargetIds[0]
        const response = await api.awvs.getVulnerabilities(targetId)

        testUtils.assertCondition(response.ok, 'Should retrieve vulnerabilities')
      }

      const duration = performance.now() - startTime
      testReporter.endTest('passed', null, duration)
    } catch (error) {
      const duration = performance.now() - startTime
      testReporter.endTest('failed', error.message, duration)
    }
  }

  async testAWVSDeleteTarget() {
    testReporter.startTest('AWVS Delete Target')
    const startTime = performance.now()

    try {
      const targetData = {
        address: `${TEST_CONFIG.TEST_TARGETS.validUrl}/delete-test`,
        description: 'Target to delete'
      }

      const createResponse = await api.awvs.createTarget(targetData)

      if (createResponse.data?.target_id || createResponse.data?.id) {
        const targetId = createResponse.data.target_id || createResponse.data.id
        
        const deleteResponse = await api.awvs.deleteTarget(targetId)
        
        testUtils.assertCondition(
          deleteResponse.ok || deleteResponse.status === 200,
          'Target deletion should succeed'
        )
      }

      const duration = performance.now() - startTime
      testReporter.endTest('passed', null, duration)
    } catch (error) {
      const duration = performance.now() - startTime
      testReporter.endTest('failed', error.message, duration)
    }
  }

  async testPOCGetTypes() {
    testReporter.startTest('POC Get Types')
    const startTime = performance.now()

    try {
      const response = await api.poc.getTypes()

      testUtils.assertCondition(response.ok, 'Should retrieve POC types')
      
      if (response.data) {
        testUtils.assertArray(response.data.types || response.data, 'POC types should be an array')
      }

      const duration = performance.now() - startTime
      testReporter.endTest('passed', null, duration)
    } catch (error) {
      const duration = performance.now() - startTime
      testReporter.endTest('failed', error.message, duration)
    }
  }

  async testPOCRunScan() {
    testReporter.startTest('POC Run Scan')
    const startTime = performance.now()

    try {
      const scanData = {
        target: TEST_CONFIG.TEST_TARGETS.validUrl,
        poc_types: ['test_poc'],
        timeout: 10
      }

      const response = await api.poc.runScan(scanData)

      testUtils.assertCondition(
        response.ok || response.status === 201,
        'POC scan should start'
      )

      const duration = performance.now() - startTime
      testReporter.endTest('passed', null, duration)
    } catch (error) {
      const duration = performance.now() - startTime
      testReporter.endTest('failed', error.message, duration)
    }
  }

  async testPOCGetInfo() {
    testReporter.startTest('POC Get Info')
    const startTime = performance.now()

    try {
      const response = await api.poc.getInfo('test_poc')

      testUtils.assertCondition(
        response.ok || response.status === 200 || response.status === 404,
        'POC info request should complete'
      )

      const duration = performance.now() - startTime
      testReporter.endTest('passed', null, duration)
    } catch (error) {
      const duration = performance.now() - startTime
      testReporter.endTest('failed', error.message, duration)
    }
  }

  async testPOCScanWithInvalidTarget() {
    testReporter.startTest('POC Scan - Invalid Target')
    const startTime = performance.now()

    try {
      const scanData = {
        target: 'not-a-valid-url',
        poc_types: ['test_poc']
      }

      const response = await api.poc.runScan(scanData)

      testUtils.assertCondition(
        !response.ok || response.status === 400,
        'Should reject invalid target'
      )

      const duration = performance.now() - startTime
      testReporter.endTest('passed', null, duration)
    } catch (error) {
      const duration = performance.now() - startTime
      testReporter.endTest('failed', error.message, duration)
    }
  }

  async testAIAgentsGetTools() {
    testReporter.startTest('AI Agents Get Tools')
    const startTime = performance.now()

    try {
      const response = await api.aiAgents.getTools()

      testUtils.assertCondition(response.ok, 'Should retrieve AI agent tools')
      
      if (response.data) {
        testUtils.assertArray(response.data.tools || response.data, 'Tools should be an array')
      }

      const duration = performance.now() - startTime
      testReporter.endTest('passed', null, duration)
    } catch (error) {
      const duration = performance.now() - startTime
      testReporter.endTest('failed', error.message, duration)
    }
  }

  async testAIAgentsGetConfig() {
    testReporter.startTest('AI Agents Get Config')
    const startTime = performance.now()

    try {
      const response = await api.aiAgents.getConfig()

      testUtils.assertCondition(response.ok, 'Should retrieve AI agent config')

      const duration = performance.now() - startTime
      testReporter.endTest('passed', null, duration)
    } catch (error) {
      const duration = performance.now() - startTime
      testReporter.endTest('failed', error.message, duration)
    }
  }

  async testAIAgentsStartScan() {
    testReporter.startTest('AI Agents Start Scan')
    const startTime = performance.now()

    try {
      const scanData = {
        target: TEST_CONFIG.TEST_TARGETS.validUrl,
        scan_type: 'quick_scan',
        user_requirement: 'Test scan requirement'
      }

      const response = await api.aiAgents.startScan(scanData)

      testUtils.assertCondition(
        response.ok || response.status === 201,
        'AI agent scan should start'
      )

      const duration = performance.now() - startTime
      testReporter.endTest('passed', null, duration)
    } catch (error) {
      const duration = performance.now() - startTime
      testReporter.endTest('failed', error.message, duration)
    }
  }

  async testAIAgentsGetTasks() {
    testReporter.startTest('AI Agents Get Tasks')
    const startTime = performance.now()

    try {
      const response = await api.aiAgents.getTasks({ limit: 10 })

      testUtils.assertCondition(response.ok, 'Should retrieve AI agent tasks')

      const duration = performance.now() - startTime
      testReporter.endTest('passed', null, duration)
    } catch (error) {
      const duration = performance.now() - startTime
      testReporter.endTest('failed', error.message, duration)
    }
  }

  async testAIAgentsGetTask() {
    testReporter.startTest('AI Agents Get Task')
    const startTime = performance.now()

    try {
      const tasksResponse = await api.aiAgents.getTasks({ limit: 1 })
      
      if (tasksResponse.ok && tasksResponse.data?.items?.[0]?.id) {
        const taskId = tasksResponse.data.items[0].id
        const response = await api.aiAgents.getTask(taskId)
        
        testUtils.assertCondition(response.ok, 'Should retrieve AI agent task by ID')
      }

      const duration = performance.now() - startTime
      testReporter.endTest('passed', null, duration)
    } catch (error) {
      const duration = performance.now() - startTime
      testReporter.endTest('failed', error.message, duration)
    }
  }

  async testAIAgentsCancelTask() {
    testReporter.startTest('AI Agents Cancel Task')
    const startTime = performance.now()

    try {
      const scanData = {
        target: TEST_CONFIG.TEST_TARGETS.validUrl,
        scan_type: 'quick_scan'
      }

      const createResponse = await api.aiAgents.startScan(scanData)

      if (createResponse.data?.task_id || createResponse.data?.id) {
        const taskId = createResponse.data.task_id || createResponse.data.id
        
        const response = await api.aiAgents.cancelTask(taskId)
        
        testUtils.assertCondition(
          response.ok || response.status === 200,
          'Task cancellation should succeed'
        )
      }

      const duration = performance.now() - startTime
      testReporter.endTest('passed', null, duration)
    } catch (error) {
      const duration = performance.now() - startTime
      testReporter.endTest('failed', error.message, duration)
    }
  }

  async cleanup() {
    testUtils.log('Cleaning up created AWVS targets...', 'info')
    for (const targetId of this.createdTargetIds) {
      try {
        await api.awvs.deleteTarget(targetId)
      } catch (error) {
        testUtils.log(`Failed to delete target ${targetId}: ${error.message}`, 'warning')
      }
    }
  }
}

export default ScanTests
