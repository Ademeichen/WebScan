/**
 * Vitest Setup File
 * 全局测试配置和模拟
 */

/* eslint-disable no-undef */

import { vi } from 'vitest'
import { config } from '@vue/test-utils'

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

const localStorageStore = {}
const localStorageMock = {
  getItem: vi.fn((key) => localStorageStore[key] || null),
  setItem: vi.fn((key, value) => {
    localStorageStore[key] = value
  }),
  removeItem: vi.fn((key) => {
    delete localStorageStore[key]
  }),
  clear: vi.fn(() => {
    Object.keys(localStorageStore).forEach(key => delete localStorageStore[key])
  }),
}
global.localStorage = localStorageMock

const sessionStorageStore = {}
const sessionStorageMock = {
  getItem: vi.fn((key) => sessionStorageStore[key] || null),
  setItem: vi.fn((key, value) => {
    sessionStorageStore[key] = value
  }),
  removeItem: vi.fn((key) => {
    delete sessionStorageStore[key]
  }),
  clear: vi.fn(() => {
    Object.keys(sessionStorageStore).forEach(key => delete sessionStorageStore[key])
  }),
}
global.sessionStorage = sessionStorageMock

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

global.fetch = vi.fn(() =>
  Promise.resolve({
    ok: true,
    status: 200,
    json: () => Promise.resolve({ code: 200, message: 'Success', data: {} })
  })
)

global.IntersectionObserver = class IntersectionObserver {
  constructor() {}
  disconnect() {}
  observe() {}
  takeRecords() { return [] }
  unobserve() {}
}

global.ResizeObserver = class ResizeObserver {
  constructor() {}
  disconnect() {}
  observe() {}
  unobserve() {}
}

global.requestAnimationFrame = (callback) => setTimeout(callback, 0)
global.cancelAnimationFrame = (id) => clearTimeout(id)

global.window.confirm = vi.fn(() => true)

global.window.alert = vi.fn()

global.HTMLElement.prototype.focus = vi.fn()

global.WebSocket = vi.fn(() => ({
  send: vi.fn(),
  close: vi.fn(),
  addEventListener: vi.fn(),
  removeEventListener: vi.fn(),
  readyState: 1,
}))

console.log('Vitest setup completed')
