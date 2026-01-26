import { createApp, ref } from 'vue'
import Toast from '@/components/common/Toast.vue'

let toastInstance = null
let toastContainer = null

const createToastContainer = () => {
  if (!toastContainer) {
    toastContainer = document.createElement('div')
    toastContainer.id = 'toast-container'
    toastContainer.style.cssText = `
      position: fixed;
      top: 0;
      left: 0;
      right: 0;
      z-index: 9999;
      pointer-events: none;
    `
    document.body.appendChild(toastContainer)
  }
  return toastContainer
}

const showToast = (options) => {
  const container = createToastContainer()

  const toastApp = createApp(Toast, {
    ...options,
    visible: true
  })

  const toastElement = document.createElement('div')
  container.appendChild(toastElement)
  
  const toastVM = toastApp.mount(toastElement)

  toastApp.unmount()
  container.removeChild(toastElement)
}

const toast = {
  success(title, message, duration = 3000) {
    showToast({
      type: 'success',
      title,
      message,
      duration
    })
  },

  error(title, message, duration = 5000) {
    showToast({
      type: 'error',
      title,
      message,
      duration
    })
  },

  warning(title, message, duration = 4000) {
    showToast({
      type: 'warning',
      title,
      message,
      duration
    })
  },

  info(title, message, duration = 3000) {
    showToast({
      type: 'info',
      title,
      message,
      duration
    })
  }
}

export default toast
