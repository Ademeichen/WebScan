<template>
  <div class="settings">
    <div class="page-header">
      <h1>系统设置</h1>
      <p class="page-subtitle">配置系统参数和用户偏好</p>
    </div>

    <div class="settings-container">
      <!-- 设置导航 -->
      <div class="settings-nav">
        <div class="nav-item" 
             :class="{ active: activeTab === 'general' }"
             @click="activeTab = 'general'">
          <span class="nav-icon">⚙️</span>
          <span class="nav-text">常规设置</span>
        </div>
        <div class="nav-item" 
             :class="{ active: activeTab === 'scan' }"
             @click="activeTab = 'scan'">
          <span class="nav-icon">🔍</span>
          <span class="nav-text">扫描配置</span>
        </div>
        <div class="nav-item" 
             :class="{ active: activeTab === 'notification' }"
             @click="activeTab = 'notification'">
          <span class="nav-icon">🔔</span>
          <span class="nav-text">通知设置</span>
        </div>
        <div class="nav-item" 
             :class="{ active: activeTab === 'security' }"
             @click="activeTab = 'security'">
          <span class="nav-icon">🔐</span>
          <span class="nav-text">安全设置</span>
        </div>
      </div>

      <!-- 设置内容 -->
      <div class="settings-content">
        <!-- 加载状态 -->
        <div v-if="loading" class="loading-state">
          <div class="loading-spinner"></div>
          <div class="loading-text">加载设置中...</div>
        </div>
        
        <!-- 常规设置 -->
        <div v-if="!loading && activeTab === 'general'" class="settings-panel">
          <div class="card">
            <div class="card-header">
              <h3 class="card-title">系统配置</h3>
            </div>
            <div class="settings-form">
              <div class="form-group">
                <label class="form-label">系统名称</label>
                <input v-model="settings.general.systemName" type="text" class="form-input" :disabled="saving">
              </div>
              
              <div class="form-group">
                <label class="form-label">默认语言</label>
                <select v-model="settings.general.language" class="form-select" :disabled="saving">
                  <option value="zh-CN">简体中文</option>
                  <option value="en-US">English</option>
                </select>
              </div>
              
              <div class="form-group">
                <label class="form-label">时区设置</label>
                <select v-model="settings.general.timezone" class="form-select" :disabled="saving">
                  <option value="Asia/Shanghai">Asia/Shanghai (UTC+8)</option>
                  <option value="UTC">UTC (UTC+0)</option>
                  <option value="America/New_York">America/New_York (UTC-5)</option>
                </select>
              </div>
              
              <div class="form-group">
                <label class="checkbox-label">
                  <input v-model="settings.general.autoUpdate" type="checkbox" class="checkbox-input" :disabled="saving">
                  <span class="checkbox-custom"></span>
                  自动更新漏洞库
                </label>
              </div>
            </div>
          </div>
        </div>

        <!-- 扫描配置 -->
        <div v-if="!loading && activeTab === 'scan'" class="settings-panel">
          <div class="card">
            <div class="card-header">
              <h3 class="card-title">默认扫描参数</h3>
            </div>
            <div class="settings-form">
              <div class="form-group">
                <label class="form-label">默认扫描深度</label>
                <select v-model="settings.scan.defaultDepth" class="form-select" :disabled="saving">
                  <option value="1">浅层扫描 (深度1)</option>
                  <option value="2">中等扫描 (深度2)</option>
                  <option value="3">深度扫描 (深度3)</option>
                </select>
              </div>
              
              <div class="form-group">
                <label class="form-label">默认并发数</label>
                <input v-model="settings.scan.defaultConcurrency" type="number" min="1" max="20" class="form-input" :disabled="saving">
              </div>
              
              <div class="form-group">
                <label class="form-label">请求超时时间 (秒)</label>
                <input v-model="settings.scan.requestTimeout" type="number" min="5" max="300" class="form-input" :disabled="saving">
              </div>
              
              <div class="form-group">
                <label class="form-label">用户代理字符串</label>
                <input v-model="settings.scan.userAgent" type="text" class="form-input" :disabled="saving">
              </div>
              
              <div class="form-group">
                <label class="checkbox-label">
                  <input v-model="settings.scan.followRedirects" type="checkbox" class="checkbox-input" :disabled="saving">
                  <span class="checkbox-custom"></span>
                  跟随重定向
                </label>
              </div>
              
              <div class="form-group">
                <label class="checkbox-label">
                  <input v-model="settings.scan.enableCookies" type="checkbox" class="checkbox-input" :disabled="saving">
                  <span class="checkbox-custom"></span>
                  启用Cookie支持
                </label>
              </div>
            </div>
          </div>
          
          <div class="card">
            <div class="card-header">
              <h3 class="card-title">扫描规则</h3>
            </div>
            <div class="rules-list">
              <div v-for="rule in scanRules" :key="rule.id" class="rule-item">
                <div class="rule-info">
                  <div class="rule-name">{{ rule.name }}</div>
                  <div class="rule-description">{{ rule.description }}</div>
                </div>
                <div class="rule-toggle">
                  <label class="switch">
                    <input v-model="rule.enabled" type="checkbox" :disabled="saving">
                    <span class="slider"></span>
                  </label>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 通知设置 -->
        <div v-if="!loading && activeTab === 'notification'" class="settings-panel">
          <div class="card">
            <div class="card-header">
              <h3 class="card-title">通知配置</h3>
            </div>
            <div class="settings-form">
              <div class="form-group">
                <label class="checkbox-label">
                  <input v-model="settings.notification.emailEnabled" type="checkbox" class="checkbox-input" :disabled="saving">
                  <span class="checkbox-custom"></span>
                  启用邮件通知
                </label>
              </div>
              
              <div v-if="settings.notification.emailEnabled" class="email-settings">
                <div class="form-group">
                  <label class="form-label">SMTP服务器</label>
                  <input v-model="settings.notification.smtpServer" type="text" class="form-input" :disabled="saving">
                </div>
                
                <div class="form-group">
                  <label class="form-label">SMTP端口</label>
                  <input v-model="settings.notification.smtpPort" type="number" class="form-input" :disabled="saving">
                </div>
                
                <div class="form-group">
                  <label class="form-label">发件人邮箱</label>
                  <input v-model="settings.notification.senderEmail" type="email" class="form-input" :disabled="saving">
                </div>
                
                <div class="form-group">
                  <label class="form-label">收件人邮箱</label>
                  <textarea v-model="settings.notification.recipientEmails" class="form-input" rows="3" 
                           placeholder="每行一个邮箱地址" :disabled="saving"></textarea>
                </div>
              </div>
              
              <div class="notification-events">
                <h4>通知事件</h4>
                <div class="event-list">
                  <label v-for="event in notificationEvents" :key="event.value" class="checkbox-label">
                    <input v-model="settings.notification.events" type="checkbox" :value="event.value" class="checkbox-input" :disabled="saving">
                    <span class="checkbox-custom"></span>
                    {{ event.label }}
                  </label>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 安全设置 -->
        <div v-if="!loading && activeTab === 'security'" class="settings-panel">
          <div class="card">
            <div class="card-header">
              <h3 class="card-title">访问控制</h3>
            </div>
            <div class="settings-form">
              <div class="form-group">
                <label class="form-label">会话超时时间 (分钟)</label>
                <input v-model="settings.security.sessionTimeout" type="number" min="5" max="1440" class="form-input" :disabled="saving">
              </div>
              
              <div class="form-group">
                <label class="checkbox-label">
                  <input v-model="settings.security.requireHttps" type="checkbox" class="checkbox-input" :disabled="saving">
                  <span class="checkbox-custom"></span>
                  强制使用HTTPS
                </label>
              </div>
              
              <div class="form-group">
                <label class="checkbox-label">
                  <input v-model="settings.security.enableTwoFactor" type="checkbox" class="checkbox-input" :disabled="saving">
                  <span class="checkbox-custom"></span>
                  启用双因素认证
                </label>
              </div>
              
              <div class="form-group">
                <label class="form-label">允许的IP地址</label>
                <textarea v-model="settings.security.allowedIPs" class="form-input" rows="3" 
                         placeholder="每行一个IP地址或CIDR块，留空表示允许所有IP" :disabled="saving"></textarea>
              </div>
            </div>
          </div>
          
          <div class="card">
            <div class="card-header">
              <h3 class="card-title">API密钥管理</h3>
            </div>
            <div class="api-keys">
              <div v-for="key in apiKeys" :key="key.id" class="api-key-item">
                <div class="key-info">
                  <div class="key-name">{{ key.name }}</div>
                  <div class="key-value">{{ key.masked }}</div>
                  <div class="key-created">创建时间: {{ key.createdAt }}</div>
                </div>
                <div class="key-actions">
                  <button @click="regenerateKey(key.id)" class="btn btn-outline" :disabled="saving">重新生成</button>
                  <button @click="deleteKey(key.id)" class="btn btn-outline btn-danger" :disabled="saving">删除</button>
                </div>
              </div>
              
              <button @click="createApiKey" class="btn btn-secondary" :disabled="saving">
                ➕ 创建新密钥
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 保存按钮 -->
    <div class="settings-footer">
      <div class="footer-actions">
        <button @click="resetSettings" class="btn btn-outline" :disabled="loading || saving">
          重置为默认
        </button>
        <button @click="saveSettings" class="btn btn-success" :disabled="loading || saving">
          <span v-if="saving">⏳ 保存中...</span>
          <span v-else>💾 保存设置</span>
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import { settingsApi } from '../utils/api.js'
import { formatDate } from '../utils/date.js'

