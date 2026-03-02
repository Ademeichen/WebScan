<template>
  <transition name="alert-fade">
    <div v-if="visible" class="alert-wrapper" :class="[`alert-${type}`, { 'alert-with-retry': showRetry }]">
      <div class="alert-content">
        <div class="alert-icon">
          <svg v-if="type === 'success'" viewBox="0 0 1024 1024" xmlns="http://www.w3.org/2000/svg">
            <path fill="currentColor" d="M512 896a384 384 0 1 0 0-768 384 384 0 0 0 0 768zm0 64a448 448 0 1 1 0-896 448 448 0 0 1 0 896zM728.576 345.6a32 32 0 0 1 0 45.248L490.24 629.248a32 32 0 0 1-45.248 0L295.424 479.744a32 32 0 0 1 45.248-45.248L467.584 561.344l215.744-215.744a32 32 0 0 1 45.248 0z"/>
          </svg>
          <svg v-else-if="type === 'error'" viewBox="0 0 1024 1024" xmlns="http://www.w3.org/2000/svg">
            <path fill="currentColor" d="M512 896a384 384 0 1 0 0-768 384 384 0 0 0 0 768zm0 64a448 448 0 1 1 0-896 448 448 0 0 1 0 896zM354.752 354.752a32 32 0 0 1 45.248 0L512 466.752l111.744-111.744a32 32 0 1 1 45.248 45.248L557.248 512l111.744 111.744a32 32 0 1 1-45.248 45.248L512 557.248 400.256 669.248a32 32 0 1 1-45.248-45.248L466.752 512 354.752 400.256a32 32 0 0 1 0-45.248z"/>
          </svg>
          <svg v-else-if="type === 'warning'" viewBox="0 0 1024 1024" xmlns="http://www.w3.org/2000/svg">
            <path fill="currentColor" d="M512 896a384 384 0 1 0 0-768 384 384 0 0 0 0 768zm0 64a448 448 0 1 1 0-896 448 448 0 0 1 0 896zM480 256a32 32 0 0 1 64 0v320a32 32 0 0 1-64 0V256zm32 448a32 32 0 1 1 0-64 32 32 0 0 1 0 64z"/>
          </svg>
          <svg v-else-if="type === 'info'" viewBox="0 0 1024 1024" xmlns="http://www.w3.org/2000/svg">
            <path fill="currentColor" d="M512 896a384 384 0 1 0 0-768 384 384 0 0 0 0 768zm0 64a448 448 0 1 1 0-896 448 448 0 0 1 0 896zM480 256a32 32 0 0 1 64 0v320a32 32 0 0 1-64 0V256zm32 448a32 32 0 1 1 0-64 32 32 0 0 1 0 64z"/>
          </svg>
          <svg v-else-if="type === 'loading'" viewBox="0 0 1024 1024" xmlns="http://www.w3.org/2000/svg">
            <path fill="currentColor" d="M512 64a32 32 0 0 1 32 32v192a32 32 0 0 1-64 0V96a32 32 0 0 1 32-32zm0 640a32 32 0 0 1 32 32v192a32 32 0 0 1-64 0V736a32 32 0 0 1 32-32zm448-192a32 32 0 0 1-32 32H736a32 32 0 0 1 0-64h192a32 32 0 0 1 32 32zm-640 0a32 32 0 0 1-32 32H96a32 32 0 0 1 0-64h192a32 32 0 0 1 32 32zM195.2 195.2a32 32 0 0 1 45.248 0L376.32 331.008a32 32 0 0 1-45.248 45.248L195.2 240.448a32 32 0 0 1 0-45.248zm452.544 452.544a32 32 0 0 1 45.248 0L828.8 783.552a32 32 0 0 1-45.248 45.248L647.744 692.992a32 32 0 0 1 0-45.248zM828.8 195.2a32 32 0 0 1 0 45.248L692.992 376.32a32 32 0 0 1-45.248-45.248L783.552 195.2a32 32 0 0 1 45.248 0zM376.32 647.744a32 32 0 0 1 0 45.248L240.448 828.8a32 32 0 0 1-45.248-45.248l135.808-135.808a32 32 0 0 1 45.248 0z"/>
          </svg>
        </div>
        <div class="alert-message">
          <span class="alert-title">{{ message }}</span>
          <span v-if="retryInfo" class="alert-retry-info">{{ retryInfo }}</span>
        </div>
        <div class="alert-actions">
          <button v-if="showRetry" class="alert-retry-btn" @click="handleRetry">
            <svg viewBox="0 0 1024 1024" xmlns="http://www.w3.org/2000/svg">
              <path fill="currentColor" d="M784.512 230.272v-50.56a32 32 0 1 1 64 0v149.056a32 32 0 0 1-32 32H667.52a32 32 0 1 1 0-64h92.992A320 320 0 1 0 524.8 833.152a320 320 0 0 0 320-320h64a384 384 0 0 1-384 384 384 384 0 0 1-384-384 384 384 0 0 1 643.712-282.88z"/>
            </svg>
            重试
          </button>
          <button v-if="dismissible" class="alert-close-btn" @click="close">
            <svg viewBox="0 0 1024 1024" xmlns="http://www.w3.org/2000/svg">
              <path fill="currentColor" d="M764.288 214.592 512 466.88 259.712 214.592a32 32 0 0 0-45.248 45.248L466.752 512 214.528 764.224a32 32 0 1 0 45.248 45.248L512 557.248l252.288 252.288a32 32 0 0 0 45.248-45.248L557.248 512l252.288-252.288a32 32 0 0 0-45.248-45.12z"/>
            </svg>
          </button>
        </div>
      </div>
      <div v-if="autoClose && duration > 0" class="alert-progress">
        <div class="alert-progress-bar" :style="{ animationDuration: `${duration}ms` }"></div>
      </div>
    </div>
  </transition>
