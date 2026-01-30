export const dateUtils = {
  formatDate(date, format = 'YYYY-MM-DD HH:mm:ss') {
    if (!date) return ''
    
    const d = new Date(date)
    if (isNaN(d.getTime())) return ''
    
    const year = d.getFullYear()
    const month = String(d.getMonth() + 1).padStart(2, '0')
    const day = String(d.getDate()).padStart(2, '0')
    const hours = String(d.getHours()).padStart(2, '0')
    const minutes = String(d.getMinutes()).padStart(2, '0')
    const seconds = String(d.getSeconds()).padStart(2, '0')
    
    return format
      .replace('YYYY', year)
      .replace('MM', month)
      .replace('DD', day)
      .replace('HH', hours)
      .replace('mm', minutes)
      .replace('ss', seconds)
  },

  formatRelative(date) {
    if (!date) return ''
    
    const now = new Date()
    const d = new Date(date)
    const diff = now - d
    const seconds = Math.floor(diff / 1000)
    const minutes = Math.floor(seconds / 60)
    const hours = Math.floor(minutes / 60)
    const days = Math.floor(hours / 24)
    const months = Math.floor(days / 30)
    const years = Math.floor(days / 365)
    
    if (years > 0) return `${years}年前`
    if (months > 0) return `${months}个月前`
    if (days > 0) return `${days}天前`
    if (hours > 0) return `${hours}小时前`
    if (minutes > 0) return `${minutes}分钟前`
    if (seconds > 0) return `${seconds}秒前`
    return '刚刚'
  },

  formatDuration(seconds) {
    if (!seconds) return '0秒'
    
    const hours = Math.floor(seconds / 3600)
    const minutes = Math.floor((seconds % 3600) / 60)
    const secs = Math.floor(seconds % 60)
    
    if (hours > 0) {
      return `${hours}小时${minutes}分钟${secs}秒`
    }
    if (minutes > 0) {
      return `${minutes}分钟${secs}秒`
    }
    return `${secs}秒`
  },

  isToday(date) {
    const today = new Date()
    const d = new Date(date)
    return today.toDateString() === d.toDateString()
  },

  isYesterday(date) {
    const yesterday = new Date()
    yesterday.setDate(yesterday.getDate() - 1)
    const d = new Date(date)
    return yesterday.toDateString() === d.toDateString()
  },

  startOfDay(date) {
    const d = new Date(date)
    d.setHours(0, 0, 0, 0)
    return d
  },

  endOfDay(date) {
    const d = new Date(date)
    d.setHours(23, 59, 59, 999)
    return d
  },

  addDays(date, days) {
    const d = new Date(date)
    d.setDate(d.getDate() + days)
    return d
  },

  subtractDays(date, days) {
    const d = new Date(date)
    d.setDate(d.getDate() - days)
    return d
  },

  getDaysDiff(date1, date2) {
    const d1 = new Date(date1)
    const d2 = new Date(date2)
    const diffTime = Math.abs(d2 - d1)
    return Math.ceil(diffTime / (1000 * 60 * 60 * 24))
  }
}

export const stringUtils = {
  truncate(str, length = 50, suffix = '...') {
    if (!str || str.length <= length) return str
    return str.substring(0, length) + suffix
  },

  capitalize(str) {
    if (!str) return ''
    return str.charAt(0).toUpperCase() + str.slice(1)
  },

  camelCase(str) {
    return str
      .replace(/[-_\s]+(.)?/g, (_, c) => (c ? c.toUpperCase() : ''))
      .replace(/^(.)/, c => c.toLowerCase())
  },

  kebabCase(str) {
    return str
      .replace(/([a-z])([A-Z])/g, '$1-$2')
      .replace(/[\s_]+/g, '-')
      .toLowerCase()
  },

  snakeCase(str) {
    return str
      .replace(/([a-z])([A-Z])/g, '$1_$2')
      .replace(/[\s-]+/g, '_')
      .toLowerCase()
  },

  slugify(str) {
    return str
      .toLowerCase()
      .trim()
      .replace(/[^\w\s-]/g, '')
      .replace(/[\s_-]+/g, '-')
      .replace(/^-+|-+$/g, '')
  },

  generateId(prefix = 'id') {
    return `${prefix}-${Math.random().toString(36).substr(2, 9)}`
  },

  hashCode(str) {
    let hash = 0
    for (let i = 0; i < str.length; i++) {
      const char = str.charCodeAt(i)
      hash = ((hash << 5) - hash) + char
      hash = hash & hash
    }
    return hash
  }
}

