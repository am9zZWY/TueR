import { defineStore } from 'pinia'
import { ref } from 'vue'

const KEY = 'tuer'

export const useLocal = defineStore('config', () => {
  const local = ref({} as Record<string, any>)

  /**
   * Save configuration to local storage
   */
  const saveToLocalStorage = () => {
    localStorage.setItem(KEY, JSON.stringify(local.value))
  }

  /**
   * Load configuration from local storage
   */
  const loadFromLocalStorage = () => {
    const stored = localStorage.getItem(KEY)
    if (stored) {
      local.value = JSON.parse(stored)
    }
  }

  /**
   * Set configuration value
   * @param key Configuration key
   * @param value Configuration value
   */
  const setConfig = (key: string, value: any) => {
    local.value[key] = value
    saveToLocalStorage()
  }

  /**
   * Get configuration value
   * @param key Configuration key
   */
  const getConfig = (key: string) => {
    return local.value[key]
  }

  // Load configuration from local storage
  loadFromLocalStorage()

  return {
    setConfig,
    getConfig
  }
})
