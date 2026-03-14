<template>
  <div class="ai-analysis-display">
    <el-card v-if="loading" class="loading-card">
      <div class="loading-content">
        <el-icon class="is-loading" :size="32"><Loading /></el-icon>
        <span>正在分析中...</span>
      </div>
    </el-card>

    <template v-else-if="analysisData">
      <el-card class="analysis-card">
        <template #header>
          <div class="card-header">
            <span class="title">
              <el-icon><Cpu /></el-icon>
              AI 分析结果
            </span>
            <el-tag :type="getConfidenceType(analysisData.confidence)">
              置信度: {{ (analysisData.confidence * 100).toFixed(1) }}%
            </el-tag>
          </div>
        </template>

        <el-tabs v-model="activeTab">
          <el-tab-pane label="漏洞成因" name="causes">
            <div class="section-content">
              <div v-for="(cause, index) in analysisData.vulnerability_causes" :key="index" class="cause-item">
                <div class="cause-header">
                  <el-icon class="cause-icon" color="#E6A23C"><WarningFilled /></el-icon>
                  <span class="cause-title">{{ cause.description || cause }}</span>
                </div>
                <div v-if="cause.evidence" class="cause-evidence">
                  <span class="label">证据:</span>
                  <ul>
                    <li v-for="(ev, i) in cause.evidence" :key="i">{{ ev }}</li>
                  </ul>
                </div>
                <div v-if="cause.confidence" class="cause-confidence">
                  <el-progress :percentage="cause.confidence * 100" :stroke-width="6" />
                </div>
              </div>
              <el-empty v-if="!analysisData.vulnerability_causes?.length" description="暂无漏洞成因分析" />
            </div>
          </el-tab-pane>

          <el-tab-pane label="利用风险" name="risks">
            <div class="section-content">
              <div v-for="(risk, index) in analysisData.exploitation_risks" :key="index" class="risk-item">
                <div class="risk-header">
                  <el-tag :type="getRiskLevelType(risk.risk_level || risk.level)" size="small">
                    {{ risk.risk_level || risk.level || '未知' }}
                  </el-tag>
                  <span class="risk-title">{{ risk.description }}</span>
                </div>
                <div v-if="risk.likelihood || risk.impact" class="risk-details">
                  <span v-if="risk.likelihood">可能性: {{ (risk.likelihood * 100).toFixed(0) }}%</span>
                  <span v-if="risk.impact">影响程度: {{ risk.impact }}</span>
                </div>
              </div>
              <el-empty v-if="!analysisData.exploitation_risks?.length" description="暂无利用风险分析" />
            </div>
          </el-tab-pane>

          <el-tab-pane label="修复优先级" name="priorities">
            <div class="section-content">
              <el-table :data="analysisData.remediation_priorities" stripe>
                <el-table-column label="优先级" width="80" align="center">
                  <template #default="{ row }">
                    <el-tag :type="getPriorityType(row.priority)" size="small">
                      P{{ row.priority }}
                    </el-tag>
                  </template>
                </el-table-column>
                <el-table-column label="漏洞名称" prop="vulnerability" min-width="150" />
                <el-table-column label="修复原因" prop="reason" min-width="200" />
                <el-table-column label="预估工作量" prop="estimated_effort" width="100" />
              </el-table>
              <el-empty v-if="!analysisData.remediation_priorities?.length" description="暂无修复优先级建议" />
            </div>
          </el-tab-pane>

          <el-tab-pane label="业务影响" name="impact">
            <div class="section-content">
              <div class="impact-grid">
                <div class="impact-item">
                  <span class="impact-label">受影响系统</span>
                  <div class="impact-value">
                    <el-tag v-for="sys in getArrayValue(analysisData.business_impact?.affected_systems)" :key="sys" class="mr-1">
                      {{ sys }}
                    </el-tag>
                    <span v-if="!getArrayValue(analysisData.business_impact?.affected_systems).length">-</span>
                  </div>
                </div>
                <div class="impact-item">
                  <span class="impact-label">数据风险</span>
                  <span class="impact-value">{{ analysisData.business_impact?.data_risk || '-' }}</span>
                </div>
                <div class="impact-item">
                  <span class="impact-label">停机风险</span>
                  <span class="impact-value">{{ analysisData.business_impact?.downtime_risk || '-' }}</span>
                </div>
                <div class="impact-item">
                  <span class="impact-label">合规风险</span>
                  <span class="impact-value">{{ analysisData.business_impact?.compliance_risk || '-' }}</span>
                </div>
                <div class="impact-item">
                  <span class="impact-label">财务影响</span>
                  <span class="impact-value">{{ analysisData.business_impact?.financial_impact || '-' }}</span>
                </div>
              </div>
              <el-empty v-if="!analysisData.business_impact" description="暂无业务影响分析" />
            </div>
          </el-tab-pane>

          <el-tab-pane label="分析依据" name="evidence">
            <div class="section-content">
              <ul class="evidence-list">
                <li v-for="(ev, index) in analysisData.analysis_evidence" :key="index">
                  {{ ev }}
                </li>
              </ul>
              <el-empty v-if="!analysisData.analysis_evidence?.length" description="暂无分析依据" />
            </div>
          </el-tab-pane>
        </el-tabs>
      </el-card>
    </template>

    <el-empty v-else description="暂无AI分析结果" />
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { Loading, Cpu, WarningFilled } from '@element-plus/icons-vue'

