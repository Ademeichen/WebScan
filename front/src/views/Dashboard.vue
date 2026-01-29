<template>
  <div class="dashboard">
    <div class="dashboard-header">
      <h1>仪表盘</h1>
<<<<<<< HEAD
      <p class="subtitle">实时监控安全扫描状态</p>
    </div>

    <div v-if="loading" class="loading-container">
      <Loading text="加载数据中..." />
    </div>

    <div v-else class="dashboard-content">
      <div class="stats-grid">
        <StatCard
          title="今日扫描"
          :value="statistics.today_scans || 0"
          icon="🔍"
          color="primary"
        />
        <StatCard
          title="高危漏洞"
          :value="statistics.high_risk_vulns || 0"
          icon="⚠️"
          color="error"
        />
        <StatCard
          title="已完成扫描"
          :value="statistics.completed_scans || 0"
          icon="✅"
          color="success"
        />
        <StatCard
          title="失败扫描"
          :value="statistics.failed_scans || 0"
          icon="❌"
          color="warning"
        />
        <StatCard
          title="总漏洞数"
          :value="statistics.total_vulns || 0"
          icon="🐛"
          color="info"
        />
        <StatCard
          title="总报告数"
          :value="statistics.total_reports || 0"
          icon="📊"
          color="secondary"
        />
      </div>

      <div class="charts-section">
        <div class="chart-card">
          <h3>漏洞趋势</h3>
          <div class="chart-container">
            <canvas ref="trendChart"></canvas>
          </div>
        </div>

        <div class="chart-card">
          <h3>漏洞分布</h3>
          <div class="chart-container">
            <canvas ref="distributionChart"></canvas>
=======
      <p class="dashboard-subtitle">Web应用漏洞扫描概览</p>
    </div>

      <!-- 核心数据卡片 -->
    <div class="stats-grid">
      <div class="stat-card stat-card-primary">
        <div class="stat-icon">🔍</div>
        <div class="stat-content">
          <div class="stat-number">{{ todayScans }}</div>
          <div class="stat-label">今日扫描任务</div>
        </div>
      </div>

      <div class="stat-card stat-card-trend" :class="trendClass">
        <div class="stat-icon">📈</div>
        <div class="stat-content">
          <div class="stat-number">{{ weeklyTrend }}%</div>
          <div class="stat-label">本周漏洞趋势</div>
        </div>
      </div>

      <div class="stat-card stat-card-success">
        <div class="stat-icon">✅</div>
        <div class="stat-content">
          <div class="stat-number">{{ completedScans }}</div>
          <div class="stat-label">已完成扫描</div>
        </div>
      </div>
    </div>

    <div class="dashboard-content">
      <!-- 漏洞趋势图 -->
      <div class="chart-section">
        <div class="card">
          <div class="card-header">
            <h3 class="card-title">漏洞趋势分析</h3>
            <select v-model="trendPeriod" class="form-select" style="width: auto;">
              <option value="7">最近7天</option>
              <option value="30">最近30天</option>
              <option value="90">最近90天</option>
            </select>
          </div>
          <div class="chart-container">
            <div class="trend-chart">
              <div class="chart-legend">
                <div class="legend-item">
                  <span class="legend-color high-risk"></span>
                  <span>高危漏洞</span>
                </div>
                <div class="legend-item">
                  <span class="legend-color medium-risk"></span>
                  <span>中危漏洞</span>
                </div>
                <div class="legend-item">
                  <span class="legend-color low-risk"></span>
                  <span>低危漏洞</span>
                </div>
              </div>
              <div class="chart-area">
                <div v-for="(day, index) in trendData" :key="index" class="chart-bar">
                  <div class="bar-stack">
                    <div 
                      class="bar-segment high-risk" 
                      :style="{ height: (day.high / maxVulns * 100) + '%' }"
                      :title="`高危: ${day.high}`"
                    ></div>
                    <div 
                      class="bar-segment medium-risk" 
                      :style="{ height: (day.medium / maxVulns * 100) + '%' }"
                      :title="`中危: ${day.medium}`"
                    ></div>
                    <div 
                      class="bar-segment low-risk" 
                      :style="{ height: (day.low / maxVulns * 100) + '%' }"
                      :title="`低危: ${day.low}`"
                    ></div>
                  </div>
                  <div class="bar-label">{{ day.date }}</div>
                </div>
              </div>
            </div>