export const numberUtils = {
  format(num, decimals = 2) {
    if (num === null || num === undefined) return ''
    return Number(num).toFixed(decimals)
  },

  formatCurrency(num, currency = 'CNY') {
    if (num === null || num === undefined) return ''
    return new Intl.NumberFormat('zh-CN', {
      style: 'currency',
      currency
    }).format(num)
  },

  formatPercent(num, decimals = 2) {
    if (num === null || num === undefined) return ''
    return `${Number(num * 100).toFixed(decimals)}%`
  },

  formatBytes(bytes) {
    if (bytes === 0) return '0 B'
    const k = 1024
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return `${parseFloat((bytes / Math.pow(k, i)).toFixed(2))} ${sizes[i]}`
  },

  formatNumber(num) {
    if (num === null || num === undefined) return ''
    return new Intl.NumberFormat('zh-CN').format(num)
  },

  clamp(num, min, max) {
    return Math.min(Math.max(num, min), max)
  },

  random(min, max) {
    return Math.floor(Math.random() * (max - min + 1)) + min
  },

  round(num, decimals = 0) {
    const factor = Math.pow(10, decimals)
    return Math.round(num * factor) / factor
  }
}

export const arrayUtils = {
  unique(arr, key = null) {
    if (key) {
      const seen = new Set()
      return arr.filter(item => {
        const val = item[key]
        if (seen.has(val)) return false
        seen.add(val)
        return true
      })
    }
    return [...new Set(arr)]
  },

  groupBy(arr, key) {
    return arr.reduce((result, item) => {
      const group = item[key]
      if (!result[group]) {
        result[group] = []
      }
      result[group].push(item)
      return result
    }, {})
  },

  sortBy(arr, key, order = 'asc') {
    return [...arr].sort((a, b) => {
      const aVal = a[key]
      const bVal = b[key]
      if (aVal < bVal) return order === 'asc' ? -1 : 1
      if (aVal > bVal) return order === 'asc' ? 1 : -1
      return 0
    })
  },

  chunk(arr, size) {
    const result = []
    for (let i = 0; i < arr.length; i += size) {
      result.push(arr.slice(i, i + size))
    }
    return result
  },

  flatten(arr) {
    return arr.reduce((acc, val) => 
      Array.isArray(val) ? acc.concat(arrayUtils.flatten(val)) : acc.concat(val), 
      []
    )
  },

  shuffle(arr) {
    const result = [...arr]
    for (let i = result.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1))
      ;[result[i], result[j]] = [result[j], result[i]]
    }
    return result
  },

  sample(arr, count = 1) {
    const shuffled = this.shuffle(arr)
    return shuffled.slice(0, count)
  },

  difference(arr1, arr2) {
    return arr1.filter(x => !arr2.includes(x))
  },

  intersection(arr1, arr2) {
    return arr1.filter(x => arr2.includes(x))
  },

  union(arr1, arr2) {
    return this.unique([...arr1, ...arr2])
  }
}

