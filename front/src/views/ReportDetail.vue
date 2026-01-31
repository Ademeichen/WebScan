<template>
  <div class="report-detail-page">
    <div class="page-header">
      <div class="header-left">
        <button class="btn-back" @click="goBack">
          <span class="icon">←</span>
          返回
        </button>
        <h1 class="page-title">{{ report?.report_name || '报告详情' }}</h1>
      </div>
      <div class="header-actions">
        <button class="btn-export" @click="exportReport" :disabled="exporting">
          {{ exporting ? '导出中...' : '导出报告' }}
        </button>
        <button class="btn-print" @click="printReport">
          打印
        </button>
      </div>
    </div>

    <div class="report-content" v-if="report">
      <div class="report-section summary-section">
        <h2 class="section-title">扫描摘要</h2>
        <div class="summary-grid">
          <div class="summary-item">
            <div class="item-label">扫描类型</div>
            <div class="item-value">{{ getScanTypeName(report.task_type) }}</div>
          </div>
          <div class="summary-item">
            <div class="item-label">目标地址</div>
            <div class="item-value">{{ report.target_url || '-' }}</div>
          </div>
          <div class="summary-item">
            <div class="item-label">扫描时间</div>
            <div class="item-value">{{ formatDate(report.created_at) }}</div>
          </div>
          <div class="summary-item">
            <div class="item-label">报告格式</div>
            <div class="item-value">{{ report.report_type?.toUpperCase() }}</div>
          </div>
          <div class="summary-item">
            <div class="item-label">漏洞总数</div>
            <div class="item-value">{{ report.total_vulnerabilities || 0 }}</div>
          </div>
          <div class="summary-item">
            <div class="item-label">高危漏洞</div>
            <div class="item-value critical">{{ report.critical_count || 0 }}</div>
          </div>
          <div class="summary-item">
            <div class="item-label">中危漏洞</div>
            <div class="item-value high">{{ report.high_count || 0 }}</div>
          </div>
          <div class="summary-item">
            <div class="item-label">低危漏洞</div>
            <div class="item-value medium">{{ report.medium_count || 0 }}</div>
          </div>
        </div>
      </div>

      <div class="report-section charts-section" v-if="report.content?.charts">
        <h2 class="section-title">统计图表</h2>
        <div class="charts-container">
          <div class="chart-wrapper">
            <h3 class="chart-title">漏洞等级分布</h3>
            <div class="pie-chart">
              <div class="pie-segment critical" :style="{ width: getCriticalPercentage() + '%' }"></div>
              <div class="pie-segment high" :style="{ width: getHighPercentage() + '%' }"></div>
              <div class="pie-segment medium" :style="{ width: getMediumPercentage() + '%' }"></div>
              <div class="pie-segment low" :style="{ width: getLowPercentage() + '%' }"></div>
            </div>
            <div class="chart-legend">
              <div class="legend-item critical">
                <span class="legend-color"></span>
                <span class="legend-label">高危: {{ report.critical_count || 0 }}</span>
              </div>
              <div class="legend-item high">
                <span class="legend-color"></span>
                <span class="legend-label">中危: {{ report.high_count || 0 }}</span>
              </div>
              <div class="legend-item medium">
                <span class="legend-color"></span>
                <span class="legend-label">低危: {{ report.medium_count || 0 }}</span>
              </div>
              <div class="legend-item low">
                <span class="legend-color"></span>
                <span class="legend-label">信息: {{ report.low_count || 0 }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="report-section vulnerabilities-section" v-if="report.content?.vulnerabilities">
        <h2 class="section-title">漏洞详情</h2>
        <div class="vulnerabilities-list">
          <div class="vulnerability-card" v-for="vuln in report.content.vulnerabilities" :key="vuln.id">
            <div class="vuln-header">
              <span class="vuln-name">{{ vuln.name }}</span>
              <span class="vuln-severity" :class="vuln.severity">{{ getSeverityLabel(vuln.severity) }}</span>
            </div>
            <div class="vuln-body">
              <div class="vuln-field">
                <span class="field-label">CVE编号:</span>
                <span class="field-value">{{ vuln.cve_id || 'N/A' }}</span>
              </div>
              <div class="vuln-field">
                <span class="field-label">CVSS评分:</span>
                <span class="field-value">{{ vuln.cvss_score || 'N/A' }}</span>
              </div>
              <div class="vuln-field">
                <span class="field-label">影响组件:</span>
                <span class="field-value">{{ vuln.component || 'N/A' }}</span>
              </div>
              <div class="vuln-description">
                <span class="field-label">描述:</span>
                <p class="description-text">{{ vuln.description }}</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="report-section recommendations-section" v-if="report.content?.recommendations">
        <h2 class="section-title">修复建议</h2>
        <div class="recommendations-list">
          <div class="recommendation-item" v-for="(rec, index) in report.content.recommendations" :key="index">
            <div class="rec-number">{{ index + 1 }}</div>
            <div class="rec-content">
              <h4 class="rec-title">{{ rec.title }}</h4>
              <p class="rec-description">{{ rec.description }}</p>
              <div class="rec-priority" :class="rec.priority">
                优先级: {{ getPriorityLabel(rec.priority) }}
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="report-section appendix-section" v-if="report.content?.appendix">
        <h2 class="section-title">技术附录</h2>
        <div class="appendix-content">
          <div class="appendix-item" v-for="(item, key) in report.content.appendix" :key="key">
            <h4 class="appendix-title">{{ getAppendixTitle(key) }}</h4>
            <pre class="appendix-code">{{ item }}</pre>
          </div>
        </div>
      </div>
    </div>

    <div class="loading-state" v-else-if="loading">
      <div class="loading-spinner"></div>
      <p>加载报告详情中...</p>
    </div>

    <div class="error-state" v-else>
      <div class="error-icon">⚠️</div>
      <p>{{ errorMessage || '报告加载失败' }}</p>
      <button class="btn-retry" @click="loadReportDetail">重试</button>
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { reportsApi } from '@/utils/api'
import { formatDate } from '@/utils/date'

export default {
  name: 'ReportDetailPage',
  setup() {
    const route = useRoute()
    const router = useRouter()
    const report = ref(null)
    const loading = ref(false)
    const exporting = ref(false)
    const errorMessage = ref('')

    const loadReportDetail = async () => {
      loading.value = true
      errorMessage.value = ''
      try {
        const reportId = route.query.report
        if (!reportId) {
          throw new Error('报告ID未提供')
        }
        
        const response = await reportsApi.getReportDetail(reportId)
        if (response && response.data) {
          report.value = response.data
        } else if (response) {
          report.value = response
        } else {
          throw new Error('无效的报告数据')
        }
      } catch (error) {
        console.error('加载报告详情失败:', error)
        errorMessage.value = error.message || '加载报告详情失败'
      } finally {
        loading.value = false
      }
    }

    const getScanTypeName = (type) => {
      const types = {
        'poc': 'POC扫描',
        'agent': 'AI Agent扫描',
        'awvs': 'AWVS扫描'
      }
      return types[type] || type || '-'
    }

    const getSeverityLabel = (severity) => {
      const labels = {
        'critical': '高危',
        'high': '中危',
        'medium': '低危',
        'low': '信息'
      }
      return labels[severity] || severity
    }

    const getPriorityLabel = (priority) => {
      const labels = {
        'critical': '紧急',
        'high': '高',
        'medium': '中',
        'low': '低'
      }
      return labels[priority] || priority
    }

    const getAppendixTitle = (key) => {
      const titles = {
        'scan_config': '扫描配置',
        'raw_output': '原始输出',
        'technical_details': '技术细节'
      }
      return titles[key] || key
    }

    const getCriticalPercentage = () => {
      if (!report.value || report.value.total_vulnerabilities === 0) return 0
      return ((report.value.critical_count || 0) / report.value.total_vulnerabilities) * 100
    }

    const getHighPercentage = () => {
      if (!report.value || report.value.total_vulnerabilities === 0) return 0
      return ((report.value.high_count || 0) / report.value.total_vulnerabilities) * 100
    }

    const getMediumPercentage = () => {
      if (!report.value || report.value.total_vulnerabilities === 0) return 0
      return ((report.value.medium_count || 0) / report.value.total_vulnerabilities) * 100
    }

    const getLowPercentage = () => {
      if (!report.value || report.value.total_vulnerabilities === 0) return 0
      return ((report.value.low_count || 0) / report.value.total_vulnerabilities) * 100
    }

    const goBack = () => {
      router.push('/reports')
    }

    const exportReport = async () => {
      exporting.value = true
      try {
        const baseUrl = import.meta.env.VITE_API_BASE_URL
        const url = `${baseUrl}/reports/${report.value.id}/export?format=${report.value.report_type}`
        
        const link = document.createElement('a')
        link.href = url
        link.download = report.value.report_name || `report.${report.value.report_type}`
        link.target = '_blank'
        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)
      } catch (error) {
        console.error('导出报告失败:', error)
        errorMessage.value = '导出报告失败'
      } finally {
        exporting.value = false
      }
    }

    const printReport = () => {
      window.print()
    }

    onMounted(() => {
      loadReportDetail()
    })

    return {
      report,
      loading,
      exporting,
      errorMessage,
      formatDate,
      getScanTypeName,
      getSeverityLabel,
      getPriorityLabel,
      getAppendixTitle,
      getCriticalPercentage,
      getHighPercentage,
      getMediumPercentage,
      getLowPercentage,
      goBack,
      exportReport,
      printReport,
      loadReportDetail
    }
  }
}
</script>

