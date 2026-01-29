<template>
  <Teleport to="body">
    <Transition name="toast">
      <div v-if="visible" :class="['toast', `toast-${type}`]" @click="handleClose">
        <div class="toast-content" @click.stop>
          <div class="toast-icon">{{ icon }}</div>
          <div class="toast-message">
            <div class="toast-title">{{ title }}</div>
            <div v-if="message" class="toast-body">{{ message }}</div>
          </div>
          <button v-if="closable" @click="handleClose" class="toast-close" type="button">×</button>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script>
import { ref, computed, onMounted, onUnmounted } from 'vue'

export default {
  name: 'Toast',
  props: {
    visible: {
      type: Boolean,
      default: false
    },
    type: {
      type: String,
      default: 'info',
      validator: (value) => ['success', 'error', 'warning', 'info'].includes(value)
    },
    title: {
      type: String,
      default: ''
    },
    message: {
      type: String,
      default: ''
    },
    duration: {
      type: Number,
      default: 3000
    },
    closable: {
      type: Boolean,
      default: true
    }
  },
  emits: ['close'],
  setup(props, { emit }) {
    const timer = ref(null)

    const icon = computed(() => {
      const icons = {
        success: '✓',
        error: '✕',
        warning: '⚠',
        info: 'ℹ'
      }
      return icons[props.type] || icons.info
    })

    const handleClose = () => {
      emit('close')
    }

    const startTimer = () => {
      if (props.duration > 0) {
        timer.value = setTimeout(() => {
          handleClose()
        }, props.duration)
      }
    }

    const clearTimer = () => {
      if (timer.value) {
        clearTimeout(timer.value)
        timer.value = null
      }
    }

    onMounted(() => {
      startTimer()
    })

    onUnmounted(() => {
      clearTimer()
    })

    return {
      icon,
      handleClose
    }
  }
}
</script>

<style scoped>
.toast {
  position: fixed;
  top: 20px;
  right: 20px;
  z-index: 10000;
  min-width: 300px;
  max-width: 500px;
}

.toast-content {
  position: relative;
  background: white;
  border-radius: var(--border-radius-lg);
  box-shadow: var(--shadow-xl);
  padding: var(--spacing-lg);
  display: flex;
  gap: var(--spacing-md);
  align-items: flex-start;
}

.toast-icon {
  font-size: 24px;
  font-weight: bold;
  flex-shrink: 0;
}

.toast-message {
  flex: 1;
}

.toast-title {
  font-weight: 600;
  font-size: 16px;
  margin-bottom: var(--spacing-xs);
}

.toast-body {
  font-size: 14px;
  color: var(--text-secondary);
  line-height: 1.5;
}

.toast-close {
  position: absolute;
  top: var(--spacing-sm);
  right: var(--spacing-sm);
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: var(--text-secondary);
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  transition: all var(--transition-fast);
}

.toast-close:hover {
  background-color: var(--background-color);
  color: var(--text-primary);
}

.toast-success .toast-content {
  border-left: 4px solid var(--success-color);
}

.toast-success .toast-icon {
  color: var(--success-color);
}

.toast-error .toast-content {
  border-left: 4px solid var(--danger-color);
}

.toast-error .toast-icon {
  color: var(--danger-color);
}

.toast-warning .toast-content {
  border-left: 4px solid var(--warning-color);
}

.toast-warning .toast-icon {
  color: var(--warning-color);
}

.toast-info .toast-content {
  border-left: 4px solid var(--info-color);
}

.toast-info .toast-icon {
  color: var(--info-color);
}

.toast-enter-active,
.toast-leave-active {
  transition: all var(--transition-base);
}

.toast-enter-from {
  opacity: 0;
  transform: translateX(100%);
}

.toast-leave-to {
  opacity: 0;
  transform: translateX(100%);
}

@media (max-width: 768px) {
  .toast {
    top: 10px;
    right: 10px;
    left: 10px;
    min-width: auto;
    max-width: none;
  }
  
  .toast-content {
    padding: var(--spacing-md);
  }
  
  .toast-icon {
    font-size: 20px;
  }
  
  .toast-title {
    font-size: 14px;
  }
  
  .toast-body {
    font-size: 12px;
  }
}
</style>
