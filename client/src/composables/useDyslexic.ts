import { ref } from 'vue'
import { useConfigStore } from '@/stores/config'

export default function useDyslexic() {
  const isDyslexic = ref(false) // Check if the user prefers dyslexic font
  const defaultFont = ref(document.body.style.fontFamily) // Get current font
  const dyslexicFont = 'Comic Sans MS' // Dyslexic-friendly font

  const configStore = useConfigStore()
  isDyslexic.value = configStore.getConfig('dyslexicFont')

  const toggleDyslexicFont = () => {
    isDyslexic.value = !isDyslexic.value
    configStore.setConfig('dyslexicFont', isDyslexic.value)

    // Save the configuration
    if (isDyslexic.value) {
      // Set the font to a person with dyslexia-friendly font
      document.body.style.fontFamily = dyslexicFont
    } else {
      // Set the font to the default font
      document.body.style.fontFamily = defaultFont.value
    }
  }

  return {
    isDyslexic,
    toggleDyslexicFont
  }
}
