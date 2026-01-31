<template>
  <div class="notifications">
    <div class="page-header">
      <h1>通知中心</h1>
      <div class="header-actions">
        <button @click="loadNotifications" class="btn btn-secondary">
          🔄 刷新
        </button>
        <button @click="handleMarkAllAsRead" class="btn btn-primary" :disabled="unreadCount === 0">
          全部标记已读 ({{ unreadCount }})
        </button>
      </div>
    </div>

    <div class="filters-section">
      <div class="filter-group">
        <label>状态:</label>
        <select v-model="filters.status" @change="loadNotifications">
          <option value="">全部</option>
          <option value="unread">未读</option>
          <option value="read">已读</option>
        </select>
      </div>

      <div class="filter-group">
        <label>类型:</label>
        <select v-model="filters.type" @change="loadNotifications">
          <option value="">全部</option>
          <option value="high-vulnerability">高危漏洞</option>
          <option value="medium-vulnerability">中危漏洞</option>
          <option value="low-vulnerability">低危漏洞</option>
          <option value="scan-completed">扫描完成</option>
          <option value="scan-failed">扫描失败</option>
          <option value="system-update">系统更新</option>
        </select>
      </div>

      <div class="filter-group">
        <button @click="handleDeleteRead" class="btn btn-danger" :disabled="readCount === 0">
          删除已读通知
        </button>
      </div>
    </div>

    <div v-if="loading" class="loading-container">
      <Loading text="加载通知中..." />
    </div>

    <div v-else-if="notifications.length === 0" class="empty-state">
      <div class="empty-icon">🔔</div>
      <h3>暂无通知</h3>
      <p>当前没有通知消息</p>
    </div>

    <div v-else class="notifications-list">
      <div
        v-for="notification in notifications"
        :key="notification.id"
        class="notification-item"
        :class="{ unread: !notification.read }"
        @click="handleViewNotification(notification)"
      >
        <div class="notification-type" :class="`type-${notification.type}`">
          <span class="type-icon">{{ getTypeIcon(notification.type) }}</span>
        </div>
        <div class="notification-content">
          <div class="notification-header">
            <span class="notification-title">{{ notification.title }}</span>
            <span class="notification-time">{{ notification.time || formatDate(notification.created_at) }}</span>
          </div>
          <div class="notification-message">{{ notification.message }}</div>
        </div>
        <div class="notification-actions">
          <button v-if="!notification.read" @click.stop="handleMarkAsRead(notification)" class="btn-icon" title="标记已读">
            ✓
          </button>
          <button @click.stop="handleDelete(notification)" class="btn-icon btn-danger" title="删除">
            🗑
          </button>
        </div>
      </div>
    </div>

    <div v-if="total > limit" class="pagination">
      <button
        class="btn-page"
        :disabled="currentPage === 1"
        @click="currentPage--; loadNotifications()"
      >
        上一页
      </button>
      <span class="page-info">第 {{ currentPage }} / {{ totalPages }} 页</span>
      <button
        class="btn-page"
        :disabled="currentPage === totalPages"
        @click="currentPage++; loadNotifications()"
      >
        下一页
      </button>
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
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { notificationsApi } from '@/utils/api'
import Loading from '@/components/common/Loading.vue'
import Alert from '@/components/common/Alert.vue'
import { formatDate } from '@/utils/date'

