<template>
  <el-card :class="`task-card task-card-${task.status}`" shadow="hover">
    <div class="task-header">
      <h3 class="task-title">{{ task.task_name }}</h3>
      <el-tag :type="statusType" size="small">
        {{ statusText }}
      </el-tag>
    </div>

    <div class="task-body">
      <el-descriptions :column="1" border>
        <el-descriptions-item label="任务类型">
          {{ taskTypeText }}
        </el-descriptions-item>
        <el-descriptions-item label="目标">
          <el-text truncated>{{ task.target }}</el-text>
        </el-descriptions-item>
        <el-descriptions-item label="创建时间">
          {{ formatDate(task.created_at) }}
        </el-descriptions-item>
      </el-descriptions>

      <div v-if="task.status === 'running' || task.status === 'pending'" class="task-progress">
        <el-progress
          :percentage="safeProgress"
          :stroke-width="10"
          :show-text="true"
        />
      </div>

      <div v-if="task.result && task.result.vulnerabilities" class="task-stats">
        <el-statistic
          title="严重"
          :value="task.result.vulnerabilities.critical || 0"
          class="stat-critical"
        >
          <template #suffix>
            <span class="stat-label">严重</span>
          </template>
        </el-statistic>
        <el-statistic
          title="高危"
          :value="task.result.vulnerabilities.high || 0"
          class="stat-high"
        >
          <template #suffix>
            <span class="stat-label">高危</span>
          </template>
        </el-statistic>
        <el-statistic
          title="中危"
          :value="task.result.vulnerabilities.medium || 0"
          class="stat-medium"
        >
          <template #suffix>
            <span class="stat-label">中危</span>
          </template>
        </el-statistic>
        <el-statistic
          title="低危"
          :value="task.result.vulnerabilities.low || 0"
          class="stat-low"
        >
          <template #suffix>
            <span class="stat-label">低危</span>
          </template>
        </el-statistic>
        <el-statistic
          title="信息"
          :value="task.result.vulnerabilities.info || 0"
          class="stat-info"
        >
          <template #suffix>
            <span class="stat-label">信息</span>
          </template>
        </el-statistic>
      </div>
    </div>

    <div class="task-actions">
      <el-button
        v-if="task.status === 'running' || task.status === 'pending'"
        type="warning"
        @click="$emit('cancel', task.id)"
      >
        <AppIcon name="Close" :size="16" />
        <span>取消</span>
      </el-button>
      <el-button
        v-if="task.status === 'completed' || task.status === 'failed'"
        type="info"
        @click="$emit('view', task.id)"
      >
        <AppIcon name="View" :size="16" />
        <span>查看详情</span>
      </el-button>
      <el-button
        v-if="task.status === 'completed'"
        type="success"
        @click="$emit('report', task.id)"
      >
        <AppIcon name="Document" :size="16" />
        <span>生成报告</span>
      </el-button>
      <el-button
        type="danger"
        @click="$emit('delete', task.id)"
      >
        <AppIcon name="Delete" :size="16" />
        <span>删除</span>
      </el-button>
    </div>
  </el-card>
</template>

<script>
import { computed } from 'vue'
import { formatDate } from '@/utils/date'
import AppIcon from '@/components/common/AppIcon.vue'

export default {
  name: 'TaskCard',
  components: {
    AppIcon
  },
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

    const statusType = computed(() => {
      const typeMap = {
        pending: 'info',
        running: 'primary',
        completed: 'success',
        failed: 'danger',
        cancelled: 'warning'
      }
      return typeMap[props.task.status] || 'info'
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

    const safeProgress = computed(() => {
      let progress = props.task.progress
      if (progress == null || progress === undefined || isNaN(progress)) {
        return 0
      }
      progress = Number(progress)
      if (progress < 0) return 0
      if (progress > 100) return 100
      return Math.round(progress)
    })

    return {
      statusText,
      statusType,
      taskTypeText,
      formatDate,
      safeProgress
    }
  }
}
</script>

<style scoped>
.task-card {
  margin-bottom: var(--spacing-md);
}

.task-card-running :deep(.el-card__body) {
  border-left: 4px solid var(--el-color-info);
}

.task-card-completed :deep(.el-card__body) {
  border-left: 4px solid var(--el-color-success);
}

.task-card-failed :deep(.el-card__body) {
  border-left: 4px solid var(--el-color-danger);
}

.task-card-pending :deep(.el-card__body) {
  border-left: 4px solid var(--el-color-warning);
}

.task-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-md);
}

.task-title {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.task-body {
  margin-bottom: var(--spacing-md);
}

.task-progress {
  margin-bottom: var(--spacing-md);
}

.task-stats {
  display: flex;
  gap: var(--spacing-sm);
  margin-bottom: var(--spacing-md);
}

.task-stats :deep(.el-statistic) {
  flex: 1;
}

.task-stats :deep(.el-statistic__content) {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.stat-critical :deep(.el-statistic__number) {
  color: var(--critical-risk);
}

.stat-high :deep(.el-statistic__number) {
  color: var(--high-risk);
}

.stat-medium :deep(.el-statistic__number) {
  color: var(--medium-risk);
}

.stat-low :deep(.el-statistic__number) {
  color: var(--low-risk);
}

.stat-info :deep(.el-statistic__number) {
  color: var(--info-risk);
}

.stat-label {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  margin-left: var(--spacing-xs);
}

.task-actions {
  display: flex;
  gap: var(--spacing-sm);
  flex-wrap: wrap;
}

@media (max-width: 768px) {
  .task-stats {
    flex-wrap: wrap;
  }

  .task-actions {
    flex-direction: column;
    width: 100%;
  }

  .task-actions :deep(.el-button) {
    width: 100%;
  }
}
</style>
