<template>
  <div class="awvs-scan">
    <div class="page-header">
<<<<<<< HEAD
      <h1>AWVS扫描</h1>
      <p class="subtitle">使用Acunetix Web Vulnerability Scanner进行深度安全扫描</p>
=======
<<<<<<< HEAD
      <h1>AWVS扫描</h1>
      <p class="subtitle">使用Acunetix Web Vulnerability Scanner进行深度安全扫描</p>
    </div>

    <div class="scan-layout">
      <div class="form-section">
        <AWVSScanForm
          @submit="handleSubmit"
          @success="handleSuccess"
          @error="handleError"
        />
      </div>

      <div v-if="recentScans.length > 0" class="recent-section">
        <h3>最近扫描</h3>
        <div class="recent-list">
          <div
            v-for="scan in recentScans"
            :key="scan.id"
            class="recent-item"
            @click="handleViewScan(scan.id)"
          >
            <div class="recent-header">
              <span class="recent-name">{{ scan.task_name }}</span>
              <span class="recent-status" :class="`status-${scan.status}`">
                {{ getStatusText(scan.status) }}
              </span>
            </div>
            <div class="recent-info">
              <span class="recent-target">{{ scan.target }}</span>
              <span class="recent-time">{{ formatDate(scan.created_at) }}</span>
            </div>
            <div v-if="scan.result && scan.result.vulnerabilities" class="recent-stats">
              <span class="stat-item" v-if="scan.result.vulnerabilities.critical > 0">
                严重: {{ scan.result.vulnerabilities.critical }}
              </span>
              <span class="stat-item" v-if="scan.result.vulnerabilities.high > 0">
                高危: {{ scan.result.vulnerabilities.high }}
              </span>
              <span class="stat-item" v-if="scan.result.vulnerabilities.medium > 0">
                中危: {{ scan.result.vulnerabilities.medium }}
              </span>
=======
      <h1>AWVS 漏洞扫描</h1>
      <p class="page-description">使用 Acunetix Web Vulnerability Scanner 进行专业的漏洞扫描</p>
>>>>>>> origin/renruipeng
    </div>

    <div class="scan-layout">
      <div class="form-section">
        <AWVSScanForm
          @submit="handleSubmit"
          @success="handleSuccess"
          @error="handleError"
        />
      </div>

      <div v-if="recentScans.length > 0" class="recent-section">
        <h3>最近扫描</h3>
        <div class="recent-list">
          <div
            v-for="scan in recentScans"
            :key="scan.id"
            class="recent-item"
            @click="handleViewScan(scan.id)"
          >
            <div class="recent-header">
              <span class="recent-name">{{ scan.task_name }}</span>
              <span class="recent-status" :class="`status-${scan.status}`">
                {{ getStatusText(scan.status) }}
              </span>
            </div>
<<<<<<< HEAD
            <div class="recent-info">
              <span class="recent-target">{{ scan.target }}</span>
              <span class="recent-time">{{ formatDate(scan.created_at) }}</span>
            </div>
            <div v-if="scan.result && scan.result.vulnerabilities" class="recent-stats">
              <span class="stat-item" v-if="scan.result.vulnerabilities.critical > 0">
                严重: {{ scan.result.vulnerabilities.critical }}
              </span>
              <span class="stat-item" v-if="scan.result.vulnerabilities.high > 0">
                高危: {{ scan.result.vulnerabilities.high }}
              </span>
              <span class="stat-item" v-if="scan.result.vulnerabilities.medium > 0">
                中危: {{ scan.result.vulnerabilities.medium }}
              </span>
=======
          </div>
          <div v-else class="status-disconnected">
            <div class="status-icon error">✗</div>
            <div class="status-info">
              <h4>AWVS 服务连接失败</h4>
              <p>{{ healthStatus.error || '无法连接到 AWVS 服务' }}</p>
>>>>>>> de97d03d8b5dfa00af0eaddf983e9c20433e9b15
>>>>>>> origin/renruipeng
            </div>
          </div>
        </div>
      </div>
    </div>

<<<<<<< HEAD
=======
<<<<<<< HEAD
>>>>>>> origin/renruipeng
    <Alert
      v-if="errorMessage"
      type="error"
      :message="errorMessage"
      @close="errorMessage = ''"
    />
