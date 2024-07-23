import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import { ENGINE_ENDPOINT } from '@/configuration'
import type { ApiSearchResultsResponse, SearchResult } from '@/types'
import { useLocal } from '@/stores/local'

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
  const localStore = useLocal()

  const lastQuery = ref('')
  const internalResults = ref<SearchResult[]>([])
  const results = computed(() => {
    const results = internalResults.value
    // Sort results by score
    results.sort((a, b) => (b.score ?? 0) - (a.score ?? 0))
    return results
  })
  const lastSearches = ref<string[]>(localStore.getConfig('lastSearches') ?? [])

  function search(query: string) {
    if (query === '') {
      internalResults.value = []
      return
    }

    lastQuery.value = query

    return fetch(`${ENGINE_ENDPOINT}/search?query=${query}`)
      .then((response) => response.json())
      .then((data: ApiSearchResultsResponse) => {
        internalResults.value = data.results
        lastSearches.value.push(query)
        localStore.setConfig('lastSearches', lastSearches.value)
      })
  }

  return {
    results,
    lastSearches,
    lastQuery,
    search
  }
})
