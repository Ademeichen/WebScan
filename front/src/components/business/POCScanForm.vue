<template>
  <div class="poc-scan-form" :class="{ 'is-submitting': isSubmitting }">
    <h2>POC扫描配置</h2>
    
    <form @submit.prevent="handleSubmit">
      <div class="form-row">
        <div class="form-group" :class="{ 'has-error': validationErrors.target }">
          <label for="target">扫描目标 *</label>
          <input
            id="target"
            v-model="formData.target"
            @input="handleFieldValidation('target')"
            @blur="handleFieldValidation('target', true)"
            type="text"
            placeholder="请输入URL或IP地址"
            :disabled="isSubmitting"
            :class="{ 'has-error': validationErrors.target, 'is-valid': isValidated.target && !validationErrors.target }"
          />
          <small class="help-text">支持URL格式：https://example.com 或 http://192.168.1.1</small>
          <transition name="fade">
            <span v-if="validationErrors.target" class="error-message">
              <span class="error-icon">!</span>
              {{ validationErrors.target }}
            </span>
          </transition>
        </div>
        
        <div class="form-group" :class="{ 'has-error': validationErrors.taskName }">
          <label for="taskName">任务名称 *</label>
          <input
            id="taskName"
            v-model="formData.taskName"
            @input="handleFieldValidation('taskName')"
            @blur="handleFieldValidation('taskName', true)"
            type="text"
            placeholder="请输入任务名称"
            :disabled="isSubmitting"
            :class="{ 'has-error': validationErrors.taskName, 'is-valid': isValidated.taskName && !validationErrors.taskName }"
          />
          <transition name="fade">
            <span v-if="validationErrors.taskName" class="error-message">
              <span class="error-icon">!</span>
              {{ validationErrors.taskName }}
            </span>
          </transition>
        </div>
      </div>

      <div class="form-group poc-type-section">
        <div class="poc-type-header">
          <label>POC类型</label>
          <div class="poc-type-actions">
            <input
              v-model="pocSearchQuery"
              type="text"
              placeholder="搜索POC类型..."
              class="poc-search-input"
              :disabled="isSubmitting"
            />
            <div class="poc-action-buttons">
              <button type="button" class="btn-text" @click="selectAllPOCTypes" :disabled="isSubmitting">
                全选
              </button>
              <button type="button" class="btn-text" @click="deselectAllPOCTypes" :disabled="isSubmitting">
                取消全选
              </button>
            </div>
          </div>
        </div>
        
        <div class="poc-categories">
          <div 
            v-for="category in filteredPOCCategories" 
            :key="category.name" 
            class="poc-category"
          >
            <div class="category-header" @click="toggleCategory(category.name)">
              <span class="category-icon">{{ expandedCategories.includes(category.name) ? '▼' : '▶' }}</span>
              <span class="category-name">{{ category.label }}</span>
              <span class="category-count">({{ category.types.length }})</span>
            </div>
            <transition name="slide">
              <div v-show="expandedCategories.includes(category.name)" class="checkbox-group">
                <label 
                  v-for="pocType in category.types" 
                  :key="pocType.value" 
                  class="checkbox-item"
                  :class="{ 'is-selected': formData.pocTypes.includes(pocType.value) }"
                >
                  <input
                    v-model="formData.pocTypes"
                    :value="pocType.value"
                    type="checkbox"
                    :disabled="isSubmitting"
                  />
                  <span class="checkbox-custom"></span>
                  <span class="checkbox-label">{{ pocType.label }}</span>
                </label>
              </div>
            </transition>
          </div>
        </div>
        <small class="help-text">不选择则扫描所有POC类型</small>
      </div>

      <div class="form-row">
        <div class="form-group" :class="{ 'has-error': validationErrors.timeout }">
          <label for="timeout">超时时间（秒）</label>
          <input
            id="timeout"
            v-model.number="formData.timeout"
            @input="handleFieldValidation('timeout')"
            @blur="handleFieldValidation('timeout', true)"
            type="number"
            min="1"
            max="300"
            placeholder="30"
            :disabled="isSubmitting"
            :class="{ 'has-error': validationErrors.timeout, 'is-valid': isValidated.timeout && !validationErrors.timeout }"
          />
          <transition name="fade">
            <span v-if="validationErrors.timeout" class="error-message">
              <span class="error-icon">!</span>
              {{ validationErrors.timeout }}
            </span>
          </transition>
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
            :disabled="isSubmitting"
          />
        </div>
      </div>

      <div class="form-group">
        <label class="checkbox-label-inline">
          <input v-model="formData.enableProxy" type="checkbox" :disabled="isSubmitting" />
          <span class="checkbox-custom"></span>
          <span>启用代理</span>
        </label>
      </div>

      <transition name="slide">
        <div v-if="formData.enableProxy" class="form-group proxy-config" :class="{ 'has-error': validationErrors.proxyUrl }">
          <label for="proxyUrl">代理地址</label>
          <input
            id="proxyUrl"
            v-model="formData.proxyUrl"
            @input="handleFieldValidation('proxyUrl')"
            @blur="handleFieldValidation('proxyUrl', true)"
            type="text"
            placeholder="http://proxy.example.com:8080"
            :disabled="isSubmitting"
            :class="{ 'has-error': validationErrors.proxyUrl, 'is-valid': isValidated.proxyUrl && !validationErrors.proxyUrl }"
          />
          <transition name="fade">
            <span v-if="validationErrors.proxyUrl" class="error-message">
              <span class="error-icon">!</span>
              {{ validationErrors.proxyUrl }}
            </span>
          </transition>
        </div>
      </transition>

      <div class="form-actions">
        <button type="button" class="btn-secondary" @click="handleReset" :disabled="isSubmitting">
          重置
        </button>
        <button type="submit" class="btn-primary" :disabled="isSubmitting || !isFormValid">
          <span v-if="isSubmitting" class="loading-content">
            <span class="spinner"></span>
            <span v-if="progress > 0" class="progress-text">{{ progress }}%</span>
            <span v-else>提交中...</span>
          </span>
          <span v-else>开始扫描</span>
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

