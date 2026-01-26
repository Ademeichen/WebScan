<template>
  <div class="task-card" :class="`task-card-${task.status}`">
    <div class="task-header">
      <h3 class="task-title">{{ task.task_name }}</h3>
      <span class="task-status" :class="`status-${task.status}`">
        {{ statusText }}
      </span>
    </div>

    <div class="task-body">
      <div class="task-info">
        <div class="info-item">
          <span class="info-label">任务类型:</span>
          <span class="info-value">{{ taskTypeText }}</span>
        </div>
        <div class="info-item">
          <span class="info-label">目标:</span>
          <span class="info-value">{{ task.target }}</span>
        </div>
        <div class="info-item">
          <span class="info-label">创建时间:</span>
          <span class="info-value">{{ formatDate(task.created_at) }}</span>
        </div>
      </div>

      <div v-if="task.status === 'running' || task.status === 'pending'" class="task-progress">
        <div class="progress-bar">
          <div
            class="progress-fill"
            :style="{ width: `${task.progress || 0}%` }"
          ></div>
        </div>
        <span class="progress-text">{{ task.progress || 0 }}%</span>
      </div>

      <div v-if="task.result && task.result.vulnerabilities" class="task-stats">
        <div class="stat-item stat-critical">
          <span class="stat-count">{{ task.result.vulnerabilities.critical || 0 }}</span>
          <span class="stat-label">严重</span>
        </div>
        <div class="stat-item stat-high">
          <span class="stat-count">{{ task.result.vulnerabilities.high || 0 }}</span>
          <span class="stat-label">高危</span>
        </div>
        <div class="stat-item stat-medium">
          <span class="stat-count">{{ task.result.vulnerabilities.medium || 0 }}</span>
          <span class="stat-label">中危</span>
        </div>
        <div class="stat-item stat-low">
          <span class="stat-count">{{ task.result.vulnerabilities.low || 0 }}</span>
          <span class="stat-label">低危</span>
        </div>
        <div class="stat-item stat-info">
          <span class="stat-count">{{ task.result.vulnerabilities.info || 0 }}</span>
          <span class="stat-label">信息</span>
        </div>
      </div>
    </div>

    <div class="task-actions">
      <button
        v-if="task.status === 'running' || task.status === 'pending'"
        class="btn-action btn-cancel"
        @click="$emit('cancel', task.id)"
      >
        取消
      </button>
      <button
        v-if="task.status === 'completed' || task.status === 'failed'"
        class="btn-action btn-view"
        @click="$emit('view', task.id)"
      >
        查看详情
      </button>
      <button
        v-if="task.status === 'completed'"
        class="btn-action btn-report"
        @click="$emit('report', task.id)"
      >
        生成报告
      </button>
      <button
        class="btn-action btn-delete"
        @click="$emit('delete', task.id)"
      >
        删除
      </button>
    </div>
  </div>
</template>

<script>
import { computed } from 'vue'
import { formatDate } from '@/utils/date'

export default {
  name: 'TaskCard',
  props: {
    task: {
      type: Object,
      required: true
    }
  },
  emits: ['cancel', 'view', 'report', 'delete'],
  setup(props) {
    const statusText = computed(() => {
      const statusMap = {
        pending: '等待中',
        running: '运行中',
        completed: '已完成',
        failed: '失败',
        cancelled: '已取消'
      }
      return statusMap[props.task.status] || props.task.status
    })

    const taskTypeText = computed(() => {
      const typeMap = {
        awvs_scan: 'AWVS扫描',
        poc_scan: 'POC扫描',
        scan_dir: '目录扫描',
        scan_webside: '网站扫描',
        scan_port: '端口扫描',
        scan_cms: 'CMS识别',
        scan_comprehensive: '综合扫描'
      }
      return typeMap[props.task.task_type] || props.task.task_type
    })

    return {
      statusText,
      taskTypeText,
      formatDate
    }
  }
}
</script>

