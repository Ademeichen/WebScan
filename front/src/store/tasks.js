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
  const queuedTasks = computed(() => tasks.value.filter(t => t.status === 'queued' || t.status === 'pending'))

  function setTasks(newTasks) {
    tasks.value = newTasks
    saveToStorage({ tasks: newTasks, currentTask: currentTask.value })
  }

  function addTask(task) {
    const normalizedTask = {
      ...task,
      id: String(task.id || task.task_id),
      task_id: String(task.id || task.task_id)
    }
    const existingIndex = tasks.value.findIndex(t => t.id === normalizedTask.id || t.task_id === normalizedTask.task_id)
    if (existingIndex === -1) {
      tasks.value.unshift(normalizedTask)
    } else {
      tasks.value[existingIndex] = { ...tasks.value[existingIndex], ...normalizedTask }
    }
    saveToStorage({ tasks: tasks.value, currentTask: currentTask.value })
  }

  function updateTask(taskId, updates) {
    const normalizedId = String(taskId)
    const index = tasks.value.findIndex(t => 
      String(t.id) === normalizedId || String(t.task_id) === normalizedId
    )
    if (index !== -1) {
      tasks.value[index] = { ...tasks.value[index], ...updates }
      saveToStorage({ tasks: tasks.value, currentTask: currentTask.value })
    }
  }

  function updateTaskProgress(taskId, progress) {
    updateTask(taskId, { progress })
  }

  function updateTaskStatus(taskId, status, extra = {}) {
    updateTask(taskId, { status, ...extra })
  }

  function completeTask(taskId, result) {
    updateTask(taskId, { 
      status: 'completed', 
      progress: 100, 
      result,
      completed_at: new Date().toISOString()
    })
  }

  function failTask(taskId, errorMessage) {
    updateTask(taskId, { 
      status: 'failed', 
      error_message: errorMessage
    })
  }

  function getTaskById(taskId) {
    const normalizedId = String(taskId)
    return tasks.value.find(t => 
      String(t.id) === normalizedId || String(t.task_id) === normalizedId
    )
  }

  function removeTask(taskId) {
    const normalizedId = String(taskId)
    tasks.value = tasks.value.filter(t => 
      String(t.id) !== normalizedId && String(t.task_id) !== normalizedId
    )
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
    queuedTasks,
    setTasks,
    addTask,
    updateTask,
    updateTaskProgress,
    updateTaskStatus,
    completeTask,
    failTask,
    getTaskById,
    removeTask,
    setCurrentTask,
    setLoading,
    setError,
    clearError,
    clearTasks
  }
})