export default {
  name: 'Settings',
  data() {
    return {
      activeTab: 'general',
      loading: false,
      saving: false,
      
      settings: {
        general: {
          systemName: 'WebScan AI',
          language: 'zh-CN',
          timezone: 'Asia/Shanghai',
          autoUpdate: true,
          theme: 'dark'
        },
        scan: {
          defaultDepth: 2,
          defaultConcurrency: 5,
          requestTimeout: 30,
          maxRetries: 3,
          enableProxy: false,
          followRedirects: true,
          enableCookies: true,
          userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        },
        notification: {
          emailEnabled: false,
          smtpServer: '',
          smtpPort: 587,
          smtpUser: '',
          senderEmail: '',
          recipientEmails: '',
          events: ['high-vulnerability', 'scan-completed']
        },
        security: {
          sessionTimeout: 120,
          requireHttps: true,
          enableTwoFactor: false,
          allowedIPs: ''
        }
      },
      
      scanRules: [
        { id: 1, name: 'SQL注入检测', description: '检测SQL注入漏洞', enabled: true },
        { id: 2, name: 'XSS跨站脚本', description: '检测跨站脚本攻击', enabled: true },
        { id: 3, name: 'CSRF跨站请求伪造', description: '检测跨站请求伪造漏洞', enabled: true },
        { id: 4, name: '文件包含漏洞', description: '检测文件包含漏洞', enabled: true },
        { id: 5, name: '命令注入', description: '检测命令注入漏洞', enabled: true },
        { id: 6, name: 'SSRF服务端请求伪造', description: '检测服务端请求伪造', enabled: true }
      ],
      
      notificationEvents: [
        { value: 'high-vulnerability', label: '发现高危漏洞' },
        { value: 'scan-complete', label: '扫描任务完成' },
        { value: 'scan-failed', label: '扫描任务失败' },
        { value: 'system-update', label: '系统更新' }
      ],
      
      apiKeys: []
    }
  },
  mounted() {
    this.fetchSettings()
  },
  methods: {
    formatDate,
    async fetchSettings() {
      this.loading = true
      try {
        const response = await settingsApi.getSettings()
        if (response.code === 200 && response.data) {
          this.settings = {
            general: { ...this.settings.general, ...response.data.general },
            scan: { ...this.settings.scan, ...response.data.scan },
            notification: { ...this.settings.notification, ...response.data.notification },
            security: { ...this.settings.security, ...response.data.security }
          }
        }
      } catch (error) {
        console.error('获取设置失败:', error)
      } finally {
        this.loading = false
      }
    },
    async saveSettings() {
      this.saving = true
      try {
        const response = await settingsApi.updateSettings({
          general: this.settings.general,
          scan: this.settings.scan,
          notification: this.settings.notification,
          security: this.settings.security
        })
        
        if (response.code === 200) {
          alert('设置已保存！')
        } else {
          alert('保存失败: ' + (response.message || '未知错误'))
        }
      } catch (error) {
        console.error('保存设置失败:', error)
        alert('保存设置失败: ' + error.message)
      } finally {
        this.saving = false
      }
    },
    async resetSettings() {
      if (confirm('确定要重置为默认设置吗？')) {
        try {
          const response = await settingsApi.resetSettings()
          if (response.code === 200) {
            await this.fetchSettings()
            alert('已重置为默认设置')
          } else {
            alert('重置失败: ' + (response.message || '未知错误'))
          }
        } catch (error) {
          console.error('重置设置失败:', error)
          alert('重置设置失败: ' + error.message)
        }
      }
    },
    createApiKey() {
      const name = prompt('请输入API密钥名称:')
      if (name) {
        const newKey = {
          id: Date.now(),
          name: name,
          masked: 'wsa_****************************' + Math.random().toString(36).substr(2, 6),
          createdAt: new Date().toLocaleString('zh-CN')
        }
        this.apiKeys.push(newKey)
      }
    },
    regenerateKey(keyId) {
      if (confirm('确定要重新生成此API密钥吗？旧密钥将失效。')) {
        const key = this.apiKeys.find(k => k.id === keyId)
        if (key) {
          key.masked = 'wsa_****************************' + Math.random().toString(36).substr(2, 6)
          key.createdAt = new Date().toLocaleString('zh-CN')
        }
      }
    },
    deleteKey(keyId) {
      if (confirm('确定要删除此API密钥吗？')) {
        this.apiKeys = this.apiKeys.filter(k => k.id !== keyId)
      }
    }
  }
}
</script>

