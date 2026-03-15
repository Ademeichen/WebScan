class TestReporter {
  constructor() {
    this.results = []
    this.startTime = null
    this.endTime = null
    this.currentSuite = null
    this.currentTest = null
  }

  startSession() {
    this.startTime = new Date()
    this.results = []
    this.log('Test session started', 'info')
  }

  endSession() {
    this.endTime = new Date()
    this.log('Test session ended', 'info')
  }

  startSuite(suiteName) {
    this.currentSuite = {
      name: suiteName,
      tests: [],
      startTime: new Date()
    }
    this.log(`Test suite started: ${suiteName}`, 'info')
  }

  endSuite() {
    if (this.currentSuite) {
      this.currentSuite.endTime = new Date()
      this.currentSuite.duration = this.currentSuite.endTime - this.currentSuite.startTime
      this.results.push({ ...this.currentSuite })
      this.currentSuite = null
    }
  }

  startTest(testName) {
    this.currentTest = {
      name: testName,
      status: 'pending',
      startTime: new Date()
    }
  }

  endTest(status, error = null, duration = 0) {
    if (this.currentTest) {
      this.currentTest.endTime = new Date()
      this.currentTest.duration = duration || (this.currentTest.endTime - this.currentTest.startTime)
      this.currentTest.status = status
      if (error) {
        this.currentTest.error = error
      }
      
      if (this.currentSuite) {
        this.currentSuite.tests.push({ ...this.currentTest })
      }
      
      const logType = status === 'passed' ? 'success' : 'error'
      this.log(`Test ${this.currentTest.name}: ${status}`, logType)
      this.currentTest = null
    }
  }

  log(message, type = 'info') {
    const entry = {
      timestamp: new Date().toISOString(),
      type,
      message
    }
    
    if (this.currentSuite) {
      if (!this.currentSuite.logs) {
        this.currentSuite.logs = []
      }
      this.currentSuite.logs.push(entry)
    }
  }

  getSummary() {
    const totalSuites = this.results.length
    let totalTests = 0
    let passedTests = 0
    let failedTests = 0
    let skippedTests = 0
    let totalDuration = 0

    for (const suite of this.results) {
      totalTests += suite.tests.length
      passedTests += suite.tests.filter(t => t.status === 'passed').length
      failedTests += suite.tests.filter(t => t.status === 'failed').length
      skippedTests += suite.tests.filter(t => t.status === 'skipped').length
      totalDuration += suite.duration || 0
    }

    return {
      totalSuites,
      totalTests,
      passedTests,
      failedTests,
      skippedTests,
      passRate: totalTests > 0 ? ((passedTests / totalTests) * 100).toFixed(2) : 0,
      duration: totalDuration,
      startTime: this.startTime,
      endTime: this.endTime
    }
  }

  generateTextReport() {
    const summary = this.getSummary()
    let report = '\n'
    report += '='.repeat(60) + '\n'
    report += '                    API TEST REPORT\n'
    report += '='.repeat(60) + '\n\n'
    
    report += `Start Time: ${this.startTime?.toISOString() || 'N/A'}\n`
    report += `End Time: ${this.endTime?.toISOString() || 'N/A'}\n`
    report += `Total Duration: ${this.formatDuration(summary.duration)}\n\n`
    
    report += '-'.repeat(60) + '\n'
    report += '                      SUMMARY\n'
    report += '-'.repeat(60) + '\n'
    report += `Total Test Suites: ${summary.totalSuites}\n`
    report += `Total Tests: ${summary.totalTests}\n`
    report += `Passed: ${summary.passedTests}\n`
    report += `Failed: ${summary.failedTests}\n`
    report += `Skipped: ${summary.skippedTests}\n`
    report += `Pass Rate: ${summary.passRate}%\n\n`

    for (const suite of this.results) {
      report += '-'.repeat(60) + '\n'
      report += `Suite: ${suite.name}\n`
      report += '-'.repeat(60) + '\n'
      
      for (const test of suite.tests) {
        const statusIcon = test.status === 'passed' ? '✓' : '✗'
        const statusColor = test.status === 'passed' ? '[PASS]' : '[FAIL]'
        report += `  ${statusColor} ${test.name} (${this.formatDuration(test.duration)})\n`
        
        if (test.error) {
          report += `       Error: ${test.error}\n`
        }
      }
      report += '\n'
    }

    report += '='.repeat(60) + '\n'
    report += `              END OF REPORT (${new Date().toISOString()})\n`
    report += '='.repeat(60) + '\n'
    
    return report
  }

  generateJSONReport() {
    return JSON.stringify({
      summary: this.getSummary(),
      results: this.results
    }, null, 2)
  }

  generateHTMLReport() {
    const summary = this.getSummary()
    
    let html = `<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>API Test Report</title>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f5f5; padding: 20px; }
    .container { max-width: 1200px; margin: 0 auto; }
    .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 10px; margin-bottom: 20px; }
    .header h1 { font-size: 28px; margin-bottom: 10px; }
    .header .meta { opacity: 0.9; font-size: 14px; }
    .summary { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-bottom: 20px; }
    .summary-card { background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); text-align: center; }
    .summary-card .value { font-size: 32px; font-weight: bold; color: #333; }
    .summary-card .label { color: #666; margin-top: 5px; }
    .summary-card.pass .value { color: #10b981; }
    .summary-card.fail .value { color: #ef4444; }
    .summary-card.rate .value { color: #3b82f6; }
    .suite { background: white; border-radius: 10px; margin-bottom: 15px; overflow: hidden; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
    .suite-header { background: #f8f9fa; padding: 15px 20px; border-bottom: 1px solid #e5e7eb; display: flex; justify-content: space-between; align-items: center; }
    .suite-header h3 { color: #333; }
    .suite-body { padding: 15px 20px; }
    .test { display: flex; justify-content: space-between; align-items: center; padding: 10px 0; border-bottom: 1px solid #f0f0f0; }
    .test:last-child { border-bottom: none; }
    .test-name { display: flex; align-items: center; gap: 10px; }
    .test-status { padding: 3px 10px; border-radius: 20px; font-size: 12px; font-weight: 500; }
    .test-status.passed { background: #d1fae5; color: #059669; }
    .test-status.failed { background: #fee2e2; color: #dc2626; }
    .test-status.skipped { background: #fef3c7; color: #d97706; }
    .test-duration { color: #666; font-size: 13px; }
    .error-message { background: #fef2f2; border-left: 3px solid #ef4444; padding: 10px 15px; margin-top: 10px; border-radius: 0 5px 5px 0; font-family: monospace; font-size: 12px; color: #991b1b; }
    .footer { text-align: center; padding: 20px; color: #666; font-size: 14px; }
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1>API Test Report</h1>
      <div class="meta">
        <div>Start: ${this.startTime?.toLocaleString() || 'N/A'}</div>
        <div>Duration: ${this.formatDuration(summary.duration)}</div>
      </div>
    </div>
    
    <div class="summary">
      <div class="summary-card">
        <div class="value">${summary.totalTests}</div>
        <div class="label">Total Tests</div>
      </div>
      <div class="summary-card pass">
        <div class="value">${summary.passedTests}</div>
        <div class="label">Passed</div>
      </div>
      <div class="summary-card fail">
        <div class="value">${summary.failedTests}</div>
        <div class="label">Failed</div>
      </div>
      <div class="summary-card rate">
        <div class="value">${summary.passRate}%</div>
        <div class="label">Pass Rate</div>
      </div>
    </div>`

    for (const suite of this.results) {
      html += `
    <div class="suite">
      <div class="suite-header">
        <h3>${suite.name}</h3>
        <span>${suite.tests.length} tests</span>
      </div>
      <div class="suite-body">`
      
      for (const test of suite.tests) {
        html += `
        <div class="test">
          <div class="test-name">
            <span class="test-status ${test.status}">${test.status}</span>
            <span>${test.name}</span>
          </div>
          <span class="test-duration">${this.formatDuration(test.duration)}</span>
        </div>`
        
        if (test.error) {
          html += `
        <div class="error-message">${test.error}</div>`
        }
      }
      
      html += `
      </div>
    </div>`
    }

    html += `
    <div class="footer">
      Generated at ${new Date().toLocaleString()}
    </div>
  </div>
</body>
</html>`

    return html
  }

  formatDuration(ms) {
    if (!ms || ms < 0) return '0ms'
    if (ms < 1000) return `${ms.toFixed(0)}ms`
    if (ms < 60000) return `${(ms / 1000).toFixed(2)}s`
    return `${(ms / 60000).toFixed(2)}m`
  }

  saveReport(format = 'text') {
    let content, filename, mimeType
    
    switch (format) {
      case 'json':
        content = this.generateJSONReport()
        filename = `test-report-${Date.now()}.json`
        mimeType = 'application/json'
        break
      case 'html':
        content = this.generateHTMLReport()
        filename = `test-report-${Date.now()}.html`
        mimeType = 'text/html'
        break
      default:
        content = this.generateTextReport()
        filename = `test-report-${Date.now()}.txt`
        mimeType = 'text/plain'
    }

    if (typeof window !== 'undefined' && window.Blob) {
      const blob = new Blob([content], { type: mimeType })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = filename
      a.click()
      URL.revokeObjectURL(url)
    }
    
    return { content, filename, mimeType }
  }

  printSummary() {
    const summary = this.getSummary()
    console.log('\n' + '='.repeat(50))
    console.log('TEST SUMMARY')
    console.log('='.repeat(50))
    console.log(`Total Suites: ${summary.totalSuites}`)
    console.log(`Total Tests: ${summary.totalTests}`)
    console.log(`Passed: ${summary.passedTests}`)
    console.log(`Failed: ${summary.failedTests}`)
    console.log(`Skipped: ${summary.skippedTests}`)
    console.log(`Pass Rate: ${summary.passRate}%`)
    console.log(`Duration: ${this.formatDuration(summary.duration)}`)
    console.log('='.repeat(50) + '\n')
  }
}

export const testReporter = new TestReporter()
export default TestReporter
