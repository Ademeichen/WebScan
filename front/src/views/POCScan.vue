<template>
  <div class="poc-scan-page">
    <div class="page-header">
      <div class="header-content">
        <h1>POC漏洞扫描</h1>
        <p class="subtitle">使用POC（Proof of Concept）进行漏洞验证，支持多种漏洞类型检测</p>
      </div>
      <div class="header-stats" v-if="totalScans > 0">
        <div class="stat-badge">
          <span class="stat-value">{{ totalScans }}</span>
          <span class="stat-label">总扫描</span>
        </div>
        <div class="stat-badge success">
          <span class="stat-value">{{ completedScans }}</span>
          <span class="stat-label">已完成</span>
        </div>
      </div>
    </div>

    <div class="main-layout">
      <div class="content-area">
        <div class="form-card card">
          <div class="card-header">
            <h2>
              <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
              </svg>
              扫描配置
            </h2>
          </div>
          <div class="card-body">
            <POCScanForm
              @submit="handleSubmit"
              @success="handleSuccess"
              @error="handleError"
            />
          </div>
        </div>

        <div v-if="currentScan" class="results-card card">
          <div class="card-header">
            <h2>
              <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"/>
              </svg>
              扫描结果
            </h2>
            <div class="header-actions">
              <span class="scan-status" :class="`status-${currentScan.status}`">
                {{ getStatusText(currentScan.status) }}
              </span>
            </div>
          </div>
          <div class="card-body">
            <div class="scan-info">
              <div class="info-item">
                <span class="label">目标:</span>
                <span class="value">{{ currentScan.target }}</span>
              </div>
              <div class="info-item">
                <span class="label">任务名称:</span>
                <span class="value">{{ currentScan.task_name }}</span>
              </div>
              <div class="info-item">
                <span class="label">开始时间:</span>
                <span class="value">{{ formatDate(currentScan.created_at) }}</span>
              </div>
            </div>

            <div v-if="currentScan.status === 'running'" class="progress-section">
              <div class="progress-header">
                <span>扫描进度</span>
                <span class="progress-percent">{{ scanProgress }}%</span>
              </div>
              <div class="progress-bar">
                <div class="progress-fill" :style="{ width: `${scanProgress}%` }"></div>
              </div>
              <div class="progress-details">
                <span>正在执行POC验证...</span>
                <span class="poc-count">{{ executedPOCs }}/{{ totalPOCs }}</span>
              </div>
            </div>

            <div class="vulnerability-summary" v-if="vulnerabilityStats.total > 0">
              <h3>漏洞统计</h3>
              <div class="stats-grid">
                <div class="stat-card critical" v-if="vulnerabilityStats.critical > 0">
                  <div class="stat-number">{{ vulnerabilityStats.critical }}</div>
                  <div class="stat-title">严重</div>
                </div>
                <div class="stat-card high" v-if="vulnerabilityStats.high > 0">
                  <div class="stat-number">{{ vulnerabilityStats.high }}</div>
                  <div class="stat-title">高危</div>
                </div>
                <div class="stat-card medium" v-if="vulnerabilityStats.medium > 0">
                  <div class="stat-number">{{ vulnerabilityStats.medium }}</div>
                  <div class="stat-title">中危</div>
                </div>
                <div class="stat-card low" v-if="vulnerabilityStats.low > 0">
                  <div class="stat-number">{{ vulnerabilityStats.low }}</div>
                  <div class="stat-title">低危</div>
                </div>
                <div class="stat-card info" v-if="vulnerabilityStats.info > 0">
                  <div class="stat-number">{{ vulnerabilityStats.info }}</div>
                  <div class="stat-title">信息</div>
                </div>
              </div>
            </div>

            <div class="poc-results" v-if="pocResults.length > 0">
              <h3>POC执行结果</h3>
              <div class="results-list">
                <div
                  v-for="(result, index) in pocResults"
                  :key="index"
                  class="result-item"
                  :class="{ 'has-vuln': result.vulnerable }"
                >
                  <div class="result-header">
                    <span class="poc-name">{{ result.poc_name }}</span>
                    <span class="result-status" :class="result.vulnerable ? 'vulnerable' : 'safe'">
                      {{ result.vulnerable ? '存在漏洞' : '安全' }}
                    </span>
                  </div>
                  <div class="result-details" v-if="result.vulnerable">
                    <div class="detail-item">
                      <span class="label">漏洞类型:</span>
                      <span class="value">{{ result.vuln_type }}</span>
                    </div>
                    <div class="detail-item" v-if="result.severity">
                      <span class="label">严重程度:</span>
                      <span class="value severity" :class="result.severity">{{ getSeverityText(result.severity) }}</span>
                    </div>
                    <div class="detail-item" v-if="result.description">
                      <span class="label">描述:</span>
                      <span class="value">{{ result.description }}</span>
                    </div>
                  </div>
                  <div class="result-time">
                    执行时间: {{ result.execution_time || 0 }}ms
                  </div>
                </div>
              </div>
            </div>

            <div class="no-results" v-if="currentScan.status === 'completed' && vulnerabilityStats.total === 0">
              <svg class="empty-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
              </svg>
              <p>未发现漏洞，目标系统安全</p>
            </div>
          </div>
        </div>
      </div>

      <aside class="sidebar">
        <div class="sidebar-card card">
          <div class="card-header">
            <h2>
              <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/>
              </svg>
              扫描历史
            </h2>
            <button class="refresh-btn" @click="loadRecentScans" :disabled="isLoadingHistory">
              <svg class="icon-sm" :class="{ 'spinning': isLoadingHistory }" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/>
              </svg>
            </button>
          </div>
          <div class="card-body">
            <div v-if="isLoadingHistory" class="loading-state">
              <div class="loading-spinner sm"></div>
              <span>加载中...</span>
            </div>
            <div v-else-if="recentScans.length === 0" class="empty-state">
              <svg class="empty-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"/>
              </svg>
              <p>暂无扫描记录</p>
            </div>
            <div v-else class="history-list">
              <div
                v-for="scan in recentScans"
                :key="scan.id"
                class="history-item"
                :class="{ 'active': currentScan && currentScan.id === scan.id }"
                @click="handleViewScan(scan)"
              >
                <div class="history-header">
                  <span class="history-name">{{ scan.task_name }}</span>
                  <span class="history-status" :class="`status-${scan.status}`">
                    {{ getStatusText(scan.status) }}
                  </span>
                </div>
                <div class="history-target">
                  <svg class="icon-xs" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <circle cx="12" cy="12" r="10"/>
                    <line x1="2" y1="12" x2="22" y2="12"/>
                    <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/>
                  </svg>
                  {{ scan.target }}
                </div>
                <div class="history-meta">
                  <span class="history-time">{{ formatDate(scan.created_at) }}</span>
                  <div class="history-vulns" v-if="scan.result && scan.result.vulnerabilities">
                    <span v-if="scan.result.vulnerabilities.critical > 0" class="vuln-badge critical">
                      {{ scan.result.vulnerabilities.critical }}
                    </span>
                    <span v-if="scan.result.vulnerabilities.high > 0" class="vuln-badge high">
                      {{ scan.result.vulnerabilities.high }}
                    </span>
                    <span v-if="scan.result.vulnerabilities.medium > 0" class="vuln-badge medium">
                      {{ scan.result.vulnerabilities.medium }}
                    </span>
                    <span v-if="scan.result.vulnerabilities.low > 0" class="vuln-badge low">
                      {{ scan.result.vulnerabilities.low }}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </aside>
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
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { tasksApi, pocApi } from '@/utils/api'
import POCScanForm from '@/components/business/POCScanForm.vue'
import Alert from '@/components/common/Alert.vue'
import { formatDate } from '@/utils/date'

