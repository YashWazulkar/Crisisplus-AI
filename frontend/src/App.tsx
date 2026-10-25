import { useCallback, useEffect, useMemo, useState } from 'react'
import {
  Activity,
  AlertTriangle,
  BrainCircuit,
  RadioTower,
  ShieldCheck,
  Waves,
  Play,
  Pause,
  RotateCcw,
  Siren,
  Download,
  Zap,
  Map as MapIcon,
  Layers,
  Sparkles,
  GitMerge,
  Target,
  RefreshCw,
  MapPin,
  Flame,
  Globe,
  Sliders,
  Filter,
  Clock,
  ExternalLink,
  ChevronRight,
  Droplets,
  Building2,
  Info,
} from 'lucide-react'
import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'

import CrisisMap from './components/Map'
import IntelligenceLab from './components/IntelligenceLab'
import CausalGraph from './components/CausalGraph'
import SourceHealthPanel from './components/SourceHealthModal'
import EvaluationPanel from './components/EvaluationPanel'
import LocationModal from './components/LocationModal'
import SubregionDetailPanel from './components/SubregionDetailPanel'

const API = 'http://127.0.0.1:8000'
type AnyObj = Record<string, any>
const pct = (v: number) => `${Math.round((v || 0) * 100)}%`
const pretty = (s: string) => (s || '').replace(/_/g, ' ')

type ViewTab = 'overview' | 'map' | 'feed' | 'forecasts' | 'sources' | 'lab' | 'evaluation'

