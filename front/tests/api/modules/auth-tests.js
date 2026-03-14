import TEST_CONFIG from './test-config.js'
import { testUtils } from './test-utils.js'
import { testReporter } from './test-reporter.js'
import { api } from './api-client.js'

export class AuthTests {
  constructor() {
    this.testUser = null
    this.authToken = null
  }

  async runAll() {
    testReporter.startSuite('Authentication API Tests')

    await this.testLogin()
    await this.testLoginWithInvalidCredentials()
    await this.testLoginWithEmptyFields()
    await this.testRegister()
    await this.testRegisterWithExistingUser()
    await this.testRegisterWithInvalidEmail()
    await this.testLogout()
    await this.testGetProfile()
    await this.testRefreshToken()
    await this.testPasswordValidation()
    await this.testTokenExpiration()

    testReporter.endSuite()
  }

  async testLogin() {
    testReporter.startTest('User Login - Valid Credentials')
    const startTime = performance.now()

    try {
      const response = await api.auth.login({
        username: TEST_CONFIG.TEST_USER.username,
        password: TEST_CONFIG.TEST_USER.password
      })

      testUtils.assertCondition(response.ok, 'Response should be successful')
      
      if (response.data?.token) {
        this.authToken = response.data.token
        testUtils.log('Login successful, token received', 'success')
      }

      const duration = performance.now() - startTime
      testReporter.endTest('passed', null, duration)
    } catch (error) {
      const duration = performance.now() - startTime
      testReporter.endTest('failed', error.message, duration)
    }
  }

  async testLoginWithInvalidCredentials() {
    testReporter.startTest('User Login - Invalid Credentials')
    const startTime = performance.now()

    try {
      const response = await api.auth.login({
        username: 'invaliduser',
        password: 'wrongpassword'
      })

      testUtils.assertCondition(!response.ok, 'Response should fail for invalid credentials')
      testUtils.assertCondition(
        response.status === 401 || response.status === 400,
        'Should return 401 or 400 status'
      )

      const duration = performance.now() - startTime
      testReporter.endTest('passed', null, duration)
    } catch (error) {
      const duration = performance.now() - startTime
      testReporter.endTest('failed', error.message, duration)
    }
  }

  async testLoginWithEmptyFields() {
    testReporter.startTest('User Login - Empty Fields')
    const startTime = performance.now()

    try {
      const response = await api.auth.login({
        username: '',
        password: ''
      })

      testUtils.assertCondition(
        !response.ok || response.status === 400,
        'Should reject empty fields'
      )

      const duration = performance.now() - startTime
      testReporter.endTest('passed', null, duration)
    } catch (error) {
      const duration = performance.now() - startTime
      testReporter.endTest('failed', error.message, duration)
    }
  }

  async testRegister() {
    testReporter.startTest('User Registration - Valid Data')
    const startTime = performance.now()

    try {
      const userData = {
        username: testUtils.generateRandomString(8),
        password: 'TestPass123!',
        email: testUtils.generateRandomEmail()
      }

      const response = await api.auth.register(userData)

      if (response.ok) {
        this.testUser = userData
        testUtils.log(`User registered: ${userData.username}`, 'success')
      }

      testUtils.assertCondition(
        response.ok || response.status === 201,
        'Registration should succeed with valid data'
      )

      const duration = performance.now() - startTime
      testReporter.endTest('passed', null, duration)
    } catch (error) {
      const duration = performance.now() - startTime
      testReporter.endTest('failed', error.message, duration)
    }
  }

  async testRegisterWithExistingUser() {
    testReporter.startTest('User Registration - Existing User')
    const startTime = performance.now()

    try {
      const response = await api.auth.register({
        username: TEST_CONFIG.TEST_USER.username,
        password: 'TestPass123!',
        email: testUtils.generateRandomEmail()
      })

      testUtils.assertCondition(
        !response.ok || response.status === 400 || response.status === 409,
        'Should reject duplicate username'
      )

      const duration = performance.now() - startTime
      testReporter.endTest('passed', null, duration)
    } catch (error) {
      const duration = performance.now() - startTime
      testReporter.endTest('failed', error.message, duration)
    }
  }

  async testRegisterWithInvalidEmail() {
    testReporter.startTest('User Registration - Invalid Email')
    const startTime = performance.now()

    try {
      const response = await api.auth.register({
        username: testUtils.generateRandomString(8),
        password: 'TestPass123!',
        email: 'not-an-email'
      })

      testUtils.assertCondition(
        !response.ok || response.status === 400,
        'Should reject invalid email format'
      )

      const duration = performance.now() - startTime
      testReporter.endTest('passed', null, duration)
    } catch (error) {
      const duration = performance.now() - startTime
      testReporter.endTest('failed', error.message, duration)
    }
  }

  async testLogout() {
    testReporter.startTest('User Logout')
    const startTime = performance.now()

    try {
      const response = await api.auth.logout()

      testUtils.assertCondition(
        response.ok || response.status === 200,
        'Logout should succeed'
      )

      const duration = performance.now() - startTime
      testReporter.endTest('passed', null, duration)
    } catch (error) {
      const duration = performance.now() - startTime
      testReporter.endTest('failed', error.message, duration)
    }
  }

  async testGetProfile() {
    testReporter.startTest('Get User Profile')
    const startTime = performance.now()

    try {
      const response = await api.auth.getProfile()

      if (response.ok && response.data) {
        testUtils.validateResponseStructure(response.data, ['username'])
      }

      const duration = performance.now() - startTime
      testReporter.endTest('passed', null, duration)
    } catch (error) {
      const duration = performance.now() - startTime
      testReporter.endTest('failed', error.message, duration)
    }
  }

  async testRefreshToken() {
    testReporter.startTest('Refresh Token')
    const startTime = performance.now()

    try {
      const response = await api.auth.refreshToken()

      if (response.ok && response.data?.token) {
        this.authToken = response.data.token
      }

      const duration = performance.now() - startTime
      testReporter.endTest('passed', null, duration)
    } catch (error) {
      const duration = performance.now() - startTime
      testReporter.endTest('failed', error.message, duration)
    }
  }

  async testPasswordValidation() {
    testReporter.startTest('Password Validation')
    const startTime = performance.now()

    try {
      const weakPasswords = ['123', 'abc', 'password']
      
      for (const weakPassword of weakPasswords) {
        const response = await api.auth.register({
          username: testUtils.generateRandomString(8),
          password: weakPassword,
          email: testUtils.generateRandomEmail()
        })

        testUtils.assertCondition(
          !response.ok || response.status === 400,
          `Should reject weak password: ${weakPassword}`
        )
      }

      const duration = performance.now() - startTime
      testReporter.endTest('passed', null, duration)
    } catch (error) {
      const duration = performance.now() - startTime
      testReporter.endTest('failed', error.message, duration)
    }
  }

  async testTokenExpiration() {
    testReporter.startTest('Token Expiration Handling')
    const startTime = performance.now()

    try {
      api.auth.setToken('invalid_expired_token')
      
      const response = await api.auth.getProfile()
      
      testUtils.assertCondition(
        !response.ok || response.status === 401,
        'Should reject expired token'
      )

      api.auth.clearToken()

      const duration = performance.now() - startTime
      testReporter.endTest('passed', null, duration)
    } catch (error) {
      api.auth.clearToken()
      const duration = performance.now() - startTime
      testReporter.endTest('failed', error.message, duration)
    }
  }
}

export default AuthTests