>>>>>>> de97d03d8b5dfa00af0eaddf983e9c20433e9b15
          </div>
        </div>
      </div>

<<<<<<< HEAD
      <div class="recent-tasks-section">
        <div class="section-header">
          <h3>最近任务</h3>
          <router-link to="/scan-tasks" class="view-all">查看全部</router-link>
        </div>
        <div v-if="recentTasks.length === 0" class="empty-state">
          <p>暂无任务数据</p>
        </div>
        <div v-else class="tasks-list">
          <TaskCard
            v-for="task in recentTasks"
            :key="task.id"
            :task="task"
            @cancel="handleCancelTask"
            @view="handleViewTask"
            @report="handleGenerateReport"
            @delete="handleDeleteTask"
          />
        </div>
      </div>

      <div class="system-info-section">
        <div class="section-header">
          <h3>系统信息</h3>
          <button class="btn-refresh" @click="loadSystemInfo">
            🔄 刷新
          </button>
        </div>
        <div v-if="systemInfo" class="system-info-grid">
          <div class="info-card">
            <h4>系统版本</h4>
            <p>{{ systemInfo.version }}</p>
          </div>
          <div class="info-card">
            <h4>运行时间</h4>
            <p>{{ systemInfo.uptime }}</p>
          </div>
          <div class="info-card">
            <h4>CPU使用率</h4>
            <p>{{ systemInfo.resources?.cpu?.usage || 'N/A' }}</p>
          </div>
          <div class="info-card">
            <h4>内存使用率</h4>
            <p>{{ systemInfo.resources?.memory?.usage || 'N/A' }}</p>
          </div>
          <div class="info-card">
            <h4>磁盘使用率</h4>
            <p>{{ systemInfo.resources?.disk?.usage || 'N/A' }}</p>
          </div>
          <div class="info-card">
            <h4>进程数</h4>
            <p>{{ systemInfo.processes?.count || 'N/A' }}</p>
=======
      <!-- 最新扫描结果 -->
      <div class="recent-scans">
        <div class="card">
          <div class="card-header">
            <h3 class="card-title">最新扫描结果</h3>
            <router-link to="/scan-tasks" class="btn btn-outline">查看全部</router-link>
          </div>
          <div class="scan-list">
            <div 
              v-for="scan in recentScans" 
              :key="scan.id" 
              class="scan-item"
              @click="viewScanResults(scan.id)"
            >
              <div class="scan-info">
                <div class="scan-name">{{ scan.name }}</div>
                <div class="scan-url">{{ scan.url }}</div>
                <div class="scan-time">{{ scan.time }}</div>
              </div>
              <div class="scan-status">
                <span :class="['status', `status-${scan.status}`]">
                  <span class="status-dot"></span>
                  {{ getStatusText(scan.status) }}
                </span>
              </div>
              <div class="scan-results">
                <div v-if="scan.vulnerabilities" class="vuln-summary">
                  <span class="vuln-count critical-risk" v-if="scan.vulnerabilities.critical > 0">{{ scan.vulnerabilities.critical }}</span>
                  <span class="vuln-count high-risk">{{ scan.vulnerabilities.high }}</span>
                  <span class="vuln-count medium-risk">{{ scan.vulnerabilities.medium }}</span>
                  <span class="vuln-count low-risk">{{ scan.vulnerabilities.low }}</span>
                </div>
              </div>
            </div>
>>>>>>> de97d03d8b5dfa00af0eaddf983e9c20433e9b15
          </div>
        </div>
      </div>
    </div>

<<<<<<< HEAD
    <Alert
      v-if="errorMessage"
      type="error"
      :message="errorMessage"
      @close="errorMessage = ''"
    />
=======
    <!-- 快速操作 -->
    <div class="quick-actions">
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">快速操作</h3>
        </div>
        <div class="actions-grid">
          <router-link to="/scan-tasks" class="action-item">
            <div class="action-icon">🚀</div>
            <div class="action-text">创建扫描任务</div>
          </router-link>
          <router-link to="/reports" class="action-item">
            <div class="action-icon">📊</div>
            <div class="action-text">生成报告</div>
          </router-link>
          <router-link to="/settings" class="action-item">
            <div class="action-icon">⚙️</div>
            <div class="action-text">系统设置</div>
          </router-link>
        </div>
      </div>
    </div>
