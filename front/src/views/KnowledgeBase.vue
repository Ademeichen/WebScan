<template>
  <div class="knowledge-base">
    <div class="page-header">
      <h1>漏洞知识库</h1>
      <p class="page-subtitle">查询和管理漏洞知识库信息</p>
    </div>

    <div class="kb-layout">
      <div class="search-section">
        <div class="card">
          <div class="card-header">
            <h3 class="card-title">搜索漏洞</h3>
          </div>
          <div class="search-content">
            <div class="seebug-status" :class="{ 'status-available': seebugStatus.available, 'status-unavailable': !seebugStatus.available }">
              <span class="status-icon">{{ seebugStatus.available ? '✅' : '⚠️' }}</span>
              <span class="status-text">Seebug API: {{ seebugStatus.available ? '已连接' : '未连接' }}</span>
              <button @click="checkSeebugStatus" class="btn-refresh" title="刷新状态">🔄</button>
            </div>

            <div class="form-group">
              <label class="form-label">搜索模式</label>
              <div class="search-mode-toggle">
                <button 
                  @click="searchMode = 'local'" 
                  :class="['mode-btn', { active: searchMode === 'local' }]"
                >
                  📚 本地数据库
                </button>
                <button 
                  @click="searchMode = 'seebug'" 
                  :class="['mode-btn', { active: searchMode === 'seebug' }]"
                  :disabled="!seebugStatus.available"
                >
                  🌐 Seebug 实时搜索
                </button>
              </div>
              <div class="mode-hint">
                {{ searchMode === 'local' ? '从本地数据库搜索已同步的漏洞' : '从 Seebug 实时搜索并自动保存到本地数据库' }}
              </div>
            </div>

            <div class="form-group">
              <label class="form-label">关键词</label>
              <input
                v-model="searchKeyword"
                type="text"
                class="form-input"
                placeholder="输入漏洞名称、CVE编号或描述"
                @keyup.enter="handleSearch"
              />
            </div>

            <div v-if="searchMode === 'local'" class="form-group">
              <label class="form-label">数据源</label>
              <select v-model="selectedSource" class="form-select">
                <option value="">全部</option>
                <option value="seebug">Seebug</option>
                <option value="exploit-db">Exploit-DB</option>
              </select>
            </div>

            <div v-if="searchMode === 'local'" class="form-group">
              <label class="checkbox-label">
                <input v-model="hasPOC" type="checkbox" class="checkbox-input" />
                <span class="checkbox-custom"></span>
                仅显示有POC的漏洞
              </label>
            </div>

            <div class="search-actions">
              <button @click="handleSearch" class="btn btn-primary" :disabled="searching || searchingFromSeebug">
                <span v-if="searching || searchingFromSeebug">⏳ 搜索中...</span>
                <span v-else>{{ searchMode === 'local' ? '🔍 搜索本地' : '🔍 从 Seebug 搜索' }}</span>
              </button>
              <button v-if="searchMode === 'local'" @click="syncVulnerabilities" class="btn btn-secondary" :disabled="syncing">
                <span v-if="syncing">⏳ 同步中...</span>
                <span v-else>🔄 同步数据</span>
              </button>
            </div>
          </div>
        </div>
      </div>

      <div class="results-section">
        <div class="card">
          <div class="card-header">
            <h3 class="card-title">漏洞列表</h3>
            <div class="result-info">
              <span>共 {{ total }} 条记录</span>
              <span>第 {{ currentPage }} / {{ totalPages }} 页</span>
            </div>
          </div>

          <div v-if="loading" class="loading-state">
            <div class="loading-spinner"></div>
            <div class="loading-text">加载中...</div>
          </div>

          <div v-else-if="vulnerabilities.length === 0" class="empty-state">
            <div class="empty-icon">📚</div>
            <div class="empty-title">暂无漏洞数据</div>
            <div class="empty-description">点击"同步数据"按钮从外部数据源获取漏洞信息</div>
          </div>

          <div v-else class="vulnerabilities-list">
            <div
              v-for="vuln in vulnerabilities"
              :key="vuln.id"
              class="vuln-item"
              @click="handleViewDetail(vuln)"
            >
              <div class="vuln-header">
                <div class="vuln-title">{{ vuln.name }}</div>
                <div class="vuln-severity" :class="`severity-${getSeverityClass(vuln.severity)}`">
                  {{ vuln.severity || '未知' }}
                </div>
              </div>

              <div v-if="vuln.cve_id" class="vuln-cve">
                <span class="cve-badge">{{ vuln.cve_id }}</span>
              </div>

              <div v-if="vuln.description" class="vuln-description">
                {{ vuln.description }}
              </div>

              <div class="vuln-meta">
                <span class="meta-item">
                  <span class="meta-label">来源:</span>
                  <span class="meta-value source-badge" :class="`source-${vuln.source}`">
                    {{ getSourceText(vuln.source) }}
                  </span>
                </span>
                <span v-if="vuln.cvss_score" class="meta-item">
                  <span class="meta-label">CVSS:</span>
                  <span class="meta-value cvss-score" :class="`cvss-${getCVSSClass(vuln.cvss_score)}`">
                    {{ vuln.cvss_score }}
                  </span>
                </span>
                <span v-if="vuln.has_poc" class="meta-item">
                  <span class="meta-label">POC:</span>
                  <span class="meta-value poc-badge">有</span>
                </span>
                <span class="meta-item">
                  <span class="meta-label">更新时间:</span>
                  <span class="meta-value">{{ formatDate(vuln.updated_at) }}</span>
                </span>
              </div>
            </div>
          </div>

          <div v-if="total > pageSize" class="pagination">
            <button
              class="btn-page"
              :disabled="currentPage === 1"
              @click="currentPage--; searchVulnerabilities()"
            >
              上一页
            </button>
            <span class="page-info">第 {{ currentPage }} / {{ totalPages }} 页</span>
            <button
              class="btn-page"
              :disabled="currentPage === totalPages"
              @click="currentPage++; searchVulnerabilities()"
            >
              下一页
            </button>
          </div>
        </div>
      </div>
    </div>

    <div v-if="selectedVuln" class="detail-modal" @click.self="selectedVuln = null">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h2>{{ selectedVuln.name }}</h2>
          <button class="btn-close" @click="selectedVuln = null">×</button>
        </div>
        <div class="modal-body">
          <div v-if="selectedVuln.cve_id" class="detail-section">
            <h3>CVE编号</h3>
            <div class="detail-value cve-badge">{{ selectedVuln.cve_id }}</div>
          </div>

          <div class="detail-section">
            <h3>严重程度</h3>
            <div
              class="detail-value severity-badge"
              :class="`severity-${getSeverityClass(selectedVuln.severity)}`"
            >
              {{ selectedVuln.severity || '未知' }}
            </div>
          </div>

          <div v-if="selectedVuln.cvss_score" class="detail-section">
            <h3>CVSS评分</h3>
            <div
              class="detail-value cvss-badge"
              :class="`cvss-${getCVSSClass(selectedVuln.cvss_score)}`"
            >
              {{ selectedVuln.cvss_score }}
            </div>
          </div>

          <div v-if="selectedVuln.affected_product" class="detail-section">
            <h3>受影响产品</h3>
            <div class="detail-value">{{ selectedVuln.affected_product }}</div>
          </div>

          <div v-if="selectedVuln.description" class="detail-section">
            <h3>漏洞描述</h3>
            <div class="detail-value description-content">{{ selectedVuln.description }}</div>
          </div>

          <div v-if="selectedVuln.solution" class="detail-section">
            <h3>修复建议</h3>
            <div class="detail-value solution-content">{{ selectedVuln.solution }}</div>
          </div>

          <div class="detail-section">
            <h3>数据源</h3>
            <div
              class="detail-value source-badge"
              :class="`source-${selectedVuln.source}`"
            >
              {{ getSourceText(selectedVuln.source) }}
            </div>
          </div>

          <div v-if="selectedVuln.ssvid" class="detail-section">
            <h3>Seebug POC</h3>
            <div class="detail-value">
              <button @click="downloadPOC(selectedVuln.ssvid)" class="btn btn-primary" :disabled="downloadingPOC">
                <span v-if="downloadingPOC">⏳ 下载中...</span>
                <span v-else>📥 下载POC</span>
              </button>
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
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { kbApi, seebugAgentApi } from '@/utils/api'
import Alert from '@/components/common/Alert.vue'
import { formatDate } from '@/utils/date'

