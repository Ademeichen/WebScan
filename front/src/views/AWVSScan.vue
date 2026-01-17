<template>
  <div class="awvs-scan">
    <div class="page-header">
      <h1>AWVS 漏洞扫描</h1>
      <p class="page-description">使用 Acunetix Web Vulnerability Scanner 进行专业的漏洞扫描</p>
    </div>

    <!-- AWVS 状态卡片 -->
    <div class="status-section">
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">AWVS 服务状态</h3>
          <button @click="checkHealth" class="btn btn-sm btn-outline">
            🔄 刷新状态
          </button>
        </div>
        <div class="card-body">
          <div v-if="healthStatus.loading" class="loading-state">
            <div class="spinner"></div>
            <p>正在检查 AWVS 服务状态...</p>
          </div>
          <div v-else-if="healthStatus.connected" class="status-connected">
            <div class="status-icon success">✓</div>
            <div class="status-info">
              <h4>AWVS 服务连接正常</h4>
              <p>服务地址: {{ awvsConfig.apiUrl }}</p>
            </div>
          </div>
          <div v-else class="status-disconnected">
            <div class="status-icon error">✗</div>
            <div class="status-info">
              <h4>AWVS 服务连接失败</h4>
              <p>{{ healthStatus.error || '无法连接到 AWVS 服务' }}</p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 创建扫描任务 -->
    <div class="create-scan-section">
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">创建新的扫描任务</h3>
        </div>
        <div class="card-body">
          <form @submit.prevent="createScan" class="scan-form">
            <div class="form-group">
              <label class="form-label">目标 URL</label>
              <input
                v-model="scanForm.url"
                type="url"
                class="form-input"
                placeholder="http://example.com"
                required
              >
            </div>
            
            <div class="form-group">
              <label class="form-label">扫描类型</label>
              <select v-model="scanForm.scanType" class="form-select">
                <option value="full_scan">完整扫描</option>
                <option value="high_risk_vuln">高风险漏洞扫描</option>
                <option value="xss_vuln">XSS 漏洞扫描</option>
                <option value="sqli_vuln">SQL 注入漏洞扫描</option>
                <option value="weak_passwords">弱密码扫描</option>
                <option value="crawl_only">仅爬取</option>
              </select>
            </div>
            
            <div class="form-actions">
              <button type="submit" class="btn btn-primary" :disabled="scanForm.loading">
                <span v-if="scanForm.loading" class="spinner-small"></span>
                {{ scanForm.loading ? '创建中...' : '创建扫描任务' }}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>

    <!-- 扫描任务列表 -->
    <div class="scans-list-section">
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">扫描任务列表</h3>
          <button @click="loadScans" class="btn btn-sm btn-outline">
            🔄 刷新列表
          </button>
        </div>
        <div class="card-body">
          <div v-if="scans.loading" class="loading-state">
            <div class="spinner"></div>
            <p>正在加载扫描任务...</p>
          </div>
          <div v-else-if="scans.data.length === 0" class="empty-state">
            <div class="empty-icon">📋</div>
            <p>暂无扫描任务</p>
          </div>
          <div v-else class="scans-table">
            <table>
              <thead>
                <tr>
                  <th>ID</th>
                  <th>目标</th>
                  <th>扫描类型</th>
                  <th>状态</th>
                  <th>漏洞统计</th>
                  <th>开始时间</th>
                  <th>操作</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(scan, index) in scans.data" :key="scan.target_id">
                  <td>{{ index + 1 }}</td>
                  <td>{{ scan.target.address }}</td>
                  <td>{{ scan.profile_name }}</td>
                  <td>
                    <span :class="['status-badge', `status-${scan.current_session.status}`]">
                      {{ getStatusText(scan.current_session.status) }}
                    </span>
                  </td>
                  <td>
                    <div class="vuln-counts">
                      <span class="vuln-count high">{{ scan.current_session.severity_counts.high || 0 }}</span>
                      <span class="vuln-count medium">{{ scan.current_session.severity_counts.medium || 0 }}</span>
                      <span class="vuln-count low">{{ scan.current_session.severity_counts.low || 0 }}</span>
                    </div>
                  </td>
                  <td>{{ formatDate(scan.current_session.start_date) }}</td>
                  <td>
                    <button
                      @click="viewVulnerabilities(scan.target_id)"
                      class="btn btn-sm btn-outline"
                      :disabled="scan.current_session.status !== 'completed'"
                    >
                      查看漏洞
                    </button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>

    <!-- 漏洞列表模态框 -->
    <div v-if="showVulnModal" class="modal-overlay" @click="closeVulnModal">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h3>漏洞列表</h3>
          <button @click="closeVulnModal" class="btn-close">×</button>
        </div>
        <div class="modal-body">
          <div v-if="vulnerabilities.loading" class="loading-state">
            <div class="spinner"></div>
            <p>正在加载漏洞列表...</p>
          </div>
          <div v-else-if="vulnerabilities.data.length === 0" class="empty-state">
            <div class="empty-icon">🔒</div>
            <p>暂无漏洞</p>
          </div>
          <div v-else class="vulnerabilities-list">
            <div
              v-for="vuln in vulnerabilities.data"
              :key="vuln.vuln_id"
              class="vuln-item"
              @click="viewVulnDetail(vuln.vuln_id)"
            >
              <div class="vuln-header">
                <span :class="['severity-badge', `severity-${String(vuln.severity || 'info').toLowerCase()}`]">
                  {{ vuln.severity || 'Info' }}
                </span>
                <h4>{{ vuln.vuln_name }}</h4>
              </div>
              <div class="vuln-info">
                <p><strong>目标:</strong> {{ vuln.target }}</p>
                <p><strong>发现时间:</strong> {{ vuln.time }}</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 漏洞详情模态框 -->
    <div v-if="showVulnDetailModal" class="modal-overlay modal-large" @click="closeVulnDetailModal">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h3>漏洞详情</h3>
          <button @click="closeVulnDetailModal" class="btn-close">×</button>
        </div>
        <div class="modal-body">
          <div v-if="vulnDetail.loading" class="loading-state">
            <div class="spinner"></div>
            <p>正在加载漏洞详情...</p>
          </div>
          <div v-else-if="vulnDetail.data" class="vuln-detail">
            <div class="detail-section">
              <h4>基本信息</h4>
              <div class="detail-grid">
                <div class="detail-item">
                  <label>漏洞名称:</label>
                  <span>{{ vulnDetail.data.vt_name }}</span>
                </div>
                <div class="detail-item">
                  <label>影响URL:</label>
                  <span>{{ vulnDetail.data.affects_url }}</span>
                </div>
                <div class="detail-item">
                  <label>最后发现:</label>
                  <span>{{ vulnDetail.data.last_seen }}</span>
                </div>
              </div>
            </div>
            
            <div class="detail-section">
              <h4>漏洞详情</h4>
              <div class="detail-content" v-html="vulnDetail.data.details"></div>
            </div>
            
            <div class="detail-section">
              <h4>HTTP 请求</h4>
              <pre class="code-block">{{ vulnDetail.data.request }}</pre>
            </div>
            
            <div class="detail-section">
              <h4>修复建议</h4>
              <div class="detail-content">{{ vulnDetail.data.recommendation }}</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted } from 'vue'
