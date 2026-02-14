<template>
  <el-form
    ref="formRef"
    :model="formData"
    :rules="rules"
    :label-position="inline ? 'top' : 'right'"
    :inline="inline"
    @submit.prevent="handleSubmit"
  >
    <slot></slot>

    <el-form-item v-if="showActions" class="form-actions">
      <slot name="actions">
        <el-button @click="handleReset">
          {{ resetText }}
        </el-button>
        <el-button
          type="primary"
          :loading="isSubmitting"
          @click="handleSubmit"
        >
          {{ submitText }}
        </el-button>
      </slot>
    </el-form-item>
  </el-form>
</template>

<script>
import { ref, provide, computed } from 'vue'

export default {
  name: 'BaseForm',
  props: {
    modelValue: {
      type: Object,
      default: () => ({})
    },
    rules: {
      type: Object,
      default: () => ({})
    },
    inline: {
      type: Boolean,
      default: false
    },
    showActions: {
      type: Boolean,
      default: true
    },
    submitText: {
      type: String,
      default: '提交'
    },
    resetText: {
      type: String,
      default: '重置'
    },
    validateOnSubmit: {
      type: Boolean,
      default: true
    }
  },
  emits: ['submit', 'reset', 'update:modelValue', 'validate'],
  setup(props, { emit }) {
    const formRef = ref(null)
    const formData = ref({ ...props.modelValue })
    const errors = ref({})
    const isSubmitting = ref(false)
    const touched = ref(new Set())

    const isValid = computed(() => {
      return Object.keys(errors.value).length === 0
    })

    const validateField = (fieldName, value) => {
      const fieldRules = props.rules[fieldName]
      if (!fieldRules) return null

      for (const rule of fieldRules) {
        const error = rule(value)
        if (error) {
          return error
        }
      }
      return null
    }

    const validateAll = () => {
      errors.value = {}
      let hasError = false

      for (const fieldName in props.rules) {
        const error = validateField(fieldName, formData.value[fieldName])
        if (error) {
          errors.value[fieldName] = error
          hasError = true
        }
      }

      return !hasError
    }

    const handleFieldChange = (fieldName, value) => {
      formData.value[fieldName] = value
      emit('update:modelValue', formData.value)

      if (touched.value.has(fieldName)) {
        const error = validateField(fieldName, value)
        if (error) {
          errors.value[fieldName] = error
        } else {
          delete errors.value[fieldName]
        }
      }
    }

    const handleFieldBlur = (fieldName) => {
      touched.value.add(fieldName)
      const error = validateField(fieldName, formData.value[fieldName])
      if (error) {
        errors.value[fieldName] = error
      } else {
        delete errors.value[fieldName]
      }
    }

    const handleSubmit = async () => {
      if (props.validateOnSubmit && !validateAll()) {
        emit('validate', false)
        return
      }

      isSubmitting.value = true
      try {
        emit('submit', formData.value)
        emit('validate', true)
      } finally {
        isSubmitting.value = false
      }
    }

    const handleReset = () => {
      formData.value = { ...props.modelValue }
      errors.value = {}
      touched.value.clear()
      emit('reset')
      emit('update:modelValue', formData.value)
    }

    provide('formData', formData)
    provide('errors', errors)
    provide('handleFieldChange', handleFieldChange)
    provide('handleFieldBlur', handleFieldBlur)

    return {
      formRef,
      formData,
      errors,
      isSubmitting,
      isValid,
      handleSubmit,
      handleReset
    }
  }
}
</script>

<style scoped>
.form-actions {
  margin-top: var(--spacing-lg);
}

.form-actions :deep(.el-form-item__content) {
  display: flex;
  gap: var(--spacing-md);
  justify-content: flex-end;
}
</style>
