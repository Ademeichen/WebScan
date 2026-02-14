<template>
  <div class="notification-detail">
    <div v-if="loading" class="loading-container">
      <Loading text="加载通知详情中..." />
    </div>

    <div v-else-if="notification" class="detail-content">
      <div class="page-header">
        <button class="btn-back" @click="goBack">
          ← 返回
        </button>
        <h1>通知详情</h1>
        <div class="header-actions">
          <button v-if="!notification.read" @click="handleMarkAsRead" class="btn btn-secondary">
            标记为已读
          </button>
          <button @click="handleDelete" class="btn btn-danger">
            删除
          </button>
        </div>
      </div>

      <div class="notification-card">
        <div class="notification-header">
          <div class="notification-type" :class="`type-${notification.type}`">
            <span class="type-icon">{{ getTypeIcon(notification.type) }}</span>
            <span class="type-label">{{ getTypeLabel(notification.type) }}</span>
          </div>
          <div class="notification-time">
            {{ notification.time || formatDate(notification.created_at) }}
          </div>
        </div>

        <div class="notification-body">
          <h2 class="notification-title">{{ notification.title }}</h2>
          <div class="notification-message">
            {{ notification.message }}
          </div>
        </div>

        <div v-if="notification.data" class="notification-extra">
          <h3>详细信息</h3>
          <pre class="data-content">{{ JSON.stringify(notification.data, null, 2) }}</pre>
        </div>

        <div v-if="notification.link" class="notification-link">
          <button @click="handleNavigate" class="btn btn-primary">
            查看详情 →
          </button>
        </div>
      </div>
    </div>

    <div v-else class="error-state">
      <div class="error-icon">⚠️</div>
      <p>{{ errorMessage || '通知加载失败' }}</p>
      <button class="btn btn-primary" @click="loadNotification">重试</button>
    </div>

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
import { useRoute, useRouter } from 'vue-router'
import { notificationsApi } from '@/utils/api'
import Loading from '@/components/common/Loading.vue'
import Alert from '@/components/common/Alert.vue'
import { formatDate } from '@/utils/date'

export default {
  name: 'NotificationDetail',
  components: {
    Loading,
    Alert
  },
  setup() {
    const route = useRoute()
    const router = useRouter()
    const loading = ref(true)
    const errorMessage = ref('')
    const successMessage = ref('')
    const notification = ref(null)

    const loadNotification = async () => {
      loading.value = true
      errorMessage.value = ''
      
      try {
        const notificationId = route.query.id || route.params.id
        if (!notificationId) {
          throw new Error('缺少通知ID参数')
        }

        const response = await notificationsApi.getNotification(notificationId)
        if (response.code === 200 && response.data) {
          notification.value = response.data
        } else {
          throw new Error('未找到通知信息')
        }
      } catch (error) {
        console.error('加载通知详情失败:', error)
        errorMessage.value = error.message || '加载通知详情失败'
      } finally {
        loading.value = false
      }
    }

    const getTypeIcon = (type) => {
      const iconMap = {
        'high-vulnerability': '🔴',
        'medium-vulnerability': '🟠',
        'low-vulnerability': '🟡',
        'scan-completed': '✅',
        'scan-failed': '❌',
        'scan-started': '🚀',
        'system-update': '🔄',
        'info': 'ℹ️',
        'warning': '⚠️',
        'error': '❌',
        'success': '✅'
      }
      return iconMap[type] || 'ℹ️'
    }

    const getTypeLabel = (type) => {
      const labelMap = {
        'high-vulnerability': '高危漏洞',
        'medium-vulnerability': '中危漏洞',
        'low-vulnerability': '低危漏洞',
        'scan-completed': '扫描完成',
        'scan-failed': '扫描失败',
        'scan-started': '扫描开始',
        'system-update': '系统更新',
        'info': '信息',
        'warning': '警告',
        'error': '错误',
        'success': '成功'
      }
      return labelMap[type] || type
    }

    const handleMarkAsRead = async () => {
      if (!notification.value) return
      
      try {
        const response = await notificationsApi.markAsRead(notification.value.id)
        if (response.code === 200) {
          notification.value.read = true
          successMessage.value = '已标记为已读'
        }
      } catch (error) {
        console.error('标记已读失败:', error)
        errorMessage.value = '标记已读失败'
      }
    }

    const handleDelete = async () => {
      if (!notification.value) return
      
      if (confirm('确定要删除此通知吗？')) {
        try {
          const response = await notificationsApi.deleteNotification(notification.value.id)
          if (response.code === 200) {
            successMessage.value = '删除成功'
            setTimeout(() => {
              router.push('/notifications')
            }, 1000)
          }
        } catch (error) {
          console.error('删除通知失败:', error)
          errorMessage.value = '删除通知失败'
        }
      }
    }

    const handleNavigate = () => {
      if (notification.value && notification.value.link) {
        router.push(notification.value.link)
      }
    }

    const goBack = () => {
      router.back()
    }

    onMounted(() => {
      loadNotification()
    })

    return {
      loading,
      errorMessage,
      successMessage,
      notification,
      getTypeIcon,
      getTypeLabel,
      handleMarkAsRead,
      handleDelete,
      handleNavigate,
      goBack,
      formatDate
    }
  }
}
</script>

