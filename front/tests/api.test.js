/**
 * API 测试用例
 * 测试前端 API 工具函数与后端 API 的集成
 */

import { describe, it, expect } from 'vitest'
import { scanApi, tasksApi, reportsApi, settingsApi, pocApi, awvsApi, agentApi, kbApi, userApi, notificationsApi } from '@/utils/api'

describe('API Tests', () => {
  describe('Scan API', () => {
    it('should call port scan endpoint', async () => {
      const mockData = { ip: '127.0.0.1', ports: '1-1000' }
      const response = await scanApi.portScan(mockData)
      expect(response).toBeDefined()
    })

    it('should call info leak detection endpoint', async () => {
      const mockData = { url: 'https://www.baidu.com' }
      const response = await scanApi.infoLeak(mockData)
      expect(response).toBeDefined()
    })

    it('should call directory scan endpoint', async () => {
      const mockData = { url: 'https://www.baidu.com' }
      const response = await scanApi.dirScan(mockData)
      expect(response).toBeDefined()
    })
  })

  describe('Tasks API', () => {
    it('should get tasks list', async () => {
      const response = await tasksApi.getTasks({ limit: 10 })
      expect(response).toBeDefined()
      expect(response.code).toBe(200)
    })

    it('should create a new task', async () => {
      const mockData = {
        task_name: 'Test Task',
        target: 'https://www.baidu.com',
        task_type: 'poc_scan'
      }
      const response = await tasksApi.createTask(mockData)
      expect(response).toBeDefined()
    })

    it('should get task details', async () => {
      const taskId = 1
      const response = await tasksApi.getTask(taskId)
      expect(response).toBeDefined()
    })

    it('should cancel a task', async () => {
      const taskId = 1
      const response = await tasksApi.cancelTask(taskId)
      expect(response).toBeDefined()
    })

    it('should delete a task', async () => {
      const taskId = 1
      const response = await tasksApi.deleteTask(taskId)
      expect(response).toBeDefined()
    })
  })

  describe('Reports API', () => {
    it('should get reports list', async () => {
      const response = await reportsApi.getReports({ limit: 10 })
      expect(response).toBeDefined()
    })

    it('should create a new report', async () => {
      const mockData = {
        task_id: 1,
        format: 'html',
        name: 'Test Report'
      }
      const response = await reportsApi.createReport(mockData)
      expect(response).toBeDefined()
    })

    it('should get report details', async () => {
      const reportId = 1
      const response = await reportsApi.getReport(reportId)
      expect(response).toBeDefined()
    })

    it('should delete a report', async () => {
      const reportId = 1
      const response = await reportsApi.delete(reportId)
      expect(response).toBeDefined()
    })

    it('should export report', async () => {
      const reportId = 1
      const response = await reportsApi.exportReport(reportId, 'json')
      expect(response).toBeDefined()
    })
  })

  describe('Settings API', () => {
    it('should get settings', async () => {
      const response = await settingsApi.getSettings()
      expect(response).toBeDefined()
    })

    it('should update settings', async () => {
      const mockData = {
        general: { systemName: 'Test System' },
        scan: { defaultDepth: 2 }
      }
      const response = await settingsApi.updateSettings(mockData)
      expect(response).toBeDefined()
    })

    it('should get system info', async () => {
      const response = await settingsApi.getSystemInfo()
      expect(response).toBeDefined()
    })

    it('should get statistics', async () => {
      const response = await settingsApi.getStatistics(7)
      expect(response).toBeDefined()
    })
  })

  describe('POC API', () => {
    it('should get POC types', async () => {
      const response = await pocApi.getPOCTypes()
      expect(response).toBeDefined()
      expect(response.code).toBe(200)
    })

    it('should run POC scan', async () => {
      const mockData = {
        target: 'https://www.baidu.com',
        poc_types: ['weblogic_cve_2020_2551'],
        timeout: 10
      }
      const response = await pocApi.runPOC(mockData)
      expect(response).toBeDefined()
    })

    it('should get POC info', async () => {
      const pocType = 'weblogic_cve_2020_2551'
      const response = await pocApi.getPOCInfo(pocType)
      expect(response).toBeDefined()
    })
  })

  describe('AWVS API', () => {
    it('should get AWVS targets', async () => {
      const response = await awvsApi.getTargets()
      expect(response).toBeDefined()
    })

    it('should create AWVS target', async () => {
      const mockData = { address: 'https://www.baidu.com', description: 'Test Target' }
      const response = await awvsApi.createTarget(mockData)
      expect(response).toBeDefined()
    })

    it('should start AWVS scan', async () => {
      const mockData = { url: 'https://www.baidu.com', scan_type: 'full_scan' }
      const response = await awvsApi.startScan(mockData)
      expect(response).toBeDefined()
    })

    it('should get AWVS vulnerabilities', async () => {
      const response = await awvsApi.getVulnerabilities({ limit: 10 })
      expect(response).toBeDefined()
    })
  })

  describe('Agent API', () => {
    it('should list agents', async () => {
      const response = await agentApi.listAgents()
      expect(response).toBeDefined()
    })

    it('should execute agent', async () => {
      const mockData = {
        tools: [{ name: 'scan', args: { target: 'https://www.baidu.com' }, description: 'Scan target' }],
        user_requirement: 'Test scan'
      }
      const response = await agentApi.executeAgent(mockData)
      expect(response).toBeDefined()
    })

    it('should get agent status', async () => {
      const agentId = 'test-agent-id'
      const response = await agentApi.getAgentStatus(agentId)
      expect(response).toBeDefined()
    })
  })

  describe('Knowledge Base API', () => {
    it('should search vulnerabilities', async () => {
      const params = { keyword: 'SQL Injection', page: 1, page_size: 10 }
      const response = await kbApi.search(params)
      expect(response).toBeDefined()
    })

    it('should sync vulnerabilities', async () => {
      const response = await kbApi.sync()
      expect(response).toBeDefined()
    })

    it('should download POC', async () => {
      const ssvid = 97343
      const response = await kbApi.downloadPOC(ssvid)
      expect(response).toBeDefined()
    })
  })

  describe('User API', () => {
    it('should get user profile', async () => {
      const response = await userApi.getProfile()
      expect(response).toBeDefined()
    })

    it('should update user profile', async () => {
      const userId = 1
      const mockData = { username: 'testuser', email: 'test@example.com' }
      const response = await userApi.updateProfile(userId, mockData)
      expect(response).toBeDefined()
    })

    it('should get user permissions', async () => {
      const response = await userApi.getPermissions()
      expect(response).toBeDefined()
    })
  })

  describe('Notifications API', () => {
    it('should get notifications', async () => {
      const response = await notificationsApi.getNotifications({ limit: 10 })
      expect(response).toBeDefined()
    })

    it('should mark notification as read', async () => {
      const notificationId = 1
      const response = await notificationsApi.markAsRead(notificationId)
      expect(response).toBeDefined()
    })

    it('should mark all notifications as read', async () => {
      const response = await notificationsApi.markAllAsRead()
      expect(response).toBeDefined()
    })

    it('should delete notification', async () => {
      const notificationId = 1
      const response = await notificationsApi.deleteNotification(notificationId)
      expect(response).toBeDefined()
    })

    it('should get unread count', async () => {
      const response = await notificationsApi.getUnreadCount()
      expect(response).toBeDefined()
    })
  })
})
