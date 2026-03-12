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
      url: `/agent/task/${taskId}`,
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
      url: `/agent/task/${taskId}/abort`,
      method: 'post'
    })
  },

  getTaskLogs: async (taskId, params = {}) => {
    return request({
      url: `/agent/task/${taskId}/logs`,
      method: 'get',
      params
    })
  },

  getFrozenTasks: async () => {
    return request({
      url: `/ai_agents/tasks/frozen`,
      method: 'get'
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

export const pocVerificationApi = {
  createTask: async (data) => {
    return request({
      url: '/poc/verification/tasks',
      method: 'post',
      data
    })
  },

  createBatchTasks: async (data) => {
    return request({
      url: '/poc/verification/tasks/batch',
      method: 'post',
      data
    })
  },

  getTasks: async (params = {}) => {
    return request({
      url: '/poc/verification/tasks',
      method: 'get',
      params
    })
  },

  getTask: async (taskId) => {
    return request({
      url: `/poc/verification/tasks/${taskId}`,
      method: 'get'
    })
  },

  pauseTask: async (taskId) => {
    return request({
      url: `/poc/verification/tasks/${taskId}/pause`,
      method: 'post'
    })
  },

  resumeTask: async (taskId) => {
    return request({
      url: `/poc/verification/tasks/${taskId}/resume`,
      method: 'post'
    })
  },

  cancelTask: async (taskId) => {
    return request({
      url: `/poc/verification/tasks/${taskId}/cancel`,
      method: 'post'
    })
  },

  getTaskResults: async (taskId) => {
    return request({
      url: `/poc/verification/tasks/${taskId}/results`,
      method: 'get'
    })
  },

  generateReport: async (taskId, format = 'html') => {
    return request({
      url: `/poc/verification/tasks/${taskId}/report`,
      method: 'post',
      params: { format }
    })
  },

  getStatistics: async () => {
    return request({
      url: '/poc/verification/statistics',
      method: 'get'
    })
  },

  getPocRegistry: async () => {
    return request({
      url: '/poc/verification/poc/registry',
      method: 'get'
    })
  },

  syncPocsFromSeebug: async (params = {}) => {
    return request({
      url: '/poc/verification/poc/sync',
      method: 'post',
      params
    })
  },

  healthCheck: async () => {
    return request({
      url: '/poc/verification/health',
      method: 'get'
    })
  }
}

export const pocFilesApi = {
  getFiles: async (params = {}) => {
    return request({
      url: '/poc/files/list',
      method: 'get',
      params
    })
  },

  getFileContent: async (filePath) => {
    return request({
      url: `/poc/files/content/${filePath}`,
      method: 'get'
    })
  },

  getFileInfo: async (filePath) => {
    return request({
      url: `/poc/files/info/${filePath}`,
      method: 'get'
    })
  },

  getDirectories: async () => {
    return request({
      url: '/poc/files/directories',
      method: 'get'
    })
  },

  syncFiles: async () => {
    return request({
      url: '/poc/files/sync',
      method: 'post'
    })
  },

  getSyncStatus: async () => {
    return request({
      url: '/poc/files/sync/status',
      method: 'get'
    })
  }
}

export const seebugAgentApi = {
  getStatus: async () => {
    return request({
      url: '/seebug/status',
      method: 'get'
    })
  },

  search: async (data) => {
    return request({
      url: '/seebug/search',
      method: 'post',
      data
    })
  },

  getVulnerabilityDetail: async (ssvid) => {
    return request({
      url: `/seebug/vulnerability/${ssvid}`,
      method: 'get'
    })
  },

  generatePoc: async (data) => {
    return request({
      url: '/seebug/generate-poc',
      method: 'post',
      data
    })
  },

  generatePocBySsvid: async (ssvid, filename = null) => {
    return request({
      url: `/seebug/generate-poc/${ssvid}`,
      method: 'get',
      params: filename ? { filename } : {}
    })
  },

  testConnection: async () => {
    return request({
      url: '/seebug/test-connection',
      method: 'get'
    })
  }
}

export const aiAgentsApi = {
  startScan: async (data) => {
    return request({
      url: '/ai_agents/scan',
      method: 'post',
      data
    })
  },

  scan: async (data) => {
    return request({
      url: '/ai_agents/scan',
      method: 'post',
      data
    })
  },

  getTask: async (taskId) => {
    return request({
      url: `/ai_agents/tasks/${taskId}`,
      method: 'get'
    })
  },

  getTasks: async (params = {}) => {
    return request({
      url: '/ai_agents/tasks',
      method: 'get',
      params
    })
  },

  cancelTask: async (taskId) => {
    return request({
      url: `/ai_agents/tasks/${taskId}/cancel`,
      method: 'post'
    })
  },

  deleteTask: async (taskId) => {
    return request({
      url: `/ai_agents/tasks/${taskId}`,
      method: 'delete'
    })
  },

  getTools: async (category) => {
    return request({
      url: '/ai_agents/tools',
      method: 'get',
      params: category ? { category } : {}
    })
  },

  getConfig: async () => {
    return request({
      url: '/ai_agents/config',
      method: 'get'
    })
  },

  updateConfig: async (data) => {
    return request({
      url: '/ai_agents/config',
      method: 'post',
      data
    })
  },

  generateCode: async (data) => {
    return request({
      url: '/ai_agents/code/generate',
      method: 'post',
      data
    })
  },

  executeCode: async (data) => {
    return request({
      url: '/ai_agents/code/execute',
      method: 'post',
      data
    })
  },

  generateAndExecuteCode: async (data) => {
    return request({
      url: '/ai_agents/code/generate-and-execute',
      method: 'post',
      data
    })
  },

  enhanceCapability: async (data) => {
    return request({
      url: '/ai_agents/capabilities/enhance',
      method: 'post',
      data
    })
  },

  listCapabilities: async () => {
    return request({
      url: '/ai_agents/capabilities/list',
      method: 'get'
    })
  },

  getCapability: async (capabilityName) => {
    return request({
      url: `/ai_agents/capabilities/${capabilityName}`,
      method: 'get'
    })
  },

  deleteCapability: async (capabilityName) => {
    return request({
      url: `/ai_agents/capabilities/${capabilityName}`,
      method: 'delete'
    })
  },

  getEnvironmentInfo: async () => {
    return request({
      url: '/ai_agents/environment/info',
      method: 'get'
    })
  },

  getEnvironmentTools: async () => {
    return request({
      url: '/ai_agents/environment/tools',
      method: 'get'
    })
  },

  getToolDetail: async (toolName) => {
    return request({
      url: `/ai_agents/environment/tools/${toolName}`,
      method: 'get'
    })
  },

  getResourceUsage: async () => {
    return request({
      url: '/ai_agents/resources/usage',
      method: 'get'
    })
  },

  getResourceStatistics: async () => {
    return request({
      url: '/ai_agents/resources/statistics',
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
  notifications: notificationsApi,
  vulnerabilities: vulnerabilitiesApi,
  pocVerification: pocVerificationApi,
  pocFiles: pocFilesApi,
  seebugAgent: seebugAgentApi,
  aiAgents: aiAgentsApi
}