const props = defineProps({
  analysisData: {
    type: Object,
    default: null
  },
  loading: {
    type: Boolean,
    default: false
  }
})

const activeTab = ref('causes')

const getConfidenceType = (confidence) => {
  if (!confidence) return 'info'
  if (confidence >= 0.8) return 'success'
  if (confidence >= 0.6) return 'warning'
  return 'danger'
}

const getRiskLevelType = (level) => {
  const levelMap = {
    'critical': 'danger',
    'high': 'danger',
    'medium': 'warning',
    'low': 'success',
    'info': 'info'
  }
  return levelMap[level?.toLowerCase()] || 'info'
}

const getPriorityType = (priority) => {
  if (priority <= 1) return 'danger'
  if (priority <= 3) return 'warning'
  return 'success'
}

const getArrayValue = (value) => {
  if (Array.isArray(value)) return value
  if (typeof value === 'string') return [value]
  return []
}
</script>

<style scoped>
.ai-analysis-display {
  width: 100%;
}

.loading-card {
  min-height: 200px;
}

.loading-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 150px;
  gap: 16px;
}

.analysis-card {
  margin-bottom: 16px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-header .title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
}

.section-content {
  padding: 16px;
  min-height: 200px;
}

.cause-item, .risk-item {
  padding: 12px;
  margin-bottom: 12px;
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  background: #fafafa;
}

.cause-header, .risk-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.cause-icon {
  font-size: 18px;
}

.cause-title, .risk-title {
  font-weight: 500;
}

.cause-evidence {
  margin-left: 26px;
  font-size: 13px;
  color: #606266;
}

.cause-evidence .label {
  font-weight: 500;
  margin-right: 8px;
}

.cause-evidence ul {
  margin: 4px 0 0 16px;
  padding: 0;
}

.cause-confidence {
  margin-top: 8px;
  margin-left: 26px;
}

.risk-details {
  display: flex;
  gap: 16px;
  font-size: 13px;
  color: #606266;
  margin-left: 8px;
}

.impact-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
}

.impact-item {
  padding: 12px;
  border: 1px solid #e4e7ed;
  border-radius: 4px;
}

.impact-label {
  display: block;
  font-size: 13px;
  color: #909399;
  margin-bottom: 8px;
}

.impact-value {
  font-weight: 500;
}

.evidence-list {
  margin: 0;
  padding-left: 20px;
}

.evidence-list li {
  margin-bottom: 8px;
  line-height: 1.6;
}

.mr-1 {
  margin-right: 4px;
}
</style>
