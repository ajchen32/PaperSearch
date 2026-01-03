export interface Paper {
  paperId: string
  title: string
  abstract?: string
  authors?: Array<{ name: string }>
  year?: number
  citationCount?: number
  referenceCount?: number
  url?: string
  relevance_rating?: 'Perfectly Relevant' | 'Relevant' | 'Somewhat Relevant'
}

export interface QueryComponent {
  component: string
  description: string
  keywords: string[]
}

export interface QueryDecompositionResponse {
  original_query: string
  components: QueryComponent[]
  main_concepts: string[]
  relationships: string[]
}

export interface PaperWithNestedCitations {
  paper: Paper
  nested_forward_citations: Paper[]
  nested_backward_citations: Paper[]
}

export interface CitationSearchResponse {
  query: string
  query_decomposition: QueryDecompositionResponse
  most_relevant_paper: Paper
  forward_citations: PaperWithNestedCitations[]
  backward_citations: PaperWithNestedCitations[]
  total_forward: number
  total_backward: number
}

