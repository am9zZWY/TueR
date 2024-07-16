import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import { ENGINE_ENDPOINT } from '@/configuration'

export interface SearchResult {
  id: number
  title: string
  url: string
  description: string
  summary: string,
  score?: number
  tags?: string[]
}

const dummyResults: SearchResult[] = [
  {
    id: 1,
    title: 'Dummy result',
    url: 'https://example.com',
    description: 'This is a dummy result',
    summary: 'This is a dummy summary'
  },
  {
    id: 2,
    title: 'Another dummy result',
    url: 'https://uni-tuebingen.de/en',
    description: 'This is another dummy result',
    summary: 'This is another dummy summary'
  }
]

export const useSearchStore = defineStore('search', () => {
  const internalResults = ref<SearchResult[]>([])
  const results = computed(() => {
    const results = internalResults.value
    // Sort results by score
    results.sort((a, b) => (b.score ?? 0) - (a.score ?? 0))
    return results
  })

  function search(query: string) {
    fetch(`${ENGINE_ENDPOINT}/search?query=${query}`)
      .then((response) => response.json())
      .then((data) => {
        internalResults.value = data
      })
  }

  return {
    results,
    search
  }
})