<style scoped>
.settings {
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

.settings-container {
  display: grid;
  grid-template-columns: 250px 1fr;
  gap: var(--spacing-xl);
  margin-bottom: var(--spacing-xl);
}

/* 设置导航 */
.settings-nav {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
}

.nav-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-md);
  border-radius: var(--border-radius);
  cursor: pointer;
  transition: all 0.2s ease;
  color: var(--text-primary);
}

.nav-item:hover {
  background-color: var(--background-color);
}

.nav-item.active {
  background-color: rgba(26, 58, 108, 0.1);
  color: var(--primary-color);
  border-left: 3px solid var(--primary-color);
}

.nav-icon {
  font-size: 18px;
}

.nav-text {
  font-weight: 500;
}

/* 设置内容 */
.settings-content {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
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

.settings-form {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  cursor: pointer;
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
  content: '✓';
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  color: white;
  font-size: 10px;
  font-weight: bold;
}

/* 邮件设置 */
.email-settings {
  margin-left: var(--spacing-lg);
  padding-left: var(--spacing-lg);
  border-left: 2px solid var(--border-color);
}

.notification-events h4 {
  color: var(--primary-color);
  margin-bottom: var(--spacing-md);
}

.event-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

/* 扫描规则 */
.rules-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.rule-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-md);
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius);
}

