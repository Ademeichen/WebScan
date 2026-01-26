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
        <small class="help-text">支持URL格式：http://example.com 或 https://example.com</small>
      </div>

      <div class="form-group">
        <label for="taskName">任务名称 *</label>
        <input
          id="taskName"
          v-model="formData.taskName"
          type="text"
          placeholder="请输入任务名称"
          required
        />
      </div>

      <div class="form-group">
        <label for="profileId">扫描配置 *</label>
        <select id="profileId" v-model="formData.profileId" required>
          <option value="">请选择扫描配置</option>
          <option
            v-for="profile in scanProfiles"
            :key="profile.value"
            :value="profile.value"
          >
            {{ profile.label }}
          </option>
        </select>
      </div>

      <div class="form-group">
        <label for="scanSpeed">扫描速度</label>
        <select id="scanSpeed" v-model="formData.scanSpeed">
          <option value="slow">慢速（更准确，耗时更长）</option>
          <option value="sequential">顺序</option>
          <option value="fast">快速（可能遗漏，耗时更短）</option>
        </select>
      </div>

      <div class="form-group">
        <label for="schedule">扫描计划</label>
        <select id="schedule" v-model="formData.schedule">
          <option value="immediate">立即扫描</option>
          <option value="daily">每天</option>
          <option value="weekly">每周</option>
          <option value="monthly">每月</option>
        </select>
      </div>

      <div v-if="formData.schedule !== 'immediate'" class="form-group">
        <label for="scheduleTime">扫描时间</label>
        <input
          id="scheduleTime"
          v-model="formData.scheduleTime"
          type="time"
        />
      </div>

      <div class="form-group">
        <label>
          <input v-model="formData.enableCrawler" type="checkbox" />
          <span>启用爬虫</span>
        </label>
      </div>

      <div v-if="formData.enableCrawler" class="form-group crawler-config">
        <label for="crawlerDepth">爬虫深度</label>
        <input
          id="crawlerDepth"
          v-model.number="formData.crawlerDepth"
          type="number"
          min="1"
          max="10"
          placeholder="3"
        />
        <small class="help-text">爬虫深度越大，扫描时间越长</small>
      </div>

      <div class="form-group">
        <label>
          <input v-model="formData.enableLogin" type="checkbox" />
          <span>启用登录</span>
        </label>
      </div>

      <div v-if="formData.enableLogin" class="form-group login-config">
        <div class="form-group">
          <label for="loginUrl">登录URL</label>
          <input
            id="loginUrl"
            v-model="formData.loginUrl"
            type="text"
            placeholder="http://example.com/login"
          />
        </div>
        <div class="form-group">
          <label for="username">用户名</label>
          <input
            id="username"
            v-model="formData.username"
            type="text"
            placeholder="请输入用户名"
          />
        </div>
        <div class="form-group">
          <label for="password">密码</label>
          <input
            id="password"
            v-model="formData.password"
            type="password"
            placeholder="请输入密码"
          />
        </div>
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
      taskName: '',
      profileId: '',
      scanSpeed: 'sequential',
      schedule: 'immediate',
      scheduleTime: '00:00',
      enableCrawler: false,
      crawlerDepth: 3,
      enableLogin: false,
      loginUrl: '',
      username: '',
      password: ''
    })

    const scanProfiles = ref([
      { value: '11111111-1111-1111-1111-111111111111', label: 'Full Scan' },
      { value: '11111111-1111-1111-1111-111111111112', label: 'High Risk Vulnerabilities' },
      { value: '11111111-1111-1111-1111-111111111113', label: 'Cross-site Scripting (XSS)' },
      { value: '11111111-1111-1111-1111-111111111114', label: 'SQL Injection' },
      { value: '11111111-1111-1111-1111-111111111115', label: 'Crawl Only' },
      { value: '11111111-1111-1111-1111-111111111116', label: 'Malware Scan' }
    ])

    const isSubmitting = ref(false)
    const errorMessage = ref('')

    const loadTargets = async () => {
      try {
        const response = await awvsApi.getTargets()
        console.log('AWVS Targets:', response)
      } catch (error) {
        console.error('加载AWVS目标失败:', error)
      }
    }

    const handleSubmit = async () => {
      if (isSubmitting.value) return

      isSubmitting.value = true
      errorMessage.value = ''

      try {
        emit('submit', formData.value)

        const taskData = {
          task_name: formData.value.taskName,
          target: formData.value.target,
          task_type: 'awvs_scan',
          config: {
            profile_id: formData.value.profileId,
            scan_speed: formData.value.scanSpeed,
            schedule: formData.value.schedule,
            schedule_time: formData.value.scheduleTime,
            enable_crawler: formData.value.enableCrawler,
            crawler_depth: formData.value.crawlerDepth,
            enable_login: formData.value.enableLogin,
            login_url: formData.value.loginUrl,
            username: formData.value.username,
            password: formData.value.password
          }
        }

        const response = await awvsApi.startScan(taskData)

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
        profileId: '',
        scanSpeed: 'sequential',
        schedule: 'immediate',
        scheduleTime: '00:00',
        enableCrawler: false,
        crawlerDepth: 3,
        enableLogin: false,
        loginUrl: '',
        username: '',
        password: ''
      }
      errorMessage.value = ''
    }

    onMounted(() => {
      loadTargets()
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
