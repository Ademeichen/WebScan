/**
 * Vitest Setup File
 * 全局测试配置和模拟
 */

import { vi } from 'vitest'
import { config } from '@vue/test-utils'

// 模拟 window.matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
})

// 模拟 localStorage
const localStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
}
global.localStorage = localStorageMock

// 模拟 sessionStorage
const sessionStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
}
global.sessionStorage = sessionStorageMock

// 配置 Vue Test Utils
config.global.stubs = {
  'el-button': true,
  'el-input': true,
  'el-select': true,
  'el-option': true,
  'el-form': true,
  'el-form-item': true,
  'el-table': true,
  'el-table-column': true,
  'el-pagination': true,
  'el-dialog': true,
  'el-drawer': true,
  'el-dropdown': true,
  'el-dropdown-menu': true,
  'el-dropdown-item': true,
  'el-badge': true,
  'el-avatar': true,
  'el-icon': true,
  'el-container': true,
  'el-header': true,
  'el-aside': true,
  'el-main': true,
  'el-menu': true,
  'el-menu-item': true,
  'el-sub-menu': true,
  'el-empty': true,
  'el-popover': true,
  'el-tooltip': true,
  'el-card': true,
  'el-tag': true,
  'el-progress': true,
  'el-switch': true,
  'el-checkbox': true,
  'el-radio': true,
  'el-radio-group': true,
  'el-radio-button': true,
  'el-upload': true,
  'el-date-picker': true,
  'el-time-picker': true,
  'el-cascader': true,
  'el-transfer': true,
  'el-tree': true,
  'el-alert': true,
  'el-notification': true,
  'el-message': true,
  'el-loading': true,
  'el-scrollbar': true,
  'el-breadcrumb': true,
  'el-breadcrumb-item': true,
  'el-tabs': true,
  'el-tab-pane': true,
  'el-collapse': true,
  'el-collapse-item': true,
  'el-timeline': true,
  'el-timeline-item': true,
  'el-statistic': true,
  'el-popconfirm': true,
  'el-image': true,
  'el-carousel': true,
  'el-carousel-item': true,
  'el-divider': true,
  'el-backtop': true,
  'el-page-header': true,
  'el-result': true,
  'el-skeleton': true,
  'el-skeleton-item': true,
  'el-descriptions': true,
  'el-descriptions-item': true,
  'el-space': true,
  'el-affix': true,
  'el-anchor': true,
  'el-anchor-link': true,
  'el-row': true,
  'el-col': true,
  'AppIcon': true
}

// 模拟 Vue Router
config.global.mocks = {
  $router: {
    push: vi.fn(),
    replace: vi.fn(),
    go: vi.fn(),
    back: vi.fn(),
    forward: vi.fn(),
    currentRoute: {
      value: {
        path: '/',
        name: 'Dashboard',
        params: {},
        query: {},
        meta: {}
      }
    }
  },
  $route: {
    path: '/',
    name: 'Dashboard',
    params: {},
    query: {},
    meta: {}
  }
}

// 模拟 API 响应
global.mockApiResponse = {
  success: (data = {}) => ({
    code: 200,
    message: 'Success',
    data
  }),
  error: (message = 'Error', code = 500) => ({
    code,
    message,
    data: null
  })
}

// 模拟 fetch
global.fetch = vi.fn(() =>
  Promise.resolve({
    ok: true,
    status: 200,
    json: () => Promise.resolve({ code: 200, message: 'Success', data: {} })
  })
)

// 模拟 IntersectionObserver
global.IntersectionObserver = class IntersectionObserver {
  constructor() {}
  disconnect() {}
  observe() {}
  takeRecords() { return [] }
  unobserve() {}
}

// 模拟 ResizeObserver
global.ResizeObserver = class ResizeObserver {
  constructor() {}
  disconnect() {}
  observe() {}
  unobserve() {}
}

// 模拟 requestAnimationFrame
global.requestAnimationFrame = (callback) => setTimeout(callback, 0)
global.cancelAnimationFrame = (id) => clearTimeout(id)

// 模拟 window.confirm
global.window.confirm = vi.fn(() => true)

// 模拟 window.alert
global.window.alert = vi.fn()

// 模拟 setTimeout 和 clearTimeout
global.setTimeout = vi.fn((callback, delay) => {
  const id = Math.random().toString(36).substring(7)
  if (typeof callback === 'function') {
    callback()
  }
  return id
})
global.clearTimeout = vi.fn()

// 模拟 setInterval 和 clearInterval
global.setInterval = vi.fn((callback, delay) => {
  const id = Math.random().toString(36).substring(7)
  if (typeof callback === 'function') {
    callback()
  }
  return id
})
global.clearInterval = vi.fn()

console.log('✅ Vitest setup completed')