import axios from 'axios'

const API_BASE = (import.meta.env.VITE_API_BASE_URL || 'http://localhost:3000/api') + '/awvs'

// AWVS 配置
const awvsConfig = reactive({
  apiUrl: 'https://127.0.0.1:3443'
})

// 轮询定时器
const pollingTimer = ref(null)

// 健康状态
const healthStatus = reactive({
  loading: false,
  connected: false,
  error: null
})

// 扫描表单
const scanForm = reactive({
  url: '',
  scanType: 'full_scan',
  loading: false
})

// 扫描任务列表
const scans = reactive({
  loading: false,
  data: []
})

// 漏洞列表
const vulnerabilities = reactive({
  loading: false,
  data: []
})

// 漏洞详情
const vulnDetail = reactive({
  loading: false,
  data: null
})

// 模态框状态
const showVulnModal = ref(false)
const showVulnDetailModal = ref(false)
const currentTargetId = ref(null)

// 检查 AWVS 健康状态
const checkHealth = async () => {
  healthStatus.loading = true
  healthStatus.error = null
  try {
    const response = await axios.get(`${API_BASE}/health`)
    healthStatus.connected = response.data.code === 200
    if (!healthStatus.connected) {
      healthStatus.error = response.data.message
    }
  } catch (error) {
    healthStatus.connected = false
    healthStatus.error = error.message
  } finally {
    healthStatus.loading = false
  }
}

