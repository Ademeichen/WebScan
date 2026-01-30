<template>
  <div class="poc-scan">
    <div class="page-header">
<<<<<<< HEAD
=======
<<<<<<< HEAD
>>>>>>> origin/renruipeng
      <h1>POC扫描</h1>
      <p class="subtitle">使用POC（Proof of Concept）进行漏洞验证</p>
    </div>

    <div class="scan-layout">
      <div class="form-section">
        <POCScanForm
          @submit="handleSubmit"
          @success="handleSuccess"
          @error="handleError"
        />
<<<<<<< HEAD
=======
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
=======
      <div class="header-content">
        <h1>POC 漏洞扫描</h1>
        <button @click="showCreateModal = true" class="btn btn-success">
          <span>➕</span>
          创建扫描任务
        </button>
>>>>>>> origin/renruipeng
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
=======
            
            <div v-if="filteredResults.length === 0" class="empty-state">
              <div class="empty-icon">📭</div>
              <div class="empty-text">暂无扫描结果</div>
              <div class="empty-hint">点击"创建扫描任务"开始扫描</div>
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

    <Alert
      v-if="successMessage"
      type="success"
      :message="successMessage"
      @close="successMessage = ''"
    />
<<<<<<< HEAD
=======
=======
    <!-- 创建扫描任务模态框 -->
    <div v-if="showCreateModal" class="modal-overlay" @click="closeModal">
      <div class="modal" @click.stop>
        <div class="modal-header">
          <h2>创建POC扫描任务</h2>
          <button @click="closeModal" class="close-btn">×</button>
        </div>
        
        <div class="modal-body">
          <form @submit.prevent="createScan">
            <div class="form-group">
              <label class="form-label">目标URL</label>
              <input 
                v-model="newScan.target" 
                type="text" 
                class="form-input" 
                placeholder="输入目标URL，例如：http://example.com"
                required
              >
            </div>
            
            <div class="form-group">
              <label class="form-label">POC类型</label>
              <div class="poc-types-grid">
                <label v-for="pocType in availablePOCTypes" :key="pocType" class="checkbox-label">
                  <input 
                    v-model="newScan.pocTypes" 
                    type="checkbox" 
                    :value="pocType"
                    class="checkbox-input"
                  >
                  <span class="checkbox-custom"></span>
                  <span class="poc-type-label">{{ getPOCTypeName(pocType) }}</span>
                </label>
              </div>
              <div class="form-help">不选择则扫描所有POC类型</div>
            </div>
            
            <div class="form-group">
              <label class="form-label">超时时间（秒）</label>
              <input 
                v-model="newScan.timeout" 
                type="number" 
                min="1" 
                max="60"
                class="form-input"
                placeholder="默认10秒"
              >
            </div>
          </form>
        </div>
        
        <div class="modal-footer">
          <button @click="closeModal" class="btn btn-outline" :disabled="isScanning">
            取消
          </button>
          <button @click="createScan" class="btn btn-success" :disabled="isScanning">
            {{ isScanning ? '扫描中...' : '开始扫描' }}
          </button>
        </div>
      </div>
    </div>
>>>>>>> de97d03d8b5dfa00af0eaddf983e9c20433e9b15
>>>>>>> origin/renruipeng
  </div>
</template>