</template>

<script>
import { ref, onMounted, onUnmounted, watch } from 'vue'

export default {
  name: 'Alert',
  props: {
    type: {
      type: String,
      default: 'info',
      validator: (value) => ['success', 'error', 'warning', 'info', 'loading'].includes(value)
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
      default: 5000
    },
    autoClose: {
      type: Boolean,
      default: true
    },
    showRetry: {
      type: Boolean,
      default: false
    },
    retryInfo: {
      type: String,
      default: ''
    }
  },
  emits: ['close', 'retry'],
  setup(props, { emit }) {
    const visible = ref(true)
    let autoCloseTimer = null

    const close = () => {
      visible.value = false
      setTimeout(() => {
        emit('close')
      }, 300)
    }

    const handleRetry = () => {
      emit('retry')
      close()
    }

    const startAutoClose = () => {
      if (props.autoClose && props.duration > 0 && props.type !== 'loading') {
        autoCloseTimer = setTimeout(() => {
          close()
        }, props.duration)
      }
    }

    const stopAutoClose = () => {
      if (autoCloseTimer) {
        clearTimeout(autoCloseTimer)
        autoCloseTimer = null
      }
    }

    watch(() => props.message, () => {
      stopAutoClose()
      visible.value = true
      startAutoClose()
    })

    onMounted(() => {
      startAutoClose()
    })

    onUnmounted(() => {
      stopAutoClose()
    })

    return {
      visible,
      close,
      handleRetry
    }
  }
}
</script>

<style scoped>
.alert-wrapper {
  position: fixed;
  top: 20px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 9999;
  min-width: 320px;
  max-width: 600px;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  overflow: hidden;
}

.alert-content {
  display: flex;
  align-items: center;
  padding: 12px 16px;
  gap: 12px;
}

.alert-icon {
  flex-shrink: 0;
  width: 20px;
  height: 20px;
}

.alert-icon svg {
  width: 100%;
  height: 100%;
}

.alert-message {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
}

.alert-title {
  font-size: 14px;
  line-height: 1.5;
  word-break: break-word;
}

.alert-retry-info {
  font-size: 12px;
  opacity: 0.8;
}

.alert-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.alert-retry-btn,
.alert-close-btn {
  background: none;
  border: none;
  cursor: pointer;
  padding: 4px;
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
  border-radius: 4px;
  transition: all 0.2s;
}

.alert-retry-btn:hover,
.alert-close-btn:hover {
  background: rgba(0, 0, 0, 0.1);
}

.alert-retry-btn svg,
.alert-close-btn svg {
  width: 16px;
  height: 16px;
}

.alert-progress {
  height: 3px;
  background: rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.alert-progress-bar {
  height: 100%;
  width: 100%;
  animation: progress-shrink linear forwards;
}

@keyframes progress-shrink {
  from { transform: translateX(0); }
  to { transform: translateX(-100%); }
}

.alert-success {
  background-color: #f0f9eb;
  border: 1px solid #e1f3d8;
}

.alert-success .alert-icon { color: #67c23a; }
.alert-success .alert-title { color: #67c23a; }
.alert-success .alert-progress-bar { background: #67c23a; }

.alert-error {
  background-color: #fef0f0;
  border: 1px solid #fde2e2;
}

.alert-error .alert-icon { color: #f56c6c; }
.alert-error .alert-title { color: #f56c6c; }
.alert-error .alert-progress-bar { background: #f56c6c; }

.alert-warning {
  background-color: #fdf6ec;
  border: 1px solid #faecd8;
}

.alert-warning .alert-icon { color: #e6a23c; }
.alert-warning .alert-title { color: #e6a23c; }
.alert-warning .alert-progress-bar { background: #e6a23c; }

.alert-info {
  background-color: #f4f4f5;
  border: 1px solid #e9e9eb;
}

.alert-info .alert-icon { color: #909399; }
.alert-info .alert-title { color: #909399; }
.alert-info .alert-progress-bar { background: #909399; }

.alert-loading {
  background-color: #ecf5ff;
  border: 1px solid #d9ecff;
}

.alert-loading .alert-icon { 
  color: #409eff;
  animation: spin 1s linear infinite;
}

.alert-loading .alert-title { color: #409eff; }
.alert-loading .alert-progress-bar { background: #409eff; }

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.alert-fade-enter-active,
.alert-fade-leave-active {
  transition: all 0.3s ease;
}

.alert-fade-enter-from {
  opacity: 0;
  transform: translateX(-50%) translateY(-20px);
}

.alert-fade-leave-to {
  opacity: 0;
  transform: translateX(-50%) translateY(-20px);
}

.alert-with-retry .alert-content {
  padding-bottom: 8px;
}
</style>