export default {
  name: 'POCScan',
  components: {
    POCScanForm,
    Alert
  },
  setup() {
    const router = useRouter()
    const errorMessage = ref('')
    const successMessage = ref('')
    const recentScans = ref([])
    const currentScan = ref(null)
    const isLoadingHistory = ref(false)
    const scanProgress = ref(0)
    const executedPOCs = ref(0)
    const totalPOCs = ref(0)
    const pocResults = ref([])
    let pollInterval = null

    const vulnerabilityStats = computed(() => {
      const stats = { critical: 0, high: 0, medium: 0, low: 0, info: 0, total: 0 }
      if (currentScan.value && currentScan.value.result && currentScan.value.result.vulnerabilities) {
        stats.critical = currentScan.value.result.vulnerabilities.critical || 0
        stats.high = currentScan.value.result.vulnerabilities.high || 0
        stats.medium = currentScan.value.result.vulnerabilities.medium || 0
        stats.low = currentScan.value.result.vulnerabilities.low || 0
        stats.info = currentScan.value.result.vulnerabilities.info || 0
        stats.total = stats.critical + stats.high + stats.medium + stats.low + stats.info
      }
      if (pocResults.value.length > 0) {
        pocResults.value.forEach(result => {
          if (result.vulnerable && result.severity) {
            stats[result.severity] = (stats[result.severity] || 0) + 1
            stats.total++
          }
        })
      }
      return stats
    })

    const totalScans = computed(() => recentScans.value.length)
    const completedScans = computed(() => 
      recentScans.value.filter(scan => scan.status === 'completed').length
    )

    const loadRecentScans = async () => {
      isLoadingHistory.value = true
      try {
        const response = await tasksApi.getTasks({ task_type: 'poc_scan', limit: 10 })
        if (response && response.data && response.data.tasks) {
          recentScans.value = response.data.tasks
        }
      } catch (error) {
        console.error('加载最近扫描失败:', error)
      } finally {
        isLoadingHistory.value = false
      }
    }

    const loadScanDetails = async (taskId) => {
      try {
        const response = await tasksApi.getTask(taskId)
        if (response && response.data) {
          currentScan.value = response.data
          if (response.data.result && response.data.result.poc_results) {
            pocResults.value = response.data.result.poc_results
          }
          if (response.data.result && response.data.result.progress !== undefined) {
            scanProgress.value = response.data.result.progress
          }
          if (response.data.result && response.data.result.executed_pocs !== undefined) {
            executedPOCs.value = response.data.result.executed_pocs
          }
          if (response.data.result && response.data.result.total_pocs !== undefined) {
            totalPOCs.value = response.data.result.total_pocs
          }
        }
      } catch (error) {
        console.error('加载扫描详情失败:', error)
      }
    }

    const pollScanStatus = async () => {
      if (!currentScan.value || currentScan.value.status !== 'running') {
        return
      }
      try {
        const response = await tasksApi.getTask(currentScan.value.id)
        if (response && response.data) {
          currentScan.value = response.data
          if (response.data.result) {
            if (response.data.result.poc_results) {
              pocResults.value = response.data.result.poc_results
            }
            if (response.data.result.progress !== undefined) {
              scanProgress.value = response.data.result.progress
            }
            if (response.data.result.executed_pocs !== undefined) {
              executedPOCs.value = response.data.result.executed_pocs
            }
            if (response.data.result.total_pocs !== undefined) {
              totalPOCs.value = response.data.result.total_pocs
            }
          }
          if (response.data.status !== 'running') {
            stopPolling()
            loadRecentScans()
          }
        }
      } catch (error) {
        console.error('轮询扫描状态失败:', error)
      }
    }

    const startPolling = () => {
      if (pollInterval) {
        clearInterval(pollInterval)
      }
      pollInterval = setInterval(pollScanStatus, 2000)
    }

    const stopPolling = () => {
      if (pollInterval) {
        clearInterval(pollInterval)
        pollInterval = null
      }
    }

    const handleSubmit = () => {
      scanProgress.value = 0
      executedPOCs.value = 0
      totalPOCs.value = 0
      pocResults.value = []
    }

    const handleSuccess = (data) => {
      successMessage.value = 'POC扫描任务创建成功'
      if (data && data.task_id) {
        loadScanDetails(data.task_id)
        startPolling()
      }
      loadRecentScans()
    }

    const handleError = (error) => {
      errorMessage.value = error.message || '创建POC扫描任务失败'
    }

    const handleViewScan = async (scan) => {
      if (currentScan.value && currentScan.value.id === scan.id) {
        return
      }
      stopPolling()
      await loadScanDetails(scan.id)
      if (currentScan.value && currentScan.value.status === 'running') {
        startPolling()
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

    const getSeverityText = (severity) => {
      const severityMap = {
        critical: '严重',
        high: '高危',
        medium: '中危',
        low: '低危',
        info: '信息'
      }
      return severityMap[severity] || severity
    }

    onMounted(() => {
      loadRecentScans()
    })

    onUnmounted(() => {
      stopPolling()
    })

    return {
      errorMessage,
      successMessage,
      recentScans,
      currentScan,
      isLoadingHistory,
      scanProgress,
      executedPOCs,
      totalPOCs,
      pocResults,
      vulnerabilityStats,
      totalScans,
      completedScans,
      loadRecentScans,
      handleSubmit,
      handleSuccess,
      handleError,
      handleViewScan,
      getStatusText,
      getSeverityText,
      formatDate
    }
  }
}
</script>

<style scoped>
.poc-scan-page {
  padding: var(--spacing-lg);
  min-height: 100%;
  background-color: var(--background-color);
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: var(--spacing-xl);
  padding-bottom: var(--spacing-lg);
  border-bottom: 1px solid var(--border-color);
}

.header-content h1 {
  margin: 0 0 var(--spacing-xs) 0;
  font-size: 1.75rem;
  color: var(--text-primary);
  font-weight: 600;
}

.subtitle {
  margin: 0;
  color: var(--text-secondary);
  font-size: 0.9rem;
}

.header-stats {
  display: flex;
  gap: var(--spacing-md);
}

.stat-badge {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: var(--spacing-sm) var(--spacing-md);
  background-color: var(--bg-secondary);
  border-radius: var(--border-radius-lg);
  min-width: 80px;
}

.stat-badge.success {
  background-color: var(--color-success-bg);
}

.stat-value {
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--text-primary);
}

.stat-badge.success .stat-value {
  color: var(--color-success);
}

.stat-label {
  font-size: 0.75rem;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.main-layout {
  display: grid;
  grid-template-columns: 1fr 320px;
  gap: var(--spacing-xl);
  align-items: start;
}

.content-area {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xl);
}

.card {
  background-color: var(--card-background);
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius-lg);
  box-shadow: var(--shadow-sm);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-lg);
  border-bottom: 1px solid var(--border-color);
}

