import { request } from './api'

const MAX_RETRIES = 3
const RETRY_DELAY = 1000
const BACKOFF_FACTOR = 2

async function requestWithRetry(config, retries = MAX_RETRIES) {
  let lastError = null
  let delay = RETRY_DELAY
  
  for (let i = 0; i <= retries; i++) {
    try {
      return await request(config)
    } catch (error) {
      lastError = error
      if (i < retries && isRetryableError(error)) {
        console.log(`请求失败，${delay}ms后重试 (${i + 1}/${retries})`)
        await new Promise(resolve => setTimeout(resolve, delay))
        delay *= BACKOFF_FACTOR
      } else {
        break
      }
    }
  }
  throw lastError
}

function isRetryableError(error) {
  if (!error.response) return true
  const status = error.response.status
  return status >= 500 || status === 429 || status === 408
}

export const aiAgentsApi = {
  executeAgent: async (data) => {
    return requestWithRetry({
      url: '/ai_agents/scan',
      method: 'post',
      data
    })
  },

  getTask: async (taskId) => {
    return requestWithRetry({
      url: `/agent/tasks/${taskId}`,
      method: 'get'
    })
  },

  getTasks: async (params = {}) => {
    return requestWithRetry({
      url: '/agent/tasks',
      method: 'get',
      params
    })
  },

  cancelTask: async (taskId) => {
    return requestWithRetry({
      url: `/agent/tasks/${taskId}`,
      method: 'delete'
    })
  },

  getTools: async (params = {}) => {
    return requestWithRetry({
      url: '/ai_agents/tools',
      method: 'get',
      params
    })
  },

  getConfig: async () => {
    return requestWithRetry({
      url: '/ai_agents/config',
      method: 'get'
    })
  },

  updateConfig: async (data) => {
    return requestWithRetry({
      url: '/ai_agents/config',
      method: 'post',
      data
    })
  },

  startScan: async (data) => {
    return requestWithRetry({
      url: '/ai_agents/scan',
      method: 'post',
      data
    })
  },

  generateCode: async (data) => {
    return requestWithRetry({
      url: '/ai_agents/code/generate',
      method: 'post',
      data
    })
  },

  executeCode: async (data) => {
    return requestWithRetry({
      url: '/ai_agents/code/execute',
      method: 'post',
      data
    })
  },

  generateAndExecuteCode: async (data) => {
    return requestWithRetry({
      url: '/ai_agents/code/generate-and-execute',
      method: 'post',
      data
    })
  },

  enhanceCapability: async (data) => {
    return requestWithRetry({
      url: '/ai_agents/capabilities/enhance',
      method: 'post',
      data
    })
  },

  getCapabilities: async () => {
    return requestWithRetry({
      url: '/ai_agents/capabilities/list',
      method: 'get'
    })
  },

  getCapability: async (capabilityName) => {
    return requestWithRetry({
      url: `/ai_agents/capabilities/${capabilityName}`,
      method: 'get'
    })
  },

  deleteCapability: async (capabilityName) => {
    return requestWithRetry({
      url: `/ai_agents/capabilities/${capabilityName}`,
      method: 'delete'
    })
  },

  getEnvironmentInfo: async () => {
    return requestWithRetry({
      url: '/ai_agents/environment/info',
      method: 'get'
    })
  },

  getEnvironmentTools: async () => {
    return requestWithRetry({
      url: '/ai_agents/environment/tools',
      method: 'get'
    })
  },

  getToolInfo: async (toolName) => {
    return requestWithRetry({
      url: `/ai_agents/environment/tools/${toolName}`,
      method: 'get'
    })
  },

  executeSubgraph: async (subgraphType, data) => {
    return requestWithRetry({
      url: `/subgraphs/${subgraphType}`,
      method: 'post',
      data
    })
  },

  getSubgraphStatus: async (taskId, subgraphType) => {
    return requestWithRetry({
      url: `/subgraphs/${subgraphType}/status/${taskId}`,
      method: 'get'
    })
  },

  getSubgraphResult: async (taskId, subgraphType) => {
    return requestWithRetry({
      url: `/subgraphs/${subgraphType}/result/${taskId}`,
      method: 'get'
    })
  },

  executeFullScan: async (data) => {
    return requestWithRetry({
      url: '/subgraphs/full-scan',
      method: 'post',
      data
    })
  },

  executePlanning: async (data) => {
    return requestWithRetry({
      url: '/subgraphs/planning',
      method: 'post',
      data
    })
  },

  executeToolScan: async (data) => {
    return requestWithRetry({
      url: '/subgraphs/tool-scan',
      method: 'post',
      data
    })
  },

  executePOCVerification: async (data) => {
    return requestWithRetry({
      url: '/subgraphs/poc-verification',
      method: 'post',
      data
    })
  },

  generateReport: async (data) => {
    return requestWithRetry({
      url: '/subgraphs/report',
      method: 'post',
      data
    })
  },

  getToolRecommendations: async (target, context = {}) => {
    return requestWithRetry({
      url: '/ai_agents/tools/recommend',
      method: 'post',
      data: { target, context }
    })
  },

  getPluginMatches: async (target) => {
    return requestWithRetry({
      url: '/ai_agents/plugins/match',
      method: 'post',
      data: { target }
    })
  },

  getExecutionPlan: async (plugins) => {
    return requestWithRetry({
      url: '/ai_agents/plugins/execution-plan',
      method: 'post',
      data: { plugins }
    })
  },

  getSubgraphHealth: async () => {
    return requestWithRetry({
      url: '/subgraphs/health',
      method: 'get'
    })
  },

  getResourceUsage: async () => {
    return requestWithRetry({
      url: '/ai_agents/resources/usage',
      method: 'get'
    })
  },

  getResourceStatistics: async () => {
    return requestWithRetry({
      url: '/ai_agents/resources/statistics',
      method: 'get'
    })
  }
}

