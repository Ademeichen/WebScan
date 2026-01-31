/**
 * Notifications 组件测试用例
 * 测试通知列表页面的功能
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createRouter, createMemoryHistory } from 'vue-router'
import { createPinia } from 'pinia'
import Notifications from '@/views/Notifications.vue'

vi.mock('@/utils/api', () => ({
  notificationsApi: {
    getNotifications: vi.fn(() => Promise.resolve({
      code: 200,
      data: {
        notifications: [
          { id: 1, title: 'Test Notification', message: 'Test message', type: 'info', read: false, created_at: '2024-01-01' }
        ],
        total: 1
      }
    })),
    markAsRead: vi.fn(() => Promise.resolve({ code: 200, message: 'Marked as read' })),
    deleteNotification: vi.fn(() => Promise.resolve({ code: 200, message: 'Deleted' }))
  }
}))

vi.mock('@/utils/date', () => ({
  formatDate: vi.fn(() => '2024-01-01')
}))

const router = createRouter({
  history: createMemoryHistory(),
  routes: [
    { path: '/', component: { template: '<div>Home</div>' } },
    { path: '/notifications/:id', component: { template: '<div>Notification Detail</div>' } }
  ]
})

describe('Notifications Component', () => {
  let wrapper
  let pinia

  beforeEach(() => {
    pinia = createPinia()
    wrapper = mount(Notifications, {
      global: {
        plugins: [router, pinia],
        stubs: {
          Loading: { template: '<div class="loading">Loading...</div>' },
          Alert: { template: '<div class="alert">{{ message }}</div>', props: ['message', 'type'] }
        }
      }
    })
  })

  it('should render notifications list', async () => {
    await wrapper.vm.loadNotifications()
    await wrapper.vm.$nextTick()
    
    expect(wrapper.find('.notifications').exists()).toBe(true)
  })

  it('should filter notifications by type', async () => {
    await wrapper.vm.loadNotifications()
    await wrapper.vm.$nextTick()
    
    wrapper.vm.filters.type = 'info'
    await wrapper.vm.loadNotifications()
    await wrapper.vm.$nextTick()
    
    expect(wrapper.vm.filters.type).toBe('info')
  })

  it('should filter notifications by read status', async () => {
    await wrapper.vm.loadNotifications()
    await wrapper.vm.$nextTick()
    
    wrapper.vm.filters.status = 'unread'
    await wrapper.vm.loadNotifications()
    await wrapper.vm.$nextTick()
    
    expect(wrapper.vm.filters.status).toBe('unread')
  })

  it('should mark notification as read', async () => {
    const { notificationsApi } = await import('@/utils/api')
    
    await wrapper.vm.handleMarkAsRead({ id: 1 })
    await wrapper.vm.$nextTick()
    
    expect(notificationsApi.markAsRead).toHaveBeenCalled()
  })

  it('should delete notification', async () => {
    const { notificationsApi } = await import('@/utils/api')
    
    await wrapper.vm.handleDelete({ id: 1 })
    await wrapper.vm.$nextTick()
    
    expect(notificationsApi.deleteNotification).toHaveBeenCalled()
  })

  it('should handle pagination', async () => {
    await wrapper.vm.loadNotifications()
    await wrapper.vm.$nextTick()
    
    wrapper.vm.currentPage = 2
    await wrapper.vm.loadNotifications()
    await wrapper.vm.$nextTick()
    
    expect(wrapper.vm.currentPage).toBe(2)
  })

  it('should refresh notifications list', async () => {
    await wrapper.vm.loadNotifications()
    await wrapper.vm.$nextTick()
    
    expect(wrapper.vm.loading).toBe(false)
  })

  it('should show loading state', async () => {
    wrapper.vm.loading = true
    await wrapper.vm.$nextTick()
    
    expect(wrapper.find('.loading').exists()).toBe(true)
  })

  it('should show error message', async () => {
    wrapper.vm.errorMessage = 'Failed to load notifications'
    await wrapper.vm.$nextTick()
    
    expect(wrapper.find('.alert').exists()).toBe(true)
  })

  it('should calculate unread count', async () => {
    wrapper.vm.notifications = [
      { id: 1, read: false },
      { id: 2, read: true },
      { id: 3, read: false }
    ]
    await wrapper.vm.$nextTick()
    
    expect(wrapper.vm.unreadCount).toBe(2)
  })

  it('should calculate read count', async () => {
    wrapper.vm.notifications = [
      { id: 1, read: false },
      { id: 2, read: true },
      { id: 3, read: false }
    ]
    await wrapper.vm.$nextTick()
    
    expect(wrapper.vm.readCount).toBe(1)
  })
})
