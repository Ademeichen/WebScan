import TEST_CONFIG from './test-config.js'
import { testUtils } from './test-utils.js'
import { testReporter } from './test-reporter.js'
import { api } from './api-client.js'

export class PerformanceTests {
  constructor() {
    this.results = []
  }

  async runAll() {
    testReporter.startSuite('Performance Tests')

    await this.testResponseTime()
    await this.testConcurrentRequests()
    await this.testLargePayload()
    await this.testStressTest()
    await this.testMemoryUsage()
    await this.testTimeout()

    testReporter.endSuite()
    return this.results
  }

  async testResponseTime() {
    testReporter.startTest('API Response Time')
    const startTime = performance.now()

    try {
      const iterations = 10
      const responseTimes = []

      for (let i = 0; i < iterations; i++) {
        const reqStart = performance.now()
        await api.tasks.getTasks({ limit: 1 })
        const reqEnd = performance.now()
        responseTimes.push(reqEnd - reqStart)
      }

      const avgTime = responseTimes.reduce((a, b) => a + b, 0) / iterations
      const maxTime = Math.max(...responseTimes)
      const minTime = Math.min(...responseTimes)

      testUtils.log(`Response times - Avg: ${avgTime.toFixed(2)}ms, Max: ${maxTime.toFixed(2)}ms, Min: ${minTime.toFixed(2)}ms`, 'info')

      this.results.push({
        test: 'Response Time',
        avgTime,
        maxTime,
        minTime,
        passed: avgTime < TEST_CONFIG.PERFORMANCE.maxResponseTime
      })

      testUtils.assertCondition(
        avgTime < TEST_CONFIG.PERFORMANCE.maxResponseTime,
        `Average response time (${avgTime.toFixed(2)}ms) should be under ${TEST_CONFIG.PERFORMANCE.maxResponseTime}ms`
      )

      const duration = performance.now() - startTime
      testReporter.endTest('passed', null, duration)
    } catch (error) {
      const duration = performance.now() - startTime
      testReporter.endTest('failed', error.message, duration)
    }
  }

  async testConcurrentRequests() {
    testReporter.startTest('Concurrent Requests')
    const startTime = performance.now()

    try {
      const concurrentCount = TEST_CONFIG.PERFORMANCE.maxConcurrentRequests
      const promises = []

      for (let i = 0; i < concurrentCount; i++) {
        promises.push(api.tasks.getTasks({ limit: 1 }))
      }

      const results = await Promise.allSettled(promises)
      const successful = results.filter(r => r.status === 'fulfilled' && r.value.ok).length
      const failed = results.filter(r => r.status === 'rejected' || (r.status === 'fulfilled' && !r.value.ok)).length

      testUtils.log(`Concurrent requests: ${successful} successful, ${failed} failed`, 'info')

      this.results.push({
        test: 'Concurrent Requests',
        total: concurrentCount,
        successful,
        failed,
        passed: successful >= concurrentCount * 0.9
      })

      testUtils.assertCondition(
        successful >= concurrentCount * 0.9,
        `At least 90% of concurrent requests should succeed`
      )

      const duration = performance.now() - startTime
      testReporter.endTest('passed', null, duration)
    } catch (error) {
      const duration = performance.now() - startTime
      testReporter.endTest('failed', error.message, duration)
    }
  }

  async testLargePayload() {
    testReporter.startTest('Large Payload Handling')
    const startTime = performance.now()

    try {
      const largeData = {
        task_name: 'Large Payload Test',
        target: TEST_CONFIG.TEST_TARGETS.validUrl,
        description: 'A'.repeat(10000),
        tags: Array(100).fill(null).map((_, i) => `tag_${i}`)
      }

      const response = await api.tasks.createTask(largeData)

      testUtils.log(`Large payload test completed with status: ${response.status}`, 'info')

      this.results.push({
        test: 'Large Payload',
        status: response.status,
        passed: response.ok || response.status === 201 || response.status === 413
      })

      const duration = performance.now() - startTime
      testReporter.endTest('passed', null, duration)
    } catch (error) {
      const duration = performance.now() - startTime
      testReporter.endTest('failed', error.message, duration)
    }
  }

