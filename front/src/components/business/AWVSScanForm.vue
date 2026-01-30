<template>
  <div class="awvs-scan-form">
    <h2>AWVS扫描配置</h2>
    
    <form @submit.prevent="handleSubmit">
      <div class="form-group">
        <label for="target">扫描目标 *</label>
        <input
          id="target"
          v-model="formData.target"
          type="text"
          placeholder="请输入URL"
          required
        />
        <small class="help-text">支持URL格式：https://www.baidu.com 或 https://www.baidu.com</small>
      </div>

      <div class="form-group">
        <label for="profileId">扫描配置 *</label>
        <select id="profileId" v-model="formData.profileId" required>
          <option
            v-for="profile in scanProfiles"
            :key="profile.value"
            :value="profile.value"
          >
            {{ profile.label }}
          </option>
        </select>
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
import { ref, onMounted } from 'vue'
import { awvsApi } from '@/utils/api'
import Alert from '@/components/common/Alert.vue'

export default {
  name: 'AWVSScanForm',
  components: {
    Alert
  },
  emits: ['submit', 'success', 'error'],
  setup(props, { emit }) {
    const formData = ref({
      target: '',
      profileId: 'full_scan'
    })

    const scanProfiles = ref([
      { value: 'full_scan', label: 'Full Scan' },
      { value: 'high_risk_vuln', label: 'High Risk Vulnerabilities' },
      { value: 'xss_vuln', label: 'Cross-site Scripting (XSS)' },
      { value: 'sqli_vuln', label: 'SQL Injection' },
      { value: 'crawl_only', label: 'Crawl Only' },
      { value: 'weak_passwords', label: 'Weak Passwords' }
    ])

    const isSubmitting = ref(false)
    const errorMessage = ref('')

    const handleSubmit = async () => {
      if (isSubmitting.value) return

      isSubmitting.value = true
      errorMessage.value = ''

      try {
        emit('submit', formData.value)

        const scanData = {
          url: formData.value.target,
          scan_type: formData.value.profileId || 'full_scan'
        }

        const response = await awvsApi.startScan(scanData)

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
        profileId: 'full_scan'
      }
      errorMessage.value = ''
    }

    onMounted(() => {
    })

    return {
      formData,
      scanProfiles,
      isSubmitting,
      errorMessage,
      handleSubmit,
      handleReset
    }
  }
}
</script>

<style scoped>
.awvs-scan-form {
  max-width: 800px;
  margin: 0 auto;
  padding: var(--spacing-lg);
}

.awvs-scan-form h2 {
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
.form-group input[type="password"],
.form-group input[type="number"],
.form-group input[type="time"],
.form-group select {
  width: 100%;
  padding: var(--spacing-sm) var(--spacing-md);
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius);
  font-size: 1rem;
  transition: border-color 0.3s;
}

.form-group input:focus,
.form-group select:focus {
  outline: none;
  border-color: var(--color-primary);
}

.help-text {
  display: block;
  margin-top: var(--spacing-xs);
  font-size: 0.875rem;
  color: var(--text-secondary);
}

.crawler-config,
.login-config {
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
