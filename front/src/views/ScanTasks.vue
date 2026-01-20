<template>
  <div class="scan-tasks">
    <div class="page-header">
      <div class="header-content">
        <h1>扫描任务管理</h1>
        <button @click="showCreateModal = true" class="btn btn-success">
          <span>➕</span>
          创建扫描任务
        </button>
      </div>
      
      <!-- 搜索和筛选 -->
      <div class="filters">
        <div class="search-box">
          <input 
            v-model="searchQuery" 
            type="text" 
            placeholder="搜索任务名称或URL..." 
            class="form-input"
          >
        </div>
        <select v-model="statusFilter" class="form-select">
          <option value="">全部状态</option>
          <option value="waiting">等待中</option>
          <option value="running">进行中</option>
          <option value="completed">已完成</option>
          <option value="failed">失败</option>
        </select>
        <select v-model="priorityFilter" class="form-select">
          <option value="">全部优先级</option>
          <option value="critical">关键</option>
          <option value="high">高</option>
          <option value="medium">中</option>
          <option value="low">低</option>
        </select>
        
        <!-- 时间范围筛选 -->
        <div class="date-range">
          <input 
            v-model="startDate" 
            type="date" 
            class="form-input date-input"
            title="开始日期"
          >
          <span class="separator">-</span>
          <input 
            v-model="endDate" 
            type="date" 
            class="form-input date-input"
            title="结束日期"
          >
        </div>
      </div>
    </div>

    <!-- 任务列表 -->
    <div class="tasks-container">
      <div class="card">
        <div class="tasks-table">
          <div class="table-header">
            <div class="th task-name">任务名称</div>
            <div class="th target-url">目标URL</div>
            <div class="th status">状态</div>
            <div class="th priority">优先级</div>
            <div class="th start-time">开始时间</div>
            <div class="th end-time">结束时间</div>
            <div class="th actions">操作</div>
          </div>
          
          <div class="table-body">
            <div 
              v-for="task in filteredTasks" 
              :key="task.id" 
              class="table-row"
              @click="viewTaskDetails(task.id)"
            >
              <div class="td task-name">
                <div class="task-info">
                  <div class="task-title">{{ task.name }}</div>
                  <div class="task-type">{{ task.scanType }}</div>
                </div>
              </div>
              
              <div class="td target-url">
                <div class="url-display" :title="task.targetUrl">
                  {{ truncateUrl(task.targetUrl) }}
                </div>
              </div>
              
              <div class="td status">
                <span :class="['status', `status-${task.status}`]">
                  <span class="status-dot"></span>
                  {{ getStatusText(task.status) }}
                </span>
                <div v-if="(task.status === 'running' || task.status === 'processing') && task.progress >= 0" class="progress-container">
                  <div class="progress-bar-bg">
                    <div class="progress-bar-fill" :style="{ width: task.progress + '%' }"></div>
                  </div>
                  <span class="progress-text">{{ task.progress }}%</span>
                </div>
              </div>
              
              <div class="td priority">
                <div :class="['priority', `priority-${task.priority}`]">
                  <div class="priority-stars">
                    <span 
                      v-for="n in 5" 
                      :key="n"
                      class="star"
                      :class="{ 'filled': n <= getPriorityStars(task.priority) }"
                    >★</span>
                  </div>
                  <span class="priority-text">{{ getPriorityText(task.priority) }}</span>
                </div>
              </div>
              
              <div class="td start-time">{{ task.startTime }}</div>
              <div class="td end-time">{{ task.endTime || '-' }}</div>
              
              <div class="td actions" @click.stop>
                <div class="action-buttons">
                  <button 
                    v-if="task.status === 'completed'" 
                    @click="viewResults(task.id)"
                    class="btn-icon"
                    title="查看结果"
                  >
                    📊
                  </button>
                  <button 
                    v-if="task.status === 'running'" 
                    @click="stopTask(task.id)"
                    class="btn-icon"
                    title="停止任务"
                  >
                    ⏹️
                  </button>
                  <button 
                    v-if="task.status === 'failed' || task.status === 'completed'" 
                    @click="restartTask(task.id)"
                    class="btn-icon"
                    title="重新扫描"
                  >
                    🔄
                  </button>
                  <button 
                    @click="deleteTask(task.id)"
                    class="btn-icon btn-danger"
                    title="删除任务"
                  >
                    🗑️
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 创建任务模态框 -->
    <div v-if="showCreateModal" class="modal-overlay" @click="closeModal">
      <div class="modal" @click.stop>
        <div class="modal-header">
          <h2>创建扫描任务</h2>
          <button @click="closeModal" class="close-btn">×</button>
        </div>
        
        <div class="modal-body">
          <form @submit.prevent="createTask">
            <div class="form-group">
              <label class="form-label">任务名称</label>
              <input 
                v-model="newTask.name" 
                type="text" 
                class="form-input" 
                placeholder="输入任务名称"
                required
              >
            </div>
            
            <div class="form-group">
              <label class="form-label">目标URL</label>
              <textarea 
                v-model="newTask.targetUrls" 
                class="form-input" 
                rows="4"
                placeholder="输入目标URL，每行一个&#10;例如：&#10;https://example.com&#10;https://api.example.com"
                required
              ></textarea>
              <div class="form-help">支持多个URL，每行一个</div>
            </div>
            
            <div class="form-row">
              <div class="form-group">
                <label class="form-label">扫描类型</label>
                <select v-model="newTask.scanType" class="form-select" required>
                  <option value="">选择扫描类型</option>
                  <option v-for="option in scanTypeOptions" :key="option.value" :value="option.value">
                    {{ option.label }}
                  </option>
                </select>
              </div>

              <div class="form-group" v-if="newTask.scanType === 'awvs_scan'">
                <label class="form-label">AWVS 扫描策略</label>
                <select v-model="newTask.scanProfile" class="form-select">
                  <option value="full_scan">完整扫描</option>
                  <option value="high_risk_vuln">高风险漏洞扫描</option>
                  <option value="xss_vuln">XSS 漏洞扫描</option>
                  <option value="sqli_vuln">SQL 注入漏洞扫描</option>
                  <option value="weak_passwords">弱密码扫描</option>
                  <option value="crawl_only">仅爬取</option>
                </select>
              </div>
              
              <div class="form-group">
                <label class="form-label">重要性级别</label>
                <div class="priority-options">
                  <label v-for="priority in priorityOptions" :key="priority.value" class="radio-label">
                    <input 
                      v-model="newTask.priority" 
                      type="radio" 
                      :value="priority.value"
                      class="radio-input"
                    >
                    <span class="radio-custom"></span>
                    <span :class="['priority-label', `priority-${priority.value}`]">
                      {{ priority.label }}
                    </span>
                  </label>
                </div>
              </div>
            </div>
            
            <div class="form-group">
              <label class="form-label">扫描时间</label>
              <div class="schedule-options">
                <label class="radio-label">
                  <input 
                    v-model="newTask.scheduleType" 
                    type="radio" 
                    value="immediate"
                    class="radio-input"
                  >
                  <span class="radio-custom"></span>
                  <span>立即执行</span>
                </label>
                <label class="radio-label">
                  <input 
                    v-model="newTask.scheduleType" 
                    type="radio" 
                    value="scheduled"
                    class="radio-input"
                  >
                  <span class="radio-custom"></span>
                  <span>定时执行</span>
                </label>
              </div>
              <div v-if="newTask.scheduleType === 'scheduled'" class="form-group">
                <input 
                  v-model="newTask.scheduledTime" 
                  type="datetime-local" 
                  class="form-input"
                >
              </div>
            </div>
            
            <!-- 高级选项 -->
            <div class="advanced-options">
              <button 
                type="button" 
                @click="showAdvanced = !showAdvanced"
                class="btn btn-outline"
              >
                {{ showAdvanced ? '收起' : '展开' }}高级选项
                <span>{{ showAdvanced ? '▲' : '▼' }}</span>
              </button>
              
              <div v-if="showAdvanced" class="advanced-content">
                <div class="form-group">
                  <label class="form-label">扫描深度</label>
                  <select v-model="newTask.depth" class="form-select">
                    <option value="1">浅层扫描 (深度1)</option>
                    <option value="2">中等扫描 (深度2)</option>
                    <option value="3">深度扫描 (深度3)</option>
                  </select>
                </div>
                
                <div class="form-group">
                  <label class="form-label">并发数</label>
                  <input 
                    v-model="newTask.concurrency" 
                    type="number" 
                    min="1" 
                    max="10"
                    class="form-input"
                  >
                </div>
                
                <div class="form-group">
                  <label class="checkbox-label">
                    <input 
                      v-model="newTask.enableAuth" 
                      type="checkbox"
                      class="checkbox-input"
                    >
                    <span class="checkbox-custom"></span>
                    <span>启用认证扫描</span>
                  </label>
                </div>

                <div class="form-group" v-if="newTask.scanType === 'poc_scan'">
                  <label class="checkbox-label">
                    <input 
                      v-model="newTask.enableAiGeneration" 
                      type="checkbox"
                      class="checkbox-input"
                    >
                    <span class="checkbox-custom"></span>
                    <span>启用AI智能生成POC (针对无POC的漏洞)</span>
                  </label>
                </div>
              </div>
            </div>
          </form>
        </div>
        
        <div class="modal-footer">
          <button @click="closeModal" class="btn btn-outline">取消</button>
          <button @click="createTask" class="btn btn-success">创建任务</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { formatDate } from '../utils/date'
