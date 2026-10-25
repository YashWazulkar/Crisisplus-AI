import { useState } from 'react'
import { MapPin, Search, Check } from 'lucide-react'

interface Props {
  apiBase: string
  currentLocation: { latitude: number; longitude: number; name: string }
  onUpdateLocation: (lat: number, lon: number, name: string) => Promise<void>
  onClose: () => void
}

const NAGPUR_PRESETS = [
  { name: 'Nagpur District (District-Wide)', latitude: 21.1458, longitude: 79.0882, desc: 'Central Vidarbha Administrative Area' },
  { name: 'Hanuman Nagar Zone (Narendra Nagar / GMCH)', latitude: 21.1180, longitude: 79.1020, desc: 'South Urban Basin · Chronic Underpass Flooding' },
  { name: 'Dharampeth Zone (Civil Lines / Ambazari)', latitude: 21.1460, longitude: 79.0620, desc: 'West Zone · Ambazari Lake Dam & Nag River Origin' },
  { name: 'Dhantoli Zone (Sitabuldi / Mor Bhavan)', latitude: 21.1380, longitude: 79.0850, desc: 'Central Transit Interchange & Bus Terminus' },
  { name: 'Gandhibagh Zone (Mayo Hospital / Mahal)', latitude: 21.1520, longitude: 79.1050, desc: 'Central-East · Old City Dense Heritage Corridors' },
  { name: 'Lakadganj Zone (Pardi / Bhandara Road NH-53)', latitude: 21.1480, longitude: 79.1360, desc: 'East Corridor · Low-Lying Industrial Freight Highway' },
  { name: 'Mangalwari Zone (Sadar / Mankapur NH-47)', latitude: 21.1760, longitude: 79.0750, desc: 'North-West · Koradi Road & Gaddigodam Underpass' },
  { name: 'Laxmi Nagar Zone (Bajaj Nagar / Khamla)', latitude: 21.1150, longitude: 79.0600, desc: 'South-West · Residential Ring Road Corridor' },
]

export default function LocationModal({ apiBase, currentLocation, onUpdateLocation, onClose }: Props) {
  const [query, setQuery] = useState('')
  const [searching, setSearching] = useState(false)
  const [error, setError] = useState('')

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!query.trim()) return
    setSearching(true)
    setError('')
    try {
      const res = await fetch(`${apiBase}/api/ingestion/geocode?q=${encodeURIComponent(query)}`)
      if (!res.ok) throw new Error('Location not found in Nagpur')
      const data = await res.json()
      await onUpdateLocation(data.latitude, data.longitude, data.label)
      onClose()
    } catch {
      setError(`Could not find Nagpur locality for "${query}". Try an NMC zone or landmark (e.g. Sitabuldi, Ambazari, GMCH).`)
    } finally {
      setSearching(false)
    }
  }

  return (
    <div className="modal-backdrop" style={{
      position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
      background: 'rgba(0,0,0,0.8)', display: 'flex', alignItems: 'center', justifyContent: 'center',
      zIndex: 9999, backdropFilter: 'blur(6px)'
    }}>
      <div className="panel modal-content" style={{ width: '480px', maxWidth: '92vw', padding: '20px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px', borderBottom: '1px solid #1e293b', paddingBottom: '10px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <MapPin size={18} style={{ color: '#38bdf8' }} />
            <h3 style={{ margin: 0, fontSize: '15px', fontWeight: 800 }}>Select Nagpur Operational Sector</h3>
          </div>
          <button className="btn" onClick={onClose} style={{ padding: '2px 8px' }}>&times;</button>
        </div>

        <form onSubmit={handleSearch} style={{ display: 'flex', gap: '8px', marginBottom: '16px' }}>
          <input
            type="text"
            placeholder="Search Nagpur locality (e.g. Sitabuldi, Ambazari, Mankapur, Pardi)..."
            value={query}
            onChange={e => setQuery(e.target.value)}
            style={{
              flex: 1, background: '#0f172a', border: '1px solid #334155', color: '#fff',
              padding: '8px 12px', borderRadius: '6px', fontSize: '12px'
            }}
          />
          <button type="submit" className="btn primary" disabled={searching} style={{ fontSize: '12px' }}>
            <Search size={14} /> {searching ? '...' : 'Search'}
          </button>
        </form>

        {error && (
          <div style={{ fontSize: '11px', color: '#f87171', marginBottom: '12px', background: '#ef444415', border: '1px solid #ef444440', padding: '6px 10px', borderRadius: '4px' }}>
            {error}
          </div>
        )}

        <div style={{ fontSize: '10px', color: '#94a3b8', marginBottom: '8px', textTransform: 'uppercase', letterSpacing: '0.6px', fontWeight: 700 }}>
          Nagpur Municipal Administrative Zones & Corridors
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', maxHeight: '280px', overflowY: 'auto' }}>
          {NAGPUR_PRESETS.map(p => {
            const isSelected = currentLocation.name.includes(p.name.split('(')[0].trim())
            return (
              <button
                key={p.name}
                className="btn"
                onClick={async () => {
                  await onUpdateLocation(p.latitude, p.longitude, p.name)
                  onClose()
                }}
                style={{
                  display: 'flex', flexDirection: 'column', alignItems: 'flex-start',
                  background: isSelected ? '#38bdf820' : '#0f172a',
                  border: `1px solid ${isSelected ? '#38bdf8' : '#1e293b'}`,
                  padding: '8px 12px', textAlign: 'left',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', width: '100%', alignItems: 'center' }}>
                  <strong style={{ fontSize: '12px', color: isSelected ? '#38bdf8' : '#f1f5f9' }}>{p.name}</strong>
                  {isSelected && <Check size={14} style={{ color: '#38bdf8' }} />}
                </div>
                <small style={{ fontSize: '10px', color: '#94a3b8', marginTop: '2px' }}>{p.desc}</small>
              </button>
            )
          })}
        </div>
      </div>
    </div>
  )
}
