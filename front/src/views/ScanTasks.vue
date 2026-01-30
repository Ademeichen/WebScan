<template>
  <div class="scan-tasks">
    <div class="page-header">
      <h1>扫描任务</h1>
      <div class="header-actions">
        <button class="btn-primary" @click="showCreateModal = true">
          ➕ 新建任务
        </button>
        <button class="btn-secondary" @click="loadTasks">
          🔄 刷新
        </button>
      </div>
    </div>

    <div class="filters-section">
      <div class="filter-group">
        <label>状态:</label>
        <select v-model="filters.status" @change="loadTasks">
          <option value="">全部</option>
          <option value="pending">等待中</option>
          <option value="running">运行中</option>
          <option value="completed">已完成</option>
          <option value="failed">失败</option>
          <option value="cancelled">已取消</option>
        </select>
      </div>

      <div class="filter-group">
        <label>类型:</label>
        <select v-model="filters.task_type" @change="loadTasks">
          <option value="">全部</option>
          <option value="awvs_scan">AWVS扫描</option>
          <option value="poc_scan">POC扫描</option>
          <option value="scan_dir">目录扫描</option>
          <option value="scan_webside">网站扫描</option>
          <option value="scan_port">端口扫描</option>
          <option value="scan_cms">CMS识别</option>
          <option value="scan_comprehensive">综合扫描</option>
        </select>
      </div>

      <div class="filter-group">
        <label>搜索:</label>
        <input
          v-model="filters.search"
          type="text"
          placeholder="搜索任务名称或目标"
          @keyup.enter="loadTasks"
        />
      </div>

      <div class="filter-group">
        <label>日期范围:</label>
        <input
          v-model="filters.start_date"
          type="date"
          @change="loadTasks"
        />
        <span>至</span>
        <input
          v-model="filters.end_date"
          type="date"
          @change="loadTasks"
        />
      </div>
    </div>

    <div v-if="loading" class="loading-container">
      <Loading text="加载任务列表中..." />
    </div>

    <div v-else-if="tasks.length === 0" class="empty-state">
      <div class="empty-icon">📋</div>
      <h3>暂无任务</h3>
      <p>点击"新建任务"按钮创建您的第一个扫描任务</p>
      <button class="btn-primary" @click="showCreateModal = true">
        新建任务
      </button>
    </div>

    <div v-else class="tasks-list">
      <TaskCard
        v-for="task in tasks"
        :key="task.id"
        :task="task"
        @cancel="handleCancelTask"
        @view="handleViewTask"
        @report="handleGenerateReport"
        @delete="handleDeleteTask"
      />
    </div>

    <div v-if="total > limit" class="pagination">
      <button
        class="btn-page"
        :disabled="currentPage === 1"
        @click="currentPage--; loadTasks()"
      >
        上一页
      </button>
      <span class="page-info">第 {{ currentPage }} / {{ totalPages }} 页</span>
      <button
        class="btn-page"
        :disabled="currentPage === totalPages"
        @click="currentPage++; loadTasks()"
      >
        下一页
      </button>
    </div>

    <div v-if="showCreateModal" class="modal-overlay" @click.self="showCreateModal = false">
      <div class="modal-content">
        <div class="modal-header">
          <h2>创建扫描任务</h2>
          <button class="btn-close" @click="showCreateModal = false">×</button>
        </div>
        <div class="modal-body">
          <div class="task-type-selector">
            <button
              v-for="type in taskTypes"
              :key="type.value"
              :class="['task-type-btn', { active: selectedTaskType === type.value }]"
              @click="selectedTaskType = type.value"
            >
              <span class="task-type-icon">{{ type.icon }}</span>
              <span class="task-type-label">{{ type.label }}</span>
            </button>
          </div>

          <div class="form-group">
            <label for="taskName">任务名称 *</label>
            <input
              id="taskName"
              v-model="newTask.task_name"
              type="text"
              placeholder="请输入任务名称"
            />
          </div>

          <div class="form-group">
            <label for="target">扫描目标 *</label>
            <input
              id="target"
              v-model="newTask.target"
              type="text"
              placeholder="请输入URL或IP地址"
            />
          </div>

          <div class="form-actions">
            <button class="btn-secondary" @click="showCreateModal = false">
              取消
            </button>
            <button class="btn-primary" :disabled="isCreating" @click="handleCreateTask">
              {{ isCreating ? '创建中...' : '创建任务' }}
            </button>
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
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { tasksApi } from '@/utils/api'
import TaskCard from '@/components/business/TaskCard.vue'
import Loading from '@/components/common/Loading.vue'
import Alert from '@/components/common/Alert.vue'

