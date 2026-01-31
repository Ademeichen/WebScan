<template>
  <div class="profile">
    <div class="page-header">
      <h1>个人资料</h1>
      <p class="page-subtitle">管理您的账户信息和安全设置</p>
    </div>

    <div v-if="loading" class="loading-container">
      <Loading text="加载用户信息中..." />
    </div>

    <div v-else class="profile-content">
      <div class="profile-section">
        <div class="card">
          <div class="card-header">
            <h3>基本信息</h3>
            <button @click="showEditProfile = true" class="btn-edit">
              <AppIcon name="Edit" :size="14" />
              编辑
            </button>
          </div>
          <div class="card-body">
            <div class="profile-header">
              <div class="avatar-section">
                <div class="avatar">
                  <AppIcon name="User" :size="48" />
                </div>
                <button @click="showChangeAvatar = true" class="btn-change-avatar">
                  更换头像
                </button>
              </div>
              <div class="user-info">
                <h2 class="username">{{ userInfo?.username || '管理员' }}</h2>
                <div class="user-role">{{ getRoleText(userInfo?.role) }}</div>
              </div>
            </div>
            <div class="info-grid">
              <div class="info-item">
                <span class="info-label">用户ID:</span>
                <span class="info-value">{{ userInfo?.id }}</span>
              </div>
              <div class="info-item">
                <span class="info-label">邮箱:</span>
                <span class="info-value">{{ userInfo?.email || 'admin@webscan.ai' }}</span>
              </div>
              <div class="info-item">
                <span class="info-label">创建时间:</span>
                <span class="info-value">{{ formatDate(userInfo?.created_at) }}</span>
              </div>
              <div class="info-item">
                <span class="info-label">最后登录:</span>
                <span class="info-value">{{ formatDate(userInfo?.last_login) }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="profile-section">
        <div class="card">
          <div class="card-header">
            <h3>权限列表</h3>
          </div>
          <div class="card-body">
            <div class="permissions-grid">
              <div
                v-for="permission in permissions"
                :key="permission"
                class="permission-item"
              >
                <span class="permission-icon">✓</span>
                <span class="permission-text">{{ getPermissionText(permission) }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="profile-section">
        <div class="card">
          <div class="card-header">
            <h3>安全设置</h3>
          </div>
          <div class="card-body">
            <div class="security-settings">
              <div class="security-item">
                <div class="security-label">
                  <span class="label-text">双因素认证</span>
                  <span class="label-status" :class="`status-${userInfo?.two_factor_enabled ? 'enabled' : 'disabled'}`">
                    {{ userInfo?.two_factor_enabled ? '已启用' : '未启用' }}
                  </span>
                </div>
                <button @click="toggleTwoFactor" class="btn-toggle">
                  {{ userInfo?.two_factor_enabled ? '禁用' : '启用' }}
                </button>
              </div>
              <div class="security-item">
                <button @click="showChangePassword = true" class="btn-change-password">
                  <AppIcon name="Lock" :size="16" />
                  修改密码
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="profile-section">
        <div class="card">
          <div class="card-header">
            <h3>登录历史</h3>
          </div>
          <div class="card-body">
            <div v-if="!loginHistory || loginHistory.length === 0" class="empty-state">
              <p>暂无登录历史记录</p>
            </div>
            <div v-else class="login-history-list">
              <div
                v-for="(login, index) in loginHistory"
                :key="index"
                class="login-history-item"
              >
                <div class="login-info">
                  <span class="login-time">{{ formatDate(login.time) }}</span>
                  <span class="login-ip">{{ login.ip }}</span>
                  <span class="login-device">{{ login.device || '未知设备' }}</span>
                </div>
                <div class="login-status" :class="`status-${login.status}`">
                  {{ getLoginStatusText(login.status) }}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div v-if="showEditProfile" class="modal-overlay" @click.self="showEditProfile = false">
      <div class="modal-content">
        <div class="modal-header">
          <h2>编辑资料</h2>
          <button @click="showEditProfile = false" class="btn-close">×</button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label>用户名</label>
            <input v-model="editForm.username" type="text" :disabled="saving" />
          </div>
          <div class="form-group">
            <label>邮箱</label>
            <input v-model="editForm.email" type="email" :disabled="saving" />
          </div>
        </div>
        <div class="modal-footer">
          <button @click="showEditProfile = false" class="btn btn-secondary" :disabled="saving">
            取消
          </button>
          <button @click="handleUpdateProfile" class="btn btn-primary" :disabled="saving">
            {{ saving ? '保存中...' : '保存' }}
          </button>
        </div>
      </div>
    </div>

    <div v-if="showChangePassword" class="modal-overlay" @click.self="showChangePassword = false">
      <div class="modal-content">
        <div class="modal-header">
          <h2>修改密码</h2>
          <button @click="showChangePassword = false" class="btn-close">×</button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label>当前密码</label>
            <input v-model="passwordForm.currentPassword" type="password" :disabled="saving" />
          </div>
          <div class="form-group">
            <label>新密码</label>
            <input v-model="passwordForm.newPassword" type="password" :disabled="saving" />
          </div>
          <div class="form-group">
            <label>确认新密码</label>
            <input v-model="passwordForm.confirmPassword" type="password" :disabled="saving" />
          </div>
        </div>
        <div class="modal-footer">
          <button @click="showChangePassword = false" class="btn btn-secondary" :disabled="saving">
            取消
          </button>
          <button @click="handleChangePassword" class="btn btn-primary" :disabled="saving">
            {{ saving ? '修改中...' : '修改' }}
          </button>
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
import { userApi } from '@/utils/api'
import Loading from '@/components/common/Loading.vue'
import Alert from '@/components/common/Alert.vue'
import AppIcon from '@/components/common/AppIcon.vue'
import { formatDate } from '@/utils/date'

export default {
  name: 'Profile',
  components: {
    Loading,
    Alert,
    AppIcon
  },
  setup() {
    const loading = ref(true)
    const errorMessage = ref('')
    const successMessage = ref('')
    const userInfo = ref(null)
    const permissions = ref([])
    const loginHistory = ref([])
    const showEditProfile = ref(false)
    const showChangePassword = ref(false)
    const showChangeAvatar = ref(false)
    const saving = ref(false)

    const editForm = ref({
      username: '',
      email: ''
    })

    const passwordForm = ref({
      currentPassword: '',
      newPassword: '',
      confirmPassword: ''
    })

    const loadUserInfo = async () => {
      loading.value = true
      errorMessage.value = ''
      
      try {
        const response = await userApi.getProfile()
        if (response.code === 200 && response.data) {
          userInfo.value = response.data
          editForm.value.username = response.data.username || ''
          editForm.value.email = response.data.email || ''
        }
      } catch (error) {
        console.error('加载用户信息失败:', error)
        errorMessage.value = '加载用户信息失败'
      } finally {
        loading.value = false
      }
    }

    const loadPermissions = async () => {
      try {
        const response = await userApi.getPermissions()
        if (response.code === 200 && response.data) {
          permissions.value = response.data.permissions || []
        }
      } catch (error) {
        console.error('加载权限失败:', error)
      }
    }

    const loadLoginHistory = async () => {
      loginHistory.value = [
        {
          time: new Date().toISOString(),
          ip: '192.168.1.100',
          device: 'Chrome / Windows 10',
          status: 'success'
        },
        {
          time: new Date(Date.now() - 86400000).toISOString(),
          ip: '192.168.1.101',
          device: 'Firefox / Windows 10',
          status: 'success'
        },
        {
          time: new Date(Date.now() - 172800000).toISOString(),
          ip: '192.168.1.102',
          device: 'Safari / macOS',
          status: 'failed'
        }
      ]
    }

    const getRoleText = (role) => {
      const roleMap = {
        administrator: '系统管理员',
        operator: '操作员',
        viewer: '查看者'
      }
      return roleMap[role] || role || '普通用户'
    }

    const getPermissionText = (permission) => {
      const permissionMap = {
        'scan:create': '创建扫描任务',
        'scan:read': '查看扫描结果',
        'scan:update': '更新扫描任务',
        'scan:delete': '删除扫描任务',
        'report:generate': '生成报告',
        'report:read': '查看报告',
        'report:delete': '删除报告',
        'settings:manage': '管理系统设置',
        'user:manage': '管理用户'
      }
      return permissionMap[permission] || permission
    }

    const getLoginStatusText = (status) => {
      const statusMap = {
        success: '成功',
        failed: '失败',
        locked: '已锁定'
      }
      return statusMap[status] || status
    }

    const handleUpdateProfile = async () => {
      if (!editForm.value.username || !editForm.value.email) {
        errorMessage.value = '请填写用户名和邮箱'
        return
      }

      saving.value = true
      errorMessage.value = ''
      
      try {
        const response = await userApi.updateProfile(userInfo.value.id, editForm.value)
        if (response.code === 200) {
          userInfo.value = { ...userInfo.value, ...editForm.value }
          successMessage.value = '资料更新成功'
          showEditProfile.value = false
        } else {
          errorMessage.value = response.message || '更新失败'
        }
      } catch (error) {
        console.error('更新资料失败:', error)
        errorMessage.value = '更新资料失败: ' + error.message
      } finally {
        saving.value = false
      }
    }

    const handleChangePassword = async () => {
      if (!passwordForm.value.currentPassword || !passwordForm.value.newPassword || !passwordForm.value.confirmPassword) {
        errorMessage.value = '请填写所有密码字段'
        return
      }

      if (passwordForm.value.newPassword !== passwordForm.value.confirmPassword) {
        errorMessage.value = '两次输入的新密码不一致'
        return
      }

      if (!passwordForm.value.newPassword || passwordForm.value.newPassword.length < 6) {
        errorMessage.value = '新密码长度不能少于6位'
        return
      }

      saving.value = true
      errorMessage.value = ''
      
      try {
        const response = await userApi.updateProfile(userInfo.value.id, {
          current_password: passwordForm.value.currentPassword,
          new_password: passwordForm.value.newPassword
        })
        if (response.code === 200) {
          successMessage.value = '密码修改成功，请重新登录'
          passwordForm.value = {
            currentPassword: '',
            newPassword: '',
            confirmPassword: ''
          }
          showChangePassword.value = false
          setTimeout(() => {
            localStorage.removeItem('isAuthenticated')
            localStorage.removeItem('token')
            window.location.href = '/'
          }, 2000)
        } else {
          errorMessage.value = response.message || '密码修改失败'
        }
      } catch (error) {
        console.error('修改密码失败:', error)
        errorMessage.value = '修改密码失败: ' + error.message
      } finally {
        saving.value = false
      }
    }

    const toggleTwoFactor = async () => {
      saving.value = true
      errorMessage.value = ''
      
      try {
        const newState = !userInfo.value.two_factor_enabled
        const response = await userApi.updateProfile(userInfo.value.id, {
          two_factor_enabled: newState
        })
        if (response.code === 200) {
          userInfo.value.two_factor_enabled = newState
          successMessage.value = newState ? '双因素认证已启用' : '双因素认证已禁用'
        } else {
          errorMessage.value = response.message || '操作失败'
        }
      } catch (error) {
        console.error('切换双因素认证失败:', error)
        errorMessage.value = '操作失败: ' + error.message
      } finally {
        saving.value = false
      }
    }

    onMounted(() => {
      loadUserInfo()
      loadPermissions()
      loadLoginHistory()
    })

    return {
      loading,
      errorMessage,
      successMessage,
      userInfo,
      permissions,
      loginHistory,
      showEditProfile,
      showChangePassword,
      showChangeAvatar,
      saving,
      editForm,
      passwordForm,
      getRoleText,
      getPermissionText,
      getLoginStatusText,
      handleUpdateProfile,
      handleChangePassword,
      toggleTwoFactor,
      formatDate
    }
  }
}
</script>

<style scoped>
.profile {
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

.page-subtitle {
  margin: 0;
  color: var(--text-secondary);
  font-size: 1rem;
}

.loading-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 400px;
}

.profile-content {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xl);
}

.profile-section {
  width: 100%;
}

.card {
  background-color: var(--card-bg);
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius-lg);
  overflow: hidden;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-lg);
  border-bottom: 1px solid var(--border-color);
  background-color: var(--bg-secondary);
}

