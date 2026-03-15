import TEST_CONFIG, { API_ENDPOINTS } from './test-config.js'
import { testUtils } from './test-utils.js'

class APIClient {
  constructor() {
    this.baseURL = TEST_CONFIG.API_BASE_URL
    this.timeout = TEST_CONFIG.TIMEOUT
    this.token = null
  }

  setToken(token) {
    this.token = token
    if (typeof localStorage !== 'undefined') {
      localStorage.setItem('token', token)
    }
  }

  clearToken() {
    this.token = null
    if (typeof localStorage !== 'undefined') {
      localStorage.removeItem('token')
    }
  }

  async request(endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`
    const controller = new AbortController()
    const timeoutId = setTimeout(() => controller.abort(), this.timeout)

    const headers = {
      'Content-Type': 'application/json',
      ...options.headers
    }

    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`
    }

    const config = {
      method: options.method || 'GET',
      headers,
      signal: controller.signal
    }

    if (options.body && ['POST', 'PUT', 'PATCH'].includes(config.method)) {
      config.body = JSON.stringify(options.body)
    }

    if (options.params) {
      const searchParams = new URLSearchParams()
      Object.entries(options.params).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          searchParams.append(key, value)
        }
      })
      const queryString = searchParams.toString()
      if (queryString) {
        endpoint += `?${queryString}`
      }
    }

    try {
      const response = await fetch(`${this.baseURL}${endpoint}`, config)
      clearTimeout(timeoutId)

      let data
      const contentType = response.headers.get('content-type')
      if (contentType && contentType.includes('application/json')) {
        data = await response.json()
      } else {
        data = await response.text()
      }

      return {
        status: response.status,
        ok: response.ok,
        data,
        headers: response.headers
      }
    } catch (error) {
      clearTimeout(timeoutId)
      if (error.name === 'AbortError') {
        throw new Error('Request timeout')
      }
      throw error
    }
  }

  async get(endpoint, params = {}) {
    return this.request(endpoint, { method: 'GET', params })
  }

  async post(endpoint, body = {}) {
    return this.request(endpoint, { method: 'POST', body })
  }

  async put(endpoint, body = {}) {
    return this.request(endpoint, { method: 'PUT', body })
  }

  async delete(endpoint) {
    return this.request(endpoint, { method: 'DELETE' })
  }

  async patch(endpoint, body = {}) {
    return this.request(endpoint, { method: 'PATCH', body })
  }
}

class AuthAPI extends APIClient {
  async login(credentials) {
    testUtils.log(`Attempting login for user: ${credentials.username}`, 'info')
    const response = await this.post(API_ENDPOINTS.AUTH.LOGIN, credentials)
    if (response.ok && response.data?.token) {
      this.setToken(response.data.token)
    }
    return response
  }

  async register(userData) {
    testUtils.log(`Registering new user: ${userData.username}`, 'info')
    return this.post(API_ENDPOINTS.AUTH.REGISTER, userData)
  }

  async logout() {
    testUtils.log('Logging out user', 'info')
    const response = await this.post(API_ENDPOINTS.AUTH.LOGOUT)
    this.clearToken()
    return response
  }

  async getProfile() {
    return this.get(API_ENDPOINTS.AUTH.PROFILE)
  }

  async refreshToken() {
    return this.post(API_ENDPOINTS.AUTH.REFRESH)
  }
}

class TasksAPI extends APIClient {
  async getTasks(params = {}) {
    return this.get(API_ENDPOINTS.TASKS.LIST, params)
  }

  async createTask(taskData) {
    testUtils.log(`Creating task: ${taskData.task_name}`, 'info')
    return this.post(API_ENDPOINTS.TASKS.CREATE, taskData)
  }

  async getTask(taskId) {
    return this.get(API_ENDPOINTS.TASKS.DETAIL(taskId))
  }

  async updateTask(taskId, data) {
    return this.put(API_ENDPOINTS.TASKS.UPDATE(taskId), data)
  }

  async deleteTask(taskId) {
    testUtils.log(`Deleting task: ${taskId}`, 'info')
    return this.delete(API_ENDPOINTS.TASKS.DELETE(taskId))
  }

