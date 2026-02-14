<template>
  <div v-if="visible" class="toast-wrapper">
    <el-notification
      ref="notificationRef"
      :title="title"
      :message="message"
      :type="type"
      :duration="duration"
      :show-close="closable"
      @close="handleClose"
    />
  </div>
</template>

<script>
import { ref, onMounted, onUnmounted } from 'vue'
import { ElNotification } from 'element-plus'

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
    const notificationRef = ref(null)

    const handleClose = () => {
      emit('close')
    }

    onMounted(() => {
      if (props.visible) {
        ElNotification({
          title: props.title,
          message: props.message,
          type: props.type,
          duration: props.duration,
          showClose: props.closable,
          onClose: handleClose
        })
      }
    })

    onUnmounted(() => {
      if (notificationRef.value) {
        notificationRef.value.close()
      }
    })

    return {
      notificationRef,
      handleClose
    }
  }
}
</script>

<style scoped>
.toast-wrapper {
  position: fixed;
  top: 20px;
  right: 20px;
  z-index: 10000;
}

@media (max-width: 768px) {
  .toast-wrapper {
    top: 10px;
    right: 10px;
    left: 10px;
  }
}
</style>
