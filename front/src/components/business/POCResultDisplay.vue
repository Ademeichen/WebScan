<template>
  <div class="poc-result-display">
    <div class="result-header">
      <h2>POC扫描结果</h2>
      <div v-if="taskId" class="task-id">
        <span class="label">任务ID:</span>
        <span class="value">{{ taskId }}</span>
      </div>
    </div>

    <div v-if="loading" class="loading-skeleton">
      <div class="skeleton-card">
        <div class="skeleton-header"></div>
        <div class="skeleton-content">
          <div class="skeleton-line"></div>
          <div class="skeleton-line short"></div>
          <div class="skeleton-line"></div>
        </div>
      </div>
      <div class="skeleton-card">
        <div class="skeleton-header"></div>
        <div class="skeleton-content">
          <div class="skeleton-line"></div>
          <div class="skeleton-line short"></div>
        </div>
      </div>
    </div>

    <template v-else>
      <div v-if="results && results.length > 0">
        <div class="summary-section">
          <div class="summary-card">
            <h3>漏洞摘要</h3>
            <div class="severity-badges">
              <div class="severity-badge critical">
                <span class="count">{{ severityCounts.critical }}</span>
                <span class="label">严重</span>
              </div>
              <div class="severity-badge high">
                <span class="count">{{ severityCounts.high }}</span>
                <span class="label">高危</span>
              </div>
              <div class="severity-badge medium">
                <span class="count">{{ severityCounts.medium }}</span>
                <span class="label">中危</span>
              </div>
              <div class="severity-badge low">
                <span class="count">{{ severityCounts.low }}</span>
                <span class="label">低危</span>
              </div>
              <div class="severity-badge safe">
                <span class="count">{{ severityCounts.safe }}</span>
                <span class="label">安全</span>
              </div>
            </div>
          </div>

          <div class="export-section">
            <el-button type="primary" @click="exportToJSON">
              <el-icon><Download /></el-icon>
              导出JSON
            </el-button>
            <el-button type="success" @click="exportToHTML">
              <el-icon><Document /></el-icon>
              导出HTML
            </el-button>
            <el-button type="info" @click="copyToClipboard">
              <el-icon><CopyDocument /></el-icon>
              复制结果
            </el-button>
          </div>
        </div>

        <div class="filter-section">
          <div class="filter-group">
            <label>严重级别:</label>
            <el-select v-model="filterSeverity" placeholder="全部" clearable style="width: 120px">
              <el-option label="全部" value="" />
              <el-option label="严重" value="critical" />
              <el-option label="高危" value="high" />
              <el-option label="中危" value="medium" />
              <el-option label="低危" value="low" />
              <el-option label="安全" value="safe" />
            </el-select>
          </div>

          <div class="filter-group">
            <label>状态:</label>
            <el-select v-model="filterStatus" placeholder="全部" clearable style="width: 120px">
              <el-option label="全部" value="" />
              <el-option label="存在漏洞" value="vulnerable" />
              <el-option label="安全" value="safe" />
            </el-select>
          </div>

          <div class="filter-group">
            <label>排序:</label>
            <el-select v-model="sortBy" placeholder="默认排序" style="width: 150px">
              <el-option label="默认排序" value="default" />
              <el-option label="严重级别" value="severity" />
              <el-option label="执行时间" value="executionTime" />
              <el-option label="POC名称" value="pocName" />
            </el-select>
            <el-button :icon="sortOrder === 'asc' ? 'ArrowUp' : 'ArrowDown'" circle size="small" @click="toggleSortOrder" />
          </div>
        </div>

        <div class="result-list">
          <div
            v-for="(result, index) in filteredAndSortedResults"
            :key="index"
            class="result-item"
            :class="`severity-${getSeverityClass(result)}`"
          >
            <div class="result-item-header" @click="toggleExpand(index)">
              <div class="result-main-info">
                <div class="poc-name">
                  <el-icon v-if="result.status === 'vulnerable'" class="status-icon vulnerable">
                    <WarningFilled />
                  </el-icon>
                  <el-icon v-else class="status-icon safe">
                    <CircleCheckFilled />
                  </el-icon>
                  {{ result.poc_name || result.pocName || '未知POC' }}
                </div>
                <div class="result-meta">
                  <span class="target">{{ result.target || result.url || '-' }}</span>
                  <span class="execution-time">{{ formatExecutionTime(result.execution_time || result.executionTime) }}</span>
                </div>
              </div>
              <div class="result-badges">
                <el-tag :type="getStatusType(result)" size="small">
                  {{ getStatusText(result) }}
                </el-tag>
                <el-tag :type="getSeverityType(result)" size="small">
                  {{ getSeverityText(result) }}
                </el-tag>
              </div>
              <el-icon class="expand-icon" :class="{ expanded: expandedItems.includes(index) }">
                <ArrowDown />
              </el-icon>
            </div>

            <el-collapse-transition>
              <div v-show="expandedItems.includes(index)" class="result-item-body">
                <el-descriptions :column="2" border size="small">
                  <el-descriptions-item label="POC名称">
                    {{ result.poc_name || result.pocName || '-' }}
                  </el-descriptions-item>
                  <el-descriptions-item label="目标地址">
                    {{ result.target || result.url || '-' }}
                  </el-descriptions-item>
                  <el-descriptions-item label="验证状态">
                    <el-tag :type="getStatusType(result)" size="small">
                      {{ getStatusText(result) }}
                    </el-tag>
                  </el-descriptions-item>
                  <el-descriptions-item label="严重级别">
                    <el-tag :type="getSeverityType(result)" size="small">
                      {{ getSeverityText(result) }}
                    </el-tag>
                  </el-descriptions-item>
                  <el-descriptions-item label="执行时间">
                    {{ formatExecutionTime(result.execution_time || result.executionTime) }}
                  </el-descriptions-item>
                  <el-descriptions-item label="检测时间">
                    {{ formatDate(result.timestamp || result.created_at || result.detectedAt) }}
                  </el-descriptions-item>
                </el-descriptions>

                <div v-if="result.description || result.vulnerability_description" class="detail-section">
                  <h4>漏洞描述</h4>
                  <p>{{ result.description || result.vulnerability_description }}</p>
                </div>

                <div v-if="result.evidence || result.proof || result.request || result.response" class="detail-section">
                  <h4>验证证据</h4>
                  <div v-if="result.evidence" class="evidence-block">
                    <span class="evidence-label">证据:</span>
                    <pre>{{ result.evidence }}</pre>
                  </div>
                  <div v-if="result.proof" class="evidence-block">
                    <span class="evidence-label">证明:</span>
                    <pre>{{ result.proof }}</pre>
                  </div>
                  <div v-if="result.request" class="evidence-block">
                    <span class="evidence-label">请求:</span>
                    <pre>{{ result.request }}</pre>
                  </div>
                  <div v-if="result.response" class="evidence-block">
                    <span class="evidence-label">响应:</span>
                    <pre>{{ typeof result.response === 'object' ? JSON.stringify(result.response, null, 2) : result.response }}</pre>
                  </div>
                </div>

                <div v-if="result.remediation || result.solution" class="detail-section">
                  <h4>修复建议</h4>
                  <p>{{ result.remediation || result.solution }}</p>
                </div>

                <div v-if="result.references && result.references.length > 0" class="detail-section">
                  <h4>参考链接</h4>
                  <ul class="reference-list">
                    <li v-for="(ref, refIndex) in result.references" :key="refIndex">
                      <a v-if="typeof ref === 'string' && ref.startsWith('http')" :href="ref" target="_blank" rel="noopener noreferrer">
                        {{ ref }}
                      </a>
                      <span v-else>{{ ref }}</span>
                    </li>
                  </ul>
                </div>
              </div>
            </el-collapse-transition>
          </div>
        </div>

        <div v-if="filteredAndSortedResults.length === 0" class="empty-result">
          <el-empty description="没有符合条件的结果" />
        </div>
      </div>

      <div v-else class="empty-result">
        <el-empty description="暂无扫描结果" />
      </div>
    </template>

    <el-message v-if="copySuccess" type="success" :duration="2000">
      结果已复制到剪贴板
    </el-message>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import {
  Download,
  Document,
  CopyDocument,
  WarningFilled,
  CircleCheckFilled,
  ArrowDown
} from '@element-plus/icons-vue'