<script setup>
import { ref, onMounted, computed, watch } from 'vue'
import { pocApi } from '@/utils/api'
import { validators, validateField } from '@/utils/validators'
import Alert from '@/components/common/Alert.vue'

const emit = defineEmits(['submit', 'success', 'error'])

const DEFAULT_TIMEOUT = parseInt(import.meta.env.VITE_REQUEST_TIMEOUT) / 1000 || 30

const formData = ref({
  target: '',
  taskName: '',
  pocTypes: [],
  timeout: DEFAULT_TIMEOUT,
  maxThreads: 10,
  enableProxy: false,
  proxyUrl: ''
})

const pocCategories = ref([
  {
    name: 'injection',
    label: '注入类漏洞',
    types: [
      { value: 'sql_injection', label: 'SQL注入' },
      { value: 'xss', label: 'XSS跨站脚本' },
      { value: 'command_injection', label: '命令注入' },
      { value: 'xxe', label: 'XXE外部实体注入' },
      { value: 'rce', label: '远程代码执行' }
    ]
  },
  {
    name: 'request',
    label: '请求伪造类',
    types: [
      { value: 'csrf', label: 'CSRF跨站请求伪造' },
      { value: 'ssrf', label: 'SSRF服务端请求伪造' }
    ]
  },
  {
    name: 'file',
    label: '文件相关漏洞',
    types: [
      { value: 'file_upload', label: '文件上传漏洞' },
      { value: 'path_traversal', label: '路径遍历' }
    ]
  },
  {
    name: 'other',
    label: '其他漏洞',
    types: [
      { value: 'information_disclosure', label: '信息泄露' }
    ]
  }
])

const expandedCategories = ref(['injection', 'request', 'file', 'other'])
const pocSearchQuery = ref('')
const isSubmitting = ref(false)
const progress = ref(0)
const errorMessage = ref('')

const validationErrors = ref({
  target: '',
  taskName: '',
  timeout: '',
  proxyUrl: ''
})

const isValidated = ref({
  target: false,
  taskName: false,
  timeout: false,
  proxyUrl: false
})

const validationRules = {
  target: [validators.required, validators.url],
  taskName: [validators.required, validators.minLength(3)],
  timeout: [validators.range(1, 300)],
  proxyUrl: [validators.required, validators.url]
}

