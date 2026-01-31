<template>
  <el-icon :size="size" :color="color" :class="iconClass" :aria-label="ariaLabel" role="img">
    <component :is="iconComponent" v-if="iconComponent" />
    <span v-else class="icon-fallback" aria-hidden="true">{{ iconText }}</span>
  </el-icon>
</template>

<script>
import { computed } from 'vue'
import { getIcon } from '@/utils/icons'

export default {
  name: 'AppIcon',
  props: {
    name: {
      type: String,
      required: true
    },
    size: {
      type: [Number, String],
      default: 16
    },
    color: {
      type: String,
      default: ''
    },
    spin: {
      type: Boolean,
      default: false
    },
    loading: {
      type: Boolean,
      default: false
    },
    label: {
      type: String,
      default: ''
    }
  },
  setup(props) {
    const iconComponent = computed(() => {
      return getIcon(props.name)
    })

    const iconText = computed(() => {
      return props.name.charAt(0).toUpperCase()
    })

    const iconClass = computed(() => {
      return {
        'app-icon': true,
        'is-spin': props.spin,
        'is-loading': props.loading
      }
    })

    const ariaLabel = computed(() => {
      return props.label || `图标: ${props.name}`
    })

    return {
      iconComponent,
      iconText,
      iconClass,
      ariaLabel
    }
  }
}
</script>

<style scoped>
.app-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  vertical-align: middle;
}

.app-icon.is-spin {
  animation: rotate 1s linear infinite;
}

.app-icon.is-loading {
  animation: rotate 1s linear infinite;
  opacity: 0.6;
}

@keyframes rotate {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

.icon-fallback {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
  font-weight: bold;
  font-size: 0.8em;
}

@media (prefers-reduced-motion: reduce) {
  .app-icon.is-spin,
  .app-icon.is-loading {
    animation: none;
  }
}
</style>
