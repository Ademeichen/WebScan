<template>
  <div class="app-layout">
    <!-- 顶部导航栏 -->
    <header class="header">
      <div class="header-content">
        <div class="logo-section">
          <!-- 移动端菜单按钮 -->
          <button class="mobile-menu-btn d-md-none" @click="toggleMobileMenu">
            <span class="menu-icon">☰</span>
          </button>
          <div class="logo">
            <span class="logo-icon">🛡️</span>
            <span class="logo-text">WebScan AI</span>
          </div>
        </div>
        <div class="header-actions">
          <button class="notification-btn" @click="showNotifications = !showNotifications">
            <span class="notification-icon">🔔</span>
            <span v-if="notificationCount > 0" class="notification-badge">{{ notificationCount }}</span>
          </button>
          <div class="user-menu">
            <div class="user-avatar" @click="showUserMenu = !showUserMenu">
              <span>👤</span>
            </div>
            <div v-if="showUserMenu" class="user-dropdown">
              <div class="user-info">
                <div class="user-name">{{ userInfo?.username || '管理员' }}</div>
                <div class="user-email">{{ userInfo?.email || 'admin@webscan.ai' }}</div>
              </div>
              <hr>
              <a href="#" class="dropdown-item">个人设置</a>
              <a href="#" class="dropdown-item">退出登录</a>
            </div>
          </div>
        </div>
      </div>
    </header>

    <div class="main-container">
      <!-- 侧边栏导航 -->
      <aside class="sidebar" :class="{ 'sidebar-collapsed': sidebarCollapsed, 'sidebar-mobile': isMobileMenuOpen }">
        <div class="sidebar-toggle d-md-flex d-sm-none" @click="toggleSidebar">
          <span>{{ sidebarCollapsed ? '→' : '←' }}</span>
        </div>
        <nav class="sidebar-nav">
          <router-link 
            v-for="item in menuItems" 
            :key="item.name"
            :to="item.path" 
            class="nav-item"
            :class="{ 'active': $route.name === item.name }"
            @click="closeMobileMenu"
          >
            <span class="nav-icon">{{ item.icon }}</span>
            <span v-if="!sidebarCollapsed" class="nav-text">{{ item.label }}</span>
          </router-link>
        </nav>
      </aside>

      <!-- 移动端遮罩层 -->
      <div v-if="isMobileMenuOpen" class="sidebar-overlay" @click="closeMobileMenu"></div>

      <!-- 主内容区域 -->
      <main class="main-content">
        <router-view />
      </main>
    </div>

    <!-- 通知面板 -->
    <div v-if="showNotifications" class="notification-panel">
      <div class="notification-header">
        <h3>通知</h3>
        <button @click="showNotifications = false" class="close-btn">×</button>
      </div>
      <div class="notification-list">
        <div v-for="notification in notifications" :key="notification.id" class="notification-item">
          <div class="notification-content">
            <div class="notification-title">{{ notification.title }}</div>
            <div class="notification-message">{{ notification.message }}</div>
            <div class="notification-time">{{ notification.time }}</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, onUnmounted } from 'vue'
import { userApi, notificationsApi } from '@/utils/api'