const filteredPOCCategories = computed(() => {
  if (!pocSearchQuery.value.trim()) {
    return pocCategories.value
  }
  
  const query = pocSearchQuery.value.toLowerCase()
  return pocCategories.value
    .map(category => ({
      ...category,
      types: category.types.filter(type => 
        type.label.toLowerCase().includes(query) ||
        type.value.toLowerCase().includes(query)
      )
    }))
    .filter(category => category.types.length > 0)
})

const isFormValid = computed(() => {
  const hasErrors = Object.values(validationErrors.value).some(error => error !== '')
  const hasRequiredFields = formData.value.target && formData.value.taskName
  const proxyValid = !formData.value.enableProxy || formData.value.proxyUrl
  
  return !hasErrors && hasRequiredFields && proxyValid
})

const toggleCategory = (categoryName) => {
  const index = expandedCategories.value.indexOf(categoryName)
  if (index > -1) {
    expandedCategories.value.splice(index, 1)
  } else {
    expandedCategories.value.push(categoryName)
  }
}

const selectAllPOCTypes = () => {
  const allValues = pocCategories.value.flatMap(cat => cat.types.map(t => t.value))
  formData.value.pocTypes = allValues
}

const deselectAllPOCTypes = () => {
  formData.value.pocTypes = []
}

const handleFieldValidation = (field, forceValidate = false) => {
  if (field === 'proxyUrl' && !formData.value.enableProxy) {
    validationErrors.value.proxyUrl = ''
    isValidated.value.proxyUrl = false
    return
  }
  
  if (forceValidate || isValidated.value[field]) {
    isValidated.value[field] = true
    const rules = validationRules[field]
    if (rules) {
      const error = validateField(formData.value[field], rules)
      validationErrors.value[field] = error || ''
    }
  }
}

const validateForm = () => {
  Object.keys(validationRules).forEach(field => {
    if (field === 'proxyUrl' && !formData.value.enableProxy) {
      validationErrors.value[field] = ''
      isValidated.value[field] = false
      return
    }
    isValidated.value[field] = true
    const error = validateField(formData.value[field], validationRules[field])
    validationErrors.value[field] = error || ''
  })
  
  return Object.values(validationErrors.value).every(error => error === '')
}

watch(() => formData.value.enableProxy, (enabled) => {
  if (!enabled) {
    validationErrors.value.proxyUrl = ''
    isValidated.value.proxyUrl = false
  }
})

const loadPOCTypes = async () => {
  try {
    const response = await pocApi.getPOCTypes()
    if (response && response.code === 200 && response.data) {
      const types = response.data.map(type => ({
        value: type.value,
        label: type.label
      }))
      updatePOCCategories(types)
    } else if (response && Array.isArray(response)) {
      const types = response.map(type => ({
        value: type.value,
        label: type.label
      }))
      updatePOCCategories(types)
    }
  } catch (error) {
    console.error('加载POC类型失败:', error)
    if (error.response && error.response.status === 500) {
      console.warn('后端服务暂时不可用，使用默认POC类型')
    }
  }
}

const updatePOCCategories = (types) => {
  if (!types || types.length === 0) return
  
  const categoryMap = {
    injection: ['sql_injection', 'xss', 'command_injection', 'xxe', 'rce'],
    request: ['csrf', 'ssrf'],
    file: ['file_upload', 'path_traversal'],
    other: ['information_disclosure']
  }
  
  pocCategories.value = pocCategories.value.map(category => ({
    ...category,
    types: types.filter(type => categoryMap[category.name]?.includes(type.value))
  })).filter(category => category.types.length > 0)
}

const simulateProgress = () => {
  progress.value = 0
  const interval = setInterval(() => {
    if (progress.value < 90) {
      progress.value += Math.random() * 15
      if (progress.value > 90) progress.value = 90
    }
  }, 500)
  return interval
}

const handleSubmit = async () => {
  if (isSubmitting.value) return
  
  if (!validateForm()) {
    errorMessage.value = '请修正表单中的错误'
    return
  }

  isSubmitting.value = true
  errorMessage.value = ''
  const progressInterval = simulateProgress()

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
    progress.value = 100
    
    if (response.code === 200) {
      emit('success', response.data)
      setTimeout(() => handleReset(), 500)
    } else {
      errorMessage.value = response.message || '创建任务失败'
      emit('error', response)
    }
  } catch (error) {
    errorMessage.value = error.message || '网络错误，请稍后重试'
    emit('error', error)
  } finally {
    clearInterval(progressInterval)
    setTimeout(() => {
      isSubmitting.value = false
      progress.value = 0
    }, 300)
  }
}

