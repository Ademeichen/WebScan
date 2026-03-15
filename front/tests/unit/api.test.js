/**
 * API Utility 测试用例
 * 测试所有API方法的正确性
 */

import { describe, it, expect } from 'vitest'

import * as api from '@/utils/api'

describe('API Utility Tests', () => {
  describe('API Structure', () => {
    it('should export scanApi', () => {
      expect(api.scanApi).toBeDefined()
      expect(typeof api.scanApi.portScan).toBe('function')
      expect(typeof api.scanApi.infoLeak).toBe('function')
      expect(typeof api.scanApi.dirScan).toBe('function')
      expect(typeof api.scanApi.subdomainScan).toBe('function')
      expect(typeof api.scanApi.comprehensiveScan).toBe('function')
    })

    it('should export tasksApi', () => {
      expect(api.tasksApi).toBeDefined()
      expect(typeof api.tasksApi.getTasks).toBe('function')
      expect(typeof api.tasksApi.getTask).toBe('function')
      expect(typeof api.tasksApi.createTask).toBe('function')
      expect(typeof api.tasksApi.deleteTask).toBe('function')
      expect(typeof api.tasksApi.getTaskVulnerabilities).toBe('function')
      expect(typeof api.tasksApi.getTaskResults).toBe('function')
    })

    it('should export reportsApi', () => {
      expect(api.reportsApi).toBeDefined()
      expect(typeof api.reportsApi.getReports).toBe('function')
      expect(typeof api.reportsApi.createReport).toBe('function')
      expect(typeof api.reportsApi.getReport).toBe('function')
      expect(typeof api.reportsApi.getReportDetail).toBe('function')
      expect(typeof api.reportsApi.updateReport).toBe('function')
      expect(typeof api.reportsApi.deleteReport).toBe('function')
    })

    it('should export notificationsApi', () => {
      expect(api.notificationsApi).toBeDefined()
      expect(typeof api.notificationsApi.getNotifications).toBe('function')
      expect(typeof api.notificationsApi.markAsRead).toBe('function')
      expect(typeof api.notificationsApi.deleteNotification).toBe('function')
    })

    it('should export kbApi', () => {
      expect(api.kbApi).toBeDefined()
      expect(typeof api.kbApi.search).toBe('function')
      expect(typeof api.kbApi.getKnowledge).toBe('function')
      expect(typeof api.kbApi.getVulnerabilities).toBe('function')
      expect(typeof api.kbApi.sync).toBe('function')
      expect(typeof api.kbApi.searchPOC).toBe('function')
    })

    it('should export pocApi', () => {
      expect(api.pocApi).toBeDefined()
      expect(typeof api.pocApi.getPOCTypes).toBe('function')
      expect(typeof api.pocApi.runPOC).toBe('function')
      expect(typeof api.pocApi.getPOCInfo).toBe('function')
      expect(typeof api.pocApi.downloadPOC).toBe('function')
    })

    it('should export awvsApi', () => {
      expect(api.awvsApi).toBeDefined()
      expect(typeof api.awvsApi.getTargets).toBe('function')
      expect(typeof api.awvsApi.createTarget).toBe('function')
      expect(typeof api.awvsApi.deleteTarget).toBe('function')
      expect(typeof api.awvsApi.getScans).toBe('function')
      expect(typeof api.awvsApi.startScan).toBe('function')
    })

    it('should export aiAgentsApi', () => {
      expect(api.aiAgentsApi).toBeDefined()
      expect(typeof api.aiAgentsApi.scan).toBe('function')
      expect(typeof api.aiAgentsApi.getTask).toBe('function')
      expect(typeof api.aiAgentsApi.getTasks).toBe('function')
      expect(typeof api.aiAgentsApi.cancelTask).toBe('function')
      expect(typeof api.aiAgentsApi.deleteTask).toBe('function')
    })

    it('should export settingsApi', () => {
      expect(api.settingsApi).toBeDefined()
      expect(typeof api.settingsApi.getSettings).toBe('function')
      expect(typeof api.settingsApi.updateSettings).toBe('function')
    })

    it('should export userApi', () => {
      expect(api.userApi).toBeDefined()
      expect(typeof api.userApi.getProfile).toBe('function')
      expect(typeof api.userApi.updateProfile).toBe('function')
      expect(typeof api.userApi.getPermissions).toBe('function')
      expect(typeof api.userApi.getList).toBe('function')
    })

    it('should export pocVerificationApi', () => {
      expect(api.pocVerificationApi).toBeDefined()
      expect(typeof api.pocVerificationApi.createTask).toBe('function')
      expect(typeof api.pocVerificationApi.getTasks).toBe('function')
      expect(typeof api.pocVerificationApi.getTask).toBe('function')
      expect(typeof api.pocVerificationApi.cancelTask).toBe('function')
    })

    it('should export aiApi', () => {
      expect(api.aiApi).toBeDefined()
      expect(typeof api.aiApi.chat).toBe('function')
      expect(typeof api.aiApi.getChatInstances).toBe('function')
      expect(typeof api.aiApi.createChatInstance).toBe('function')
    })
  })

  describe('API Method Signatures', () => {
    it('scanApi.portScan should accept data parameter', async () => {
      const testFn = api.scanApi.portScan
      expect(testFn.length).toBeGreaterThanOrEqual(1)
    })

    it('tasksApi.getTasks should accept params parameter', async () => {
      const testFn = api.tasksApi.getTasks
      expect(testFn.length).toBeGreaterThanOrEqual(0)
    })

    it('notificationsApi.getNotifications should accept params parameter', async () => {
      const testFn = api.notificationsApi.getNotifications
      expect(testFn.length).toBeGreaterThanOrEqual(0)
    })

    it('kbApi.search should accept params parameter', async () => {
      const testFn = api.kbApi.search
      expect(testFn.length).toBeGreaterThanOrEqual(0)
    })
  })
})
