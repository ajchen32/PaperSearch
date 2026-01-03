import { useState } from 'react'
import GraphVisualization from './GraphVisualization'
import PaperListView from './PaperListView'
import type { CitationSearchResponse } from '../types'

interface ViewToggleProps {
  data: CitationSearchResponse
}

export default function ViewToggle({ data }: ViewToggleProps) {
  const [viewMode, setViewMode] = useState<'graph' | 'list'>('graph')

  return (
    <div className="view-toggle-container">
      <div className="view-toggle-header">
        <div className="view-toggle-buttons">
          <button
            className={`toggle-button ${viewMode === 'graph' ? 'active' : ''}`}
            onClick={() => setViewMode('graph')}
          >
            Graph View
          </button>
          <button
            className={`toggle-button ${viewMode === 'list' ? 'active' : ''}`}
            onClick={() => setViewMode('list')}
          >
            List View
          </button>
        </div>
      </div>
      <div className="view-content">
        {viewMode === 'graph' ? (
          <GraphVisualization data={data} />
        ) : (
          <PaperListView data={data} />
        )}
      </div>
    </div>
  )
}

