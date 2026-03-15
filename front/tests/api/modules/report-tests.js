import TEST_CONFIG from './test-config.js'
import { testUtils } from './test-utils.js'
import { testReporter } from './test-reporter.js'
import { api } from './api-client.js'

export class ReportTests {
  constructor() {
    this.createdReportIds = []
  }

  async runAll() {
    testReporter.startSuite('Report API Tests')

    await this.testGetReports()
    await this.testCreateReport()
    await this.testCreateReportWithInvalidData()
    await this.testGetReportById()
    await this.testGetNonExistentReport()
    await this.testUpdateReport()
    await this.testDeleteReport()
    await this.testExportReport()
    await this.testExportReportInDifferentFormats()
    await this.testPreviewReport()

    await this.cleanup()
    testReporter.endSuite()
  }

  async testGetReports() {
    testReporter.startTest('Get Reports List')
    const startTime = performance.now()

    try {
      const response = await api.reports.getReports({ limit: 10 })

      testUtils.assertCondition(response.ok, 'Response should be successful')
      
      if (response.data) {
        testUtils.assertArray(response.data.items || response.data, 'Reports should be an array')
      }

      const duration = performance.now() - startTime
      testReporter.endTest('passed', null, duration)
    } catch (error) {
      const duration = performance.now() - startTime
      testReporter.endTest('failed', error.message, duration)
    }
  }

  async testCreateReport() {
    testReporter.startTest('Create Report - Valid Data')
    const startTime = performance.now()

    try {
      const reportData = {
        name: `Test Report ${testUtils.generateRandomString(6)}`,
        format: 'html',
        task_id: 1
      }

      const response = await api.reports.createReport(reportData)

      testUtils.assertCondition(
        response.ok || response.status === 201,
        'Report creation should succeed'
      )

      if (response.data?.id || response.data?.report_id) {
        const reportId = response.data.id || response.data.report_id
        this.createdReportIds.push(reportId)
        testUtils.log(`Report created with ID: ${reportId}`, 'success')
      }

      const duration = performance.now() - startTime
      testReporter.endTest('passed', null, duration)
    } catch (error) {
      const duration = performance.now() - startTime
      testReporter.endTest('failed', error.message, duration)
    }
  }

  async testCreateReportWithInvalidData() {
    testReporter.startTest('Create Report - Invalid Data')
    const startTime = performance.now()

    try {
      const invalidDataSets = [
        { name: '', format: 'html' },
        { name: 'Test Report', format: 'invalid_format' },
        { name: '', format: '' }
      ]

      for (const data of invalidDataSets) {
        const response = await api.reports.createReport(data)
        testUtils.assertCondition(
          !response.ok || response.status === 400,
          'Should reject invalid report data'
        )
      }

      const duration = performance.now() - startTime
      testReporter.endTest('passed', null, duration)
    } catch (error) {
      const duration = performance.now() - startTime
      testReporter.endTest('failed', error.message, duration)
    }
  }

  async testGetReportById() {
    testReporter.startTest('Get Report By ID')
    const startTime = performance.now()

    try {
      if (this.createdReportIds.length === 0) {
        const listResponse = await api.reports.getReports({ limit: 1 })
        if (listResponse.data?.items?.[0]?.id) {
          this.createdReportIds.push(listResponse.data.items[0].id)
        }
      }

      if (this.createdReportIds.length > 0) {
        const reportId = this.createdReportIds[0]
        const response = await api.reports.getReport(reportId)

        testUtils.assertCondition(response.ok, 'Should retrieve report by ID')
        
        if (response.data) {
          testUtils.assertCondition(
            response.data.id === reportId || response.data.report_id === reportId,
            'Report ID should match'
          )
        }
      }

      const duration = performance.now() - startTime
      testReporter.endTest('passed', null, duration)
    } catch (error) {
      const duration = performance.now() - startTime
      testReporter.endTest('failed', error.message, duration)
    }
  }

  async testGetNonExistentReport() {
    testReporter.startTest('Get Non-Existent Report')
    const startTime = performance.now()

    try {
      const response = await api.reports.getReport(999999)

      testUtils.assertCondition(
        !response.ok || response.status === 404,
        'Should return 404 for non-existent report'
      )

      const duration = performance.now() - startTime
      testReporter.endTest('passed', null, duration)
    } catch (error) {
      const duration = performance.now() - startTime
      testReporter.endTest('failed', error.message, duration)
    }
  }