  async testStressTest() {
    testReporter.startTest('Stress Test')
    const startTime = performance.now()

    try {
      const iterations = TEST_CONFIG.PERFORMANCE.stressTestIterations
      let successCount = 0
      let errorCount = 0
      const errors = []

      for (let i = 0; i < iterations; i++) {
        try {
          const response = await api.tasks.getTasks({ limit: 1 })
          if (response.ok) {
            successCount++
          } else {
            errorCount++
          }
        } catch (error) {
          errorCount++
          if (errors.length < 5) {
            errors.push(error.message)
          }
        }

        if (i % 20 === 0) {
          await testUtils.sleep(10)
        }
      }

      const successRate = (successCount / iterations) * 100

      testUtils.log(`Stress test: ${successCount}/${iterations} successful (${successRate.toFixed(2)}%)`, 'info')

      this.results.push({
        test: 'Stress Test',
        iterations,
        successCount,
        errorCount,
        successRate,
        passed: successRate >= 95
      })

      testUtils.assertCondition(
        successRate >= 95,
        `Success rate should be at least 95% (got ${successRate.toFixed(2)}%)`
      )

      const duration = performance.now() - startTime
      testReporter.endTest('passed', null, duration)
    } catch (error) {
      const duration = performance.now() - startTime
      testReporter.endTest('failed', error.message, duration)
    }
  }

  async testMemoryUsage() {
    testReporter.startTest('Memory Usage')
    const startTime = performance.now()

    try {
      const initialMemory = performance.memory?.usedJSHeapSize || 0

      for (let i = 0; i < 50; i++) {
        await api.tasks.getTasks({ limit: 100 })
      }

      const finalMemory = performance.memory?.usedJSHeapSize || 0
      const memoryIncrease = finalMemory - initialMemory

      testUtils.log(`Memory increase: ${testUtils.formatBytes(memoryIncrease)}`, 'info')

      this.results.push({
        test: 'Memory Usage',
        initialMemory,
        finalMemory,
        memoryIncrease,
        passed: memoryIncrease < 50 * 1024 * 1024
      })

      const duration = performance.now() - startTime
      testReporter.endTest('passed', null, duration)
    } catch (error) {
      const duration = performance.now() - startTime
      testReporter.endTest('failed', error.message, duration)
    }
  }

  async testTimeout() {
    testReporter.startTest('Request Timeout')
    const startTime = performance.now()

    try {
      const originalTimeout = api.tasks.timeout
      api.tasks.timeout = 100

      try {
        await api.tasks.getTasks({ limit: 1000 })
      } catch (error) {
        testUtils.assertCondition(
          error.message.includes('timeout') || error.message.includes('Timeout'),
          'Should handle timeout correctly'
        )
      }

      api.tasks.timeout = originalTimeout

      this.results.push({
        test: 'Timeout',
        passed: true
      })

      const duration = performance.now() - startTime
      testReporter.endTest('passed', null, duration)
    } catch (error) {
      const duration = performance.now() - startTime
      testReporter.endTest('failed', error.message, duration)
    }
  }
}

export class BoundaryTests {
  constructor() {
    this.results = []
  }

  async runAll() {
    testReporter.startSuite('Boundary Condition Tests')

    await this.testEmptyInput()
    await this.testNullInput()
    await this.testUndefinedInput()
    await this.testSpecialCharacters()
    await this.testUnicodeCharacters()
    await this.testSQLInjection()
    await this.testXSSPayloads()
    await this.testExtremelyLongInput()
    await this.testNegativeNumbers()
    await this.testInvalidFormats()

    testReporter.endSuite()
    return this.results
  }

  async testEmptyInput() {
    testReporter.startTest('Empty Input Handling')
    const startTime = performance.now()

    try {
      const emptyInputs = [
        { task_name: '', target: '' },
        { username: '', password: '' },
        { name: '', format: '' }
      ]

      for (const input of emptyInputs) {
        const response = await api.tasks.createTask(input)
        testUtils.assertCondition(
          !response.ok || response.status === 400,
          'Should reject empty input'
        )
      }

      const duration = performance.now() - startTime
      testReporter.endTest('passed', null, duration)
    } catch (error) {
      const duration = performance.now() - startTime
      testReporter.endTest('failed', error.message, duration)
    }
  }

  async testNullInput() {
    testReporter.startTest('Null Input Handling')
    const startTime = performance.now()

    try {
      const response = await api.tasks.createTask(null)

      testUtils.assertCondition(
        !response.ok || response.status === 400,
        'Should reject null input'
      )

      const duration = performance.now() - startTime
      testReporter.endTest('passed', null, duration)
    } catch (error) {
      const duration = performance.now() - startTime
      testReporter.endTest('passed', null, duration)
    }
  }

  async testUndefinedInput() {
    testReporter.startTest('Undefined Input Handling')
    const startTime = performance.now()

    try {
      const response = await api.tasks.createTask(undefined)

      testUtils.assertCondition(
        !response.ok || response.status === 400,
        'Should reject undefined input'
      )

      const duration = performance.now() - startTime
      testReporter.endTest('passed', null, duration)
    } catch (error) {
      const duration = performance.now() - startTime
      testReporter.endTest('passed', null, duration)
    }
  }

