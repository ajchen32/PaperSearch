import { useMemo, useRef, useState, useEffect } from 'react'
import type { CitationSearchResponse, Paper } from '../types'

interface GraphNode {
  id: string
  paper: Paper
  x: number
  y: number
  level: number // 0 = center, 1 = forward/backward, 2 = nested
  direction: 'center' | 'forward' | 'backward'
}

interface GraphLink {
  source: string
  target: string
}

interface GraphVisualizationProps {
  data: CitationSearchResponse
}

export default function GraphVisualization({ data }: GraphVisualizationProps) {
  const centerY = 400
  const graphContainerRef = useRef<HTMLDivElement>(null)
  const [isFullscreen, setIsFullscreen] = useState(false)

  useEffect(() => {
    const handleFullscreenChange = () => {
      setIsFullscreen(!!document.fullscreenElement)
    }

    document.addEventListener('fullscreenchange', handleFullscreenChange)
    return () => {
      document.removeEventListener('fullscreenchange', handleFullscreenChange)
    }
  }, [])

  const toggleFullscreen = async () => {
    if (!graphContainerRef.current) return

    try {
      if (!document.fullscreenElement) {
        await graphContainerRef.current.requestFullscreen()
      } else {
        await document.exitFullscreen()
      }
    } catch (error) {
      console.error('Error toggling fullscreen:', error)
    }
  }

  const { nodes, links } = useMemo(() => {
    const graphNodes: GraphNode[] = []
    const graphLinks: GraphLink[] = []
    const centerId = data.most_relevant_paper.paperId

    // Add center node
    graphNodes.push({
      id: centerId,
      paper: data.most_relevant_paper,
      x: 0,
      y: 0,
      level: 0,
      direction: 'center',
    })

    // Add forward citations (level 1)
    data.forward_citations.forEach((paperWithNested, idx) => {
      const forwardId = paperWithNested.paper.paperId
      graphNodes.push({
        id: forwardId,
        paper: paperWithNested.paper,
        x: 0,
        y: 0,
        level: 1,
        direction: 'forward',
      })
      graphLinks.push({ source: centerId, target: forwardId })

      // Add nested forward citations (level 2 - going further forward)
      paperWithNested.nested_forward_citations.forEach((nestedPaper) => {
        const nestedId = nestedPaper.paperId
        graphNodes.push({
          id: nestedId,
          paper: nestedPaper,
          x: 0,
          y: 0,
          level: 2,
          direction: 'forward',
        })
        graphLinks.push({ source: forwardId, target: nestedId })
      })
      
      // Add nested backward citations (level 2 - going backward from forward citations)
      paperWithNested.nested_backward_citations.forEach((nestedPaper) => {
        const nestedId = nestedPaper.paperId
        graphNodes.push({
          id: nestedId,
          paper: nestedPaper,
          x: 0,
          y: 0,
          level: 2,
          direction: 'forward', // Still in forward branch, but going backward
        })
        graphLinks.push({ source: nestedId, target: forwardId })
      })
    })

    // Add backward citations (level 1)
    data.backward_citations.forEach((paperWithNested, idx) => {
      const backwardId = paperWithNested.paper.paperId
      graphNodes.push({
        id: backwardId,
        paper: paperWithNested.paper,
        x: 0,
        y: 0,
        level: 1,
        direction: 'backward',
      })
      graphLinks.push({ source: backwardId, target: centerId })

      // Add nested backward citations (level 2 - going further backward)
      paperWithNested.nested_backward_citations.forEach((nestedPaper) => {
        const nestedId = nestedPaper.paperId
        graphNodes.push({
          id: nestedId,
          paper: nestedPaper,
          x: 0,
          y: 0,
          level: 2,
          direction: 'backward',
        })
        graphLinks.push({ source: nestedId, target: backwardId })
      })
      
      // Add nested forward citations (level 2 - going forward from backward citations)
      paperWithNested.nested_forward_citations.forEach((nestedPaper) => {
        const nestedId = nestedPaper.paperId
        graphNodes.push({
          id: nestedId,
          paper: nestedPaper,
          x: 0,
          y: 0,
          level: 2,
          direction: 'backward', // Still in backward branch, but going forward
        })
        graphLinks.push({ source: backwardId, target: nestedId })
      })
    })

    // Calculate positions
    const centerX = 500
    const centerY = 400
    const level1Radius = 200
    const topPadding = 80  // Space for forward label
    const bottomPadding = 80  // Space for backward label

    // Position forward nodes (above center)
    const forwardNodes = graphNodes.filter((n) => n.direction === 'forward' && n.level === 1)
    if (forwardNodes.length > 0) {
      const angleStep = Math.PI / (forwardNodes.length + 1)
      forwardNodes.forEach((node, idx) => {
        const angle = angleStep * (idx + 1) - Math.PI / 2
        node.x = centerX + level1Radius * Math.cos(angle)
        node.y = centerY - topPadding + level1Radius * Math.sin(angle)
      })
    }

    // Position backward nodes (below center)
    const backwardNodes = graphNodes.filter((n) => n.direction === 'backward' && n.level === 1)
    if (backwardNodes.length > 0) {
      const angleStep = Math.PI / (backwardNodes.length + 1)
      backwardNodes.forEach((node, idx) => {
        const angle = angleStep * (idx + 1) + Math.PI / 2
        node.x = centerX + level1Radius * Math.cos(angle)
        node.y = centerY + bottomPadding + level1Radius * Math.sin(angle)
      })
    }

    // Position nested nodes for forward citations (both nested_forward and nested_backward)
    forwardNodes.forEach((parentNode) => {
      // Nested forward citations (going further forward)
      const nestedForwardNodes = graphNodes.filter(
        (n) => n.direction === 'forward' && n.level === 2 && graphLinks.some((l) => l.source === parentNode.id && l.target === n.id)
      )
      // Nested backward citations (going backward from forward citations)
      const nestedBackwardNodes = graphNodes.filter(
        (n) => n.direction === 'forward' && n.level === 2 && graphLinks.some((l) => l.source === n.id && l.target === parentNode.id)
      )
      const allNestedNodes = [...nestedForwardNodes, ...nestedBackwardNodes]
      
      if (allNestedNodes.length > 0) {
        const parentAngle = Math.atan2(parentNode.y - centerY, parentNode.x - centerX)
        allNestedNodes.forEach((node, idx) => {
          const offsetAngle = (Math.PI / 8) * (idx - (allNestedNodes.length - 1) / 2)
          node.x = parentNode.x + 120 * Math.cos(parentAngle + offsetAngle)
          node.y = parentNode.y + 120 * Math.sin(parentAngle + offsetAngle)
        })
      }
    })

    // Position nested nodes for backward citations (both nested_backward and nested_forward)
    backwardNodes.forEach((parentNode) => {
      // Nested backward citations (going further backward)
      const nestedBackwardNodes = graphNodes.filter(
        (n) => n.direction === 'backward' && n.level === 2 && graphLinks.some((l) => l.source === n.id && l.target === parentNode.id)
      )
      // Nested forward citations (going forward from backward citations)
      const nestedForwardNodes = graphNodes.filter(
        (n) => n.direction === 'backward' && n.level === 2 && graphLinks.some((l) => l.source === parentNode.id && l.target === n.id)
      )
      const allNestedNodes = [...nestedBackwardNodes, ...nestedForwardNodes]
      
      if (allNestedNodes.length > 0) {
        const parentAngle = Math.atan2(parentNode.y - centerY, parentNode.x - centerX)
        allNestedNodes.forEach((node, idx) => {
          const offsetAngle = (Math.PI / 8) * (idx - (allNestedNodes.length - 1) / 2)
          node.x = parentNode.x + 120 * Math.cos(parentAngle + offsetAngle)
          node.y = parentNode.y + 120 * Math.sin(parentAngle + offsetAngle)
        })
      }
    })

    // Center node position
    const centerNode = graphNodes.find((n) => n.id === centerId)
    if (centerNode) {
      centerNode.x = centerX
      centerNode.y = centerY
    }

    return { nodes: graphNodes, links: graphLinks }
  }, [data])

  const getNodeColor = (rating?: string) => {
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

  const getNodeRadius = (level: number) => {
    if (level === 0) return 20
    if (level === 1) return 15
    return 10
  }

  // Calculate dynamic SVG size based on fullscreen state
  const svgWidth = isFullscreen ? window.innerWidth - 100 : 800
  const svgHeight = isFullscreen ? window.innerHeight - 200 : 600

  return (
    <div className="graph-container" ref={graphContainerRef}>
      <div className="graph-header">
        <div className="graph-legend">
          <div className="legend-item">
            <span className="legend-color" style={{ backgroundColor: '#4CAF50' }}></span>
            <span>Perfectly Relevant</span>
          </div>
          <div className="legend-item">
            <span className="legend-color" style={{ backgroundColor: '#FFC107' }}></span>
            <span>Relevant</span>
          </div>
          <div className="legend-item">
            <span className="legend-color" style={{ backgroundColor: '#FF9800' }}></span>
            <span>Somewhat Relevant</span>
          </div>
        </div>
        <button 
          className="fullscreen-button"
          onClick={toggleFullscreen}
          title={isFullscreen ? "Exit Fullscreen" : "Enter Fullscreen"}
        >
          {isFullscreen ? '⛶' : '⛶'}
        </button>
      </div>
      <svg width={svgWidth} height={svgHeight} className="graph-svg" viewBox="0 0 1000 800" preserveAspectRatio="xMidYMid meet">
        <defs>
          <marker
            id="arrowhead"
            markerWidth="10"
            markerHeight="10"
            refX="9"
            refY="3"
            orient="auto"
          >
            <polygon points="0 0, 10 3, 0 6" fill="#666" />
          </marker>
        </defs>

        {/* Draw links */}
        {links.map((link, idx) => {
          const sourceNode = nodes.find((n) => n.id === link.source)
          const targetNode = nodes.find((n) => n.id === link.target)
          if (!sourceNode || !targetNode) return null

          return (
            <line
              key={idx}
              x1={sourceNode.x}
              y1={sourceNode.y}
              x2={targetNode.x}
              y2={targetNode.y}
              stroke="#666"
              strokeWidth="2"
              markerEnd="url(#arrowhead)"
            />
          )
        })}

        {/* Draw nodes */}
        {nodes.map((node) => (
          <g key={node.id}>
            <circle
              cx={node.x}
              cy={node.y}
              r={getNodeRadius(node.level)}
              fill={getNodeColor(node.paper.relevance_rating)}
              stroke="#333"
              strokeWidth="2"
              className="graph-node"
            />
            <text
              x={node.x}
              y={node.y + getNodeRadius(node.level) + 15}
              textAnchor="middle"
              fontSize="10"
              fill="#333"
              className="node-label"
            >
              {node.paper.title.length > 30
                ? node.paper.title.substring(0, 30) + '...'
                : node.paper.title}
            </text>
          </g>
        ))}
      </svg>
    </div>
  )
}
