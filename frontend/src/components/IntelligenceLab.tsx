import { useState, useEffect } from 'react'
import {
  Play,
  Pause,
  RotateCcw,
  SkipForward,
  Scale,
  GitCompare,
  HelpCircle,
  ShieldCheck,
  Zap,
  Activity,
  Layers,
  Sparkles,
  CheckCircle2,
  AlertCircle,
  TrendingUp,
  BrainCircuit,
  Radio,
  FileCheck,
} from 'lucide-react'

interface Props {
  apiBase: string
  onClose?: () => void
}

type TabMode = 'replay' | 'twin_test' | 'counterfactual' | 'learning'

const ALL_SCENARIOS = [
  { id: 'cascade', label: 'Genuine Cascading Crisis (Flood → Grid → Medical)' },
  { id: 'twin_a', label: 'Twin A (Genuine Cascade - Min 0-6 Shared, Min 7 Escalation)' },
  { id: 'twin_b', label: 'Twin B (Sensor Look-alike - Min 0-6 Shared, Min 7 Hardware Fail)' },
  { id: 'sensor_failure', label: 'Sensor Hardware Failure & Telemetry Glitch' },
  { id: 'normal', label: 'Normal Storm Flow Sequence' },
  { id: 'misleading', label: 'Coordinated Misleading Reports / Social Rumors' },
  { id: 'delayed_arrival', label: 'Out-of-Order Delayed Packet Arrivals' },
  { id: 'duplicate_burst', label: 'Duplicate Message Storm (Idempotency Test)' },
  { id: 'correlated_gateway_outage', label: 'Correlated Gateway / Power Substation Outage' },
  { id: 'rumor_retraction', label: 'Citizen Rumor Followed by Official Police Retraction' },
  { id: 'environmental_drift', label: 'Environmental Climate / Monsoon Base-Rate Drift' },
  { id: 'unreliable_source', label: 'Source Degradation & Rapid Trust Recovery' },
  { id: 'intermittent_telemetry', label: 'Intermittent Dropouts & Telemetry Cutouts' },
  { id: 'flash_flood_rapid', label: 'Rapid Flash Flood (Under 5-Min Escalation)' },
  { id: 'hospital_mass_casualty', label: 'Isolated Medical Surge (Non-Cascading)' },
  { id: 'substation_blackout', label: 'Electrical Substation Blackout Cascade' },
]

