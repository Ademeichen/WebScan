<template>
  <div class="execution-details-display">
    <el-card v-if="loading" class="loading-card">
      <div class="loading-content">
        <el-icon class="is-loading" :size="32"><Loading /></el-icon>
        <span>加载执行详情...</span>
      </div>
    </el-card>

    <template v-else-if="executionData">
      <el-card class="summary-card">
        <template #header>
          <div class="card-header">
            <span class="title">
              <el-icon><DataLine /></el-icon>
              执行概览
            </span>
            <el-tag :type="getStatusType(executionData.status)">
              {{ getStatusLabel(executionData.status) }}
            </el-tag>
          </div>
        </template>

        <el-row :gutter="20">
          <el-col :span="6">
            <div class="stat-item">
              <span class="stat-value">{{ executionData.progress || 0 }}%</span>
              <span class="stat-label">进度</span>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="stat-item">
              <span class="stat-value">{{ executionData.execution_history?.length || 0 }}</span>
              <span class="stat-label">执行步骤</span>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="stat-item">
              <span class="stat-value">{{ formatDuration(executionData.duration) }}</span>
              <span class="stat-label">总耗时</span>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="stat-item">
              <span class="stat-value">{{ executionData.target || '-' }}</span>
              <span class="stat-label">扫描目标</span>
            </div>
          </el-col>
        </el-row>
      </el-card>

      <el-card class="timeline-card">
        <template #header>
          <div class="card-header">
            <span class="title">
              <el-icon><Clock /></el-icon>
              执行时间线
            </span>
          </div>
        </template>

        <el-timeline>
          <el-timeline-item
            v-for="(step, index) in executionData.execution_history"
            :key="index"
            :type="getStepType(step.status)"
            :timestamp="formatTimestamp(step.timestamp || step.timestamp_iso)"
            placement="top"
          >
            <el-card class="step-card">
              <div class="step-header">
                <span class="step-number">步骤 {{ step.step_number || index + 1 }}</span>
                <el-tag :type="getStatusType(step.status)" size="small">
                  {{ getStatusLabel(step.status) }}
                </el-tag>
              </div>
              <div class="step-content">
                <div class="step-info">
                  <span class="step-task">{{ step.task || step.tool_name || '未知任务' }}</span>
                  <span v-if="step.execution_time" class="step-time">
                    耗时: {{ step.execution_time.toFixed(2) }}s
                  </span>
                </div>
                <div v-if="step.input_params" class="step-params">
                  <span class="label">输入参数:</span>
                  <pre>{{ JSON.stringify(step.input_params, null, 2) }}</pre>
                </div>
                <div v-if="step.output_data" class="step-output">
                  <span class="label">输出数据:</span>
                  <pre>{{ JSON.stringify(step.output_data, null, 2) }}</pre>
                </div>
                <div v-if="step.error" class="step-error">
                  <el-icon color="#F56C6C"><CircleCloseFilled /></el-icon>
                  <span>{{ step.error }}</span>
                </div>
              </div>
            </el-card>
          </el-timeline-item>
        </el-timeline>

        <el-empty v-if="!executionData.execution_history?.length" description="暂无执行记录" />
      </el-card>

      <el-card v-if="executionData.graph_flow" class="graph-card">
        <template #header>
          <div class="card-header">
            <span class="title">
              <el-icon><Share /></el-icon>
              图流程结构
            </span>
          </div>
        </template>

        <div class="graph-flow">
          <div v-for="(subgraph, index) in executionData.graph_flow?.subgraphs" :key="index" class="subgraph-item">
            <div class="subgraph-header">
              <el-icon><FolderOpened /></el-icon>
              <span>{{ subgraph.subgraph_name || `子图 ${subgraph.subgraph_id}` }}</span>
            </div>
            <div class="nodes-list">
              <div v-for="node in subgraph.nodes" :key="node.node_id" class="node-item">
                <el-tag :type="getStatusType(node.status)" size="small">
                  {{ node.status || 'pending' }}
                </el-tag>
                <span class="node-name">{{ node.node_name || node.node_id }}</span>
              </div>
            </div>
          </div>
        </div>

        <el-empty v-if="!executionData.graph_flow?.subgraphs?.length" description="暂无图流程数据" />
      </el-card>
    </template>

    <el-empty v-else description="暂无执行详情" />
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { Loading, DataLine, Clock, Share, FolderOpened, CircleCloseFilled } from '@element-plus/icons-vue'

const props = defineProps({
  executionData: {
    type: Object,
    default: null
  },
  loading: {
    type: Boolean,
    default: false
  }
})

const getStatusType = (status) => {
  const statusMap = {
    'success': 'success',
    'completed': 'success',
    'running': 'primary',
    'pending': 'info',
    'failed': 'danger',
    'error': 'danger',
    'cancelled': 'warning'
  }
  return statusMap[status?.toLowerCase()] || 'info'
}

const getStatusLabel = (status) => {
  const labelMap = {
    'success': '成功',
    'completed': '已完成',
    'running': '运行中',
    'pending': '等待中',
    'failed': '失败',
    'error': '错误',
    'cancelled': '已取消'
  }
  return labelMap[status?.toLowerCase()] || status || '未知'
}

const getStepType = (status) => {
  const typeMap = {
    'success': 'success',
    'completed': 'success',
    'running': 'primary',
    'pending': 'info',
    'failed': 'danger',
    'error': 'danger'
  }
  return typeMap[status?.toLowerCase()] || 'info'
}

const formatTimestamp = (timestamp) => {
  if (!timestamp) return '-'
  try {
    const date = new Date(timestamp)
    return date.toLocaleString('zh-CN')
  } catch {
    return timestamp
  }
}

const formatDuration = (seconds) => {
  if (!seconds) return '-'
  if (seconds < 60) return `${seconds.toFixed(1)}s`
  const minutes = Math.floor(seconds / 60)
  const secs = (seconds % 60).toFixed(0)
  return `${minutes}m ${secs}s`
}
</script>

<style scoped>
.execution-details-display {
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

.summary-card, .timeline-card, .graph-card {
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

.stat-item {
  text-align: center;
  padding: 12px;
}

.stat-value {
  display: block;
  font-size: 24px;
  font-weight: 600;
  color: #303133;
}

.stat-label {
  display: block;
  font-size: 13px;
  color: #909399;
  margin-top: 4px;
}

.step-card {
  margin-bottom: 0;
}

.step-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.step-number {
  font-weight: 600;
  color: #303133;
}

.step-content {
  font-size: 14px;
}

.step-info {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
}

.step-task {
  font-weight: 500;
}

.step-time {
  color: #909399;
  font-size: 13px;
}

.step-params, .step-output {
  margin-top: 8px;
  padding: 8px;
  background: #f5f7fa;
  border-radius: 4px;
}

.step-params .label, .step-output .label {
  display: block;
  font-size: 12px;
  color: #909399;
  margin-bottom: 4px;
}

.step-params pre, .step-output pre {
  margin: 0;
  font-size: 12px;
  white-space: pre-wrap;
  word-break: break-all;
}

.step-error {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 8px;
  padding: 8px;
  background: #fef0f0;
  border-radius: 4px;
  color: #F56C6C;
}

.graph-flow {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.subgraph-item {
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  padding: 12px;
}

.subgraph-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 1px solid #e4e7ed;
}

.nodes-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.node-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 12px;
  background: #f5f7fa;
  border-radius: 4px;
}

.node-name {
  font-size: 13px;
}
</style>