  async getTaskResults(taskId) {
    return this.get(API_ENDPOINTS.TASKS.RESULTS(taskId))
  }

  async cancelTask(taskId) {
    return this.post(API_ENDPOINTS.TASKS.CANCEL(taskId))
  }

  async getTaskLogs(taskId, params = {}) {
    return this.get(API_ENDPOINTS.TASKS.LOGS(taskId), params)
  }
}

class ScanAPI extends APIClient {
  async portScan(data) {
    testUtils.log(`Starting port scan for: ${data.ip}`, 'info')
    return this.post(API_ENDPOINTS.SCAN.PORT, data)
  }

  async infoLeak(data) {
    testUtils.log(`Starting info leak scan for: ${data.url}`, 'info')
    return this.post(API_ENDPOINTS.SCAN.INFO_LEAK, data)
  }

  async dirScan(data) {
    testUtils.log(`Starting directory scan for: ${data.url}`, 'info')
    return this.post(API_ENDPOINTS.SCAN.DIR, data)
  }

  async subdomainScan(data) {
    testUtils.log(`Starting subdomain scan for: ${data.domain}`, 'info')
    return this.post(API_ENDPOINTS.SCAN.SUBDOMAIN, data)
  }

  async comprehensiveScan(data) {
    testUtils.log(`Starting comprehensive scan for: ${data.target}`, 'info')
    return this.post(API_ENDPOINTS.SCAN.COMPREHENSIVE, data)
  }
}

class AWVSAPI extends APIClient {
  async getTargets() {
    return this.get(API_ENDPOINTS.AWVS.TARGETS)
  }

  async createTarget(data) {
    testUtils.log(`Creating AWVS target: ${data.address}`, 'info')
    return this.post(API_ENDPOINTS.AWVS.TARGETS, data)
  }

  async getTarget(targetId) {
    return this.get(API_ENDPOINTS.AWVS.TARGET(targetId))
  }

  async deleteTarget(targetId) {
    return this.delete(API_ENDPOINTS.AWVS.TARGET(targetId))
  }

  async startScan(data) {
    testUtils.log(`Starting AWVS scan for: ${data.url}`, 'info')
    return this.post(API_ENDPOINTS.AWVS.SCAN, data)
  }

  async getScans(params = {}) {
    return this.get(API_ENDPOINTS.AWVS.SCANS, params)
  }

  async getVulnerabilities(targetId) {
    return this.get(API_ENDPOINTS.AWVS.VULNERABILITIES(targetId))
  }

  async healthCheck() {
    return this.get(API_ENDPOINTS.AWVS.HEALTH)
  }
}

class POCAPI extends APIClient {
  async getTypes() {
    return this.get(API_ENDPOINTS.POC.TYPES)
  }

  async runScan(data) {
    testUtils.log(`Running POC scan for: ${data.target}`, 'info')
    return this.post(API_ENDPOINTS.POC.SCAN, data)
  }

  async getInfo(pocType) {
    return this.get(API_ENDPOINTS.POC.INFO(pocType))
  }
}

class AIAgentsAPI extends APIClient {
  async startScan(data) {
    testUtils.log(`Starting AI agent scan for: ${data.target}`, 'info')
    return this.post(API_ENDPOINTS.AI_AGENTS.SCAN, data)
  }

  async getTasks(params = {}) {
    return this.get(API_ENDPOINTS.AI_AGENTS.TASKS, params)
  }

  async getTask(taskId) {
    return this.get(API_ENDPOINTS.AI_AGENTS.TASK(taskId))
  }

  async cancelTask(taskId) {
    return this.post(`${API_ENDPOINTS.AI_AGENTS.TASK(taskId)}/cancel`)
  }

  async getConfig() {
    return this.get(API_ENDPOINTS.AI_AGENTS.CONFIG)
  }

  async getTools() {
    return this.get(API_ENDPOINTS.AI_AGENTS.TOOLS)
  }
}

class AIChatAPI extends APIClient {
  async chat(data) {
    testUtils.log('Sending AI chat message', 'info')
    return this.post(API_ENDPOINTS.AI.CHAT, data)
  }

  async getInstances() {
    return this.get(API_ENDPOINTS.AI.INSTANCES)
  }