import { taskApi } from '../utils/api'

export default {
  name: 'ScanTasks',
  data() {
    return {
      searchQuery: '',
      statusFilter: '',
      priorityFilter: '',
      showCreateModal: false,
      showAdvanced: false,
      
      tasks: [],
      loading: false,
      pollingTimer: null,
      
      newTask: {
        name: '',
        targetUrls: '',
        scanType: '',
        scanProfile: 'full_scan',
        priority: 'medium',
        scheduleType: 'immediate',
        scheduledTime: '',
        depth: '2',
        concurrency: 3,
        enableAuth: false,
        enableAiGeneration: false
      },
      
      scanTypeOptions: [
        { value: 'awvs_scan', label: 'AWVS 漏洞扫描' },
        { value: 'poc_scan', label: 'POC 漏洞验证' },
        { value: 'scan_dir', label: '目录扫描' },
        { value: 'scan_port', label: '端口扫描' },
        { value: 'scan_webside', label: '网站指纹识别' },
        { value: 'scan_cms', label: 'CMS 识别' },
        { value: 'scan_comprehensive', label: '综合扫描' }
      ],
      
      priorityOptions: [
        { value: 'low', label: '低' },
        { value: 'medium', label: '中' },
        { value: 'high', label: '高' },
        { value: 'critical', label: '关键' }
      ]
    }
  },
  computed: {
    filteredTasks() {
      return this.tasks.filter(task => {
        const matchesSearch = !this.searchQuery || 
          (task.name && task.name.toLowerCase().includes(this.searchQuery.toLowerCase())) ||
          (task.targetUrl && task.targetUrl.toLowerCase().includes(this.searchQuery.toLowerCase()))
        
        const matchesStatus = !this.statusFilter || task.status === this.statusFilter
        const matchesPriority = !this.priorityFilter || task.priority === this.priorityFilter
        
        let matchesDate = true
        if (this.startDate || this.endDate) {
          if (!task.startTime) return false
          const taskDate = new Date(task.startTime)
          if (this.startDate) {
            matchesDate = matchesDate && taskDate >= new Date(this.startDate)
          }
          if (this.endDate) {
            const nextDay = new Date(this.endDate)
            nextDay.setDate(nextDay.getDate() + 1)
            matchesDate = matchesDate && taskDate < nextDay
          }
        }
        
        return matchesSearch && matchesStatus && matchesPriority && matchesDate
      })
    }
  },
  mounted() {
    this.fetchTasks()
    // 开启轮询，实现实时状态更新
    this.pollingTimer = setInterval(this.fetchTasks, 5000)
  },
  beforeUnmount() {
    if (this.pollingTimer) {
      clearInterval(this.pollingTimer)
    }
  },
  methods: {
    async fetchTasks() {
      try {
        const response = await taskApi.list()
        
        if (response.code === 200 && response.data && response.data.tasks) {
          this.tasks = response.data.tasks.map(task => ({
            id: task.id,
            name: task.task_name,
            targetUrl: task.target,
            status: task.status,
            scanType: this.getScanTypeLabel(task.task_type),
            priority: task.config?.priority || 'medium',
            startTime: formatDate(task.created_at),
            endTime: task.status === 'completed' || task.status === 'failed' ? formatDate(task.updated_at) : '-',
            progress: task.progress || 0
          }))
        } else if (response.code === 200 && Array.isArray(response.data)) {
          this.tasks = response.data.map(task => ({
            id: task.id,
            name: task.task_name,
            targetUrl: task.target,
            status: task.status,
            scanType: this.getScanTypeLabel(task.task_type),
            priority: task.config?.priority || 'medium',
            startTime: formatDate(task.created_at),
            endTime: task.status === 'completed' || task.status === 'failed' ? formatDate(task.updated_at) : '-',
            progress: task.progress || 0
          }))
        }
      } catch (error) {
        console.error('获取任务列表失败:', error)
      }
    },
    
    getStatusText(status) {
      const statusMap = {
        pending: '等待中',
        waiting: '等待中',
        running: '进行中',
        completed: '已完成',
        failed: '失败',
        cancelled: '已取消'
      }
      return statusMap[status] || status
    },
    
    getPriorityText(priority) {
      const priorityMap = {
        low: '低',
        medium: '中',
        high: '高',
        critical: '关键'
      }
      return priorityMap[priority] || priority
    },
    
    getPriorityStars(priority) {
      const starMap = {
        low: 1,
        medium: 2,
        high: 4,
        critical: 5
      }
      return starMap[priority] || 1
    },
    
    getScanTypeLabel(type) {
      const option = this.scanTypeOptions.find(opt => opt.value === type)
      return option ? option.label : type
    },
    
    truncateUrl(url) {
      if (!url) return ''
      return url.length > 40 ? url.substring(0, 40) + '...' : url
    },
    
    viewTaskDetails(taskId) {
      // TODO: 实现查看任务详情弹窗或页面
      console.log('查看任务详情:', taskId)
    },
    
    viewResults(taskId) {
      this.$router.push(`/vulnerabilities/${taskId}`)
    },
    
    async stopTask(taskId) {
      if (!confirm('确定要停止该任务吗？')) return
      
      try {
        const response = await fetch(`/api/tasks/${taskId}/cancel`, {
          method: 'POST'
        })
        const result = await response.json()
        if (result.code === 200) {
          this.fetchTasks() // 立即刷新
        } else {
          alert(result.message || '停止任务失败')
        }
      } catch (error) {
        console.error('停止任务出错:', error)
        alert('停止任务出错')
      }
    },
    
    async restartTask(taskId) {
      // 目前没有直接的重启API，可以通过获取任务详情后重新创建来实现
      // 这里暂时只提示
      alert('暂不支持直接重启，请重新创建任务')
    },
    
    async deleteTask(taskId) {
      if (!confirm('确定要删除这个任务吗？')) return
      
      try {
        const response = await fetch(`/api/tasks/${taskId}`, {
          method: 'DELETE'
        })
        const result = await response.json()
        if (result.code === 200) {
          this.tasks = this.tasks.filter(task => task.id !== taskId)
        } else {
          alert(result.message || '删除任务失败')
        }
      } catch (error) {
        console.error('删除任务出错:', error)
        alert('删除任务出错')
      }
    },
    
    closeModal() {
      this.showCreateModal = false
      this.showAdvanced = false
      this.resetForm()
    },
    
    resetForm() {
      this.newTask = {
        name: '',
        targetUrls: '',
        scanType: '',
        priority: 'medium',
        scheduleType: 'immediate',
        scheduledTime: '',
        depth: '2',
        concurrency: 3,
        enableAuth: false
      }
    },
    
    async createTask() {
      // 验证表单
      if (!this.newTask.name || !this.newTask.targetUrls || !this.newTask.scanType) {
        alert('请填写必填字段')
        return
      }
      
      const targets = this.newTask.targetUrls.split('\n').filter(url => url.trim())
      
      if (targets.length === 0) {
        alert('请输入有效的目URL')
        return
      }
      
      let successCount = 0
      let failCount = 0
      
      // 批量创建任务
      for (const target of targets) {
        try {
          const payload = {
            task_name: targets.length > 1 ? `${this.newTask.name} - ${target}` : this.newTask.name,
            target: target.trim(),
            task_type: this.newTask.scanType,
            config: {
            priority: this.newTask.priority,
            depth: this.newTask.depth,
            concurrency: this.newTask.concurrency,
            enable_auth: this.newTask.enableAuth,
            enable_ai_generation: this.newTask.enableAiGeneration,
            schedule_type: this.newTask.scheduleType,
            scheduled_time: this.newTask.scheduledTime,
            profile: this.newTask.scanType === 'awvs_scan' ? this.newTask.scanProfile : undefined
          }
          }
          
          const response = await fetch('/api/tasks/create', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
          })
          
          const result = await response.json()
          if (result.code === 200) {
            successCount++
          } else {
            failCount++
            console.error(`创建任务失败 (${target}):`, result.message)
          }
        } catch (error) {
          failCount++
          console.error(`创建任务出错 (${target}):`, error)
        }
      }
      
      if (successCount > 0) {
        // alert(`成功创建 ${successCount} 个任务` + (failCount > 0 ? `，失败 ${failCount} 个` : ''))
        this.closeModal()
        this.fetchTasks() // 刷新列表
      } else {
        alert('创建任务失败，请重试')
      }
    }
  }
}
</script>