export default {
  name: 'AppLayout',
  data() {
    return {
      sidebarCollapsed: false,
      showNotifications: false,
      showUserMenu: false,
      isMobileMenuOpen: false,
      isMobile: false,
      
      menuItems: [
        { name: 'Dashboard', path: '/', label: '仪表盘', icon: '📊' },
        { name: 'ScanTasks', path: '/scan-tasks', label: '扫描任务', icon: '🔍' },
        { name: 'POCScan', path: '/poc-scan', label: 'POC扫描', icon: '🎯' },
        { name: 'AWVSScan', path: '/awvs-scan', label: 'AWVS扫描', icon: '🛡️' },
        { name: 'AgentScan', path: '/agent-scan', label: 'AI Agent', icon: '🤖' },
        { name: 'Reports', path: '/reports', label: '报告', icon: '📋' },
        { name: 'Settings', path: '/settings', label: '设置', icon: '⚙️' }
      ],
      
      notifications: [],
      userInfo: null
    }
  },
  computed: {
    notificationCount() {
      return this.notifications.filter(n => !n.read).length
    }
  },
  methods: {
    toggleSidebar() {
      this.sidebarCollapsed = !this.sidebarCollapsed
    },
    toggleMobileMenu() {
      this.isMobileMenuOpen = !this.isMobileMenuOpen
    },
    closeMobileMenu() {
      this.isMobileMenuOpen = false
    },
    checkMobile() {
      this.isMobile = window.innerWidth <= 768
      if (this.isMobile) {
        this.sidebarCollapsed = false
      }
    },
    async loadUserInfo() {
      try {
        const response = await userApi.getProfile()
        if (response.code === 200) {
          this.userInfo = response.data
        }
      } catch (error) {
        console.error('加载用户信息失败:', error)
      }
    },
    async loadNotifications() {
      try {
        const response = await notificationsApi.getNotifications({ limit: 10 })
        if (response.code === 200) {
          this.notifications = response.data.notifications || []
        }
      } catch (error) {
        console.error('加载通知失败:', error)
      }
    }
  },
  mounted() {
    this.loadUserInfo()
    this.loadNotifications()
    
    this.checkMobile()
    
    window.addEventListener('resize', this.checkMobile)
    
    document.addEventListener('click', (e) => {
      if (!e.target.closest('.user-menu')) {
        this.showUserMenu = false
      }
      if (!e.target.closest('.notification-panel') && !e.target.closest('.notification-btn')) {
        this.showNotifications = false
      }
    })
  },
  beforeUnmount() {
    window.removeEventListener('resize', this.checkMobile)
  }
}
</script>

<style scoped>
.app-layout {
  display: flex;
  flex-direction: column;
  height: 100vh;
}

/* 顶部导航栏 */
.header {
  background-color: var(--card-background);
  border-bottom: 1px solid var(--border-color);
  box-shadow: var(--shadow-sm);
  z-index: 1000;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 var(--spacing-md);
  height: 60px;
}

.logo-section {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
}

/* 移动端菜单按钮 */
.mobile-menu-btn {
  display: none;
  background: none;
  border: none;
  cursor: pointer;
  padding: var(--spacing-sm);
  border-radius: var(--border-radius);
  transition: background-color 0.2s ease;
}

.mobile-menu-btn:hover {
  background-color: var(--background-color);
}

.menu-icon {
  font-size: 20px;
}

.logo {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
}

.logo-icon {
  font-size: 24px;
}

.logo-text {
  font-size: 20px;
  font-weight: bold;
  color: var(--primary-color);
}

.header-actions {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
}

.notification-btn {
  position: relative;
  background: none;
  border: none;
  cursor: pointer;
  padding: var(--spacing-sm);
  border-radius: var(--border-radius);
  transition: background-color 0.2s ease;
}

.notification-btn:hover {
  background-color: var(--background-color);
}

.notification-icon {
  font-size: 20px;
}

.notification-badge {
  position: absolute;
  top: 0;
  right: 0;
  background-color: var(--high-risk);
  color: white;
  font-size: 10px;
  padding: 2px 6px;
  border-radius: 10px;
  min-width: 16px;
  text-align: center;
}

.user-menu {
  position: relative;
}

.user-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background-color: var(--secondary-color);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: white;
  font-size: 16px;
}

.user-dropdown {
  position: absolute;
  top: 100%;
  right: 0;
  background-color: var(--card-background);
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius);
  box-shadow: var(--shadow-md);
  min-width: 200px;
  z-index: 1001;
  margin-top: var(--spacing-xs);
}

.user-info {
  padding: var(--spacing-md);
}

.user-name {
  font-weight: bold;
  color: var(--text-primary);
}

.user-email {
  font-size: 12px;
  color: var(--text-secondary);
}

.dropdown-item {
  display: block;
  padding: var(--spacing-sm) var(--spacing-md);
  color: var(--text-primary);
  text-decoration: none;
  transition: background-color 0.2s ease;
}

.dropdown-item:hover {
  background-color: var(--background-color);
}

/* 主容器 */
.main-container {
  display: flex;
  flex: 1;
  overflow: hidden;
  position: relative;
}

/* 侧边栏 */
.sidebar {
  width: 240px;
  background-color: var(--card-background);
  border-right: 1px solid var(--border-color);
  transition: width 0.3s ease, transform 0.3s ease;
  position: relative;
  z-index: 100;
}

.sidebar-collapsed {
  width: 60px;
}