.card-header h2 {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  margin: 0;
  font-size: 1.125rem;
  color: var(--text-primary);
  font-weight: 600;
}

.card-header .icon {
  width: 20px;
  height: 20px;
  color: var(--color-primary);
}

.card-body {
  padding: var(--spacing-lg);
}

.form-card {
  background: linear-gradient(135deg, var(--card-background) 0%, rgba(64, 158, 255, 0.02) 100%);
}

.results-card {
  min-height: 300px;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
}

.scan-status {
  padding: var(--spacing-xs) var(--spacing-md);
  border-radius: var(--border-radius-full);
  font-size: 0.8rem;
  font-weight: 500;
}

.status-pending {
  background-color: var(--color-warning-bg);
  color: var(--color-warning);
}

.status-running {
  background-color: var(--color-info-bg);
  color: var(--color-info);
  animation: pulse 2s ease-in-out infinite;
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

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.7; }
}

.scan-info {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: var(--spacing-md);
  padding: var(--spacing-md);
  background-color: var(--bg-secondary);
  border-radius: var(--border-radius);
  margin-bottom: var(--spacing-lg);
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
}

.info-item .label {
  font-size: 0.75rem;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.info-item .value {
  font-size: 0.9rem;
  color: var(--text-primary);
  font-weight: 500;
}

.progress-section {
  margin-bottom: var(--spacing-lg);
  padding: var(--spacing-md);
  background-color: var(--bg-secondary);
  border-radius: var(--border-radius);
}

.progress-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-sm);
  font-size: 0.9rem;
  color: var(--text-primary);
}