const handleReset = () => {
  formData.value = {
    target: '',
    taskName: '',
    pocTypes: [],
    timeout: DEFAULT_TIMEOUT,
    maxThreads: 10,
    enableProxy: false,
    proxyUrl: ''
  }
  validationErrors.value = {
    target: '',
    taskName: '',
    timeout: '',
    proxyUrl: ''
  }
  isValidated.value = {
    target: false,
    taskName: false,
    timeout: false,
    proxyUrl: false
  }
  errorMessage.value = ''
  pocSearchQuery.value = ''
  expandedCategories.value = ['injection', 'request', 'file', 'other']
}

onMounted(() => {
  loadPOCTypes()
})
</script>

<style scoped>
.poc-scan-form {
  max-width: 900px;
  margin: 0 auto;
  padding: var(--spacing-lg);
}

.poc-scan-form h2 {
  margin-bottom: var(--spacing-xl);
  color: var(--text-primary);
  font-size: 1.5rem;
}

.form-row {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: var(--spacing-lg);
}

.form-group {
  margin-bottom: var(--spacing-lg);
}

.form-group label {
  display: block;
  margin-bottom: var(--spacing-sm);
  font-weight: 500;
  color: var(--text-primary);
  font-size: 0.9rem;
}

.form-group input[type="text"],
.form-group input[type="number"] {
  width: 100%;
  padding: 0.75rem 1rem;
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius);
  font-size: 0.95rem;
  transition: all var(--transition-base);
  background-color: var(--bg-primary);
  color: var(--text-primary);
}

.form-group input[type="text"]:focus,
.form-group input[type="number"]:focus {
  outline: none;
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px rgba(74, 144, 226, 0.15);
}

.form-group input:disabled {
  background-color: var(--bg-secondary);
  cursor: not-allowed;
  opacity: 0.7;
}

.form-group input.has-error {
  border-color: var(--high-risk);
  background-color: rgba(231, 76, 60, 0.05);
}

.form-group input.has-error:focus {
  border-color: var(--high-risk);
  box-shadow: 0 0 0 3px rgba(231, 76, 60, 0.15);
}

.form-group input.is-valid {
  border-color: var(--low-risk, #27ae60);
}

.form-group input.is-valid:focus {
  box-shadow: 0 0 0 3px rgba(39, 174, 96, 0.15);
}

.error-message {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: var(--high-risk);
  font-size: 0.8rem;
  margin-top: var(--spacing-xs);
  padding: 0.25rem 0;
}

.error-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 16px;
  height: 16px;
  background-color: var(--high-risk);
  color: white;
  border-radius: 50%;
  font-size: 0.7rem;
  font-weight: bold;
}

.help-text {
  display: block;
  margin-top: var(--spacing-xs);
  font-size: 0.8rem;
  color: var(--text-secondary);
}

.poc-type-section {
  margin-top: var(--spacing-lg);
}

.poc-type-header {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
  margin-bottom: var(--spacing-md);
}

.poc-type-header > label {
  margin-bottom: 0;
}

.poc-type-actions {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-md);
  align-items: center;
}

.poc-search-input {
  flex: 1;
  min-width: 200px;
  padding: 0.5rem 0.75rem;
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius);
  font-size: 0.9rem;
  background-color: var(--bg-primary);
  color: var(--text-primary);
}

.poc-search-input:focus {
  outline: none;
  border-color: var(--color-primary);
  box-shadow: 0 0 0 2px rgba(74, 144, 226, 0.1);
}

.poc-action-buttons {
  display: flex;
  gap: var(--spacing-sm);
}

.btn-text {
  padding: 0.4rem 0.75rem;
  background: none;
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius-sm);
  color: var(--color-primary);
  font-size: 0.85rem;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-text:hover:not(:disabled) {
  background-color: var(--color-primary-bg);
  border-color: var(--color-primary);
}

.btn-text:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.poc-categories {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.poc-category {
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius);
  overflow: hidden;
}

.category-header {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  padding: 0.75rem 1rem;
  background-color: var(--bg-secondary);
  cursor: pointer;
  user-select: none;
  transition: background-color 0.2s;
}

.category-header:hover {
  background-color: var(--color-primary-bg);
}

