<template>
  <div class="poc-scan-form">
    <h2>POC扫描配置</h2>
    
    <form @submit.prevent="handleSubmit">
      <div class="form-group">
        <label for="target">扫描目标 *</label>
        <input
          id="target"
          v-model="formData.target"
          @input="debouncedValidate"
          type="text"
          placeholder="请输入URL或IP地址"
          required
          :class="{ 'has-error': validationErrors.target }"
        />
        <small class="help-text">支持URL格式：https://www.baidu.com 或 https://www.baidu.com</small>
        <span v-if="validationErrors.target" class="error-message">{{ validationErrors.target }}</span>
      </div>
      
      <div class="form-group">
        <label for="taskName">任务名称 *</label>
        <input
          id="taskName"
          v-model="formData.taskName"
          @input="debouncedValidate"
          type="text"
          placeholder="请输入任务名称"
          required
          :class="{ 'has-error': validationErrors.taskName }"
        />
        <span v-if="validationErrors.taskName" class="error-message">{{ validationErrors.taskName }}</span>
      </div>

      <div class="form-group">
        <label>POC类型</label>
        <div class="checkbox-group">
          <label v-for="pocType in availablePOCTypes" :key="pocType.value" class="checkbox-item">
            <input
              v-model="formData.pocTypes"
              :value="pocType.value"
              type="checkbox"
            />
            <span>{{ pocType.label }}</span>
          </label>
        </div>
        <small class="help-text">不选择则扫描所有POC类型</small>
      </div>

      <div class="form-group">
        <label for="timeout">超时时间（秒）</label>
        <input
          id="timeout"
          v-model.number="formData.timeout"
          type="number"
          min="1"
          max="300"
          placeholder="30"
        />
      </div>

      <div class="form-group">
        <label for="maxThreads">最大线程数</label>
        <input
          id="maxThreads"
          v-model.number="formData.maxThreads"
          type="number"
          min="1"
          max="50"
          placeholder="10"
        />
      </div>

      <div class="form-group">
        <label>
          <input v-model="formData.enableProxy" type="checkbox" />
          <span>启用代理</span>
        </label>
      </div>

      <div v-if="formData.enableProxy" class="form-group proxy-config">
        <label for="proxyUrl">代理地址</label>
        <input
          id="proxyUrl"
          v-model="formData.proxyUrl"
          @input="debouncedValidate"
          type="text"
          placeholder="http://proxy.www.baidu.com:8080"
          :class="{ 'has-error': validationErrors.proxyUrl }"
        />
        <span v-if="validationErrors.proxyUrl" class="error-message">{{ validationErrors.proxyUrl }}</span>
      </div>

      <div class="form-actions">
        <button type="button" class="btn-secondary" @click="handleReset">
          重置
        </button>
        <button type="submit" class="btn-primary" :disabled="isSubmitting">
          {{ isSubmitting ? '提交中...' : '开始扫描' }}
        </button>
      </div>
    </form>

    <Alert
      v-if="errorMessage"
      type="error"
      :message="errorMessage"
      @close="errorMessage = ''"
    />
  </div>
</template>

<script>
import { ref, onMounted, computed } from 'vue'
import { pocApi } from '@/utils/api'
import { validators, debounce } from '@/utils/validators'
import Alert from '@/components/common/Alert.vue'

