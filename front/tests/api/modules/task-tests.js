import TEST_CONFIG from './test-config.js'
import { testUtils } from './test-utils.js'
import { testReporter } from './test-reporter.js'
import { api } from './api-client.js'

export class TaskTests {
  constructor() {
    this.createdTaskIds = []
  }

  async runAll() {
    testReporter.startSuite('Task Management API Tests')

    await this.testGetTasks()
    await this.testCreateTask()
    await this.testCreateTaskWithInvalidData()
    await this.testGetTaskById()
    await this.testGetNonExistentTask()
    await this.testUpdateTask()
    await this.testDeleteTask()
    await this.testGetTaskResults()
    await this.testCancelTask()
    await this.testGetTaskLogs()
    await this.testPagination()
    await this.testFiltering()

    await this.cleanup()
    testReporter.endSuite()
  }

  async testGetTasks() {
    testReporter.startTest('Get Tasks List')
    const startTime = performance.now()

    try {
      const response = await api.tasks.getTasks({ limit: 10 })

      testUtils.assertCondition(response.ok, 'Response should be successful')
      
      if (response.data) {
        testUtils.assertArray(response.data.items || response.data, 'Tasks should be an array')
      }

      const duration = performance.now() - startTime
      testReporter.endTest('passed', null, duration)
    } catch (error) {
      const duration = performance.now() - startTime
      testReporter.endTest('failed', error.message, duration)
    }
  }

  async testCreateTask() {
    testReporter.startTest('Create Task - Valid Data')
    const startTime = performance.now()

    try {
      const taskData = testUtils.generateTestData('task')
      
      const response = await api.tasks.createTask(taskData)

      testUtils.assertCondition(
        response.ok || response.status === 201,
        'Task creation should succeed'
      )

      if (response.data?.id || response.data?.task_id) {
        const taskId = response.data.id || response.data.task_id
        this.createdTaskIds.push(taskId)
        testUtils.log(`Task created with ID: ${taskId}`, 'success')
      }

      const duration = performance.now() - startTime
      testReporter.endTest('passed', null, duration)
    } catch (error) {
      const duration = performance.now() - startTime
      testReporter.endTest('failed', error.message, duration)
    }
  }

  async testCreateTaskWithInvalidData() {
    testReporter.startTest('Create Task - Invalid Data')
    const startTime = performance.now()

    try {
      const invalidDataSets = [
        { task_name: '', target: TEST_CONFIG.TEST_TARGETS.validUrl },
        { task_name: 'Test', target: '' },
        { task_name: '', target: '' },
        { task_name: 'Test', target: 'not-a-valid-url' }
      ]

      for (const data of invalidDataSets) {
        const response = await api.tasks.createTask(data)
        testUtils.assertCondition(
          !response.ok || response.status === 400,
          'Should reject invalid task data'
        )
      }

      const duration = performance.now() - startTime
      testReporter.endTest('passed', null, duration)
    } catch (error) {
      const duration = performance.now() - startTime
      testReporter.endTest('failed', error.message, duration)
    }
  }

  async testGetTaskById() {
    testReporter.startTest('Get Task By ID')
    const startTime = performance.now()

    try {
      if (this.createdTaskIds.length === 0) {
        const listResponse = await api.tasks.getTasks({ limit: 1 })
        if (listResponse.data?.items?.[0]?.id) {
          this.createdTaskIds.push(listResponse.data.items[0].id)
        }
      }

      if (this.createdTaskIds.length > 0) {
        const taskId = this.createdTaskIds[0]
        const response = await api.tasks.getTask(taskId)

        testUtils.assertCondition(response.ok, 'Should retrieve task by ID')
        
        if (response.data) {
          testUtils.assertCondition(
            response.data.id === taskId || response.data.task_id === taskId,
            'Task ID should match'
          )
        }
      }

      const duration = performance.now() - startTime
      testReporter.endTest('passed', null, duration)
    } catch (error) {
      const duration = performance.now() - startTime
      testReporter.endTest('failed', error.message, duration)
    }
  }

  async testGetNonExistentTask() {
    testReporter.startTest('Get Non-Existent Task')
    const startTime = performance.now()

    try {
      const response = await api.tasks.getTask(999999)

      testUtils.assertCondition(
        !response.ok || response.status === 404,
        'Should return 404 for non-existent task'
      )

      const duration = performance.now() - startTime
      testReporter.endTest('passed', null, duration)
    } catch (error) {
      const duration = performance.now() - startTime
      testReporter.endTest('failed', error.message, duration)
    }
  }