export default function App() {
  const [state, setState] = useState<AnyObj>({})
  const [scenarios, setScenarios] = useState<{ id: string; name: string }[]>([])
  const [connected, setConnected] = useState(false)
  const [speed, setSpeed] = useState(1)
  const [error, setError] = useState('')
  const [activeTab, setActiveTab] = useState<ViewTab>('overview')
  const [showLocationModal, setShowLocationModal] = useState(false)
  const [selectedZoneId, setSelectedZoneId] = useState<string | null>(null)

  // Map and Feed Filters
  const [selectedEvent, setSelectedEvent] = useState<AnyObj | null>(null)
  const [eventSearch, setEventSearch] = useState('')
  const [selectedCategory, setSelectedCategory] = useState('all')
  const [selectedProvenance, setSelectedProvenance] = useState('all')
  const [selectedVerification, setSelectedVerification] = useState('all')

  const refresh = useCallback(async () => {
    try {
      const r = await fetch(`${API}/api/state`)
      if (!r.ok) throw new Error('Backend unavailable')
      setState(await r.json())
      setError('')
    } catch {
      setError('Backend not connected. Start FastAPI backend on port 8000.')
    }
  }, [])

  useEffect(() => {
    refresh()
    fetch(`${API}/api/scenarios`)
      .then(r => r.json())
      .then(setScenarios)
      .catch(() => {})

    let ws: WebSocket | undefined
    try {
      ws = new WebSocket('ws://127.0.0.1:8000/ws')
      ws.onopen = () => setConnected(true)
      ws.onclose = () => setConnected(false)
      ws.onmessage = e => {
        try {
          const msg = JSON.parse(e.data)
          if (msg.snapshot) setState((old: AnyObj) => ({ ...old, ...msg.snapshot }))
        } catch {}
      }
    } catch {
      setConnected(false)
    }

    const timer = window.setInterval(refresh, 3000)
    return () => {
      window.clearInterval(timer)
      ws?.close()
    }
  }, [refresh])

  const act = async (path: string, method = 'POST', body?: any) => {
    try {
      const opts: RequestInit = { method }
      if (body) {
        opts.headers = { 'Content-Type': 'application/json' }
        opts.body = JSON.stringify(body)
      }
      await fetch(`${API}${path}`, opts)
      await refresh()
    } catch {
      setError('Could not reach backend.')
    }
  }

  const choose = async (id: string) => {
    await act(`/api/scenario/${id}`)
    await refresh()
  }

  const switchMode = async (newMode: 'live' | 'simulation') => {
    await act('/api/mode', 'POST', { mode: newMode })
  }

  const pollNow = async (sourceId?: string) => {
    await act(`/api/ingestion/poll${sourceId ? `?source=${sourceId}` : ''}`, 'POST')
  }

  const updateLocation = async (latitude: number, longitude: number, name: string) => {
    await act('/api/ingestion/location', 'POST', { latitude, longitude, name })
  }

  const history = useMemo(
    () =>
      (state.ledger || [])
        .slice()
        .reverse()
        .map((x: AnyObj, i: number) => ({
          tick: x.tick || i + 1,
          cascade: x.posterior?.cascading_crisis || 0,
          isolated: x.posterior?.isolated_incident || 0,
          failure: x.posterior?.source_failure || 0,
        })),
    [state.ledger]
  )

  const probs = state.probabilities || {
    normal: 0.55,
    source_failure: 0.15,
    isolated_incident: 0.2,
    cascading_crisis: 0.1,
  }

  const action = state.action || 'WATCH'
  const actionClass = action.toLowerCase()
  const events = state.events || []
  const sources = state.sources_health || state.sources || []
  const forecasts = state.forecasts || []
  const ledger = state.ledger || []
  const anomalies = state.active_anomalies || []
  const causalGraph = state.causal_graph || {}
  const location = state.monitored_location || {
    latitude: 21.1458,
    longitude: 79.0882,
    name: 'Nagpur District, Maharashtra, India',
  }
  const mode = state.mode || 'live'
  const monitoringMode = state.monitoring_mode || 'MIXED'
  const riskOverview = state.risk_overview || {}
  const xai = state.xai_explanation || {}
  const subregions = state.subregions || {}
  const eventCounts = state.event_counts || { total_active: events.length, verified: 0, unverified: 0 }

  // Filtered Events for Live Feed
  const filteredEvents = useMemo(() => {
    return events.filter((e: AnyObj) => {
      const matchesSearch =
        !eventSearch ||
        (e.title || '').toLowerCase().includes(eventSearch.toLowerCase()) ||
        (e.source_id || '').toLowerCase().includes(eventSearch.toLowerCase()) ||
        (e.region || '').toLowerCase().includes(eventSearch.toLowerCase()) ||
        (e.assigned_zone_name || '').toLowerCase().includes(eventSearch.toLowerCase())

      const matchesCat =
        selectedCategory === 'all' ||
        (selectedCategory === 'weather' && ['rainfall', 'wind_gust', 'severe_weather'].includes(e.event_type)) ||
        (selectedCategory === 'drainage' && ['water_level', 'drainage_overflow', 'road_flooding'].includes(e.event_type)) ||
        (selectedCategory === 'traffic' && ['traffic_speed', 'ambulance_delay'].includes(e.event_type)) ||
        (selectedCategory === 'health' && e.event_type === 'hospital_demand') ||
        (selectedCategory === 'earthquake' && e.event_type === 'earthquake') ||
        (selectedCategory === 'wildfire' && e.event_type === 'wildfire')

      const matchesProv =
        selectedProvenance === 'all' ||
        (e.data_provenance || 'LIVE').toUpperCase() === selectedProvenance.toUpperCase()

      const matchesVerif =
        selectedVerification === 'all' ||
        (e.verification_status || 'preliminary').toLowerCase() === selectedVerification.toLowerCase()

      return matchesSearch && matchesCat && matchesProv && matchesVerif
    })
  }, [events, eventSearch, selectedCategory, selectedProvenance, selectedVerification])

  const exportReport = () => {
    const blob = new Blob([JSON.stringify(state, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `crisispulse-nagpur-${mode}-report-${new Date().toISOString().slice(0, 10)}.json`
    a.click()
    URL.revokeObjectURL(url)
  }

  // Monitoring Mode styling
  const modeBadgeColor =
    monitoringMode === 'LIVE' ? '#22c55e' : monitoringMode === 'MIXED' ? '#38bdf8' : monitoringMode === 'DEGRADED' ? '#f59e0b' : '#ef4444'

  return (
    <div className="app">
      {/* ----------------- SECTION 4.2.A: OPERATIONAL HEADER ----------------- */}
      <header className="topbar">
        <div className="brand">
          <div className="brand-icon">
            <Activity size={21} />
          </div>
          <div>
            <strong>
              CrisisPulse <span>AI · NAGPUR</span>
            </strong>
            <small>LIVE EMERGENCY INTELLIGENCE & EARLY-WARNING PLATFORM</small>
          </div>
        </div>

        {/* Operational Telemetry & Monitoring Mode */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flexWrap: 'wrap' }}>
          <div className="mode-toggle">
            <button
              className={`mode-btn ${mode === 'live' ? 'active live' : ''}`}
              onClick={() => switchMode('live')}
            >
              ● LIVE OPERATIONS
            </button>
            <button
              className={`mode-btn ${mode === 'simulation' ? 'active sim' : ''}`}
              onClick={() => switchMode('simulation')}
            >
              BENCHMARK LAB
            </button>
          </div>

          <div
            className="location-pill"
            onClick={() => setShowLocationModal(true)}
            title="Click to view/select Nagpur administrative sector"
          >
            <MapPin size={13} style={{ color: '#38bdf8' }} />
            <span>{location.name.split(',')[0]}</span>
          </div>

          {/* Monitoring Mode Badge */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              background: `${modeBadgeColor}15`,
              border: `1px solid ${modeBadgeColor}60`,
              color: modeBadgeColor,
              padding: '4px 8px',
              borderRadius: '6px',
              fontSize: '10px',
              fontFamily: 'monospace',
              fontWeight: 700,
            }}
            title="Current feed monitoring mode"
          >
            <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: modeBadgeColor }} />
            MODE: {monitoringMode}
          </div>

          <div className="top-right">
            <span className={`live-dot ${connected ? 'on' : ''}`}></span>
            <span>{connected ? 'STREAM LIVE' : 'RECONNECTING...'}</span>
          </div>

          <button
            className="btn"
            onClick={() => pollNow()}
            title="Fetch latest observations across IMD, Open-Meteo, NMC, USGS, and FIRMS"
            style={{ fontSize: '11px', padding: '6px 10px' }}
          >
            <RefreshCw size={13} /> Poll Now
          </button>

          <button
            className="btn"
            onClick={exportReport}
            title="Export full operational snapshot with audit trail JSON"
            style={{ fontSize: '11px', padding: '6px 10px' }}
          >
            <Download size={13} /> Export
          </button>
        </div>
      </header>

      <main>
        {/* Operational Status Hero Banner */}
        <section className="hero">
          <div>
            <div className="eyebrow">
              <span className="pulse"></span> NAGPUR OPERATIONAL JURISDICTION · NMC & DDMA
            </div>
            <h1>
              Emergency Decision Intelligence
              <br />
              <em>for Nagpur District & Municipal Zones.</em>
            </h1>
            <p>
              Real-time atmospheric telemetry, municipal stormwater surcharge tracking,
              and evidence-grounded xAI reasoning across 10 NMC administrative zones.
            </p>
          </div>

          <div className="hero-status">
            <div className="status-icon">
              <RadioTower size={22} />
            </div>
            <div>
              <small>DISTRICT RESPONSE LEVEL</small>
              <h2 className={actionClass}>{action}</h2>
              <p>
                {mode === 'live'
                  ? `Active Monitoring: ${location.name}`
                  : state.scenario_name || 'Genuine cascading crisis'}
              </p>
            </div>
            <span className={`status-pill ${actionClass}`}>
              {action === 'WATCH'
                ? 'PASSIVE MONITORING'
                : action === 'PREPARE'
                ? 'PRE-POSITIONING'
                : action === 'ALERT'
                ? 'FIELD VERIFICATION'
                : 'INTER-AGENCY ESCALATION'}
            </span>
          </div>
        </section>

        {error && (
          <div className="error">
            <AlertTriangle size={16} />
            {error}
          </div>
        )}

        {/* Active Anomalies Warning Alert if present */}
        {anomalies.length > 0 && (
          <div className="anomaly-alert-banner">
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <Siren size={20} style={{ color: '#ef4444' }} />
              <div>
                <strong>Active Telemetry Anomaly Detected: {anomalies[0].metric_name?.toUpperCase()}</strong>
                <p>{anomalies[0].explanation}</p>
              </div>
            </div>
            <span style={{ fontSize: '11px', background: '#ef4444', color: '#fff', padding: '3px 8px', borderRadius: '4px', fontWeight: 700 }}>
              Z-SCORE: {anomalies[0].score}
            </span>
          </div>
        )}

        {/* Navigation View Tabs */}
        <div className="nav-tabs">
          <button
            className={`nav-tab ${activeTab === 'overview' ? 'active' : ''}`}
            onClick={() => setActiveTab('overview')}
          >
            <Activity size={15} /> Operations & Risk Overview
          </button>
          <button
            className={`nav-tab ${activeTab === 'map' ? 'active' : ''}`}
            onClick={() => setActiveTab('map')}
          >
            <MapIcon size={15} /> Nagpur GIS Hazard Map
          </button>
          <button
            className={`nav-tab ${activeTab === 'feed' ? 'active' : ''}`}
            onClick={() => setActiveTab('feed')}
          >
            <Layers size={15} /> Live Intelligence Feed ({events.length})
          </button>
          <button
            className={`nav-tab ${activeTab === 'forecasts' ? 'active' : ''}`}
            onClick={() => setActiveTab('forecasts')}
          >
            <Clock size={15} /> Near-Term Forecasts & Cascades
          </button>
          <button
            className={`nav-tab ${activeTab === 'sources' ? 'active' : ''}`}
            onClick={() => setActiveTab('sources')}
          >
            <RadioTower size={15} /> Connectors & Health ({sources.length})
          </button>
          <button
            className={`nav-tab ${activeTab === 'lab' ? 'active' : ''}`}
            onClick={() => setActiveTab('lab')}
          >
            <Sparkles size={15} /> First-10-Min Lab
          </button>
          <button
            className={`nav-tab ${activeTab === 'evaluation' ? 'active' : ''}`}
            onClick={() => setActiveTab('evaluation')}
          >
            <Target size={15} /> Evaluation
          </button>
        </div>

        {/* Top KPIs Metric Grid */}
        <section className="metrics-grid">
          <Metric
            icon={<Siren size={18} />}
            label="CASCADE POSTERIOR"
            value={pct(probs.cascading_crisis)}
            sub="Cascading crisis probability P(H4)"
            tone={probs.cascading_crisis > 0.6 ? 'red' : 'amber'}
          />
          <Metric
            icon={<Waves size={18} />}
            label="NORMAL CONDITIONS"
            value={pct(probs.normal)}
            sub="Baseline hypothesis P(H1)"
            tone="blue"
          />
          <Metric
            icon={<RadioTower size={18} />}
            label="NAGPUR FEEDS HEALTHY"
            value={`${sources.filter((s: AnyObj) => s.status === 'healthy').length}/${sources.length}`}
            sub="IMD, Open-Meteo, NMC, FIRMS"
            tone="green"
          />
          <Metric
            icon={<BrainCircuit size={18} />}
            label="VERIFIED OBSERVATIONS"
            value={`${eventCounts.verified}/${eventCounts.total_active}`}
            sub={`${eventCounts.unverified} unverified · Ingestion filtered`}
            tone="purple"
          />
        </section>

        {/* ----------------- TAB: OPERATIONS & RISK OVERVIEW ----------------- */}
        {activeTab === 'overview' && (
          <>
            {/* Section 4.2.B: NAGPUR RISK OVERVIEW CARD */}
            <div
              className="panel"
              style={{
                padding: '18px 20px',
                marginBottom: '16px',
                background: 'linear-gradient(135deg, #111e33, #0b1320)',
                border: '1px solid #1e3a5f',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <ShieldCheck size={18} style={{ color: '#38bdf8' }} />
                  <h3 style={{ margin: 0, fontSize: '15px', fontWeight: 800, letterSpacing: '0.5px' }}>
                    NAGPUR OPERATIONAL RISK OVERVIEW
                  </h3>
                </div>
                <span style={{ fontSize: '11px', color: '#94a3b8', fontFamily: 'monospace' }}>
                  UPDATED: {new Date().toLocaleTimeString()}
                </span>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '14px' }}>
                <div style={{ background: '#0f172a', padding: '12px', borderRadius: '8px', border: '1px solid #1e293b' }}>
                  <span style={{ fontSize: '9px', color: '#94a3b8', textTransform: 'uppercase' }}>Dominant Hazard</span>
                  <div style={{ fontSize: '14px', fontWeight: 700, color: '#f8fafc', marginTop: '2px' }}>
                    {riskOverview.dominant_hazard || 'Normal Weather Flow'}
                  </div>
                </div>

                <div style={{ background: '#0f172a', padding: '12px', borderRadius: '8px', border: '1px solid #1e293b' }}>
                  <span style={{ fontSize: '9px', color: '#94a3b8', textTransform: 'uppercase' }}>Most Affected Area</span>
                  <div style={{ fontSize: '14px', fontWeight: 700, color: '#38bdf8', marginTop: '2px' }}>
                    {riskOverview.most_affected_area || 'Hanuman Nagar Zone'}
                  </div>
                </div>

                <div style={{ background: '#0f172a', padding: '12px', borderRadius: '8px', border: '1px solid #1e293b' }}>
                  <span style={{ fontSize: '9px', color: '#94a3b8', textTransform: 'uppercase' }}>Severity Index</span>
                  <div style={{ fontSize: '14px', fontWeight: 700, color: '#fbbf24', marginTop: '2px' }}>
                    {Math.round((riskOverview.severity_index || 0.25) * 100)}% Potential Impact
                  </div>
                </div>

                <div style={{ background: '#0f172a', padding: '12px', borderRadius: '8px', border: '1px solid #1e293b' }}>
                  <span style={{ fontSize: '9px', color: '#94a3b8', textTransform: 'uppercase' }}>Model Uncertainty</span>
                  <div style={{ fontSize: '14px', fontWeight: 700, color: '#5eead4', marginTop: '2px' }}>
                    {riskOverview.uncertainty_level || 'Moderate'} Uncertainty
                  </div>
                </div>
              </div>
            </div>

            {/* Section 4.2.D: PROMINENT xAI REASONING SECTION */}
            <div
              className="panel"
              style={{
                padding: '20px',
                marginBottom: '16px',
                background: 'linear-gradient(145deg, #0d1b2a, #10233d)',
                border: '1px solid #2563eb50',
                boxShadow: '0 8px 32px rgba(37,99,235,0.12)',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px', borderBottom: '1px solid #1e3a5f', paddingBottom: '12px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <div style={{ width: '28px', height: '28px', borderRadius: '6px', background: '#1e3a8a', display: 'grid', placeItems: 'center', color: '#60a5fa' }}>
                    <BrainCircuit size={17} />
                  </div>
                  <div>
                    <h2 style={{ margin: 0, fontSize: '16px', fontWeight: 800, color: '#f8fafc', letterSpacing: '0.4px' }}>
                      WHY DOES CRISISPULSE BELIEVE THIS AREA IS AT RISK?
                    </h2>
                    <span style={{ fontSize: '10px', color: '#94a3b8' }}>
                      EVIDENCE-GROUNDED EXPLAINABLE AI (xAI) REASONING LAYER
                    </span>
                  </div>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span
                    style={{
                      fontSize: '9px',
                      fontFamily: 'monospace',
                      padding: '3px 8px',
                      borderRadius: '4px',
                      background: xai.provider_status === 'xai_grok_live' ? '#22c55e20' : '#38bdf820',
                      color: xai.provider_status === 'xai_grok_live' ? '#22c55e' : '#38bdf8',
                      border: `1px solid ${xai.provider_status === 'xai_grok_live' ? '#22c55e' : '#38bdf8'}40`,
                    }}
                  >
                    ENGINE: {xai.model_identifier || 'xAI Grok / Deterministic'}
                  </span>
                </div>
              </div>

              {/* Rationale and Synthesis */}
              <div style={{ marginBottom: '14px' }}>
                <p style={{ fontSize: '13px', lineHeight: '1.7', color: '#e2e8f0', margin: '0 0 10px' }}>
                  {xai.decision_rationale || xai.summary || 'Processing analytical evidence packet...'}
                </p>

                {xai.evidence_synthesis && (
                  <div style={{ background: '#0b1320', padding: '10px 14px', borderRadius: '6px', fontSize: '11px', border: '1px solid #1e293b' }}>
                    <strong style={{ color: '#38bdf8' }}>Supporting Field Evidence: </strong>
                    <span style={{ color: '#cbd5e1' }}>{xai.evidence_synthesis}</span>
                  </div>
                )}
              </div>

              {/* Contradictory & Missing Data Disclosures */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', fontSize: '11px', marginBottom: '14px' }}>
                <div style={{ background: '#0b1320', padding: '10px', borderRadius: '6px', border: '1px solid #1e293b' }}>
                  <strong style={{ color: '#fbbf24', display: 'block', marginBottom: '4px' }}>Contradictory / Discrepancy Analysis:</strong>
                  <span style={{ color: '#94a3b8' }}>{xai.contradictory_evidence_analysis || 'No conflicting signals identified.'}</span>
                </div>

                <div style={{ background: '#0b1320', padding: '10px', borderRadius: '6px', border: '1px solid #1e293b' }}>
                  <strong style={{ color: '#94a3b8', display: 'block', marginBottom: '4px' }}>Missing Data & Telemetry Gaps:</strong>
                  <span style={{ color: '#64748b' }}>{xai.missing_data_disclosure || 'All primary public feeds streaming normally.'}</span>
                </div>
              </div>

              {/* Recommended Verification Checklist */}
              {xai.recommended_verification_steps && (
                <div style={{ background: '#0b1320', padding: '12px 14px', borderRadius: '6px', border: '1px solid #1e293b' }}>
                  <strong style={{ fontSize: '10px', color: '#5eead4', textTransform: 'uppercase', letterSpacing: '0.6px', display: 'block', marginBottom: '6px' }}>
                    Actionable Verification Protocol for Response Teams:
                  </strong>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '6px' }}>
                    {xai.recommended_verification_steps.map((step: string, i: number) => (
                      <div key={i} style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '11px', color: '#cbd5e1' }}>
                        <ChevronRight size={13} style={{ color: '#5eead4', flexShrink: 0 }} />
                        <span>{step}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* 10 NMC Subregions Grid */}
            <div className="panel" style={{ padding: '18px 20px', marginBottom: '16px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <Building2 size={16} style={{ color: '#38bdf8' }} />
                  <h3 style={{ margin: 0, fontSize: '13px', fontWeight: 700 }}>
                    NAGPUR MUNICIPAL CORPORATION · 10 ADMINISTRATIVE ZONES
                  </h3>
                </div>
                <span style={{ fontSize: '10px', color: '#94a3b8' }}>CLICK ZONE CARD TO DRILL DOWN</span>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(180px, 1fr))', gap: '10px' }}>
                {Object.entries(subregions).map(([zid, z]: [string, any]) => {
                  const zAction = z.action || 'WATCH'
                  const zColor =
                    zAction === 'ESCALATE' ? '#fb7185' : zAction === 'ALERT' ? '#fb7185' : zAction === 'PREPARE' ? '#fbbf24' : '#5eead4'
                  const isSelected = selectedZoneId === zid

                  return (
                    <div
                      key={zid}
                      onClick={() => setSelectedZoneId(zid)}
                      style={{
                        background: isSelected ? '#1e3a5f' : '#0f172a',
                        border: `1px solid ${isSelected ? '#38bdf8' : '#1e293b'}`,
                        borderRadius: '6px',
                        padding: '10px',
                        cursor: 'pointer',
                        transition: 'all 0.2s ease',
                      }}
                    >
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
                        <strong style={{ fontSize: '11px', color: isSelected ? '#38bdf8' : '#f8fafc' }}>{z.name}</strong>
                        <span
                          style={{
                            fontSize: '8px',
                            fontWeight: 700,
                            padding: '1px 5px',
                            borderRadius: '3px',
                            background: `${zColor}20`,
                            color: zColor,
                            border: `1px solid ${zColor}60`,
                          }}
                        >
                          {zAction}
                        </span>
                      </div>
                      <div style={{ fontSize: '10px', color: '#94a3b8', marginBottom: '4px' }}>{z.marathi_name}</div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '9px', color: '#64748b' }}>
                        <span>Active signals: {z.event_count || 0}</span>
                        <span style={{ color: '#38bdf8' }}>View &rarr;</span>
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>

            {/* Main Dual Grid: Bayesian Belief Progression and Response Matrix */}
            <section className="main-grid">
              <div className="panel hypotheses">
                <PanelTitle icon={<BrainCircuit size={17} />} title="Bayesian Hypothesis Monitor" meta="DYNAMIC POSTERIOR (SUM = 1.0)" />
                <p className="section-desc">
                  Tempered Dirichlet-adapted Bayesian updates recalculate as validated external evidence arrives.
                </p>
                {[
                  ['normal', 'H1', 'Normal conditions (Noise)', 'blue'],
                  ['source_failure', 'H2', 'Sensor / Gateway failure', 'purple'],
                  ['isolated_incident', 'H3', 'Isolated localized incident', 'amber'],
                  ['cascading_crisis', 'H4', 'Cascading emergency crisis', 'red'],
                ].map(([key, code, label, tone]) => (
                  <div className="hyp-row" key={key}>
                    <div className="hyp-label">
                      <span className={`hyp-code ${tone}`}>{code}</span>
                      <span>{label}</span>
                    </div>
                    <strong>{pct(probs[key])}</strong>
                    <div className="bar">
                      <span className={tone} style={{ width: pct(probs[key]) }} />
                    </div>
                  </div>
                ))}

                <div className="chart-wrap">
                  <div className="chart-title">
                    BELIEF PROGRESSION <span>cascade vs failure vs isolated</span>
                  </div>
                  {history.length > 1 ? (
                    <ResponsiveContainer width="100%" height={145}>
                      <AreaChart data={history}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#263348" />
                        <XAxis dataKey="tick" stroke="#7f8da3" tickLine={false} />
                        <YAxis domain={[0, 1]} tickFormatter={v => `${Math.round(v * 100)}%`} stroke="#7f8da3" tickLine={false} />
                        <Tooltip contentStyle={{ background: '#111c2c', border: '1px solid #2c3b50', borderRadius: 8 }} formatter={(v: any) => pct(Number(v))} />
                        <Area type="monotone" dataKey="cascade" name="Cascade" stroke="#fb7185" fill="#fb7185" fillOpacity={0.15} />
                        <Area type="monotone" dataKey="isolated" name="Isolated" stroke="#fbbf24" fill="#fbbf24" fillOpacity={0.08} />
                        <Area type="monotone" dataKey="failure" name="Failure" stroke="#a78bfa" fill="#a78bfa" fillOpacity={0.08} />
                      </AreaChart>
                    </ResponsiveContainer>
                  ) : (
                    <div className="empty-chart">Streaming observations to build live belief history timeline.</div>
                  )}
                </div>
              </div>

              {/* Response Cost Matrix & Gating */}
              <div className="panel decision">
                <PanelTitle icon={<ShieldCheck size={17} />} title="Response Cost Evaluation" meta="EXPECTED LOSS OPTIMAL" />
                <p className="section-desc">
                  Expected-cost action selection across four operational levels under asymmetric disaster risk.
                </p>

                <div className={`decision-banner ${actionClass}`}>
                  <div>
                    <small>DECISION ENGINE OUTPUT</small>
                    <h2>{action}</h2>
                  </div>
                  <div className="decision-icon">
                    {action === 'WATCH' ? <ShieldCheck size={32} /> : <AlertTriangle size={32} />}
                  </div>
                </div>

                <div className="costs">
                  <strong style={{ fontSize: '10px', textTransform: 'uppercase', color: '#94a3b8' }}>
                    Expected Loss per Response Strategy:
                  </strong>
                  {['WATCH', 'PREPARE', 'ALERT', 'ESCALATE'].map(actName => {
                    const costVal = state.expected_costs?.[actName] ?? 0.0
                    const maxCost = 20.0
                    const widthPct = Math.min(100, (costVal / maxCost) * 100)
                    const isOptimal = actName === action

                    return (
                      <div className="cost-row" key={actName}>
                        <span style={{ color: isOptimal ? '#5eead4' : '#94a3b8', fontWeight: isOptimal ? 700 : 400 }}>
                          {actName}
                        </span>
                        <div className="cost-track">
                          <i style={{ width: `${widthPct}%`, background: isOptimal ? '#5eead4' : '#334155' }} />
                        </div>
                        <strong>{costVal.toFixed(2)}</strong>
                      </div>
                    )
                  })}
                </div>

                {/* Alert Stability Policy & Gating Disclosure */}
                <div style={{ background: '#09040e', border: '1px solid var(--border-gold)', borderRadius: '6px', padding: '8px 10px', margin: '10px 0', fontSize: '10px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--saffron-400)', fontWeight: 700, marginBottom: '2px' }}>
                    <span>HYSTERESIS & STABILITY POLICY:</span>
                    <span>COOLDOWN: 180s</span>
                  </div>
                  <div style={{ color: 'var(--text-secondary)' }}>
                    {state.gate_reason || 'ESCALATE requires ≥2 independent corroborating sources. Hysteresis enter ≥0.70, exit <0.50.'}
                  </div>
                </div>

                <div className="human-note">
                  <Info size={14} style={{ flexShrink: 0 }} />
                  <span>
                    CrisisPulse Decision Support: Autonomous dispatch is strictly disabled.
                    Final emergency mobilization requires authorized incident commander verification.
                  </span>
                </div>
              </div>
            </section>
          </>
        )}

        {/* ----------------- TAB: NAGPUR GIS HAZARD MAP ----------------- */}
        {activeTab === 'map' && (
          <section className="map-view-grid" style={{ display: 'grid', gridTemplateColumns: selectedZoneId ? '1fr 340px' : '1fr', gap: '16px', height: '76vh' }}>
            <div className="panel" style={{ padding: '8px', height: '100%', position: 'relative' }}>
              <CrisisMap
                events={events}
                center={[location.latitude, location.longitude]}
                zoom={12}
                selectedZoneId={selectedZoneId}
                selectedEventId={selectedEvent?.event_id}
                onSelectZone={zid => setSelectedZoneId(zid)}
                onSelectEvent={evt => setSelectedEvent(evt)}
                onResetView={() => setSelectedZoneId(null)}
                apiBase={API}
              />
            </div>

            {selectedZoneId && (
              <SubregionDetailPanel
                apiBase={API}
                zoneId={selectedZoneId}
                onClose={() => setSelectedZoneId(null)}
              />
            )}
          </section>
        )}

        {/* ----------------- TAB: LIVE INTELLIGENCE FEED ----------------- */}
        {activeTab === 'feed' && (
          <section className="panel" style={{ padding: '20px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px', flexWrap: 'wrap', gap: '10px' }}>
              <div>
                <h3 style={{ margin: 0, fontSize: '15px', fontWeight: 800 }}>LIVE NAGPUR INTELLIGENCE FEED</h3>
                <small style={{ color: '#94a3b8' }}>
                  Validated external signals filtered strictly to Nagpur District & NMC Urban Area
                </small>
              </div>

              {/* Feed Filters */}
              <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                <input
                  type="text"
                  placeholder="Filter by keyword or zone..."
                  value={eventSearch}
                  onChange={e => setEventSearch(e.target.value)}
                  style={{
                    background: '#0f172a', border: '1px solid #334155', color: '#fff',
                    padding: '6px 10px', borderRadius: '6px', fontSize: '11px', minWidth: '170px'
                  }}
                />

                <select
                  value={selectedCategory}
                  onChange={e => setSelectedCategory(e.target.value)}
                  style={{ background: '#0f172a', border: '1px solid #334155', color: '#fff', padding: '6px 10px', borderRadius: '6px', fontSize: '11px' }}
                >
                  <option value="all">All Categories</option>
                  <option value="weather">Weather & Severe Storms</option>
                  <option value="drainage">Drainage & Waterlogging</option>
                  <option value="traffic">Traffic & EMS Transit</option>
                  <option value="health">Hospital Capacity</option>
                  <option value="earthquake">Seismic Shocks</option>
                  <option value="wildfire">Thermal Hotspots</option>
                </select>

                <select
                  value={selectedProvenance}
                  onChange={e => setSelectedProvenance(e.target.value)}
                  style={{ background: '#0f172a', border: '1px solid #334155', color: '#fff', padding: '6px 10px', borderRadius: '6px', fontSize: '11px' }}
                >
                  <option value="all">All Provenance</option>
                  <option value="LIVE">LIVE Observations</option>
                  <option value="FORECAST">Model Forecasts</option>
                  <option value="CACHED">Cached / Reference</option>
                  <option value="SYNTHETIC">Synthetic / Lab</option>
                </select>
              </div>
            </div>

            <div className="table-scroll" style={{ maxHeight: '68vh', overflowY: 'auto' }}>
              <table>
                <thead>
                  <tr>
                    <th>PROVENANCE</th>
                    <th>SOURCE / CATEGORY</th>
                    <th>EVENT SUMMARY</th>
                    <th>MEASUREMENT</th>
                    <th>ZONE / LOCATION</th>
                    <th>PRECISION</th>
                    <th>SEVERITY</th>
                    <th>OBSERVED TIME</th>
                    <th>STATUS</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredEvents.length === 0 ? (
                    <tr>
                      <td colSpan={9} style={{ textAlign: 'center', padding: '30px', color: '#64748b' }}>
                        No events match current filter criteria.
                      </td>
                    </tr>
                  ) : (
                    filteredEvents.map((evt: AnyObj) => {
                      const isRetracted = evt.event_type === 'retraction' || evt.verification_status === 'retracted'
                      const isSuperseded = !!evt.superseded_by
                      const prov = (evt.data_provenance || 'LIVE').toUpperCase()
                      const provColor = isRetracted
                        ? '#ef4444'
                        : prov === 'LIVE'
                        ? '#10b981'
                        : prov === 'FORECAST'
                        ? '#06b6d4'
                        : prov === 'CACHED'
                        ? '#f59e0b'
                        : '#a855f7'

                      return (
                        <tr
                          key={evt.event_id}
                          style={{
                            background: isRetracted ? 'rgba(239, 68, 68, 0.06)' : isSuperseded ? 'rgba(148, 163, 184, 0.04)' : 'transparent',
                            opacity: isSuperseded ? 0.7 : 1,
                          }}
                        >
                          <td>
                            <span
                              style={{
                                fontSize: '8px',
                                fontFamily: 'monospace',
                                fontWeight: 700,
                                padding: '2px 5px',
                                borderRadius: '3px',
                                background: `${provColor}20`,
                                color: provColor,
                                border: `1px solid ${provColor}60`,
                              }}
                            >
                              {isRetracted ? 'RETRACTED' : isSuperseded ? 'SUPERSEDED' : prov}
                            </span>
                          </td>
                          <td>
                            <strong style={{ color: '#f1f5f9' }}>{evt.source_id}</strong>
                            <small style={{ display: 'block', color: '#64748b', fontSize: '9px' }}>
                              {evt.event_type}
                            </small>
                          </td>
                          <td style={{ maxWidth: '280px', whiteSpace: 'normal' }}>
                            <strong
                              style={{
                                color: isRetracted ? '#f87171' : '#e2e8f0',
                                fontSize: '11px',
                                textDecoration: isRetracted || isSuperseded ? 'line-through' : 'none',
                              }}
                            >
                              {evt.title}
                            </strong>
                            <span style={{ display: 'block', color: '#94a3b8', fontSize: '10px' }}>
                              {evt.description}
                            </span>
                            {evt.superseded_by && (
                              <span style={{ display: 'block', color: 'var(--saffron-400)', fontSize: '9px' }}>
                                Superseded by: {evt.superseded_by}
                              </span>
                            )}
                          </td>
                          <td>
                            {evt.magnitude !== null && evt.magnitude !== undefined ? (
                              <strong style={{ color: '#5eead4', fontFamily: 'monospace' }}>
                                {evt.magnitude} {evt.magnitude_unit || ''}
                              </strong>
                            ) : (
                              <span style={{ color: '#64748b' }}>--</span>
                            )}
                          </td>
                          <td>
                            <span style={{ color: '#38bdf8' }}>{evt.assigned_zone_name || evt.zone_id}</span>
                          </td>
                          <td>
                            <span style={{ fontSize: '9px', color: '#94a3b8' }}>
                              {evt.geographic_precision || 'approximate'}
                            </span>
                          </td>
                          <td>
                            <span
                              className={`severity ${
                                evt.severity > 0.7 ? 'high' : evt.severity > 0.4 ? 'med' : 'low'
                              }`}
                            >
                              {Math.round(evt.severity * 100)}%
                            </span>
                          </td>
                          <td style={{ fontSize: '10px', color: '#94a3b8' }}>
                            {new Date(evt.event_timestamp).toLocaleTimeString()}
                          </td>
                          <td>
                            <span
                              style={{
                                fontSize: '9px',
                                textTransform: 'uppercase',
                                color: isRetracted ? '#ef4444' : evt.verification_status === 'verified' ? '#10b981' : '#cbd5e1',
                                fontWeight: evt.verification_status === 'verified' ? 700 : 400,
                              }}
                            >
                              {evt.verification_status || 'preliminary'}
                            </span>
                          </td>
                        </tr>
                      )
                    })
                  )}
                </tbody>
              </table>
            </div>
          </section>
        )}

        {/* ----------------- TAB: NEAR-TERM FORECASTS & CASCADES ----------------- */}
        {activeTab === 'forecasts' && (
          <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 0.8fr', gap: '16px' }}>
            <div className="panel" style={{ padding: '20px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '14px', borderBottom: '1px solid var(--border-gold)', paddingBottom: '10px' }}>
                <Clock size={18} style={{ color: 'var(--saffron-400)' }} />
                <div>
                  <h3 style={{ margin: 0, fontSize: '15px', fontWeight: 800, color: 'var(--text-ivory)' }}>
                    PREDICTIVE MULTI-HORIZON EMERGENCY FORECAST (10, 30, 60 MIN)
                  </h3>
                  <small style={{ color: 'var(--text-secondary)', fontSize: '11px' }}>
                    Three plausible causal projections grounded in real-time telemetry and hydrodynamic lag rules
                  </small>
                </div>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
                {forecasts.map((fc: any, i: number) => (
                  <div
                    key={i}
                    style={{
                      background: 'var(--bg-card)',
                      border: '1px solid var(--border-card)',
                      borderRadius: '8px',
                      padding: '16px',
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px', flexWrap: 'wrap', gap: '6px' }}>
                      <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                        <span
                          style={{
                            background: 'rgba(245, 158, 11, 0.15)',
                            color: 'var(--saffron-400)',
                            fontFamily: 'var(--font-mono)',
                            fontSize: '11px',
                            fontWeight: 800,
                            padding: '3px 8px',
                            borderRadius: '4px',
                            border: '1px solid var(--border-gold)',
                          }}
                        >
                          WINDOW: {fc.horizon}
                        </span>
                        <span style={{ fontSize: '9px', color: '#06b6d4', background: 'rgba(6, 182, 212, 0.12)', padding: '3px 6px', borderRadius: '4px', fontFamily: 'var(--font-mono)' }}>
                          {fc.data_basis || 'OBSERVED_DATA + CAUSAL_RULE'}
                        </span>
                      </div>

                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <span style={{ fontSize: '10px', color: 'var(--text-muted)' }}>
                          CONFIDENCE: <strong style={{ color: '#10b981' }}>{fc.confidence_band || 'HIGH'}</strong>
                        </span>
                        <span style={{ fontSize: '14px', color: 'var(--saffron-400)', fontWeight: 800, fontFamily: 'var(--font-mono)' }}>
                          {Math.round((fc.probability || 0) * 100)}%
                        </span>
                      </div>
                    </div>

                    <strong style={{ fontSize: '13px', color: 'var(--text-ivory)', display: 'block', marginBottom: '4px' }}>
                      {fc.label}
                    </strong>
                    <div style={{ fontSize: '11px', color: '#06b6d4', marginBottom: '8px' }}>
                      Geographic Scope: {fc.geographic_scope}
                    </div>

                    {/* Anticipated Causal Chain Progression */}
                    {fc.causal_chain && fc.causal_chain.length > 0 && (
                      <div style={{ background: 'var(--bg-secondary)', padding: '10px 12px', borderRadius: '6px', marginBottom: '10px', border: '1px solid var(--border-subtle)' }}>
                        <strong style={{ fontSize: '10px', color: 'var(--text-muted)', textTransform: 'uppercase', display: 'block', marginBottom: '6px' }}>
                          Anticipated Causal Propagation Chain:
                        </strong>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                          {fc.causal_chain.map((step: string, sIdx: number) => (
                            <div key={sIdx} style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '11px', color: 'var(--text-primary)' }}>
                              <span style={{ color: 'var(--saffron-400)', fontWeight: 700, fontFamily: 'var(--font-mono)', minWidth: '16px' }}>{sIdx + 1}.</span>
                              <span>{step}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Evidence & Alternative Branch */}
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', fontSize: '11px', marginBottom: '8px' }}>
                      <div style={{ background: 'var(--bg-secondary)', padding: '8px 10px', borderRadius: '6px', border: '1px solid var(--border-subtle)' }}>
                        <strong style={{ color: 'var(--saffron-400)', display: 'block', marginBottom: '2px', fontSize: '10px' }}>Evidence Basis:</strong>
                        <span style={{ color: 'var(--text-secondary)' }}>{(fc.evidence_basis || []).join(' • ') || fc.assumptions}</span>
                      </div>
                      <div style={{ background: 'var(--bg-secondary)', padding: '8px 10px', borderRadius: '6px', border: '1px solid var(--border-subtle)' }}>
                        <strong style={{ color: '#06b6d4', display: 'block', marginBottom: '2px', fontSize: '10px' }}>Uncertainty Alternative:</strong>
                        <span style={{ color: 'var(--text-secondary)' }}>{fc.uncertainty_alternative || 'Localized ponding resolves without arterial breakdown.'}</span>
                      </div>
                    </div>

                    <div style={{ fontSize: '10px', color: 'var(--text-dim)' }}>
                      <em>Known Limitations: {fc.known_limitations || 'Hydrodynamic ponding extrapolation.'}</em>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="panel" style={{ padding: '20px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '14px', borderBottom: '1px solid var(--border-gold)', paddingBottom: '10px' }}>
                <GitMerge size={17} style={{ color: 'var(--fuchsia-400)' }} />
                <h3 style={{ margin: 0, fontSize: '14px', fontWeight: 800, color: 'var(--text-ivory)' }}>
                  CASCADING HAZARD PROPAGATION GRAPH
                </h3>
              </div>
              <CausalGraph graphData={causalGraph} />
            </div>
          </div>
        )}

        {/* ----------------- TAB: SOURCES & INGESTION HEALTH ----------------- */}
        {activeTab === 'sources' && (
          <SourceHealthPanel sources={sources} onPollSource={pollNow} />
        )}

        {/* ----------------- TAB: FIRST-10-MINUTE LAB ----------------- */}
        {activeTab === 'lab' && (
          <IntelligenceLab apiBase={API} />
        )}

        {/* ----------------- TAB: MODEL EVALUATION ----------------- */}
        {activeTab === 'evaluation' && (
          <EvaluationPanel apiBase={API} />
        )}

        {/* Location Selection Modal */}
        {showLocationModal && (
          <LocationModal
            apiBase={API}
            currentLocation={location}
            onUpdateLocation={updateLocation}
            onClose={() => setShowLocationModal(false)}
          />
        )}
      </main>

      {/* Operational Footer */}
      <footer>
        <div>
          CRISISPULSE AI · NAGPUR OPERATIONAL EDITION · LAT {NAGPUR_CENTER_LAT.toFixed(4)}° N, LON {NAGPUR_CENTER_LON.toFixed(4)}° E
        </div>
        <div>
          NON-AUTONOMOUS DECISION SUPPORT · HUMAN COMMANDER VERIFICATION MANDATORY
        </div>
      </footer>
    </div>
  )
}

function PanelTitle({ icon, title, meta }: { icon: React.ReactNode; title: string; meta?: string }) {
  return (
    <div className="panel-title">
      <div className="panel-title-icon">{icon}</div>
      <h3>{title}</h3>
      {meta && <span>{meta}</span>}
    </div>
  )
}

function Metric({
  icon,
  label,
  value,
  sub,
  tone,
}: {
  icon: React.ReactNode
  label: string
  value: string
  sub: string
  tone: string
}) {
  return (
    <div className="panel metric">
      <div className={`metric-icon ${tone}`}>{icon}</div>
      <div className="metric-label">{label}</div>
      <div className="metric-value">{value}</div>
      <div className="metric-sub">{sub}</div>
    </div>
  )
}

const NAGPUR_CENTER_LAT = 21.1458
const NAGPUR_CENTER_LON = 79.0882
