import { request } from './api'

export const aiAgentsApi = {
  executeAgent: async (data) => {
    return request({
      url: '/agent/run',
      method: 'post',
      data
    })
  },

  getTask: async (taskId) => {
    return request({
      url: `/agent/tasks/${taskId}`,
      method: 'get'
    })
  },

  getTasks: async (params = {}) => {
    return request({
      url: '/agent/tasks',
      method: 'get',
      params
    })
  },

  cancelTask: async (taskId) => {
    return request({
      url: `/agent/tasks/${taskId}`,
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

  startScan: async (data) => {
    return request({
      url: '/ai_agents/scan',
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

  getCapabilities: async () => {
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

  getToolInfo: async (toolName) => {
    return request({
      url: `/ai_agents/environment/tools/${toolName}`,
      method: 'get'
    })
  }
}
