import axios from 'axios'
import { errorHandler } from './errorHandler'
import { handleResponse, handleApiError } from './apiResponse'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:3000/api'
const REQUEST_TIMEOUT = parseInt(import.meta.env.VITE_REQUEST_TIMEOUT) || 30000

const instance = axios.create({
  baseURL: API_BASE_URL,
  timeout: REQUEST_TIMEOUT,
  headers: {
    'Content-Type': 'application/json'
  }
})

instance.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

instance.interceptors.response.use(
  (response) => {
    const handled = handleResponse(response.data)
    if (!handled.success) {
      errorHandler.handle(handled)
      return Promise.reject(new Error(handled.message || '操作失败'))
    }
    return handled
  },
  (error) => {
    if (error.response && error.response.status === 404) {
      return Promise.reject(new Error('资源不存在'))
    }
    const handled = handleApiError(error)
    errorHandler.handle(handled)
    return Promise.reject(new Error(handled.message || '请求失败'))
  }
)

export function request(config) {
  return instance(config)
}

export const scanApi = {
  startScan: async (data) => {
    return request({
      url: '/scan/start',
      method: 'post',
      data
    })
  },

  getScanStatus: async (scanId) => {
    return request({
      url: `/scan/status/${scanId}`,
      method: 'get'
    })
  },

  getScanResults: async (scanId) => {
    return request({
      url: `/scan/results/${scanId}`,
      method: 'get'
    })
  },

  stopScan: async (scanId) => {
    return request({
      url: `/scan/stop/${scanId}`,
      method: 'post'
    })
  },

  portScan: async (data) => {
    return request({
      url: '/scan/port-scan',
      method: 'post',
      data
    })
  },

  infoLeak: async (data) => {
    return request({
      url: '/scan/info-leak',
      method: 'post',
      data
    })
  },

  dirScan: async (data) => {
    return request({
      url: '/scan/dir-scan',
      method: 'post',
      data
    })
  },

  webSideScan: async (data) => {
    return request({
      url: '/scan/web-side',
      method: 'post',
      data
    })
  },

  baseInfo: async (data) => {
    return request({
      url: '/scan/baseinfo',
      method: 'post',
      data
    })
  },

  subdomainScan: async (data) => {
    return request({
      url: '/scan/subdomain',
      method: 'post',
      data
    })
  },

  comprehensiveScan: async (data) => {
    return request({
      url: '/scan/comprehensive',
      method: 'post',
      data
    })
  }
}

export const tasksApi = {
  createTask: async (data) => {
    return request({
      url: '/tasks/create',
      method: 'post',
      data
    })
  },

  getTasks: async (params = {}) => {
    return request({
      url: '/tasks/',
      method: 'get',
      params
    })
  },

  getTask: async (taskId) => {
    return request({
      url: `/tasks/${taskId}`,
      method: 'get'
    })
  },

  updateTask: async (taskId, data) => {
    return request({
      url: `/tasks/${taskId}`,
      method: 'put',
      data
    })
  },

  deleteTask: async (taskId) => {
    return request({
      url: `/tasks/${taskId}`,
      method: 'delete'
    })
  },

  getTaskResults: async (taskId) => {
    return request({
      url: `/tasks/${taskId}/results`,
      method: 'get'
    })
  },

  cancelTask: async (taskId) => {
    return request({
      url: `/tasks/${taskId}/cancel`,
      method: 'post'
    })
  },

  getTaskVulnerabilities: async (taskId, params = {}) => {
    return request({
      url: `/tasks/${taskId}/vulnerabilities`,
      method: 'get',
      params
    })
  },

  getStatisticsOverview: async () => {
    return request({
      url: '/tasks/statistics/overview',
      method: 'get'
    })
  }
}

export const reportsApi = {
  getReports: async (params = {}) => {
    return request({
      url: '/reports/',
      method: 'get',
      params
    })
  },

  createReport: async (data) => {
    return request({
      url: '/reports/',
      method: 'post',
      data
    })
  },

  getReport: async (reportId) => {
    return request({
      url: `/reports/${reportId}`,
      method: 'get'
    })
  },

  getReportDetail: async (reportId) => {
    return request({
      url: `/reports/${reportId}`,
      method: 'get'
    })
  },

  updateReport: async (reportId, data) => {
    return request({
      url: `/reports/${reportId}`,
      method: 'put',
      data
    })
  },

  delete: async (reportId) => {
    return request({
      url: `/reports/${reportId}`,
      method: 'delete'
    })
  },

  exportReport: async (reportId, format = 'json') => {
    return request({
      url: `/reports/${reportId}/export`,
      method: 'get',
      params: { format },
      responseType: format === 'html' ? 'blob' : 'json'
    })
  }
}