const props = defineProps({
  results: {
    type: Array,
    default: () => []
  },
  loading: {
    type: Boolean,
    default: false
  },
  taskId: {
    type: String,
    default: ''
  }
})

const filterSeverity = ref('')
const filterStatus = ref('')
const sortBy = ref('default')
const sortOrder = ref('desc')
const expandedItems = ref([])
const copySuccess = ref(false)

const severityOrder = {
  critical: 0,
  high: 1,
  medium: 2,
  low: 3,
  safe: 4,
  info: 5
}

const severityCounts = computed(() => {
  const counts = {
    critical: 0,
    high: 0,
    medium: 0,
    low: 0,
    safe: 0
  }

  if (!props.results) return counts

  props.results.forEach(result => {
    const severity = getSeverityValue(result)
    if (severity === 'critical') counts.critical++
    else if (severity === 'high') counts.high++
    else if (severity === 'medium') counts.medium++
    else if (severity === 'low') counts.low++
    else counts.safe++
  })

  return counts
})

const filteredAndSortedResults = computed(() => {
  let filtered = [...(props.results || [])]

  if (filterSeverity.value) {
    filtered = filtered.filter(result => getSeverityValue(result) === filterSeverity.value)
  }

  if (filterStatus.value) {
    filtered = filtered.filter(result => {
      const status = (result.status || '').toLowerCase()
      if (filterStatus.value === 'vulnerable') {
        return status === 'vulnerable' || status === 'vuln' || status === 'found'
      }
      return status === 'safe' || status === 'not_vulnerable' || status === 'not found'
    })
  }

  if (sortBy.value !== 'default') {
    filtered.sort((a, b) => {
      let comparison = 0

      if (sortBy.value === 'severity') {
        const severityA = severityOrder[getSeverityValue(a)] ?? 5
        const severityB = severityOrder[getSeverityValue(b)] ?? 5
        comparison = severityA - severityB
      } else if (sortBy.value === 'executionTime') {
        const timeA = a.execution_time || a.executionTime || 0
        const timeB = b.execution_time || b.executionTime || 0
        comparison = timeA - timeB
      } else if (sortBy.value === 'pocName') {
        const nameA = (a.poc_name || a.pocName || '').toLowerCase()
        const nameB = (b.poc_name || b.pocName || '').toLowerCase()
        comparison = nameA.localeCompare(nameB)
      }

      return sortOrder.value === 'asc' ? comparison : -comparison
    })
  }

  return filtered
})