export default {
  name: 'POCScanForm',
  components: {
    Alert
  },
  emits: ['submit', 'success', 'error'],
  setup(props, { emit }) {
    const formData = ref({
      target: '',
      taskName: '',
      pocTypes: [],
      timeout: 30,
      maxThreads: 10,
      enableProxy: false,
      proxyUrl: ''
    })

    const availablePOCTypes = ref([
      { value: 'sql_injection', label: 'SQL注入' },
      { value: 'xss', label: 'XSS跨站脚本' },
      { value: 'csrf', label: 'CSRF跨站请求伪造' },
      { value: 'file_upload', label: '文件上传漏洞' },
      { value: 'path_traversal', label: '路径遍历' },
      { value: 'command_injection', label: '命令注入' },
      { value: 'ssrf', label: 'SSRF服务端请求伪造' },
      { value: 'xxe', label: 'XXE外部实体注入' },
      { value: 'rce', label: '远程代码执行' },
      { value: 'information_disclosure', label: '信息泄露' }
    ])

    const isSubmitting = ref(false)
    const errorMessage = ref('')

    const validationErrors = ref({
      target: '',
      taskName: '',
      proxyUrl: ''
    })

    const debouncedValidate = debounce(() => {
      validateForm()
    }, 300)

    const validateField = (field, value, rules) => {
      const error = validators.validateField(value, rules)
      validationErrors.value[field] = error || ''
    }

    const validateForm = () => {
      validateField('target', formData.value.target, [validators.required, validators.url])
      validateField('taskName', formData.value.taskName, [validators.required, validators.minLength(2)])
      if (formData.value.enableProxy) {
        validateField('proxyUrl', formData.value.proxyUrl, [validators.required, validators.url])
      } else {
        validationErrors.value.proxyUrl = ''
      }
    }

    const isFormValid = computed(() => {
      return Object.values(validationErrors.value).every(error => error === '') &&
             formData.value.target &&
             formData.value.taskName &&
             (!formData.value.enableProxy || formData.value.proxyUrl)
    })

    const loadPOCTypes = async () => {
      try {
        const response = await pocApi.getPOCTypes()
        if (response.code === 200 && response.data) {
          availablePOCTypes.value = response.data.map(type => ({
            value: type.value,
            label: type.label
          }))
        }
      } catch (error) {
        console.error('加载POC类型失败:', error)
      }
    }

    const handleSubmit = async () => {
      if (isSubmitting.value) return
      if (!isFormValid.value) {
        errorMessage.value = '请修正表单中的错误'
        return
      }

      isSubmitting.value = true
      errorMessage.value = ''

      try {
        emit('submit', formData.value)

        const taskData = {
          task_name: formData.value.taskName,
          target: formData.value.target,
          task_type: 'poc_scan',
          config: {
            poc_types: formData.value.pocTypes,
            timeout: formData.value.timeout,
            max_threads: formData.value.maxThreads,
            enable_proxy: formData.value.enableProxy,
            proxy_url: formData.value.proxyUrl
          }
        }
        const response = await pocApi.runPOC(taskData)
        if (response.code === 200) {
          emit('success', response.data)
          handleReset()
        } else {
          errorMessage.value = response.message || '创建任务失败'
          emit('error', response)
        }
      } catch (error) {
        errorMessage.value = error.message || '网络错误，请稍后重试'
        emit('error', error)
      } finally {
        isSubmitting.value = false
      }
    }

    const handleReset = () => {
      formData.value = {
        target: '',
        taskName: '',
        pocTypes: [],
        timeout: 30,
        maxThreads: 10,
        enableProxy: false,
        proxyUrl: ''
      }
      validationErrors.value = {
        target: '',
        taskName: '',
        proxyUrl: ''
      }
      errorMessage.value = ''
    }

    onMounted(() => {
      loadPOCTypes()
    })

    return {
      formData,
      availablePOCTypes,
      isSubmitting,
      errorMessage,
      validationErrors,
      isFormValid,
      handleSubmit,
      handleReset
    }
  }
}
</script>

<style scoped>
.poc-scan-form {
  max-width: 800px;
  margin: 0 auto;
  padding: var(--spacing-lg);
}

.poc-scan-form h2 {
  margin-bottom: var(--spacing-xl);
  color: var(--text-primary);
}

.form-group {
  margin-bottom: var(--spacing-lg);
}

.form-group label {
  display: block;
  margin-bottom: var(--spacing-sm);
  font-weight: 500;
  color: var(--text-primary);
}

.form-group input[type="text"],
.form-group input[type="number"] {
  width: 100%;
  padding: var(--spacing-sm) var(--spacing-md);
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius);
  font-size: 14px;
  transition: all var(--transition-base);
}

.form-group input[type="text"]:focus,
.form-group input[type="number"]:focus {
  outline: none;
  border-color: var(--secondary-color);
  box-shadow: 0 0 0 3px rgba(74, 144, 226, 0.1);
}

.form-group input.has-error {
  border-color: var(--high-risk);
}

.form-group input.has-error:focus {
  border-color: var(--high-risk);
  box-shadow: 0 0 0 3px rgba(231, 76, 60, 0.1);
}

.error-message {
  display: block;
  color: var(--high-risk);
  font-size: 12px;
  margin-top: var(--spacing-xs);
}

.help-text {
  display: block;
  margin-top: var(--spacing-xs);
  font-size: 0.875rem;
  color: var(--text-secondary);
}

.checkbox-group {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: var(--spacing-sm);
  margin-top: var(--spacing-sm);
}

.checkbox-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-sm);
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius-sm);
  cursor: pointer;
  transition: all 0.3s;
}

.checkbox-item:hover {
  background-color: var(--color-primary-bg);
  border-color: var(--color-primary);
}

.checkbox-item input[type="checkbox"] {
  cursor: pointer;
}

.proxy-config {
  margin-left: var(--spacing-lg);
  padding-left: var(--spacing-lg);
  border-left: 2px solid var(--color-primary);
}

.form-actions {
  display: flex;
  gap: var(--spacing-md);
  margin-top: var(--spacing-xl);
}

.btn-primary,
.btn-secondary {
  flex: 1;
  padding: var(--spacing-md) var(--spacing-lg);
  border: none;
  border-radius: var(--border-radius);
  font-size: 1rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s;
}

.btn-primary {
  background-color: var(--color-primary);
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background-color: var(--color-primary-dark);
}

.btn-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-secondary {
  background-color: var(--color-secondary);
  color: white;
}

.btn-secondary:hover {
  background-color: var(--color-secondary-dark);
}
</style>