.progress-percent {
  font-weight: 600;
  color: var(--color-primary);
}

.progress-bar {
  height: 8px;
  background-color: var(--border-color);
  border-radius: var(--border-radius-full);
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--color-primary) 0%, var(--color-primary-light-3) 100%);
  border-radius: var(--border-radius-full);
  transition: width 0.3s ease;
}

.progress-details {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: var(--spacing-sm);
  font-size: 0.8rem;
  color: var(--text-secondary);
}

.poc-count {
  font-weight: 500;
}

.vulnerability-summary {
  margin-bottom: var(--spacing-lg);
}

.vulnerability-summary h3 {
  margin: 0 0 var(--spacing-md) 0;
  font-size: 1rem;
  color: var(--text-primary);
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(100px, 1fr));
  gap: var(--spacing-md);
}

.stat-card {
  padding: var(--spacing-md);
  border-radius: var(--border-radius);
  text-align: center;
  background-color: var(--bg-secondary);
  border-left: 4px solid transparent;
}

.stat-card.critical {
  border-left-color: var(--critical-risk);
  background-color: rgba(192, 57, 43, 0.1);
}

.stat-card.high {
  border-left-color: var(--high-risk);
  background-color: rgba(231, 76, 60, 0.1);
}

.stat-card.medium {
  border-left-color: var(--medium-risk);
  background-color: rgba(243, 156, 18, 0.1);
}

