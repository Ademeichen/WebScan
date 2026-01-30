<<<<<<< HEAD
=======
<<<<<<< HEAD
>>>>>>> origin/renruipeng
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import './style.css'
import App from './App.vue'
import router from './router'
import { ErrorHandlerPlugin } from './utils/errorHandler.js'
import { LoadingPlugin } from './utils/loading.js'

const app = createApp(App)
const pinia = createPinia()

// 注册全局插件
app.use(router)
app.use(pinia)
app.use(ErrorHandlerPlugin)
app.use(LoadingPlugin)

// 全局错误捕获
window.addEventListener('unhandledrejection', (event) => {
  console.error('未处理的Promise拒绝:', event.reason)
  event.preventDefault()
})

window.addEventListener('error', (event) => {
  console.error('全局错误:', event.error)
})

app.mount('#app')
<<<<<<< HEAD
=======
=======
import { createApp } from 'vue'
import './style.css'
import App from './App.vue'
import router from './router'
import { ErrorHandlerPlugin } from './utils/errorHandler.js'
import { LoadingPlugin } from './utils/loading.js'

const app = createApp(App)

// 注册全局插件
app.use(router)
app.use(ErrorHandlerPlugin)
app.use(LoadingPlugin)

// 全局错误捕获
window.addEventListener('unhandledrejection', (event) => {
  console.error('未处理的Promise拒绝:', event.reason)
  event.preventDefault()
})

window.addEventListener('error', (event) => {
  console.error('全局错误:', event.error)
})

app.mount('#app')
>>>>>>> de97d03d8b5dfa00af0eaddf983e9c20433e9b15
>>>>>>> origin/renruipeng