<style scoped>
.report-detail-page {
  padding: 24px;
  background-color: #f5f5f5;
  min-height: 100vh;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  background-color: #ffffff;
  padding: 16px 24px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.btn-back {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 8px 16px;
  background-color: #f5f5f5;
  border: 1px solid #ddd;
  border-radius: 6px;
  color: #1a1a1a;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.3s;
}

.btn-back:hover {
  background-color: #e0e0e0;
}

.icon {
  font-size: 16px;
}

.page-title {
  margin: 0;
  font-size: 20px;
  color: #1a1a1a;
  font-weight: 600;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.btn-export,
.btn-print {
  padding: 8px 20px;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.3s;
}

.btn-export {
  background-color: #1890ff;
  color: #ffffff;
}

.btn-export:hover:not(:disabled) {
  background-color: #40a9ff;
}

.btn-export:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-print {
  background-color: #f5f5f5;
  color: #1a1a1a;
  border: 1px solid #ddd;
}

.btn-print:hover {
  background-color: #e0e0e0;
}

.report-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.report-section {
  background-color: #ffffff;
  padding: 24px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.section-title {
  margin: 0 0 20px 0;
  font-size: 18px;
  color: #1a1a1a;
  font-weight: 600;
  padding-bottom: 12px;
  border-bottom: 2px solid #f0f0f0;
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
}

.summary-item {
  padding: 16px;
  background-color: #f9f9f9;
  border-radius: 6px;
  border-left: 4px solid #1890ff;
}

.item-label {
  font-size: 12px;
  color: #666;
  margin-bottom: 8px;
}

.item-value {
  font-size: 16px;
  font-weight: 600;
  color: #1a1a1a;
}

.item-value.critical {
  color: #ff4d4f;
}

.item-value.high {
  color: #faad14;
}

.item-value.medium {
  color: #52c41a;
}

.charts-container {
  display: flex;
  justify-content: center;
  padding: 20px;
}

.chart-wrapper {
  text-align: center;
}

.chart-title {
  margin: 0 0 20px 0;
  font-size: 16px;
  color: #1a1a1a;
}

.pie-chart {
  width: 300px;
  height: 300px;
  border-radius: 50%;
  background: conic-gradient(
    #ff4d4f 0deg var(--critical-deg, 0deg),
    #faad14 var(--critical-deg, 0deg) var(--high-deg, 0deg),
    #52c41a var(--high-deg, 0deg) var(--medium-deg, 0deg),
    #1890ff var(--medium-deg, 0deg) 360deg
  );
  margin: 0 auto 20px;
  position: relative;
}

.pie-segment {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  border-radius: 50%;
}

.chart-legend {
  display: flex;
  justify-content: center;
  gap: 20px;
  flex-wrap: wrap;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: #1a1a1a;
}

.legend-color {
  width: 16px;
  height: 16px;
  border-radius: 4px;
}

.legend-item.critical .legend-color {
  background-color: #ff4d4f;
}

.legend-item.high .legend-color {
  background-color: #faad14;
}

.legend-item.medium .legend-color {
  background-color: #52c41a;
}

.legend-item.low .legend-color {
  background-color: #1890ff;
}

.vulnerabilities-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.vulnerability-card {
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  padding: 16px;
  transition: all 0.3s;
}

.vulnerability-card:hover {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.vuln-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.vuln-name {
  font-size: 16px;
  font-weight: 600;
  color: #1a1a1a;
}

.vuln-severity {
  padding: 4px 12px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 600;
}

.vuln-severity.critical {
  background-color: #fff1f0;
  color: #ff4d4f;
}

.vuln-severity.high {
  background-color: #fffbe6;
  color: #faad14;
}

.vuln-severity.medium {
  background-color: #f6ffed;
  color: #52c41a;
}

.vuln-severity.low {
  background-color: #e6f7ff;
  color: #1890ff;
}

.vuln-body {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.vuln-field {
  display: flex;
  gap: 8px;
  font-size: 14px;
}

.field-label {
  color: #666;
  min-width: 80px;
}

.field-value {
  color: #1a1a1a;
}

.vuln-description {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.description-text {
  margin: 0;
  color: #1a1a1a;
  line-height: 1.6;
}

.recommendations-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.recommendation-item {
  display: flex;
  gap: 16px;
  padding: 16px;
  background-color: #f9f9f9;
  border-radius: 6px;
}

.rec-number {
  flex-shrink: 0;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #1890ff;
  color: #ffffff;
  border-radius: 50%;
  font-weight: 600;
  font-size: 14px;
}

.rec-content {
  flex: 1;
}

.rec-title {
  margin: 0 0 8px 0;
  font-size: 16px;
  font-weight: 600;
  color: #1a1a1a;
}

.rec-description {
  margin: 0 0 8px 0;
  color: #666;
  line-height: 1.6;
}

.rec-priority {
  display: inline-block;
  padding: 4px 12px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 600;
}

.rec-priority.critical {
  background-color: #fff1f0;
  color: #ff4d4f;
}

.rec-priority.high {
  background-color: #fffbe6;
  color: #faad14;
}

.rec-priority.medium {
  background-color: #f6ffed;
  color: #52c41a;
}

.rec-priority.low {
  background-color: #e6f7ff;
  color: #1890ff;
}

.appendix-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.appendix-item {
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  padding: 16px;
}

.appendix-title {
  margin: 0 0 12px 0;
  font-size: 14px;
  font-weight: 600;
  color: #1a1a1a;
}

.appendix-code {
  margin: 0;
  padding: 12px;
  background-color: #f5f5f5;
  border-radius: 4px;
  font-family: 'Courier New', monospace;
  font-size: 12px;
  color: #1a1a1a;
  overflow-x: auto;
  white-space: pre-wrap;
  word-wrap: break-word;
}

.loading-state,
.error-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  background-color: #ffffff;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #f0f0f0;
  border-top-color: #1890ff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.loading-state p,
.error-state p {
  margin-top: 16px;
  color: #666;
  font-size: 14px;
}

.error-icon {
  font-size: 48px;
  margin-bottom: 16px;
}

.btn-retry {
  margin-top: 16px;
  padding: 8px 20px;
  background-color: #1890ff;
  color: #ffffff;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.3s;
}

.btn-retry:hover {
  background-color: #40a9ff;
}

@media print {
  .page-header,
  .btn-export,
  .btn-print {
    display: none;
  }

  .report-section {
    box-shadow: none;
    border: 1px solid #e0e0e0;
  }
}
</style>
