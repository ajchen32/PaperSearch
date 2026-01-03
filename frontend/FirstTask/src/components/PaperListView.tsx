import type { CitationSearchResponse, Paper } from '../types'

interface PaperListViewProps {
  data: CitationSearchResponse
}

interface PaperWithSource extends Paper {
  source: string // Where the paper came from (most_relevant, forward, backward, etc.)
  level: number
}

export default function PaperListView({ data }: PaperListViewProps) {
  // Collect all papers with their source information
  const allPapers: PaperWithSource[] = []

  // Add most relevant paper
  allPapers.push({
    ...data.most_relevant_paper,
    source: 'Most Relevant Paper',
    level: 0,
  })

  // Add forward citations
  data.forward_citations.forEach((paperWithNested) => {
    allPapers.push({
      ...paperWithNested.paper,
      source: 'Forward Citation',
      level: 1,
    })

    // Add nested forward citations
    paperWithNested.nested_forward_citations.forEach((nestedPaper) => {
      allPapers.push({
        ...nestedPaper,
        source: 'Nested Forward Citation',
        level: 2,
      })
    })

    // Add nested backward citations from forward citations
    paperWithNested.nested_backward_citations.forEach((nestedPaper) => {
      allPapers.push({
        ...nestedPaper,
        source: 'Nested Backward Citation (from Forward)',
        level: 2,
      })
    })
  })

  // Add backward citations
  data.backward_citations.forEach((paperWithNested) => {
    allPapers.push({
      ...paperWithNested.paper,
      source: 'Backward Citation',
      level: 1,
    })

    // Add nested backward citations
    paperWithNested.nested_backward_citations.forEach((nestedPaper) => {
      allPapers.push({
        ...nestedPaper,
        source: 'Nested Backward Citation',
        level: 2,
      })
    })

    // Add nested forward citations from backward citations
    paperWithNested.nested_forward_citations.forEach((nestedPaper) => {
      allPapers.push({
        ...nestedPaper,
        source: 'Nested Forward Citation (from Backward)',
        level: 2,
      })
    })
  })

  // Sort by relevance rating
  const ratingOrder: Record<string, number> = {
    'Perfectly Relevant': 1,
    'Relevant': 2,
    'Somewhat Relevant': 3,
  }

  const sortedPapers = [...allPapers].sort((a, b) => {
    const aRating = a.relevance_rating || 'Somewhat Relevant'
    const bRating = b.relevance_rating || 'Somewhat Relevant'
    const aOrder = ratingOrder[aRating] || 999
    const bOrder = ratingOrder[bRating] || 999

    if (aOrder !== bOrder) {
      return aOrder - bOrder
    }

    // If same rating, sort by citation count (higher first)
    const aCitations = a.citationCount || 0
    const bCitations = b.citationCount || 0
    return bCitations - aCitations
  })

  const getRatingColor = (rating?: string) => {
    switch (rating) {
      case 'Perfectly Relevant':
        return '#4CAF50' // Green
      case 'Relevant':
        return '#FFC107' // Yellow
      case 'Somewhat Relevant':
        return '#FF9800' // Orange
      default:
        return '#9E9E9E' // Gray
    }
  }

  const getRatingBadge = (rating?: string) => {
    const color = getRatingColor(rating)
    return (
      <span
        className="rating-badge"
        style={{
          backgroundColor: color,
          color: 'white',
          padding: '4px 12px',
          borderRadius: '12px',
          fontSize: '12px',
          fontWeight: '600',
        }}
      >
        {rating || 'Not Rated'}
      </span>
    )
  }

  return (
    <div className="paper-list-container">
      <div className="paper-list-header">
        <h3>Papers ({sortedPapers.length})</h3>
        <div className="list-legend">
          <span className="legend-item">
            <span className="legend-color" style={{ backgroundColor: '#4CAF50' }}></span>
            <span>Perfectly Relevant</span>
          </span>
          <span className="legend-item">
            <span className="legend-color" style={{ backgroundColor: '#FFC107' }}></span>
            <span>Relevant</span>
          </span>
          <span className="legend-item">
            <span className="legend-color" style={{ backgroundColor: '#FF9800' }}></span>
            <span>Somewhat Relevant</span>
          </span>
        </div>
      </div>
      <div className="paper-list">
        {sortedPapers.map((paper, idx) => (
          <div key={paper.paperId} className="paper-list-item">
            <div className="paper-list-item-header">
              <div className="paper-rank">#{idx + 1}</div>
              {getRatingBadge(paper.relevance_rating)}
              <span className="paper-source">{paper.source}</span>
            </div>
            <h4 className="paper-title">{paper.title}</h4>
            {paper.abstract && (
              <p className="paper-abstract">{paper.abstract.substring(0, 200)}...</p>
            )}
            <div className="paper-meta">
              {paper.year && <span>Year: {paper.year}</span>}
              {paper.citationCount !== undefined && (
                <span>Citations: {paper.citationCount}</span>
              )}
              {paper.authors && paper.authors.length > 0 && (
                <span>
                  Authors: {paper.authors.slice(0, 3).map((a: any) => a.name || a).join(', ')}
                  {paper.authors.length > 3 && '...'}
                </span>
              )}
            </div>
            {paper.url && (
              <a
                href={paper.url}
                target="_blank"
                rel="noopener noreferrer"
                className="paper-link"
              >
                View on Semantic Scholar →
              </a>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}