watch(() => props.results, () => {
  expandedItems.value = []
}, { deep: true })

function getSeverityValue(result) {
  const severity = (result.severity || result.level || '').toLowerCase()
  const status = (result.status || '').toLowerCase()

  if (status === 'safe' || status === 'not_vulnerable' || status === 'not found') {
    return 'safe'
  }

  if (severity === 'critical') return 'critical'
  if (severity === 'high') return 'high'
  if (severity === 'medium') return 'medium'
  if (severity === 'low') return 'low'

  return 'safe'
}

function getSeverityClass(result) {
  return getSeverityValue(result)
}

function getSeverityText(result) {
  const severity = getSeverityValue(result)
  const textMap = {
    critical: '严重',
    high: '高危',
    medium: '中危',
    low: '低危',
    safe: '安全'
  }
  return textMap[severity] || '未知'
}

function getSeverityType(result) {
  const severity = getSeverityValue(result)
  const typeMap = {
    critical: 'danger',
    high: 'danger',
    medium: 'warning',
    low: 'info',
    safe: 'success'
  }
  return typeMap[severity] || 'info'
}

function getStatusType(result) {
  const status = (result.status || '').toLowerCase()
  if (status === 'vulnerable' || status === 'vuln' || status === 'found') {
    return 'danger'
  }
  return 'success'
}

function getStatusText(result) {
  const status = (result.status || '').toLowerCase()
  if (status === 'vulnerable' || status === 'vuln' || status === 'found') {
    return '存在漏洞'
  }
  return '安全'
}

