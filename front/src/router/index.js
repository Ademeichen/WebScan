import { createRouter, createWebHistory } from 'vue-router'
import Dashboard from '../views/Dashboard.vue'
import ScanTasks from '../views/ScanTasks.vue'
import POCScan from '../views/POCScan.vue'
import VulnerabilityResults from '../views/VulnerabilityResults.vue'
import VulnerabilityDetail from '../views/VulnerabilityDetail.vue'
import Reports from '../views/Reports.vue'
import Settings from '../views/Settings.vue'
import AWVSScan from '../views/AWVSScan.vue'
<<<<<<< HEAD
import AgentScan from '../views/AgentScan.vue'
import NotFound from '../views/NotFound.vue'
=======
>>>>>>> de97d03d8b5dfa00af0eaddf983e9c20433e9b15

const routes = [
  {
    path: '/',
    name: 'Dashboard',
<<<<<<< HEAD
    component: Dashboard,
    meta: {
      title: '仪表盘',
      requiresAuth: false
    }
=======
    component: Dashboard
>>>>>>> de97d03d8b5dfa00af0eaddf983e9c20433e9b15
  },
  {
    path: '/scan-tasks',
    name: 'ScanTasks',
<<<<<<< HEAD
    component: ScanTasks,
    meta: {
      title: '扫描任务',
      requiresAuth: false
    }
=======
    component: ScanTasks
>>>>>>> de97d03d8b5dfa00af0eaddf983e9c20433e9b15
  },
  {
    path: '/poc-scan',
    name: 'POCScan',
<<<<<<< HEAD
    component: POCScan,
    meta: {
      title: 'POC扫描',
      requiresAuth: false
    }
=======
    component: POCScan
>>>>>>> de97d03d8b5dfa00af0eaddf983e9c20433e9b15
  },
  {
    path: '/vulnerabilities/:taskId',
    name: 'VulnerabilityResults',
    component: VulnerabilityResults,
<<<<<<< HEAD
    props: true,
    meta: {
      title: '漏洞结果',
      requiresAuth: false
    }
=======
    props: true
>>>>>>> de97d03d8b5dfa00af0eaddf983e9c20433e9b15
  },
  {
    path: '/vulnerability/:id',
    name: 'VulnerabilityDetail',
    component: VulnerabilityDetail,
<<<<<<< HEAD
    props: true,
    meta: {
      title: '漏洞详情',
      requiresAuth: false
    }
=======
    props: true
>>>>>>> de97d03d8b5dfa00af0eaddf983e9c20433e9b15
  },
  {
    path: '/reports',
    name: 'Reports',
<<<<<<< HEAD
    component: Reports,
    meta: {
      title: '报告',
      requiresAuth: false
    }
=======
    component: Reports
>>>>>>> de97d03d8b5dfa00af0eaddf983e9c20433e9b15
  },
  {
    path: '/settings',
    name: 'Settings',
<<<<<<< HEAD
    component: Settings,
    meta: {
      title: '系统设置',
      requiresAuth: false
    }
=======
    component: Settings
>>>>>>> de97d03d8b5dfa00af0eaddf983e9c20433e9b15
  },
  {
    path: '/awvs-scan',
    name: 'AWVSScan',
<<<<<<< HEAD
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
=======
    component: AWVSScan
>>>>>>> de97d03d8b5dfa00af0eaddf983e9c20433e9b15
  }
]

const router = createRouter({
  history: createWebHistory(),
<<<<<<< HEAD
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

router.afterEach((to, from) => {
  window.scrollTo(0, 0)
=======
  routes
>>>>>>> de97d03d8b5dfa00af0eaddf983e9c20433e9b15
})

export default router