.stat-card.low {
  border-left-color: var(--low-risk);
  background-color: rgba(52, 152, 219, 0.1);
}

.stat-card.info {
  border-left-color: var(--info-risk);
  background-color: rgba(149, 165, 166, 0.1);
}

.stat-number {
  font-size: 1.75rem;
  font-weight: 700;
  color: var(--text-primary);
}

.stat-card.critical .stat-number { color: var(--critical-risk); }
.stat-card.high .stat-number { color: var(--high-risk); }
.stat-card.medium .stat-number { color: var(--medium-risk); }
.stat-card.low .stat-number { color: var(--low-risk); }
.stat-card.info .stat-number { color: var(--info-risk); }

.stat-title {
  font-size: 0.8rem;
  color: var(--text-secondary);
  margin-top: var(--spacing-xs);
}

.poc-results {
  margin-top: var(--spacing-lg);
}

.poc-results h3 {
  margin: 0 0 var(--spacing-md) 0;
  font-size: 1rem;
  color: var(--text-primary);
}

.results-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
  max-height: 400px;
  overflow-y: auto;
}

.result-item {
  padding: var(--spacing-md);
  background-color: var(--bg-secondary);
  border-radius: var(--border-radius);
  border-left: 3px solid var(--color-success);
  transition: all var(--transition-base);
}

.result-item.has-vuln {
  border-left-color: var(--high-risk);
  background-color: rgba(231, 76, 60, 0.05);
}

.result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-sm);
}

.poc-name {
  font-weight: 600;
  color: var(--text-primary);
}

.result-status {
  padding: var(--spacing-xs) var(--spacing-sm);
  border-radius: var(--border-radius-sm);
  font-size: 0.75rem;
  font-weight: 500;
}

.result-status.safe {
  background-color: var(--color-success-bg);
  color: var(--color-success);
}

.result-status.vulnerable {
  background-color: var(--color-error-bg);
  color: var(--color-error);
}

.result-details {
  padding: var(--spacing-sm);
  background-color: var(--bg-primary);
  border-radius: var(--border-radius-sm);
  margin-bottom: var(--spacing-sm);
}

.detail-item {
  display: flex;
  gap: var(--spacing-sm);
  margin-bottom: var(--spacing-xs);
  font-size: 0.85rem;
}

.detail-item:last-child {
  margin-bottom: 0;
}

.detail-item .label {
  color: var(--text-secondary);
  min-width: 70px;
}

.detail-item .value {
  color: var(--text-primary);
}

.detail-item .value.severity {
  font-weight: 600;
}

.detail-item .value.severity.critical { color: var(--critical-risk); }
.detail-item .value.severity.high { color: var(--high-risk); }
.detail-item .value.severity.medium { color: var(--medium-risk); }
.detail-item .value.severity.low { color: var(--low-risk); }

