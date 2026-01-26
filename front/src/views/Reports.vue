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
              <select v-model="selectedTask" class="form-select" :disabled="loadingTasks">
                <option value="">请选择扫描任务</option>
                <option v-for="task in scanTasks" :key="task.id" :value="task.id">
                  {{ task.task_name }} - {{ task.target }}
                </option>
              </select>
              <span v-if="loadingTasks" class="form-hint">加载中...</span>
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
          <button @click="generateReport" class="btn btn-success" :disabled="!canGenerate || generating">
            <span v-if="generating">⏳ 生成中...</span>
            <span v-else>📄 生成报告</span>
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
        
        <div v-if="loadingReports" class="loading-state">
          <div class="loading-spinner"></div>
          <div class="loading-text">加载报告列表...</div>
        </div>
        
        <div v-else class="history-list">
          <div 
            v-for="report in filteredReports" 
            :key="report.id"
            class="report-item"
          >
            <div class="report-info">
              <div class="report-name">{{ report.report_name }}</div>
              <div class="report-meta">
                <span class="report-task">{{ report.task_name }}</span>
                <span class="report-date">{{ formatDate(report.created_at) }}</span>
              </div>
            </div>
            
            <div class="report-format">
              <span :class="['format-badge', `format-${report.report_type}`]">
                {{ (report.report_type || '').toUpperCase() }}
              </span>
            </div>
            
            <div class="report-size">
              {{ formatFileSize(report.file_size) }}
            </div>
            
            <div class="report-actions">
              <button @click="downloadReport(report)" class="btn-icon" title="下载" :disabled="downloading === report.id">
                <span v-if="downloading === report.id">⏳</span>
                <span v-else>📥</span>
              </button>
              <button @click="viewReport(report)" class="btn-icon" title="预览">
                👁️
              </button>
              <button @click="deleteReport(report.id)" class="btn-icon btn-danger" title="删除" :disabled="deleting === report.id">
                <span v-if="deleting === report.id">⏳</span>
                <span v-else>🗑️</span>
              </button>
            </div>
          </div>
        </div>
        
        <div v-if="!loadingReports && filteredReports.length === 0" class="empty-state">
          <div class="empty-icon">📋</div>
          <div class="empty-title">暂无报告</div>
          <div class="empty-description">生成第一个安全扫描报告</div>
        </div>
      </div>
    </div>

    <!-- 报告预览模态框 -->
    <div v-if="showPreviewModal" class="modal-overlay" @click="closePreviewModal">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h3 class="modal-title">报告预览</h3>
          <button @click="closePreviewModal" class="modal-close">×</button>
        </div>
        <div class="modal-body">
          <div v-if="previewLoading" class="preview-loading">
            <div class="loading-spinner"></div>
            <div class="loading-text">加载预览...</div>
          </div>
          <div v-else class="preview-content">
            <div class="preview-info">
              <div class="preview-item">
                <span class="preview-label">报告名称:</span>
                <span class="preview-value">{{ currentPreviewReport?.report_name }}</span>
              </div>
              <div class="preview-item">
                <span class="preview-label">关联任务:</span>
                <span class="preview-value">{{ currentPreviewReport?.task_name }}</span>
              </div>
              <div class="preview-item">
                <span class="preview-label">报告格式:</span>
                <span class="preview-value">{{ (currentPreviewReport?.report_type || '').toUpperCase() }}</span>
              </div>
              <div class="preview-item">
                <span class="preview-label">创建时间:</span>
                <span class="preview-value">{{ formatDate(currentPreviewReport?.created_at) }}</span>
              </div>
              <div class="preview-item">
                <span class="preview-label">文件大小:</span>
                <span class="preview-value">{{ formatFileSize(currentPreviewReport?.file_size) }}</span>
              </div>
            </div>
            <div v-if="currentPreviewReport?.description" class="preview-description">
              <h4>描述</h4>
              <p>{{ currentPreviewReport.description }}</p>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button @click="downloadReport(currentPreviewReport)" class="btn btn-primary">
            📥 下载报告
          </button>
          <button @click="closePreviewModal" class="btn btn-secondary">
            关闭
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { reportsApi, tasksApi } from '../utils/api.js'
import { formatDate } from '../utils/date.js'

