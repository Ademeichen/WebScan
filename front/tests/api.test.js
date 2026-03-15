/**
 * API 测试用例
 * 测试前端 API 工具函数的结构和方法存在性
 */

import { describe, it, expect } from 'vitest'
import { scanApi, tasksApi, reportsApi, settingsApi, pocApi, awvsApi, aiAgentsApi, kbApi, userApi, notificationsApi, aiApi, pocVerificationApi } from '@/utils/api'

describe('API Tests', () => {
  describe('Scan API', () => {
    it('should have portScan method', () => {
      expect(scanApi.portScan).toBeDefined()
      expect(typeof scanApi.portScan).toBe('function')
    })

    it('should have infoLeak method', () => {
      expect(scanApi.infoLeak).toBeDefined()
      expect(typeof scanApi.infoLeak).toBe('function')
    })

    it('should have dirScan method', () => {
      expect(scanApi.dirScan).toBeDefined()
      expect(typeof scanApi.dirScan).toBe('function')
    })

    it('should have subdomainScan method', () => {
      expect(scanApi.subdomainScan).toBeDefined()
      expect(typeof scanApi.subdomainScan).toBe('function')
    })

    it('should have comprehensiveScan method', () => {
      expect(scanApi.comprehensiveScan).toBeDefined()
      expect(typeof scanApi.comprehensiveScan).toBe('function')
    })
  })

  describe('Tasks API', () => {
    it('should have getTasks method', () => {
      expect(tasksApi.getTasks).toBeDefined()
      expect(typeof tasksApi.getTasks).toBe('function')
    })

    it('should have createTask method', () => {
      expect(tasksApi.createTask).toBeDefined()
      expect(typeof tasksApi.createTask).toBe('function')
    })

    it('should have getTask method', () => {
      expect(tasksApi.getTask).toBeDefined()
      expect(typeof tasksApi.getTask).toBe('function')
    })

    it('should have cancelTask method', () => {
      expect(tasksApi.cancelTask).toBeDefined()
      expect(typeof tasksApi.cancelTask).toBe('function')
    })

    it('should have deleteTask method', () => {
      expect(tasksApi.deleteTask).toBeDefined()
      expect(typeof tasksApi.deleteTask).toBe('function')
    })
  })

  describe('Reports API', () => {
    it('should have getReports method', () => {
      expect(reportsApi.getReports).toBeDefined()
      expect(typeof reportsApi.getReports).toBe('function')
    })

    it('should have createReport method', () => {
      expect(reportsApi.createReport).toBeDefined()
      expect(typeof reportsApi.createReport).toBe('function')
    })

    it('should have getReport method', () => {
      expect(reportsApi.getReport).toBeDefined()
      expect(typeof reportsApi.getReport).toBe('function')
    })

    it('should have deleteReport method', () => {
      expect(reportsApi.deleteReport).toBeDefined()
      expect(typeof reportsApi.deleteReport).toBe('function')
    })

    it('should have exportReport method', () => {
      expect(reportsApi.exportReport).toBeDefined()
      expect(typeof reportsApi.exportReport).toBe('function')
    })
  })

  describe('Settings API', () => {
    it('should have getSettings method', () => {
      expect(settingsApi.getSettings).toBeDefined()
      expect(typeof settingsApi.getSettings).toBe('function')
    })

    it('should have updateSettings method', () => {
      expect(settingsApi.updateSettings).toBeDefined()
      expect(typeof settingsApi.updateSettings).toBe('function')
    })

    it('should have getSystemInfo method', () => {
      expect(settingsApi.getSystemInfo).toBeDefined()
      expect(typeof settingsApi.getSystemInfo).toBe('function')
    })

    it('should have getStatistics method', () => {
      expect(settingsApi.getStatistics).toBeDefined()
      expect(typeof settingsApi.getStatistics).toBe('function')
    })
  })

  describe('POC API', () => {
    it('should have getPOCTypes method', () => {
      expect(pocApi.getPOCTypes).toBeDefined()
      expect(typeof pocApi.getPOCTypes).toBe('function')
    })

    it('should have runPOC method', () => {
      expect(pocApi.runPOC).toBeDefined()
      expect(typeof pocApi.runPOC).toBe('function')
    })

    it('should have getPOCInfo method', () => {
      expect(pocApi.getPOCInfo).toBeDefined()
      expect(typeof pocApi.getPOCInfo).toBe('function')
    })

    it('should have downloadPOC method', () => {
      expect(pocApi.downloadPOC).toBeDefined()
      expect(typeof pocApi.downloadPOC).toBe('function')
    })
  })

  describe('AWVS API', () => {
    it('should have getTargets method', () => {
      expect(awvsApi.getTargets).toBeDefined()
      expect(typeof awvsApi.getTargets).toBe('function')
    })

    it('should have createTarget method', () => {
      expect(awvsApi.createTarget).toBeDefined()
      expect(typeof awvsApi.createTarget).toBe('function')
    })

    it('should have startScan method', () => {
      expect(awvsApi.startScan).toBeDefined()
      expect(typeof awvsApi.startScan).toBe('function')
    })

    it('should have getVulnerabilities method', () => {
      expect(awvsApi.getVulnerabilities).toBeDefined()
      expect(typeof awvsApi.getVulnerabilities).toBe('function')
    })
  })

  describe('AI Agents API', () => {
    it('should have scan method', () => {
      expect(aiAgentsApi.scan).toBeDefined()
      expect(typeof aiAgentsApi.scan).toBe('function')
    })

    it('should have getTask method', () => {
      expect(aiAgentsApi.getTask).toBeDefined()
      expect(typeof aiAgentsApi.getTask).toBe('function')
    })

    it('should have getTasks method', () => {
      expect(aiAgentsApi.getTasks).toBeDefined()
      expect(typeof aiAgentsApi.getTasks).toBe('function')
    })

    it('should have cancelTask method', () => {
      expect(aiAgentsApi.cancelTask).toBeDefined()
      expect(typeof aiAgentsApi.cancelTask).toBe('function')
    })

    it('should have deleteTask method', () => {
      expect(aiAgentsApi.deleteTask).toBeDefined()
      expect(typeof aiAgentsApi.deleteTask).toBe('function')
    })
  })

  describe('Knowledge Base API', () => {
    it('should have search method', () => {
      expect(kbApi.search).toBeDefined()
      expect(typeof kbApi.search).toBe('function')
    })

    it('should have sync method', () => {
      expect(kbApi.sync).toBeDefined()
      expect(typeof kbApi.sync).toBe('function')
    })

    it('should have downloadPOC method', () => {
      expect(kbApi.downloadPOC).toBeDefined()
      expect(typeof kbApi.downloadPOC).toBe('function')
    })

    it('should have getKnowledge method', () => {
      expect(kbApi.getKnowledge).toBeDefined()
      expect(typeof kbApi.getKnowledge).toBe('function')
    })
  })

  describe('User API', () => {
    it('should have getProfile method', () => {
      expect(userApi.getProfile).toBeDefined()
      expect(typeof userApi.getProfile).toBe('function')
    })

    it('should have updateProfile method', () => {
      expect(userApi.updateProfile).toBeDefined()
      expect(typeof userApi.updateProfile).toBe('function')
    })

    it('should have getPermissions method', () => {
      expect(userApi.getPermissions).toBeDefined()
      expect(typeof userApi.getPermissions).toBe('function')
    })
  })

  describe('Notifications API', () => {
    it('should have getNotifications method', () => {
      expect(notificationsApi.getNotifications).toBeDefined()
      expect(typeof notificationsApi.getNotifications).toBe('function')
    })

    it('should have markAsRead method', () => {
      expect(notificationsApi.markAsRead).toBeDefined()
      expect(typeof notificationsApi.markAsRead).toBe('function')
    })

    it('should have markAllAsRead method', () => {
      expect(notificationsApi.markAllAsRead).toBeDefined()
      expect(typeof notificationsApi.markAllAsRead).toBe('function')
    })

    it('should have deleteNotification method', () => {
      expect(notificationsApi.deleteNotification).toBeDefined()
      expect(typeof notificationsApi.deleteNotification).toBe('function')
    })

    it('should have getUnreadCount method', () => {
      expect(notificationsApi.getUnreadCount).toBeDefined()
      expect(typeof notificationsApi.getUnreadCount).toBe('function')
    })
  })

  describe('AI API', () => {
    it('should have chat method', () => {
      expect(aiApi.chat).toBeDefined()
      expect(typeof aiApi.chat).toBe('function')
    })

    it('should have getChatInstances method', () => {
      expect(aiApi.getChatInstances).toBeDefined()
      expect(typeof aiApi.getChatInstances).toBe('function')
    })

    it('should have createChatInstance method', () => {
      expect(aiApi.createChatInstance).toBeDefined()
      expect(typeof aiApi.createChatInstance).toBe('function')
    })
  })

  describe('POC Verification API', () => {
    it('should have createTask method', () => {
      expect(pocVerificationApi.createTask).toBeDefined()
      expect(typeof pocVerificationApi.createTask).toBe('function')
    })

    it('should have getTasks method', () => {
      expect(pocVerificationApi.getTasks).toBeDefined()
      expect(typeof pocVerificationApi.getTasks).toBe('function')
    })

    it('should have cancelTask method', () => {
      expect(pocVerificationApi.cancelTask).toBeDefined()
      expect(typeof pocVerificationApi.cancelTask).toBe('function')
    })

    it('should have getPocRegistry method', () => {
      expect(pocVerificationApi.getPocRegistry).toBeDefined()
      expect(typeof pocVerificationApi.getPocRegistry).toBe('function')
    })
  })
})
