<template>
  <el-card :class="`stat-card stat-card-${type}`" shadow="hover">
    <div class="stat-content">
      <div class="stat-icon-wrapper">
        <el-icon :size="32" :color="iconColor">
          <component :is="iconComponent" />
        </el-icon>
      </div>
      <div class="stat-data">
        <div class="stat-number">{{ value }}</div>
        <div class="stat-label">{{ label }}</div>
      </div>
    </div>
  </el-card>
</template>

<script>
import { computed } from 'vue'
import { getIcon } from '@/utils/icons'

export default {
  name: 'StatCard',
  props: {
    icon: {
      type: String,
      required: true
    },
    value: {
      type: [Number, String],
      required: true
    },
    label: {
      type: String,
      required: true
    },
    type: {
      type: String,
      default: 'primary',
      validator: (value) => ['primary', 'danger', 'success', 'warning', 'trend', 'error', 'info', 'secondary'].includes(value)
    }
  },
  setup(props) {
    const iconColor = computed(() => {
      const colorMap = {
        primary: '#409EFF',
        danger: '#F56C6C',
        success: '#67C23A',
        warning: '#E6A23C',
        trend: '#909399',
        error: '#F56C6C',
        info: '#909399',
        secondary: '#409EFF'
      }
      return colorMap[props.type] || colorMap.primary
    })

    const iconComponent = computed(() => {
      return getIcon(props.icon)
    })

    return {
      iconColor,
      iconComponent
    }
  }
}
</script>

<style scoped>
.stat-card {
  margin-bottom: var(--spacing-lg);
}

.stat-card :deep(.el-card__body) {
  padding: var(--spacing-lg);
}

.stat-content {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
}

.stat-icon-wrapper {
  width: 56px;
  height: 56px;
  border-radius: var(--border-radius-lg);
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: var(--el-fill-color-light);
}

.stat-data {
  flex: 1;
}

.stat-number {
  font-size: 28px;
  font-weight: 700;
  color: var(--el-text-color-primary);
  line-height: 1;
  letter-spacing: 0.5px;
}

.stat-label {
  font-size: 14px;
  color: var(--el-text-color-secondary);
  margin-top: var(--spacing-xs);
  font-weight: 500;
  letter-spacing: 0.2px;
}

.stat-card-primary :deep(.el-card) {
  border-top: 3px solid var(--el-color-primary);
}

.stat-card-danger :deep(.el-card) {
  border-top: 3px solid var(--el-color-danger);
}

.stat-card-success :deep(.el-card) {
  border-top: 3px solid var(--el-color-success);
}

.stat-card-warning :deep(.el-card) {
  border-top: 3px solid var(--el-color-warning);
}

.stat-card-error :deep(.el-card) {
  border-top: 3px solid var(--el-color-danger);
}

.stat-card-info :deep(.el-card) {
  border-top: 3px solid var(--el-color-info);
}

.stat-card-secondary :deep(.el-card) {
  border-top: 3px solid var(--el-color-primary);
}

@media (max-width: 768px) {
  .stat-number {
    font-size: 24px;
  }

  .stat-label {
    font-size: 12px;
  }

  .stat-icon-wrapper {
    width: 48px;
    height: 48px;
  }
}
</style>
