import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

const STORAGE_KEY = 'vulnerabilities_store'

const loadFromStorage = () => {
  try {
    const stored = localStorage.getItem(STORAGE_KEY)
    if (stored) {
      return JSON.parse(stored)
    }
  } catch (error) {
    console.error('加载漏洞状态失败:', error)
    return null
  }
  return null
}

const saveToStorage = (state) => {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(state))
  } catch (error) {
    console.error('保存漏洞状态失败:', error)
  }
}

export const useVulnerabilityStore = defineStore('vulnerabilities', () => {
  const stored = loadFromStorage() || {}
  const vulnerabilities = ref(stored.vulnerabilities || [])
  const currentVulnerability = ref(stored.currentVulnerability || null)
  const filters = ref(stored.filters || {
    severity: '',
    status: '',
    search: '',
    dateRange: null
  })
  const loading = ref(false)
  const error = ref(null)

  const vulnerabilityCount = computed(() => vulnerabilities.value.length)
  const criticalVulnerabilities = computed(() => 
    vulnerabilities.value.filter(v => v.severity === 'Critical' || v.severity === 'critical')
  )
  const highVulnerabilities = computed(() => 
    vulnerabilities.value.filter(v => v.severity === 'High' || v.severity === 'high')
  )
  const mediumVulnerabilities = computed(() => 
    vulnerabilities.value.filter(v => v.severity === 'Medium' || v.severity === 'medium')
  )
  const lowVulnerabilities = computed(() => 
    vulnerabilities.value.filter(v => v.severity === 'Low' || v.severity === 'low')
  )
  const openVulnerabilities = computed(() => 
    vulnerabilities.value.filter(v => v.status === 'open')
  )

  const filteredVulnerabilities = computed(() => {
    let result = vulnerabilities.value

    if (filters.value.severity) {
      result = result.filter(v => 
        v.severity.toLowerCase() === filters.value.severity.toLowerCase()
      )
    }

    if (filters.value.status) {
      result = result.filter(v => 
        v.status.toLowerCase() === filters.value.status.toLowerCase()
      )
    }

    if (filters.value.search) {
      const search = filters.value.search.toLowerCase()
      result = result.filter(v => 
        v.name?.toLowerCase().includes(search) ||
        v.description?.toLowerCase().includes(search) ||
        v.target?.toLowerCase().includes(search)
      )
    }

    return result
  })

  const severityDistribution = computed(() => ({
    critical: criticalVulnerabilities.value.length,
    high: highVulnerabilities.value.length,
    medium: mediumVulnerabilities.value.length,
    low: lowVulnerabilities.value.length
  }))

  function setVulnerabilities(newVulnerabilities) {
    vulnerabilities.value = newVulnerabilities
    saveToStorage({ vulnerabilities: newVulnerabilities, filters: filters.value, currentVulnerability: currentVulnerability.value })
  }

  function addVulnerability(vulnerability) {
    vulnerabilities.value.unshift(vulnerability)
    saveToStorage({ vulnerabilities: vulnerabilities.value, filters: filters.value, currentVulnerability: currentVulnerability.value })
  }

  function updateVulnerability(vulnId, updates) {
    const index = vulnerabilities.value.findIndex(v => v.id === vulnId)
    if (index !== -1) {
      vulnerabilities.value[index] = { ...vulnerabilities.value[index], ...updates }
      saveToStorage({ vulnerabilities: vulnerabilities.value, filters: filters.value, currentVulnerability: currentVulnerability.value })
    }
  }

  function removeVulnerability(vulnId) {
    vulnerabilities.value = vulnerabilities.value.filter(v => v.id !== vulnId)
    saveToStorage({ vulnerabilities: vulnerabilities.value, filters: filters.value, currentVulnerability: currentVulnerability.value })
  }

  function setCurrentVulnerability(vulnerability) {
    currentVulnerability.value = vulnerability
    saveToStorage({ vulnerabilities: vulnerabilities.value, filters: filters.value, currentVulnerability: vulnerability })
  }

  function setFilters(newFilters) {
    filters.value = { ...filters.value, ...newFilters }
    saveToStorage({ vulnerabilities: vulnerabilities.value, filters: filters.value, currentVulnerability: currentVulnerability.value })
  }

  function resetFilters() {
    filters.value = {
      severity: '',
      status: '',
      search: '',
      dateRange: null
    }
    saveToStorage({ vulnerabilities: vulnerabilities.value, filters: filters.value, currentVulnerability: currentVulnerability.value })
  }

  function setLoading(isLoading) {
    loading.value = isLoading
  }

  function setError(errorMessage) {
    error.value = errorMessage
  }

  function clearError() {
    error.value = null
  }

  function clearVulnerabilities() {
    vulnerabilities.value = []
    currentVulnerability.value = null
    error.value = null
    localStorage.removeItem(STORAGE_KEY)
  }

  return {
    vulnerabilities,
    currentVulnerability,
    filters,
    loading,
    error,
    vulnerabilityCount,
    criticalVulnerabilities,
    highVulnerabilities,
    mediumVulnerabilities,
    lowVulnerabilities,
    openVulnerabilities,
    filteredVulnerabilities,
    severityDistribution,
    setVulnerabilities,
    addVulnerability,
    updateVulnerability,
    removeVulnerability,
    setCurrentVulnerability,
    setFilters,
    resetFilters,
    setLoading,
    setError,
    clearError,
    clearVulnerabilities
  }
})