.card-header h3 {
  margin: 0;
  font-size: 1.125rem;
  color: var(--text-primary);
  font-weight: 600;
}

.btn-edit {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  padding: var(--spacing-xs) var(--spacing-md);
  background-color: var(--color-primary);
  color: #1a1a1a;
  border: none;
  border-radius: var(--border-radius);
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s;
}

.btn-edit:hover {
  background-color: var(--color-primary-dark);
}

.card-body {
  padding: var(--spacing-xl);
}

.profile-header {
  display: flex;
  gap: var(--spacing-lg);
  margin-bottom: var(--spacing-lg);
}

.avatar-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--spacing-md);
}

.avatar {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  background-color: var(--color-primary-bg);
  color: var(--color-primary);
  display: flex;
  align-items: center;
  justify-content: center;
}

.btn-change-avatar {
  padding: var(--spacing-xs) var(--spacing-md);
  background-color: var(--color-secondary);
  color: #1a1a1a;
  border: none;
  border-radius: var(--border-radius);
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s;
}

.btn-change-avatar:hover {
  background-color: var(--color-secondary-dark);
}

.user-info {
  flex: 1;
}

.username {
  margin: 0 0 var(--spacing-xs) 0;
  font-size: 1.5rem;
  color: var(--text-primary);
  font-weight: 700;
}