export default {
  name: 'KnowledgeBase',
  components: {
    Alert
  },
  setup() {
    const router = useRouter()
    const loading = ref(false)
    const searching = ref(false)
    const syncing = ref(false)
    const downloadingPOC = ref(false)
    const searchingFromSeebug = ref(false)
    const errorMessage = ref('')
    const successMessage = ref('')
    const vulnerabilities = ref([])
    const selectedVuln = ref(null)
    const searchKeyword = ref('')
    const selectedSource = ref('')
    const hasPOC = ref(false)
    const currentPage = ref(1)
    const pageSize = ref(10)
    const total = ref(0)
    const seebugStatus = ref({ available: false, message: '' })
    const searchMode = ref('local')

    const totalPages = computed(() => Math.ceil(total.value / pageSize.value))

    const checkSeebugStatus = async () => {
      try {
        const response = await seebugAgentApi.getStatus()
        seebugStatus.value = {
          available: response.available || false,
          message: response.message || ''
        }
      } catch (error) {
        console.error('检查 Seebug 状态失败:', error)
        seebugStatus.value = {
          available: false,
          message: '无法连接到 Seebug 服务'
        }
      }
    }

    const searchVulnerabilities = async () => {
      searching.value = true
      errorMessage.value = ''
      
      try {
        const params = {
          page: currentPage.value,
          page_size: pageSize.value,
          keyword: searchKeyword.value || undefined,
          source: selectedSource.value || undefined,
          has_poc: hasPOC.value || undefined
        }

        const response = await kbApi.search(params)
        
        if (response && response.code === 200 && response.data) {
          vulnerabilities.value = response.data.items || []
          total.value = response.data.total || 0
        } else if (response && response.total !== undefined) {
          vulnerabilities.value = response.items || []
          total.value = response.total
        } else {
          vulnerabilities.value = []
          total.value = 0
        }
      } catch (error) {
        console.error('搜索漏洞失败:', error)
        errorMessage.value = '搜索漏洞失败，请稍后重试'
        vulnerabilities.value = []
        total.value = 0
      } finally {
        searching.value = false
      }
    }

    const searchFromSeebug = async () => {
      if (!searchKeyword.value.trim()) {
        errorMessage.value = '请输入搜索关键词'
        return
      }

      searchingFromSeebug.value = true
      errorMessage.value = ''
      
      try {
        const response = await kbApi.searchFromSeebug({
          keyword: searchKeyword.value,
          page: currentPage.value,
          page_size: pageSize.value
        })

        if (response && response.code === 200 && response.data) {
          const pocs = response.data.pocs || []
          vulnerabilities.value = pocs.map(poc => ({
            id: poc.id,
            cve_id: poc.cve_id,
            name: poc.name,
            description: poc.description,
            severity: poc.severity,
            cvss_score: poc.cvss_score,
            affected_product: poc.affected_product,
            solution: poc.solution,
            source: 'seebug',
            has_poc: true,
            ssvid: poc.ssvid,
            is_new: poc.is_new
          }))
          total.value = response.data.total || 0
          
          const savedCount = response.data.saved_count || 0
          const updatedCount = response.data.updated_count || 0
          if (savedCount > 0 || updatedCount > 0) {
            successMessage.value = `搜索成功！新增 ${savedCount} 条，更新 ${updatedCount} 条数据已保存到本地数据库`
          } else {
            successMessage.value = `搜索成功！找到 ${total.value} 条数据（已存在于本地数据库）`
          }
        } else {
          errorMessage.value = response?.message || '从 Seebug 搜索失败'
          vulnerabilities.value = []
          total.value = 0
        }
      } catch (error) {
        console.error('从 Seebug 搜索失败:', error)
        errorMessage.value = '从 Seebug 搜索失败，请检查 API Key 配置'
        vulnerabilities.value = []
        total.value = 0
      } finally {
        searchingFromSeebug.value = false
      }
    }

    const handleSearch = () => {
      if (searchMode.value === 'seebug') {
        searchFromSeebug()
      } else {
        searchVulnerabilities()
      }
    }

    const syncVulnerabilities = async () => {
      syncing.value = true
      errorMessage.value = ''
      
      try {
        const response = await kbApi.sync()
        if (response && response.message) {
          successMessage.value = response.message
          await searchVulnerabilities()
        }
      } catch (error) {
        console.error('同步漏洞失败:', error)
        errorMessage.value = '同步漏洞失败'
      } finally {
        syncing.value = false
      }
    }

    const downloadPOC = async (ssvid) => {
      downloadingPOC.value = true
      errorMessage.value = ''
      
      try {
        const response = await kbApi.downloadPOC(ssvid)
        if (response && response.code === 200 && response.data && response.data.poc_code) {
          const blob = new Blob([response.data.poc_code], { type: 'text/plain' })
          const url = URL.createObjectURL(blob)
          const link = document.createElement('a')
          link.href = url
          link.download = `poc_${ssvid}.py`
          link.click()
          URL.revokeObjectURL(url)
          successMessage.value = 'POC下载成功'
        } else {
          errorMessage.value = '下载POC失败'
        }
      } catch (error) {
        console.error('下载POC失败:', error)
        errorMessage.value = '下载POC失败'
      } finally {
        downloadingPOC.value = false
      }
    }

    const handleViewDetail = (vuln) => {
      router.push(`/vulnerability/${vuln.id}`)
    }

    const getSeverityClass = (severity) => {
      const s = (severity || '').toLowerCase()
      const severityMap = {
        critical: 'critical',
        high: 'high',
        medium: 'medium',
        low: 'low',
        info: 'info'
      }
      return severityMap[s] || 'info'
    }

    const getCVSSClass = (score) => {
      if (!score) return 'info'
      if (score >= 9.0) return 'critical'
      if (score >= 7.0) return 'high'
      if (score >= 4.0) return 'medium'
      if (score > 0) return 'low'
      return 'info'
    }

    const getSourceText = (source) => {
      const sourceMap = {
        seebug: 'Seebug',
        'exploit-db': 'Exploit-DB'
      }
      return sourceMap[source] || source
    }

    onMounted(() => {
      checkSeebugStatus()
      searchVulnerabilities()
    })

    return {
      loading,
      searching,
      syncing,
      downloadingPOC,
      searchingFromSeebug,
      errorMessage,
      successMessage,
      vulnerabilities,
      selectedVuln,
      searchKeyword,
      selectedSource,
      hasPOC,
      currentPage,
      pageSize,
      total,
      totalPages,
      seebugStatus,
      searchMode,
      checkSeebugStatus,
      searchVulnerabilities,
      searchFromSeebug,
      handleSearch,
      syncVulnerabilities,
      downloadPOC,
      handleViewDetail,
      getSeverityClass,
      getCVSSClass,
      getSourceText,
      formatDate
    }
  }
}
</script>