<style scoped>
.notification-detail {
  padding: var(--spacing-xl);
}

.loading-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 400px;
}

.detail-content {
  max-width: 900px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-xl);
  padding-bottom: var(--spacing-lg);
  border-bottom: 1px solid var(--border-color);
}

.btn-back {
  padding: var(--spacing-sm) var(--spacing-md);
  background-color: var(--color-secondary);
  color: #1a1a1a;
  border: none;
  border-radius: var(--border-radius);
  cursor: pointer;
  transition: background-color 0.3s;
}

.btn-back:hover {
  background-color: var(--color-secondary-dark);
}

.page-header h1 {
  margin: 0;
  flex: 1;
  font-size: 1.75rem;
  color: var(--text-primary);
}

.header-actions {
  display: flex;
  gap: var(--spacing-md);
}

.notification-card {
  background-color: var(--card-bg);
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius-lg);
  padding: var(--spacing-xl);
  box-shadow: var(--shadow-md);
}

.notification-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-lg);
  padding-bottom: var(--spacing-md);
  border-bottom: 1px solid var(--border-color);
}

.notification-type {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-sm) var(--spacing-md);
  border-radius: var(--border-radius);
  font-size: 0.875rem;
  font-weight: 600;
}

.type-high-vulnerability {
  background-color: var(--color-critical-bg);
  color: var(--color-critical);
}

.type-medium-vulnerability {
  background-color: var(--color-error-bg);
  color: var(--color-error);
}

.type-low-vulnerability {
  background-color: var(--color-warning-bg);
  color: var(--color-warning);
}

.type-scan-completed {
  background-color: var(--color-success-bg);
  color: var(--color-success);
}

.type-scan-failed {
  background-color: var(--color-error-bg);
  color: var(--color-error);
}

.type-scan-started {
  background-color: var(--color-info-bg);
  color: var(--color-info);
}

.type-system-update {
  background-color: var(--color-primary-bg);
  color: var(--color-primary);
}

.type-info {
  background-color: var(--color-info-bg);
  color: var(--color-info);
}

.type-warning {
  background-color: var(--color-warning-bg);
  color: var(--color-warning);
}

.type-error {
  background-color: var(--color-error-bg);
  color: var(--color-error);
}

.type-success {
  background-color: var(--color-success-bg);
  color: var(--color-success);
}

.type-icon {
  font-size: 1.25rem;
}

.notification-time {
  color: var(--text-secondary);
  font-size: 0.875rem;
}

.notification-body {
  margin-bottom: var(--spacing-lg);
}

.notification-title {
  margin: 0 0 var(--spacing-md) 0;
  font-size: 1.5rem;
  color: var(--text-primary);
  font-weight: 600;
}

.notification-message {
  padding: var(--spacing-lg);
  background-color: var(--bg-secondary);
  border-radius: var(--border-radius);
  line-height: 1.6;
  color: var(--text-secondary);
}

.notification-extra {
  margin-bottom: var(--spacing-lg);
}

.notification-extra h3 {
  margin: 0 0 var(--spacing-md) 0;
  font-size: 1rem;
  color: var(--text-primary);
  font-weight: 600;
}

.data-content {
  padding: var(--spacing-md);
  background-color: var(--bg-secondary);
  border-radius: var(--border-radius);
  font-family: 'Courier New', monospace;
  font-size: 0.875rem;
  color: var(--text-secondary);
  overflow-x: auto;
  white-space: pre-wrap;
  word-wrap: break-word;
}

.notification-link {
  display: flex;
  justify-content: center;
}

.btn {
  padding: var(--spacing-md) var(--spacing-lg);
  border: none;
  border-radius: var(--border-radius);
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s;
}

.btn-primary {
  background-color: var(--color-primary);
  color: #1a1a1a;
}

.btn-primary:hover {
  background-color: var(--color-primary-dark);
}

.btn-secondary {
  background-color: var(--color-secondary);
  color: #1a1a1a;
}

.btn-secondary:hover {
  background-color: var(--color-secondary-dark);
}

.btn-danger {
  background-color: var(--color-error);
  color: #ffffff;
}

.btn-danger:hover {
  background-color: var(--color-error-dark);
}

.error-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--spacing-xxl);
  text-align: center;
}

.error-icon {
  font-size: 4rem;
  margin-bottom: var(--spacing-lg);
}

.error-state p {
  margin: 0 0 var(--spacing-lg) 0;
  color: var(--text-secondary);
  font-size: 1rem;
}

@media (max-width: 768px) {
  .notification-detail {
    padding: var(--spacing-md);
  }

  .page-header {
    flex-direction: column;
    align-items: flex-start;
    gap: var(--spacing-md);
  }

  .page-header h1 {
    font-size: 1.5rem;
  }

  .header-actions {
    width: 100%;
    justify-content: flex-start;
  }

  .notification-card {
    padding: var(--spacing-lg);
  }

  .notification-title {
    font-size: 1.25rem;
  }
}
</style>