export default {
  name: 'NotificationsPage',
  components: {
    Loading,
    Alert
  },
  setup() {
    const router = useRouter()
    const loading = ref(true)
    const errorMessage = ref('')
    const successMessage = ref('')
    const notifications = ref([])
    const total = ref(0)
    const currentPage = ref(1)
    const limit = ref(20)

    const filters = ref({
      status: '',
      type: ''
    })

    const totalPages = computed(() => Math.ceil(total.value / limit.value))

    const unreadCount = computed(() => {
      return notifications.value.filter(n => !n.read).length
    })

    const readCount = computed(() => {
      return notifications.value.filter(n => n.read).length
    })

    const loadNotifications = async () => {
      loading.value = true
      errorMessage.value = ''
      
      try {
        const params = {
          ...filters.value,
          skip: (currentPage.value - 1) * limit.value,
          limit: limit.value
        }

        if (filters.value.status === 'unread') {
          params.unread_only = true
        }

        const response = await notificationsApi.getNotifications(params)
        if (response.code === 200) {
          notifications.value = response.data.notifications || []
          total.value = response.data.total || 0
        }
      } catch (error) {
        console.error('加载通知失败:', error)
        errorMessage.value = '加载通知失败'
        notifications.value = []
        total.value = 0
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

    const handleViewNotification = (notification) => {
      router.push(`/notification/${notification.id}`)
    }

    const handleMarkAsRead = async (notification) => {
      try {
        const response = await notificationsApi.markAsRead(notification.id)
        if (response.code === 200) {
          notification.read = true
          successMessage.value = '已标记为已读'
        }
      } catch (error) {
        console.error('标记已读失败:', error)
        errorMessage.value = '标记已读失败'
      }
    }

    const handleMarkAllAsRead = async () => {
      try {
        const response = await notificationsApi.markAllAsRead()
        if (response.code === 200) {
          notifications.value.forEach(n => n.read = true)
          successMessage.value = '已全部标记为已读'
        }
      } catch (error) {
        console.error('全部标记已读失败:', error)
        errorMessage.value = '全部标记已读失败'
      }
    }

    const handleDelete = async (notification) => {
      if (confirm('确定要删除此通知吗？')) {
        try {
          const response = await notificationsApi.deleteNotification(notification.id)
          if (response.code === 200) {
            notifications.value = notifications.value.filter(n => n.id !== notification.id)
            total.value -= 1
            successMessage.value = '删除成功'
          }
        } catch (error) {
          console.error('删除通知失败:', error)
          errorMessage.value = '删除通知失败'
        }
      }
    }

    const handleDeleteRead = async () => {
      if (confirm('确定要删除所有已读通知吗？')) {
        try {
          const response = await notificationsApi.deleteReadNotifications()
          if (response.code === 200) {
            notifications.value = notifications.value.filter(n => !n.read)
            total.value = notifications.value.length
            successMessage.value = '已删除所有已读通知'
          }
        } catch (error) {
          console.error('删除已读通知失败:', error)
          errorMessage.value = '删除已读通知失败'
        }
      }
    }

    onMounted(() => {
      loadNotifications()
    })

    return {
      loading,
      errorMessage,
      successMessage,
      notifications,
      total,
      currentPage,
      limit,
      totalPages,
      filters,
      unreadCount,
      readCount,
      loadNotifications,
      getTypeIcon,
      handleViewNotification,
      handleMarkAsRead,
      handleMarkAllAsRead,
      handleDelete,
      handleDeleteRead,
      formatDate
    }
  }
}
</script>

<style scoped>
.notifications {
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

.filter-group select {
  padding: var(--spacing-sm) var(--spacing-md);
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius);
  font-size: 0.875rem;
  transition: border-color 0.3s;
}

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
  margin: 0 0 var(--spacing-md) 0;
  font-size: 1.5rem;
  color: var(--text-primary);
}

.empty-state p {
  margin: 0;
}

.notifications-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.notification-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  padding: var(--spacing-lg);
  background-color: var(--card-bg);
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius);
  cursor: pointer;
  transition: all 0.3s;
}

.notification-item:hover {
  border-color: var(--color-primary);
  box-shadow: var(--shadow-md);
}

.notification-item.unread {
  border-left: 4px solid var(--color-primary);
  background-color: var(--color-primary-bg);
}

.notification-type {
  flex-shrink: 0;
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background-color: var(--bg-secondary);
}

.type-high-vulnerability {
  background-color: var(--color-critical-bg);
}

.type-medium-vulnerability {
  background-color: var(--color-error-bg);
}

.type-low-vulnerability {
  background-color: var(--color-warning-bg);
}

.type-scan-completed {
  background-color: var(--color-success-bg);
}

.type-scan-failed {
  background-color: var(--color-error-bg);
}

.type-scan-started {
  background-color: var(--color-info-bg);
}

.type-system-update {
  background-color: var(--color-primary-bg);
}

.type-icon {
  font-size: 1.5rem;
}

.notification-content {
  flex: 1;
  min-width: 0;
}

.notification-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-sm);
}

.notification-title {
  font-size: 1rem;
  font-weight: 600;
  color: var(--text-primary);
}

.notification-time {
  font-size: 0.875rem;
  color: var(--text-secondary);
  white-space: nowrap;
}

.notification-message {
  color: var(--text-secondary);
  font-size: 0.875rem;
  line-height: 1.5;
}

.notification-actions {
  display: flex;
  gap: var(--spacing-xs);
  flex-shrink: 0;
}

.btn-icon {
  width: 32px;
  height: 32px;
  border: none;
  border-radius: var(--border-radius);
  background-color: var(--bg-secondary);
  color: var(--text-primary);
  cursor: pointer;
  transition: all 0.3s;
  display: flex;
  align-items: center;
  justify-content: center;
}

.btn-icon:hover {
  background-color: var(--color-primary-bg);
  color: var(--color-primary);
}

.btn-icon.btn-danger {
  background-color: var(--color-error-bg);
  color: var(--color-error);
}

.btn-icon.btn-danger:hover {
  background-color: var(--color-error);
  color: #ffffff;
}

.btn {
  padding: var(--spacing-sm) var(--spacing-md);
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

.btn-primary:hover:not(:disabled) {
  background-color: var(--color-primary-dark);
}

.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
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

.btn-danger:hover:not(:disabled) {
  background-color: var(--color-error-dark);
}

.btn-danger:disabled {
  opacity: 0.5;
  cursor: not-allowed;
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
  color: #1a1a1a;
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

@media (max-width: 768px) {
  .notifications {
    padding: var(--spacing-md);
  }

  .page-header {
    flex-direction: column;
    align-items: flex-start;
    gap: var(--spacing-md);
  }

  .filters-section {
    flex-direction: column;
    align-items: stretch;
  }

  .notification-item {
    flex-direction: column;
    align-items: flex-start;
    gap: var(--spacing-sm);
  }

  .notification-actions {
    width: 100%;
    justify-content: flex-start;
  }

  .header-actions {
    flex-direction: column;
    width: 100%;
  }

  .pagination {
    flex-direction: column;
    gap: var(--spacing-sm);
  }
}
</style>