<<<<<<< HEAD
=======

    <Alert
      v-if="successMessage"
      type="success"
      :message="successMessage"
      @close="successMessage = ''"
    />
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { awvsApi } from '@/utils/api'
import AWVSScanForm from '@/components/business/AWVSScanForm.vue'
import Alert from '@/components/common/Alert.vue'
import { formatDate } from '@/utils/date'

export default {
  name: 'AWVSScan',
  components: {
    AWVSScanForm,
    Alert
  },
  setup() {
    const router = useRouter()
    const errorMessage = ref('')
    const successMessage = ref('')
    const recentScans = ref([])

    const loadRecentScans = async () => {
      try {
        const response = await awvsApi.getScans()
        if (response && response.data) {
          recentScans.value = response.data.slice(0, 5)
        }
      } catch (error) {
        console.error('加载最近扫描失败:', error)
      }
    }

    const handleSubmit = (formData) => {
      console.log('提交AWVS扫描:', formData)
    }

    const handleSuccess = (data) => {
      successMessage.value = 'AWVS扫描任务创建成功'
      loadRecentScans()
    }

    const handleError = (error) => {
      errorMessage.value = error.message || '创建AWVS扫描任务失败'
    }

    const handleViewScan = (scanId) => {
      router.push(`/vulnerability-results?task=${scanId}`)
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

    onMounted(() => {
      loadRecentScans()
    })

    return {
      errorMessage,
      successMessage,
      recentScans,
      handleSubmit,
      handleSuccess,
      handleError,
      handleViewScan,
      getStatusText,
      formatDate
    }
  }
}
=======
    <!-- 创建扫描任务 -->
    <div class="create-scan-section">
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">创建新的扫描任务</h3>
        </div>
        <div class="card-body">
          <form @submit.prevent="createScan" class="scan-form">
            <div class="form-group">
              <label class="form-label">目标 URL</label>
              <input
                v-model="scanForm.url"
                type="url"
                class="form-input"
                placeholder="http://example.com"
                required
              >
            </div>
            
            <div class="form-group">
              <label class="form-label">扫描类型</label>
              <select v-model="scanForm.scanType" class="form-select">
                <option value="full_scan">完整扫描</option>
                <option value="high_risk_vuln">高风险漏洞扫描</option>
                <option value="xss_vuln">XSS 漏洞扫描</option>
                <option value="sqli_vuln">SQL 注入漏洞扫描</option>
                <option value="weak_passwords">弱密码扫描</option>
                <option value="crawl_only">仅爬取</option>
              </select>
            </div>
            
            <div class="form-actions">
              <button type="submit" class="btn btn-primary" :disabled="scanForm.loading">
                <span v-if="scanForm.loading" class="spinner-small"></span>
                {{ scanForm.loading ? '创建中...' : '创建扫描任务' }}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
>>>>>>> origin/renruipeng

    <Alert
      v-if="successMessage"
      type="success"
      :message="successMessage"
      @close="successMessage = ''"
    />
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { awvsApi } from '@/utils/api'
import AWVSScanForm from '@/components/business/AWVSScanForm.vue'
import Alert from '@/components/common/Alert.vue'
import { formatDate } from '@/utils/date'

export default {
  name: 'AWVSScan',
  components: {
    AWVSScanForm,
    Alert
  },
  setup() {
    const router = useRouter()
    const errorMessage = ref('')
    const successMessage = ref('')
    const recentScans = ref([])

    const loadRecentScans = async () => {
      try {
        const response = await awvsApi.getScans()
        if (response && response.data) {
          recentScans.value = response.data.slice(0, 5)
        }
      } catch (error) {
        console.error('加载最近扫描失败:', error)
      }
    }

    const handleSubmit = (formData) => {
      console.log('提交AWVS扫描:', formData)
    }

    const handleSuccess = (data) => {
      successMessage.value = 'AWVS扫描任务创建成功'
      loadRecentScans()
    }

    const handleError = (error) => {
      errorMessage.value = error.message || '创建AWVS扫描任务失败'
    }

    const handleViewScan = (scanId) => {
      router.push(`/vulnerability-results?task=${scanId}`)
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

    onMounted(() => {
      loadRecentScans()
    })

    return {
      errorMessage,
      successMessage,
      recentScans,
      handleSubmit,
      handleSuccess,
      handleError,
      handleViewScan,
      getStatusText,
      formatDate
    }
  }
}
<<<<<<< HEAD
=======

// 查看漏洞列表
const viewVulnerabilities = async (targetId) => {
  currentTargetId.value = targetId
  vulnerabilities.loading = true
  showVulnModal.value = true
  try {
    const response = await axios.get(`${API_BASE}/vulnerabilities/${targetId}`)
    if (response.data.code === 200) {
      vulnerabilities.data = response.data.data || []
    }
  } catch (error) {
    console.error('加载漏洞列表失败:', error)
  } finally {
    vulnerabilities.loading = false
  }
}

// 查看漏洞详情
const viewVulnDetail = async (vulnId) => {
  vulnDetail.loading = true
  showVulnDetailModal.value = true
  try {
    const response = await axios.get(`${API_BASE}/vulnerability/${vulnId}`)
    if (response.data.code === 200) {
      vulnDetail.data = response.data.data
    }
  } catch (error) {
    console.error('加载漏洞详情失败:', error)
  } finally {
    vulnDetail.loading = false
  }
}

// 关闭模态框
const closeVulnModal = () => {
  showVulnModal.value = false
  vulnerabilities.data = []
}

const closeVulnDetailModal = () => {
  showVulnDetailModal.value = false
  vulnDetail.data = null
}

// 辅助函数
const getStatusText = (status) => {
  const statusMap = {
    'processing': '进行中',
    'completed': '已完成',
    'failed': '失败',
    'aborted': '已中止',
    'queued': '排队中',
    'scanning': '扫描中',
    'submitted': '已提交',
    'pending': '等待中',
    'unknown': '未知'
  }
  return statusMap[status] || status
}

const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleString()
}

// 生命周期
onMounted(() => {
  checkHealth()
  loadScans()
  
  // 启动轮询，每5秒更新一次状态
  pollingTimer.value = setInterval(() => {
    loadScans(true)
  }, 5000)
})

onUnmounted(() => {
  if (pollingTimer.value) {
    clearInterval(pollingTimer.value)
  }
})
>>>>>>> de97d03d8b5dfa00af0eaddf983e9c20433e9b15
>>>>>>> origin/renruipeng
</script>

<style scoped>
.awvs-scan {
<<<<<<< HEAD
  padding: var(--spacing-xl);
=======
<<<<<<< HEAD
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
  font-size: 1.125rem;
  color: var(--text-primary);
  padding-bottom: var(--spacing-md);
  border-bottom: 1px solid var(--border-color);
}

.recent-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
  margin-top: var(--spacing-md);
}

