import { useEffect, useState } from 'react'
import {
  MapPin,
  AlertTriangle,
  Activity,
  ShieldCheck,
  Clock,
  ExternalLink,
  ChevronRight,
  Droplets,
  Layers,
  X,
  CloudRain,
  Thermometer,
  CarFront,
  Waves,
} from 'lucide-react'

interface Props {
  apiBase: string
  zoneId: string
  onClose: () => void
}

export default function SubregionDetailPanel({ apiBase, zoneId, onClose }: Props) {
  const [data, setData] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [showAreaInfo, setShowAreaInfo] = useState(false)

  useEffect(() => {
    let active = true
    const loadAssessment = async () => {
      try {
        const response = await fetch(`${apiBase}/api/region/${zoneId}`)
        if (!response.ok) throw new Error('Zone assessment unavailable')
        const assessment = await response.json()
        if (active) {
          setData(assessment)
          setError('')
          setLoading(false)
        }
      } catch (err) {
        if (active) {
          setError(err instanceof Error ? err.message : 'Could not load zone assessment')
          setLoading(false)
        }
      }
    }

    setLoading(true)
    setError('')
    setShowAreaInfo(false)
    loadAssessment()
    const refreshTimer = window.setInterval(loadAssessment, 15000)
    return () => {
      active = false
      window.clearInterval(refreshTimer)
    }
  }, [apiBase, zoneId])

  if (loading) {
    return (
      <div className="subregion-panel panel" style={{ padding: '20px', minWidth: '320px' }}>
        <div style={{ color: '#94a3b8', fontSize: '12px' }}>Loading subregion intelligence for {zoneId}...</div>
      </div>
    )
  }

  if (!data) {
    return (
      <div className="subregion-panel panel" style={{ padding: '20px', minWidth: '320px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <strong style={{ color: '#f87171' }}>Subregion Assessment Notice</strong>
          <button className="btn" onClick={onClose} style={{ padding: '2px 6px' }}>&times;</button>
        </div>
        <p style={{ fontSize: '11px', color: '#94a3b8', marginTop: '10px' }}>
          {error || 'Insufficient data for a reliable subregion assessment.'}
        </p>
      </div>
    )
  }

  const action = data.action || 'WATCH'
  const actionColor =
    action === 'ESCALATE' ? '#fb7185' : action === 'ALERT' ? '#fb7185' : action === 'PREPARE' ? '#fbbf24' : '#5eead4'

  const xai = data.xai_explanation || {}
  const forecasts = data.forecasts || []
  const events = data.events || []
  const latestEvent = (types: string[]) => events.find((event: any) => types.includes(event.event_type))
  const temperatureEvent = events.find((event: any) =>
    event.payload?.temperature_c !== undefined || event.event_type === 'temperature_anomaly'
  )
  const trafficEvent = latestEvent(['traffic_speed', 'ambulance_delay'])
  const waterEvent = latestEvent(['water_level', 'road_flooding', 'drainage_overflow', 'flood'])
  const activityEvents = events.slice(0, 5)
  const temperature = temperatureEvent?.payload?.temperature_c
  const rainfall = events.find((event: any) => event.event_type === 'rainfall')

  return (
    <div
      className="subregion-panel panel"
      style={{
        padding: '18px',
        maxHeight: '85vh',
        overflowY: 'auto',
        border: `1px solid ${actionColor}40`,
        background: 'linear-gradient(145deg, #0f172a, #111e33)',
      }}
    >
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '14px', borderBottom: '1px solid #1e293b', paddingBottom: '12px' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '10px', textTransform: 'uppercase', letterSpacing: '0.8px', color: '#38bdf8' }}>
            <MapPin size={12} />
            <span>NMC Administrative Zone · {data.zone_id}</span>
          </div>
          <h2 style={{ margin: '4px 0 2px', fontSize: '18px', color: '#f8fafc', fontWeight: 800 }}>
            {data.name}
          </h2>
          <span style={{ fontSize: '11px', color: '#94a3b8' }}>{data.marathi_name}</span>
        </div>
        <button
          onClick={onClose}
          style={{ background: 'transparent', border: 0, color: '#94a3b8', cursor: 'pointer', padding: '4px' }}
          title="Close Subregion Panel"
        >
          <X size={18} />
        </button>
      </div>

      {/* Response Action Status Badge */}
      <div
        style={{
          background: `${actionColor}15`,
          border: `1px solid ${actionColor}50`,
          borderRadius: '8px',
          padding: '12px 14px',
          marginBottom: '14px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}
      >
        <div>
          <span style={{ fontSize: '9px', textTransform: 'uppercase', letterSpacing: '0.6px', color: actionColor, fontWeight: 700 }}>
            Zone Response Classification
          </span>
          <div style={{ fontSize: '20px', fontWeight: 800, color: actionColor, letterSpacing: '0.5px' }}>
            {action}
          </div>
        </div>
        <div style={{ textAlign: 'right' }}>
          <span style={{ fontSize: '9px', color: '#94a3b8' }}>Active Events</span>
          <div style={{ fontSize: '16px', fontWeight: 700, color: '#f8fafc' }}>{data.events_count || 0}</div>
        </div>
      </div>

      <button className="area-info-open" onClick={() => setShowAreaInfo(true)}>
        <Activity size={15} />
        View area conditions & activity
        <ChevronRight size={15} />
      </button>

      {/* Localities & Critical Assets */}
      <div style={{ marginBottom: '14px', background: '#0b1320', padding: '10px 12px', borderRadius: '6px', fontSize: '11px' }}>
        <strong style={{ color: '#cbd5e1', display: 'block', marginBottom: '4px' }}>Key Localities Covered:</strong>
        <div style={{ color: '#94a3b8', marginBottom: '8px' }}>
          {(data.localities || []).join(' · ')}
        </div>
        <strong style={{ color: '#cbd5e1', display: 'block', marginBottom: '4px' }}>Critical Infrastructure:</strong>
        <div style={{ color: '#38bdf8' }}>
          {(data.critical_infrastructure || []).join(' · ')}
        </div>
        {data.flood_vulnerability && (
          <div style={{ marginTop: '8px', paddingTop: '8px', borderTop: '1px solid #1e293b', color: '#fbbf24', fontSize: '10px' }}>
            <Droplets size={10} style={{ display: 'inline', marginRight: '4px' }} />
            Vulnerability Profile: {data.flood_vulnerability}
          </div>
        )}
      </div>

      {/* xAI Grounded Reasoning */}
      <div style={{ marginBottom: '16px', background: '#0d1829', border: '1px solid #1e3a5f', padding: '12px', borderRadius: '8px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '6px' }}>
          <Activity size={14} style={{ color: '#5eead4' }} />
          <strong style={{ fontSize: '11px', color: '#5eead4', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
            Why does CrisisPulse consider this zone at risk?
          </strong>
        </div>
        <p style={{ margin: '0 0 8px', fontSize: '11px', lineHeight: '1.6', color: '#e2e8f0' }}>
          {xai.decision_rationale || xai.summary || 'Conditions monitored within normal parameters.'}
        </p>

        {xai.evidence_synthesis && (
          <div style={{ fontSize: '10px', color: '#94a3b8', borderTop: '1px solid #1e293b', paddingTop: '6px' }}>
            <strong style={{ color: '#cbd5e1' }}>Supporting Evidence:</strong> {xai.evidence_synthesis}
          </div>
        )}

        {xai.missing_data_disclosure && (
          <div style={{ fontSize: '9px', color: '#64748b', marginTop: '6px' }}>
            <em>Telemetry Note: {xai.missing_data_disclosure}</em>
          </div>
        )}
      </div>

      {/* Subregion Multi-Horizon Forecasts */}
      <div style={{ marginBottom: '16px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '8px' }}>
          <Clock size={13} style={{ color: '#38bdf8' }} />
          <strong style={{ fontSize: '11px', color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.6px' }}>
            Zone Near-Term Outlook (10, 30, 60 Min)
          </strong>
        </div>

        {forecasts.length === 0 ? (
          <div style={{ fontSize: '11px', color: '#64748b', padding: '8px', background: '#0b1320', borderRadius: '6px' }}>
            Insufficient localized telemetry for horizon projections.
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {forecasts.map((fc: any, i: number) => (
              <div
                key={i}
                style={{
                  background: '#0b1320',
                  border: '1px solid #1e293b',
                  borderRadius: '6px',
                  padding: '10px',
                  display: 'flex',
                  gap: '10px',
                  alignItems: 'flex-start',
                }}
              >
                <span
                  style={{
                    background: '#1e293b',
                    color: '#38bdf8',
                    fontFamily: 'monospace',
                    fontSize: '10px',
                    fontWeight: 700,
                    padding: '3px 6px',
                    borderRadius: '4px',
                    whiteSpace: 'nowrap',
                  }}
                >
                  {fc.horizon}
                </span>
                <div style={{ flex: 1 }}>
                  <strong style={{ fontSize: '11px', color: '#f1f5f9', display: 'block', marginBottom: '2px' }}>
                    {fc.label}
                  </strong>
                  <div style={{ fontSize: '10px', color: '#94a3b8', marginBottom: '4px' }}>
                    Scope: {fc.geographic_scope}
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '9px', color: '#64748b' }}>
                    <span>Likelihood: <strong style={{ color: '#5eead4' }}>{Math.round((fc.probability || 0) * 100)}%</strong></span>
                    <span>Confidence: <strong>{Math.round((fc.confidence || 0) * 100)}%</strong></span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Recommended Verification Checklist */}
      {xai.recommended_verification_steps && xai.recommended_verification_steps.length > 0 && (
        <div style={{ background: '#0b1320', padding: '12px', borderRadius: '6px', border: '1px solid #1e293b' }}>
          <strong style={{ fontSize: '10px', color: '#cbd5e1', textTransform: 'uppercase', letterSpacing: '0.6px', display: 'block', marginBottom: '6px' }}>
            Recommended Field Actions:
          </strong>
          <ul style={{ margin: 0, paddingLeft: '16px', fontSize: '10px', color: '#94a3b8', lineHeight: '1.6' }}>
            {xai.recommended_verification_steps.map((step: string, i: number) => (
              <li key={i}>{step}</li>
            ))}
          </ul>
        </div>
      )}

      {showAreaInfo && (
        <div className="area-info-backdrop" onClick={() => setShowAreaInfo(false)}>
          <section
            className="area-info-dialog"
            role="dialog"
            aria-modal="true"
            aria-labelledby="area-info-title"
            onClick={event => event.stopPropagation()}
          >
            <header className="area-info-header">
              <div>
                <span>LIVE AREA SNAPSHOT</span>
                <h2 id="area-info-title">{data.name}</h2>
                <small>Area readings refresh every 15 seconds</small>
              </div>
              <button aria-label="Close area information" onClick={() => setShowAreaInfo(false)}>
                <X size={18} />
              </button>
            </header>

            {error && <p className="area-info-refresh-error">Latest refresh failed: {error}. Showing the last available assessment.</p>}

            <div className="area-info-metrics">
              <article>
                <CloudRain size={17} />
                <span>Rainfall</span>
                <strong>{rainfall ? `${rainfall.magnitude ?? 'Observed'} ${rainfall.magnitude_unit || ''}` : 'No local reading'}</strong>
                <small>{rainfall?.title || 'No recent rainfall event for this zone'}</small>
              </article>
              <article>
                <Thermometer size={17} />
                <span>Temperature</span>
                <strong>{temperature !== undefined ? `${temperature} °C` : 'No local reading'}</strong>
                <small>{temperatureEvent?.title || 'No recent temperature observation for this zone'}</small>
              </article>
              <article>
                <CarFront size={17} />
                <span>Traffic & transit</span>
                <strong>
                  {trafficEvent
                    ? `${trafficEvent.magnitude ?? trafficEvent.event_type.replace('_', ' ')} ${trafficEvent.magnitude_unit || ''}`
                    : 'No local reading'}
                </strong>
                <small>{trafficEvent?.title || 'No recent traffic or ambulance activity for this zone'}</small>
              </article>
              <article>
                <Waves size={17} />
                <span>Water & drainage</span>
                <strong>{waterEvent ? waterEvent.event_type.replace(/_/g, ' ') : 'No active report'}</strong>
                <small>{waterEvent?.title || 'No recent water-level or flooding report for this zone'}</small>
              </article>
            </div>

            <section className="area-info-activities">
              <h3>Other recent area activity</h3>
              {activityEvents.length > 0 ? (
                <ul>
                  {activityEvents.map((event: any, index: number) => (
                    <li key={`${event.event_id || event.source_id}-${index}`}>
                      <span className="area-activity-type">{event.event_type.replace(/_/g, ' ')}</span>
                      <span>{event.title}</span>
                      <small>{event.source_id} · {Math.round((event.severity || 0) * 100)}% severity</small>
                    </li>
                  ))}
                </ul>
              ) : (
                <p>No recent local activity has been recorded for this area. District-wide readings are not presented as area measurements.</p>
              )}
            </section>

            <footer>
              Figures use observations assigned to this administrative zone. Missing readings mean no localized observation is currently available.
            </footer>
          </section>
        </div>
      )}
    </div>
  )
}