export const settingsApi = {
  getSettings: async () => {
    return request({
      url: '/settings/',
      method: 'get'
    })
  },

  updateSettings: async (data) => {
    return request({
      url: '/settings/',
      method: 'put',
      data
    })
  },

  getSettingItem: async (category, key) => {
    return request({
      url: `/settings/item/${category}/${key}`,
      method: 'get'
    })
  },

  updateSettingItem: async (data) => {
    return request({
      url: '/settings/item',
      method: 'put',
      data
    })
  },

  deleteSettingItem: async (category, key) => {
    return request({
      url: `/settings/item/${category}/${key}`,
      method: 'delete'
    })
  },

  getSystemInfo: async () => {
    return request({
      url: '/settings/system-info',
      method: 'get'
    })
  },

  getStatistics: async (period = 7) => {
    return request({
      url: '/settings/statistics',
      method: 'get',
      params: { period }
    })
  },

  getCategories: async () => {
    return request({
      url: '/settings/categories',
      method: 'get'
    })
  },

  getCategorySettings: async (category) => {
    return request({
      url: `/settings/category/${category}`,
      method: 'get'
    })
  },

  resetSettings: async () => {
    return request({
      url: '/settings/reset',
      method: 'post'
    })
  },

  resetCategorySettings: async (category) => {
    return request({
      url: `/settings/reset/${category}`,
      method: 'post'
    })
  },

  getApiKeys: async () => {
    return request({
      url: '/settings/api-keys',
      method: 'get'
    })
  },

  createApiKey: async (data) => {
    return request({
      url: '/settings/api-keys',
      method: 'post',
      data
    })
  },

  deleteApiKey: async (keyId) => {
    return request({
      url: `/settings/api-keys/${keyId}`,
      method: 'delete'
    })
  },

  regenerateApiKey: async (keyId) => {
    return request({
      url: `/settings/api-keys/${keyId}/regenerate`,
      method: 'put'
    })
  }
}

export const pocApi = {
  getPOCTypes: async () => {
    return request({
      url: '/poc/types',
      method: 'get'
    })
  },

  runPOC: async (data) => {
    return request({
      url: '/poc/scan',
      method: 'post',
      data
    })
  },

  getPOCResults: async (taskId) => {
    return request({
      url: `/tasks/${taskId}/results`,
      method: 'get'
    })
  },

  getPOCInfo: async (pocType) => {
    return request({
      url: `/poc/info/${pocType}`,
      method: 'get'
    })
  },

  scanSinglePOC: async (pocType, target, timeout = 10) => {
    return request({
      url: `/poc/scan/${pocType}`,
      method: 'post',
      params: { target, timeout }
    })
  }
}

export const awvsApi = {
  getTargets: async () => {
    return request({
      url: '/awvs/targets',
      method: 'get'
    })
  },

  createTarget: async (data) => {
    return request({
      url: '/awvs/target',
      method: 'post',
      data
    })
  },

  deleteTarget: async (targetId) => {
    return request({
      url: `/awvs/target/${targetId}`,
      method: 'delete'
    })
  },

  getScans: async (targetId) => {
    return request({
      url: '/awvs/scans',
      method: 'get',
      params: { target_id: targetId }
    })
  },

  startScan: async (data) => {
    return request({
      url: '/awvs/scan',
      method: 'post',
      data
    })
  },

  getScanStatus: async (scanId) => {
    return request({
      url: `/awvs/scans/${scanId}`,
      method: 'get'
    })
  },

  stopScan: async (scanId) => {
    return request({
      url: `/awvs/scans/${scanId}/stop`,
      method: 'post'
    })
  },

  getVulnerabilities: async (params = {}) => {
    return request({
      url: '/awvs/vulnerabilities',
      method: 'get',
      params
    })
  },

  getVulnerabilityDetail: async (vulnId) => {
    return request({
      url: `/awvs/vulnerability/${vulnId}`,
      method: 'get'
    })
  }
}

export const aiApi = {
  chat: async (data) => {
    return request({
      url: '/ai/chat',
      method: 'post',
      data
    })
  },

  analyzeVulnerability: async (data) => {
    return request({
      url: '/ai/analyze',
      method: 'post',
      data
    })
  },

  generatePOC: async (data) => {
    return request({
      url: '/ai/poc/generate',
      method: 'post',
      data
    })
  }
}

export const agentApi = {
  listAgents: async () => {
    return request({
      url: '/agent/list',
      method: 'get'
    })
  },

  getAgentStatus: async (agentId) => {
    return request({
      url: `/agent/${agentId}/status`,
      method: 'get'
    })
  },

  executeAgent: async (data) => {
    return request({
      url: '/agent/execute',
      method: 'post',
      data
    })
  },

  getAgentTypes: async () => {
    return request({
      url: '/agent/types',
      method: 'get'
    })
  },

  getAgentDetail: async (agentId) => {
    return request({
      url: `/agent/${agentId}`,
      method: 'get'
    })
  },

  createAgent: async (data) => {
    return request({
      url: '/agent/create',
      method: 'post',
      data
    })
  },

  updateAgent: async (agentId, data) => {
    return request({
      url: `/agent/${agentId}`,
      method: 'put',
      data
    })
  },

  deleteAgent: async (agentId) => {
    return request({
      url: `/agent/${agentId}`,
      method: 'delete'
    })
  }
}