<style scoped>
.knowledge-base {
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

.kb-layout {
  display: grid;
  grid-template-columns: 350px 1fr;
  gap: var(--spacing-xl);
}

.search-section {
  position: sticky;
  top: var(--spacing-lg);
  align-self: start;
}

.search-content {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
}

.seebug-status {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-sm) var(--spacing-md);
  border-radius: var(--border-radius);
  font-size: 13px;
  margin-bottom: var(--spacing-sm);
}

.seebug-status.status-available {
  background-color: var(--color-success-bg);
  color: var(--color-success);
  border: 1px solid var(--color-success);
}

.seebug-status.status-unavailable {
  background-color: var(--color-warning-bg);
  color: var(--color-warning);
  border: 1px solid var(--color-warning);
}

.status-icon {
  font-size: 14px;
}

.status-text {
  flex: 1;
}

.btn-refresh {
  background: none;
  border: none;
  cursor: pointer;
  padding: 2px 4px;
  font-size: 12px;
  opacity: 0.7;
  transition: opacity 0.2s;
}

.btn-refresh:hover {
  opacity: 1;
}

.search-mode-toggle {
  display: flex;
  gap: var(--spacing-xs);
  margin-bottom: var(--spacing-xs);
}

.mode-btn {
  flex: 1;
  padding: var(--spacing-sm) var(--spacing-md);
  border: 1px solid var(--border-color);
  background-color: var(--bg-secondary);
  color: var(--text-secondary);
  border-radius: var(--border-radius);
  cursor: pointer;
  font-size: 13px;
  transition: all 0.2s;
}

