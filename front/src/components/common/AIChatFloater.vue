<template>
  <div class="ai-chat-floater">
    <div
      class="floater-button"
      :class="{ 'expanded': isExpanded }"
      @click="toggleChat"
    >
      <el-icon v-if="!isExpanded" :size="28" color="#409EFF">
        <ChatDotRound />
      </el-icon>
      <el-icon v-else :size="28" color="#909399">
        <Close />
      </el-icon>
    </div>

    <transition name="slide-up">
      <div v-if="isExpanded" class="chat-panel">
        <div class="panel-header">
          <div class="header-title">
            <el-icon :size="18" color="#409EFF">
              <ChatDotRound />
            </el-icon>
            <span>AI 对话助手</span>
          </div>
          <div class="header-actions">
            <el-button
              v-if="messages.length > 0"
              link
              type="primary"
              size="small"
              @click="clearHistory"
            >
              清空
            </el-button>
            <el-button
              link
              type="primary"
              size="small"
              @click="toggleChat"
            >
              <el-icon><Close /></el-icon>
            </el-button>
          </div>
        </div>

        <div class="panel-body">
          <div v-if="isLoading" class="loading-state">
            <el-icon :size="32" class="is-loading">
              <Loading />
            </el-icon>
            <p>连接中...</p>
          </div>

          <div v-else-if="messages.length === 0" class="empty-state">
            <el-icon :size="48" color="#C0C4CC">
              <ChatDotRound />
            </el-icon>
            <p>开始与AI助手对话</p>
            <p class="hint">您可以询问漏洞分析、POC生成等问题</p>
          </div>

          <div v-else ref="messagesContainer" class="messages-container">
            <div
              v-for="(message, index) in messages"
              :key="message.id || index"
              :class="['message-item', message.role]"
            >
              <div class="message-avatar">
                <el-avatar v-if="message.role === 'user'" :size="32">
                  <el-icon><User /></el-icon>
                </el-avatar>
                <el-avatar v-else :size="32" color="#409EFF">
                  <el-icon><ChatDotRound /></el-icon>
                </el-avatar>
              </div>
              <div class="message-content">
                <div class="message-info">
                  <span class="message-role">{{ message.role === 'user' ? '我' : 'AI助手' }}</span>
                  <span class="message-time">{{ formatTime(message.timestamp) }}</span>
                </div>
                <div class="message-text">{{ message.content }}</div>
              </div>
            </div>
          </div>
        </div>

        <div class="panel-footer">
          <el-input
            v-model="inputMessage"
            type="textarea"
            :rows="3"
            placeholder="输入您的问题..."
            :disabled="isSending"
            @keydown.enter.exact.prevent="sendMessage"
            @keydown.enter.shift.exact="inputMessage += '\n'"
          />
          <div class="footer-actions">
            <span v-if="isSending" class="sending-hint">
              <el-icon :size="14" class="is-loading">
                <Loading />
              </el-icon>
              发送中...
            </span>
            <el-button
              type="primary"
              :disabled="!inputMessage.trim() || isSending"
              @click="sendMessage"
            >
              发送
              <el-icon class="el-icon--right"><Promotion /></el-icon>
            </el-button>
          </div>
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref, watch, nextTick, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import {
  ChatDotRound,
  Close,
  Loading,
  User,
  Promotion
} from '@element-plus/icons-vue'

const isExpanded = ref(false)
const messages = ref([])
const inputMessage = ref('')
const messagesContainer = ref(null)
const isLoading = ref(false)
const isSending = ref(false)
const ws = ref(null)

const STORAGE_KEY = 'ai_chat_history'

const toggleChat = () => {
  isExpanded.value = !isExpanded.value
  if (isExpanded.value) {
    connectWebSocket()
  } else {
    disconnectWebSocket()
  }
}

const loadHistory = () => {
  try {
    const history = localStorage.getItem(STORAGE_KEY)
    if (history) {
      messages.value = JSON.parse(history)
    }
  } catch (error) {
    console.error('加载聊天历史失败:', error)
  }
}

