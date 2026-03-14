import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createTestingPinia } from '@pinia/testing'
import AIChatFloater from '@/components/common/AIChatFloater.vue'

const mockWebSocket = () => {
  const ws = {
    send: vi.fn(),
    close: vi.fn(),
    readyState: WebSocket.OPEN,
    onopen: null,
    onmessage: null,
    onerror: null,
    onclose: null
  }
  vi.spyOn(window, 'WebSocket').mockImplementation(() => ws)
  return ws
}

describe('AIChatFloater', () => {
  let wrapper
  let wsMock

  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.clear()
    wsMock = mockWebSocket()
  })

  afterEach(() => {
    wrapper?.unmount()
    vi.restoreAllMocks()
  })

  const mountComponent = () => {
    return mount(AIChatFloater, {
      global: {
        plugins: [createTestingPinia()],
        stubs: {
          'el-icon': true,
          'el-avatar': true,
          'el-input': true,
          'el-button': true,
          'el-tooltip': true
        }
      }
    })
  }

  describe('组件渲染', () => {
    it('应该正确渲染悬浮球按钮', () => {
      wrapper = mountComponent()
      expect(wrapper.find('.floater-button').exists()).toBe(true)
    })

    it('初始状态应该未展开', () => {
      wrapper = mountComponent()
      expect(wrapper.find('.chat-panel').exists()).toBe(false)
    })

    it('点击按钮应该展开聊天面板', async () => {
      wrapper = mountComponent()
      await wrapper.find('.floater-button').trigger('click')
      await flushPromises()
      expect(wrapper.find('.chat-panel').exists()).toBe(true)
    })
  })

  describe('拖拽功能', () => {
    it('应该支持拖拽移动', async () => {
      wrapper = mountComponent()
      const button = wrapper.find('.floater-button')
      
      await button.trigger('mousedown', { clientX: 100, clientY: 100 })
      await document.dispatchEvent(new MouseEvent('mousemove', { clientX: 150, clientY: 150 }))
      await document.dispatchEvent(new MouseEvent('mouseup'))
      
      expect(wrapper.vm.floaterPos.x).not.toBe(24)
    })

    it('拖拽后应该保存位置到localStorage', async () => {
      wrapper = mountComponent()
      const button = wrapper.find('.floater-button')
      
      await button.trigger('mousedown', { clientX: 100, clientY: 100 })
      await document.dispatchEvent(new MouseEvent('mousemove', { clientX: 150, clientY: 150 }))
      await document.dispatchEvent(new MouseEvent('mouseup'))
      
      const saved = localStorage.getItem('ai_chat_floater_position')
      expect(saved).not.toBeNull()
    })
  })

  describe('消息发送', () => {
    it('发送消息应该添加到消息列表', async () => {
      wrapper = mountComponent()
      await wrapper.find('.floater-button').trigger('click')
      await flushPromises()
      
      wrapper.vm.inputMessage = '测试消息'
      await wrapper.vm.sendMessage()
      
      expect(wrapper.vm.messages.length).toBe(1)
      expect(wrapper.vm.messages[0].content).toBe('测试消息')
      expect(wrapper.vm.messages[0].role).toBe('user')
    })

    it('空消息不应该发送', async () => {
      wrapper = mountComponent()
      wrapper.vm.inputMessage = ''
      await wrapper.vm.sendMessage()
      
      expect(wrapper.vm.messages.length).toBe(0)
    })

    it('发送后应该清空输入框', async () => {
      wrapper = mountComponent()
      await wrapper.find('.floater-button').trigger('click')
      await flushPromises()
      
      wrapper.vm.inputMessage = '测试消息'
      await wrapper.vm.sendMessage()
      
      expect(wrapper.vm.inputMessage).toBe('')
    })
  })

  describe('历史记录', () => {
    it('应该从localStorage加载历史记录', async () => {
      const history = [
        { id: 1, role: 'user', content: '历史消息', timestamp: new Date().toISOString() }
      ]
      localStorage.setItem('ai_chat_history', JSON.stringify(history))
      
      wrapper = mountComponent()
      await wrapper.find('.floater-button').trigger('click')
      await flushPromises()
      
      expect(wrapper.vm.messages.length).toBe(1)
    })

    it('清空历史应该清除localStorage', async () => {
      localStorage.setItem('ai_chat_history', JSON.stringify([{ id: 1 }]))
      
      wrapper = mountComponent()
      await wrapper.find('.floater-button').trigger('click')
      await flushPromises()
      
      wrapper.vm.clearHistory()
      
      expect(localStorage.getItem('ai_chat_history')).toBeNull()
      expect(wrapper.vm.messages.length).toBe(0)
    })
  })

  describe('WebSocket连接', () => {
    it('展开面板时应该建立WebSocket连接', async () => {
      wrapper = mountComponent()
      await wrapper.find('.floater-button').trigger('click')
      await flushPromises()
      
      expect(WebSocket).toHaveBeenCalled()
    })

    it('收起面板时应该断开WebSocket连接', async () => {
      wrapper = mountComponent()
      await wrapper.find('.floater-button').trigger('click')
      await flushPromises()
      
      await wrapper.find('.floater-button').trigger('click')
      await flushPromises()
      
      expect(wsMock.close).toHaveBeenCalled()
    })
  })

  describe('未读消息', () => {
    it('收到消息时面板关闭应该显示未读徽章', async () => {
      wrapper = mountComponent()
      
      wrapper.vm.hasUnreadMessages = true
      wrapper.vm.unreadCount = 3
      await wrapper.vm.$nextTick()
      
      expect(wrapper.find('.unread-badge').exists()).toBe(true)
      expect(wrapper.find('.unread-badge').text()).toBe('3')
    })

    it('展开面板应该清除未读状态', async () => {
      wrapper = mountComponent()
      wrapper.vm.hasUnreadMessages = true
      wrapper.vm.unreadCount = 5
      
      await wrapper.find('.floater-button').trigger('click')
      await flushPromises()
      
      expect(wrapper.vm.hasUnreadMessages).toBe(false)
      expect(wrapper.vm.unreadCount).toBe(0)
    })
  })

  describe('快捷操作', () => {
    it('点击快捷操作按钮应该发送对应消息', async () => {
      wrapper = mountComponent()
      await wrapper.find('.floater-button').trigger('click')
      await flushPromises()
      
      await wrapper.vm.sendQuickAction('漏洞分析')
      
      expect(wrapper.vm.messages.length).toBe(1)
      expect(wrapper.vm.messages[0].content).toBe('漏洞分析')
    })
  })

  describe('消息格式化', () => {
    it('应该正确格式化代码块', () => {
      wrapper = mountComponent()
      const result = wrapper.vm.formatMessage('```python\nprint("hello")\n```')
      expect(result).toContain('<pre class="code-block">')
    })

    it('应该正确格式化内联代码', () => {
      wrapper = mountComponent()
      const result = wrapper.vm.formatMessage('这是 `code` 代码')
      expect(result).toContain('<code class="inline-code">code</code>')
    })

    it('应该正确格式化粗体文本', () => {
      wrapper = mountComponent()
      const result = wrapper.vm.formatMessage('这是 **粗体** 文本')
      expect(result).toContain('<strong>粗体</strong>')
    })
  })

  describe('时间格式化', () => {
    it('应该正确格式化时间', () => {
      wrapper = mountComponent()
      const date = new Date('2024-01-01T14:30:00')
      const result = wrapper.vm.formatTime(date)
      expect(result).toBe('14:30')
    })

    it('无效日期应该返回默认值', () => {
      wrapper = mountComponent()
      const result = wrapper.vm.formatTime(null)
      expect(result).toBe('--:--')
    })
  })

  describe('复制功能', () => {
    it('复制消息应该调用clipboard API', async () => {
      wrapper = mountComponent()
      const spy = vi.spyOn(navigator.clipboard, 'writeText')
      
      await wrapper.vm.copyMessage('测试内容')
      
      expect(spy).toHaveBeenCalledWith('测试内容')
    })
  })
})

describe('AgentScan 子图状态测试', () => {
  it('应该正确映射子图状态文本', () => {
    const statusMap = {
      pending: '等待中',
      running: '执行中',
      completed: '已完成',
      failed: '失败'
    }
    
    expect(statusMap['pending']).toBe('等待中')
    expect(statusMap['running']).toBe('执行中')
    expect(statusMap['completed']).toBe('已完成')
    expect(statusMap['failed']).toBe('失败')
  })

  it('应该正确处理任务状态', () => {
    const taskStatusMap = {
      pending: '等待中',
      queued: '队列中',
      running: '运行中',
      completed: '已完成',
      failed: '失败',
      cancelled: '已取消'
    }
    
    expect(taskStatusMap['queued']).toBe('队列中')
    expect(taskStatusMap['cancelled']).toBe('已取消')
  })
})
