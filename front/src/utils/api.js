import axios from 'axios'
import { errorHandler } from './errorHandler'
import { loadingManager } from './loading'
import { handleResponse, handleApiError } from './apiResponse'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8888/api'

const instance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
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
      return Promise.reject(handled)
    }
    return handled
  },
  (error) => {
    const handled = handleApiError(error)
    errorHandler.handle(handled)
    return Promise.reject(handled)
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

  updateReport: async (reportId, data) => {
    return request({
      url: `/reports/${reportId}`,
      method: 'put',
      data
    })
  },

  deleteReport: async (reportId) => {
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
      url: '/poc/run',
      method: 'post',
      data
    })
  },

  getPOCResults: async (taskId) => {
    return request({
      url: `/poc/results/${taskId}`,
      method: 'get'
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
      url: '/awvs/targets',
      method: 'post',
      data
    })
  },

  deleteTarget: async (targetId) => {
    return request({
      url: `/awvs/targets/${targetId}`,
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
      url: '/awvs/scans',
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

  getVulnerabilities: async (params = {}) => {
    return request({
      url: '/awvs/vulnerabilities',
      method: 'get',
      params
    })
  },

  getVulnerabilityDetail: async (vulnId) => {
    return request({
      url: `/awvs/vulnerabilities/${vulnId}`,
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
  }
}

export const kbApi = {
  search: async (params) => {
    return request({
      url: '/kb/search',
      method: 'get',
      params
    })
  },

  addKnowledge: async (data) => {
    return request({
      url: '/kb/add',
      method: 'post',
      data
    })
  },

  getKnowledge: async (knowledgeId) => {
    return request({
      url: `/kb/${knowledgeId}`,
      method: 'get'
    })
  },

  updateKnowledge: async (knowledgeId, data) => {
    return request({
      url: `/kb/${knowledgeId}`,
      method: 'put',
      data
    })
  },

  deleteKnowledge: async (knowledgeId) => {
    return request({
      url: `/kb/${knowledgeId}`,
      method: 'delete'
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
  notifications: notificationsApi
}
