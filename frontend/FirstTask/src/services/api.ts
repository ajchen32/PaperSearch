import type { CitationSearchResponse } from '../types'

const API_BASE_URL = 'http://localhost:8000'

export async function searchPapers(query: string): Promise<CitationSearchResponse> {
  const response = await fetch(`${API_BASE_URL}/citation-search-rated`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      query,
      forward_limit: 3,
      backward_limit: 3,
    }),
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }))
    throw new Error(error.detail || `HTTP error! status: ${response.status}`)
  }

  return response.json()
}