>>>>>>> de97d03d8b5dfa00af0eaddf983e9c20433e9b15
  </div>
</template>

<script>
<<<<<<< HEAD
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { tasksApi, settingsApi } from '@/utils/api'
import StatCard from '@/components/common/StatCard.vue'
import TaskCard from '@/components/business/TaskCard.vue'
import Loading from '@/components/common/Loading.vue'
import Alert from '@/components/common/Alert.vue'

export default {
  name: 'Dashboard',
  components: {
    StatCard,
    TaskCard,
    Loading,
    Alert
  },
  setup() {
    const router = useRouter()
    const loading = ref(true)
    const errorMessage = ref('')
    const statistics = ref({})
    const recentTasks = ref([])
    const systemInfo = ref(null)
    const trendChart = ref(null)
    const distributionChart = ref(null)
    let chartInstances = null

    const loadStatistics = async () => {
      try {
        const response = await settingsApi.getStatistics(7)
        if (response.code === 200) {
          statistics.value = response.data
        }
      } catch (error) {
        console.error('加载统计数据失败:', error)
      }
    }

    const loadRecentTasks = async () => {
      try {
        const response = await tasksApi.getTasks({ limit: 5 })
        if (response.code === 200) {
          recentTasks.value = response.data.tasks || []
        }
      } catch (error) {
        console.error('加载最近任务失败:', error)
      }
    }

    const loadSystemInfo = async () => {
      try {
        const response = await settingsApi.getSystemInfo()
        if (response.code === 200) {
          systemInfo.value = response.data
        }
      } catch (error) {
        console.error('加载系统信息失败:', error)
        errorMessage.value = '加载系统信息失败'
      }
    }

    const initCharts = () => {
      nextTick(() => {
        if (typeof Chart === 'undefined') {
          console.warn('Chart.js未加载，跳过图表初始化')
          return
        }

        if (trendChart.value && statistics.value.trend_data) {
          const ctx = trendChart.value.getContext('2d')
          chartInstances = chartInstances || {}
          chartInstances.trend = new Chart(ctx, {
            type: 'line',
            data: {
              labels: statistics.value.trend_data.map(d => d.date),
              datasets: [
                {
                  label: '高危',
                  data: statistics.value.trend_data.map(d => d.high),
                  borderColor: '#e74c3c',
                  backgroundColor: 'rgba(231, 76, 60, 0.1)',
                  fill: true,
                  tension: 0.4
                },
                {
                  label: '中危',
                  data: statistics.value.trend_data.map(d => d.medium),
                  borderColor: '#f39c12',
                  backgroundColor: 'rgba(243, 156, 18, 0.1)',
                  fill: true,
                  tension: 0.4
                },
                {
                  label: '低危',
                  data: statistics.value.trend_data.map(d => d.low),
                  borderColor: '#3498db',
                  backgroundColor: 'rgba(52, 152, 219, 0.1)',
                  fill: true,
                  tension: 0.4
                }
              ]
            },
            options: {
              responsive: true,
              maintainAspectRatio: false,
              plugins: {
                legend: {
                  position: 'top'
                }
              },
              scales: {
                y: {
                  beginAtZero: true
                }
              }
            }
          })
        }

        if (distributionChart.value && statistics.value.severity_distribution) {
          const ctx = distributionChart.value.getContext('2d')
          chartInstances = chartInstances || {}
          chartInstances.distribution = new Chart(ctx, {
            type: 'doughnut',
            data: {
              labels: ['严重', '高危', '中危', '低危', '信息'],
              datasets: [{
                data: [
                  statistics.value.severity_distribution.critical || 0,
                  statistics.value.severity_distribution.high || 0,
                  statistics.value.severity_distribution.medium || 0,
                  statistics.value.severity_distribution.low || 0,
                  statistics.value.severity_distribution.info || 0
                ],
                backgroundColor: [
                  '#c0392b',
                  '#e74c3c',
                  '#f39c12',
                  '#3498db',
                  '#95a5a6'
                ]
              }]
            },
            options: {
              responsive: true,
              maintainAspectRatio: false,
              plugins: {
                legend: {
                  position: 'right'
                }
              }
            }
          })
        }
      })
    }

    const handleCancelTask = async (taskId) => {
      try {
        await tasksApi.cancelTask(taskId)
        await loadRecentTasks()
      } catch (error) {
        errorMessage.value = '取消任务失败'
      }
    }

    const handleViewTask = (taskId) => {
      router.push(`/scan-tasks?task=${taskId}`)
    }

    const handleGenerateReport = async (taskId) => {
      router.push(`/reports?task=${taskId}`)
    }

    const handleDeleteTask = async (taskId) => {
      if (confirm('确定要删除此任务吗？')) {
        try {
          await tasksApi.deleteTask(taskId)
          await loadRecentTasks()
        } catch (error) {
          errorMessage.value = '删除任务失败'
        }
      }
    }

    const loadData = async () => {
      loading.value = true
      try {
        await Promise.all([
          loadStatistics(),
          loadRecentTasks(),
          loadSystemInfo()
        ])
        await nextTick()
        initCharts()
      } catch (error) {
        errorMessage.value = '加载数据失败'
      } finally {
        loading.value = false
      }
    }

    onMounted(() => {
      loadData()
    })

    onUnmounted(() => {
      if (chartInstances) {
        if (chartInstances.trend) {
          chartInstances.trend.destroy()
        }
        if (chartInstances.distribution) {
          chartInstances.distribution.destroy()
        }
      }
    })

    return {
      loading,
      errorMessage,
      statistics,
      recentTasks,
      systemInfo,
      trendChart,
      distributionChart,
      handleCancelTask,
      handleViewTask,
      handleGenerateReport,
      handleDeleteTask,
      loadSystemInfo
=======
import { settingsApi, taskApi } from '../utils/api.js'

export default {
  name: 'Dashboard',
  data() {
    return {
      // 仪表盘统计数据
      todayScans: 0,
      highRiskVulns: 0,
      weeklyTrend: 0,
      completedScans: 0,
      
      trendPeriod: '7',
      trendData: [],
      
      recentScans: [],
      
      // 加载状态
      loading: false,
      error: null
    }
  },
  computed: {
    trendClass() {
      return this.weeklyTrend > 0 ? 'trend-up' : 'trend-down'
    },
    maxVulns() {
      if (this.trendData.length === 0) return 1
      return Math.max(...this.trendData.map(day => day.high + day.medium + day.low), 1)
    }
  },
  async mounted() {
    await this.loadDashboardData()
  },
  methods: {
    async loadDashboardData() {
      this.loading = true
      this.error = null
      
      try {
        // 并行加载所有数据
        await Promise.all([
          this.loadStats(),
          this.loadTrendData(),
          this.loadRecentScans()
        ])
      } catch (error) {
        console.error('加载仪表盘数据失败:', error)
        this.error = '加载数据失败，请稍后重试'
      } finally {
        this.loading = false
      }
    },
    async loadStats() {
      try {
        const response = await settingsApi.getStatistics()
        if (response && response.data) {
          const stats = response.data
          this.todayScans = stats.today_scans || 0
          this.highRiskVulns = stats.high_risk_vulns || 0
          this.weeklyTrend = stats.weekly_trend || 0
          this.completedScans = stats.completed_scans || 0
        }
      } catch (error) {
        console.error('加载统计数据失败:', error)
        // 设置默认值
        this.todayScans = 0
        this.highRiskVulns = 0
        this.weeklyTrend = 0
        this.completedScans = 0
      }
    },
    async loadTrendData() {
      try {
        const response = await settingsApi.getStatistics({ period: this.trendPeriod })
        if (response && response.data && response.data.trend_data) {
          this.trendData = response.data.trend_data
        } else {
          // 生成默认的空数据
          this.trendData = this.generateDefaultTrendData()
        }
      } catch (error) {
        console.error('加载趋势数据失败:', error)
        this.trendData = this.generateDefaultTrendData()
      }
    },
    async loadRecentScans() {
      try {
        const response = await taskApi.list({ limit: 4, sort: '-created_at' })
        if (response && response.data && response.data.tasks) {
          this.recentScans = response.data.tasks.map(task => ({
            id: task.id,
            name: task.task_name || `扫描任务 ${task.id}`,
            url: task.target || '-',
            time: this.formatTime(task.created_at),
            status: this.mapTaskStatus(task.status),
            vulnerabilities: task.result?.vulnerabilities || {
              critical: 0,
              high: 0,
              medium: 0,
              low: 0,
              info: 0
            }
          }))
        } else {
          this.recentScans = []
        }
      } catch (error) {
        console.error('加载最近扫描失败:', error)
        this.recentScans = []
      }
    },
    generateDefaultTrendData() {
      const days = []
      const today = new Date()
      
      for (let i = parseInt(this.trendPeriod) - 1; i >= 0; i--) {
        const date = new Date(today)
        date.setDate(date.getDate() - i)
        days.push({
          date: `${date.getMonth() + 1}/${date.getDate()}`,
          high: 0,
          medium: 0,
          low: 0
        })
      }
      
      return days
    },
    mapTaskStatus(status) {
      const statusMap = {
        'pending': 'waiting',
        'running': 'running',
        'completed': 'completed',
        'failed': 'failed'
      }
      return statusMap[status] || status
    },
    getStatusText(status) {
      const statusMap = {
        waiting: '等待中',
        running: '进行中',
        completed: '已完成',
        failed: '失败'
      }
      return statusMap[status] || status
    },
    formatTime(timestamp) {
      if (!timestamp) return '-'
      const date = new Date(timestamp)
      const now = new Date()
      const diff = now - date
      
      if (diff < 60000) {
        return '刚刚'
      } else if (diff < 3600000) {
        return `${Math.floor(diff / 60000)}分钟前`
      } else if (diff < 86400000) {
        return `${Math.floor(diff / 3600000)}小时前`
      } else {
        return date.toLocaleDateString('zh-CN')
      }
    },
    viewScanResults(scanId) {
      // Check if the scanId is an integer (regular scan) or UUID (AWVS scan)
      if (typeof scanId === 'string' && scanId.length > 10) {
          // Likely a UUID, navigate to AWVS scan details or handle accordingly
          // Assuming AWVS scans might be viewed in the same component or a different one
          // If AWVS scans are stored in tasks table with a specific ID format
           this.$router.push(`/vulnerabilities/${scanId}`)
      } else {
           this.$router.push(`/vulnerabilities/${scanId}`)
      }
    }
  },
  watch: {
    trendPeriod() {
      this.loadTrendData()
>>>>>>> de97d03d8b5dfa00af0eaddf983e9c20433e9b15
    }
  }
}
</script>

<style scoped>
.dashboard {
<<<<<<< HEAD
  padding: var(--spacing-xl);
=======
  max-width: 1200px;
  margin: 0 auto;
>>>>>>> de97d03d8b5dfa00af0eaddf983e9c20433e9b15
}

.dashboard-header {
  margin-bottom: var(--spacing-xl);
}

<<<<<<< HEAD
.dashboard-header h1 {
  margin: 0 0 var(--spacing-sm) 0;
  font-size: 2rem;
  color: var(--text-primary);
}

.subtitle {
  margin: 0;
  color: var(--text-secondary);
  font-size: 1rem;
}

.loading-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 400px;
}

.dashboard-content {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xl);
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: var(--spacing-lg);
}

.charts-section {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
  gap: var(--spacing-lg);
}

.chart-card {
  background-color: var(--card-bg);
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius-lg);
  padding: var(--spacing-lg);
}

