<template>
  <div class="reports">
    <div class="page-header">
      <h1>报告生成</h1>
      <p class="page-subtitle">生成和管理安全扫描报告</p>
    </div>

    <!-- 报告生成表单 -->
    <div class="report-generator">
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">生成新报告</h3>
        </div>
        <div class="generator-content">
          <div class="form-section">
            <div class="form-group">
              <label class="form-label">选择扫描任务</label>
              <select v-model="selectedTask" class="form-select">
                <option value="">请选择扫描任务</option>
                <option v-for="task in scanTasks" :key="task.id" :value="task.id">
                  {{ task.task_name }} - {{ task.target }}
                </option>
              </select>
            </div>
            
            <div class="form-group">
              <label class="form-label">报告格式</label>
              <div class="format-tabs">
                <button 
                  v-for="format in reportFormats" 
                  :key="format.value"
                  @click="selectedFormat = format.value"
                  :class="['format-tab', { 'active': selectedFormat === format.value }]"
                >
                  <span class="format-icon">{{ format.icon }}</span>
                  <span class="format-name">{{ format.name }}</span>
                </button>
              </div>
            </div>
            
            <div class="form-group">
              <label class="form-label">报告内容</label>
              <div class="content-options">
                <label v-for="option in contentOptions" :key="option.value" class="checkbox-label">
                  <input 
                    v-model="selectedContent" 
                    type="checkbox" 
                    :value="option.value"
                    class="checkbox-input"
                  >
                  <span class="checkbox-custom"></span>
                  <span>{{ option.label }}</span>
                </label>
              </div>
            </div>
          </div>
          
        </div>
        
        <div class="generator-actions">
          <button @click="generateReport" class="btn btn-success" :disabled="!canGenerate">
            📄 生成报告
          </button>
        </div>
      </div>
    </div>

    <!-- 历史报告 -->
    <div class="report-history">
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">历史报告</h3>
          <div class="history-filters">
            <select v-model="historyFilter" class="form-select">
              <option value="">全部报告</option>
              <option value="html">HTML报告</option>
              <option value="pdf">PDF报告</option>
              <option value="json">JSON报告</option>
            </select>
          </div>
        </div>
        
        <div class="history-list">
          <div 
            v-for="report in filteredReports" 
            :key="report.id"
            class="report-item"
          >
            <div class="report-info">
              <div class="report-name">{{ report.report_name }}</div>
              <div class="report-meta">
                <span class="report-task">{{ report.task_name }}</span>
                <span class="report-date">{{ report.created_at }}</span>
              </div>
            </div>
            
            <div class="report-format">
              <span :class="['format-badge', `format-${report.report_type}`]">
                {{ (report.report_type || '').toUpperCase() }}
              </span>
            </div>
            
            <div class="report-size">
              {{ report.size }}
            </div>
            
            <div class="report-actions">
              <button @click="downloadReport(report)" class="btn-icon" title="下载">
                📥
              </button>
              <button @click="viewReport(report)" class="btn-icon" title="预览">
                👁️
              </button>
              <button @click="deleteReport(report.id)" class="btn-icon btn-danger" title="删除">
                🗑️
              </button>
            </div>
          </div>
        </div>
        
        <div v-if="filteredReports.length === 0" class="empty-state">
          <div class="empty-icon">📋</div>
          <div class="empty-title">暂无报告</div>
          <div class="empty-description">生成第一个安全扫描报告</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { reportApi, taskApi } from '../utils/api.js'

export default {
  name: 'Reports',
  data() {
    return {
      scanTasks: [], // Will be populated from API
      reports: [],
      selectedTask: '',
      selectedFormat: 'html',
      selectedContent: ['summary', 'vulnerabilities', 'recommendations'],
      historyFilter: '',
      reportFormats: [
        { value: 'html', name: 'HTML', icon: '🌐' },
        { value: 'pdf', name: 'PDF', icon: '📄' },
        { value: 'json', name: 'JSON', icon: '📊' }
      ],
      contentOptions: [
        { value: 'summary', label: '扫描摘要' },
        { value: 'vulnerabilities', label: '漏洞详情' },
        { value: 'recommendations', label: '修复建议' },
        { value: 'charts', label: '统计图表' },
        { value: 'appendix', label: '技术附录' }
      ]
    }
  },
  computed: {
    canGenerate() {
      return this.selectedTask && this.selectedFormat && this.selectedContent.length > 0
    },
    filteredReports() {
      if (!this.historyFilter) return this.reports
      return this.reports.filter(report => report.report_type === this.historyFilter)
    }
  },
  mounted() {
    this.fetchTasks()
    this.fetchReports()
  },
  methods: {
    async fetchTasks() {
      try {
        const response = await taskApi.list()
        if (response.code === 200 && response.data && response.data.tasks) {
            this.scanTasks = response.data.tasks
        } else if (Array.isArray(response.data)) {
            // Fallback if structure is different
            this.scanTasks = response.data
        } else {
            this.scanTasks = []
        }
      } catch (error) {
        console.error('获取任务列表失败:', error)
      }
    },
    async fetchReports() {
      try {
        const response = await reportApi.list()
        if (response.code === 200 && response.data && response.data.reports) {
            this.reports = response.data.reports
        } else {
             // Try direct array if format differs
             this.reports = response.data || []
        }
      } catch (error) {
        console.error('获取报告列表失败:', error)
        this.reports = []
      }
    },
    async generateReport() {
      if (!this.canGenerate) return
      
      const task = this.scanTasks.find(t => t.id == this.selectedTask)
      if (!task) return

      try {
        const reportData = {
          task_id: task.id,
          format: this.selectedFormat,
          content: this.selectedContent,
          name: `${task.task_name}报告`
        }
        
        await reportApi.create(reportData)
        alert('报告生成成功！')
        this.fetchReports()
      } catch (error) {
        console.error('生成报告失败:', error)
        alert('生成报告失败: ' + error.message)
      }
    },
    downloadReport(report) {
      // 实现下载功能
      const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:3000/api'
      const url = `${baseUrl}/reports/${report.id}/export?format=${report.report_type}`
      
      const link = document.createElement('a')
      link.href = url
      link.target = '_blank' // Open in new tab if it doesn't download immediately, though attachment header should force download
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
    },
    viewReport(report) {
      // 实现预览功能
      console.log('预览报告:', report.report_name)
    },
    async deleteReport(reportId) {
      if (confirm('确定要删除这个报告吗？')) {
        try {
            await reportApi.delete(reportId)
            this.reports = this.reports.filter(r => r.id !== reportId)
        } catch (error) {
            console.error('删除报告失败:', error)
            alert('删除报告失败')
        }
      }
    }
  }
}
</script>