<script>
<<<<<<< HEAD
=======
<<<<<<< HEAD
>>>>>>> origin/renruipeng
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { pocApi } from '@/utils/api'
import POCScanForm from '@/components/business/POCScanForm.vue'
import Alert from '@/components/common/Alert.vue'
import { formatDate } from '@/utils/date'
<<<<<<< HEAD
=======

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

    const loadRecentScans = async () => {
      try {
        const response = await pocApi.getPOCResults()
        if (response && response.data) {
          recentScans.value = response.data.slice(0, 5)
        }
      } catch (error) {
        console.error('加载最近扫描失败:', error)
      }
    }

    const handleSubmit = (formData) => {
      console.log('提交POC扫描:', formData)
    }

    const handleSuccess = (data) => {
      successMessage.value = 'POC扫描任务创建成功'
      loadRecentScans()
    }

    const handleError = (error) => {
      errorMessage.value = error.message || '创建POC扫描任务失败'
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
=======
import { pocApi } from '../utils/api.js'
>>>>>>> origin/renruipeng

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

    const loadRecentScans = async () => {
      try {
        const response = await pocApi.getPOCResults()
        if (response && response.data) {
          recentScans.value = response.data.slice(0, 5)
        }
      } catch (error) {
        console.error('加载最近扫描失败:', error)
      }
    }

    const handleSubmit = (formData) => {
      console.log('提交POC扫描:', formData)
    }

    const handleSuccess = (data) => {
      successMessage.value = 'POC扫描任务创建成功'
      loadRecentScans()
    }

    const handleError = (error) => {
      errorMessage.value = error.message || '创建POC扫描任务失败'
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
<<<<<<< HEAD
      errorMessage,
      successMessage,
      recentScans,
      handleSubmit,
      handleSuccess,
      handleError,
      handleViewScan,
      getStatusText,
      formatDate
=======
      searchQuery: '',
      pocTypeFilter: '',
      vulnerabilityFilter: '',
      showCreateModal: false,
      isScanning: false,
      
      // 扫描结果
      results: [],
      availablePOCTypes: [],
      
      // 新扫描配置
      newScan: {
        target: '',
        pocTypes: [],
        timeout: 10
      }
    }
  },
  computed: {
    filteredResults() {
      return this.results.filter(result => {
        const matchesSearch = !this.searchQuery || 
          result.target.toLowerCase().includes(this.searchQuery.toLowerCase()) ||
          result.poc_type.toLowerCase().includes(this.searchQuery.toLowerCase())
        
        const matchesPOCType = !this.pocTypeFilter || result.poc_type === this.pocTypeFilter
        const matchesVulnerability = !this.vulnerabilityFilter || 
          (this.vulnerabilityFilter === 'vulnerable' && result.vulnerable) ||
          (this.vulnerabilityFilter === 'safe' && !result.vulnerable)
        
        return matchesSearch && matchesPOCType && matchesVulnerability
      })
    },
    totalScanned() {
      return this.results.length
    },
    vulnerableCount() {
      return this.results.filter(r => r.vulnerable).length
    },
    safeCount() {
      return this.results.filter(r => !r.vulnerable).length
    }
  },
  async mounted() {
    await this.loadAvailablePOCTypes()
  },
  methods: {
    async loadAvailablePOCTypes() {
      try {
        const response = await pocApi.getTypes()
        this.availablePOCTypes = response.data || response
      } catch (error) {
        console.error('加载POC类型失败:', error)
        this.availablePOCTypes = [
          'weblogic_cve_2020_2551',
          'weblogic_cve_2018_2628',
          'weblogic_cve_2018_2894',
          'struts2_009',
          'struts2_032',
          'tomcat_cve_2017_12615',
          'jboss_cve_2017_12149',
          'nexus_cve_2020_10199',
          'drupal_cve_2018_7600'
        ]
      }
    },
    async createScan() {
      if (!this.newScan.target) {
        alert('请输入目标URL')
        return
      }
      
      this.isScanning = true
      
      try {
        const payload = {
          target: this.newScan.target,
          poc_types: this.newScan.pocTypes.length > 0 ? this.newScan.pocTypes : undefined,
          timeout: this.newScan.timeout
        }
        
        const response = await pocApi.scan(payload)
        
        if (response.code === 200) {
          alert('扫描任务已创建！请前往"扫描任务"页面查看进度。')
        } else {
          alert(response.message || '扫描失败')
        }
      } catch (error) {
        console.error('扫描失败:', error)
        alert('扫描失败：' + (error.message || '未知错误'))
      } finally {
        this.isScanning = false
        this.closeModal()
      }
    },
    closeModal() {
      if (!this.isScanning) {
        this.showCreateModal = false
        this.resetForm()
      }
    },
    resetForm() {
      this.newScan = {
        target: '',
        pocTypes: [],
        timeout: 10
      }
    },
    getPOCTypeName(pocType) {
      const nameMap = {
        'weblogic_cve_2020_2551': 'WebLogic CVE-2020-2551',
        'weblogic_cve_2018_2628': 'WebLogic CVE-2018-2628',
        'weblogic_cve_2018_2894': 'WebLogic CVE-2018-2894',
        'struts2_009': 'Struts2 S2-009',
        'struts2_032': 'Struts2 S2-032',
        'tomcat_cve_2017_12615': 'Tomcat CVE-2017-12615',
        'jboss_cve_2017_12149': 'JBoss CVE-2017-12149',
        'nexus_cve_2020_10199': 'Nexus CVE-2020-10199',
        'drupal_cve_2018_7600': 'Drupal CVE-2018-7600'
      }
      return nameMap[pocType] || pocType
    },
    getSeverityText(severity) {
      const severityMap = {
        'high': '高危',
        'medium': '中危',
        'low': '低危'
      }
      return severityMap[severity] || '未知'
    },
    truncateMessage(message) {
      if (!message) return '-'
      return message.length > 50 ? message.substring(0, 50) + '...' : message
    },
    formatTime(timestamp) {
      if (!timestamp) return '-'
      const date = new Date(timestamp)
      return date.toLocaleString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
      })
