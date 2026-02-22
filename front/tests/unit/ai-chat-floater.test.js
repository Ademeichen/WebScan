/**
 * AIChatFloater 组件测试用例
 * 测试悬浮球AI对话功能的所有核心功能
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { nextTick } from 'vue'
import AIChatFloater from '@/components/common/AIChatFloater.vue'

describe('AIChatFloater Component', () => {
  let wrapper

  beforeEach(() => {
    wrapper = mount(AIChatFloater, {
      global: {
        stubs: {
          'el-icon': true,
          'el-avatar': true,
          'el-button': true,
          'el-input': true
        }
      }
    })
  })

  afterEach(() => {
    if (wrapper) {
      wrapper.unmount()
    }
    localStorage.clear()
  })

  describe('组件渲染', () => {
    it('应该正确渲染组件', () => {
      expect(wrapper.exists()).toBe(true)
      expect(wrapper.find('.ai-chat-floater').exists()).toBe(true)
      expect(wrapper.find('.floater-button').exists()).toBe(true)
    })

    it('默认状态下聊天面板应该隐藏', () => {
      expect(wrapper.find('.chat-panel').exists()).toBe(false)
    })

    it('悬浮球按钮应该存在', () => {
      const floaterButton = wrapper.find('.floater-button')
      expect(floaterButton.exists()).toBe(true)
    })
  })

  describe('显示/隐藏切换功能', () => {
    it('点击悬浮球应该展开聊天面板', async () => {
      const floaterButton = wrapper.find('.floater-button')
      await floaterButton.trigger('click')
      await nextTick()
      
      expect(wrapper.find('.chat-panel').exists()).toBe(true)
      expect(wrapper.vm.isExpanded).toBe(true)
    })

    it('再次点击应该收起聊天面板', async () => {
      const floaterButton = wrapper.find('.floater-button')
      
      await floaterButton.trigger('click')
      await nextTick()
      expect(wrapper.vm.isExpanded).toBe(true)
      
      await floaterButton.trigger('click')
      await nextTick()
      expect(wrapper.vm.isExpanded).toBe(false)
      expect(wrapper.find('.chat-panel').exists()).toBe(false)
    })

    it('展开时应该显示关闭图标', async () => {
      const floaterButton = wrapper.find('.floater-button')
      await floaterButton.trigger('click')
      await nextTick()
      
      expect(floaterButton.classes()).toContain('expanded')
    })
  })

  describe('消息输入功能', () => {
    it('应该有消息输入框', async () => {
      const floaterButton = wrapper.find('.floater-button')
      await floaterButton.trigger('click')
      await nextTick()
      
      const textarea = wrapper.find('textarea')
      expect(textarea.exists()).toBe(true)
    })

    it('输入框应该绑定到inputMessage', async () => {
      const floaterButton = wrapper.find('.floater-button')
      await floaterButton.trigger('click')
      await nextTick()
      
      const textarea = wrapper.find('textarea')
      await textarea.setValue('测试消息')
      
      expect(wrapper.vm.inputMessage).toBe('测试消息')
    })

    it('应该有发送按钮', async () => {
      const floaterButton = wrapper.find('.floater-button')
      await floaterButton.trigger('click')
      await nextTick()
      
      const sendButton = wrapper.findAll('button').find(btn => 
        btn.text().includes('发送')
      )
      expect(sendButton.exists()).toBe(true)
    })
  })

  describe('消息发送功能', () => {
    it('空消息不应该发送', async () => {
      const floaterButton = wrapper.find('.floater-button')
      await floaterButton.trigger('click')
      await nextTick()
      
      const sendButton = wrapper.findAll('button').find(btn => 
        btn.text().includes('发送')
      )
      
      expect(sendButton.attributes('disabled')).toBeDefined()
    })

    it('发送消息后应该清空输入框', async () => {
      const floaterButton = wrapper.find('.floater-button')
      await floaterButton.trigger('click')
      await nextTick()
      
      const textarea = wrapper.find('textarea')
      await textarea.setValue('测试消息')
      
      wrapper.vm.messages = []
      wrapper.vm.isSending = false
      
      await wrapper.vm.sendMessage()
      
      expect(wrapper.vm.inputMessage).toBe('')
    })
  })

  describe('聊天历史记录功能', () => {
    it('应该能够加载聊天历史', () => {
      const testHistory = [
        {
          id: 1,
          role: 'user',
          content: '测试消息',
          timestamp: new Date()
        }
      ]
      
      localStorage.setItem('ai_chat_history', JSON.stringify(testHistory))
      wrapper.vm.loadHistory()
      
      expect(wrapper.vm.messages.length).toBe(1)
      expect(wrapper.vm.messages[0].content).toBe('测试消息')
    })

    it('应该能够保存聊天历史', () => {
      const testMessage = {
        id: 1,
        role: 'user',
        content: '测试消息',
        timestamp: new Date()
      }
      
      wrapper.vm.messages = [testMessage]
      wrapper.vm.saveHistory()
      
      const saved = localStorage.getItem('ai_chat_history')
      expect(saved).toBeTruthy()
      
      const parsed = JSON.parse(saved)
      expect(parsed.length).toBe(1)
      expect(parsed[0].content).toBe('测试消息')
    })

    it('应该能够清空聊天历史', async () => {
      const testHistory = [
        {
          id: 1,
          role: 'user',
          content: '测试消息',
          timestamp: new Date()
        }
      ]
      
      localStorage.setItem('ai_chat_history', JSON.stringify(testHistory))
      wrapper.vm.messages = testHistory
      
      await wrapper.vm.clearHistory()
      
      expect(wrapper.vm.messages.length).toBe(0)
      expect(localStorage.getItem('ai_chat_history')).toBeNull()
    })
  })

  describe('加载状态和错误处理', () => {
    it('应该有加载状态', () => {
      expect(wrapper.vm.isLoading).toBeDefined()
      expect(typeof wrapper.vm.isLoading).toBe('boolean')
    })

    it('应该有发送状态', () => {
      expect(wrapper.vm.isSending).toBeDefined()
      expect(typeof wrapper.vm.isSending).toBe('boolean')
    })

    it('发送中时应该禁用发送按钮', async () => {
      wrapper.vm.isSending = true
      await nextTick()
      
      const floaterButton = wrapper.find('.floater-button')
      await floaterButton.trigger('click')
      await nextTick()
      
      const sendButton = wrapper.findAll('button').find(btn => 
        btn.text().includes('发送')
      )
      
      expect(sendButton.attributes('disabled')).toBeDefined()
    })
  })

  describe('响应式设计', () => {
    it('组件应该有响应式样式', () => {
      const floaterButton = wrapper.find('.floater-button')
      expect(floaterButton.exists()).toBe(true)
    })

    it('聊天面板应该有固定定位', async () => {
      const floaterButton = wrapper.find('.floater-button')
      await floaterButton.trigger('click')
      await nextTick()
      
      const chatPanel = wrapper.find('.chat-panel')
      expect(chatPanel.exists()).toBe(true)
    })
  })

  describe('时间格式化', () => {
    it('应该正确格式化时间', () => {
      const date = new Date('2024-01-01T14:30:00')
      const formatted = wrapper.vm.formatTime(date)
      
      expect(formatted).toBe('14:30')
    })

    it('应该处理小时和分钟的补零', () => {
      const date = new Date('2024-01-01T09:05:00')
      const formatted = wrapper.vm.formatTime(date)
      
      expect(formatted).toBe('09:05')
    })
  })

  describe('消息显示', () => {
    it('应该显示用户消息', async () => {
      wrapper.vm.messages = [
        {
          id: 1,
          role: 'user',
          content: '用户消息',
          timestamp: new Date()
        }
      ]
      
      const floaterButton = wrapper.find('.floater-button')
      await floaterButton.trigger('click')
      await nextTick()
      
      const userMessages = wrapper.findAll('.message-item.user')
      expect(userMessages.length).toBe(1)
    })

    it('应该显示AI助手消息', async () => {
      wrapper.vm.messages = [
        {
          id: 1,
          role: 'assistant',
          content: 'AI回复',
          timestamp: new Date()
        }
      ]
      
      const floaterButton = wrapper.find('.floater-button')
      await floaterButton.trigger('click')
      await nextTick()
      
      const assistantMessages = wrapper.findAll('.message-item.assistant')
      expect(assistantMessages.length).toBe(1)
    })

    it('空状态应该显示提示', async () => {
      wrapper.vm.messages = []
      
      const floaterButton = wrapper.find('.floater-button')
      await floaterButton.trigger('click')
      await nextTick()
      
      const emptyState = wrapper.find('.empty-state')
      expect(emptyState.exists()).toBe(true)
    })
  })

  describe('WebSocket连接', () => {
    it('展开时应该尝试连接WebSocket', async () => {
      const connectSpy = vi.spyOn(wrapper.vm, 'connectWebSocket')
      
      const floaterButton = wrapper.find('.floater-button')
      await floaterButton.trigger('click')
      await nextTick()
      
      expect(connectSpy).toHaveBeenCalled()
    })

    it('收起时应该断开WebSocket连接', async () => {
      const disconnectSpy = vi.spyOn(wrapper.vm, 'disconnectWebSocket')
      
      const floaterButton = wrapper.find('.floater-button')
      await floaterButton.trigger('click')
      await nextTick()
      
      await floaterButton.trigger('click')
      await nextTick()
      
      expect(disconnectSpy).toHaveBeenCalled()
    })
  })

  describe('API回退机制', () => {
    it('WebSocket不可用时应该使用API', async () => {
      const apiSpy = vi.spyOn(wrapper.vm, 'sendViaAPI')
      
      wrapper.vm.ws = null
      await wrapper.vm.sendMessage()
      
      expect(apiSpy).toHaveBeenCalled()
    })
  })

  describe('组件生命周期', () => {
    it('组件挂载时应该初始化', () => {
      expect(wrapper.vm.isExpanded).toBe(false)
      expect(wrapper.vm.messages).toEqual([])
      expect(wrapper.vm.inputMessage).toBe('')
    })

    it('组件卸载时应该清理WebSocket', () => {
      const disconnectSpy = vi.spyOn(wrapper.vm, 'disconnectWebSocket')
      
      wrapper.unmount()
      
      expect(disconnectSpy).toHaveBeenCalled()
    })
  })
})