.recent-item {
  padding: var(--spacing-md);
  background-color: var(--bg-secondary);
  border-radius: var(--border-radius);
=======
  padding: 20px;
>>>>>>> origin/renruipeng
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
  font-size: 1.125rem;
  color: var(--text-primary);
  padding-bottom: var(--spacing-md);
  border-bottom: 1px solid var(--border-color);
}

.recent-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
  margin-top: var(--spacing-md);
}

<<<<<<< HEAD
.recent-item {
  padding: var(--spacing-md);
  background-color: var(--bg-secondary);
  border-radius: var(--border-radius);
=======
.card-title {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
}

.card-body {
  padding: 20px;
}

.status-connected,
.status-disconnected {
  display: flex;
  align-items: center;
  gap: 16px;
}

.status-icon {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  font-weight: bold;
}

.status-icon.success {
  background: #d4edda;
  color: #155724;
}

.status-icon.error {
  background: #f8d7da;
  color: #721c24;
}

.status-info h4 {
  margin: 0 0 4px 0;
  font-size: 16px;
}

.status-info p {
  margin: 0;
  color: #666;
}

.scan-form {
  max-width: 600px;
}

.form-group {
  margin-bottom: 20px;
}

.form-label {
  display: block;
  margin-bottom: 8px;
  font-weight: 500;
  color: #333;
}

.form-input,
.form-select {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
}

.form-input:focus,
.form-select:focus {
  outline: none;
  border-color: #1890ff;
}

.form-actions {
  display: flex;
  gap: 12px;
}

.btn {
  padding: 8px 16px;
  border: none;
  border-radius: 4px;
  font-size: 14px;
>>>>>>> de97d03d8b5dfa00af0eaddf983e9c20433e9b15
>>>>>>> origin/renruipeng
  cursor: pointer;
  transition: all 0.3s;
}

<<<<<<< HEAD
=======
<<<<<<< HEAD
>>>>>>> origin/renruipeng
.recent-item:hover {
  background-color: var(--color-primary-bg);
  transform: translateX(4px);
  box-shadow: var(--shadow-sm);
<<<<<<< HEAD
=======
}

.recent-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-sm);
}