export default {
  name: 'ScanTasks',
  components: {
    TaskCard,
    Loading,
    Alert
  },
  setup() {
    const router = useRouter()
    const route = useRoute()
    const loading = ref(true)
    const errorMessage = ref('')
    const tasks = ref([])
    const total = ref(0)
    const currentPage = ref(1)
    const limit = ref(20)
    const showCreateModal = ref(false)
    const isCreating = ref(false)
    const selectedTaskType = ref('poc_scan')

    const filters = ref({
      status: '',
      task_type: '',
      search: '',
      start_date: '',
      end_date: ''
    })

    const newTask = ref({
      task_name: '',
      target: ''
    })

    const taskTypes = [
      { value: 'poc_scan', label: 'POC扫描', icon: '🔍' },
      { value: 'awvs_scan', label: 'AWVS扫描', icon: '🛡️' },
      { value: 'scan_dir', label: '目录扫描', icon: '📁' },
      { value: 'scan_webside', label: '网站扫描', icon: '🌐' },
      { value: 'scan_port', label: '端口扫描', icon: '🔌' },
      { value: 'scan_cms', label: 'CMS识别', icon: '🔎' },
      { value: 'scan_comprehensive', label: '综合扫描', icon: '🎯' }
    ]

    const totalPages = computed(() => Math.ceil(total.value / limit.value))

    const loadTasks = async () => {
      loading.value = true
      errorMessage.value = ''
      try {
        const params = {
          ...filters.value,
          skip: (currentPage.value - 1) * limit.value,
          limit: limit.value
        }

        const response = await tasksApi.getTasks(params)
        if (response.code === 200) {
          tasks.value = response.data.tasks || []
          total.value = response.data.total || 0
        }
      } catch (error) {
        errorMessage.value = '加载任务列表失败'
        console.error('加载任务失败:', error)
      } finally {
        loading.value = false
      }
    }

    const handleCancelTask = async (taskId) => {
      if (confirm('确定要取消此任务吗？')) {
        try {
          await tasksApi.cancelTask(taskId)
          await loadTasks()
        } catch (error) {
          errorMessage.value = '取消任务失败'
        }
      }
    }

    const handleViewTask = (taskId) => {
      router.push(`/vulnerability-results?task=${taskId}`)
    }

    const handleGenerateReport = async (taskId) => {
      router.push(`/reports?task=${taskId}`)
    }

    const handleDeleteTask = async (taskId) => {
      if (confirm('确定要删除此任务吗？此操作不可恢复。')) {
        try {
          await tasksApi.deleteTask(taskId)
          await loadTasks()
        } catch (error) {
          errorMessage.value = '删除任务失败'
        }
      }
    }

    const handleCreateTask = async () => {
      if (!newTask.value.task_name || !newTask.value.target) {
        errorMessage.value = '请填写任务名称和扫描目标'
        return
      }

      isCreating.value = true
      errorMessage.value = ''

      try {
        const taskData = {
          task_name: newTask.value.task_name,
          target: newTask.value.target,
          task_type: selectedTaskType.value,
          config: {}
        }

        const response = await tasksApi.createTask(taskData)
        if (response.code === 200) {
          showCreateModal.value = false
          newTask.value = { task_name: '', target: '' }
          await loadTasks()
        } else {
          errorMessage.value = response.message || '创建任务失败'
        }
      } catch (error) {
        errorMessage.value = error.message || '创建任务失败'
      } finally {
        isCreating.value = false
      }
    }

    onMounted(() => {
      loadTasks()

      if (route.query.task) {
        handleViewTask(parseInt(route.query.task))
      }
    })

    return {
      loading,
      errorMessage,
      tasks,
      total,
      currentPage,
      limit,
      totalPages,
      filters,
      showCreateModal,
      isCreating,
      selectedTaskType,
      newTask,
      taskTypes,
      loadTasks,
      handleCancelTask,
      handleViewTask,
      handleGenerateReport,
      handleDeleteTask,
      handleCreateTask
    }
  }
}
</script>