export class ProgressWatcher {
  constructor(wsUrl, options = {}) {
    this.wsUrl = wsUrl
    this.ws = null
    this.reconnectAttempts = 0
    this.maxReconnectAttempts = options.maxReconnectAttempts || 5
    this.reconnectDelay = options.reconnectDelay || 1000
    this.callbacks = new Map()
    this.isConnected = false
  }

  connect() {
    if (this.ws) {
      this.ws.close()
    }

    try {
      this.ws = new WebSocket(this.wsUrl)

      this.ws.onopen = () => {
        console.log('WebSocket连接已建立')
        this.isConnected = true
        this.reconnectAttempts = 0
        this.emit('connected')
      }

      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          this.handleMessage(data)
        } catch (error) {
          console.error('解析WebSocket消息失败:', error)
        }
      }

      this.ws.onclose = () => {
        console.log('WebSocket连接已关闭')
        this.isConnected = false
        this.emit('disconnected')
        this.attemptReconnect()
      }

      this.ws.onerror = (error) => {
        console.error('WebSocket错误:', error)
        this.emit('error', error)
      }
    } catch (error) {
      console.error('创建WebSocket连接失败:', error)
      this.attemptReconnect()
    }
  }

  handleMessage(data) {
    const { type, payload } = data

    switch (type) {
      case 'task:update':
        this.emit('taskUpdate', payload)
        break
      case 'task:progress':
        this.emit('taskProgress', payload)
        break
      case 'task:completed':
        this.emit('taskCompleted', payload)
        break
      case 'task:failed':
        this.emit('taskFailed', payload)
        break
      case 'stage:update':
        this.emit('stageUpdate', payload)
        break
      case 'subgraph:progress':
        this.emit('subgraphProgress', payload)
        break
      case 'tool:execution':
        this.emit('toolExecution', payload)
        break
      default:
        this.emit('message', data)
    }
  }

  attemptReconnect() {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('WebSocket重连失败，已达最大重试次数')
      this.emit('reconnectFailed')
      return
    }

    this.reconnectAttempts++
    const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1)
    console.log(`${delay}ms后尝试重连 (${this.reconnectAttempts}/${this.maxReconnectAttempts})`)

    setTimeout(() => {
      this.connect()
    }, delay)
  }

  on(event, callback) {
    if (!this.callbacks.has(event)) {
      this.callbacks.set(event, [])
    }
    this.callbacks.get(event).push(callback)
  }

  off(event, callback) {
    if (!this.callbacks.has(event)) return
    const callbacks = this.callbacks.get(event)
    const index = callbacks.indexOf(callback)
    if (index > -1) {
      callbacks.splice(index, 1)
    }
  }

  emit(event, data) {
    if (!this.callbacks.has(event)) return
    this.callbacks.get(event).forEach(callback => {
      try {
        callback(data)
      } catch (error) {
        console.error(`事件回调执行失败 [${event}]:`, error)
      }
    })
  }

  send(type, payload) {
    if (!this.isConnected || !this.ws) {
      console.warn('WebSocket未连接，无法发送消息')
      return false
    }

    try {
      this.ws.send(JSON.stringify({ type, payload }))
      return true
    } catch (error) {
      console.error('发送WebSocket消息失败:', error)
      return false
    }
  }

  subscribeTask(taskId) {
    return this.send('subscribe', { task_id: taskId })
  }

  unsubscribeTask(taskId) {
    return this.send('unsubscribe', { task_id: taskId })
  }

  disconnect() {
    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
    this.isConnected = false
    this.callbacks.clear()
  }
}

export function createProgressWatcher(wsUrl, options = {}) {
  return new ProgressWatcher(wsUrl, options)
}

export default {
  ...aiAgentsApi,
  ProgressWatcher,
  createProgressWatcher
}