.recent-name {
  font-weight: 600;
  color: var(--text-primary);
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.recent-status {
  padding: var(--spacing-xs) var(--spacing-sm);
  border-radius: var(--border-radius-sm);
  font-size: 0.75rem;
  font-weight: 500;
  white-space: nowrap;
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

.recent-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.875rem;
  margin-bottom: var(--spacing-sm);
}

.recent-target {
  color: var(--text-primary);
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.recent-time {
  color: var(--text-secondary);
}

.recent-stats {
  display: flex;
  gap: var(--spacing-sm);
  flex-wrap: wrap;
  font-size: 0.875rem;
}

.stat-item {
  padding: var(--spacing-xs) var(--spacing-sm);
  background-color: var(--bg-primary);
  border-radius: var(--border-radius-sm);
  color: var(--text-secondary);
}

.stat-item.critical {
  background-color: var(--color-critical-bg);
  color: var(--color-critical);
}

.stat-item.high {
  background-color: var(--color-error-bg);
  color: var(--color-error);
}

.stat-item.medium {
  background-color: var(--color-warning-bg);
  color: var(--color-warning);
}

@media (max-width: 1024px) {
  .scan-layout {
    grid-template-columns: 1fr;
  }
=======
.btn-primary {
  background: #1890ff;
  color: white;
>>>>>>> origin/renruipeng
}

.recent-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-sm);
}

.recent-name {
  font-weight: 600;
  color: var(--text-primary);
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.recent-status {
  padding: var(--spacing-xs) var(--spacing-sm);
  border-radius: var(--border-radius-sm);
  font-size: 0.75rem;
  font-weight: 500;
  white-space: nowrap;
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

.recent-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.875rem;
  margin-bottom: var(--spacing-sm);
}

.recent-target {
  color: var(--text-primary);
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.recent-time {
  color: var(--text-secondary);
}

.recent-stats {
  display: flex;
  gap: var(--spacing-sm);
  flex-wrap: wrap;
  font-size: 0.875rem;
}

.stat-item {
  padding: var(--spacing-xs) var(--spacing-sm);
  background-color: var(--bg-primary);
  border-radius: var(--border-radius-sm);
  color: var(--text-secondary);
}

.stat-item.critical {
  background-color: var(--color-critical-bg);
  color: var(--color-critical);
}

.stat-item.high {
  background-color: var(--color-error-bg);
  color: var(--color-error);
}

.stat-item.medium {
  background-color: var(--color-warning-bg);
  color: var(--color-warning);
}

<<<<<<< HEAD
@media (max-width: 1024px) {
  .scan-layout {
    grid-template-columns: 1fr;
  }
=======
.vuln-item:hover {
  border-color: #1890ff;
  background: #f0f7ff;
}

.vuln-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
}

.severity-badge {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 600;
}

.severity-critical {
  background: #391010;
  color: #ff0000;
}

.severity-high {
  background: #fff2f0;
  color: #ff4d4f;
}

.severity-medium {
  background: #fff7e6;
  color: #fa8c16;
}

.severity-low {
  background: #f6ffed;
  color: #52c41a;
}

.vuln-header h4 {
  margin: 0;
  font-size: 14px;
}

.vuln-info p {
  margin: 4px 0;
  font-size: 12px;
  color: #666;
}

.vuln-detail {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.detail-section h4 {
  margin: 0 0 12px 0;
  font-size: 16px;
  color: #333;
}

.detail-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 12px;
}

.detail-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.detail-item label {
  font-size: 12px;
  color: #666;
  font-weight: 500;
}

.detail-item span {
  font-size: 14px;
  color: #333;
}

.detail-content {
  padding: 12px;
  background: #f5f5f5;
  border-radius: 4px;
  font-size: 14px;
  line-height: 1.6;
}

.code-block {
  padding: 12px;
  background: #f5f5f5;
  border-radius: 4px;
  overflow-x: auto;
  font-size: 12px;
  line-height: 1.5;
>>>>>>> de97d03d8b5dfa00af0eaddf983e9c20433e9b15
>>>>>>> origin/renruipeng
}
</style>
