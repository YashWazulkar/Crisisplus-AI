import { GitMerge, ArrowRight, ShieldAlert, CheckCircle2, Clock } from 'lucide-react'

interface Edge {
  from: string
  to: string
  mechanism: string
  latency_range: string
  status: string
  confidence: number
}

interface Node {
  id: string
  label: string
  category: string
}

interface Props {
  graphData: {
    nodes?: Node[]
    edges?: Edge[]
    confirmed_pathways?: number
  }
}

export default function CausalGraph({ graphData }: Props) {
  const edges = graphData?.edges || []

  return (
    <div className="panel causal-graph-panel" style={{ height: '100%' }}>
      <div className="panel-title" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <div style={{ color: '#ec4899' }}><GitMerge size={17} /></div>
          <h3 style={{ fontSize: '14px', fontWeight: 700, margin: 0 }}>Causal Cascading Risk Pathways</h3>
        </div>
        <span style={{ fontSize: '11px', color: '#94a3b8' }}>
          {graphData?.confirmed_pathways || 0} CONFIRMED PATHWAYS
        </span>
      </div>

      <p style={{ fontSize: '12px', color: '#94a3b8', margin: '0 0 12px 0' }}>
        Dynamic dependency graph modeling physical disaster propagation and operational bottlenecks.
      </p>

      <div className="causal-pathways-list" style={{ display: 'flex', flexDirection: 'column', gap: '10px', maxHeight: '340px', overflowY: 'auto' }}>
        {edges.map((edge, idx) => {
          const isConfirmed = edge.status === 'confirmed_cascade'
          const isDeveloping = edge.status === 'developing_risk'

          return (
            <div
              key={idx}
              style={{
                background: isConfirmed ? '#ef444415' : isDeveloping ? '#f59e0b15' : '#0f172a',
                border: `1px solid ${isConfirmed ? '#ef4444' : isDeveloping ? '#f59e0b' : '#1e293b'}`,
                borderRadius: '8px',
                padding: '10px 12px',
                transition: 'all 0.2s ease',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '12px', fontWeight: 600 }}>
                  <span style={{ color: '#38bdf8' }}>{edge.from.replace('_', ' ').toUpperCase()}</span>
                  <ArrowRight size={13} style={{ color: '#64748b' }} />
                  <span style={{ color: '#f8fafc' }}>{edge.to.replace('_', ' ').toUpperCase()}</span>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <span
                    style={{
                      fontSize: '10px',
                      fontWeight: 700,
                      textTransform: 'uppercase',
                      padding: '2px 6px',
                      borderRadius: '4px',
                      background: isConfirmed ? '#ef4444' : isDeveloping ? '#f59e0b' : '#334155',
                      color: isConfirmed || isDeveloping ? '#ffffff' : '#94a3b8',
                    }}
                  >
                    {isConfirmed ? 'CONFIRMED' : isDeveloping ? 'DEVELOPING RISK' : 'INACTIVE'}
                  </span>
                  <span style={{ fontSize: '11px', color: '#cbd5e1' }}>
                    {Math.round(edge.confidence * 100)}%
                  </span>
                </div>
              </div>

              <div style={{ fontSize: '11px', color: '#94a3b8', marginBottom: '4px' }}>
                {edge.mechanism}
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '10px', color: '#64748b' }}>
                <Clock size={11} /> Expected latency window: <strong style={{ color: '#cbd5e1' }}>{edge.latency_range}</strong>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
