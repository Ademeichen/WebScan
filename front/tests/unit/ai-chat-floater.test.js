/**
 * AIChatFloater 组件测试用例
 * 测试悬浮球AI对话功能的核心功能
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { nextTick } from 'vue'
import AIChatFloater from '@/components/common/AIChatFloater.vue'

describe('AIChatFloater Component', () => {
  let wrapper

  beforeEach(() => {
    vi.clearAllMocks()
    
    wrapper = mount(AIChatFloater, {
      global: {
        stubs: {
          'el-icon': true,
          'el-avatar': true,
          'el-button': true,
          'el-input': true,
          'el-tooltip': true
        },
        mocks: {
          $router: {
            push: vi.fn()
          },
          $route: {
            path: '/'
          }
        }
      }
    })
  })

  afterEach(() => {
    if (wrapper) {
      try {
        wrapper.unmount()
      } catch (e) {
        // ignore unmount errors
      }
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
    })

    it('展开时应该显示关闭图标', async () => {
      const floaterButton = wrapper.find('.floater-button')
      await floaterButton.trigger('click')
      await nextTick()
      
      expect(floaterButton.classes()).toContain('expanded')
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
  })

  describe('响应式设计', () => {
    it('组件应该有响应式样式', () => {
      const floaterButton = wrapper.find('.floater-button')
      expect(floaterButton.exists()).toBe(true)
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

  describe('组件生命周期', () => {
    it('组件挂载时应该初始化', () => {
      expect(wrapper.vm.isExpanded).toBe(false)
      expect(wrapper.vm.messages).toEqual([])
      expect(wrapper.vm.inputMessage).toBe('')
    })
  })
})