// 创建扫描任务
const createScan = async () => {
  scanForm.loading = true
  try {
    const response = await axios.post(`${API_BASE}/scan`, {
      url: scanForm.url,
      scan_type: scanForm.scanType
    })
    
    if (response.data.code === 200) {
      alert('扫描任务创建成功！')
      scanForm.url = ''
      loadScans()
    } else {
      alert('创建失败: ' + response.data.message)
    }
  } catch (error) {
    alert('创建失败: ' + error.message)
  } finally {
    scanForm.loading = false
  }
}

// 加载扫描任务列表
const loadScans = async (silent = false) => {
  if (!silent) {
    scans.loading = true
  }
  try {
    const response = await axios.get(`${API_BASE}/scans`)
    if (response.data.code === 200) {
      scans.data = response.data.data || []
    }
  } catch (error) {
    console.error('加载扫描任务失败:', error)
  } finally {
    if (!silent) {
      scans.loading = false
    }
  }
}

// 查看漏洞列表
const viewVulnerabilities = async (targetId) => {
  currentTargetId.value = targetId
  vulnerabilities.loading = true
  showVulnModal.value = true
  try {
    const response = await axios.get(`${API_BASE}/vulnerabilities/${targetId}`)
    if (response.data.code === 200) {
      vulnerabilities.data = response.data.data || []
    }
  } catch (error) {
    console.error('加载漏洞列表失败:', error)
  } finally {
    vulnerabilities.loading = false
  }
}

// 查看漏洞详情
const viewVulnDetail = async (vulnId) => {
  vulnDetail.loading = true
  showVulnDetailModal.value = true
  try {
    const response = await axios.get(`${API_BASE}/vulnerability/${vulnId}`)
    if (response.data.code === 200) {
      vulnDetail.data = response.data.data
    }
  } catch (error) {
    console.error('加载漏洞详情失败:', error)
  } finally {
    vulnDetail.loading = false
  }
}

// 关闭模态框
const closeVulnModal = () => {
  showVulnModal.value = false
  vulnerabilities.data = []
}

const closeVulnDetailModal = () => {
  showVulnDetailModal.value = false
  vulnDetail.data = null
}

// 辅助函数
const getStatusText = (status) => {
  const statusMap = {
    'processing': '进行中',
    'completed': '已完成',
    'failed': '失败',
    'aborted': '已中止',
    'queued': '排队中',
    'scanning': '扫描中',
    'submitted': '已提交',
    'pending': '等待中',
    'unknown': '未知'
  }
  return statusMap[status] || status
}

const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleString()
}

// 生命周期
onMounted(() => {
  checkHealth()
  loadScans()
  
  // 启动轮询，每5秒更新一次状态
  pollingTimer.value = setInterval(() => {
    loadScans(true)
  }, 5000)
})

onUnmounted(() => {
  if (pollingTimer.value) {
    clearInterval(pollingTimer.value)
  }
})
</script>

<style scoped>
.awvs-scan {
  padding: 20px;
}

.page-header {
  margin-bottom: 24px;
}

.page-header h1 {
  font-size: 28px;
  margin: 0 0 8px 0;
  color: #1a1a1a;
}

.page-description {
  color: #666;
  margin: 0;
}

.status-section,
.create-scan-section,
.scans-list-section {
  margin-bottom: 24px;
}

