/**
 * 组件测试用例
 * 测试前端主要组件的功能
 */

import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia } from 'pinia'
import StatCard from '@/components/common/StatCard.vue'
import TaskCard from '@/components/business/TaskCard.vue'
import VulnerabilityCard from '@/components/business/VulnerabilityCard.vue'
import Alert from '@/components/common/Alert.vue'

describe('StatCard Component', () => {
  it('renders correctly with props', () => {
    const wrapper = mount(StatCard, {
      props: {
        icon: 'Search',
        value: 100,
        label: 'Test Label',
        type: 'primary'
      },
      global: {
        plugins: [createPinia()]
      }
    })

    expect(wrapper.text()).toContain('Test Label')
    expect(wrapper.text()).toContain('100')
  })

  it('applies correct type class', () => {
    const wrapper = mount(StatCard, {
      props: {
        icon: 'Warning',
        value: 50,
        label: 'Warning',
        type: 'danger'
      },
      global: {
        plugins: [createPinia()]
      }
    })

    expect(wrapper.classes()).toContain('stat-card-danger')
  })
})

describe('TaskCard Component', () => {
  const mockTask = {
    id: 1,
    task_name: 'Test Task',
    target: 'https://www.baidu.com',
    task_type: 'poc_scan',
    status: 'completed',
    progress: 100,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T01:00:00Z',
    result: {
      vulnerabilities: {
        critical: 1,
        high: 2,
        medium: 3,
        low: 4
      }
    }
  }

  it('renders task information', () => {
    const wrapper = mount(TaskCard, {
      props: {
        task: mockTask
      },
      global: {
        plugins: [createPinia()]
      }
    })

    expect(wrapper.text()).toContain('Test Task')
    expect(wrapper.text()).toContain('https://www.baidu.com')
  })

  it('emits cancel event', async () => {
    const wrapper = mount(TaskCard, {
      props: {
        task: mockTask
      },
      global: {
        plugins: [createPinia()]
      }
    })

    await wrapper.find('.btn-cancel').trigger('click')
    expect(wrapper.emitted()).toHaveProperty('cancel')
    expect(wrapper.emitted().cancel[0]).toEqual([mockTask.id])
  })

  it('emits view event', async () => {
    const wrapper = mount(TaskCard, {
      props: {
        task: mockTask
      },
      global: {
        plugins: [createPinia()]
      }
    })

    await wrapper.find('.btn-view').trigger('click')
    expect(wrapper.emitted()).toHaveProperty('view')
    expect(wrapper.emitted().view[0]).toEqual([mockTask.id])
  })
})

describe('VulnerabilityCard Component', () => {
  const mockVuln = {
    id: 1,
    title: 'Test Vulnerability',
    severity: 'high',
    type: 'SQL Injection',
    source: 'awvs',
    status: 'open',
    target: 'https://www.baidu.com',
    description: 'Test description',
    cvss_score: 7.5,
    discovered_at: '2024-01-01T00:00:00Z',
    created_at: '2024-01-01T00:00:00Z'
  }

  it('renders vulnerability information', () => {
    const wrapper = mount(VulnerabilityCard, {
      props: {
        vulnerability: mockVuln
      },
      global: {
        plugins: [createPinia()]
      }
    })

    expect(wrapper.text()).toContain('Test Vulnerability')
    expect(wrapper.text()).toContain('SQL Injection')
  })

  it('applies correct severity class', () => {
    const wrapper = mount(VulnerabilityCard, {
      props: {
        vulnerability: mockVuln
      },
      global: {
        plugins: [createPinia()]
      }
    })

    expect(wrapper.find('.severity-badge').classes()).toContain('severity-high')
  })

  it('emits click event', async () => {
    const wrapper = mount(VulnerabilityCard, {
      props: {
        vulnerability: mockVuln
      },
      global: {
        plugins: [createPinia()]
      }
    })

    await wrapper.trigger('click')
    expect(wrapper.emitted()).toHaveProperty('click')
    expect(wrapper.emitted().click[0]).toEqual([mockVuln.id])
  })
})

describe('Alert Component', () => {
  it('renders error alert', () => {
    const wrapper = mount(Alert, {
      props: {
        type: 'error',
        message: 'Error message'
      },
      global: {
        plugins: [createPinia()]
      }
    })

    expect(wrapper.text()).toContain('Error message')
    expect(wrapper.find('.alert-error').exists()).toBe(true)
  })

  it('renders success alert', () => {
    const wrapper = mount(Alert, {
      props: {
        type: 'success',
        message: 'Success message'
      },
      global: {
        plugins: [createPinia()]
      }
    })

    expect(wrapper.text()).toContain('Success message')
    expect(wrapper.find('.alert-success').exists()).toBe(true)
  })

  it('emits close event', async () => {
    const wrapper = mount(Alert, {
      props: {
        type: 'error',
        message: 'Test message'
      },
      global: {
        plugins: [createPinia()]
      }
    })

    await wrapper.find('.btn-close').trigger('click')
    expect(wrapper.emitted()).toHaveProperty('close')
  })
})
