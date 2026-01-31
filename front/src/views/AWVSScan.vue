<template>
  <div class="awvs-scan">
    <div class="page-header">
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

      <div v-if="recentScans && recentScans.length > 0" class="recent-section">
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
              <span class="stat-item" v-if="scan.result.vulnerabilities.low > 0">
                低危: {{ scan.result.vulnerabilities.low }}
              </span>
            </div>
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
          recentScans.value = response.data.slice(0, 5).map(scan => {
            const currentSession = scan.current_session || {}
            const severityCounts = currentSession.severity_counts || {}
            const target = scan.target || {}
            
            return {
              id: scan.scan_id,
              task_name: target.description || target.address || 'AWVS Scan',
              target: target.address || '',
              status: currentSession.status || 'unknown',
              created_at: currentSession.start_date || scan.next_run || new Date().toISOString(),
              result: {
                vulnerabilities: {
                  critical: severityCounts.critical || 0,
                  high: severityCounts.high || 0,
                  medium: severityCounts.medium || 0,
                  low: severityCounts.low || 0
                }
              }
            }
          })
        }
      } catch (error) {
        console.error('加载最近扫描失败:', error)
      }
    }

    const handleSubmit = () => {
      console.log('提交AWVS扫描')
    }

    const handleSuccess = () => {
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
</script>

<style scoped>
.awvs-scan {
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
  background-color: var(--card-background);
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
  transition: all var(--transition-base);
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
}
</style>
