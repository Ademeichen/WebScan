import { request } from './api'

export const aiAgentsApi = {
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
      url: `/ai_agents/tasks/${taskId}`,
      method: 'delete'
    })
  },

  getTools: async (params = {}) => {
    return request({
      url: '/ai_agents/tools',
      method: 'get',
      params
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
  }
}
