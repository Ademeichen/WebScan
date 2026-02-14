<template>
  <div class="agent-scan">
    <div class="page-header">
      <h1>AI Agent智能扫描</h1>
      <p class="subtitle">使用AI Agent进行自动化安全扫描和漏洞发现</p>
    </div>

    <div class="scan-layout">
      <div class="form-section">
        <AgentScanForm
          @submit="handleSubmit"
          @success="handleSuccess"
          @error="handleError"
        />
      </div>

      <div v-if="recentTasks && recentTasks.length > 0" class="recent-section">
        <h3>最近任务</h3>
        <div class="tasks-list">
          <div
            v-for="task in recentTasks"
            :key="task.task_id"
            class="task-item"
            @click="handleViewTask(task.task_id)"
          >
            <div class="task-header">
              <span class="task-id">{{ String(task.task_id).substring(0, 8) }}...</span>
              <span class="task-status" :class="`status-${task.status}`">
                {{ getStatusText(task.status) }}
              </span>
            </div>
            <div class="task-info">
              <span class="task-target">{{ task.target }}</span>
              <span class="task-time">{{ formatDate(task.created_at) }}</span>
            </div>
            <div v-if="task.status === 'running' || task.status === 'queued'" class="task-progress">
              <div class="progress-bar">
                <div class="progress-fill" :style="{ width: `${task.progress || 0}%` }"></div>
              </div>
              <span class="progress-text">{{ task.progress || 0 }}%</span>
            </div>
            <!-- Stage Summary Mini-view -->
            <div v-if="task.stages" class="stage-mini-summary">
               <span v-for="(stageData, stageName) in task.stages" :key="stageName" 
                     class="stage-dot" 
                     :class="stageData.status"
                     :title="`${stageName}: ${stageData.status}`">
               </span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div v-if="selectedTask" class="task-detail-modal" @click.self="selectedTask = null">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h2>任务详情</h2>
          <button class="btn-close" @click="selectedTask = null">×</button>
        </div>
        <div class="modal-body">
          <div class="detail-section">
            <h3>基本信息</h3>
            <div class="detail-grid">
              <div class="detail-item">
                <span class="detail-label">任务ID:</span>
                <span class="detail-value">{{ selectedTask.task_id }}</span>
              </div>
              <div class="detail-item">
                <span class="detail-label">目标:</span>
                <span class="detail-value">{{ selectedTask.target }}</span>
              </div>
              <div class="detail-item">
                <span class="detail-label">状态:</span>
                <span class="detail-value" :class="`status-${selectedTask.status}`">
                  {{ getStatusText(selectedTask.status) }}
                </span>
              </div>
              <div class="detail-item">
                <span class="detail-label">创建时间:</span>
                <span class="detail-value">{{ formatDate(selectedTask.created_at) }}</span>
              </div>
              <div class="detail-item">
                <span class="detail-label">完成时间:</span>
                <span class="detail-value">{{ formatDate(selectedTask.completed_at) }}</span>
              </div>
            </div>
          </div>

          <!-- Stage Progress Section -->
          <div class="detail-section" v-if="selectedTask.stages">
            <h3>执行阶段</h3>
            <div class="stages-container">
              <div v-for="(stageData, stageName) in selectedTask.stages" :key="stageName" class="stage-item" :class="stageData.status">
                <div class="stage-header">
                  <span class="stage-name">{{ formatStageName(stageName) }}</span>
                  <span class="stage-status-text">{{ getStatusText(stageData.status) }}</span>
                </div>
                <div class="stage-details" v-if="stageData.sub_status || stageData.log">
                   <div v-if="stageData.sub_status" class="sub-status">当前步骤: {{ stageData.sub_status }}</div>
                   <div v-if="stageData.log" class="stage-log">{{ stageData.log }}</div>
                </div>
              </div>
            </div>
          </div>

          <div v-if="selectedTask.result" class="detail-section">
            <h3>扫描结果</h3>
            <div class="result-content">
              <div v-if="selectedTask.result.final_output" class="result-json">
                <pre>{{ JSON.stringify(selectedTask.result.final_output, null, 2) }}</pre>
              </div>
              <div v-if="selectedTask.result.execution_time" class="result-info">
                <span class="info-label">执行时间:</span>
                <span class="info-value">{{ selectedTask.result.execution_time }}秒</span>
              </div>
            </div>
          </div>

          <div v-if="selectedTask.error_message" class="detail-section error-section">
            <h3>错误信息</h3>
            <div class="error-message">{{ selectedTask.error_message }}</div>
          </div>
        </div>
      </div>
    </div>

    <Alert
      v-if="errorMessage"
      type="error"
      :message="errorMessage"
      @close="errorMessage = ''"
    />

    <Alert
      v-if="successMessage"
      type="success"
      :message="successMessage"
      @close="successMessage = ''"
    />
  </div>
