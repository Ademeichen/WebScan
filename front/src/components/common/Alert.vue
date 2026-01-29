<template>
  <div v-if="show" class="alert" :class="`alert-${type}`">
    <span class="alert-icon">{{ icon }}</span>
    <span class="alert-message">{{ message }}</span>
    <button v-if="dismissible" @click="close" class="alert-close">×</button>
  </div>
</template>

<script>
export default {
  name: 'Alert',
  props: {
    type: {
      type: String,
      default: 'info',
      validator: (value) => ['success', 'error', 'warning', 'info'].includes(value)
    },
    message: {
      type: String,
      required: true
    },
    dismissible: {
      type: Boolean,
      default: true
    },
    duration: {
      type: Number,
      default: 3000
    }
  },
  data() {
    return {
      show: true
    }
  },
  computed: {
    icon() {
      const icons = {
        success: '✅',
        error: '❌',
        warning: '⚠️',
        info: 'ℹ️'
      }
      return icons[this.type]
    }
  },
  mounted() {
    if (this.duration > 0) {
      setTimeout(() => {
        this.close()
      }, this.duration)
    }
  },
  methods: {
    close() {
      this.show = false
      this.$emit('close')
    }
  }
}
</script>

<style scoped>
.alert {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  padding: var(--spacing-md) var(--spacing-lg);
  border-radius: var(--border-radius);
  margin-bottom: var(--spacing-md);
  animation: slideIn 0.3s ease;
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.alert-icon {
  font-size: 1.25rem;
}

.alert-message {
  flex: 1;
}

.alert-close {
  background: none;
  border: none;
  font-size: 1.5rem;
  cursor: pointer;
  color: var(--text-secondary);
  padding: 0;
  line-height: 1;
}

.alert-close:hover {
  color: var(--text-primary);
}

.alert-success {
  background-color: var(--color-success-bg);
  color: var(--color-success);
  border-left: 4px solid var(--color-success);
}

.alert-error {
  background-color: var(--color-error-bg);
  color: var(--color-error);
  border-left: 4px solid var(--color-error);
}

.alert-warning {
  background-color: var(--color-warning-bg);
  color: var(--color-warning);
  border-left: 4px solid var(--color-warning);
}

.alert-info {
  background-color: var(--color-info-bg);
  color: var(--color-info);
  border-left: 4px solid var(--color-info);
}
</style>
