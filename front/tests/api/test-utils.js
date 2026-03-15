import TEST_CONFIG from './test-config.js'

class TestUtils {
  constructor() {
    this.testResults = []
    this.authToken = null
  }

  log(message, type = 'info') {
    const timestamp = new Date().toISOString()
    const logEntry = { timestamp, type, message }
    this.testResults.push(logEntry)
    
    const colors = {
      info: '\x1b[36m',
      success: '\x1b[32m',
      error: '\x1b[31m',
      warning: '\x1b[33m',
      reset: '\x1b[0m'
    }
    
    console.log(`${colors[type]}[${timestamp}] [${type.toUpperCase()}] ${message}${colors.reset}`)
  }

  async measureTime(fn, label = 'Operation') {
    const start = performance.now()
    try {
      const result = await fn()
      const end = performance.now()
      const duration = end - start
      this.log(`${label} completed in ${duration.toFixed(2)}ms`, 'success')
      return { success: true, result, duration }
    } catch (error) {
      const end = performance.now()
      const duration = end - start
      this.log(`${label} failed after ${duration.toFixed(2)}ms: ${error.message}`, 'error')
      return { success: false, error, duration }
    }
  }

  async retry(fn, maxRetries = TEST_CONFIG.RETRY_COUNT, delay = TEST_CONFIG.RETRY_DELAY) {
    let lastError
    for (let i = 0; i < maxRetries; i++) {
      try {
        return await fn()
      } catch (error) {
        lastError = error
        if (i < maxRetries - 1) {
          await this.sleep(delay)
          this.log(`Retry ${i + 1}/${maxRetries} after error: ${error.message}`, 'warning')
        }
      }
    }
    throw lastError
  }

  sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms))
  }

  generateRandomString(length = 10) {
    const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'
    let result = ''
    for (let i = 0; i < length; i++) {
      result += chars.charAt(Math.floor(Math.random() * chars.length))
    }
    return result
  }

  generateRandomEmail() {
    return `test_${this.generateRandomString(8)}@example.com`
  }

  generateRandomUrl() {
    return `https://${this.generateRandomString(8)}.example.com`
  }

  generateTestData(type = 'task') {
    const baseData = {
      task: {
        task_name: `Test Task ${this.generateRandomString(6)}`,
        target: TEST_CONFIG.TEST_TARGETS.validUrl,
        task_type: 'poc_scan'
      },
      scan: {
        target: TEST_CONFIG.TEST_TARGETS.validUrl,
        scan_type: 'quick_scan'
      },
      report: {
        name: `Test Report ${this.generateRandomString(6)}`,
        format: 'html'
      },
      user: {
        username: `user_${this.generateRandomString(6)}`,
        password: 'TestPass123!',
        email: this.generateRandomEmail()
      }
    }
    return baseData[type] || baseData.task
  }

  validateResponse(response, expectedStatus = 200) {
    if (!response) {
      throw new Error('Response is null or undefined')
    }
    
    const status = response.status || response.code || 200
    if (status !== expectedStatus && status !== 200 && status !== 201) {
      throw new Error(`Expected status ${expectedStatus}, got ${status}`)
    }
    
    return true
  }

  validateResponseStructure(response, requiredFields = []) {
    if (!response || typeof response !== 'object') {
      throw new Error('Invalid response structure: not an object')
    }
    
    for (const field of requiredFields) {
      if (!(field in response) && !(field in (response.data || {}))) {
        throw new Error(`Missing required field: ${field}`)
      }
    }
    
    return true
  }

  assertCondition(condition, message) {
    if (!condition) {
      throw new Error(`Assertion failed: ${message}`)
    }
    return true
  }

  assertEqual(actual, expected, message = '') {
    if (actual !== expected) {
      throw new Error(`Assertion failed: expected ${expected}, got ${actual}. ${message}`)
    }
    return true
  }

  assertType(value, expectedType, message = '') {
    const actualType = typeof value
    if (actualType !== expectedType) {
      throw new Error(`Type assertion failed: expected ${expectedType}, got ${actualType}. ${message}`)
    }
    return true
  }

  assertArray(value, message = '') {
    if (!Array.isArray(value)) {
      throw new Error(`Array assertion failed: value is not an array. ${message}`)
    }
    return true
  }

  assertContains(haystack, needle, message = '') {
    const contains = typeof haystack === 'string' 
      ? haystack.includes(needle)
      : haystack && needle in haystack
    
    if (!contains) {
      throw new Error(`Contains assertion failed: ${JSON.stringify(haystack)} does not contain ${needle}. ${message}`)
    }
    return true
  }

  sanitizeInput(input) {
    if (typeof input === 'string') {
      return input.replace(/[<>]/g, '')
    }
    return input
  }

  createMockResponse(data, status = 200) {
    return {
      status,
      code: status,
      data,
      message: 'Success',
      success: status >= 200 && status < 300
    }
  }

  formatBytes(bytes) {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  getTestResults() {
    return this.testResults
  }

  clearResults() {
    this.testResults = []
  }

  summarizeResults() {
    const summary = {
      total: this.testResults.length,
      info: this.testResults.filter(r => r.type === 'info').length,
      success: this.testResults.filter(r => r.type === 'success').length,
      error: this.testResults.filter(r => r.type === 'error').length,
      warning: this.testResults.filter(r => r.type === 'warning').length
    }
    return summary
  }
}

export const testUtils = new TestUtils()
export default TestUtils