<style scoped>
.scan-tasks {
  max-width: 1400px;
  margin: 0 auto;
}

.page-header {
  margin-bottom: var(--spacing-xl);
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-lg);
}

.filters {
  display: flex;
  gap: var(--spacing-md);
  align-items: center;
  flex-wrap: wrap;
}

.date-range {
  display: flex;
  align-items: center;
  gap: 5px;
}

.date-input {
  width: 140px;
}

.separator {
  color: var(--text-secondary);
}

.search-box {
  flex: 1;
  max-width: 300px;
}

/* 任务表格 */
.tasks-table {
  display: table;
  width: 100%;
  border-collapse: collapse;
}

.progress-container {
  margin-top: 5px;
  display: flex;
  align-items: center;
  gap: 5px;
  width: 100%;
  max-width: 120px;
}

.progress-bar-bg {
  flex: 1;
  height: 6px;
  background-color: #eee;
  border-radius: 3px;
  overflow: hidden;
}

.progress-bar-fill {
  height: 100%;
  background-color: #007bff;
  transition: width 0.3s ease;
}

.progress-text {
  font-size: 12px;
  color: #666;
  min-width: 30px;
}

.vuln-badges {
  display: flex;
  gap: 4px;
  margin-top: 4px;
}

.badge {
  padding: 2px 6px;
  border-radius: 10px;
  font-size: 11px;
  font-weight: bold;
  color: white;
}

