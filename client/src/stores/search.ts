import { ref } from 'vue'
import { defineStore } from 'pinia'
import { ENGINE_ENDPOINT } from '@/configuration'

export interface SearchResult {
  title: string
  url: string
  description: string
}

const dummyResults: SearchResult[] = [
  {
    title: 'Dummy result',
    url: 'https://example.com',
    description: 'This is a dummy result'
  },
  {
    title: 'Another dummy result',
    url: 'https://example.com',
    description: 'This is another dummy result'
  }
]

export const useSearchStore = defineStore('search', () => {
  const results = ref([] as SearchResult[])

  function search(query: string) {
    fetch(`${ENGINE_ENDPOINT}/search?q=${query}`)
      .then((response) => response.json())
      .then((data) => {
        results.value = data
      }).catch(() => {
      results.value = dummyResults
    })
  }

  return {
    results,
    search
  }
})