<style scoped>
.task-card {
  background-color: var(--card-bg);
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius-lg);
  padding: var(--spacing-lg);
  margin-bottom: var(--spacing-md);
  transition: all 0.3s;
}

.task-card:hover {
  box-shadow: var(--shadow-md);
  transform: translateY(-2px);
}

.task-card-running {
  border-left: 4px solid var(--color-info);
}

.task-card-completed {
  border-left: 4px solid var(--color-success);
}

.task-card-failed {
  border-left: 4px solid var(--color-error);
}

.task-card-pending {
  border-left: 4px solid var(--color-warning);
}

.task-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-md);
}

.task-title {
  margin: 0;
  font-size: 1.125rem;
  font-weight: 600;
  color: var(--text-primary);
}

.task-status {
  padding: var(--spacing-xs) var(--spacing-sm);
  border-radius: var(--border-radius-sm);
  font-size: 0.875rem;
  font-weight: 500;
}

.status-pending {
  background-color: var(--color-warning-bg);
  color: var(--color-warning);
}

.status-running {
  background-color: var(--color-info-bg);
  color: var(--color-info);
}

.status-completed {
  background-color: var(--color-success-bg);
  color: var(--color-success);
}

.status-failed,
.status-cancelled {
  background-color: var(--color-error-bg);
  color: var(--color-error);
}

.task-body {
  margin-bottom: var(--spacing-md);
}

.task-info {
  margin-bottom: var(--spacing-md);
}

.info-item {
  display: flex;
  margin-bottom: var(--spacing-sm);
  font-size: 0.875rem;
}

.info-label {
  width: 80px;
  color: var(--text-secondary);
  font-weight: 500;
}

.info-value {
  flex: 1;
  color: var(--text-primary);
  word-break: break-all;
}

.task-progress {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  margin-bottom: var(--spacing-md);
}

.progress-bar {
  flex: 1;
  height: 8px;
  background-color: var(--border-color);
  border-radius: 4px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background-color: var(--color-primary);
  transition: width 0.3s;
}

.progress-text {
  min-width: 40px;
  font-size: 0.875rem;
  color: var(--text-secondary);
  text-align: right;
}

.task-stats {
  display: flex;
  gap: var(--spacing-sm);
  margin-bottom: var(--spacing-md);
}

.stat-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: var(--spacing-sm);
  border-radius: var(--border-radius);
  background-color: var(--bg-secondary);
}

.stat-count {
  font-size: 1.5rem;
  font-weight: 700;
  line-height: 1;
}

.stat-label {
  font-size: 0.75rem;
  color: var(--text-secondary);
  margin-top: var(--spacing-xs);
}

.stat-critical .stat-count {
  color: var(--color-critical);
}

.stat-high .stat-count {
  color: var(--color-error);
}

.stat-medium .stat-count {
  color: var(--color-warning);
}

.stat-low .stat-count {
  color: var(--color-info);
}

.stat-info .stat-count {
  color: var(--color-success);
}

.task-actions {
  display: flex;
  gap: var(--spacing-sm);
  flex-wrap: wrap;
}

.btn-action {
  padding: var(--spacing-sm) var(--spacing-md);
  border: none;
  border-radius: var(--border-radius);
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s;
}

.btn-view {
  background-color: var(--color-primary);
  color: white;
}

.btn-view:hover {
  background-color: var(--color-primary-dark);
}

.btn-report {
  background-color: var(--color-success);
  color: white;
}

.btn-report:hover {
  background-color: var(--color-success-dark);
}

.btn-cancel {
  background-color: var(--color-warning);
  color: white;
}

.btn-cancel:hover {
  background-color: var(--color-warning-dark);
}

.btn-delete {
  background-color: var(--color-error);
  color: white;
}

.btn-delete:hover {
  background-color: var(--color-error-dark);
}
</style>