</template>

<script>
import { ref, onMounted, onUnmounted } from 'vue'
import { aiAgentsApi } from '@/utils/aiAgents'
import AgentScanForm from '@/components/business/AgentScanForm.vue'
import Alert from '@/components/common/Alert.vue'
import { formatDate } from '@/utils/date'
import { useWebSocket } from '@/utils/websocket'

export default {
  name: 'AgentScan',
  components: {
    AgentScanForm,
    Alert
  },
  setup() {
    const errorMessage = ref('')
    const successMessage = ref('')
    const recentTasks = ref([])
    const selectedTask = ref(null)

    // Use WebSocket composable
    // Use hardcoded URL for now, or get from environment/config if available
    // Assuming backend runs on localhost:3000 based on config.py
    const { connect, on, disconnect } = useWebSocket('ws://localhost:3000/api/ws')

    const loadRecentTasks = async () => {
      try {
        const response = await aiAgentsApi.getTasks({ page: 1, page_size: 10 })
        let tasks = []
        if (response && response.data && response.data.tasks) {
          tasks = response.data.tasks
        } else if (response && response.tasks) {
          tasks = response.tasks
        } else if (response && Array.isArray(response)) {
          tasks = response
        }
        
        // Initialize stages for existing tasks if not present
        recentTasks.value = tasks.map(task => ({
          ...task,
          task_id: String(task.task_id || task.id),
          stages: task.stages || {
            openai: { status: 'pending' },
            plugins: { status: 'pending' },
            awvs: { status: 'pending' },
            pocsuite3: { status: 'pending' }
          }
        }))
      } catch (error) {
        console.error('加载最近任务失败:', error)
        if (error.response && error.response.status === 500) {
          console.warn('后端服务暂时不可用，使用空任务列表')
          recentTasks.value = []
        } else {
          recentTasks.value = []
        }
      }
    }

    const handleSubmit = () => {
      console.log('提交Agent扫描')
    }

    const handleSuccess = () => {
      successMessage.value = 'AI Agent扫描任务创建成功'
      // loadRecentTasks() // WebSocket will handle updates
    }

    const handleError = (error) => {
      errorMessage.value = error.message || '创建AI Agent扫描任务失败'
    }

    const handleViewTask = (taskId) => {
      const task = recentTasks.value.find(t => t.task_id === taskId)
      if (task) {
        selectedTask.value = task
      }
    }

    const getStatusText = (status) => {
      const statusMap = {
        pending: '等待中',
        queued: '队列中',
        running: '运行中',
        completed: '已完成',
        failed: '失败',
        cancelled: '已取消'
      }
      return statusMap[status] || status
    }

    const formatStageName = (name) => {
      const map = {
        openai: 'AI分析规划',
        plugins: '插件执行',
        awvs: '漏洞扫描',
        pocsuite3: 'POC验证'
      }
      return map[name] || name
    }

    // WebSocket Handlers
    const updateTaskStatus = (taskId, payload) => {
      taskId = String(taskId)
      const taskIndex = recentTasks.value.findIndex(t => t.task_id === taskId)
      if (taskIndex !== -1) {
        recentTasks.value[taskIndex] = { ...recentTasks.value[taskIndex], ...payload }
        if (selectedTask.value && selectedTask.value.task_id === taskId) {
           selectedTask.value = { ...selectedTask.value, ...payload }
        }
      } else if (payload.status === 'queued') {
        // New task
        const newTask = {
          task_id: taskId,
          target: payload.target || 'Unknown', // Ideally payload has target
          status: 'queued',
          created_at: new Date().toISOString(),
          progress: 0,
          stages: {
            openai: { status: 'pending' },
            plugins: { status: 'pending' },
            awvs: { status: 'pending' },
            pocsuite3: { status: 'pending' }
          }
        }
        recentTasks.value.unshift(newTask)
      }
    }

    const updateTaskProgress = (taskId, progress) => {
      taskId = String(taskId)
      const task = recentTasks.value.find(t => t.task_id === taskId)
      if (task) {
        task.progress = progress
      }
    }

    const updateTaskCompleted = (taskId, payload) => {
      taskId = String(taskId)
      const taskIndex = recentTasks.value.findIndex(t => t.task_id === taskId)
      if (taskIndex !== -1) {
        const result = payload.result || {}
        const stages = result.stages || recentTasks.value[taskIndex].stages
        
        const updatedTask = {
            ...recentTasks.value[taskIndex],
            status: 'completed',
            progress: 100,
            result: result,
            stages: stages,
            completed_at: payload.completed_at
        }
        recentTasks.value[taskIndex] = updatedTask
        if (selectedTask.value && selectedTask.value.task_id === taskId) {
            selectedTask.value = updatedTask
        }
      }
    }
    
    const updateTaskFailed = (taskId, error) => {
      taskId = String(taskId)
      const taskIndex = recentTasks.value.findIndex(t => t.task_id === taskId)
      if (taskIndex !== -1) {
        const updatedTask = {
             ...recentTasks.value[taskIndex],
             status: 'failed',
             error_message: error
        }
        recentTasks.value[taskIndex] = updatedTask
        if (selectedTask.value && selectedTask.value.task_id === taskId) {
            selectedTask.value = updatedTask
        }
      }
    }

    const updateTaskStage = (taskId, stage, data) => {
      taskId = String(taskId)
      const task = recentTasks.value.find(t => t.task_id === taskId)
      if (task) {
        if (!task.stages) task.stages = {}
        task.stages[stage] = { ...task.stages[stage], ...data }
        
        // Update selectedTask if it matches
        if (selectedTask.value && selectedTask.value.task_id === taskId) {
           if (!selectedTask.value.stages) selectedTask.value.stages = {}
           selectedTask.value.stages[stage] = { ...selectedTask.value.stages[stage], ...data }
           // Force reactivity update if needed (Vue 3 ref should handle deep changes, but sometimes replacing the object is safer)
           selectedTask.value = { ...selectedTask.value }
        }
      }
    }

    onMounted(() => {
      loadRecentTasks()
      
      // Connect WebSocket
      connect()
      
      on('task:update', (payload) => {
        updateTaskStatus(payload.task_id || payload.payload.task_id, payload.payload || payload)
      })
      
      on('task:progress', (payload) => {
        updateTaskProgress(payload.payload.task_id, payload.payload.progress)
      })
      
      on('task:completed', (payload) => {
        updateTaskCompleted(payload.payload.task_id, payload.payload)
      })
      
      on('task:failed', (payload) => {
        updateTaskFailed(payload.payload.task_id, payload.payload.error)
      })

      on('stage:update', (payload) => {
         updateTaskStage(payload.task_id, payload.stage, payload.data)
      })
    })
    
    onUnmounted(() => {
      disconnect()
    })

    return {
      errorMessage,
      successMessage,
      recentTasks,
      selectedTask,
      handleSubmit,
      handleSuccess,
      handleError,
      handleViewTask,
      getStatusText,
      formatDate,
      formatStageName
    }
  }
}
</script>