.chart-card h3 {
  margin: 0 0 var(--spacing-md) 0;
  font-size: 1.125rem;
  color: var(--text-primary);
}

.chart-container {
  height: 300px;
}

.recent-tasks-section,
.system-info-section {
  background-color: var(--card-bg);
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius-lg);
  padding: var(--spacing-lg);
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-lg);
}

.section-header h3 {
  margin: 0;
  font-size: 1.25rem;
  color: var(--text-primary);
}

.view-all {
  color: var(--color-primary);
  text-decoration: none;
  font-weight: 500;
  transition: color 0.3s;
}

.view-all:hover {
  color: var(--color-primary-dark);
}

.empty-state {
  text-align: center;
  padding: var(--spacing-xl);
  color: var(--text-secondary);
}

.tasks-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.system-info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: var(--spacing-md);
}

.info-card {
  background-color: var(--bg-secondary);
  border-radius: var(--border-radius);
  padding: var(--spacing-md);
}

.info-card h4 {
  margin: 0 0 var(--spacing-sm) 0;
  font-size: 0.875rem;
  color: var(--text-secondary);
  font-weight: 500;
}

.info-card p {
  margin: 0;
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--text-primary);
}

.btn-refresh {
  padding: var(--spacing-sm) var(--spacing-md);
  background-color: var(--color-primary);
  color: white;
  border: none;
  border-radius: var(--border-radius);
  cursor: pointer;
  transition: all 0.3s;
}