<style scoped>
.scan-tasks {
  padding: var(--spacing-xl);
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-xl);
}

.page-header h1 {
  margin: 0;
  font-size: 2rem;
  color: var(--text-primary);
}

.header-actions {
  display: flex;
  gap: var(--spacing-md);
}

.filters-section {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-md);
  padding: var(--spacing-lg);
  background-color: var(--card-bg);
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius-lg);
  margin-bottom: var(--spacing-lg);
}

.filter-group {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
}

.filter-group label {
  font-weight: 500;
  color: var(--text-secondary);
  white-space: nowrap;
}

.filter-group input,
.filter-group select {
  padding: var(--spacing-sm) var(--spacing-md);
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius);
  font-size: 0.875rem;
  transition: border-color 0.3s;
}

.filter-group input:focus,
.filter-group select:focus {
  outline: none;
  border-color: var(--color-primary);
}

.loading-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 400px;
}

.empty-state {
  text-align: center;
  padding: var(--spacing-xxl);
  color: var(--text-secondary);
}

.empty-icon {
  font-size: 4rem;
  margin-bottom: var(--spacing-lg);
}

.empty-state h3 {
  margin: 0 0 var(--spacing-md);
  font-size: 1.5rem;
  color: var(--text-primary);
}

.empty-state p {
  margin: 0 0 var(--spacing-xl);
}

.tasks-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: var(--spacing-md);
  margin-top: var(--spacing-xl);
  padding: var(--spacing-md);
  background-color: var(--card-bg);
  border-radius: var(--border-radius);
}

.btn-page {
  padding: var(--spacing-sm) var(--spacing-md);
  background-color: var(--color-primary);
  color: white;
  border: none;
  border-radius: var(--border-radius);
  cursor: pointer;
  transition: all 0.3s;
}

.btn-page:hover:not(:disabled) {
  background-color: var(--color-primary-dark);
}

.btn-page:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.page-info {
  color: var(--text-secondary);
  font-size: 0.875rem;
}

.modal-overlay {
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
  max-width: 600px;
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

.task-type-selector {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
  gap: var(--spacing-md);
  margin-bottom: var(--spacing-lg);
}

.task-type-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-md);
  border: 2px solid var(--border-color);
  border-radius: var(--border-radius);
  background-color: var(--bg-secondary);
  cursor: pointer;
  transition: all 0.3s;
}

.task-type-btn:hover {
  border-color: var(--color-primary);
  background-color: var(--color-primary-bg);
}

.task-type-btn.active {
  border-color: var(--color-primary);
  background-color: var(--color-primary-bg);
}

.task-type-icon {
  font-size: 2rem;
}

.task-type-label {
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--text-primary);
}

.form-group {
  margin-bottom: var(--spacing-lg);
}

.form-group label {
  display: block;
  margin-bottom: var(--spacing-sm);
  font-weight: 500;
  color: var(--text-primary);
}

.form-group input {
  width: 100%;
  padding: var(--spacing-sm) var(--spacing-md);
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius);
  font-size: 1rem;
  transition: border-color 0.3s;
}

.form-group input:focus {
  outline: none;
  border-color: var(--color-primary);
}

.form-actions {
  display: flex;
  gap: var(--spacing-md);
  margin-top: var(--spacing-xl);
}

.btn-primary,
.btn-secondary {
  flex: 1;
  padding: var(--spacing-md) var(--spacing-lg);
  border: none;
  border-radius: var(--border-radius);
  font-size: 1rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s;
}

.btn-primary {
  background-color: var(--color-primary);
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background-color: var(--color-primary-dark);
}

.btn-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-secondary {
  background-color: var(--color-secondary);
  color: white;
}

.btn-secondary:hover {
  background-color: var(--color-secondary-dark);
}

@media (max-width: 768px) {
  .filters-section {
    flex-direction: column;
    align-items: stretch;
  }
  
  .task-type-selector {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