export default function IntelligenceLab({ apiBase }: Props) {
  const [activeTab, setActiveTab] = useState<TabMode>('replay')

  // Replay State
  const [replayData, setReplayData] = useState<any>(null)
  const [currentMinute, setCurrentMinute] = useState(0)
  const [isPlaying, setIsPlaying] = useState(false)
  const [replayScenario, setReplayScenario] = useState('cascade')

  // Twin Test State
  const [twinData, setTwinData] = useState<any>(null)
  const [twinMinute, setTwinMinute] = useState(7)
  const [twinLoading, setTwinLoading] = useState(false)

  // Counterfactual State
  const [counterfactualResult, setCounterfactualResult] = useState<any>(null)
  const [selectedCfType, setSelectedCfType] = useState('weather_offline')
  const [cfLoading, setCfLoading] = useState(false)

  // Online Trust & Base-Rate State
  const [trustSources, setTrustSources] = useState<any[]>([])
  const [baseRateDrift, setBaseRateDrift] = useState<any>(null)
  const [experimentResult, setExperimentResult] = useState<any>(null)
  const [learningLoading, setLearningLoading] = useState(false)

  // Fetch replay data
  useEffect(() => {
    fetch(`${apiBase}/api/lab/replay?scenario=${replayScenario}`)
      .then(r => r.json())
      .then(d => {
        setReplayData(d)
        setCurrentMinute(0)
      })
      .catch(() => {})
  }, [apiBase, replayScenario])

  // Fetch Twin Test data
  const loadTwinTest = () => {
    setTwinLoading(true)
    fetch(`${apiBase}/api/twin-test`)
      .then(r => r.json())
      .then(d => {
        setTwinData(d)
        setTwinLoading(false)
      })
      .catch(() => setTwinLoading(false))
  }

  useEffect(() => {
    loadTwinTest()
  }, [apiBase])

  // Fetch Online Trust & Base Rate Drift
  const loadTrustAndDrift = () => {
    fetch(`${apiBase}/api/sources`)
      .then(r => r.json())
      .then(setTrustSources)
      .catch(() => {})
    fetch(`${apiBase}/api/base-rate/drift`)
      .then(r => r.json())
      .then(setBaseRateDrift)
      .catch(() => {})
  }

  useEffect(() => {
    if (activeTab === 'learning') {
      loadTrustAndDrift()
    }
  }, [activeTab, apiBase])

  // Replay scrubber animation loop
  useEffect(() => {
    if (!isPlaying) return
    const timer = setInterval(() => {
      setCurrentMinute(prev => {
        if (prev >= 10) {
          setIsPlaying(false)
          return 10
        }
        return prev + 1
      })
    }, 1400)
    return () => clearInterval(timer)
  }, [isPlaying])

  const runCounterfactual = async (cfType: string) => {
    setCfLoading(true)
    setSelectedCfType(cfType)
    try {
      const res = await fetch(`${apiBase}/api/lab/counterfactual`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ counterfactual_type: cfType }),
      })
      const data = await res.json()
      setCounterfactualResult(data)
    } catch {
      // handled
    } finally {
      setCfLoading(false)
    }
  }

  const runLearningExperiment = async () => {
    setLearningLoading(true)
    try {
      const res = await fetch(`${apiBase}/api/learning/experiment`, { method: 'POST' })
      const data = await res.json()
      setExperimentResult(data)
      loadTrustAndDrift()
    } catch {
      // handled
    } finally {
      setLearningLoading(false)
    }
  }

  const currentReplayStep = replayData?.timeline?.[currentMinute] || {}
  const twinAStep = twinData?.scenario_a?.timeline?.[twinMinute] || {}
  const twinBStep = twinData?.scenario_b?.timeline?.[twinMinute] || {}
  const sideBySideList = twinData?.side_by_side_timeline || []

  const pct = (v: number) => `${Math.round((v || 0) * 100)}%`

  return (
    <div className="intelligence-lab-container panel" style={{ marginTop: '16px' }}>
      {/* Header with TantraFiesta accents */}
      <div
        className="lab-header"
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          borderBottom: '1px solid var(--border-gold)',
          paddingBottom: '14px',
          marginBottom: '16px',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div
            style={{
              background: 'linear-gradient(135deg, rgba(217, 70, 239, 0.2), rgba(245, 158, 11, 0.2))',
              color: 'var(--saffron-400)',
              padding: '10px',
              borderRadius: '10px',
              border: '1px solid var(--border-gold)',
              boxShadow: '0 0 15px rgba(245, 158, 11, 0.2)',
            }}
          >
            <Sparkles size={22} />
          </div>
          <div>
            <h2
              style={{
                fontSize: '17px',
                fontWeight: 800,
                margin: 0,
                color: 'var(--text-ivory)',
                letterSpacing: '0.5px',
              }}
            >
              The First 10 Minutes · Intelligence Lab
            </h2>
            <small style={{ color: 'var(--text-secondary)', fontSize: '11px' }}>
              Twin Test Benchmark · Counterfactual Reasoning · Online Trust Learning · 16 Scenarios
            </small>
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="lab-tabs" style={{ display: 'flex', gap: '8px' }}>
          <button
            className={`btn ${activeTab === 'replay' ? 'primary' : ''}`}
            onClick={() => setActiveTab('replay')}
            style={{ fontSize: '12px', padding: '6px 14px' }}
          >
            <Activity size={14} /> Evidence Replay
          </button>
          <button
            className={`btn ${activeTab === 'twin_test' ? 'primary' : ''}`}
            onClick={() => setActiveTab('twin_test')}
            style={{ fontSize: '12px', padding: '6px 14px' }}
          >
            <GitCompare size={14} /> Twin Test
          </button>
          <button
            className={`btn ${activeTab === 'counterfactual' ? 'primary' : ''}`}
            onClick={() => {
              setActiveTab('counterfactual')
              if (!counterfactualResult) runCounterfactual(selectedCfType)
            }}
            style={{ fontSize: '12px', padding: '6px 14px' }}
          >
            <HelpCircle size={14} /> Counterfactuals
          </button>
          <button
            className={`btn ${activeTab === 'learning' ? 'primary' : ''}`}
            onClick={() => setActiveTab('learning')}
            style={{ fontSize: '12px', padding: '6px 14px' }}
          >
            <BrainCircuit size={14} /> Online Trust & Health
          </button>
        </div>
      </div>

      {/* =========================================================================
          TAB 1: MINUTE-BY-MINUTE REPLAY (16 Scenarios)
         ========================================================================= */}
      {activeTab === 'replay' && (
        <div className="lab-replay-tab">
          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              marginBottom: '14px',
              background: 'var(--bg-secondary)',
              border: '1px solid var(--border-subtle)',
              padding: '10px 14px',
              borderRadius: '8px',
              flexWrap: 'wrap',
              gap: '10px',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <span style={{ fontSize: '11px', color: 'var(--text-muted)', fontWeight: 700 }}>SCENARIO:</span>
              <select
                value={replayScenario}
                onChange={e => setReplayScenario(e.target.value)}
                style={{
                  background: 'var(--bg-card)',
                  border: '1px solid var(--border-gold)',
                  color: 'var(--text-ivory)',
                  padding: '6px 10px',
                  borderRadius: '6px',
                  fontSize: '12px',
                  fontWeight: 600,
                  maxWidth: '380px',
                }}
              >
                {ALL_SCENARIOS.map(sc => (
                  <option key={sc.id} value={sc.id}>
                    {sc.label}
                  </option>
                ))}
              </select>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <button className="btn" onClick={() => setIsPlaying(!isPlaying)}>
                {isPlaying ? <Pause size={14} /> : <Play size={14} />} {isPlaying ? 'Pause' : 'Play Replay'}
              </button>
              <button className="btn" onClick={() => setCurrentMinute(Math.min(10, currentMinute + 1))}>
                <SkipForward size={14} /> Step +1m
              </button>
              <button
                className="btn"
                onClick={() => {
                  setIsPlaying(false)
                  setCurrentMinute(0)
                }}
              >
                <RotateCcw size={14} /> Reset
              </button>
            </div>
          </div>

          {/* Scrubber Range */}
          <div
            style={{
              marginBottom: '16px',
              background: 'var(--bg-card)',
              padding: '12px 16px',
              borderRadius: '8px',
              border: '1px solid var(--border-subtle)',
            }}
          >
            <div
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                fontSize: '11px',
                color: 'var(--text-muted)',
                marginBottom: '8px',
              }}
            >
              <span>Minute 0 (Initial Telemetry)</span>
              <strong style={{ color: 'var(--saffron-400)', fontSize: '14px', fontFamily: 'var(--font-mono)' }}>
                T + {currentMinute} MINUTES
              </strong>
              <span>Minute 10 (Crisis Peak / Resolution)</span>
            </div>
            <input
              type="range"
              min={0}
              max={10}
              value={currentMinute}
              onChange={e => setCurrentMinute(Number(e.target.value))}
              style={{ width: '100%', accentColor: 'var(--saffron-500)', height: '6px', cursor: 'pointer' }}
            />
          </div>

          {/* Minute Inspection Cards */}
          <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1.5fr', gap: '16px' }}>
            {/* Probabilities at this minute */}
            <div
              style={{
                background: 'var(--bg-card)',
                padding: '16px',
                borderRadius: '8px',
                border: '1px solid var(--border-card)',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                <span style={{ fontSize: '11px', fontWeight: 800, color: 'var(--text-secondary)', letterSpacing: '0.4px' }}>
                  POSTERIOR BELIEFS AT T+{currentMinute}M
                </span>
                <span className={`status-pill ${currentReplayStep.recommended_action?.toLowerCase()}`}>
                  {currentReplayStep.recommended_action || 'WATCH'}
                </span>
              </div>

              {[
                ['normal', 'H1', 'Normal conditions', '#06b6d4'],
                ['sensor_failure', 'H2', 'Sensor / Gateway failure', '#a855f7'],
                ['isolated_incident', 'H3', 'Isolated localized incident', '#f59e0b'],
                ['cascading_crisis', 'H4', 'Cascading emergency cascade', '#ef4444'],
              ].map(([key, code, label, color]) => {
                const val = currentReplayStep.probabilities?.[key] ?? 0
                return (
                  <div key={key} style={{ marginBottom: '10px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', marginBottom: '4px' }}>
                      <span style={{ color: 'var(--text-primary)' }}>
                        <strong style={{ color }}>{code}</strong> · {label}
                      </span>
                      <strong style={{ fontFamily: 'var(--font-mono)', color: 'var(--text-ivory)' }}>{pct(val)}</strong>
                    </div>
                    <div style={{ height: '7px', background: 'var(--bg-tertiary)', borderRadius: '4px', overflow: 'hidden' }}>
                      <div
                        style={{
                          height: '100%',
                          width: pct(val),
                          background: color,
                          transition: 'width 0.3s ease',
                        }}
                      />
                    </div>
                  </div>
                )
              })}
            </div>

            {/* Observations and Missing Information */}
            <div
              style={{
                background: 'var(--bg-card)',
                padding: '16px',
                borderRadius: '8px',
                border: '1px solid var(--border-card)',
              }}
            >
              <span
                style={{
                  fontSize: '11px',
                  fontWeight: 800,
                  color: 'var(--text-secondary)',
                  display: 'block',
                  marginBottom: '10px',
                  letterSpacing: '0.4px',
                }}
              >
                EVIDENCE RECEIVED AT T+{currentMinute}M ({currentReplayStep.events_count || 0} TOTAL ACCUMULATED)
              </span>

              <div style={{ maxHeight: '120px', overflowY: 'auto', marginBottom: '14px' }}>
                {(currentReplayStep.new_events_this_minute || []).length > 0 ? (
                  currentReplayStep.new_events_this_minute.map((item: string, idx: number) => (
                    <div
                      key={idx}
                      style={{
                        fontSize: '12px',
                        color: 'var(--text-ivory)',
                        padding: '5px 0',
                        borderBottom: '1px solid var(--border-subtle)',
                        display: 'flex',
                        gap: '8px',
                      }}
                    >
                      <span style={{ color: 'var(--saffron-400)' }}>&bull;</span>
                      <span>{item}</span>
                    </div>
                  ))
                ) : (
                  <div style={{ fontSize: '12px', color: 'var(--text-muted)', fontStyle: 'italic', padding: '10px 0' }}>
                    No new discrete observations received at minute {currentMinute}. Continuous telemetry stream unchanged.
                  </div>
                )}
              </div>

              <div
                style={{
                  background: 'rgba(245, 158, 11, 0.08)',
                  padding: '10px 12px',
                  borderRadius: '6px',
                  borderLeft: '3px solid var(--saffron-500)',
                }}
              >
                <div style={{ fontSize: '10px', fontWeight: 800, color: 'var(--saffron-400)', marginBottom: '3px', letterSpacing: '0.5px' }}>
                  INFORMATION REQUIRED TO CONFIRM OR DISCONFIRM CASCADE:
                </div>
                <div style={{ fontSize: '12px', color: 'var(--text-primary)', lineHeight: '1.4' }}>
                  {currentReplayStep.missing_information_needed || 'Monitoring stream status.'}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* =========================================================================
          TAB 2: THE TWIN TEST BENCHMARK
         ========================================================================= */}
      {activeTab === 'twin_test' && (
        <div className="lab-twin-tab">
          {/* Top Verification Status Banner */}
          <div
            style={{
              background: twinData?.identical_prefix_verified
                ? 'linear-gradient(135deg, rgba(16, 185, 129, 0.15), rgba(22, 12, 37, 0.9))'
                : 'linear-gradient(135deg, rgba(239, 68, 68, 0.15), rgba(22, 12, 37, 0.9))',
              border: `1px solid ${twinData?.identical_prefix_verified ? 'rgba(16, 185, 129, 0.4)' : 'rgba(239, 68, 68, 0.4)'}`,
              padding: '14px 18px',
              borderRadius: '10px',
              marginBottom: '16px',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              flexWrap: 'wrap',
              gap: '12px',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              {twinData?.identical_prefix_verified ? (
                <div style={{ color: '#10b981' }}>
                  <CheckCircle2 size={24} />
                </div>
              ) : (
                <div style={{ color: '#ef4444' }}>
                  <AlertCircle size={24} />
                </div>
              )}
              <div>
                <strong style={{ fontSize: '14px', color: 'var(--text-ivory)', letterSpacing: '0.4px' }}>
                  {twinData?.identical_prefix_verified
                    ? 'FORMAL PREFIX ASSERTION PASSED: MINUTES 0 TO 6 ARE STRICTLY IDENTICAL'
                    : 'PREFIX ASSERTION FAILED'}
                </strong>
                <p style={{ margin: '3px 0 0 0', fontSize: '12px', color: 'var(--text-secondary)' }}>
                  {twinData?.prefix_verification_message ||
                    'Both twins receive identical evidence, timestamps, and source IDs up to minute 6, then diverge at minute 7.'}
                </p>
              </div>
            </div>

            <span
              style={{
                fontSize: '11px',
                fontFamily: 'var(--font-mono)',
                fontWeight: 800,
                padding: '4px 10px',
                borderRadius: '6px',
                background: 'rgba(245, 158, 11, 0.2)',
                color: 'var(--saffron-400)',
                border: '1px solid var(--border-gold)',
              }}
            >
              DIVERGENCE AT MINUTE {twinData?.divergence_minute ?? 7}
            </span>
          </div>

          {/* Key Challenge Evaluation Metrics */}
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
              gap: '12px',
              marginBottom: '16px',
            }}
          >
            <div style={{ background: 'var(--bg-card)', padding: '12px 14px', borderRadius: '8px', border: '1px solid var(--border-card)' }}>
              <span style={{ fontSize: '10px', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Divergence Split Point</span>
              <div style={{ fontSize: '18px', fontWeight: 800, color: 'var(--saffron-400)', marginTop: '2px', fontFamily: 'var(--font-mono)' }}>
                Minute {twinData?.divergence_minute ?? 7}
              </div>
              <small style={{ color: 'var(--text-dim)', fontSize: '10px' }}>Min 0-6 identical prefix</small>
            </div>

            <div style={{ background: 'var(--bg-card)', padding: '12px 14px', borderRadius: '8px', border: '1px solid var(--border-card)' }}>
              <span style={{ fontSize: '10px', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Time to Justified Detection</span>
              <div style={{ fontSize: '18px', fontWeight: 800, color: '#10b981', marginTop: '2px', fontFamily: 'var(--font-mono)' }}>
                T + {twinData?.time_to_justified_detection_minute ?? 7} min
              </div>
              <small style={{ color: 'var(--text-dim)', fontSize: '10px' }}>Immediate at corroborated divergence</small>
            </div>

            <div style={{ background: 'var(--bg-card)', padding: '12px 14px', borderRadius: '8px', border: '1px solid var(--border-card)' }}>
              <span style={{ fontSize: '10px', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Premature Penalty</span>
              <div style={{ fontSize: '18px', fontWeight: 800, color: '#06b6d4', marginTop: '2px', fontFamily: 'var(--font-mono)' }}>
                {twinData?.premature_confidence_penalty?.toFixed(2) ?? '0.00'}
              </div>
              <small style={{ color: 'var(--text-dim)', fontSize: '10px' }}>Zero early escalation in prefix</small>
            </div>

            <div style={{ background: 'var(--bg-card)', padding: '12px 14px', borderRadius: '8px', border: '1px solid var(--border-card)' }}>
              <span style={{ fontSize: '10px', color: 'var(--text-muted)', textTransform: 'uppercase' }}>False-Alarm Cost Avoided</span>
              <div style={{ fontSize: '18px', fontWeight: 800, color: 'var(--fuchsia-400)', marginTop: '2px', fontFamily: 'var(--font-mono)' }}>
                +${twinData?.false_alarm_cost_avoided?.toFixed(2) ?? '9.30'}
              </div>
              <small style={{ color: 'var(--text-dim)', fontSize: '10px' }}>Twin B escalation avoided</small>
            </div>

            <div style={{ background: 'var(--bg-card)', padding: '12px 14px', borderRadius: '8px', border: '1px solid var(--border-card)' }}>
              <span style={{ fontSize: '10px', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Missed-Detection Cost Avoided</span>
              <div style={{ fontSize: '18px', fontWeight: 800, color: '#ef4444', marginTop: '2px', fontFamily: 'var(--font-mono)' }}>
                +${twinData?.missed_detection_cost_avoided?.toFixed(2) ?? '17.00'}
              </div>
              <small style={{ color: 'var(--text-dim)', fontSize: '10px' }}>Twin A cascade captured</small>
            </div>
          </div>

          {/* Interactive Scrub Timeline */}
          <div
            style={{
              background: 'var(--bg-card)',
              padding: '12px 16px',
              borderRadius: '8px',
              border: '1px solid var(--border-subtle)',
              marginBottom: '16px',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
              <span style={{ fontSize: '11px', color: 'var(--text-muted)', fontWeight: 700 }}>SCRUB TWIN TEST TIMELINE:</span>
              <span
                style={{
                  fontSize: '11px',
                  fontFamily: 'var(--font-mono)',
                  fontWeight: 800,
                  color: twinMinute < 7 ? '#06b6d4' : twinMinute === 7 ? 'var(--saffron-400)' : '#ef4444',
                }}
              >
                {twinMinute < 7
                  ? `MINUTE ${twinMinute} (SHARED IDENTICAL PREFIX)`
                  : twinMinute === 7
                  ? `MINUTE 7 (DIVERGENCE MOMENT)`
                  : `MINUTE ${twinMinute} (FULL DIVERGENCE)`}
              </span>
            </div>
            <input
              type="range"
              min={0}
              max={10}
              value={twinMinute}
              onChange={e => setTwinMinute(Number(e.target.value))}
              style={{ width: '100%', accentColor: 'var(--saffron-500)', height: '6px' }}
            />
          </div>

          {/* Side-by-Side Split Cards at Current Scrubber Minute */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '16px' }}>
            {/* Twin A Card */}
            <div
              style={{
                background: 'var(--bg-card)',
                padding: '16px',
                borderRadius: '8px',
                border: '1px solid rgba(239, 68, 68, 0.45)',
                boxShadow: twinMinute >= 7 ? '0 0 20px rgba(239, 68, 68, 0.12)' : 'none',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                <strong style={{ color: '#ef4444', fontSize: '13px', letterSpacing: '0.5px' }}>
                  TWIN A · GENUINE CASCADE
                </strong>
                <span className={`status-pill ${twinAStep.recommended_action?.toLowerCase()}`}>
                  {twinAStep.recommended_action || 'WATCH'}
                </span>
              </div>

              <div style={{ display: 'flex', alignItems: 'baseline', gap: '8px', marginBottom: '6px' }}>
                <span style={{ fontSize: '28px', fontWeight: 800, color: 'var(--text-ivory)', fontFamily: 'var(--font-mono)' }}>
                  {pct(twinAStep.probabilities?.cascading_crisis)}
                </span>
                <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Cascade Probability P(H4)</span>
              </div>

              <div style={{ fontSize: '11px', color: 'var(--text-secondary)', marginBottom: '10px' }}>
                Expected Action Loss: <strong style={{ color: 'var(--text-ivory)' }}>{twinAStep.expected_costs?.[twinAStep.recommended_action]?.toFixed(2) ?? '--'}</strong>
              </div>

              <div
                style={{
                  background: 'var(--bg-secondary)',
                  padding: '10px 12px',
                  borderRadius: '6px',
                  border: '1px solid var(--border-subtle)',
                  minHeight: '60px',
                  fontSize: '12px',
                  color: 'var(--text-primary)',
                }}
              >
                {twinMinute < 7 ? (
                  <span style={{ color: 'var(--text-muted)' }}>
                    Precipitation 22-32 mm/h, water stage 0.9-1.2m. Ambiguous state shared with Twin B.
                  </span>
                ) : (
                  <div>
                    <strong style={{ color: '#ef4444' }}>Arterial Road Submersion Corroborated: </strong>
                    Independent traffic police confirm arterial gridlock. Cascade probability surges to 97%.
                  </div>
                )}
              </div>
            </div>

            {/* Twin B Card */}
            <div
              style={{
                background: 'var(--bg-card)',
                padding: '16px',
                borderRadius: '8px',
                border: '1px solid rgba(168, 85, 247, 0.45)',
                boxShadow: twinMinute >= 7 ? '0 0 20px rgba(168, 85, 247, 0.12)' : 'none',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                <strong style={{ color: '#c084fc', fontSize: '13px', letterSpacing: '0.5px' }}>
                  TWIN B · SENSOR FAILURE LOOK-ALIKE
                </strong>
                <span className={`status-pill ${twinBStep.recommended_action?.toLowerCase()}`}>
                  {twinBStep.recommended_action || 'WATCH'}
                </span>
              </div>

              <div style={{ display: 'flex', alignItems: 'baseline', gap: '8px', marginBottom: '6px' }}>
                <span style={{ fontSize: '28px', fontWeight: 800, color: 'var(--text-ivory)', fontFamily: 'var(--font-mono)' }}>
                  {pct(twinBStep.probabilities?.source_failure ?? twinBStep.probabilities?.sensor_failure)}
                </span>
                <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Sensor Failure Prob P(H2)</span>
              </div>

              <div style={{ fontSize: '11px', color: 'var(--text-secondary)', marginBottom: '10px' }}>
                Expected Action Loss: <strong style={{ color: 'var(--text-ivory)' }}>{twinBStep.expected_costs?.[twinBStep.recommended_action]?.toFixed(2) ?? '--'}</strong>
              </div>

              <div
                style={{
                  background: 'var(--bg-secondary)',
                  padding: '10px 12px',
                  borderRadius: '6px',
                  border: '1px solid var(--border-subtle)',
                  minHeight: '60px',
                  fontSize: '12px',
                  color: 'var(--text-primary)',
                }}
              >
                {twinMinute < 7 ? (
                  <span style={{ color: 'var(--text-muted)' }}>
                    Precipitation 22-32 mm/h, water stage 0.9-1.2m. Ambiguous state shared with Twin A.
                  </span>
                ) : (
                  <div>
                    <strong style={{ color: '#c084fc' }}>Gateway Controller Failure Isolated: </strong>
                    Water telemetry gateway times out. High readings discounted as sensor malfunction. False alarm avoided.
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Full Side-by-Side Timeline Comparative Table */}
          <div
            style={{
              background: 'var(--bg-card)',
              padding: '16px',
              borderRadius: '8px',
              border: '1px solid var(--border-card)',
              marginBottom: '16px',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
              <strong style={{ fontSize: '13px', color: 'var(--text-ivory)', letterSpacing: '0.4px' }}>
                CHRONOLOGICAL SIDE-BY-SIDE TRAJECTORY (T+0 TO T+10 MINUTES)
              </strong>
              <span style={{ fontSize: '10px', color: 'var(--text-muted)' }}>
                Rows 0-6 verify identical prefix; Rows 7-10 capture divergence
              </span>
            </div>

            <div className="table-scroll" style={{ maxHeight: '280px', overflowY: 'auto' }}>
              <table>
                <thead>
                  <tr>
                    <th>MINUTE</th>
                    <th>PREFIX STATUS</th>
                    <th>TWIN A P(CASCADE)</th>
                    <th>TWIN B P(CASCADE)</th>
                    <th>TWIN A P(FAIL)</th>
                    <th>TWIN B P(FAIL)</th>
                    <th>ACTION A</th>
                    <th>ACTION B</th>
                    <th>KEY OBSERVATIONS</th>
                  </tr>
                </thead>
                <tbody>
                  {sideBySideList.map((row: any) => {
                    const isDiverged = row.minute >= (twinData?.divergence_minute ?? 7)
                    return (
                      <tr
                        key={row.minute}
                        style={{
                          background: row.minute === twinMinute ? 'rgba(245, 158, 11, 0.12)' : isDiverged ? 'rgba(239, 68, 68, 0.04)' : 'transparent',
                        }}
                      >
                        <td style={{ fontFamily: 'var(--font-mono)', fontWeight: 700, color: 'var(--text-ivory)' }}>
                          T+{row.minute}m
                        </td>
                        <td>
                          {row.is_prefix_shared ? (
                            <span style={{ fontSize: '9px', padding: '2px 6px', borderRadius: '4px', background: 'rgba(6, 182, 212, 0.15)', color: '#06b6d4', fontWeight: 700 }}>
                              IDENTICAL PREFIX
                            </span>
                          ) : (
                            <span style={{ fontSize: '9px', padding: '2px 6px', borderRadius: '4px', background: 'rgba(239, 68, 68, 0.2)', color: '#ef4444', fontWeight: 700 }}>
                              DIVERGED
                            </span>
                          )}
                        </td>
                        <td style={{ fontFamily: 'var(--font-mono)', color: row.twin_a_cascade_prob > 0.5 ? '#ef4444' : 'var(--text-secondary)' }}>
                          {pct(row.twin_a_cascade_prob)}
                        </td>
                        <td style={{ fontFamily: 'var(--font-mono)', color: row.twin_b_cascade_prob > 0.5 ? '#ef4444' : 'var(--text-secondary)' }}>
                          {pct(row.twin_b_cascade_prob)}
                        </td>
                        <td style={{ fontFamily: 'var(--font-mono)', color: row.twin_a_sensor_failure_prob > 0.5 ? '#c084fc' : 'var(--text-secondary)' }}>
                          {pct(row.twin_a_sensor_failure_prob)}
                        </td>
                        <td style={{ fontFamily: 'var(--font-mono)', color: row.twin_b_sensor_failure_prob > 0.5 ? '#c084fc' : 'var(--text-secondary)' }}>
                          {pct(row.twin_b_sensor_failure_prob)}
                        </td>
                        <td>
                          <span className={`status-pill ${row.twin_a_action?.toLowerCase()}`} style={{ fontSize: '9px', padding: '2px 6px' }}>
                            {row.twin_a_action}
                          </span>
                        </td>
                        <td>
                          <span className={`status-pill ${row.twin_b_action?.toLowerCase()}`} style={{ fontSize: '9px', padding: '2px 6px' }}>
                            {row.twin_b_action}
                          </span>
                        </td>
                        <td style={{ fontSize: '11px', color: 'var(--text-muted)', maxWidth: '240px' }}>
                          {isDiverged ? (
                            <span>
                              <strong style={{ color: '#ef4444' }}>A:</strong> {row.events_a?.[0] || 'Flows continuing'} |{' '}
                              <strong style={{ color: '#c084fc' }}>B:</strong> {row.events_b?.[0] || 'Hardware timeout'}
                            </span>
                          ) : (
                            <span>{row.events_a?.[0] || 'Ambiguous shared telemetry'}</span>
                          )}
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          </div>

          {/* Causal Explanation of Divergence */}
          <div
            style={{
              background: 'linear-gradient(135deg, rgba(32, 16, 54, 0.95), rgba(13, 7, 20, 0.95))',
              border: '1px solid var(--border-gold)',
              padding: '16px',
              borderRadius: '8px',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
              <ShieldCheck size={18} style={{ color: 'var(--saffron-400)' }} />
              <strong style={{ fontSize: '13px', color: 'var(--text-ivory)', letterSpacing: '0.4px' }}>
                WHY DID THE TWINS DIVERGE AT MINUTE 7?
              </strong>
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px', fontSize: '12px', marginTop: '10px' }}>
              <div style={{ background: 'var(--bg-secondary)', padding: '12px', borderRadius: '6px', borderLeft: '3px solid #ef4444' }}>
                <strong style={{ color: '#ef4444', display: 'block', marginBottom: '4px' }}>Twin A (Genuine Cascade):</strong>
                <p style={{ margin: 0, color: 'var(--text-secondary)', lineHeight: '1.5' }}>
                  At minute 7, independent traffic police reports confirmed arterial road flooding. The Bayesian engine received multiple correlated physical signals from independent sources, exceeding the gating threshold and escalating response posture to ALERT and ESCALATE.
                </p>
              </div>

              <div style={{ background: 'var(--bg-secondary)', padding: '12px', borderRadius: '6px', borderLeft: '3px solid #a855f7' }}>
                <strong style={{ color: '#c084fc', display: 'block', marginBottom: '4px' }}>Twin B (Sensor Glitch):</strong>
                <p style={{ margin: 0, color: 'var(--text-secondary)', lineHeight: '1.5' }}>
                  At minute 7, the drainage sensor gateway reported a hardware controller fault. The engine tracked common-cause dependency, discounted anomalous water readings as sensor artifacts, and kept response posture at PREPARE/WATCH, successfully averting a costly false alarm.
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* =========================================================================
          TAB 3: WHAT-IF COUNTERFACTUAL SIMULATOR
         ========================================================================= */}
      {activeTab === 'counterfactual' && (
        <div className="lab-cf-tab">
          <div style={{ marginBottom: '16px' }}>
            <span style={{ fontSize: '11px', color: 'var(--text-muted)', display: 'block', marginBottom: '8px', fontWeight: 700 }}>
              SELECT OPERATIONAL HYPOTHETICAL QUESTION:
            </span>
            <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
              {[
                ['weather_offline', 'What if weather feed goes offline?'],
                ['independent_confirmation', 'What if police confirm road submersion?'],
                ['rainfall_spikes', 'What if rain surges to 85 mm/h cloudburst?'],
                ['duplicate_retraction', 'What if citizen reports are retracted as rumors?'],
              ].map(([key, label]) => (
                <button
                  key={key}
                  className={`btn ${selectedCfType === key ? 'primary' : ''}`}
                  onClick={() => runCounterfactual(key)}
                  disabled={cfLoading}
                  style={{ fontSize: '12px', padding: '8px 14px' }}
                >
                  <Zap size={13} /> {label}
                </button>
              ))}
            </div>
          </div>

          {counterfactualResult && (
            <div
              style={{
                background: 'var(--bg-card)',
                padding: '16px',
                borderRadius: '8px',
                border: '1px solid var(--border-card)',
              }}
            >
              <div
                style={{
                  background: 'rgba(245, 158, 11, 0.08)',
                  borderLeft: '3px solid var(--saffron-500)',
                  padding: '10px 14px',
                  borderRadius: '6px',
                  marginBottom: '16px',
                }}
              >
                <strong style={{ fontSize: '12px', color: 'var(--saffron-400)' }}>ASSUMPTIONS TESTED:</strong>
                <p style={{ margin: '3px 0 0 0', fontSize: '12px', color: 'var(--text-ivory)' }}>
                  {counterfactualResult.assumptions}
                </p>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '14px' }}>
                <div style={{ background: 'var(--bg-secondary)', padding: '14px', borderRadius: '8px', border: '1px solid var(--border-subtle)' }}>
                  <span style={{ fontSize: '10px', color: 'var(--text-muted)', textTransform: 'uppercase' }}>BASELINE OPERATIONAL ACTION</span>
                  <div style={{ fontSize: '20px', fontWeight: 800, color: 'var(--text-ivory)', marginTop: '4px' }}>
                    {counterfactualResult.baseline_action}
                  </div>
                  <small style={{ color: 'var(--text-secondary)' }}>
                    Cascade Prob: {pct(counterfactualResult.baseline_probabilities?.cascading_crisis)}
                  </small>
                </div>

                <div style={{ background: 'var(--bg-secondary)', padding: '14px', borderRadius: '8px', border: '1px solid var(--border-gold)' }}>
                  <span style={{ fontSize: '10px', color: 'var(--saffron-400)', textTransform: 'uppercase' }}>COUNTERFACTUAL RECOMPUTED ACTION</span>
                  <div style={{ fontSize: '20px', fontWeight: 800, color: 'var(--saffron-400)', marginTop: '4px' }}>
                    {counterfactualResult.counterfactual_action}
                  </div>
                  <small style={{ color: counterfactualResult.delta_cascade_prob > 0 ? '#ef4444' : '#10b981' }}>
                    Cascade Prob: {pct(counterfactualResult.counterfactual_probabilities?.cascading_crisis)} ({counterfactualResult.delta_cascade_prob > 0 ? '+' : ''}{Math.round(counterfactualResult.delta_cascade_prob * 100)}%)
                  </small>
                </div>
              </div>

              <div style={{ fontSize: '11px', color: 'var(--text-dim)', fontStyle: 'italic' }}>
                {counterfactualResult.disclaimer}
              </div>
            </div>
          )}
        </div>
      )}

      {/* =========================================================================
          TAB 4: ONLINE TRUST LEARNING & SOURCE HEALTH
         ========================================================================= */}
      {activeTab === 'learning' && (
        <div className="lab-learning-tab">
          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              marginBottom: '16px',
              background: 'var(--bg-secondary)',
              padding: '12px 16px',
              borderRadius: '8px',
              border: '1px solid var(--border-subtle)',
              flexWrap: 'wrap',
              gap: '10px',
            }}
          >
            <div>
              <strong style={{ fontSize: '13px', color: 'var(--text-ivory)' }}>
                Bayesian Conjugate Trust Updating & Environmental Base-Rate Adaptation
              </strong>
              <p style={{ margin: '2px 0 0 0', fontSize: '11px', color: 'var(--text-secondary)' }}>
                Learns Beta parameters (α, β, variance) per source from ground truth verification; tracks monsoon Dirichlet priors.
              </p>
            </div>

            <button
              className="btn primary"
              onClick={runLearningExperiment}
              disabled={learningLoading}
              style={{ fontSize: '12px', padding: '6px 14px' }}
            >
              <Zap size={14} /> {learningLoading ? 'Updating Trust...' : 'Run Trust Update Experiment'}
            </button>
          </div>

          {/* Environmental Base-Rate Drift Card */}
          {baseRateDrift && (
            <div
              style={{
                background: 'var(--bg-card)',
                padding: '14px',
                borderRadius: '8px',
                border: '1px solid var(--border-card)',
                marginBottom: '16px',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
                <span style={{ fontSize: '11px', fontWeight: 800, color: 'var(--saffron-400)', letterSpacing: '0.4px' }}>
                  ENVIRONMENTAL BASE-RATE DRIFT TRACKER (DIRICHLET ADAPTIVE PRIORS)
                </span>
                <span style={{ fontSize: '10px', color: 'var(--text-muted)' }}>
                  Active Season: {baseRateDrift.current_season || 'Monsoon Season'} · Drift: {baseRateDrift.drift_detected ? 'ACTIVE' : 'NOMINAL'}
                </span>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: '10px' }}>
                {Object.entries(baseRateDrift.adapted_priors || {}).map(([hyp, p]: [string, any]) => (
                  <div key={hyp} style={{ background: 'var(--bg-secondary)', padding: '10px', borderRadius: '6px', border: '1px solid var(--border-subtle)' }}>
                    <span style={{ fontSize: '9px', color: 'var(--text-muted)', textTransform: 'uppercase' }}>{hyp.replace('_', ' ')}</span>
                    <div style={{ fontSize: '16px', fontWeight: 800, color: 'var(--text-ivory)', fontFamily: 'var(--font-mono)' }}>
                      {pct(p)}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Experiment Result Callout */}
          {experimentResult && (
            <div
              style={{
                background: 'rgba(217, 70, 239, 0.08)',
                border: '1px solid rgba(217, 70, 239, 0.3)',
                padding: '14px',
                borderRadius: '8px',
                marginBottom: '16px',
              }}
            >
              <strong style={{ fontSize: '12px', color: 'var(--fuchsia-400)', display: 'block', marginBottom: '4px' }}>
                EXPERIMENT VERIFICATION RESULT:
              </strong>
              <p style={{ margin: '0 0 8px 0', fontSize: '12px', color: 'var(--text-ivory)' }}>
                {experimentResult.message || 'Ground-truth outcome successfully verified. Beta conjugate trust posteriors updated.'}
              </p>
              <div style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>
                Source: <strong style={{ color: 'var(--text-ivory)' }}>{experimentResult.source_id}</strong> | New Trust Mean: <strong style={{ color: '#10b981' }}>{(experimentResult.updated_trust_mean * 100)?.toFixed(1)}%</strong> | Variance: {experimentResult.updated_variance?.toFixed(5)}
              </div>
            </div>
          )}

          {/* Sources Beta Trust Parameters Grid */}
          <div
            style={{
              background: 'var(--bg-card)',
              padding: '16px',
              borderRadius: '8px',
              border: '1px solid var(--border-card)',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
              <strong style={{ fontSize: '13px', color: 'var(--text-ivory)', letterSpacing: '0.4px' }}>
                ONLINE SOURCE RELIABILITY & BETA DISTRIBUTIONS
              </strong>
              <span style={{ fontSize: '10px', color: 'var(--text-muted)' }}>
                Beta(α, β) determines evidence weighting in Bayes inference
              </span>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(240px, 1fr))', gap: '12px' }}>
              {trustSources.map((src: any) => {
                const alpha = src.alpha ?? 9.5
                const beta = src.beta ?? 1.5
                const mean = alpha / (alpha + beta)
                const variance = (alpha * beta) / (Math.pow(alpha + beta, 2) * (alpha + beta + 1))

                return (
                  <div
                    key={src.source_id}
                    style={{
                      background: 'var(--bg-secondary)',
                      padding: '12px',
                      borderRadius: '6px',
                      border: '1px solid var(--border-subtle)',
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                      <strong style={{ fontSize: '12px', color: 'var(--text-ivory)' }}>{src.source_id}</strong>
                      <span
                        style={{
                          fontSize: '9px',
                          padding: '1px 5px',
                          borderRadius: '3px',
                          background: src.status === 'healthy' ? 'rgba(16, 185, 129, 0.2)' : 'rgba(234, 179, 8, 0.2)',
                          color: src.status === 'healthy' ? '#10b981' : '#eab308',
                        }}
                      >
                        {src.status}
                      </span>
                    </div>

                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '6px', fontSize: '11px', color: 'var(--text-secondary)', marginBottom: '6px' }}>
                      <div>Trust Mean: <strong style={{ color: 'var(--text-ivory)' }}>{pct(mean)}</strong></div>
                      <div>Gateway: <strong style={{ color: '#06b6d4' }}>{src.gateway_id || 'direct'}</strong></div>
                      <div>Alpha: <strong style={{ color: 'var(--text-ivory)' }}>{alpha.toFixed(1)}</strong></div>
                      <div>Beta: <strong style={{ color: 'var(--text-ivory)' }}>{beta.toFixed(1)}</strong></div>
                    </div>

                    <div style={{ height: '4px', background: 'var(--bg-tertiary)', borderRadius: '2px', overflow: 'hidden' }}>
                      <div style={{ height: '100%', width: pct(mean), background: 'var(--saffron-500)' }} />
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