  async createInstance(data) {
    return this.post(API_ENDPOINTS.AI.INSTANCES, data)
  }

  async getInstance(instanceId) {
    return this.get(API_ENDPOINTS.AI.INSTANCE(instanceId))
  }

  async deleteInstance(instanceId) {
    return this.delete(API_ENDPOINTS.AI.INSTANCE(instanceId))
  }
}

class ReportsAPI extends APIClient {
  async getReports(params = {}) {
    return this.get(API_ENDPOINTS.REPORTS.LIST, params)
  }

  async createReport(data) {
    testUtils.log(`Creating report: ${data.name}`, 'info')
    return this.post(API_ENDPOINTS.REPORTS.CREATE, data)
  }

  async getReport(reportId) {
    return this.get(API_ENDPOINTS.REPORTS.DETAIL(reportId))
  }

  async updateReport(reportId, data) {
    return this.put(API_ENDPOINTS.REPORTS.DETAIL(reportId), data)
  }

  async deleteReport(reportId) {
    return this.delete(API_ENDPOINTS.REPORTS.DETAIL(reportId))
  }

  async exportReport(reportId, format = 'json') {
    return this.get(API_ENDPOINTS.REPORTS.EXPORT(reportId), { format })
  }

  async previewReport(reportId) {
    return this.get(API_ENDPOINTS.REPORTS.PREVIEW(reportId))
  }
}

class VulnerabilitiesAPI extends APIClient {
  async getVulnerabilities(params = {}) {
    return this.get(API_ENDPOINTS.VULNERABILITIES.LIST, params)
  }

  async getVulnerability(vulnId) {
    return this.get(API_ENDPOINTS.VULNERABILITIES.DETAIL(vulnId))
  }

  async search(keyword, params = {}) {
    return this.get(API_ENDPOINTS.VULNERABILITIES.SEARCH, { keyword, ...params })
  }
}

class UserAPI extends APIClient {
  async getProfile(userId = 1) {
    return this.get(API_ENDPOINTS.USER.PROFILE, { user_id: userId })
  }

  async updateProfile(userId, data) {
    return this.put(API_ENDPOINTS.USER.PROFILE, { user_id: userId, ...data })
  }

  async getPermissions(userId = 1) {
    return this.get(API_ENDPOINTS.USER.PERMISSIONS, { user_id: userId })
  }

  async getList(params = {}) {
    return this.get(API_ENDPOINTS.USER.LIST, params)
  }
}

class NotificationsAPI extends APIClient {
  async getNotifications(params = {}) {
    return this.get(API_ENDPOINTS.NOTIFICATIONS.LIST, params)
  }

  async getNotification(notificationId) {
    return this.get(API_ENDPOINTS.NOTIFICATIONS.DETAIL(notificationId))
  }

  async getUnreadCount() {
    return this.get(API_ENDPOINTS.NOTIFICATIONS.UNREAD_COUNT)
  }

  async markAsRead(notificationId) {
    return this.put(`${API_ENDPOINTS.NOTIFICATIONS.DETAIL(notificationId)}/read`)
  }

  async markAllAsRead() {
    return this.put('/notifications/read-all')
  }
}

class SettingsAPI extends APIClient {
  async getSettings() {
    return this.get(API_ENDPOINTS.SETTINGS.LIST)
  }

  async updateSettings(data) {
    return this.put(API_ENDPOINTS.SETTINGS.LIST, data)
  }

  async getSystemInfo() {
    return this.get(API_ENDPOINTS.SETTINGS.SYSTEM_INFO)
  }

  async getStatistics(period = 7) {
    return this.get(API_ENDPOINTS.SETTINGS.STATISTICS, { period })
  }
}

export const api = {
  auth: new AuthAPI(),
  tasks: new TasksAPI(),
  scan: new ScanAPI(),
  awvs: new AWVSAPI(),
  poc: new POCAPI(),
  aiAgents: new AIAgentsAPI(),
  aiChat: new AIChatAPI(),
  reports: new ReportsAPI(),
  vulnerabilities: new VulnerabilitiesAPI(),
  user: new UserAPI(),
  notifications: new NotificationsAPI(),
  settings: new SettingsAPI()
}

export default api