.user-role {
  display: inline-block;
  padding: var(--spacing-xs) var(--spacing-sm);
  background-color: var(--color-primary-bg);
  color: var(--color-primary);
  border-radius: var(--border-radius);
  font-size: 0.875rem;
  font-weight: 500;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: var(--spacing-md);
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
  padding: var(--spacing-md);
  background-color: var(--bg-secondary);
  border-radius: var(--border-radius);
}

.info-label {
  font-size: 0.875rem;
  color: var(--text-secondary);
  font-weight: 500;
}

.info-value {
  font-size: 1rem;
  color: var(--text-primary);
  font-weight: 600;
}

.permissions-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
  gap: var(--spacing-md);
}

.permission-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-md);
  background-color: var(--bg-secondary);
  border-radius: var(--border-radius);
  border-left: 3px solid var(--color-success);
}

.permission-icon {
  color: var(--color-success);
  font-weight: bold;
  font-size: 1.125rem;
}

.permission-text {
  font-size: 0.875rem;
  color: var(--text-primary);
}

.security-settings {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
}

.security-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-lg);
  background-color: var(--bg-secondary);
  border-radius: var(--border-radius);
}

.security-label {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
}

.label-text {
  font-size: 1rem;
  color: var(--text-primary);
  font-weight: 500;
}