.mode-btn:hover:not(:disabled) {
  border-color: var(--color-primary);
  color: var(--color-primary);
}

.mode-btn.active {
  background-color: var(--color-primary);
  border-color: var(--color-primary);
  color: #1a1a1a;
}

.mode-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.mode-hint {
  font-size: 12px;
  color: var(--text-secondary);
  margin-top: var(--spacing-xs);
}

.form-group {
  margin-bottom: 0;
}

.form-label {
  display: block;
  margin-bottom: var(--spacing-sm);
  font-weight: 500;
  color: var(--text-primary);
}

.form-input,
.form-select {
  width: 100%;
  padding: var(--spacing-sm) var(--spacing-md);
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius);
  font-size: 14px;
  transition: border-color 0.3s;
}

.form-input:focus,
.form-select:focus {
  outline: none;
  border-color: var(--color-primary);
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
  background-color: var(--color-primary);
  border-color: var(--color-primary);
}

.checkbox-input:checked + .checkbox-custom::after {
  content: '';
  position: absolute;
  left: 5px;
  top: 1px;
  width: 4px;
  height: 9px;
  border: solid white;
  border-width: 0 2px 2px 0;
  transform: rotate(45deg);
}

.search-actions {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.btn,
.btn-primary,
.btn-secondary {
  width: 100%;
  padding: var(--spacing-md);
  border: none;
  border-radius: var(--border-radius);
  font-size: 14px;
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

.btn-secondary:hover:not(:disabled) {
  background-color: var(--color-secondary-dark);
}

.btn-secondary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.result-info {
  display: flex;
  gap: var(--spacing-md);
  font-size: 14px;
  color: var(--text-secondary);
}

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--spacing-md);
  padding: var(--spacing-xl);
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 4px solid var(--border-color);
  border-top-color: var(--color-primary);
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

.empty-state {
  text-align: center;
  padding: var(--spacing-xl);
  color: var(--text-secondary);
}

.empty-icon {
  font-size: 4rem;
  margin-bottom: var(--spacing-lg);
}

.empty-title {
  font-size: 18px;
  font-weight: bold;
  margin-bottom: var(--spacing-sm);
  color: var(--text-primary);
}

.empty-description {
  font-size: 14px;
}

.vulnerabilities-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
  margin-top: var(--spacing-md);
}

