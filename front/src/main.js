import { createApp } from 'vue'
import { createPinia } from 'pinia'
import 'element-plus/dist/index.css'
import 'element-plus/theme-chalk/dark/css-vars.css'
import './style.css'
import './styles/transitions.css'
import './styles/responsive.css'
import './styles/buttons.css'
import './styles/icons.css'
import App from './App.vue'
import router from './router'
import { ErrorHandlerPlugin } from './utils/errorHandler.js'
import { LoadingPlugin } from './utils/loading.js'

const app = createApp(App)
const pinia = createPinia()

app.use(router)
app.use(pinia)
app.use(ErrorHandlerPlugin)
app.use(LoadingPlugin)

class GlobalErrorHandler {
  constructor() {
    this.errorQueue = []
    this.maxRetries = 3
    this.retryDelay = 1000
    this.isRetrying = false
  }

  handleError(error, context = '') {
    console.error(`[${context}] 全局错误:`, error)
    
    if (this.isNetworkError(error)) {
      return this.handleNetworkError(error, context)
    }
    
    this.showErrorNotification(error, context)
    return false
  }

  isNetworkError(error) {
    if (!error) return false
    
    const networkErrorPatterns = [
      'Network Error',
      'network error',
      'timeout',
      'ECONNREFUSED',
      'ENOTFOUND',
      'ERR_NETWORK',
      'Failed to fetch',
      'fetch failed',
      'NetworkError'
    ]
    
    const errorMessage = error.message || error.toString()
    return networkErrorPatterns.some(pattern => 
      errorMessage.toLowerCase().includes(pattern.toLowerCase())
    )
  }

  async handleNetworkError(error, context) {
    if (this.isRetrying) {
      return false
    }

    this.isRetrying = true
    const errorKey = this.getErrorKey(error, context)
    
    const existingError = this.errorQueue.find(e => e.key === errorKey)
    if (existingError) {
      existingError.retryCount++
    } else {
      this.errorQueue.push({
        key: errorKey,
        error,
        context,
        retryCount: 1,
        timestamp: Date.now()
      })
    }

    const currentError = this.errorQueue.find(e => e.key === errorKey)
    
    if (currentError.retryCount <= this.maxRetries) {
      this.showRetryNotification(currentError)
      
      try {
        await this.delay(this.retryDelay * currentError.retryCount)
        
        if (currentError.retryCount < this.maxRetries) {
          this.isRetrying = false
          return true
        }
      } catch (retryError) {
        console.error('重试失败:', retryError)
      }
    }

    this.showErrorNotification(error, context, true)
    this.isRetrying = false
    return false
  }

  getErrorKey(error, context) {
    return `${context}-${error.message || 'unknown'}`
  }

  delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms))
  }

  showErrorNotification(error, context, isNetworkError = false) {
    const event = new CustomEvent('global-error', {
      detail: {
        error,
        context,
        isNetworkError,
        timestamp: Date.now()
      }
    })
    window.dispatchEvent(event)
  }

  showRetryNotification(errorInfo) {
    const event = new CustomEvent('global-retry', {
      detail: {
        error: errorInfo.error,
        context: errorInfo.context,
        retryCount: errorInfo.retryCount,
        maxRetries: this.maxRetries,
        timestamp: Date.now()
      }
    })
    window.dispatchEvent(event)
  }

  clearErrorQueue() {
    this.errorQueue = []
  }
}

const globalErrorHandler = new GlobalErrorHandler()

app.config.errorHandler = (err, vm, info) => {
  console.error('Vue错误:', err)
  console.error('错误信息:', info)
  
  globalErrorHandler.handleError(err, 'Vue')
  
  if (typeof window !== 'undefined' && window.__VUE_DEVTOOLS_GLOBAL_HOOK__) {
    window.__VUE_DEVTOOLS_GLOBAL_HOOK__.emit('error', err)
  }
}

app.config.warnHandler = (msg, vm, trace) => {
  console.warn('Vue警告:', msg)
  console.warn('追踪:', trace)
}

window.addEventListener('unhandledrejection', (event) => {
  console.error('未处理的Promise拒绝:', event.reason)
  
  const isNetworkError = globalErrorHandler.isNetworkError(event.reason)
  if (isNetworkError) {
    event.preventDefault()
    globalErrorHandler.handleNetworkError(event.reason, 'Promise')
  } else {
    globalErrorHandler.handleError(event.reason, 'Promise')
  }
})

window.addEventListener('error', (event) => {
  console.error('全局错误:', event.error)
  
  if (event.error) {
    globalErrorHandler.handleError(event.error, 'Window')
  }
})

window.addEventListener('offline', () => {
  console.warn('网络连接已断开')
  const event = new CustomEvent('network-status', {
    detail: { online: false, timestamp: Date.now() }
  })
  window.dispatchEvent(event)
})

window.addEventListener('online', () => {
  console.log('网络连接已恢复')
  globalErrorHandler.clearErrorQueue()
  
  const event = new CustomEvent('network-status', {
    detail: { online: true, timestamp: Date.now() }
  })
  window.dispatchEvent(event)
})

window.globalErrorHandler = globalErrorHandler

app.mount('#app')
