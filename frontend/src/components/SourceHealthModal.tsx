import { RefreshCw, RadioTower, CheckCircle, AlertTriangle, XCircle, Key, Layers, Server } from 'lucide-react'

interface SourceHealth {
  source_id: string
  source_type: string
  status: string
  enabled: boolean
  polling_interval_seconds: number
  last_fetch: string | null
  last_success: string | null
  data_freshness_seconds: number | null
  latency_ms: number
  records_accepted: number
  records_rejected: number
  error_message: string | null
  gateway_id?: string
  alpha?: number
  beta?: number
  variance?: number
}

interface Props {
  sources: SourceHealth[]
  onPollSource: (sourceId: string) => Promise<void>
  onClose?: () => void
}

export default function SourceHealthPanel({ sources, onPollSource }: Props) {
  return (
    <div className="panel sources-panel" style={{ padding: '20px' }}>
      <div
        className="panel-title"
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: '14px',
          borderBottom: '1px solid var(--border-gold)',
          paddingBottom: '10px',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div style={{ color: 'var(--saffron-400)' }}>
            <RadioTower size={19} />
          </div>
          <div>
            <h3 style={{ fontSize: '15px', fontWeight: 800, margin: 0, color: 'var(--text-ivory)' }}>
              Public Ingestion Adapters & Gateway Reliability Telemetry
            </h3>
            <small style={{ color: 'var(--text-secondary)', fontSize: '11px' }}>
              Tracks common-cause gateway groups, Beta conjugate trust distributions, and live polling latency
            </small>
          </div>
        </div>
        <span
          style={{
            fontSize: '11px',
            color: 'var(--saffron-400)',
            fontFamily: 'var(--font-mono)',
            padding: '4px 8px',
            borderRadius: '6px',
            background: 'rgba(245, 158, 11, 0.12)',
            border: '1px solid var(--border-gold)',
          }}
        >
          {sources.length} CONNECTORS ACTIVE
        </span>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(310px, 1fr))', gap: '14px' }}>
        {sources.map(src => {
          const isHealthy = src.status === 'healthy'
          const isAwaitingKey = src.status === 'awaiting_api_key' || src.status === 'awaiting_authorization'
          const isDegraded = src.status === 'degraded'

          const badgeColor = isHealthy ? '#10b981' : isAwaitingKey ? '#06b6d4' : isDegraded ? '#f59e0b' : '#ef4444'

          const alpha = src.alpha ?? 9.5
          const beta = src.beta ?? 1.5
          const trustPct = Math.round((alpha / (alpha + beta)) * 100)

          return (
            <div
              key={src.source_id}
              style={{
                background: 'var(--bg-card)',
                border: `1px solid ${isHealthy ? 'var(--border-card)' : badgeColor + '70'}`,
                borderRadius: '8px',
                padding: '14px',
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'space-between',
              }}
            >
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                  <strong style={{ fontSize: '13px', color: 'var(--text-ivory)', letterSpacing: '0.4px' }}>
                    {src.source_id.toUpperCase()}
                  </strong>
                  <span
                    style={{
                      fontSize: '9px',
                      fontWeight: 700,
                      textTransform: 'uppercase',
                      padding: '2px 7px',
                      borderRadius: '4px',
                      background: badgeColor + '20',
                      color: badgeColor,
                      border: `1px solid ${badgeColor}`,
                    }}
                  >
                    {src.status.replace(/_/g, ' ')}
                  </span>
                </div>

                <div style={{ display: 'flex', gap: '8px', fontSize: '11px', color: 'var(--text-muted)', marginBottom: '8px', flexWrap: 'wrap' }}>
                  <span>Type: <strong style={{ color: 'var(--text-secondary)' }}>{src.source_type}</strong></span>
                  <span>•</span>
                  <span>Gateway: <strong style={{ color: '#06b6d4' }}>{src.gateway_id || 'direct'}</strong></span>
                  <span>•</span>
                  <span>Polling: {src.polling_interval_seconds}s</span>
                </div>

                <div
                  style={{
                    display: 'grid',
                    gridTemplateColumns: '1fr 1fr',
                    gap: '6px',
                    fontSize: '11px',
                    background: 'var(--bg-secondary)',
                    padding: '8px 10px',
                    borderRadius: '6px',
                    marginBottom: '8px',
                    border: '1px solid var(--border-subtle)',
                  }}
                >
                  <div>Latency: <strong style={{ color: 'var(--text-ivory)', fontFamily: 'var(--font-mono)' }}>{src.latency_ms > 0 ? `${src.latency_ms}ms` : '--'}</strong></div>
                  <div>Trust Est: <strong style={{ color: '#10b981', fontFamily: 'var(--font-mono)' }}>{trustPct}%</strong></div>
                  <div>Accepted: <strong style={{ color: '#10b981', fontFamily: 'var(--font-mono)' }}>{src.records_accepted}</strong></div>
                  <div>Rejected: <strong style={{ color: src.records_rejected > 0 ? '#ef4444' : 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>{src.records_rejected}</strong></div>
                  <div style={{ gridColumn: 'span 2' }}>
                    Freshness: <strong style={{ color: 'var(--text-secondary)', fontFamily: 'var(--font-mono)' }}>
                      {src.data_freshness_seconds !== null ? `${Math.round(src.data_freshness_seconds)}s ago` : 'Awaiting baseline'}
                    </strong>
                  </div>
                </div>

                {src.error_message && (
                  <div
                    style={{
                      fontSize: '10px',
                      color: 'var(--saffron-400)',
                      background: 'rgba(245, 158, 11, 0.1)',
                      border: '1px solid var(--border-gold)',
                      padding: '5px 8px',
                      borderRadius: '4px',
                      marginBottom: '8px',
                    }}
                  >
                    {src.error_message}
                  </div>
                )}
              </div>

              <button
                className="btn"
                onClick={() => onPollSource(src.source_id)}
                style={{ width: '100%', fontSize: '11px', padding: '6px', marginTop: '6px' }}
              >
                <RefreshCw size={12} /> Force Ingestion Poll
              </button>
            </div>
          )
        })}
      </div>
    </div>
  )
}
