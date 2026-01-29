<<<<<<< HEAD
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
      url: `/awvs/scans`,
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
=======
/**
 * API 基础配置
 */

// API 基础 URL
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:3000/api'

/**
 * API 请求封装
 */
class ApiClient {
  constructor(baseURL) {
    this.baseURL = baseURL
    this.defaultHeaders = {
      'Content-Type': 'application/json'
    }
  }

  /**
   * 通用请求方法
   */
  async request(url, options = {}) {
    const fullUrl = `${this.baseURL}${url}`
    
    const config = {
      ...options,
      headers: {
        ...this.defaultHeaders,
        ...options.headers
      }
    }

    try {
      const response = await fetch(fullUrl, config)
      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.message || '请求失败')
      }

      return data
    } catch (error) {
      console.error('API 请求错误:', error)
      throw error
    }
  }

  /**
   * GET 请求
   */
  get(url, params = {}) {
    const queryString = new URLSearchParams(params).toString()
    const fullUrl = queryString ? `${url}?${queryString}` : url
    return this.request(fullUrl, { method: 'GET' })
  }

  /**
   * POST 请求
   */
  post(url, data = {}) {
    return this.request(url, {
      method: 'POST',
      body: JSON.stringify(data)
    })
  }

  /**
   * PUT 请求
   */
  put(url, data = {}) {
    return this.request(url, {
      method: 'PUT',
      body: JSON.stringify(data)
    })
  }

  /**
   * DELETE 请求
   */
  delete(url) {
    return this.request(url, { method: 'DELETE' })
  }
}

// 创建 API 客户端实例
const apiClient = new ApiClient(API_BASE_URL)

/**
 * 扫描相关 API
 */
export const scanApi = {
  // 端口扫描
  portScan: (data) => apiClient.post('/scan/port-scan', data),
  
  // 信息泄露检测
  infoLeak: (data) => apiClient.post('/scan/info-leak', data),
  
  // 旁站扫描
  webSide: (data) => apiClient.post('/scan/web-side', data),
  
  // 网站基本信息
  baseInfo: (data) => apiClient.post('/scan/baseinfo', data),
  
  // 网站权重
  webWeight: (data) => apiClient.post('/scan/web-weight', data),
  
  // IP定位
  ipLocating: (data) => apiClient.post('/scan/ip-locating', data),
  
  // CDN检测
  cdnCheck: (data) => apiClient.post('/scan/cdn-check', data),
  
  // WAF检测
  wafCheck: (data) => apiClient.post('/scan/waf-check', data),
  
  // CMS指纹识别
  whatCms: (data) => apiClient.post('/scan/what-cms', data),
  
  // 子域名扫描
  subdomain: (data) => apiClient.post('/scan/subdomain', data),
  
  // 目录扫描
  dirScan: (data) => apiClient.post('/scan/dir-scan', data),
  
  // 综合扫描
  comprehensive: (data) => apiClient.post('/scan/comprehensive', data)
}

/**
 * 任务管理 API
 */
export const taskApi = {
  // 获取任务列表
  list: (params) => apiClient.get('/tasks/', params),
  
  // 创建任务
  create: (data) => apiClient.post('/tasks/', data),
  
  // 获取任务详情
  get: (taskId) => apiClient.get(`/tasks/${taskId}/`),
  
  // 更新任务
  update: (taskId, data) => apiClient.put(`/tasks/${taskId}/`, data),
  
  // 删除任务
  delete: (taskId) => apiClient.delete(`/tasks/${taskId}/`),
  
  // 取消任务
  cancel: (taskId) => apiClient.post(`/tasks/${taskId}/cancel/`)
}

/**
 * 报告管理 API
 */
export const reportApi = {
  // 获取报告列表
  list: (params) => apiClient.get('/reports', params),
  
  // 创建报告
  create: (data) => apiClient.post('/reports', data),
  
  // 获取报告详情
  get: (reportId) => apiClient.get(`/reports/${reportId}`),
  
  // 更新报告
  update: (reportId, data) => apiClient.put(`/reports/${reportId}`, data),
  
  // 删除报告
  delete: (reportId) => apiClient.delete(`/reports/${reportId}`),
  
  // 导出报告
  export: (reportId, format = 'json') => apiClient.get(`/reports/${reportId}/export`, { format })
}

/**
 * 系统设置 API
 */
export const settingsApi = {
  // 获取系统设置
  get: () => apiClient.get('/settings'),
  
  // 更新系统设置
  update: (data) => apiClient.put('/settings', data),
  
  // 获取系统信息
  getSystemInfo: () => apiClient.get('/settings/system-info'),
  
  // 获取统计信息
  getStatistics: (params) => apiClient.get('/settings/statistics', params)
}

/**
 * POC 扫描相关 API
 */
export const pocApi = {
  // 获取可用的POC类型列表
  getTypes: () => apiClient.get('/poc/types'),
  
  // 执行POC扫描
  scan: (data) => apiClient.post('/poc/scan', data),
  
  // 获取POC扫描结果
  getResults: (params) => apiClient.get('/poc/results', params),
  
  // 获取POC扫描详情
  getResult: (resultId) => apiClient.get(`/poc/results/${resultId}`),
  
  // 导出POC扫描报告
  exportReport: (resultId, format = 'json') => apiClient.get(`/poc/results/${resultId}/export`, { format })
}

/**
 * 健康检查
 */
export const healthCheck = () => apiClient.get('/health')

export default apiClient

>>>>>>> de97d03d8b5dfa00af0eaddf983e9c20433e9b15
