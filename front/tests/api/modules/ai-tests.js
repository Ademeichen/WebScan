import TEST_CONFIG from './test-config.js'
import { testUtils } from './test-utils.js'
import { testReporter } from './test-reporter.js'
import { api } from './api-client.js'

export class AITests {
  constructor() {
    this.createdInstanceIds = []
  }

  async runAll() {
    testReporter.startSuite('AI API Tests')

    await this.testAIChat()
    await this.testAIChatWithEmptyMessage()
    await this.testAIChatWithLongMessage()
    await this.testGetChatInstances()
    await this.testCreateChatInstance()
    await this.testGetChatInstance()
    await this.testDeleteChatInstance()
    await this.testAIAgentsScan()
    await this.testAIAgentsGetTasks()
    await this.testAIAgentsGetTools()
    await this.testAIAgentsGetConfig()
    await this.testAIAgentsCodeGeneration()
    await this.testAIAnalysis()

    await this.cleanup()
    testReporter.endSuite()
  }

  async testAIChat() {
    testReporter.startTest('AI Chat - Valid Message')
    const startTime = performance.now()

    try {
      const chatData = {
        message: 'Hello, this is a test message',
        context: 'API Testing'
      }

      const response = await api.aiChat.chat(chatData)

      testUtils.assertCondition(response.ok, 'AI chat should succeed')
      
      if (response.data) {
        testUtils.log('AI chat response received', 'success')
      }

      const duration = performance.now() - startTime
      testReporter.endTest('passed', null, duration)
    } catch (error) {
      const duration = performance.now() - startTime
      testReporter.endTest('failed', error.message, duration)
    }
  }

  async testAIChatWithEmptyMessage() {
    testReporter.startTest('AI Chat - Empty Message')
    const startTime = performance.now()

    try {
      const response = await api.aiChat.chat({ message: '' })

      testUtils.assertCondition(
        !response.ok || response.status === 400,
        'Should reject empty message'
      )

      const duration = performance.now() - startTime
      testReporter.endTest('passed', null, duration)
    } catch (error) {
      const duration = performance.now() - startTime
      testReporter.endTest('failed', error.message, duration)
    }
  }

  async testAIChatWithLongMessage() {
    testReporter.startTest('AI Chat - Long Message')
    const startTime = performance.now()

    try {
      const longMessage = 'A'.repeat(5000)
      const response = await api.aiChat.chat({ message: longMessage })

      testUtils.assertCondition(
        response.ok || response.status === 400,
        'Should handle long message'
      )

      const duration = performance.now() - startTime
      testReporter.endTest('passed', null, duration)
    } catch (error) {
      const duration = performance.now() - startTime
      testReporter.endTest('failed', error.message, duration)
    }
  }

  async testGetChatInstances() {
    testReporter.startTest('Get AI Chat Instances')
    const startTime = performance.now()

    try {
      const response = await api.aiChat.getInstances()

      testUtils.assertCondition(response.ok, 'Should retrieve chat instances')
      
      if (response.data) {
        testUtils.assertArray(response.data.instances || response.data, 'Instances should be an array')
      }

      const duration = performance.now() - startTime
      testReporter.endTest('passed', null, duration)
    } catch (error) {
      const duration = performance.now() - startTime
      testReporter.endTest('failed', error.message, duration)
    }
  }

  async testCreateChatInstance() {
    testReporter.startTest('Create AI Chat Instance')
    const startTime = performance.now()

    try {
      const instanceData = {
        name: `Test Instance ${testUtils.generateRandomString(6)}`,
        model: 'gpt-4',
        context: 'API Testing'
      }

      const response = await api.aiChat.createInstance(instanceData)

      testUtils.assertCondition(
        response.ok || response.status === 201,
        'Chat instance creation should succeed'
      )

      if (response.data?.instance_id || response.data?.id) {
        const instanceId = response.data.instance_id || response.data.id
        this.createdInstanceIds.push(instanceId)
        testUtils.log(`Chat instance created: ${instanceId}`, 'success')
      }

      const duration = performance.now() - startTime
      testReporter.endTest('passed', null, duration)
    } catch (error) {
      const duration = performance.now() - startTime
      testReporter.endTest('failed', error.message, duration)
    }
  }

