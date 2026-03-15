/**
 * 组件测试用例
 * 测试前端主要组件的基本功能
 */

import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia } from 'pinia'
import StatCard from '@/components/common/StatCard.vue'
import TaskCard from '@/components/business/TaskCard.vue'
import VulnerabilityCard from '@/components/business/VulnerabilityCard.vue'
import Alert from '@/components/common/Alert.vue'

describe('StatCard Component', () => {
  it('renders component without errors', () => {
    const wrapper = mount(StatCard, {
      props: {
        icon: 'Search',
        value: 100,
        label: 'Test Label',
        type: 'primary'
      },
      global: {
        plugins: [createPinia()],
        stubs: {
          'el-icon': true
        }
      }
    })

    expect(wrapper.exists()).toBe(true)
    expect(wrapper.vm).toBeDefined()
  })

  it('accepts props correctly', () => {
    const wrapper = mount(StatCard, {
      props: {
        icon: 'Warning',
        value: 50,
        label: 'Warning Label',
        type: 'danger'
      },
      global: {
        plugins: [createPinia()],
        stubs: {
          'el-icon': true
        }
      }
    })

    expect(wrapper.props('value')).toBe(50)
    expect(wrapper.props('label')).toBe('Warning Label')
    expect(wrapper.props('type')).toBe('danger')
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

  it('renders component without errors', () => {
    const wrapper = mount(TaskCard, {
      props: {
        task: mockTask
      },
      global: {
        plugins: [createPinia()],
        stubs: {
          'el-icon': true,
          'el-tag': true,
          'el-progress': true
        }
      }
    })

    expect(wrapper.exists()).toBe(true)
    expect(wrapper.vm).toBeDefined()
  })

  it('accepts task prop correctly', () => {
    const wrapper = mount(TaskCard, {
      props: {
        task: mockTask
      },
      global: {
        plugins: [createPinia()],
        stubs: {
          'el-icon': true,
          'el-tag': true,
          'el-progress': true
        }
      }
    })

    expect(wrapper.props('task')).toEqual(mockTask)
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

  it('renders component without errors', () => {
    const wrapper = mount(VulnerabilityCard, {
      props: {
        vulnerability: mockVuln
      },
      global: {
        plugins: [createPinia()],
        stubs: {
          'el-icon': true,
          'el-tag': true
        }
      }
    })

    expect(wrapper.exists()).toBe(true)
    expect(wrapper.vm).toBeDefined()
  })

  it('accepts vulnerability prop correctly', () => {
    const wrapper = mount(VulnerabilityCard, {
      props: {
        vulnerability: mockVuln
      },
      global: {
        plugins: [createPinia()],
        stubs: {
          'el-icon': true,
          'el-tag': true
        }
      }
    })

    expect(wrapper.props('vulnerability')).toEqual(mockVuln)
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
        plugins: [createPinia()],
        stubs: {
          'el-icon': true
        }
      }
    })

    expect(wrapper.exists()).toBe(true)
    expect(wrapper.props('type')).toBe('error')
    expect(wrapper.props('message')).toBe('Error message')
  })

  it('renders success alert', () => {
    const wrapper = mount(Alert, {
      props: {
        type: 'success',
        message: 'Success message'
      },
      global: {
        plugins: [createPinia()],
        stubs: {
          'el-icon': true
        }
      }
    })

    expect(wrapper.exists()).toBe(true)
    expect(wrapper.props('type')).toBe('success')
    expect(wrapper.props('message')).toBe('Success message')
  })
})
