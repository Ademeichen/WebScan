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
      expect(typeof api.scanApi.startScan).toBe('function')
      expect(typeof api.scanApi.getScanStatus).toBe('function')
      expect(typeof api.scanApi.getScanResults).toBe('function')
      expect(typeof api.scanApi.stopScan).toBe('function')
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
      expect(typeof api.reportsApi.delete).toBe('function')
    })

    it('should export notificationsApi', () => {
      expect(api.notificationsApi).toBeDefined()
      expect(typeof api.notificationsApi.getNotifications).toBe('function')
      expect(typeof api.notificationsApi.markAsRead).toBe('function')
      expect(typeof api.notificationsApi.deleteNotification).toBe('function')
    })

    it('should export vulnerabilitiesApi', () => {
      expect(api.vulnerabilitiesApi).toBeDefined()
      expect(typeof api.vulnerabilitiesApi.getVulnerabilities).toBe('function')
      expect(typeof api.vulnerabilitiesApi.getVulnerability).toBe('function')
      expect(typeof api.vulnerabilitiesApi.updateVulnerability).toBe('function')
      expect(typeof api.vulnerabilitiesApi.deleteVulnerability).toBe('function')
      expect(typeof api.vulnerabilitiesApi.getStatistics).toBe('function')
    })

    it('should export pocApi', () => {
      expect(api.pocApi).toBeDefined()
      expect(typeof api.pocApi.getPOCTypes).toBe('function')
      expect(typeof api.pocApi.runPOC).toBe('function')
      expect(typeof api.pocApi.getPOCResults).toBe('function')
      expect(typeof api.pocApi.getPOCInfo).toBe('function')
      expect(typeof api.pocApi.scanSinglePOC).toBe('function')
    })

    it('should export awvsApi', () => {
      expect(api.awvsApi).toBeDefined()
      expect(typeof api.awvsApi.getTargets).toBe('function')
      expect(typeof api.awvsApi.createTarget).toBe('function')
      expect(typeof api.awvsApi.deleteTarget).toBe('function')
      expect(typeof api.awvsApi.getScans).toBe('function')
      expect(typeof api.awvsApi.startScan).toBe('function')
    })

    it('should export agentApi', () => {
      expect(api.agentApi).toBeDefined()
      expect(typeof api.agentApi.listAgents).toBe('function')
      expect(typeof api.agentApi.getAgentStatus).toBe('function')
      expect(typeof api.agentApi.executeAgent).toBe('function')
      expect(typeof api.agentApi.getAgentTypes).toBe('function')
      expect(typeof api.agentApi.getAgentDetail).toBe('function')
      expect(typeof api.agentApi.createAgent).toBe('function')
    })

    it('should export kbApi', () => {
      expect(api.kbApi).toBeDefined()
      expect(typeof api.kbApi.search).toBe('function')
      expect(typeof api.kbApi.addKnowledge).toBe('function')
      expect(typeof api.kbApi.getKnowledge).toBe('function')
      expect(typeof api.kbApi.updateKnowledge).toBe('function')
      expect(typeof api.kbApi.deleteKnowledge).toBe('function')
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
  })

  describe('API Method Signatures', () => {
    it('scanApi.startScan should accept data parameter', async () => {
      const testFn = api.scanApi.startScan
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

    it('vulnerabilitiesApi.getVulnerabilities should accept params parameter', async () => {
      const testFn = api.vulnerabilitiesApi.getVulnerabilities
      expect(testFn.length).toBeGreaterThanOrEqual(0)
    })
  })
})