.vuln-item {
  padding: var(--spacing-md);
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius);
  cursor: pointer;
  transition: all 0.3s;
}

.vuln-item:hover {
  background-color: var(--color-primary-bg);
  border-color: var(--color-primary);
  transform: translateX(4px);
}

.vuln-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-sm);
}

.vuln-title {
  font-weight: 600;
  color: var(--text-primary);
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.vuln-severity {
  padding: var(--spacing-xs) var(--spacing-sm);
  border-radius: var(--border-radius-sm);
  font-size: 12px;
  font-weight: 500;
  white-space: nowrap;
}

.severity-critical {
  background-color: var(--color-critical-bg);
  color: var(--color-critical);
}

.severity-high {
  background-color: var(--color-error-bg);
  color: var(--color-error);
}

.severity-medium {
  background-color: var(--color-warning-bg);
  color: var(--color-warning);
}

.severity-low {
  background-color: var(--color-info-bg);
  color: var(--color-info);
}

.severity-info {
  background-color: var(--color-success-bg);
  color: var(--color-success);
}

.vuln-cve {
  margin-bottom: var(--spacing-sm);
}

.cve-badge {
  display: inline-block;
  padding: var(--spacing-xs) var(--spacing-sm);
  background-color: var(--color-primary-bg);
  color: var(--color-primary);
  border-radius: var(--border-radius-sm);
  font-size: 12px;
  font-weight: 500;
  font-family: monospace;
}

.vuln-description {
  color: var(--text-secondary);
  font-size: 14px;
  margin-bottom: var(--spacing-sm);
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.vuln-meta {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-md);
  font-size: 12px;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
}

.meta-label {
  color: var(--text-secondary);
  font-weight: 500;
}

.meta-value {
  color: var(--text-primary);
  font-weight: 500;
}

.source-badge {
  padding: var(--spacing-xs) var(--spacing-sm);
  border-radius: var(--border-radius-sm);
  font-size: 12px;
}

.source-seebug {
  background-color: var(--color-primary-bg);
  color: var(--color-primary);
}

.source-exploit-db {
  background-color: var(--color-accent-bg);
  color: var(--color-accent);
}

.cvss-score {
  padding: var(--spacing-xs) var(--spacing-sm);
  border-radius: var(--border-radius-sm);
  font-weight: 700;
}

.cvss-critical {
  background-color: var(--color-critical-bg);
  color: var(--color-critical);
}

.cvss-high {
  background-color: var(--color-error-bg);
  color: var(--color-error);
}

.cvss-medium {
  background-color: var(--color-warning-bg);
  color: var(--color-warning);
}

.cvss-low {
  background-color: var(--color-info-bg);
  color: var(--color-info);
}

.cvss-info {
  background-color: var(--color-success-bg);
  color: var(--color-success);
}

.poc-badge {
  padding: var(--spacing-xs) var(--spacing-sm);
  background-color: var(--color-success-bg);
  color: var(--color-success);
  border-radius: var(--border-radius-sm);
  font-size: 12px;
  font-weight: 500;
}

.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: var(--spacing-md);
  margin-top: var(--spacing-xl);
  padding: var(--spacing-md);
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
  font-size: 14px;
}

