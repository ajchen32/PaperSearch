import { useState } from 'react'
import './App.css'
import ViewToggle from './components/ViewToggle'
import QueryDecomposition from './components/QueryDecomposition'
import { searchPapers } from './services/api'
import type { CitationSearchResponse } from './types'

function App() {
  const [query, setQuery] = useState('')
  const [loading, setLoading] = useState(false)
  const [data, setData] = useState<CitationSearchResponse | null>(null)
  const [error, setError] = useState<string | null>(null)

  const handleSearch = async () => {
    if (!query.trim()) return

    setLoading(true)
    setError(null)
    setData(null)

    try {
      const result = await searchPapers(query)
      setData(result)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred')
    } finally {
      setLoading(false)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      handleSearch()
    }
  }

  return (
    <div className="app-container">
      {/* Left Side - Search and Query Decomposition */}
      <div className="left-panel">
        <div className="search-section">
          <h2>Research Paper Search</h2>
          <div className="search-input-container">
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Enter your research query (e.g., 'transformer architecture attention mechanism')"
              className="search-input"
              disabled={loading}
            />
            <button 
              onClick={handleSearch} 
              className="search-button"
              disabled={loading || !query.trim()}
            >
              {loading ? 'Searching...' : 'Search'}
            </button>
          </div>
        </div>

        {error && (
          <div className="error-message">
            Error: {error}
          </div>
        )}

        {data && (
          <QueryDecomposition decomposition={data.query_decomposition} />
        )}
      </div>

      {/* Right Side - Graph Visualization or List View */}
      <div className="right-panel">
        {data ? (
          <ViewToggle data={data} />
        ) : (
          <div className="graph-placeholder">
            <p>Enter a search query to visualize the citation network</p>
          </div>
        )}
      </div>
    </div>
  )
}

export default App