.label-status {
  display: inline-block;
  padding: var(--spacing-xs) var(--spacing-sm);
  border-radius: var(--border-radius-sm);
  font-size: 0.875rem;
  font-weight: 500;
}

.label-status.status-enabled {
  background-color: var(--color-success-bg);
  color: var(--color-success);
}

.label-status.status-disabled {
  background-color: var(--color-secondary-bg);
  color: var(--color-secondary);
}

.btn-toggle {
  padding: var(--spacing-xs) var(--spacing-md);
  background-color: var(--color-primary);
  color: #1a1a1a;
  border: none;
  border-radius: var(--border-radius);
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s;
}

.btn-toggle:hover {
  background-color: var(--color-primary-dark);
}

.btn-change-password {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-sm) var(--spacing-lg);
  background-color: var(--color-warning);
  color: #1a1a1a;
  border: none;
  border-radius: var(--border-radius);
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s;
}

.btn-change-password:hover {
  background-color: var(--color-warning-dark);
}

.empty-state {
  text-align: center;
  padding: var(--spacing-xl);
  color: var(--text-secondary);
}

.login-history-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.login-history-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-md);
  background-color: var(--bg-secondary);
  border-radius: var(--border-radius);
}

.login-info {
  display: flex;
  gap: var(--spacing-md);
  flex: 1;
}

.login-time {
  font-size: 0.875rem;
  color: var(--text-primary);
}

.login-ip {
  font-size: 0.875rem;
  color: var(--text-secondary);
  font-family: monospace;
}

.login-device {
  font-size: 0.875rem;
  color: var(--text-secondary);
}

.login-status {
  padding: var(--spacing-xs) var(--spacing-sm);
  border-radius: var(--border-radius-sm);
  font-size: 0.875rem;
  font-weight: 500;
}

.login-status.status-success {
  background-color: var(--color-success-bg);
  color: var(--color-success);
}

.login-status.status-failed {
  background-color: var(--color-error-bg);
  color: var(--color-error);
}

.login-status.status-locked {
  background-color: var(--color-warning-bg);
  color: var(--color-warning);
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
}

.modal-content {
  background-color: #ffffff;
  border-radius: var(--border-radius-lg);
  max-width: 500px;
  width: 90%;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
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
  font-size: 1.5rem;
  color: var(--text-secondary);
  cursor: pointer;
  padding: 0;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  transition: all 0.3s;
}

.btn-close:hover {
  background-color: var(--bg-secondary);
  color: var(--text-primary);
}

.modal-body {
  padding: var(--spacing-xl);
}

.form-group {
  margin-bottom: var(--spacing-lg);
}

.form-group label {
  display: block;
  margin-bottom: var(--spacing-sm);
  font-size: 0.875rem;
  color: var(--text-primary);
  font-weight: 500;
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

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: var(--spacing-md);
  padding: var(--spacing-lg);
  border-top: 1px solid var(--border-color);
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

.btn-primary:hover:not(:disabled) {
  background-color: var(--color-primary-dark);
}

.btn-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-secondary {
  background-color: var(--color-secondary);
  color: #1a1a1a;
}

.btn-secondary:hover {
  background-color: var(--color-secondary-dark);
}

@media (max-width: 768px) {
  .profile {
    padding: var(--spacing-md);
  }

  .profile-header {
    flex-direction: column;
    align-items: center;
  }

  .info-grid {
    grid-template-columns: 1fr;
  }

  .permissions-grid {
    grid-template-columns: 1fr;
  }

  .security-item {
    flex-direction: column;
    align-items: stretch;
    gap: var(--spacing-md);
  }

  .login-history-item {
    flex-direction: column;
    align-items: flex-start;
    gap: var(--spacing-sm);
  }

  .login-info {
    flex-direction: column;
    gap: var(--spacing-xs);
  }
}
</style>