.detail-modal {
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
  padding: var(--spacing-lg);
}

.modal-content {
  background-color: var(--card-bg);
  border-radius: var(--border-radius-lg);
  max-width: 800px;
  width: 100%;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: var(--shadow-lg);
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
  font-size: 2rem;
  color: var(--text-secondary);
  cursor: pointer;
  padding: 0;
  line-height: 1;
  transition: color 0.3s;
}

.btn-close:hover {
  color: var(--text-primary);
}

.modal-body {
  padding: var(--spacing-lg);
}

.detail-section {
  margin-bottom: var(--spacing-lg);
  padding-bottom: var(--spacing-lg);
  border-bottom: 1px solid var(--border-color);
}

.detail-section:last-child {
  border-bottom: none;
}

.detail-section h3 {
  margin: 0 0 var(--spacing-sm) 0;
  font-size: 1rem;
  color: var(--text-primary);
  font-weight: 600;
}

.detail-value {
  color: var(--text-secondary);
  line-height: 1.6;
}

.description-content,
.solution-content {
  padding: var(--spacing-md);
  background-color: var(--bg-secondary);
  border-radius: var(--border-radius);
}

.severity-badge {
  display: inline-block;
  padding: var(--spacing-sm) var(--spacing-md);
  border-radius: var(--border-radius);
  font-weight: 600;
}

.cvss-badge {
  display: inline-block;
  padding: var(--spacing-sm) var(--spacing-md);
  border-radius: var(--border-radius);
  font-weight: 700;
}

@media (max-width: 1024px) {
  .kb-layout {
    grid-template-columns: 1fr;
  }

  .search-section {
    position: static;
  }
}
</style>
