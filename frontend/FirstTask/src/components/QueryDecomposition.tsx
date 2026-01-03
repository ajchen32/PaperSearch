import type { QueryDecompositionResponse } from '../types'

interface QueryDecompositionProps {
  decomposition: QueryDecompositionResponse
}

export default function QueryDecomposition({ decomposition }: QueryDecompositionProps) {
  return (
    <div className="query-decomposition">
      <h3>Query Decomposition</h3>
      
      <div className="decomposition-section">
        <h4>Main Concepts</h4>
        <div className="concepts-list">
          {decomposition.main_concepts.map((concept, idx) => (
            <span key={idx} className="concept-tag">{concept}</span>
          ))}
        </div>
      </div>

      <div className="decomposition-section">
        <h4>Components</h4>
        {decomposition.components.map((component, idx) => (
          <div key={idx} className="component-item">
            <strong>{component.component}:</strong>
            <p>{component.description}</p>
            <div className="keywords">
              {component.keywords.map((keyword, kIdx) => (
                <span key={kIdx} className="keyword-tag">{keyword}</span>
              ))}
            </div>
          </div>
        ))}
      </div>

      {decomposition.relationships.length > 0 && (
        <div className="decomposition-section">
          <h4>Relationships</h4>
          <ul className="relationships-list">
            {decomposition.relationships.map((rel, idx) => (
              <li key={idx}>{rel}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}