<style scoped>
.agent-scan {
  padding: var(--spacing-xl);

  /* Fix: Map missing CSS variables to global styles */
  --card-bg: var(--card-background);
  --bg-secondary: var(--el-fill-color-light);
  --bg-primary: var(--el-fill-color);
  
  --color-primary: var(--el-color-primary);
  --color-success: var(--el-color-success);
  --color-warning: var(--el-color-warning);
  --color-error: var(--el-color-danger);
  --color-info: var(--el-color-info);
  
  --color-primary-bg: var(--el-color-primary-light-9);
  --color-success-bg: var(--el-color-success-light-9);
  --color-warning-bg: var(--el-color-warning-light-9);
  --color-error-bg: var(--el-color-danger-light-9);
  --color-info-bg: var(--el-color-info-light-9);

  --color-accent: #9b59b6;
}

.page-header {
  margin-bottom: var(--spacing-xl);
}

.page-header h1 {
  margin: 0 0 var(--spacing-sm) 0;
  font-size: 2rem;
  color: var(--text-primary);
}

.subtitle {
  margin: 0;
  color: var(--text-secondary);
  font-size: 1rem;
}

.scan-layout {
  display: grid;
  grid-template-columns: 1fr 350px;
  gap: var(--spacing-xl);
}

.form-section {
  min-width: 0;
}

