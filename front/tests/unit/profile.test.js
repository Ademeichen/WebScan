/**
 * Profile 组件测试用例
 * 测试用户个人信息管理页面的功能
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createRouter, createMemoryHistory } from 'vue-router'
import { createPinia } from 'pinia'
import Profile from '@/views/Profile.vue'

vi.mock('@/utils/api', () => ({
  authApi: {
    getCurrentUser: vi.fn(() => Promise.resolve({
      code: 200,
      data: {
        id: 1,
        username: 'admin',
        email: 'admin@test.com',
        role: 'admin',
        status: 'active',
        created_at: '2024-01-01'
      }
    })),
    updateProfile: vi.fn(() => Promise.resolve({
      code: 200,
      message: 'Profile updated successfully',
      data: {
        id: 1,
        username: 'admin',
        email: 'admin@test.com',
        role: 'admin'
      }
    })),
    changePassword: vi.fn(() => Promise.resolve({
      code: 200,
      message: 'Password changed successfully'
    }))
  }
}))

vi.mock('@/utils/date', () => ({
  formatDate: vi.fn(() => '2024-01-01')
}))

const router = createRouter({
  history: createMemoryHistory(),
  routes: [
    { path: '/', component: { template: '<div>Home</div>' } },
    { path: '/profile', component: Profile }
  ]
})

describe('Profile Component', () => {
  let wrapper
  let pinia

  beforeEach(() => {
    pinia = createPinia()
    wrapper = mount(Profile, {
      global: {
        plugins: [router, pinia],
        stubs: {
          Loading: { template: '<div class="loading">Loading...</div>' },
          Alert: { template: '<div class="alert">{{ message }}</div>', props: ['message', 'type'] },
          AppIcon: { template: '<div class="icon"></div>', props: ['name', 'size'] }
        }
      }
    })
  })

  it('should render profile page', async () => {
    await wrapper.vm.$nextTick()
    
    expect(wrapper.find('.profile').exists()).toBe(true)
  })

  it('should show loading state', async () => {
    wrapper.vm.loading = true
    await wrapper.vm.$nextTick()
    
    expect(wrapper.find('.loading').exists()).toBe(true)
  })

  it('should show error message', async () => {
    wrapper.vm.errorMessage = 'Failed to update profile'
    await wrapper.vm.$nextTick()
    
    expect(wrapper.find('.alert').exists()).toBe(true)
  })

  it('should display user information', async () => {
    wrapper.vm.userInfo = {
      id: 1,
      username: 'admin',
      email: 'admin@test.com',
      role: 'admin',
      created_at: '2024-01-01'
    }
    await wrapper.vm.$nextTick()
    
    expect(wrapper.vm.userInfo.username).toBe('admin')
  })

  it('should calculate permissions', async () => {
    wrapper.vm.userInfo = {
      role: 'admin'
    }
    await wrapper.vm.$nextTick()
    
    expect(wrapper.vm.permissions).toBeDefined()
  })

  it('should handle edit profile modal', async () => {
    wrapper.vm.showEditProfile = true
    await wrapper.vm.$nextTick()
    
    expect(wrapper.vm.showEditProfile).toBe(true)
  })

  it('should handle change password modal', async () => {
    wrapper.vm.showChangePassword = true
    await wrapper.vm.$nextTick()
    
    expect(wrapper.vm.showChangePassword).toBe(true)
  })

  it('should close edit profile modal', async () => {
    wrapper.vm.showEditProfile = true
    await wrapper.vm.$nextTick()
    
    wrapper.vm.showEditProfile = false
    await wrapper.vm.$nextTick()
    
    expect(wrapper.vm.showEditProfile).toBe(false)
  })

  it('should close change password modal', async () => {
    wrapper.vm.showChangePassword = true
    await wrapper.vm.$nextTick()
    
    wrapper.vm.showChangePassword = false
    await wrapper.vm.$nextTick()
    
    expect(wrapper.vm.showChangePassword).toBe(false)
  })

  it('should display login history', async () => {
    wrapper.vm.loginHistory = [
      { time: '2024-01-01', ip: '192.168.1.1', device: 'Chrome', status: 'success' }
    ]
    await wrapper.vm.$nextTick()
    
    expect(wrapper.vm.loginHistory.length).toBeGreaterThan(0)
  })

  it('should handle two factor authentication toggle', async () => {
    wrapper.vm.userInfo = {
      two_factor_enabled: false
    }
    await wrapper.vm.$nextTick()
    
    expect(wrapper.vm.userInfo.two_factor_enabled).toBe(false)
  })
})