  async testUpdateTask() {
    testReporter.startTest('Update Task')
    const startTime = performance.now()

    try {
      if (this.createdTaskIds.length > 0) {
        const taskId = this.createdTaskIds[0]
        const updateData = {
          task_name: `Updated Task ${testUtils.generateRandomString(4)}`
        }

        const response = await api.tasks.updateTask(taskId, updateData)

        testUtils.assertCondition(
          response.ok || response.status === 200,
          'Task update should succeed'
        )
      }

      const duration = performance.now() - startTime
      testReporter.endTest('passed', null, duration)
    } catch (error) {
      const duration = performance.now() - startTime
      testReporter.endTest('failed', error.message, duration)
    }
  }

  async testDeleteTask() {
    testReporter.startTest('Delete Task')
    const startTime = performance.now()

    try {
      const taskData = testUtils.generateTestData('task')
      const createResponse = await api.tasks.createTask(taskData)

      if (createResponse.data?.id || createResponse.data?.task_id) {
        const taskId = createResponse.data.id || createResponse.data.task_id
        
        const deleteResponse = await api.tasks.deleteTask(taskId)
        
        testUtils.assertCondition(
          deleteResponse.ok || deleteResponse.status === 200,
          'Task deletion should succeed'
        )

        const verifyResponse = await api.tasks.getTask(taskId)
        testUtils.assertCondition(
          !verifyResponse.ok || verifyResponse.status === 404,
          'Deleted task should not be accessible'
        )
      }

      const duration = performance.now() - startTime
      testReporter.endTest('passed', null, duration)
    } catch (error) {
      const duration = performance.now() - startTime
      testReporter.endTest('failed', error.message, duration)
    }
  }

  async testGetTaskResults() {
    testReporter.startTest('Get Task Results')
    const startTime = performance.now()

    try {
      if (this.createdTaskIds.length > 0) {
        const taskId = this.createdTaskIds[0]
        const response = await api.tasks.getTaskResults(taskId)

        testUtils.assertCondition(response.ok, 'Should retrieve task results')
      }

      const duration = performance.now() - startTime
      testReporter.endTest('passed', null, duration)
    } catch (error) {
      const duration = performance.now() - startTime
      testReporter.endTest('failed', error.message, duration)
    }
  }

  async testCancelTask() {
    testReporter.startTest('Cancel Task')
    const startTime = performance.now()

    try {
      const taskData = testUtils.generateTestData('task')
      const createResponse = await api.tasks.createTask(taskData)

      if (createResponse.data?.id || createResponse.data?.task_id) {
        const taskId = createResponse.data.id || createResponse.data.task_id
        
        const response = await api.tasks.cancelTask(taskId)
        
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

  async testGetTaskLogs() {
    testReporter.startTest('Get Task Logs')
    const startTime = performance.now()

    try {
      if (this.createdTaskIds.length > 0) {
        const taskId = this.createdTaskIds[0]
        const response = await api.tasks.getTaskLogs(taskId, { limit: 100 })

        testUtils.assertCondition(response.ok, 'Should retrieve task logs')
      }

      const duration = performance.now() - startTime
      testReporter.endTest('passed', null, duration)
    } catch (error) {
      const duration = performance.now() - startTime
      testReporter.endTest('failed', error.message, duration)
    }
  }

  async testPagination() {
    testReporter.startTest('Task Pagination')
    const startTime = performance.now()

    try {
      const page1 = await api.tasks.getTasks({ page: 1, limit: 5 })
      const page2 = await api.tasks.getTasks({ page: 2, limit: 5 })

      testUtils.assertCondition(page1.ok, 'Page 1 should load')
      testUtils.assertCondition(page2.ok, 'Page 2 should load')

      const duration = performance.now() - startTime
      testReporter.endTest('passed', null, duration)
    } catch (error) {
      const duration = performance.now() - startTime
      testReporter.endTest('failed', error.message, duration)
    }
  }

  async testFiltering() {
    testReporter.startTest('Task Filtering')
    const startTime = performance.now()

    try {
      const filters = [
        { status: 'completed' },
        { task_type: 'poc_scan' },
        { search: 'test' }
      ]

      for (const filter of filters) {
        const response = await api.tasks.getTasks(filter)
        testUtils.assertCondition(response.ok, `Filter ${JSON.stringify(filter)} should work`)
      }

      const duration = performance.now() - startTime
      testReporter.endTest('passed', null, duration)
    } catch (error) {
      const duration = performance.now() - startTime
      testReporter.endTest('failed', error.message, duration)
    }
  }

  async cleanup() {
    testUtils.log('Cleaning up created tasks...', 'info')
    for (const taskId of this.createdTaskIds) {
      try {
        await api.tasks.deleteTask(taskId)
      } catch (error) {
        testUtils.log(`Failed to delete task ${taskId}: ${error.message}`, 'warning')
      }
    }
  }
}

export default TaskTests