.recent-section {
  background-color: var(--card-bg);
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius-lg);
  padding: var(--spacing-lg);
}

.recent-section h3 {
  margin: 0 0 var(--spacing-lg) 0;
  font-size: 1.25rem;
  color: var(--text-primary);
  padding-bottom: var(--spacing-md);
  border-bottom: 1px solid var(--border-color);
}

.tasks-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
  margin-top: var(--spacing-md);
}

.task-item {
  padding: var(--spacing-md);
  background-color: var(--bg-secondary);
  border-radius: var(--border-radius);
  cursor: pointer;
  transition: all 0.3s;
  border: 1px solid transparent;
}

.task-item:hover {
  background-color: var(--color-primary-bg);
  border-color: var(--color-primary);
  transform: translateX(4px);
  box-shadow: var(--shadow-sm);
}

.task-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-sm);
}

.task-id {
  font-family: monospace;
  font-size: 0.875rem;
  color: var(--text-secondary);
}

.task-status {
  padding: var(--spacing-xs) var(--spacing-sm);
  border-radius: var(--border-radius-sm);
  font-size: 0.75rem;
  font-weight: 500;
}

.status-pending {
  background-color: var(--color-warning-bg);
  color: var(--color-warning);
}

.status-queued {
    background-color: var(--color-info-bg);
    color: var(--color-info);
    opacity: 0.8;
}

.status-running {
  background-color: var(--color-info-bg);
  color: var(--color-info);
}

.status-completed {
  background-color: var(--color-success-bg);
  color: var(--color-success);
}

.status-failed,
.status-cancelled {
  background-color: var(--color-error-bg);
  color: var(--color-error);
}

.task-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.875rem;
  margin-bottom: var(--spacing-sm);
}

.task-target {
  color: var(--text-primary);
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.task-time {
  color: var(--text-secondary);
}

.task-progress {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
}

.progress-bar {
  flex: 1;
  height: 6px;
  background-color: var(--border-color);
  border-radius: 3px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--color-primary), var(--color-accent));
  transition: width 0.3s;
}

.progress-text {
  min-width: 40px;
  font-size: 0.75rem;
  color: var(--text-secondary);
  text-align: right;
}