<style scoped>
.reports {
  max-width: 1200px;
  margin: 0 auto;
}

.page-header {
  margin-bottom: var(--spacing-xl);
}

.page-subtitle {
  color: var(--text-secondary);
  margin-top: var(--spacing-xs);
}

/* 报告生成器 */
.report-generator {
  margin-bottom: var(--spacing-xl);
}

.generator-content {
  display: block; /* Removed grid to allow full width since preview is gone */
}

.form-section {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
  max-width: 800px; /* Limit width for better readability */
  margin: 0 auto; /* Center the form */
}

/* 格式选择标签 */
.format-tabs {
  display: flex;
  gap: var(--spacing-sm);
}

.format-tab {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: var(--spacing-md);
  border: 2px solid var(--border-color);
  border-radius: var(--border-radius);
  background: none;
  cursor: pointer;
  transition: all 0.2s ease;
  flex: 1;
}

.format-tab:hover {
  border-color: var(--secondary-color);
}

.format-tab.active {
  border-color: var(--secondary-color);
  background-color: rgba(74, 144, 226, 0.1);
}

.format-icon {
  font-size: 24px;
  margin-bottom: var(--spacing-xs);
}

.format-name {
  font-size: 12px;
  font-weight: bold;
}

/* 内容选项 */
.content-options {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  cursor: pointer;
  padding: var(--spacing-sm);
  border-radius: var(--border-radius);
  transition: background-color 0.2s ease;
}

.checkbox-label:hover {
  background-color: var(--background-color);
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
  content: '';
  position: absolute;
  left: 5px;
  top: 1px;
  width: 4px;
  height: 9px;
  border: solid white;
  border-width: 0 2px 2px 0;
  transform: rotate(45deg);
}

.generator-actions {
  display: flex;
  justify-content: flex-end;
  padding-top: var(--spacing-lg);
  border-top: 1px solid var(--border-color);
}

/* 历史报告 */
.history-filters {
  display: flex;
  gap: var(--spacing-md);
}

.history-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.report-item {
  display: flex;
  align-items: center;
  padding: var(--spacing-md);
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius);
  transition: all 0.2s ease;
}

.report-item:hover {
  background-color: var(--background-color);
  border-color: var(--secondary-color);
}

.report-info {
  flex: 1;
}

.report-name {
  font-weight: bold;
  color: var(--text-primary);
  margin-bottom: var(--spacing-xs);
}

.report-meta {
  display: flex;
  gap: var(--spacing-md);
  font-size: 12px;
  color: var(--text-secondary);
}

.report-format {
  margin: 0 var(--spacing-md);
}

.format-badge {
  padding: 2px var(--spacing-xs);
  border-radius: 3px;
  font-size: 10px;
  font-weight: bold;
}

.format-badge.format-html {
  background-color: rgba(74, 144, 226, 0.1);
  color: var(--secondary-color);
}

.format-badge.format-pdf {
  background-color: rgba(231, 76, 60, 0.1);
  color: var(--high-risk);
}

.format-badge.format-json {
  background-color: rgba(46, 204, 113, 0.1);
  color: var(--success-color);
}

.report-size {
  color: var(--text-secondary);
  font-size: 12px;
  margin-right: var(--spacing-md);
}

.report-actions {
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

/* 空状态 */
.empty-state {
  text-align: center;
  padding: var(--spacing-xl);
  color: var(--text-secondary);
}

.empty-icon {
  font-size: 48px;
  margin-bottom: var(--spacing-md);
}

.empty-title {
  font-size: 18px;
  font-weight: bold;
  margin-bottom: var(--spacing-sm);
}

.empty-description {
  font-size: 14px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .generator-content {
    grid-template-columns: 1fr;
  }
  
  .format-tabs {
    flex-direction: column;
  }
  
  .report-item {
    flex-direction: column;
    align-items: flex-start;
    gap: var(--spacing-sm);
  }
  
  .report-meta {
    flex-direction: column;
    gap: var(--spacing-xs);
  }
}
</style>
