import { createRouter, createWebHistory } from 'vue-router'
import Dashboard from '../views/Dashboard.vue'
import ScanTasks from '../views/ScanTasks.vue'
import POCScan from '../views/POCScan.vue'
import VulnerabilityResults from '../views/VulnerabilityResults.vue'
import VulnerabilityDetail from '../views/VulnerabilityDetail.vue'
import Reports from '../views/Reports.vue'
import ReportDetail from '../views/ReportDetail.vue'
import Settings from '../views/Settings.vue'
import AWVSScan from '../views/AWVSScan.vue'
import AgentScan from '../views/AgentScan.vue'
import NotFound from '../views/NotFound.vue'

const routes = [
  {
    path: '/',
    name: 'Dashboard',
    component: Dashboard,
    meta: {
      title: '仪表盘',
      requiresAuth: false
    }
  },
  {
    path: '/scan-tasks',
    name: 'ScanTasks',
    component: ScanTasks,
    meta: {
      title: '扫描任务',
      requiresAuth: false
    }
  },
  {
    path: '/poc-scan',
    name: 'POCScan',
    component: POCScan,
    meta: {
      title: 'POC扫描',
      requiresAuth: false
    }
  },
  {
    path: '/vulnerabilities/:taskId',
    name: 'VulnerabilityResults',
    component: VulnerabilityResults,
    props: true,
    meta: {
      title: '漏洞结果',
      requiresAuth: false
    }
  },
  {
    path: '/vulnerability/:id',
    name: 'VulnerabilityDetail',
    component: VulnerabilityDetail,
    props: true,
    meta: {
      title: '漏洞详情',
      requiresAuth: false
    }
  },
  {
    path: '/reports',
    name: 'Reports',
    component: Reports,
    meta: {
      title: '报告',
      requiresAuth: false
    }
  },
  {
    path: '/report-detail',
    name: 'ReportDetail',
    component: ReportDetail,
    meta: {
      title: '报告详情',
      requiresAuth: false
    }
  },
  {
    path: '/settings',
    name: 'Settings',
    component: Settings,
    meta: {
      title: '系统设置',
      requiresAuth: false
    }
  },
  {
    path: '/awvs-scan',
    name: 'AWVSScan',
    component: AWVSScan,
    meta: {
      title: 'AWVS扫描',
      requiresAuth: false
    }
  },
  {
    path: '/agent-scan',
    name: 'AgentScan',
    component: AgentScan,
    meta: {
      title: 'AI Agent扫描',
      requiresAuth: false
    }
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: NotFound,
    meta: {
      title: '页面未找到'
    }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior(to, from, savedPosition) {
    if (savedPosition) {
      return savedPosition
    } else {
      return { top: 0 }
    }
  }
})

router.beforeEach((to, from, next) => {
  document.title = `${to.meta.title || 'WebScan AI'} - WebScan AI`
  
  const isAuthenticated = localStorage.getItem('isAuthenticated') === 'true'
  
  if (to.meta.requiresAuth && !isAuthenticated) {
    next({
      name: 'Dashboard',
      query: { redirect: to.fullPath }
    })
  } else {
    next()
  }
})

router.afterEach(() => {
  window.scrollTo(0, 0)
})

export default router
