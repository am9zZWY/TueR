export interface SearchResult {
  id: number
  title: string
  url: string
  description: string
  summary: string,
  score?: number
  tags?: string[]
}