function formatExecutionTime(time) {
  if (!time) return '-'
  if (typeof time === 'number') {
    if (time < 1000) return `${time}ms`
    return `${(time / 1000).toFixed(2)}s`
  }
  return time
}

function formatDate(dateStr) {
  if (!dateStr) return '-'
  try {
    const date = new Date(dateStr)
    return date.toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    })
  } catch {
    return dateStr
  }
}

function toggleExpand(index) {
  const idx = expandedItems.value.indexOf(index)
  if (idx === -1) {
    expandedItems.value.push(index)
  } else {
    expandedItems.value.splice(idx, 1)
  }
}

function toggleSortOrder() {
  sortOrder.value = sortOrder.value === 'asc' ? 'desc' : 'asc'
}

function exportToJSON() {
  try {
    const data = {
      taskId: props.taskId,
      exportTime: new Date().toISOString(),
      summary: severityCounts.value,
      results: props.results
    }

    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `poc-result-${props.taskId || Date.now()}.json`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)

    ElMessage.success('JSON导出成功')
  } catch (error) {
    ElMessage.error('导出失败: ' + error.message)
  }
}

function exportToHTML() {
  try {
    const htmlContent = generateHTMLReport()
    const blob = new Blob([htmlContent], { type: 'text/html;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `poc-result-${props.taskId || Date.now()}.html`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)

    ElMessage.success('HTML导出成功')
  } catch (error) {
    ElMessage.error('导出失败: ' + error.message)
  }
}

function generateHTMLReport() {
  const severityColors = {
    critical: '#dc3545',
    high: '#fd7e14',
    medium: '#ffc107',
    low: '#17a2b8',
    safe: '#28a745'
  }

  let resultsHTML = ''
  props.results.forEach((result, index) => {
    const severity = getSeverityValue(result)
    const severityText = getSeverityText(result)
    const statusText = getStatusText(result)
    const color = severityColors[severity] || '#6c757d'

    resultsHTML += `
      <div class="result-item" style="border-left: 4px solid ${color}; margin-bottom: 16px; padding: 16px; background: #f8f9fa; border-radius: 8px;">
        <h4 style="margin: 0 0 8px 0; color: #333;">${result.poc_name || result.pocName || '未知POC'}</h4>
        <div style="display: flex; gap: 8px; margin-bottom: 8px;">
          <span style="padding: 2px 8px; border-radius: 4px; font-size: 12px; background: ${statusText === '存在漏洞' ? '#dc3545' : '#28a745'}; color: white;">${statusText}</span>
          <span style="padding: 2px 8px; border-radius: 4px; font-size: 12px; background: ${color}; color: white;">${severityText}</span>
        </div>
        <p style="margin: 4px 0; color: #666;"><strong>目标:</strong> ${result.target || result.url || '-'}</p>
        <p style="margin: 4px 0; color: #666;"><strong>执行时间:</strong> ${formatExecutionTime(result.execution_time || result.executionTime)}</p>
        ${result.description || result.vulnerability_description ? `<p style="margin: 4px 0; color: #666;"><strong>描述:</strong> ${result.description || result.vulnerability_description}</p>` : ''}
      </div>
    `
  })

  return `
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>POC扫描报告 - ${props.taskId || '未知任务'}</title>
  <style>
    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 1200px; margin: 0 auto; padding: 20px; background: #fff; }
    h1 { color: #333; border-bottom: 2px solid #4a90e2; padding-bottom: 10px; }
    h2 { color: #555; margin-top: 30px; }
    .summary { display: flex; gap: 16px; margin: 20px 0; flex-wrap: wrap; }
    .badge { padding: 12px 20px; border-radius: 8px; text-align: center; min-width: 80px; }
    .badge .count { font-size: 24px; font-weight: bold; display: block; }
    .badge .label { font-size: 12px; opacity: 0.9; }
    .badge.critical { background: #dc3545; color: white; }
    .badge.high { background: #fd7e14; color: white; }
    .badge.medium { background: #ffc107; color: #333; }
    .badge.low { background: #17a2b8; color: white; }
    .badge.safe { background: #28a745; color: white; }
    .meta { color: #888; font-size: 14px; margin-bottom: 20px; }
  </style>
</head>
<body>
  <h1>POC扫描报告</h1>
  <div class="meta">
    <p><strong>任务ID:</strong> ${props.taskId || '-'}</p>
    <p><strong>导出时间:</strong> ${new Date().toLocaleString('zh-CN')}</p>
  </div>

  <h2>漏洞摘要</h2>
  <div class="summary">
    <div class="badge critical"><span class="count">${severityCounts.value.critical}</span><span class="label">严重</span></div>
    <div class="badge high"><span class="count">${severityCounts.value.high}</span><span class="label">高危</span></div>
    <div class="badge medium"><span class="count">${severityCounts.value.medium}</span><span class="label">中危</span></div>
    <div class="badge low"><span class="count">${severityCounts.value.low}</span><span class="label">低危</span></div>
    <div class="badge safe"><span class="count">${severityCounts.value.safe}</span><span class="label">安全</span></div>
  </div>

  <h2>详细结果</h2>
  ${resultsHTML || '<p style="color: #888;">暂无扫描结果</p>'}
</body>
</html>
  `
}

async function copyToClipboard() {
  try {
    const data = {
      taskId: props.taskId,
      exportTime: new Date().toISOString(),
      summary: severityCounts.value,
      results: props.results
    }

    await navigator.clipboard.writeText(JSON.stringify(data, null, 2))
    ElMessage.success('结果已复制到剪贴板')
  } catch (error) {
    ElMessage.error('复制失败: ' + error.message)
  }
}
</script>

<style scoped>
.poc-result-display {
  padding: var(--spacing-lg);
}

.result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-xl);
}