const saveHistory = () => {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(messages.value))
  } catch (error) {
    console.error('保存聊天历史失败:', error)
  }
}

const clearHistory = () => {
  messages.value = []
  localStorage.removeItem(STORAGE_KEY)
  ElMessage.success('聊天历史已清空')
}

const connectWebSocket = () => {
  if (ws.value && ws.value.readyState === WebSocket.OPEN) {
    return
  }

  isLoading.value = true

  const token = localStorage.getItem('token')
  const wsUrl = `ws://localhost:3000/api/ws?token=${token}`

  try {
    ws.value = new WebSocket(wsUrl)

    ws.value.onopen = () => {
      console.log('AI聊天WebSocket连接成功')
      isLoading.value = false
    }

    ws.value.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        
        if (data.type === 'chat_message' || data.type === 'ai_response') {
          messages.value.push({
            id: Date.now(),
            role: data.role || 'assistant',
            content: data.content || data.message,
            timestamp: new Date()
          })
          
          saveHistory()
          scrollToBottom()
        } else if (data.type === 'error') {
          ElMessage.error(data.message || '发生错误')
          isSending.value = false
        }
      } catch (error) {
        console.error('处理WebSocket消息失败:', error)
        isSending.value = false
      }
    }

    ws.value.onerror = (error) => {
      console.error('WebSocket错误:', error)
      isLoading.value = false
      isSending.value = false
      ElMessage.error('连接失败，请检查网络')
    }

    ws.value.onclose = () => {
      console.log('WebSocket连接关闭')
      isLoading.value = false
      isSending.value = false
    }
  } catch (error) {
    console.error('创建WebSocket连接失败:', error)
    isLoading.value = false
    ElMessage.error('无法建立连接')
  }
}

const disconnectWebSocket = () => {
  if (ws.value) {
    ws.value.close()
    ws.value = null
  }
}

const sendMessage = async () => {
  const message = inputMessage.value.trim()
  if (!message || isSending.value) {
    return
  }

  isSending.value = true

  const userMessage = {
    id: Date.now(),
    role: 'user',
    content: message,
    timestamp: new Date()
  }

  messages.value.push(userMessage)
  saveHistory()
  scrollToBottom()

  inputMessage.value = ''

  try {
    const token = localStorage.getItem('token')
    
    if (ws.value && ws.value.readyState === WebSocket.OPEN) {
      ws.value.send(JSON.stringify({
        type: 'chat_message',
        message: message,
        token: token
      }))
    } else {
      await sendViaAPI(message, token)
    }
  } catch (error) {
    console.error('发送消息失败:', error)
    isSending.value = false
    ElMessage.error('发送失败，请重试')
  }
}

const sendViaAPI = async (message, token) => {
  try {
    const response = await fetch('http://127.0.0.1:3000/api/ai/chat', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({ message })
    })

    const data = await response.json()
    
    if (data.code === 200 && data.data) {
      messages.value.push({
        id: Date.now(),
        role: 'assistant',
        content: data.data.response || data.data.message || '处理完成',
        timestamp: new Date()
      })
      saveHistory()
      scrollToBottom()
    } else {
      throw new Error(data.message || '请求失败')
    }
  } catch (error) {
    console.error('API请求失败:', error)
    ElMessage.error('发送失败，请重试')
  } finally {
    isSending.value = false
  }
}

const scrollToBottom = () => {
  nextTick(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    }
  })
}

const formatTime = (date) => {
  const hours = date.getHours().toString().padStart(2, '0')
  const minutes = date.getMinutes().toString().padStart(2, '0')
  return `${hours}:${minutes}`
}

watch(isExpanded, (newVal) => {
  if (newVal) {
    loadHistory()
    nextTick(() => {
      scrollToBottom()
    })
  }
})

onMounted(() => {
  console.log('AI聊天悬浮球组件已挂载')
})

onUnmounted(() => {
  disconnectWebSocket()
})
</script>

<style scoped>
.ai-chat-floater {
  position: fixed;
  right: 24px;
  bottom: 24px;
  z-index: 9999;
}