>>>>>>> de97d03d8b5dfa00af0eaddf983e9c20433e9b15
>>>>>>> origin/renruipeng
    }
  }
}
</script>

<style scoped>
.poc-scan {
<<<<<<< HEAD
  padding: var(--spacing-xl);
=======
<<<<<<< HEAD
  padding: var(--spacing-xl);
=======
  max-width: 1400px;
  margin: 0 auto;
>>>>>>> de97d03d8b5dfa00af0eaddf983e9c20433e9b15
>>>>>>> origin/renruipeng
}

.page-header {
  margin-bottom: var(--spacing-xl);
}

<<<<<<< HEAD
.page-header h1 {
  margin: 0 0 var(--spacing-sm) 0;
  font-size: 2rem;
=======
<<<<<<< HEAD
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
  grid-template-columns: 1fr 300px;
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
  cursor: pointer;
  transition: all 0.3s;
}

.recent-item:hover {
  background-color: var(--color-primary-bg);
  transform: translateX(4px);
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
}

.recent-status {
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

.recent-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.875rem;
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

@media (max-width: 1024px) {
  .scan-layout {
    grid-template-columns: 1fr;
  }
}
</style>
=======
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
}

.search-box {
  flex: 1;
  max-width: 300px;
}

/* 统计卡片 */
.stats-container {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: var(--spacing-lg);
  margin-bottom: var(--spacing-xl);
}

.stat-card {
  background-color: var(--card-background);
  border-radius: var(--border-radius-lg);
  padding: var(--spacing-lg);
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  box-shadow: var(--shadow-sm);
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
}

.stat-card.stat-danger {
  border-left: 4px solid #e74c3c;
}

.stat-card.stat-success {
  border-left: 4px solid #27ae60;
}

.stat-icon {
  font-size: 32px;
  opacity: 0.8;
}

.stat-content {
  flex: 1;
}

.stat-value {
  font-size: 28px;
  font-weight: bold;
>>>>>>> origin/renruipeng
  color: var(--text-primary);
}

.subtitle {
  margin: 0;
  color: var(--text-secondary);
  font-size: 1rem;
}

.scan-layout {
  display: grid;
  grid-template-columns: 1fr 300px;
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
  cursor: pointer;
  transition: all 0.3s;
}

.recent-item:hover {
  background-color: var(--color-primary-bg);
  transform: translateX(4px);
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
}

.recent-status {
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

.recent-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.875rem;
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

@media (max-width: 1024px) {
  .scan-layout {
    grid-template-columns: 1fr;
  }
}
<<<<<<< HEAD
</style>
=======

/* 响应式设计 - 小屏手机 */
@media (max-width: 480px) {
  .page-header h1 {
    font-size: 20px;
  }
  
  .stat-card {
    padding: var(--spacing-sm);
  }
  
  .stat-value {
    font-size: 24px;
  }
  
  .stat-label {
    font-size: 13px;
  }
  
  .modal {
    width: 100%;
    max-height: 100vh;
    border-radius: 0;
  }
  
  .modal-header h2 {
    font-size: 18px;
  }
  
  .form-label {
    font-size: 13px;
  }
  
  .form-input {
    font-size: 13px;
  }
  
  .poc-type-label {
    font-size: 12px;
  }
  
  .btn {
    padding: var(--spacing-xs) var(--spacing-sm);
    font-size: 12px;
  }
}

/* 响应式设计 - 超小屏设备 */
@media (max-width: 360px) {
  .stat-value {
    font-size: 20px;
  }
  
  .stat-label {
    font-size: 12px;
  }
  
  .poc-type-badge,
  .cve-badge {
    font-size: 11px;
  }
  
  .status,
  .severity {
    font-size: 11px;
    padding: 2px 6px;
  }
}
</style>
>>>>>>> de97d03d8b5dfa00af0eaddf983e9c20433e9b15
>>>>>>> origin/renruipeng
