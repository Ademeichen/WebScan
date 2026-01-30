export class ApiResponse {
  constructor(data = null, message = '', code = 200, success = true) {
    this.code = code
    this.success = success
    this.message = message
    this.data = data
    this.timestamp = new Date().toISOString()
  }

  static success(data, message = '操作成功') {
    return new ApiResponse(data, message, 200, true)
  }

  static error(message = '操作失败', code = 500, data = null) {
    return new ApiResponse(data, message, code, false)
  }

  static created(data, message = '创建成功') {
    return new ApiResponse(data, message, 201, true)
  }

  static updated(data, message = '更新成功') {
    return new ApiResponse(data, message, 200, true)
  }

  static deleted(message = '删除成功') {
    return new ApiResponse(null, message, 200, true)
  }

  static notFound(message = '资源不存在') {
    return new ApiResponse(null, message, 404, false)
  }

  static unauthorized(message = '未授权，请重新登录') {
    return new ApiResponse(null, message, 401, false)
  }

  static forbidden(message = '没有权限访问') {
    return new ApiResponse(null, message, 403, false)
  }

  static validationError(message = '数据验证失败', errors = null) {
    return new ApiResponse(errors, message, 422, false)
  }

  static serverError(message = '服务器错误，请稍后重试') {
    return new ApiResponse(null, message, 500, false)
  }

  static networkError(message = '网络连接失败，请检查网络设置') {
    return new ApiResponse(null, message, 0, false)
  }

  static timeout(message = '请求超时，请稍后重试') {
    return new ApiResponse(null, message, 408, false)
  }

  static paginated(data, pagination = {}) {
    return new ApiResponse({
      items: data,
      pagination: {
        page: pagination.page || 1,
        pageSize: pagination.pageSize || 10,
        total: pagination.total || 0,
        totalPages: Math.ceil((pagination.total || 0) / (pagination.pageSize || 10))
      }
    }, '获取成功', 200, true)
  }
}

export function handleResponse(response) {
  if (!response) {
    return ApiResponse.error('响应数据为空')
  }

  const { code, data, message } = response

  if (code === 200 || code === 201) {
    return ApiResponse.success(data, message || '操作成功')
  } else if (code === 401) {
    return ApiResponse.unauthorized(message)
  } else if (code === 403) {
    return ApiResponse.forbidden(message)
  } else if (code === 404) {
    return ApiResponse.notFound(message)
  } else if (code === 422) {
    return ApiResponse.validationError(message, data)
  } else if (code >= 500) {
    return ApiResponse.serverError(message)
  } else {
    return ApiResponse.error(message || '操作失败', code, data)
  }
}

export function handleApiError(error) {
  if (!error) {
    return ApiResponse.networkError('未知错误')
  }

  if (error.code === 'ECONNABORTED') {
    return ApiResponse.timeout()
  }

  if (error.response) {
    const { status, data } = error.response
    return handleResponse({
      code: status,
      data: data?.data || data,
      message: data?.message || error.message,
      success: false
    })
  }

  if (error.request) {
    return ApiResponse.networkError()
  }

  return ApiResponse.error(error.message || '操作失败', 0)
}

export function createApiWrapper(apiFunction) {
  return async function(...args) {
    try {
      const response = await apiFunction(...args)
      return handleResponse(response)
    } catch (error) {
      return handleApiError(error)
    }
  }
}

export function wrapApiObject(apiObject) {
  const wrapped = {}
  for (const [key, value] of Object.entries(apiObject)) {
    if (typeof value === 'function') {
      wrapped[key] = createApiWrapper(value)
    } else {
      wrapped[key] = value
    }
  }
  return wrapped
}

export default {
  ApiResponse,
  handleResponse,
  handleApiError,
  createApiWrapper,
  wrapApiObject
}