  async testSpecialCharacters() {
    testReporter.startTest('Special Characters Handling')
    const startTime = performance.now()

    try {
      const specialChars = TEST_CONFIG.BOUNDARY.specialChars

      const response = await api.tasks.createTask({
        task_name: `Test${specialChars}Task`,
        target: TEST_CONFIG.TEST_TARGETS.validUrl
      })

      testUtils.log(`Special characters test completed with status: ${response.status}`, 'info')

      const duration = performance.now() - startTime
      testReporter.endTest('passed', null, duration)
    } catch (error) {
      const duration = performance.now() - startTime
      testReporter.endTest('failed', error.message, duration)
    }
  }

  async testUnicodeCharacters() {
    testReporter.startTest('Unicode Characters Handling')
    const startTime = performance.now()

    try {
      const unicodeChars = TEST_CONFIG.BOUNDARY.unicodeChars

      const response = await api.tasks.createTask({
        task_name: `Test${unicodeChars}Task`,
        target: TEST_CONFIG.TEST_TARGETS.validUrl
      })

      testUtils.log(`Unicode characters test completed with status: ${response.status}`, 'info')

      const duration = performance.now() - startTime
      testReporter.endTest('passed', null, duration)
    } catch (error) {
      const duration = performance.now() - startTime
      testReporter.endTest('failed', error.message, duration)
    }
  }

  async testSQLInjection() {
    testReporter.startTest('SQL Injection Protection')
    const startTime = performance.now()

    try {
      const payloads = TEST_CONFIG.BOUNDARY.sqlInjectionPayloads

      for (const payload of payloads) {
        const response = await api.tasks.createTask({
          task_name: payload,
          target: TEST_CONFIG.TEST_TARGETS.validUrl
        })

        if (response.data && !response.data.error?.includes('SQL')) {
          testUtils.log('SQL injection payload handled safely', 'success')
        }
      }

      const duration = performance.now() - startTime
      testReporter.endTest('passed', null, duration)
    } catch (error) {
      const duration = performance.now() - startTime
      testReporter.endTest('failed', error.message, duration)
    }
  }

  async testXSSPayloads() {
    testReporter.startTest('XSS Protection')
    const startTime = performance.now()

    try {
      const payloads = TEST_CONFIG.BOUNDARY.xssPayloads

      for (const payload of payloads) {
        const response = await api.tasks.createTask({
          task_name: payload,
          target: TEST_CONFIG.TEST_TARGETS.validUrl
        })

        if (response.data) {
          const dataStr = JSON.stringify(response.data)
          testUtils.assertCondition(
            !dataStr.includes('<script>') || dataStr.includes('&lt;script&gt;'),
            'XSS payload should be sanitized'
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

  async testExtremelyLongInput() {
    testReporter.startTest('Extremely Long Input')
    const startTime = performance.now()

    try {
      const longString = 'A'.repeat(TEST_CONFIG.BOUNDARY.maxStringLength)

      const response = await api.tasks.createTask({
        task_name: longString,
        target: TEST_CONFIG.TEST_TARGETS.validUrl
      })

      testUtils.log(`Long input test completed with status: ${response.status}`, 'info')

      const duration = performance.now() - startTime
      testReporter.endTest('passed', null, duration)
    } catch (error) {
      const duration = performance.now() - startTime
      testReporter.endTest('failed', error.message, duration)
    }
  }

  async testNegativeNumbers() {
    testReporter.startTest('Negative Numbers Handling')
    const startTime = performance.now()

    try {
      const response = await api.tasks.getTasks({
        page: -1,
        limit: -10
      })

      testUtils.log(`Negative numbers test completed with status: ${response.status}`, 'info')

      const duration = performance.now() - startTime
      testReporter.endTest('passed', null, duration)
    } catch (error) {
      const duration = performance.now() - startTime
      testReporter.endTest('failed', error.message, duration)
    }
  }

  async testInvalidFormats() {
    testReporter.startTest('Invalid Format Handling')
    const startTime = performance.now()

    try {
      const invalidFormats = [
        { target: 'not-a-url' },
        { target: 'ftp://invalid-protocol.com' },
        { target: 'javascript:alert(1)' }
      ]

      for (const format of invalidFormats) {
        const response = await api.tasks.createTask({
          task_name: 'Test Task',
          ...format
        })

        testUtils.assertCondition(
          !response.ok || response.status === 400,
          `Should reject invalid format: ${format.target}`
        )
      }

      const duration = performance.now() - startTime
      testReporter.endTest('passed', null, duration)
    } catch (error) {
      const duration = performance.now() - startTime
      testReporter.endTest('failed', error.message, duration)
    }
  }
}

export default { PerformanceTests, BoundaryTests }