.stage-mini-summary {
    display: flex;
    gap: 4px;
    margin-top: 8px;
}
.stage-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background-color: var(--border-color);
}
.stage-dot.running { background-color: var(--color-info); animation: pulse 1.5s infinite; }
.stage-dot.completed { background-color: var(--color-success); }
.stage-dot.failed { background-color: var(--color-error); }

@keyframes pulse {
    0% { opacity: 0.5; transform: scale(0.9); }
    50% { opacity: 1; transform: scale(1.1); }
    100% { opacity: 0.5; transform: scale(0.9); }
}

.task-detail-modal {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
  padding: var(--spacing-lg);
}

.modal-content {
  background-color: var(--card-bg);
  border-radius: var(--border-radius-lg);
  max-width: 800px;
  width: 100%;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: var(--shadow-lg);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-lg);
  border-bottom: 1px solid var(--border-color);
}

.modal-header h2 {
  margin: 0;
  font-size: 1.25rem;
  color: var(--text-primary);
}

.btn-close {
  background: none;
  border: none;
  font-size: 2rem;
  color: var(--text-secondary);
  cursor: pointer;
  padding: 0;
  line-height: 1;
  transition: color 0.3s;
}

.btn-close:hover {
  color: var(--text-primary);
}

.modal-body {
  padding: var(--spacing-lg);
}

.detail-section {
  margin-bottom: var(--spacing-lg);
}

.detail-section h3 {
  margin: 0 0 var(--spacing-md) 0;
  font-size: 1rem;
  color: var(--text-primary);
  padding-bottom: var(--spacing-sm);
  border-bottom: 1px solid var(--border-color);
}

.detail-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: var(--spacing-md);
}

.detail-item {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
}

.detail-label {
  font-size: 0.875rem;
  color: var(--text-secondary);
  font-weight: 500;
}

.detail-value {
  font-size: 1rem;
  color: var(--text-primary);
  word-break: break-all;
}

/* Stage Styles */
.stages-container {
    display: flex;
    flex-direction: column;
    gap: 12px;
}
.stage-item {
    border: 1px solid var(--border-color);
    border-radius: 6px;
    padding: 12px;
    background: var(--bg-secondary);
}
.stage-item.running { border-left: 4px solid var(--color-info); }
.stage-item.completed { border-left: 4px solid var(--color-success); }
.stage-item.failed { border-left: 4px solid var(--color-error); }

.stage-header {
    display: flex;
    justify-content: space-between;
    font-weight: 600;
    margin-bottom: 4px;
}
.sub-status {
    font-size: 0.85rem;
    color: var(--text-secondary);
}
.stage-log {
    margin-top: 8px;
    font-family: monospace;
    font-size: 0.8rem;
    background: var(--bg-primary);
    padding: 8px;
    border-radius: 4px;
    white-space: pre-wrap;
    max-height: 100px;
    overflow-y: auto;
}

.result-content {
  background-color: var(--bg-secondary);
  border-radius: var(--border-radius);
  padding: var(--spacing-md);
}

.result-json {
  margin-bottom: var(--spacing-md);
}

.result-json pre {
  margin: 0;
  padding: var(--spacing-md);
  background-color: var(--bg-primary);
  border-radius: var(--border-radius);
  font-size: 0.875rem;
  overflow-x: auto;
}

.result-info {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
}

.info-label {
  font-size: 0.875rem;
  color: var(--text-secondary);
  font-weight: 500;
}

.info-value {
  font-size: 1rem;
  color: var(--text-primary);
  font-weight: 600;
}

.error-section {
  background-color: var(--color-error-bg);
  border: 1px solid var(--color-error);
  border-radius: var(--border-radius);
  padding: var(--spacing-md);
}

.error-section h3 {
  color: var(--color-error);
}

.error-message {
  color: var(--color-error);
  font-size: 0.875rem;
  line-height: 1.6;
}

@media (max-width: 1024px) {
  .scan-layout {
    grid-template-columns: 1fr;
  }
}
</style>