export default {
  name: 'Reports',
  data() {
    return {
      scanTasks: [],
      reports: [],
      selectedTask: '',
      selectedFormat: 'html',
      selectedContent: ['summary', 'vulnerabilities', 'recommendations'],
      historyFilter: '',
      loadingTasks: false,
      loadingReports: false,
      generating: false,
      downloading: null,
      deleting: null,
      showPreviewModal: false,
      previewLoading: false,
      currentPreviewReport: null,
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
    formatDate,
    async fetchTasks() {
      this.loadingTasks = true
      try {
        const response = await tasksApi.getTasks()
        if (response.code === 200 && response.data && response.data.tasks) {
          this.scanTasks = response.data.tasks
        } else if (Array.isArray(response.data)) {
          this.scanTasks = response.data
        } else {
          this.scanTasks = []
        }
      } catch (error) {
        console.error('获取任务列表失败:', error)
        this.scanTasks = []
      } finally {
        this.loadingTasks = false
      }
    },
    async fetchReports() {
      this.loadingReports = true
      try {
        const response = await reportsApi.list()
        if (response.code === 200 && response.data && response.data.reports) {
          this.reports = response.data.reports
        } else {
          this.reports = response.data || []
        }
      } catch (error) {
        console.error('获取报告列表失败:', error)
        this.reports = []
      } finally {
        this.loadingReports = false
      }
    },
    async generateReport() {
      if (!this.canGenerate) return
      
      const task = this.scanTasks.find(t => t.id == this.selectedTask)
      if (!task) return

      this.generating = true
      try {
        const reportData = {
          task_id: task.id,
          format: this.selectedFormat,
          content: this.selectedContent,
          name: `${task.task_name}报告`
        }
        
        const response = await reportsApi.create(reportData)
        if (response.code === 200) {
          alert('报告生成成功！')
          await this.fetchReports()
        } else {
          alert('生成报告失败: ' + (response.message || '未知错误'))
        }
      } catch (error) {
        console.error('生成报告失败:', error)
        alert('生成报告失败: ' + error.message)
      } finally {
        this.generating = false
      }
    },
    downloadReport(report) {
      if (!report) return
      
      this.downloading = report.id
      const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:3000/api'
      const url = `${baseUrl}/reports/${report.id}/export?format=${report.report_type}`
      
      const link = document.createElement('a')
      link.href = url
      link.download = report.report_name || `report.${report.report_type}`
      link.target = '_blank'
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      
      setTimeout(() => {
        this.downloading = null
      }, 1000)
    },
    async viewReport(report) {
      this.currentPreviewReport = report
      this.showPreviewModal = true
      this.previewLoading = true
      
      try {
        const response = await reportsApi.get(report.id)
        if (response.code === 200) {
          this.currentPreviewReport = { ...report, ...response.data }
        }
      } catch (error) {
        console.error('获取报告详情失败:', error)
      } finally {
        this.previewLoading = false
      }
    },
    closePreviewModal() {
      this.showPreviewModal = false
      this.currentPreviewReport = null
      this.previewLoading = false
    },
    async deleteReport(reportId) {
      if (confirm('确定要删除这个报告吗？')) {
        this.deleting = reportId
        try {
          const response = await reportsApi.delete(reportId)
          if (response.code === 200) {
            this.reports = this.reports.filter(r => r.id !== reportId)
            alert('删除成功')
          } else {
            alert('删除失败: ' + (response.message || '未知错误'))
          }
        } catch (error) {
          console.error('删除报告失败:', error)
          alert('删除报告失败')
        } finally {
          this.deleting = null
        }
      }
    },
    formatFileSize(bytes) {
      if (!bytes) return '0 B'
      const k = 1024
      const sizes = ['B', 'KB', 'MB', 'GB']
      const i = Math.floor(Math.log(bytes) / Math.log(k))
      return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
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
  display: block;
}

.form-section {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
  max-width: 800px;
  margin: 0 auto;
}

.form-hint {
  display: block;
  font-size: 12px;
  color: var(--text-secondary);
  margin-top: var(--spacing-xs);
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

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: var(--spacing-xl);
  gap: var(--spacing-md);
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 4px solid var(--border-color);
  border-top-color: var(--secondary-color);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.loading-text {
  color: var(--text-secondary);
  font-size: 14px;
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

.btn-icon:hover:not(:disabled) {
  background-color: var(--background-color);
}

.btn-icon:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-icon.btn-danger:hover:not(:disabled) {
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
  padding: var(--spacing-md);
}

.modal-content {
  background: white;
  border-radius: var(--border-radius);
  max-width: 600px;
  width: 100%;
  max-height: 90vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-lg);
  border-bottom: 1px solid var(--border-color);
}

.modal-title {
  margin: 0;
  font-size: 18px;
  font-weight: bold;
}

.modal-close {
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  padding: 0;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--border-radius);
  transition: background-color 0.2s ease;
}

.modal-close:hover {
  background-color: var(--background-color);
}

.modal-body {
  padding: var(--spacing-lg);
  overflow-y: auto;
  flex: 1;
}

.preview-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--spacing-md);
  padding: var(--spacing-xl);
}

.preview-content {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
}

.preview-info {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.preview-item {
  display: flex;
  gap: var(--spacing-sm);
}

.preview-label {
  font-weight: bold;
  color: var(--text-secondary);
  min-width: 80px;
}

.preview-value {
  color: var(--text-primary);
}

.preview-description {
  padding-top: var(--spacing-md);
  border-top: 1px solid var(--border-color);
}

.preview-description h4 {
  margin: 0 0 var(--spacing-sm) 0;
  font-size: 14px;
  font-weight: bold;
}

.preview-description p {
  margin: 0;
  color: var(--text-secondary);
  line-height: 1.6;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: var(--spacing-md);
  padding: var(--spacing-lg);
  border-top: 1px solid var(--border-color);
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
  
  .modal-content {
    max-height: 95vh;
  }
}
</style>
