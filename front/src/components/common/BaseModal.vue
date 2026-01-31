<template>
  <el-dialog
    v-model="dialogVisible"
    :title="title"
    :width="modalWidth"
    :close-on-click-modal="closeOnClickOverlay"
    :close-on-press-escape="closeOnEsc"
    :show-close="closable"
    :draggable="true"
    @close="handleClose"
  >
    <slot></slot>

    <template #footer v-if="showFooter">
      <slot name="footer">
        <el-button @click="handleCancel">
          {{ cancelText }}
        </el-button>
        <el-button
          type="primary"
          :loading="loading"
          @click="handleConfirm"
        >
          {{ confirmText }}
        </el-button>
      </slot>
    </template>
  </el-dialog>
</template>

<script>
import { computed, watch } from 'vue'

export default {
  name: 'BaseModal',
  props: {
    visible: {
      type: Boolean,
      default: false
    },
    title: {
      type: String,
      default: ''
    },
    size: {
      type: String,
      default: 'medium',
      validator: (value) => ['small', 'medium', 'large', 'full'].includes(value)
    },
    closable: {
      type: Boolean,
      default: true
    },
    closeOnClickOverlay: {
      type: Boolean,
      default: true
    },
    closeOnEsc: {
      type: Boolean,
      default: true
    },
    showHeader: {
      type: Boolean,
      default: true
    },
    showFooter: {
      type: Boolean,
      default: true
    },
    confirmText: {
      type: String,
      default: '确定'
    },
    cancelText: {
      type: String,
      default: '取消'
    },
    loading: {
      type: Boolean,
      default: false
    },
    customClass: {
      type: String,
      default: ''
    }
  },
  emits: ['update:visible', 'confirm', 'cancel', 'close'],
  setup(props, { emit }) {
    const dialogVisible = computed({
      get: () => props.visible,
      set: (val) => {
        emit('update:visible', val)
      }
    })

    const modalWidth = computed(() => {
      const widthMap = {
        small: '400px',
        medium: '600px',
        large: '800px',
        full: '95%'
      }
      return widthMap[props.size] || widthMap.medium
    })

    const handleClose = () => {
      emit('update:visible', false)
      emit('close')
    }

    const handleConfirm = () => {
      emit('confirm')
    }

    const handleCancel = () => {
      emit('cancel')
      handleClose()
    }

    watch(() => props.visible, (newVal) => {
      if (newVal) {
        document.body.style.overflow = 'hidden'
      } else {
        document.body.style.overflow = ''
      }
    })

    return {
      dialogVisible,
      modalWidth,
      handleClose,
      handleConfirm,
      handleCancel
    }
  }
}
</script>

<style scoped>
@media (max-width: 768px) {
  :deep(.el-dialog) {
    width: 90% !important;
    margin: 0 auto;
  }

  :deep(.el-dialog__footer) {
    flex-direction: column;
    gap: var(--spacing-md);
  }

  :deep(.el-dialog__footer .el-button) {
    width: 100%;
  }
}
</style>