  async testGetChatInstance() {
    testReporter.startTest('Get AI Chat Instance By ID')
    const startTime = performance.now()

    try {
      if (this.createdInstanceIds.length > 0) {
        const instanceId = this.createdInstanceIds[0]
        const response = await api.aiChat.getInstance(instanceId)

        testUtils.assertCondition(response.ok, 'Should retrieve chat instance by ID')
      }

      const duration = performance.now() - startTime
      testReporter.endTest('passed', null, duration)
    } catch (error) {
      const duration = performance.now() - startTime
      testReporter.endTest('failed', error.message, duration)
    }
  }

  async testDeleteChatInstance() {
    testReporter.startTest('Delete AI Chat Instance')
    const startTime = performance.now()

    try {
      const instanceData = {
        name: 'Instance to Delete',
        model: 'gpt-4'
      }

      const createResponse = await api.aiChat.createInstance(instanceData)

      if (createResponse.data?.instance_id || createResponse.data?.id) {
        const instanceId = createResponse.data.instance_id || createResponse.data.id
        
        const deleteResponse = await api.aiChat.deleteInstance(instanceId)
        
        testUtils.assertCondition(
          deleteResponse.ok || deleteResponse.status === 200,
          'Chat instance deletion should succeed'
        )
      }

      const duration = performance.now() - startTime
      testReporter.endTest('passed', null, duration)
    } catch (error) {
      const duration = performance.now() - startTime
      testReporter.endTest('failed', error.message, duration)
    }
  }

  async testAIAgentsScan() {
    testReporter.startTest('AI Agents Scan')
    const startTime = performance.now()

    try {
      const scanData = {
        target: TEST_CONFIG.TEST_TARGETS.validUrl,
        scan_type: 'vulnerability_scan',
        user_requirement: 'Perform a comprehensive security scan'
      }

      const response = await api.aiAgents.startScan(scanData)

      testUtils.assertCondition(
        response.ok || response.status === 201,
        'AI agents scan should start'
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
      const response = await api.aiAgents.getTasks({ limit: 10, status: 'all' })

      testUtils.assertCondition(response.ok, 'Should retrieve AI agent tasks')

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
        testUtils.log(`Found ${response.data.length || 0} tools`, 'info')
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
      
      if (response.data) {
        testUtils.validateResponseStructure(response.data, ['model'])
      }

      const duration = performance.now() - startTime
      testReporter.endTest('passed', null, duration)
    } catch (error) {
      const duration = performance.now() - startTime
      testReporter.endTest('failed', error.message, duration)
    }
  }

  async testAIAgentsCodeGeneration() {
    testReporter.startTest('AI Agents Code Generation')
    const startTime = performance.now()

    try {
      const codeData = {
        prompt: 'Generate a simple port scanner in Python',
        language: 'python',
        context: 'security testing'
      }

      const response = await api.aiAgents.startScan({
        target: 'code_generation',
        ...codeData
      })

      testUtils.assertCondition(
        response.ok || response.status === 201 || response.status === 400,
        'Code generation request should be handled'
      )

      const duration = performance.now() - startTime
      testReporter.endTest('passed', null, duration)
    } catch (error) {
      const duration = performance.now() - startTime
      testReporter.endTest('failed', error.message, duration)
    }
  }

  async testAIAnalysis() {
    testReporter.startTest('AI Analysis')
    const startTime = performance.now()

    try {
      const tasksResponse = await api.aiAgents.getTasks({ limit: 1 })
      
      if (tasksResponse.ok && tasksResponse.data?.items?.[0]?.id) {
        const taskId = tasksResponse.data.items[0].id
        
        const response = await api.aiAgents.getTask(taskId)
        
        testUtils.assertCondition(
          response.ok || response.status === 200,
          'AI analysis should be accessible'
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
    testUtils.log('Cleaning up created chat instances...', 'info')
    for (const instanceId of this.createdInstanceIds) {
      try {
        await api.aiChat.deleteInstance(instanceId)
      } catch (error) {
        testUtils.log(`Failed to delete instance ${instanceId}: ${error.message}`, 'warning')
      }
    }
  }
}

export default AITests
