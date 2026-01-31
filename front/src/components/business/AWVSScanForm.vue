<template>
  <el-card class="awvs-scan-form">
    <template #header>
      <h2>AWVS扫描配置</h2>
    </template>

    <el-form
      ref="formRef"
      :model="formData"
      :rules="rules"
      label-width="120px"
      @submit.prevent="handleSubmit"
    >
      <el-form-item label="扫描目标" prop="target">
        <el-input
          v-model="formData.target"
          placeholder="请输入URL"
          clearable
        >
          <template #prepend>
            <el-icon><Link /></el-icon>
          </template>
        </el-input>
        <template #help>
          支持URL格式：https://www.baidu.com 或 https://www.baidu.com
        </template>
      </el-form-item>

      <el-form-item label="扫描配置" prop="profileId">
        <el-select
          v-model="formData.profileId"
          placeholder="请选择扫描配置"
        >
          <el-option
            v-for="profile in scanProfiles"
            :key="profile.value"
            :label="profile.label"
            :value="profile.value"
          >
            <el-icon><Setting /></el-icon>
          </el-option>
        </el-select>
      </el-form-item>

      <el-form-item>
        <el-button
          type="info"
          @click="handleReset"
          :icon="RefreshLeft"
        >
          重置
        </el-button>
        <el-button
          type="primary"
          :loading="isSubmitting"
          @click="handleSubmit"
          :icon="Position"
        >
          {{ isSubmitting ? '提交中...' : '开始扫描' }}
        </el-button>
      </el-form-item>
    </el-form>

    <el-alert
      v-if="errorMessage"
      type="error"
      :title="errorMessage"
      :closable="true"
      @close="errorMessage = ''"
      style="margin-top: 16px"
    />
  </el-card>
</template>

<script>
import { ref, onMounted } from 'vue'
import { awvsApi } from '@/utils/api'
import { Link, Setting, RefreshLeft, Position } from '@element-plus/icons-vue'

export default {
  name: 'AWVSScanForm',
  components: {
    Link, Setting, RefreshLeft, Position
  },
  emits: ['submit', 'success', 'error'],
  setup(props, { emit }) {
    const formRef = ref(null)
    const formData = ref({
      target: '',
      profileId: 'full_scan'
    })

    const rules = ref({
      target: [
        { required: true, message: '请输入扫描目标', trigger: 'blur' }
      ],
      profileId: [
        { required: true, message: '请选择扫描配置', trigger: 'change' }
      ]
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
      if (!formRef.value) return

      try {
        await formRef.value.validate()
      } catch {
        return
      }

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
          ElMessage.success('扫描任务创建成功')
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
      formRef.value?.clearValidate()
    }

    onMounted(() => {
    })

    return {
      formRef,
      formData,
      rules,
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
}

.awvs-scan-form :deep(.el-card__header) {
  padding: var(--spacing-lg);
  border-bottom: 1px solid var(--el-border-color-light);
}

.awvs-scan-form :deep(.el-card__body) {
  padding: var(--spacing-xl);
}

.awvs-scan-form h2 {
  margin: 0;
  font-size: 18px;
  color: var(--el-text-color-primary);
  font-weight: 600;
}
</style>
