export const TEST_CONFIG = {
  API_BASE_URL: 'http://127.0.0.1:8888/api',
  TIMEOUT: 30000,
  RETRY_COUNT: 3,
  RETRY_DELAY: 1000,
  
  TEST_USER: {
    username: 'testuser',
    password: 'testpassword123',
    email: 'test@example.com'
  },
  
  TEST_TARGETS: {
    validUrl: 'https://example.com',
    invalidUrl: 'not-a-valid-url',
    localhost: 'http://127.0.0.1',
    testDomain: 'testphp.vulnweb.com'
  },
  
  PERFORMANCE: {
    maxResponseTime: 5000,
    maxConcurrentRequests: 10,
    stressTestIterations: 100
  },
  
  BOUNDARY: {
    maxStringLength: 10000,
    maxArrayLength: 1000,
    specialChars: '!@#$%^&*()_+-=[]{}|;\':",./<>?`~',
    unicodeChars: '中文日本語한국어العربيةעברית',
    sqlInjectionPayloads: [
      "' OR '1'='1",
      "'; DROP TABLE users;--",
      "1' UNION SELECT * FROM users--"
    ],
    xssPayloads: [
      '<script>alert("XSS")</script>',
      '<img src=x onerror=alert("XSS")>',
      'javascript:alert("XSS")'
    ]
  },
  
  HTTP_STATUS: {
    OK: 200,
    CREATED: 201,
    BAD_REQUEST: 400,
    UNAUTHORIZED: 401,
    FORBIDDEN: 403,
    NOT_FOUND: 404,
    INTERNAL_ERROR: 500
  }
}

export const API_ENDPOINTS = {
  AUTH: {
    LOGIN: '/auth/login',
    REGISTER: '/auth/register',
    LOGOUT: '/auth/logout',
    REFRESH: '/auth/refresh',
    PROFILE: '/auth/profile'
  },
  TASKS: {
    LIST: '/tasks/',
    CREATE: '/tasks/create',
    DETAIL: (id) => `/tasks/${id}`,
    UPDATE: (id) => `/tasks/${id}`,
    DELETE: (id) => `/tasks/${id}`,
    RESULTS: (id) => `/tasks/${id}/results`,
    CANCEL: (id) => `/tasks/${id}/cancel`,
    LOGS: (id) => `/tasks/${id}/logs`
  },
  SCAN: {
    PORT: '/scan/port-scan',
    INFO_LEAK: '/scan/info-leak',
    DIR: '/scan/dir-scan',
    SUBDOMAIN: '/scan/subdomain',
    COMPREHENSIVE: '/scan/comprehensive'
  },
  AWVS: {
    TARGETS: '/awvs/targets',
    TARGET: (id) => `/awvs/target/${id}`,
    SCAN: '/awvs/scan',
    SCANS: '/awvs/scans',
    VULNERABILITIES: (id) => `/awvs/vulnerabilities/${id}`,
    HEALTH: '/awvs/health'
  },
  POC: {
    TYPES: '/poc/types',
    SCAN: '/poc/scan',
    INFO: (type) => `/poc/info/${type}`
  },
  AI_AGENTS: {
    SCAN: '/ai_agents/scan',
    TASKS: '/ai_agents/tasks',
    TASK: (id) => `/ai_agents/tasks/${id}`,
    CONFIG: '/ai_agents/config',
    TOOLS: '/ai_agents/tools'
  },
  AI: {
    CHAT: '/ai/chat',
    INSTANCES: '/ai/chat/instances',
    INSTANCE: (id) => `/ai/chat/instances/${id}`
  },
  REPORTS: {
    LIST: '/reports/',
    CREATE: '/reports/',
    DETAIL: (id) => `/reports/${id}`,
    EXPORT: (id) => `/reports/${id}/export`,
    PREVIEW: (id) => `/reports/${id}/preview`
  },
  VULNERABILITIES: {
    LIST: '/kb/vulnerabilities',
    DETAIL: (id) => `/kb/vulnerabilities/${id}`,
    SEARCH: '/kb/vulnerabilities'
  },
  USER: {
    PROFILE: '/user/profile',
    PERMISSIONS: '/user/permissions',
    LIST: '/user/list'
  },
  NOTIFICATIONS: {
    LIST: '/notifications/',
    DETAIL: (id) => `/notifications/${id}`,
    UNREAD_COUNT: '/notifications/count/unread'
  },
  SETTINGS: {
    LIST: '/settings/',
    SYSTEM_INFO: '/settings/system-info',
    STATISTICS: '/settings/statistics'
  }
}

export default TEST_CONFIG