.rule-name {
  font-weight: bold;
  color: var(--text-primary);
  margin-bottom: var(--spacing-xs);
}

.rule-description {
  color: var(--text-secondary);
  font-size: 12px;
}

/* 开关样式 */
.switch {
  position: relative;
  display: inline-block;
  width: 44px;
  height: 24px;
}

.switch input {
  opacity: 0;
  width: 0;
  height: 0;
}

.slider {
  position: absolute;
  cursor: pointer;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: #ccc;
  transition: 0.2s;
  border-radius: 24px;
}

.slider:before {
  position: absolute;
  content: "";
  height: 18px;
  width: 18px;
  left: 3px;
  bottom: 3px;
  background-color: white;
  transition: 0.2s;
  border-radius: 50%;
}

input:checked + .slider {
  background-color: var(--secondary-color);
}

input:checked + .slider:before {
  transform: translateX(20px);
}

/* API密钥 */
.api-keys {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.api-key-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-md);
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius);
}

.key-name {
  font-weight: bold;
  color: var(--text-primary);
  margin-bottom: var(--spacing-xs);
}

.key-value {
  font-family: monospace;
  color: var(--text-secondary);
  font-size: 12px;
  margin-bottom: var(--spacing-xs);
}

.key-created {
  color: var(--text-secondary);
  font-size: 11px;
}

.key-actions {
  display: flex;
  gap: var(--spacing-sm);
}

/* 设置页脚 */
.settings-footer {
  border-top: 1px solid var(--border-color);
  padding-top: var(--spacing-lg);
}

.footer-actions {
  display: flex;
  justify-content: flex-end;
  gap: var(--spacing-md);
}

/* 响应式设计 */
@media (max-width: 768px) {
  .settings-container {
    grid-template-columns: 1fr;
  }
  
  .settings-nav {
    flex-direction: row;
    overflow-x: auto;
    padding-bottom: var(--spacing-sm);
  }
  
  .nav-item {
    flex-shrink: 0;
    min-width: 120px;
  }
  
  .rule-item {
    flex-direction: column;
    align-items: flex-start;
    gap: var(--spacing-sm);
  }
  
  .api-key-item {
    flex-direction: column;
    align-items: flex-start;
    gap: var(--spacing-sm);
  }
  
  .footer-actions {
    flex-direction: column;
  }
}
</style>