.btn-refresh:hover {
  background-color: var(--color-primary-dark);
}
</style>
=======
.dashboard-subtitle {
  color: var(--text-secondary);
  margin-top: var(--spacing-xs);
}

/* 统计卡片网格 */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: var(--spacing-md);
  margin-bottom: var(--spacing-xl);
}

.stat-card {
  background-color: var(--card-background);
  border-radius: var(--border-radius);
  padding: var(--spacing-lg);
  box-shadow: var(--shadow-sm);
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  transition: all 0.2s ease;
  border-left: 4px solid transparent;
}

.stat-card:hover {
  box-shadow: var(--shadow-md);
  transform: translateY(-2px);
}

.stat-card-primary {
  border-left-color: var(--secondary-color);
}

.stat-card-danger {
  border-left-color: var(--high-risk);
}

.stat-card-success {
  border-left-color: var(--success-color);
}

.stat-card-trend.trend-up {
  border-left-color: var(--success-color);
}

.stat-card-trend.trend-down {
  border-left-color: var(--high-risk);
}

.stat-icon {
  font-size: 32px;
  opacity: 0.8;
}

.stat-number {
  font-size: 28px;
  font-weight: bold;
  color: var(--text-primary);
  line-height: 1;
}

.stat-label {
  color: var(--text-secondary);
  font-size: 14px;
  margin-top: var(--spacing-xs);
}

