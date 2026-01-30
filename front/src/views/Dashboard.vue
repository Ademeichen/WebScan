<template>
  <div class="dashboard">
    <div class="dashboard-header">
      <h1>仪表盘</h1>
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
          </div>
        </div>
      </div>

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
          </div>
        </div>
      </div>
    </div>

    <Alert
      v-if="errorMessage"
      type="error"
      :message="errorMessage"
      @close="errorMessage = ''"
    />
  </div>
</template>

<script>
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { tasksApi, settingsApi } from '@/utils/api'
import StatCard from '@/components/common/StatCard.vue'
import TaskCard from '@/components/business/TaskCard.vue'
import Loading from '@/components/common/Loading.vue'
import Alert from '@/components/common/Alert.vue'
import Chart from 'chart.js/auto'

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
      } catch {
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
        } catch {
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
      } catch {
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
    }
  }
}
</script>

<style scoped>
.dashboard {
  padding: var(--spacing-xl);
}

.dashboard-header {
  margin-bottom: var(--spacing-xl);
}

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
