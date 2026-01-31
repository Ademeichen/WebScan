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

      <div v-if="recentTasks.length > 0" class="recent-section">
        <h3>最近任务</h3>
        <div class="tasks-list">
          <div
            v-for="task in recentTasks"
            :key="task.task_id"
            class="task-item"
            @click="handleViewTask(task.task_id)"
          >
            <div class="task-header">
              <span class="task-id">{{ task.task_id.substring(0, 8) }}...</span>
              <span class="task-status" :class="`status-${task.status}`">
                {{ getStatusText(task.status) }}
              </span>
            </div>
            <div class="task-info">
              <span class="task-target">{{ task.target }}</span>
              <span class="task-time">{{ formatDate(task.created_at) }}</span>
            </div>
            <div v-if="task.status === 'running'" class="task-progress">
              <div class="progress-bar">
                <div class="progress-fill" :style="{ width: `${task.progress || 0}%` }"></div>
              </div>
              <span class="progress-text">{{ task.progress || 0 }}%</span>
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
    let refreshInterval = null

    const loadRecentTasks = async () => {
      try {
        const response = await aiAgentsApi.getTasks({ page: 1, page_size: 10 })
        if (response && response.data && response.data.tasks) {
          recentTasks.value = response.data.tasks
        } else if (response && response.tasks) {
          recentTasks.value = response.tasks
        } else if (response && Array.isArray(response)) {
          recentTasks.value = response
        } else {
          recentTasks.value = []
        }
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
      loadRecentTasks()
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
        running: '运行中',
        completed: '已完成',
        failed: '失败',
        cancelled: '已取消'
      }
      return statusMap[status] || status
    }

    const refreshRunningTasks = async () => {
      const runningTasks = recentTasks.value.filter(t => t.status === 'running')
      if (runningTasks.length > 0) {
        for (const task of runningTasks) {
          try {
            const response = await aiAgentsApi.getTask(task.task_id)
            let taskData = null
            if (response && response.data) {
              taskData = response.data
            } else if (response && response.task_id) {
              taskData = response
            }
            
            if (taskData && taskData.status) {
              const index = recentTasks.value.findIndex(t => t.task_id === task.task_id)
              if (index !== -1) {
                recentTasks.value[index] = {
                  ...recentTasks.value[index],
                  ...taskData
                }
              }
            }
          } catch (error) {
            console.error('刷新任务状态失败:', error)
          }
        }
      }
    }

    onMounted(() => {
      loadRecentTasks()
      refreshInterval = setInterval(refreshRunningTasks, 5000)
    })

    onUnmounted(() => {
      if (refreshInterval) {
        clearInterval(refreshInterval)
      }
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
      formatDate
    }
  }
}
</script>

<style scoped>
.agent-scan {
  padding: var(--spacing-xl);
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