.floater-button {
  width: 56px;
  height: 56px;
  border-radius: 50%;
  background: linear-gradient(135deg, #409EFF 0%, #66B1FF 100%);
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.3s ease;
  z-index: 10000;
}

.floater-button:hover {
  transform: scale(1.1);
  box-shadow: 0 6px 16px rgba(64, 158, 255, 0.5);
}

.floater-button.expanded {
  background: linear-gradient(135deg, #909399 0%, #A6A9AD 100%);
  box-shadow: 0 4px 12px rgba(144, 147, 153, 0.4);
}

.chat-panel {
  position: absolute;
  right: 0;
  bottom: 72px;
  width: 400px;
  max-height: 600px;
  background: #ffffff;
  border-radius: 12px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  border-bottom: 1px solid #EBEEF5;
  background: linear-gradient(135deg, #409EFF 0%, #66B1FF 100%);
  color: #ffffff;
}

.header-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 600;
}

.header-actions {
  display: flex;
  gap: 8px;
}

.header-actions .el-button {
  color: #ffffff;
}

.header-actions .el-button:hover {
  color: #ffffff;
  opacity: 0.8;
}

.panel-body {
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  min-height: 300px;
  max-height: 400px;
}

.loading-state,
.empty-state {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
  color: #909399;
}

.loading-state p,
.empty-state p {
  margin-top: 16px;
  font-size: 14px;
}

.empty-state .hint {
  font-size: 12px;
  color: #C0C4CC;
  margin-top: 8px;
}

.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  background: #F5F7FA;
}

.messages-container::-webkit-scrollbar {
  width: 6px;
}

.messages-container::-webkit-scrollbar-thumb {
  background: #DCDFE6;
  border-radius: 3px;
}

.messages-container::-webkit-scrollbar-thumb:hover {
  background: #C0C4CC;
}

.message-item {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
  animation: fadeIn 0.3s ease;
}

.message-item:last-child {
  margin-bottom: 0;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.message-avatar {
  flex-shrink: 0;
}

.message-content {
  flex: 1;
  min-width: 0;
}

.message-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
  font-size: 12px;
}

.message-role {
  font-weight: 600;
  color: #606266;
}

.message-item.user .message-role {
  color: #409EFF;
}

.message-item.assistant .message-role {
  color: #67C23A;
}

.message-time {
  color: #909399;
}

.message-text {
  padding: 10px 14px;
  border-radius: 8px;
  line-height: 1.6;
  word-wrap: break-word;
  font-size: 14px;
  color: #303133;
}

.message-item.user .message-text {
  background: #409EFF;
  color: #ffffff;
}

.message-item.assistant .message-text {
  background: #ffffff;
  border: 1px solid #EBEEF5;
}

.panel-footer {
  padding: 16px;
  border-top: 1px solid #EBEEF5;
  background: #ffffff;
}

.footer-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 12px;
}

.sending-hint {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: #909399;
}

.slide-up-enter-active,
.slide-up-leave-active {
  transition: all 0.3s ease;
}

.slide-up-enter-from {
  opacity: 0;
  transform: translateY(20px);
}

.slide-up-leave-to {
  opacity: 0;
  transform: translateY(20px);
}

@media (max-width: 768px) {
  .ai-chat-floater {
    right: 16px;
    bottom: 16px;
  }

  .floater-button {
    width: 48px;
    height: 48px;
  }

  .chat-panel {
    width: calc(100vw - 32px);
    max-width: 360px;
    right: 0;
    bottom: 64px;
  }

  .panel-body {
    max-height: 350px;
  }
}

@media (max-width: 480px) {
  .chat-panel {
    width: calc(100vw - 16px);
    max-width: none;
    right: 0;
    bottom: 64px;
  }

  .panel-header {
    padding: 12px;
  }

  .header-title {
    font-size: 14px;
  }

  .messages-container {
    padding: 12px;
  }

  .message-text {
    font-size: 13px;
    padding: 8px 12px;
  }

  .panel-footer {
    padding: 12px;
  }
}
</style>