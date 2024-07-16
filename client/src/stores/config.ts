import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useConfigStore = defineStore('config', () => {
  const configuration = ref({} as Record<string, any>)

  /**
   * Save configuration to local storage
   */
  const saveConfigurationToLocalStorage = () => {
    localStorage.setItem('configuration', JSON.stringify(configuration.value))
  }

  /**
   * Load configuration from local storage
   */
  const loadConfigurationFromLocalStorage = () => {
    const storedConfiguration = localStorage.getItem('configuration')
    if (storedConfiguration) {
      configuration.value = JSON.parse(storedConfiguration)
    }
  }

  /**
   * Set configuration value
   * @param key Configuration key
   * @param value Configuration value
   */
  const setConfig = (key: string, value: any) => {
    configuration.value[key] = value
    saveConfigurationToLocalStorage()
  }

  /**
   * Toggle configuration value
   * @param key Configuration key
   */
  const toggleConfig = (key: string) => {
    // Check if key exists in the configuration
    if (!(key in configuration.value)) {
      setConfig(key, true)
    } else {
      configuration.value[key] = !configuration.value[key]
      saveConfigurationToLocalStorage()
    }
  }

  /**
   * Get configuration value
   * @param key Configuration key
   */
  const getConfig = (key: string) => {
    return configuration.value[key]
  }

  // Load configuration from local storage
  loadConfigurationFromLocalStorage()

  return {
    setConfig,
    toggleConfig,
    getConfig
  }
})