export const objectUtils = {
  deepClone(obj) {
    if (obj === null || typeof obj !== 'object') return obj
    if (obj instanceof Date) return new Date(obj)
    if (obj instanceof Array) return obj.map(item => this.deepClone(item))
    
    const cloned = {}
    for (const key in obj) {
      if (Object.prototype.hasOwnProperty.call(obj, key)) {
        cloned[key] = this.deepClone(obj[key])
      }
    }
    return cloned
  },

  deepMerge(target, source) {
    const output = { ...target }
    
    if (this.isObject(target) && this.isObject(source)) {
      Object.keys(source).forEach(key => {
        if (this.isObject(source[key])) {
          if (!(key in target)) {
            Object.assign(output, { [key]: source[key] })
          } else {
            output[key] = this.deepMerge(target[key], source[key])
          }
        } else {
          Object.assign(output, { [key]: source[key] })
        }
      })
    }
    
    return output
  },

  isObject(item) {
    return item && typeof item === 'object' && !Array.isArray(item)
  },

  isEmpty(obj) {
    if (obj === null || obj === undefined) return true
    if (Array.isArray(obj)) return obj.length === 0
    if (typeof obj === 'object') return Object.keys(obj).length === 0
    return false
  },

  pick(obj, keys) {
    return keys.reduce((result, key) => {
      if (key in obj) {
        result[key] = obj[key]
      }
      return result
    }, {})
  },

  omit(obj, keys) {
    const result = { ...obj }
    keys.forEach(key => delete result[key])
    return result
  },

  get(obj, path, defaultValue = undefined) {
    const keys = path.split('.')
    let result = obj
    
    for (const key of keys) {
      if (result === null || result === undefined) {
        return defaultValue
      }
      result = result[key]
    }
    
    return result !== undefined ? result : defaultValue
  },

  set(obj, path, value) {
    const keys = path.split('.')
    let current = obj
    
    for (let i = 0; i < keys.length - 1; i++) {
      const key = keys[i]
      if (!(key in current)) {
        current[key] = {}
      }
      current = current[key]
    }
    
    current[keys[keys.length - 1]] = value
    return obj
  }
}

export const validationUtils = {
  isEmail(email) {
    const pattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
    return pattern.test(email)
  },

  isPhone(phone) {
    const pattern = /^1[3-9]\d{9}$/
    return pattern.test(phone)
  },

  isUrl(url) {
    try {
      new URL(url)
      return true
    } catch {
      return false
    }
  },

  isIP(ip) {
    const pattern = /^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$/
    return pattern.test(ip)
  },

  isPort(port) {
    const num = parseInt(port)
    return !isNaN(num) && num >= 1 && num <= 65535
  },

  isNumber(value) {
    return !isNaN(parseFloat(value)) && isFinite(value)
  },

  isInteger(value) {
    return Number.isInteger(Number(value))
  },

  isPositive(value) {
    return this.isNumber(value) && Number(value) > 0
  },

  isNegative(value) {
    return this.isNumber(value) && Number(value) < 0
  },

  isBetween(value, min, max) {
    return this.isNumber(value) && value >= min && value <= max
  },

  isLength(value, min, max) {
    const len = String(value).length
    return len >= min && len <= max
  }
}

export const storageUtils = {
  set(key, value, ttl = null) {
    const item = {
      value,
      timestamp: Date.now(),
      ttl
    }
    localStorage.setItem(key, JSON.stringify(item))
  },

  get(key) {
    const item = localStorage.getItem(key)
    if (!item) return null
    
    try {
      const parsed = JSON.parse(item)
      
      if (parsed.ttl) {
        const now = Date.now()
        if (now - parsed.timestamp > parsed.ttl) {
          this.remove(key)
          return null
        }
      }
      
      return parsed.value
    } catch {
      return null
    }
  },

  remove(key) {
    localStorage.removeItem(key)
  },

  clear() {
    localStorage.clear()
  },

  setSession(key, value) {
    sessionStorage.setItem(key, JSON.stringify(value))
  },

  getSession(key) {
    const item = sessionStorage.getItem(key)
    if (!item) return null
    
    try {
      return JSON.parse(item)
    } catch {
      return null
    }
  },

  removeSession(key) {
    sessionStorage.removeItem(key)
  },

  clearSession() {
    sessionStorage.clear()
  }
}

export default {
  date: dateUtils,
  string: stringUtils,
  number: numberUtils,
  array: arrayUtils,
  object: objectUtils,
  validation: validationUtils,
  storage: storageUtils
}
