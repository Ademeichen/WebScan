import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

const STORAGE_KEY = 'settings_store'

const loadFromStorage = () => {
  try {
    const stored = localStorage.getItem(STORAGE_KEY)
    if (stored) {
      return JSON.parse(stored)
    }
  } catch (error) {
    console.error('加载设置失败:', error)
    return null
  }
  return null
}

const saveToStorage = (state) => {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(state))
  } catch (error) {
    console.error('保存设置失败:', error)
  }
}

export const useSettingsStore = defineStore('settings', () => {
  const stored = loadFromStorage()
  const settings = ref(stored?.settings || {
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
  })
  
  const loading = ref(false)
  const saving = ref(false)
  const error = ref(null)

  const theme = computed(() => settings.value.general.theme)
  const language = computed(() => settings.value.general.language)
  const timezone = computed(() => settings.value.general.timezone)

  function setSettings(newSettings) {
    settings.value = {
      general: { ...settings.value.general, ...newSettings.general },
      scan: { ...settings.value.scan, ...newSettings.scan },
      notification: { ...settings.value.notification, ...newSettings.notification },
      security: { ...settings.value.security, ...newSettings.security }
    }
    saveToStorage({ settings: settings.value })
  }

  function updateSetting(category, key, value) {
    if (settings.value[category]) {
      settings.value[category][key] = value
      saveToStorage({ settings: settings.value })
    }
  }

  function setCategorySettings(category, categorySettings) {
    if (settings.value[category]) {
      settings.value[category] = { ...settings.value[category], ...categorySettings }
      saveToStorage({ settings: settings.value })
    }
  }

  function setLoading(isLoading) {
    loading.value = isLoading
  }

  function setSaving(isSaving) {
    saving.value = isSaving
  }

  function setError(errorMessage) {
    error.value = errorMessage
  }

  function clearError() {
    error.value = null
  }

  function resetSettings() {
    settings.value = {
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
    }
    error.value = null
    saveToStorage({ settings: settings.value })
  }

  return {
    settings,
    loading,
    saving,
    error,
    theme,
    language,
    timezone,
    setSettings,
    updateSetting,
    setCategorySettings,
    setLoading,
    setSaving,
    setError,
    clearError,
    resetSettings
  }
})