.badge-high { background-color: #dc3545; }
.badge-medium { background-color: #ffc107; color: #333; }
.badge-low { background-color: #28a745; }

.table-header {
  display: table-row;
  background-color: var(--background-color);
  font-weight: bold;
}

.table-body {
  display: table-row-group;
}

.table-row {
  display: table-row;
  cursor: pointer;
  transition: background-color 0.2s ease;
}

.table-row:hover {
  background-color: var(--background-color);
}

.th, .td {
  display: table-cell;
  padding: var(--spacing-md);
  border-bottom: 1px solid var(--border-color);
  vertical-align: middle;
}

.th {
  color: var(--text-primary);
  font-weight: bold;
  font-size: 13px;
}

.task-name {
  width: 20%;
}

.target-url {
  width: 25%;
}

.status {
  width: 12%;
}

.priority {
  width: 15%;
}

.start-time {
  width: 12%;
}

.end-time {
  width: 12%;
}

.actions {
  width: 10%;
}

.task-info {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
}

.task-title {
  font-weight: bold;
  color: var(--text-primary);
}

.task-type {
  font-size: 12px;
  color: var(--text-secondary);
}

.url-display {
  color: var(--secondary-color);
  font-family: monospace;
  font-size: 12px;
}

.priority-stars {
  display: flex;
  gap: 1px;
  margin-bottom: var(--spacing-xs);
}

.star {
  font-size: 12px;
  color: #ddd;
}

.star.filled {
  color: currentColor;
}

.priority-text {
  font-size: 11px;
  font-weight: bold;
}

.action-buttons {
  display: flex;
  gap: var(--spacing-xs);
}

.btn-icon {
  background: none;
  border: none;
  cursor: pointer;
  padding: var(--spacing-xs);
  border-radius: var(--border-radius);
  font-size: 14px;
  transition: background-color 0.2s ease;
}

.btn-icon:hover {
  background-color: var(--background-color);
}

.btn-icon.btn-danger:hover {
  background-color: rgba(231, 76, 60, 0.1);
}

/* 模态框 */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal {
  background-color: var(--card-background);
  border-radius: var(--border-radius-lg);
  box-shadow: var(--shadow-lg);
  width: 90%;
  max-width: 600px;
  max-height: 90vh;
  overflow-y: auto;
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
  color: var(--text-primary);
}

.close-btn {
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: var(--text-secondary);
  padding: 0;
  width: 30px;
  height: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.modal-body {
  padding: var(--spacing-lg);
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: var(--spacing-md);
  padding: var(--spacing-lg);
  border-top: 1px solid var(--border-color);
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--spacing-md);
}

.form-help {
  font-size: 12px;
  color: var(--text-secondary);
  margin-top: var(--spacing-xs);
}

.priority-options {
  display: flex;
  gap: var(--spacing-md);
}

.schedule-options {
  display: flex;
  gap: var(--spacing-lg);
  margin-bottom: var(--spacing-md);
}

.radio-label {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  cursor: pointer;
  font-size: 14px;
}

.radio-input {
  display: none;
}

.radio-custom {
  width: 16px;
  height: 16px;
  border: 2px solid var(--border-color);
  border-radius: 50%;
  position: relative;
  transition: border-color 0.2s ease;
}

.radio-input:checked + .radio-custom {
  border-color: var(--secondary-color);
}

.radio-input:checked + .radio-custom::after {
  content: '';
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 8px;
  height: 8px;
  background-color: var(--secondary-color);
  border-radius: 50%;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  cursor: pointer;
}

.checkbox-input {
  display: none;
}

.checkbox-custom {
  width: 16px;
  height: 16px;
  border: 2px solid var(--border-color);
  border-radius: 3px;
  position: relative;
  transition: all 0.2s ease;
}

.checkbox-input:checked + .checkbox-custom {
  background-color: var(--secondary-color);
  border-color: var(--secondary-color);
}

.checkbox-input:checked + .checkbox-custom::after {
  content: '✓';
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  color: white;
  font-size: 10px;
  font-weight: bold;
}

.advanced-options {
  margin-top: var(--spacing-lg);
  border-top: 1px solid var(--border-color);
  padding-top: var(--spacing-lg);
}

.advanced-content {
  margin-top: var(--spacing-md);
  padding: var(--spacing-md);
  background-color: var(--background-color);
  border-radius: var(--border-radius);
}

/* 响应式设计 */
@media (max-width: 768px) {
  .filters {
    flex-direction: column;
    align-items: stretch;
  }
  
  .search-box {
    max-width: none;
  }
  
  .tasks-table {
    display: block;
  }
  
  .table-header {
    display: none;
  }
  
  .table-row {
    display: block;
    margin-bottom: var(--spacing-md);
    border: 1px solid var(--border-color);
    border-radius: var(--border-radius);
    padding: var(--spacing-md);
  }
  
  .td {
    display: block;
    padding: var(--spacing-xs) 0;
    border-bottom: none;
  }
  
  .td::before {
    content: attr(data-label);
    font-weight: bold;
    color: var(--text-secondary);
    display: inline-block;
    width: 100px;
    font-size: 12px;
  }
  
  .form-row {
    grid-template-columns: 1fr;
  }
  
  .priority-options {
    flex-direction: column;
    gap: var(--spacing-sm);
  }
}
</style>
