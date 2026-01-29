import { ref, computed, watch, onMounted, onUnmounted } from 'vue'

export function useAsyncData(apiCall, options = {}) {
  const { immediate = true, initialData = null } = options
  
  const data = ref(initialData)
  const loading = ref(false)
  const error = ref(null)
  
  const execute = async (...args) => {
    loading.value = true
    error.value = null
    
    try {
      const result = await apiCall(...args)
      data.value = result.data
      return result
    } catch (err) {
      error.value = err
      throw err
    } finally {
      loading.value = false
    }
  }
  
  const refresh = () => execute()
  
  if (immediate) {
    onMounted(() => {
      execute()
    })
  }
  
  return {
    data,
    loading,
    error,
    execute,
    refresh
  }
}

export function usePagination(fetchData, options = {}) {
  const { pageSize = 10 } = options
  
  const page = ref(1)
  const total = ref(0)
  const loading = ref(false)
  const data = ref([])
  
  const totalPages = computed(() => Math.ceil(total.value / pageSize))
  const hasNextPage = computed(() => page.value < totalPages.value)
  const hasPrevPage = computed(() => page.value > 1)
  
  const fetch = async () => {
    loading.value = true
    try {
      const result = await fetchData({
        page: page.value,
        pageSize
      })
      data.value = result.data.items || result.data
      total.value = result.data.pagination?.total || result.data.length
    } catch (error) {
      console.error('分页数据加载失败:', error)
    } finally {
      loading.value = false
    }
  }
  
  const nextPage = () => {
    if (hasNextPage.value) {
      page.value++
      fetch()
    }
  }
  
  const prevPage = () => {
    if (hasPrevPage.value) {
      page.value--
      fetch()
    }
  }
  
  const goToPage = (pageNum) => {
    if (pageNum >= 1 && pageNum <= totalPages.value) {
      page.value = pageNum
      fetch()
    }
  }
  
  const reset = () => {
    page.value = 1
    total.value = 0
    data.value = []
  }
  
  return {
    page,
    total,
    totalPages,
    hasNextPage,
    hasPrevPage,
    loading,
    data,
    fetch,
    nextPage,
    prevPage,
    goToPage,
    reset
  }
}

export function useSearch(fetchData, options = {}) {
  const { debounceMs = 300 } = options
  
  const query = ref('')
  const loading = ref(false)
  const data = ref([])
  const error = ref(null)
  
  let debounceTimer = null
  
  const search = async (searchQuery = query.value) => {
    loading.value = true
    error.value = null
    
    try {
      const result = await fetchData({ search: searchQuery })
      data.value = result.data
    } catch (err) {
      error.value = err
      console.error('搜索失败:', err)
    } finally {
      loading.value = false
    }
  }
  
  const debouncedSearch = (searchQuery) => {
    clearTimeout(debounceTimer)
    debounceTimer = setTimeout(() => {
      search(searchQuery)
    }, debounceMs)
  }
  
  const clear = () => {
    query.value = ''
    data.value = []
    error.value = null
  }
  
  watch(query, (newQuery) => {
    debouncedSearch(newQuery)
  })
  
  return {
    query,
    loading,
    data,
    error,
    search,
    debouncedSearch,
    clear
  }
}

export function useDialog(options = {}) {
  const { title = '确认', message = '确定要执行此操作吗？' } = options
  
  const visible = ref(false)
  const loading = ref(false)
  const resolve = ref(null)
  const reject = ref(null)
  
  const show = () => {
    visible.value = true
    return new Promise((res, rej) => {
      resolve.value = res
      reject.value = rej
    })
  }
  
  const confirm = async () => {
    loading.value = true
    try {
      await resolve.value?.()
      visible.value = false
    } catch (error) {
      console.error('确认操作失败:', error)
    } finally {
      loading.value = false
    }
  }
  
  const cancel = () => {
    reject.value?.()
    visible.value = false
  }
  
  return {
    visible,
    loading,
    title,
    message,
    show,
    confirm,
    cancel
  }
}

export function usePolling(callback, options = {}) {
  const { interval = 5000, immediate = true } = options
  
  const isActive = ref(false)
  let timer = null
  
  const start = () => {
    if (isActive.value) return
    
    isActive.value = true
    if (immediate) {
      callback()
    }
    timer = setInterval(callback, interval)
  }
  
  const stop = () => {
    isActive.value = false
    if (timer) {
      clearInterval(timer)
      timer = null
    }
  }
  
  const toggle = () => {
    if (isActive.value) {
      stop()
    } else {
      start()
    }
  }
  
  onUnmounted(() => {
    stop()
  })
  
  return {
    isActive,
    start,
    stop,
    toggle
  }
}

export function useLocalStorage(key, defaultValue = null) {
  const stored = localStorage.getItem(key)
  const value = ref(stored ? JSON.parse(stored) : defaultValue)
  
  const save = () => {
    localStorage.setItem(key, JSON.stringify(value.value))
  }
  
  watch(value, save, { deep: true })
  
  const reset = () => {
    value.value = defaultValue
    localStorage.removeItem(key)
  }
  
  return {
    value,
    save,
    reset
  }
}

export function useWindowSize() {
  const width = ref(window.innerWidth)
  const height = ref(window.innerHeight)
  
  const update = () => {
    width.value = window.innerWidth
    height.value = window.innerHeight
  }
  
  onMounted(() => {
    window.addEventListener('resize', update)
  })
  
  onUnmounted(() => {
    window.removeEventListener('resize', update)
  })
  
  const isMobile = computed(() => width.value < 768)
  const isTablet = computed(() => width.value >= 768 && width.value < 1024)
  const isDesktop = computed(() => width.value >= 1024)
  
  return {
    width,
    height,
    isMobile,
    isTablet,
    isDesktop
  }
}

export function useCopyToClipboard() {
  const copied = ref(false)
  const error = ref(null)
  
  const copy = async (text) => {
    try {
      await navigator.clipboard.writeText(text)
      copied.value = true
      error.value = null
      
      setTimeout(() => {
        copied.value = false
      }, 2000)
    } catch (err) {
      error.value = err
      copied.value = false
    }
  }
  
  return {
    copied,
    error,
    copy
  }
}

export default {
  useAsyncData,
  usePagination,
  useSearch,
  useDialog,
  usePolling,
  useLocalStorage,
  useWindowSize,
  useCopyToClipboard
}
