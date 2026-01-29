<template>
  <form @submit.prevent="handleSubmit" :class="['form', { 'form-inline': inline }]">
    <slot></slot>
    
    <div v-if="showActions" class="form-actions">
      <slot name="actions">
        <button type="button" class="btn btn-secondary" @click="handleReset">
          {{ resetText }}
        </button>
        <button type="submit" class="btn btn-primary" :disabled="isSubmitting">
          <span v-if="isSubmitting" class="btn-loading"></span>
          {{ submitText }}
        </button>
      </slot>
    </div>
  </form>
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
.form {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.form-inline {
  flex-direction: row;
  align-items: center;
  gap: var(--spacing-md);
}

.form-actions {
  display: flex;
  gap: var(--spacing-md);
  justify-content: flex-end;
  margin-top: var(--spacing-lg);
}

.btn {
  padding: var(--spacing-sm) var(--spacing-lg);
  border: none;
  border-radius: var(--border-radius);
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all var(--transition-base);
  display: inline-flex;
  align-items: center;
  gap: var(--spacing-xs);
}

.btn-primary {
  background-color: var(--secondary-color);
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background-color: var(--secondary-dark);
}

.btn-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-secondary {
  background-color: var(--background-color);
  color: var(--text-primary);
  border: 1px solid var(--border-color);
}

.btn-secondary:hover {
  background-color: var(--background-dark);
}

.btn-loading {
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

@media (max-width: 768px) {
  .form-actions {
    flex-direction: column;
  }
  
  .btn {
    width: 100%;
  }
}
</style>
