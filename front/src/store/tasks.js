import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

const STORAGE_KEY = 'tasks_store'

const loadFromStorage = () => {
  try {
    const stored = localStorage.getItem(STORAGE_KEY)
    if (stored) {
      return JSON.parse(stored)
    }
  } catch (error) {
    console.error('加载任务状态失败:', error)
    return null
  }
  return null
}

const saveToStorage = (state) => {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(state))
  } catch (error) {
    console.error('保存任务状态失败:', error)
  }
}

export const useTaskStore = defineStore('tasks', () => {
  const tasks = ref(loadFromStorage()?.tasks || [])
  const currentTask = ref(loadFromStorage()?.currentTask || null)
  const loading = ref(false)
  const error = ref(null)

  const taskCount = computed(() => tasks.value.length)
  const runningTasks = computed(() => tasks.value.filter(t => t.status === 'running'))
  const completedTasks = computed(() => tasks.value.filter(t => t.status === 'completed'))
  const failedTasks = computed(() => tasks.value.filter(t => t.status === 'failed'))

  function setTasks(newTasks) {
    tasks.value = newTasks
    saveToStorage({ tasks: newTasks, currentTask: currentTask.value })
  }

  function addTask(task) {
    tasks.value.unshift(task)
    saveToStorage({ tasks: tasks.value, currentTask: currentTask.value })
  }

  function updateTask(taskId, updates) {
    const index = tasks.value.findIndex(t => t.id === taskId)
    if (index !== -1) {
      tasks.value[index] = { ...tasks.value[index], ...updates }
      saveToStorage({ tasks: tasks.value, currentTask: currentTask.value })
    }
  }

  function removeTask(taskId) {
    tasks.value = tasks.value.filter(t => t.id !== taskId)
    saveToStorage({ tasks: tasks.value, currentTask: currentTask.value })
  }

  function setCurrentTask(task) {
    currentTask.value = task
    saveToStorage({ tasks: tasks.value, currentTask: task })
  }

  function setLoading(isLoading) {
    loading.value = isLoading
  }

  function setError(errorMessage) {
    error.value = errorMessage
  }

  function clearError() {
    error.value = null
  }

  function clearTasks() {
    tasks.value = []
    currentTask.value = null
    error.value = null
    localStorage.removeItem(STORAGE_KEY)
  }

  return {
    tasks,
    currentTask,
    loading,
    error,
    taskCount,
    runningTasks,
    completedTasks,
    failedTasks,
    setTasks,
    addTask,
    updateTask,
    removeTask,
    setCurrentTask,
    setLoading,
    setError,
    clearError,
    clearTasks
  }
})
