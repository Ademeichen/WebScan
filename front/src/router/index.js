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
<<<<<<< HEAD
import AgentScan from '../views/AgentScan.vue'
import NotFound from '../views/NotFound.vue'
=======
>>>>>>> de97d03d8b5dfa00af0eaddf983e9c20433e9b15
>>>>>>> origin/renruipeng

const routes = [
  {
    path: '/',
    name: 'Dashboard',
<<<<<<< HEAD
=======
<<<<<<< HEAD
>>>>>>> origin/renruipeng
    component: Dashboard,
    meta: {
      title: '仪表盘',
      requiresAuth: false
    }
<<<<<<< HEAD
=======
=======
    component: Dashboard
>>>>>>> de97d03d8b5dfa00af0eaddf983e9c20433e9b15
>>>>>>> origin/renruipeng
  },
  {
    path: '/scan-tasks',
    name: 'ScanTasks',
<<<<<<< HEAD
=======
<<<<<<< HEAD
>>>>>>> origin/renruipeng
    component: ScanTasks,
    meta: {
      title: '扫描任务',
      requiresAuth: false
    }
<<<<<<< HEAD
=======
=======
    component: ScanTasks
>>>>>>> de97d03d8b5dfa00af0eaddf983e9c20433e9b15
>>>>>>> origin/renruipeng
  },
  {
    path: '/poc-scan',
    name: 'POCScan',
<<<<<<< HEAD
=======
<<<<<<< HEAD
>>>>>>> origin/renruipeng
    component: POCScan,
    meta: {
      title: 'POC扫描',
      requiresAuth: false
    }
<<<<<<< HEAD
=======
=======
    component: POCScan
>>>>>>> de97d03d8b5dfa00af0eaddf983e9c20433e9b15
>>>>>>> origin/renruipeng
  },
  {
    path: '/vulnerabilities/:taskId',
    name: 'VulnerabilityResults',
    component: VulnerabilityResults,
<<<<<<< HEAD
=======
<<<<<<< HEAD
>>>>>>> origin/renruipeng
    props: true,
    meta: {
      title: '漏洞结果',
      requiresAuth: false
    }
<<<<<<< HEAD
=======
=======
    props: true
>>>>>>> de97d03d8b5dfa00af0eaddf983e9c20433e9b15
>>>>>>> origin/renruipeng
  },
  {
    path: '/vulnerability/:id',
    name: 'VulnerabilityDetail',
    component: VulnerabilityDetail,
<<<<<<< HEAD
=======
<<<<<<< HEAD
>>>>>>> origin/renruipeng
    props: true,
    meta: {
      title: '漏洞详情',
      requiresAuth: false
    }
<<<<<<< HEAD
=======
=======
    props: true
>>>>>>> de97d03d8b5dfa00af0eaddf983e9c20433e9b15
>>>>>>> origin/renruipeng
  },
  {
    path: '/reports',
    name: 'Reports',
<<<<<<< HEAD
=======
<<<<<<< HEAD
>>>>>>> origin/renruipeng
    component: Reports,
    meta: {
      title: '报告',
      requiresAuth: false
    }
<<<<<<< HEAD
=======
=======
    component: Reports
>>>>>>> de97d03d8b5dfa00af0eaddf983e9c20433e9b15
>>>>>>> origin/renruipeng
  },
  {
    path: '/settings',
    name: 'Settings',
<<<<<<< HEAD
=======
<<<<<<< HEAD
>>>>>>> origin/renruipeng
    component: Settings,
    meta: {
      title: '系统设置',
      requiresAuth: false
    }
<<<<<<< HEAD
=======
=======
    component: Settings
>>>>>>> de97d03d8b5dfa00af0eaddf983e9c20433e9b15
>>>>>>> origin/renruipeng
  },
  {
    path: '/awvs-scan',
    name: 'AWVSScan',
<<<<<<< HEAD
=======
<<<<<<< HEAD
>>>>>>> origin/renruipeng
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
<<<<<<< HEAD
=======
=======
    component: AWVSScan
>>>>>>> de97d03d8b5dfa00af0eaddf983e9c20433e9b15
>>>>>>> origin/renruipeng
  }
]

const router = createRouter({
  history: createWebHistory(),
<<<<<<< HEAD
=======
<<<<<<< HEAD
>>>>>>> origin/renruipeng
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
<<<<<<< HEAD
=======
=======
  routes
>>>>>>> de97d03d8b5dfa00af0eaddf983e9c20433e9b15
>>>>>>> origin/renruipeng
})

export default router