  async testUpdateReport() {
    testReporter.startTest('Update Report')
    const startTime = performance.now()

    try {
      if (this.createdReportIds.length > 0) {
        const reportId = this.createdReportIds[0]
        const updateData = {
          name: `Updated Report ${testUtils.generateRandomString(4)}`
        }

        const response = await api.reports.updateReport(reportId, updateData)

        testUtils.assertCondition(
          response.ok || response.status === 200,
          'Report update should succeed'
        )
      }

      const duration = performance.now() - startTime
      testReporter.endTest('passed', null, duration)
    } catch (error) {
      const duration = performance.now() - startTime
      testReporter.endTest('failed', error.message, duration)
    }
  }

  async testDeleteReport() {
    testReporter.startTest('Delete Report')
    const startTime = performance.now()

    try {
      const reportData = {
        name: `Report to Delete ${testUtils.generateRandomString(4)}`,
        format: 'html'
      }
      const createResponse = await api.reports.createReport(reportData)

      if (createResponse.data?.id || createResponse.data?.report_id) {
        const reportId = createResponse.data.id || createResponse.data.report_id
        
        const deleteResponse = await api.reports.deleteReport(reportId)
        
        testUtils.assertCondition(
          deleteResponse.ok || deleteResponse.status === 200,
          'Report deletion should succeed'
        )

        const verifyResponse = await api.reports.getReport(reportId)
        testUtils.assertCondition(
          !verifyResponse.ok || verifyResponse.status === 404,
          'Deleted report should not be accessible'
        )
      }

      const duration = performance.now() - startTime
      testReporter.endTest('passed', null, duration)
    } catch (error) {
      const duration = performance.now() - startTime
      testReporter.endTest('failed', error.message, duration)
    }
  }

  async testExportReport() {
    testReporter.startTest('Export Report')
    const startTime = performance.now()

    try {
      if (this.createdReportIds.length > 0) {
        const reportId = this.createdReportIds[0]
        const response = await api.reports.exportReport(reportId, 'json')

        testUtils.assertCondition(
          response.ok || response.status === 200,
          'Report export should succeed'
        )
      }

      const duration = performance.now() - startTime
      testReporter.endTest('passed', null, duration)
    } catch (error) {
      const duration = performance.now() - startTime
      testReporter.endTest('failed', error.message, duration)
    }
  }

  async testExportReportInDifferentFormats() {
    testReporter.startTest('Export Report - Different Formats')
    const startTime = performance.now()

    try {
      if (this.createdReportIds.length > 0) {
        const reportId = this.createdReportIds[0]
        const formats = ['json', 'html', 'pdf', 'csv']

        for (const format of formats) {
          const response = await api.reports.exportReport(reportId, format)
          testUtils.assertCondition(
            response.ok || response.status === 200 || response.status === 400,
            `Export format ${format} should be handled`
          )
        }
      }

      const duration = performance.now() - startTime
      testReporter.endTest('passed', null, duration)
    } catch (error) {
      const duration = performance.now() - startTime
      testReporter.endTest('failed', error.message, duration)
    }
  }

  async testPreviewReport() {
    testReporter.startTest('Preview Report')
    const startTime = performance.now()

    try {
      if (this.createdReportIds.length > 0) {
        const reportId = this.createdReportIds[0]
        const response = await api.reports.previewReport(reportId)

        testUtils.assertCondition(
          response.ok || response.status === 200,
          'Report preview should succeed'
        )
      }

      const duration = performance.now() - startTime
      testReporter.endTest('passed', null, duration)
    } catch (error) {
      const duration = performance.now() - startTime
      testReporter.endTest('failed', error.message, duration)
    }
  }

  async cleanup() {
    testUtils.log('Cleaning up created reports...', 'info')
    for (const reportId of this.createdReportIds) {
      try {
        await api.reports.deleteReport(reportId)
      } catch (error) {
        testUtils.log(`Failed to delete report ${reportId}: ${error.message}`, 'warning')
      }
    }
  }
}

export default ReportTests
