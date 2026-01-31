<template>
  <el-alert
    v-if="show"
    :title="message"
    :type="type"
    :closable="dismissible"
    :show-icon="true"
    @close="close"
  />
</template>

<script>
import { ref, onMounted } from 'vue'

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
  emits: ['close'],
  setup(props, { emit }) {
    const show = ref(true)

    const close = () => {
      show.value = false
      emit('close')
    }

    onMounted(() => {
      if (props.duration > 0) {
        setTimeout(() => {
          close()
        }, props.duration)
      }
    })

    return {
      show,
      close
    }
  }
}
</script>
