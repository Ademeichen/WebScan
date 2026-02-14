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

window.addEventListener('unhandledrejection', (event) => {
  console.error('未处理的Promise拒绝:', event.reason)
  event.preventDefault()
})

window.addEventListener('error', (event) => {
  console.error('全局错误:', event.error)
})

app.mount('#app')
