import { ref, onMounted, onUnmounted } from 'vue'

class WebSocketManager {
  constructor(url, options = {}) {
    this.url = url
    this.options = {
      reconnect: true,
      reconnectInterval: 3000,
      maxReconnectAttempts: 5,
      heartbeatInterval: 30000,
      ...options
    }
    
    this.ws = null
    this.reconnectAttempts = 0
    this.heartbeatTimer = null
    this.reconnectTimer = null
    this.messageQueue = []
    this.eventHandlers = new Map()
    this.isConnected = ref(false)
    this.isConnecting = ref(false)
  }

  connect() {
    if (this.isConnecting.value || this.isConnected.value) {
      return
    }

    this.isConnecting.value = true

    try {
      this.ws = new WebSocket(this.url)
      this.setupEventListeners()
    } catch (error) {
      console.error('WebSocket连接失败:', error)
      this.handleConnectionError(error)
    }
  }

  setupEventListeners() {
    this.ws.onopen = () => {
      console.log('WebSocket连接成功')
      this.isConnected.value = true
      this.isConnecting.value = false
      this.reconnectAttempts = 0
      
      this.startHeartbeat()
      this.flushMessageQueue()
      
      this.emit('connected')
    }

    this.ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        this.handleMessage(data)
      } catch (error) {
        console.error('WebSocket消息解析失败:', error)
      }
    }

    this.ws.onerror = (error) => {
      console.error('WebSocket错误:', error)
      this.emit('error', error)
    }

    this.ws.onclose = (event) => {
      console.log('WebSocket连接关闭:', event.code, event.reason)
      this.isConnected.value = false
      this.isConnecting.value = false
      
      this.stopHeartbeat()
      this.emit('disconnected', event)
      
      if (this.options.reconnect && !event.wasClean) {
        this.scheduleReconnect()
      }
    }
  }

  handleMessage(data) {
    const { type, payload } = data
    
    switch (type) {
      case 'task_update':
        this.emit('task:update', payload)
        break
      case 'task_progress':
        this.emit('task:progress', payload)
        break
      case 'task_completed':
        this.emit('task:completed', payload)
        break
      case 'stage_update':
        this.emit('stage:update', payload)
        break
      case 'task_failed':
        this.emit('task:failed', payload)
        break
      case 'vulnerability_found':
        this.emit('vulnerability:found', payload)
        break
      case 'scan_started':
        this.emit('scan:started', payload)
        break
      case 'scan_stopped':
        this.emit('scan:stopped', payload)
        break
      case 'notification':
        this.emit('notification', payload)
        break
      case 'heartbeat':
        this.handleHeartbeat()
        break
      default:
        this.emit('message', data)
    }
  }

  on(event, handler) {
    if (!this.eventHandlers.has(event)) {
      this.eventHandlers.set(event, [])
    }
    this.eventHandlers.get(event).push(handler)
  }

  off(event, handler) {
    if (!this.eventHandlers.has(event)) return
    
    const handlers = this.eventHandlers.get(event)
    const index = handlers.indexOf(handler)
    if (index > -1) {
      handlers.splice(index, 1)
    }
  }

  emit(event, data) {
    const handlers = this.eventHandlers.get(event)
    if (handlers) {
      handlers.forEach(handler => handler(data))
    }
  }

  send(type, payload = {}) {
    const message = JSON.stringify({ type, payload })
    
    if (this.isConnected.value) {
      this.ws.send(message)
    } else {
      this.messageQueue.push(message)
    }
  }

  flushMessageQueue() {
    while (this.messageQueue.length > 0 && this.isConnected.value) {
      const message = this.messageQueue.shift()
      this.ws.send(message)
    }
  }

  startHeartbeat() {
    if (this.options.heartbeatInterval > 0) {
      this.heartbeatTimer = setInterval(() => {
        this.send('heartbeat')
      }, this.options.heartbeatInterval)
    }
  }

  stopHeartbeat() {
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer)
      this.heartbeatTimer = null
    }
  }

  handleHeartbeat() {
    console.log('收到心跳响应')
  }

  scheduleReconnect() {
    if (this.reconnectAttempts >= this.options.maxReconnectAttempts) {
      console.error('WebSocket重连次数超过最大限制')
      this.emit('reconnect_failed')
      return
    }

    this.reconnectAttempts++
    const delay = this.options.reconnectInterval * this.reconnectAttempts
    
    console.log(`WebSocket将在${delay}ms后尝试第${this.reconnectAttempts}次重连`)
    
    this.reconnectTimer = setTimeout(() => {
      this.connect()
    }, delay)
  }

  handleConnectionError(error) {
    this.isConnecting.value = false
    this.emit('error', error)
    
    if (this.options.reconnect) {
      this.scheduleReconnect()
    }
  }

  disconnect() {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer)
      this.reconnectTimer = null
    }
    
    this.stopHeartbeat()
    
    if (this.ws) {
      this.ws.close(1000, '客户端主动断开')
      this.ws = null
    }
    
    this.isConnected.value = false
    this.isConnecting.value = false
    this.messageQueue = []
  }

  getStatus() {
    return {
      connected: this.isConnected.value,
      connecting: this.isConnecting.value,
      reconnectAttempts: this.reconnectAttempts
    }
  }
}

export function useWebSocket(url, options = {}) {
  const wsManager = new WebSocketManager(url, options)
  
  onMounted(() => {
    wsManager.connect()
  })
  
  onUnmounted(() => {
    wsManager.disconnect()
  })
  
  return {
    isConnected: wsManager.isConnected,
    isConnecting: wsManager.isConnecting,
    connect: () => wsManager.connect(),
    disconnect: () => wsManager.disconnect(),
    send: (type, payload) => wsManager.send(type, payload),
    on: (event, handler) => wsManager.on(event, handler),
    off: (event, handler) => wsManager.off(event, handler),
    getStatus: () => wsManager.getStatus()
  }
}

export default {
  WebSocketManager,
  useWebSocket
}