.result-time {
  font-size: 0.75rem;
  color: var(--text-secondary);
}

.no-results {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--spacing-2xl);
  color: var(--color-success);
}

.empty-icon {
  width: 48px;
  height: 48px;
  margin-bottom: var(--spacing-md);
  stroke: currentColor;
}

.no-results p {
  margin: 0;
  font-size: 1rem;
}

.sidebar {
  position: sticky;
  top: var(--spacing-lg);
}

.sidebar-card {
  position: relative;
}

.refresh-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  padding: 0;
  border: none;
  background-color: transparent;
  border-radius: var(--border-radius);
  cursor: pointer;
  color: var(--text-secondary);
  transition: all var(--transition-base);
}

.refresh-btn:hover:not(:disabled) {
  background-color: var(--bg-secondary);
  color: var(--color-primary);
}

.refresh-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.icon-sm {
  width: 18px;
  height: 18px;
}

.icon-sm.spinning {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.loading-state,
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--spacing-xl);
  color: var(--text-secondary);
}

.loading-state {
  flex-direction: row;
  gap: var(--spacing-sm);
}

.loading-spinner.sm {
  width: 20px;
  height: 20px;
  border: 2px solid var(--border-color);
  border-top-color: var(--color-primary);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

.empty-state .empty-icon {
  width: 40px;
  height: 40px;
  margin-bottom: var(--spacing-sm);
  opacity: 0.5;
}

.empty-state p {
  margin: 0;
  font-size: 0.9rem;
}

.history-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
  max-height: calc(100vh - 300px);
  overflow-y: auto;
}

.history-item {
  padding: var(--spacing-md);
  background-color: var(--bg-secondary);
  border-radius: var(--border-radius);
  cursor: pointer;
  transition: all var(--transition-base);
  border: 2px solid transparent;
}

.history-item:hover {
  background-color: var(--color-primary-bg);
  transform: translateX(4px);
}

.history-item.active {
  border-color: var(--color-primary);
  background-color: var(--color-primary-bg);
}

.history-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-xs);
}

.history-name {
  font-weight: 600;
  color: var(--text-primary);
  font-size: 0.9rem;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  flex: 1;
  margin-right: var(--spacing-sm);
}

.history-status {
  padding: 2px var(--spacing-sm);
  border-radius: var(--border-radius-sm);
  font-size: 0.7rem;
  font-weight: 500;
  white-space: nowrap;
}

.history-target {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  font-size: 0.8rem;
  color: var(--text-secondary);
  margin-bottom: var(--spacing-xs);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.icon-xs {
  width: 12px;
  height: 12px;
  flex-shrink: 0;
}

.history-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.history-time {
  font-size: 0.75rem;
  color: var(--text-secondary);
}

.history-vulns {
  display: flex;
  gap: var(--spacing-xs);
}

.vuln-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 20px;
  height: 20px;
  padding: 0 var(--spacing-xs);
  border-radius: var(--border-radius-sm);
  font-size: 0.7rem;
  font-weight: 600;
}

.vuln-badge.critical {
  background-color: rgba(192, 57, 43, 0.2);
  color: var(--critical-risk);
}

.vuln-badge.high {
  background-color: rgba(231, 76, 60, 0.2);
  color: var(--high-risk);
}

.vuln-badge.medium {
  background-color: rgba(243, 156, 18, 0.2);
  color: var(--medium-risk);
}

.vuln-badge.low {
  background-color: rgba(52, 152, 219, 0.2);
  color: var(--low-risk);
}

@media (max-width: 1200px) {
  .main-layout {
    grid-template-columns: 1fr 280px;
  }
}

@media (max-width: 1024px) {
  .main-layout {
    grid-template-columns: 1fr;
  }

  .sidebar {
    position: static;
  }

  .history-list {
    max-height: 400px;
  }
}

@media (max-width: 768px) {
  .poc-scan-page {
    padding: var(--spacing-md);
  }

  .page-header {
    flex-direction: column;
    gap: var(--spacing-md);
  }

  .header-stats {
    width: 100%;
    justify-content: flex-start;
  }

  .scan-info {
    grid-template-columns: 1fr;
  }

  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