.result-header h2 {
  margin: 0;
  font-size: 1.5rem;
  color: var(--text-primary);
}

.task-id {
  display: flex;
  gap: var(--spacing-xs);
  font-size: 0.875rem;
  color: var(--text-secondary);
}

.task-id .label {
  font-weight: 500;
}

.loading-skeleton {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
}

.skeleton-card {
  background: var(--card-bg);
  border-radius: var(--border-radius-lg);
  padding: var(--spacing-lg);
  animation: skeleton-pulse 1.5s ease-in-out infinite;
}

.skeleton-header {
  width: 40%;
  height: 24px;
  background: var(--border-color);
  border-radius: var(--border-radius);
  margin-bottom: var(--spacing-md);
}

.skeleton-content {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.skeleton-line {
  width: 100%;
  height: 16px;
  background: var(--border-color);
  border-radius: var(--border-radius);
}

.skeleton-line.short {
  width: 60%;
}

@keyframes skeleton-pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.summary-section {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: var(--spacing-lg);
  margin-bottom: var(--spacing-xl);
  flex-wrap: wrap;
}

.summary-card {
  flex: 1;
  min-width: 300px;
  background: var(--card-bg);
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius-lg);
  padding: var(--spacing-lg);
}

.summary-card h3 {
  margin: 0 0 var(--spacing-md) 0;
  font-size: 1rem;
  color: var(--text-primary);
}

.severity-badges {
  display: flex;
  gap: var(--spacing-md);
  flex-wrap: wrap;
}

.severity-badge {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: var(--spacing-md) var(--spacing-lg);
  border-radius: var(--border-radius);
  min-width: 70px;
}

.severity-badge .count {
  font-size: 1.5rem;
  font-weight: 700;
}

.severity-badge .label {
  font-size: 0.75rem;
  margin-top: var(--spacing-xs);
}

.severity-badge.critical {
  background-color: rgba(220, 53, 69, 0.15);
  color: #dc3545;
}

.severity-badge.high {
  background-color: rgba(253, 126, 20, 0.15);
  color: #fd7e14;
}

.severity-badge.medium {
  background-color: rgba(255, 193, 7, 0.15);
  color: #d39e00;
}

.severity-badge.low {
  background-color: rgba(23, 162, 184, 0.15);
  color: #17a2b8;
}