/* 仪表盘内容布局 */
.dashboard-content {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: var(--spacing-lg);
  margin-bottom: var(--spacing-xl);
}

/* 趋势图 */
.chart-container {
  padding: var(--spacing-md) 0;
}

.chart-legend {
  display: flex;
  gap: var(--spacing-lg);
  margin-bottom: var(--spacing-md);
}

.legend-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  font-size: 12px;
}

.legend-color {
  width: 12px;
  height: 12px;
  border-radius: 2px;
}

.legend-color.high-risk {
  background-color: var(--high-risk);
}

.legend-color.medium-risk {
  background-color: var(--medium-risk);
}

.legend-color.low-risk {
  background-color: var(--low-risk);
}

.chart-area {
  display: flex;
  align-items: end;
  gap: var(--spacing-sm);
  height: 200px;
  padding: var(--spacing-md) 0;
}

.chart-bar {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  height: 100%;
}

.bar-stack {
  display: flex;
  flex-direction: column-reverse;
  width: 100%;
  height: 180px;
  border-radius: var(--border-radius);
  overflow: hidden;
}

.bar-segment {
  width: 100%;
  min-height: 2px;
  cursor: pointer;
  transition: opacity 0.2s ease;
}

.bar-segment:hover {
  opacity: 0.8;
}

.bar-segment.high-risk {
  background-color: var(--high-risk);
}

.bar-segment.medium-risk {
  background-color: var(--medium-risk);
}

.bar-segment.low-risk {
  background-color: var(--low-risk);
}

.bar-label {
  font-size: 11px;
  color: var(--text-secondary);
  margin-top: var(--spacing-xs);
}

/* 扫描列表 */
.scan-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.scan-item {
  display: flex;
  align-items: center;
  padding: var(--spacing-md);
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius);
  cursor: pointer;
  transition: all 0.2s ease;
}

.scan-item:hover {
  background-color: var(--background-color);
  border-color: var(--secondary-color);
}

.scan-info {
  flex: 1;
}

.scan-name {
  font-weight: bold;
  color: var(--text-primary);
  margin-bottom: var(--spacing-xs);
}

.scan-url {
  color: var(--text-secondary);
  font-size: 12px;
  margin-bottom: var(--spacing-xs);
}

.scan-time {
  color: var(--text-secondary);
  font-size: 11px;
}

.scan-status {
  margin: 0 var(--spacing-md);
}

.status-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  display: inline-block;
  margin-right: var(--spacing-xs);
}

.status-waiting .status-dot {
  background-color: var(--secondary-color);
}

.status-running .status-dot {
  background-color: var(--secondary-color);
  animation: pulse 1.5s infinite;
}

.status-completed .status-dot {
  background-color: var(--success-color);
}