.card {
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.card-header {
  padding: 16px 20px;
  border-bottom: 1px solid #e5e5e5;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-title {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
}

.card-body {
  padding: 20px;
}

.status-connected,
.status-disconnected {
  display: flex;
  align-items: center;
  gap: 16px;
}

.status-icon {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  font-weight: bold;
}

.status-icon.success {
  background: #d4edda;
  color: #155724;
}

.status-icon.error {
  background: #f8d7da;
  color: #721c24;
}

.status-info h4 {
  margin: 0 0 4px 0;
  font-size: 16px;
}

.status-info p {
  margin: 0;
  color: #666;
}

.scan-form {
  max-width: 600px;
}

.form-group {
  margin-bottom: 20px;
}

.form-label {
  display: block;
  margin-bottom: 8px;
  font-weight: 500;
  color: #333;
}

.form-input,
.form-select {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
}

.form-input:focus,
.form-select:focus {
  outline: none;
  border-color: #1890ff;
}

.form-actions {
  display: flex;
  gap: 12px;
}

.btn {
  padding: 8px 16px;
  border: none;
  border-radius: 4px;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.3s;
}

.btn-primary {
  background: #1890ff;
  color: white;
}

.btn-primary:hover {
  background: #40a9ff;
}

.btn-outline {
  background: white;
  border: 1px solid #d9d9d9;
  color: #333;
}

.btn-outline:hover {
  border-color: #1890ff;
  color: #1890ff;
}

.btn-sm {
  padding: 4px 12px;
  font-size: 12px;
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.loading-state,
.empty-state {
  text-align: center;
  padding: 40px 20px;
  color: #999;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #f3f3f3;
  border-top: 4px solid #1890ff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 16px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.spinner-small {
  display: inline-block;
  width: 14px;
  height: 14px;
  border: 2px solid #ffffff;
  border-top: 2px solid transparent;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
  margin-right: 8px;
}

.empty-icon {
  font-size: 48px;
  margin-bottom: 16px;
}

.scans-table {
  overflow-x: auto;
}

table {
  width: 100%;
  border-collapse: collapse;
}

th,
td {
  padding: 12px;
  text-align: left;
  border-bottom: 1px solid #e5e5e5;
}

th {
  background: #fafafa;
  font-weight: 600;
}

.status-badge {
  display: inline-block;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
}

.status-processing {
  background: #e6f7ff;
  color: #1890ff;
}

.status-completed {
  background: #f6ffed;
  color: #52c41a;
}

.status-failed {
  background: #fff2f0;
  color: #ff4d4f;
}

.vuln-counts {
  display: flex;
  gap: 8px;
}

.vuln-count {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 600;
}

.vuln-count.critical {
  background: #391010;
  color: #ff0000;
}

.vuln-count.high {
  background: #fff2f0;
  color: #ff4d4f;
}

.vuln-count.medium {
  background: #fff7e6;
  color: #fa8c16;
}

.vuln-count.low {
  background: #f6ffed;
  color: #52c41a;
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-large .modal-content {
  max-width: 900px;
  max-height: 80vh;
}

.modal-content {
  background: white;
  border-radius: 8px;
  max-width: 600px;
  width: 90%;
  max-height: 80vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.modal-header {
  padding: 16px 20px;
  border-bottom: 1px solid #e5e5e5;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.modal-header h3 {
  margin: 0;
  font-size: 18px;
}

.btn-close {
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: #999;
  padding: 0;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.btn-close:hover {
  color: #333;
}

.modal-body {
  padding: 20px;
  overflow-y: auto;
}

.vulnerabilities-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.vuln-item {
  padding: 12px;
  border: 1px solid #e5e5e5;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.3s;
}

.vuln-item:hover {
  border-color: #1890ff;
  background: #f0f7ff;
}

.vuln-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
}

.severity-badge {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 600;
}

.severity-critical {
  background: #391010;
  color: #ff0000;
}

.severity-high {
  background: #fff2f0;
  color: #ff4d4f;
}

.severity-medium {
  background: #fff7e6;
  color: #fa8c16;
}

.severity-low {
  background: #f6ffed;
  color: #52c41a;
}

.vuln-header h4 {
  margin: 0;
  font-size: 14px;
}

.vuln-info p {
  margin: 4px 0;
  font-size: 12px;
  color: #666;
}

.vuln-detail {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.detail-section h4 {
  margin: 0 0 12px 0;
  font-size: 16px;
  color: #333;
}

.detail-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 12px;
}

.detail-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.detail-item label {
  font-size: 12px;
  color: #666;
  font-weight: 500;
}

.detail-item span {
  font-size: 14px;
  color: #333;
}

.detail-content {
  padding: 12px;
  background: #f5f5f5;
  border-radius: 4px;
  font-size: 14px;
  line-height: 1.6;
}

.code-block {
  padding: 12px;
  background: #f5f5f5;
  border-radius: 4px;
  overflow-x: auto;
  font-size: 12px;
  line-height: 1.5;
}
</style>