export const kbApi = {
  search: async (params) => {
    return request({
      url: '/kb/vulnerabilities',
      method: 'get',
      params
    })
  },

  addKnowledge: async (data) => {
    return request({
      url: '/kb/vulnerabilities',
      method: 'post',
      data
    })
  },

  getKnowledge: async (knowledgeId) => {
    const response = await request({
      url: `/kb/vulnerabilities/${knowledgeId}`,
      method: 'get'
    })
    return { success: true, data: response, message: '获取成功' }
  },

  updateKnowledge: async (knowledgeId, data) => {
    return request({
      url: `/kb/vulnerabilities/${knowledgeId}`,
      method: 'put',
      data
    })
  },

  deleteKnowledge: async (knowledgeId) => {
    return request({
      url: `/kb/vulnerabilities/${knowledgeId}`,
      method: 'delete'
    })
  },

  sync: async () => {
    return request({
      url: '/kb/sync',
      method: 'post'
    })
  },

  searchPOC: async (data) => {
    return request({
      url: '/kb/seebug/poc/search',
      method: 'post',
      data
    })
  },

  downloadPOC: async (ssvid) => {
    return request({
      url: '/kb/seebug/poc/download',
      method: 'post',
      data: { ssvid }
    })
  },

  getPOCDetail: async (ssvid) => {
    return request({
      url: `/kb/seebug/poc/${ssvid}/detail`,
      method: 'get'
    })
  }
}

export const pocGenApi = {
  generate: async (data) => {
    return request({
      url: '/poc_gen/generate',
      method: 'post',
      data
    })
  },

  validate: async (data) => {
    return request({
      url: '/poc_gen/validate',
      method: 'post',
      data
    })
  }
}

export const userApi = {
  getProfile: async (userId = 1) => {
    return request({
      url: '/user/profile',
      method: 'get',
      params: { user_id: userId }
    })
  },

  updateProfile: async (userId, data) => {
    return request({
      url: '/user/profile',
      method: 'put',
      params: { user_id: userId },
      data
    })
  },

  getPermissions: async (userId = 1) => {
    return request({
      url: '/user/permissions',
      method: 'get',
      params: { user_id: userId }
    })
  },

  getList: async (params = {}) => {
    return request({
      url: '/user/list',
      method: 'get',
      params
    })
  }
}

export const notificationsApi = {
  getNotifications: async (params = {}) => {
    return request({
      url: '/notifications/',
      method: 'get',
      params
    })
  },

  getNotification: async (notificationId) => {
    return request({
      url: `/notifications/${notificationId}`,
      method: 'get'
    })
  },

  createNotification: async (data) => {
    return request({
      url: '/notifications/',
      method: 'post',
      data
    })
  },

  markAsRead: async (notificationId) => {
    return request({
      url: `/notifications/${notificationId}/read`,
      method: 'put'
    })
  },

  markAllAsRead: async () => {
    return request({
      url: '/notifications/read-all',
      method: 'put'
    })
  },

  deleteNotification: async (notificationId) => {
    return request({
      url: `/notifications/${notificationId}`,
      method: 'delete'
    })
  },

  deleteReadNotifications: async () => {
    return request({
      url: '/notifications/',
      method: 'delete'
    })
  },

  getUnreadCount: async () => {
    return request({
      url: '/notifications/count/unread',
      method: 'get'
    })
  }
}

export const vulnerabilitiesApi = {
  getVulnerabilities: async (params = {}) => {
    return request({
      url: '/vulnerabilities/',
      method: 'get',
      params
    })
  },

  getVulnerability: async (vulnId) => {
    return request({
      url: `/vulnerabilities/${vulnId}`,
      method: 'get'
    })
  },

  updateVulnerability: async (vulnId, data) => {
    return request({
      url: `/vulnerabilities/${vulnId}`,
      method: 'put',
      data
    })
  },

  deleteVulnerability: async (vulnId) => {
    return request({
      url: `/vulnerabilities/${vulnId}`,
      method: 'delete'
    })
  },

  getStatistics: async (params = {}) => {
    return request({
      url: '/vulnerabilities/statistics',
      method: 'get',
      params
    })
  }
}

export default {
  request,
  scan: scanApi,
  tasks: tasksApi,
  reports: reportsApi,
  settings: settingsApi,
  poc: pocApi,
  awvs: awvsApi,
  ai: aiApi,
  agent: agentApi,
  kb: kbApi,
  pocGen: pocGenApi,
  user: userApi,
  notifications: notificationsApi,
  vulnerabilities: vulnerabilitiesApi
}