.status-failed .status-dot {
  background-color: var(--high-risk);
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.vuln-summary {
  display: flex;
  gap: var(--spacing-xs);
}

.vuln-count {
  padding: 2px var(--spacing-xs);
  border-radius: 10px;
  font-size: 11px;
  font-weight: bold;
  min-width: 20px;
  text-align: center;
}

.vuln-count.critical-risk {
  background-color: rgba(139, 0, 0, 0.1);
  color: #8B0000;
}

.vuln-count.high-risk {
  background-color: rgba(231, 76, 60, 0.1);
  color: var(--high-risk);
}

.vuln-count.medium-risk {
  background-color: rgba(245, 166, 35, 0.1);
  color: var(--medium-risk);
}

.vuln-count.low-risk {
  background-color: rgba(241, 196, 15, 0.1);
  color: var(--low-risk);
}

/* 快速操作 */
.quick-actions {
  margin-bottom: var(--spacing-xl);
}

.actions-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: var(--spacing-md);
}

.action-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: var(--spacing-lg);
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius);
  text-decoration: none;
  color: var(--text-primary);
  transition: all 0.2s ease;
}

.action-item:hover {
  background-color: var(--background-color);
  border-color: var(--secondary-color);
  transform: translateY(-2px);
}

.action-icon {
  font-size: 32px;
  margin-bottom: var(--spacing-sm);
}

.action-text {
  font-weight: 500;
  text-align: center;
}

/* 响应式设计 - 平板设备 */
@media (max-width: 1024px) {
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .dashboard-content {
    grid-template-columns: 1fr;
  }
  
  .chart-area {
    height: 180px;
  }
  
  .bar-stack {
    height: 160px;
  }
}

/* 响应式设计 - 手机设备 */
@media (max-width: 768px) {
  .dashboard-header {
    flex-direction: column;
    align-items: flex-start;
    gap: var(--spacing-sm);
  }
  
  .period-selector {
    width: 100%;
  }
  
  .stats-grid {
    grid-template-columns: 1fr;
  }
  
  .stat-card {
    padding: var(--spacing-md);
  }
  
  .dashboard-content {
    grid-template-columns: 1fr;
    gap: var(--spacing-md);
  }
  
  .chart-area {
    height: 150px;
  }
  
  .bar-stack {
    height: 130px;
  }
  
  .bar-label {
    font-size: 10px;
  }
  
  .scan-item {
    flex-direction: column;
    align-items: flex-start;
    gap: var(--spacing-sm);
    padding: var(--spacing-sm);
  }
  
  .scan-status {
    margin: 0;
    align-self: flex-end;
  }
  
  .actions-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .action-item {
    padding: var(--spacing-md);
  }
  
  .action-icon {
    font-size: 28px;
  }
  
  .action-text {
    font-size: 13px;
  }
}

/* 响应式设计 - 小屏手机 */
@media (max-width: 480px) {
  .stat-card {
    padding: var(--spacing-sm);
  }
  
  .stat-value {
    font-size: 24px;
  }
  
  .stat-label {
    font-size: 12px;
  }
  
  .chart-legend {
    flex-wrap: wrap;
    gap: var(--spacing-sm);
  }
  
  .legend-item {
    font-size: 11px;
  }
  
  .chart-area {
    height: 120px;
  }
  
  .bar-stack {
    height: 100px;
  }
  
  .bar-label {
    font-size: 9px;
  }
  
  .scan-item {
    padding: var(--spacing-xs) var(--spacing-sm);
  }
  
  .scan-name {
    font-size: 14px;
  }
  
  .scan-url {
    font-size: 11px;
  }
  
  .vuln-count {
    font-size: 10px;
    padding: 1px 4px;
    min-width: 16px;
  }
  
  .actions-grid {
    grid-template-columns: 1fr;
  }
  
  .action-item {
    padding: var(--spacing-sm);
  }
  
  .action-icon {
    font-size: 24px;
  }
  
  .action-text {
    font-size: 12px;
  }
}

/* 响应式设计 - 超小屏设备 */
@media (max-width: 360px) {
  .stat-value {
    font-size: 20px;
  }
  
  .stat-label {
    font-size: 11px;
  }
  
  .chart-area {
    height: 100px;
  }
  
  .bar-stack {
    height: 80px;
  }
  
  .legend-color {
    width: 10px;
    height: 10px;
  }
  
  .action-icon {
    font-size: 20px;
  }
}

</style>


>>>>>>> de97d03d8b5dfa00af0eaddf983e9c20433e9b15