.severity-badge.safe {
  background-color: rgba(40, 167, 69, 0.15);
  color: #28a745;
}

.export-section {
  display: flex;
  gap: var(--spacing-sm);
  flex-wrap: wrap;
}

.filter-section {
  display: flex;
  gap: var(--spacing-lg);
  margin-bottom: var(--spacing-lg);
  padding: var(--spacing-md);
  background: var(--bg-secondary);
  border-radius: var(--border-radius);
  flex-wrap: wrap;
}

.filter-group {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
}

.filter-group label {
  font-size: 0.875rem;
  color: var(--text-secondary);
  white-space: nowrap;
}

.result-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.result-item {
  background: var(--card-bg);
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius-lg);
  overflow: hidden;
  transition: all 0.3s;
}

.result-item:hover {
  box-shadow: var(--shadow-md);
}

.result-item.severity-critical {
  border-left: 4px solid #dc3545;
}

.result-item.severity-high {
  border-left: 4px solid #fd7e14;
}

.result-item.severity-medium {
  border-left: 4px solid #ffc107;
}

.result-item.severity-low {
  border-left: 4px solid #17a2b8;
}

.result-item.severity-safe {
  border-left: 4px solid #28a745;
}

.result-item-header {
  display: flex;
  align-items: center;
  padding: var(--spacing-md) var(--spacing-lg);
  cursor: pointer;
  gap: var(--spacing-md);
}

.result-main-info {
  flex: 1;
  min-width: 0;
}

.poc-name {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: var(--spacing-xs);
}

.status-icon {
  font-size: 18px;
}

.status-icon.vulnerable {
  color: #dc3545;
}

.status-icon.safe {
  color: #28a745;
}

.result-meta {
  display: flex;
  gap: var(--spacing-lg);
  font-size: 0.875rem;
  color: var(--text-secondary);
}

.target {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.execution-time {
  white-space: nowrap;
}

.result-badges {
  display: flex;
  gap: var(--spacing-sm);
}

.expand-icon {
  transition: transform 0.3s;
  color: var(--text-secondary);
}

.expand-icon.expanded {
  transform: rotate(180deg);
}

.result-item-body {
  padding: var(--spacing-lg);
  border-top: 1px solid var(--border-color);
  background: var(--bg-secondary);
}

.detail-section {
  margin-top: var(--spacing-lg);
}

.detail-section h4 {
  margin: 0 0 var(--spacing-sm) 0;
  font-size: 0.875rem;
  color: var(--text-primary);
  font-weight: 600;
}

.detail-section p {
  margin: 0;
  font-size: 0.875rem;
  color: var(--text-secondary);
  line-height: 1.6;
}

.evidence-block {
  margin-bottom: var(--spacing-md);
}

.evidence-label {
  display: block;
  font-size: 0.75rem;
  color: var(--text-secondary);
  margin-bottom: var(--spacing-xs);
  font-weight: 500;
}

.evidence-block pre {
  margin: 0;
  padding: var(--spacing-md);
  background: var(--bg-primary);
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius);
  font-size: 0.75rem;
  overflow-x: auto;
  white-space: pre-wrap;
  word-break: break-all;
}

.reference-list {
  margin: 0;
  padding-left: var(--spacing-lg);
  font-size: 0.875rem;
}

.reference-list li {
  margin-bottom: var(--spacing-xs);
}

.reference-list a {
  color: var(--color-primary);
  text-decoration: none;
}

.reference-list a:hover {
  text-decoration: underline;
}

.empty-result {
  padding: var(--spacing-xl);
  text-align: center;
}

@media (max-width: 768px) {
  .summary-section {
    flex-direction: column;
  }

  .export-section {
    width: 100%;
    justify-content: center;
  }

  .filter-section {
    flex-direction: column;
    gap: var(--spacing-md);
  }

  .filter-group {
    width: 100%;
  }

  .result-item-header {
    flex-wrap: wrap;
  }

  .result-badges {
    width: 100%;
    justify-content: flex-start;
    margin-top: var(--spacing-sm);
  }

  .result-meta {
    flex-direction: column;
    gap: var(--spacing-xs);
  }
}
</style>
