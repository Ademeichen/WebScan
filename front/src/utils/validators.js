export const validators = {
  required: (value) => {
    if (value === null || value === undefined || value === '') {
      return '此字段为必填项'
    }
    return null
  },

  url: (value) => {
    if (!value) return null
    try {
      new URL(value)
      return null
    } catch {
      return '请输入有效的URL地址'
    }
  },

  ipAddress: (value) => {
    if (!value) return null
    const parts = value.split('.')
    if (parts.length !== 4) {
      return '请输入有效的IP地址'
    }
    for (const part of parts) {
      const num = parseInt(part)
      if (isNaN(num) || num < 0 || num > 255) {
        return '请输入有效的IP地址'
      }
    }
    return null
  },

  port: (value) => {
    if (!value) return null
    const port = parseInt(value)
    if (isNaN(port) || port < 1 || port > 65535) {
      return '端口号必须在1-65535之间'
    }
    return null
  },

  email: (value) => {
    if (!value) return null
    const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
    if (!emailPattern.test(value)) {
      return '请输入有效的邮箱地址'
    }
    return null
  },

  minLength: (min) => (value) => {
    if (!value) return null
    if (value.length < min) {
      return `最少需要${min}个字符`
    }
    return null
  },

  maxLength: (max) => (value) => {
    if (!value) return null
    if (value.length > max) {
      return `最多允许${max}个字符`
    }
    return null
  },

  pattern: (regex, message) => (value) => {
    if (!value) return null
    if (!regex.test(value)) {
      return message || '格式不正确'
    }
    return null
  },

  numeric: (value) => {
    if (!value) return null
    if (!/^\d+$/.test(value)) {
      return '请输入数字'
    }
    return null
  },

  range: (min, max) => (value) => {
    if (!value) return null
    const num = parseFloat(value)
    if (isNaN(num) || num < min || num > max) {
      return `数值必须在${min}到${max}之间`
    }
    return null
  }
}

export const validateField = (value, rules) => {
  for (const rule of rules) {
    const error = rule(value)
    if (error) {
      return error
    }
  }
  return null
}

export const validateForm = (formData, schema) => {
  const errors = {}
  let isValid = true

  for (const [field, rules] of Object.entries(schema)) {
    const value = formData[field]
    const error = validateField(value, rules)
    if (error) {
      errors[field] = error
      isValid = false
    }
  }

  return { isValid, errors }
}

export const debounce = (fn, delay = 300) => {
  let timeoutId
  return (...args) => {
    clearTimeout(timeoutId)
    timeoutId = setTimeout(() => fn(...args), delay)
  }
}

export const throttle = (fn, limit = 300) => {
  let inThrottle
  return (...args) => {
    if (!inThrottle) {
      fn(...args)
      inThrottle = true
      setTimeout(() => inThrottle = false, limit)
    }
  }
}