.category-icon {
  font-size: 0.7rem;
  color: var(--text-secondary);
  transition: transform 0.2s;
}

.category-name {
  font-weight: 500;
  color: var(--text-primary);
}

.category-count {
  font-size: 0.8rem;
  color: var(--text-secondary);
}

.checkbox-group {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: var(--spacing-sm);
  padding: var(--spacing-md);
  background-color: var(--bg-primary);
}

.checkbox-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  padding: 0.5rem 0.75rem;
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius-sm);
  cursor: pointer;
  transition: all 0.2s;
  background-color: var(--bg-primary);
}

.checkbox-item:hover {
  background-color: var(--color-primary-bg);
  border-color: var(--color-primary);
}

.checkbox-item.is-selected {
  background-color: var(--color-primary-bg);
  border-color: var(--color-primary);
}

.checkbox-item input[type="checkbox"] {
  display: none;
}

.checkbox-custom {
  width: 18px;
  height: 18px;
  border: 2px solid var(--border-color);
  border-radius: 3px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
  flex-shrink: 0;
}

.checkbox-item input[type="checkbox"]:checked + .checkbox-custom {
  background-color: var(--color-primary);
  border-color: var(--color-primary);
}

.checkbox-item input[type="checkbox"]:checked + .checkbox-custom::after {
  content: '✓';
  color: white;
  font-size: 0.7rem;
  font-weight: bold;
}

.checkbox-label {
  font-size: 0.9rem;
  color: var(--text-primary);
}

.checkbox-label-inline {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  cursor: pointer;
}

.checkbox-label-inline input[type="checkbox"] {
  display: none;
}

.proxy-config {
  margin-left: var(--spacing-lg);
  padding-left: var(--spacing-lg);
  border-left: 3px solid var(--color-primary);
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

.form-actions {
  display: flex;
  gap: var(--spacing-md);
  margin-top: var(--spacing-xl);
}

.btn-primary,
.btn-secondary {
  flex: 1;
  padding: 0.875rem var(--spacing-lg);
  border: none;
  border-radius: var(--border-radius);
  font-size: 1rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s;
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 48px;
}

.btn-primary {
  background-color: var(--color-primary);
  color: #1a1a1a;
}

.btn-primary:hover:not(:disabled) {
  background-color: var(--color-primary-dark);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(74, 144, 226, 0.3);
}

.btn-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

.btn-secondary {
  background-color: var(--color-secondary);
  color: #1a1a1a;
}

.btn-secondary:hover:not(:disabled) {
  background-color: var(--color-secondary-dark);
}

.btn-secondary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.loading-content {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
}

.spinner {
  width: 18px;
  height: 18px;
  border: 2px solid transparent;
  border-top-color: currentColor;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.progress-text {
  font-size: 0.9rem;
  font-weight: 600;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

.slide-enter-active,
.slide-leave-active {
  transition: all 0.3s ease;
  overflow: hidden;
}

.slide-enter-from,
.slide-leave-to {
  opacity: 0;
  max-height: 0;
  padding-top: 0;
  padding-bottom: 0;
}

.slide-enter-to,
.slide-leave-from {
  max-height: 500px;
}

@media (max-width: 768px) {
  .poc-scan-form {
    padding: var(--spacing-md);
  }

  .form-row {
    grid-template-columns: 1fr;
    gap: 0;
  }

  .poc-type-actions {
    flex-direction: column;
    align-items: stretch;
  }

  .poc-search-input {
    min-width: 100%;
  }

  .poc-action-buttons {
    justify-content: flex-end;
  }

  .checkbox-group {
    grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
  }

  .form-actions {
    flex-direction: column-reverse;
  }

  .btn-primary,
  .btn-secondary {
    width: 100%;
  }

  .proxy-config {
    margin-left: var(--spacing-sm);
    padding-left: var(--spacing-sm);
  }
}

@media (max-width: 480px) {
  .poc-scan-form h2 {
    font-size: 1.25rem;
  }

  .checkbox-group {
    grid-template-columns: 1fr;
  }

  .category-header {
    padding: 0.6rem 0.75rem;
  }

  .btn-text {
    padding: 0.35rem 0.5rem;
    font-size: 0.8rem;
  }
}

@media (min-width: 1200px) {
  .poc-scan-form {
    max-width: 1000px;
  }

  .checkbox-group {
    grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  }
}
</style>