.sidebar-toggle {
  position: absolute;
  top: var(--spacing-md);
  right: -12px;
  width: 24px;
  height: 24px;
  background-color: var(--card-background);
  border: 1px solid var(--border-color);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  font-size: 12px;
  z-index: 10;
}

.sidebar-nav {
  padding: var(--spacing-md) 0;
}

.nav-item {
  display: flex;
  align-items: center;
  padding: var(--spacing-md);
  color: var(--text-primary);
  text-decoration: none;
  transition: all 0.2s ease;
  gap: var(--spacing-md);
}

.nav-item:hover {
  background-color: var(--background-color);
}

.nav-item.active {
  background-color: rgba(26, 58, 108, 0.1);
  color: var(--primary-color);
  border-right: 3px solid var(--primary-color);
}

.nav-icon {
  font-size: 18px;
  min-width: 18px;
}

.nav-text {
  font-weight: 500;
}

/* 移动端遮罩层 */
.sidebar-overlay {
  position: fixed;
  top: 60px;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  z-index: 99;
}

/* 主内容区域 */
.main-content {
  flex: 1;
  padding: var(--spacing-lg);
  overflow-y: auto;
  background-color: var(--background-color);
}

/* 通知面板 */
.notification-panel {
  position: fixed;
  top: 60px;
  right: var(--spacing-md);
  width: 320px;
  background-color: var(--card-background);
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius);
  box-shadow: var(--shadow-lg);
  z-index: 1001;
  max-height: 400px;
  overflow-y: auto;
}

.notification-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-md);
  border-bottom: 1px solid var(--border-color);
}

.notification-header h3 {
  margin: 0;
  font-size: 16px;
  color: var(--text-primary);
}

.close-btn {
  background: none;
  border: none;
  font-size: 20px;
  cursor: pointer;
  color: var(--text-secondary);
}

.notification-list {
  max-height: 300px;
  overflow-y: auto;
}

.notification-item {
  padding: var(--spacing-md);
  border-bottom: 1px solid var(--border-color);
}

.notification-item:last-child {
  border-bottom: none;
}

.notification-title {
  font-weight: bold;
  color: var(--text-primary);
  margin-bottom: var(--spacing-xs);
}

.notification-message {
  color: var(--text-secondary);
  font-size: 13px;
  margin-bottom: var(--spacing-xs);
}

.notification-time {
  color: var(--text-secondary);
  font-size: 11px;
}

/* 响应式设计 - 平板设备 */
@media (max-width: 1024px) {
  .sidebar {
    width: 200px;
  }
  
  .sidebar-collapsed {
    width: 60px;
  }
}

/* 响应式设计 - 手机设备 */
@media (max-width: 768px) {
  .mobile-menu-btn {
    display: flex;
  }
  
  .logo-text {
    font-size: 16px;
  }
  
  .sidebar {
    position: fixed;
    left: -240px;
    top: 60px;
    height: calc(100vh - 60px);
    width: 240px;
    z-index: 100;
    transition: left 0.3s ease;
  }
  
  .sidebar.sidebar-mobile {
    left: 0;
  }
  
  .sidebar-toggle {
    display: none;
  }
  
  .main-content {
    padding: var(--spacing-md);
  }
  
  .notification-panel {
    width: calc(100vw - 32px);
    right: var(--spacing-md);
    left: var(--spacing-md);
  }
  
  .user-avatar {
    width: 32px;
    height: 32px;
  }
}

/* 响应式设计 - 小屏手机 */
@media (max-width: 480px) {
  .header-content {
    padding: 0 var(--spacing-sm);
    height: 50px;
  }
  
  .logo-icon {
    font-size: 20px;
  }
  
  .logo-text {
    font-size: 14px;
  }
  
  .notification-icon {
    font-size: 18px;
  }
  
  .sidebar {
    top: 50px;
    height: calc(100vh - 50px);
  }
  
  .sidebar-overlay {
    top: 50px;
  }
  
  .notification-panel {
    top: 50px;
  }
  
  .main-content {
    padding: var(--spacing-sm);
  }
}

/* 响应式设计 - 超小屏设备 */
@media (max-width: 360px) {
  .logo-text {
    display: none;
  }
  
  .notification-badge {
    min-width: 14px;
    font-size: 9px;
    padding: 1px 4px;
  }
}
</style>


