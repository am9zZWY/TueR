/**
 * Search result object
 */
export interface SearchResult {
  id: number
  title: string
  url: string
  description: string
  summary: string,
  score?: number
  tags?: string[]
}

/**
 * API response for search results
 */
export interface ApiSearchResultsResponse {
  query: string
  spellchecked_query?: string
  results: SearchResult[]
}

/**
 * API response for summary
 */
export interface ApiSummaryResponse {
  doc_id: number
  summary: string
}
