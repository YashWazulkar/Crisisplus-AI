import { useEffect, useRef, useState } from 'react'
import L from 'leaflet'

interface EventItem {
  event_id: string
  event_type: string
  title: string
  description?: string
  latitude: number
  longitude: number
  depth_km?: number | null
  magnitude?: number | null
  magnitude_unit?: string | null
  severity: number
  reliability?: number
  verification_status?: string
  data_provenance?: string
  geographic_precision?: string
  assigned_zone_id?: string | null
  assigned_zone_name?: string | null
  source_id: string
  source_url?: string | null
  event_timestamp: string
}

interface MapProps {
  events: EventItem[]
  center: [number, number]
  zoom?: number
  selectedZoneId?: string | null
  selectedEventId?: string | null
  onSelectZone?: (zoneId: string) => void
  onSelectEvent?: (event: EventItem) => void
  onResetView?: () => void
  apiBase?: string
}

const DEFAULT_CENTER: [number, number] = [21.1458, 79.0882]

export default function CrisisMap({
  events,
  center = DEFAULT_CENTER,
  zoom = 12,
  selectedZoneId,
  selectedEventId,
  onSelectZone,
  onSelectEvent,
  onResetView,
  apiBase = 'http://127.0.0.1:8000',
}: MapProps) {
  const mapContainerRef = useRef<HTMLDivElement>(null)
  const mapInstanceRef = useRef<L.Map | null>(null)

  // Layer groups
  const districtLayerRef = useRef<L.GeoJSON | null>(null)
  const urbanLayerRef = useRef<L.GeoJSON | null>(null)
  const zonesLayerRef = useRef<L.GeoJSON | null>(null)
  const hotspotsLayerRef = useRef<L.LayerGroup | null>(null)
  const hospitalsLayerRef = useRef<L.LayerGroup | null>(null)
  const hydrologyLayerRef = useRef<L.LayerGroup | null>(null)
  const eventsLayerRef = useRef<L.LayerGroup | null>(null)

  // Layer Visibility Toggles
  const [layers, setLayers] = useState({
    zones: true,
    hotspots: true,
    hospitals: true,
    hydrology: true,
    events: true,
  })

  const [geoData, setGeoData] = useState<any>(null)

  // Fetch Authoritative Nagpur GeoJSON
  useEffect(() => {
    fetch(`${apiBase}/api/geography/master`)
      .then(res => res.json())
      .then(data => setGeoData(data))
      .catch(() => {})
  }, [apiBase])

  // Initialize Map
  useEffect(() => {
    if (!mapContainerRef.current || mapInstanceRef.current) return

    const map = L.map(mapContainerRef.current, {
      center: DEFAULT_CENTER,
      zoom: 12,
      minZoom: 9,
      maxZoom: 17,
      zoomControl: false,
    })

    L.control.zoom({ position: 'bottomright' }).addTo(map)

    // Dark tactical CartoDB tile layer
    L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
      attribution: '&copy; OpenStreetMap &copy; CARTO &copy; NMC GIS',
      subdomains: 'abcd',
      maxZoom: 19,
    }).addTo(map)

    // Setup Layer Groups
    districtLayerRef.current = L.geoJSON(undefined, {
      style: {
        color: '#64748b',
        weight: 1.5,
        dashArray: '5, 5',
        fillOpacity: 0.02,
        fillColor: '#334155',
      },
    }).addTo(map)

    urbanLayerRef.current = L.geoJSON(undefined, {
      style: {
        color: '#38bdf8',
        weight: 2,
        fillOpacity: 0.04,
        fillColor: '#0284c7',
      },
    }).addTo(map)

    zonesLayerRef.current = L.geoJSON(undefined, {
      style: (feature: any) => {
        const isSelected = selectedZoneId === feature?.id
        return {
          color: isSelected ? '#5eead4' : '#0284c7',
          weight: isSelected ? 2.5 : 1.2,
          fillOpacity: isSelected ? 0.25 : 0.08,
          fillColor: isSelected ? '#0d9488' : '#0369a1',
        }
      },
      onEachFeature: (feature, layer) => {
        const p = feature.properties || {}
        layer.bindTooltip(
          `<div style="font-family: inherit; font-size: 11px;">
            <strong>${p.name}</strong><br/>
            <span style="color: #94a3b8;">${p.marathi_name || ''}</span>
          </div>`,
          { sticky: true, className: 'tactical-tooltip' }
        )
        layer.on('click', () => {
          if (onSelectZone && feature.id !== undefined) {
            onSelectZone(String(feature.id))
          }
        })
      },
    }).addTo(map)

    hotspotsLayerRef.current = L.layerGroup().addTo(map)
    hospitalsLayerRef.current = L.layerGroup().addTo(map)
    hydrologyLayerRef.current = L.layerGroup().addTo(map)
    eventsLayerRef.current = L.layerGroup().addTo(map)

    mapInstanceRef.current = map

    return () => {
      map.remove()
      mapInstanceRef.current = null
    }
  }, [])

  // Populate GeoJSON vector layers once loaded
  useEffect(() => {
    if (!geoData || !mapInstanceRef.current) return

    // 1. District Boundary
    if (districtLayerRef.current && geoData.district_boundary) {
      districtLayerRef.current.clearLayers()
      districtLayerRef.current.addData(geoData.district_boundary)
    }

    // 2. NMC Urban Boundary
    if (urbanLayerRef.current && geoData.urban_boundary) {
      urbanLayerRef.current.clearLayers()
      urbanLayerRef.current.addData(geoData.urban_boundary)
    }

    // 3. 10 Administrative Zones
    if (zonesLayerRef.current && geoData.zones) {
      zonesLayerRef.current.clearLayers()
      zonesLayerRef.current.addData(geoData.zones)
    }

    // 4. Hydrology Rivers (Nag, Pili, Pora)
    if (hydrologyLayerRef.current && geoData.hydrology) {
      hydrologyLayerRef.current.clearLayers()
      L.geoJSON(geoData.hydrology, {
        style: {
          color: '#38bdf8',
          weight: 3,
          opacity: 0.7,
        },
        onEachFeature: (feature, layer) => {
          layer.bindTooltip(`<strong>${feature.properties?.name || 'Watercourse'}</strong>`, {
            className: 'tactical-tooltip',
          })
        },
      }).addTo(hydrologyLayerRef.current)
    }

    // 5. Chronic Waterlogging Hotspots
    if (hotspotsLayerRef.current && geoData.hotspots) {
      hotspotsLayerRef.current.clearLayers()
      const features = geoData.hotspots.features || []
      features.forEach((h: any) => {
        const [lon, lat] = h.geometry.coordinates
        const p = h.properties || {}

        const hotspotIcon = L.divIcon({
          className: 'custom-hotspot-marker',
          html: `
            <div style="
              width: 14px; height: 14px; border-radius: 50%;
              background: #f43f5e; border: 2px solid #ffffff;
              box-shadow: 0 0 10px #f43f5e; display: flex; align-items: center; justify-content: center;
              font-size: 8px; color: #fff; cursor: pointer;
            " title="${p.name}">
              !
            </div>
          `,
          iconSize: [14, 14],
          iconAnchor: [7, 7],
        })

        const marker = L.marker([lat, lon], { icon: hotspotIcon })
        marker.bindPopup(`
          <div style="font-family: inherit; font-size: 11px; color: #f8fafc; padding: 4px; min-width: 220px;">
            <div style="font-size: 9px; font-weight: 700; color: #f43f5e; text-transform: uppercase;">
              Chronic Waterlogging Hotspot
            </div>
            <strong style="font-size: 13px; color: #fff; display: block; margin: 3px 0 6px;">
              ${p.name}
            </strong>
            <div style="font-size: 11px; color: #94a3b8; margin-bottom: 6px;">
              ${p.impact || ''}
            </div>
            <div style="background: #1e293b; padding: 5px 8px; border-radius: 4px; font-size: 10px;">
              Submersion Threshold: <strong style="color: #fbbf24;">${p.threshold_mm_h || 25} mm/h</strong><br/>
              Drainage Basin: <strong>${p.drainage_basin || 'Municipal Network'}</strong>
            </div>
          </div>
        `, { className: 'dark-leaflet-popup' })

        hotspotsLayerRef.current?.addLayer(marker)
      })
    }

    // 6. Emergency Hospitals
    if (hospitalsLayerRef.current && geoData.hospitals) {
      hospitalsLayerRef.current.clearLayers()
      const hospFeatures = geoData.hospitals.features || []
      hospFeatures.forEach((h: any) => {
        const [lon, lat] = h.geometry.coordinates
        const p = h.properties || {}

        const hospIcon = L.divIcon({
          className: 'custom-hospital-marker',
          html: `
            <div style="
              width: 16px; height: 16px; border-radius: 4px;
              background: #0ea5e9; border: 1.5px solid #ffffff;
              box-shadow: 0 0 8px #0ea5e980; display: flex; align-items: center; justify-content: center;
              font-size: 9px; font-weight: 800; color: #fff; cursor: pointer;
            ">
              +
            </div>
          `,
          iconSize: [16, 16],
          iconAnchor: [8, 8],
        })

        const marker = L.marker([lat, lon], { icon: hospIcon })
        marker.bindPopup(`
          <div style="font-family: inherit; font-size: 11px; color: #f8fafc; padding: 4px; min-width: 220px;">
            <div style="font-size: 9px; font-weight: 700; color: #38bdf8; text-transform: uppercase;">
              Emergency Healthcare Hub
            </div>
            <strong style="font-size: 13px; color: #fff; display: block; margin: 3px 0 6px;">
              ${p.name}
            </strong>
            <div style="background: #1e293b; padding: 6px 8px; border-radius: 4px; font-size: 10px; display: grid; grid-template-columns: 1fr 1fr; gap: 4px;">
              <span>Total Beds: <strong>${p.total_beds || 'N/A'}</strong></span>
              <span>ER Beds: <strong style="color: #38bdf8;">${p.emergency_beds || 'N/A'}</strong></span>
              <span>Trauma Unit: <strong>${p.trauma_center ? 'Yes' : 'No'}</strong></span>
              <span>Bays: <strong>${p.ambulance_bays || 'N/A'}</strong></span>
            </div>
          </div>
        `, { className: 'dark-leaflet-popup' })

        hospitalsLayerRef.current?.addLayer(marker)
      })
    }
  }, [geoData, onSelectZone])

  // Update Zone Polygon Styling when selectedZoneId changes
  useEffect(() => {
    if (!zonesLayerRef.current) return
    zonesLayerRef.current.setStyle((feature: any) => {
      const isSelected = selectedZoneId === feature?.id
      return {
        color: isSelected ? '#5eead4' : '#0284c7',
        weight: isSelected ? 2.5 : 1.2,
        fillOpacity: isSelected ? 0.28 : 0.08,
        fillColor: isSelected ? '#0d9488' : '#0369a1',
      }
    })
  }, [selectedZoneId])

  // Update Observation Events Layer
  useEffect(() => {
    if (!eventsLayerRef.current || !mapInstanceRef.current) return
    eventsLayerRef.current.clearLayers()

    if (!layers.events) return

    events.forEach(evt => {
      const lat = evt.latitude
      const lon = evt.longitude
      if (lat === 0 && lon === 0) return
      if (isNaN(lat) || isNaN(lon)) return

      let color = '#38bdf8'
      let symbol = '🌧'
      let radius = 8

      if (evt.event_type === 'earthquake') {
        color = '#ef4444'
        symbol = '⚡'
        radius = Math.max(7, Math.min(22, Math.round((evt.magnitude || 3.0) * 2.8)))
      } else if (evt.event_type === 'wildfire') {
        color = '#f59e0b'
        symbol = '🔥'
        radius = 9
      } else if (['flood', 'cyclone', 'road_flooding', 'drainage_overflow'].includes(evt.event_type)) {
        color = '#ec4899'
        symbol = '🌊'
        radius = 10
      } else if (evt.event_type === 'ambulance_delay') {
        color = '#f97316'
        symbol = '🚑'
        radius = 9
      }

      const isSelected = selectedEventId === evt.event_id

      const customIcon = L.divIcon({
        className: 'custom-event-marker',
        html: `
          <div style="
            background: ${color};
            width: ${radius * 2}px;
            height: ${radius * 2}px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            border: 2px solid ${isSelected ? '#ffffff' : '#0b1220'};
            box-shadow: 0 0 ${isSelected ? '16px' : '8px'} ${color};
            cursor: pointer;
            font-size: ${Math.max(9, radius - 2)}px;
            transform: ${isSelected ? 'scale(1.3)' : 'scale(1)'};
            transition: all 0.2s ease;
          ">
            <span>${radius > 8 ? symbol : ''}</span>
          </div>
        `,
        iconSize: [radius * 2, radius * 2],
        iconAnchor: [radius, radius],
      })

      const marker = L.marker([lat, lon], { icon: customIcon })
      marker.bindPopup(`
        <div style="font-family: inherit; color: #f1f5f9; padding: 4px; min-width: 230px;">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 2px;">
            <span style="font-size: 9px; font-weight: 700; text-transform: uppercase; color: ${color};">
              ${evt.event_type.replace('_', ' ')} · ${evt.source_id}
            </span>
            <span style="font-size: 8px; font-family: monospace; background: #334155; padding: 2px 4px; border-radius: 3px; color: #cbd5e1;">
              ${evt.data_provenance || 'LIVE'}
            </span>
          </div>
          <strong style="font-size: 13px; line-height: 1.3; display: block; margin-bottom: 5px; color: #fff;">
            ${evt.title}
          </strong>
          <div style="font-size: 11px; color: #94a3b8; margin-bottom: 6px;">
            ${evt.description || 'Observed telemetry.'}
          </div>
          <div style="background: #1e293b; padding: 5px 8px; border-radius: 4px; font-size: 10px; display: flex; justify-content: space-between; margin-bottom: 4px;">
            <span>Severity: <strong style="color: ${color};">${Math.round(evt.severity * 100)}%</strong></span>
            ${evt.magnitude !== null && evt.magnitude !== undefined ? `<span>Value: <strong>${evt.magnitude} ${evt.magnitude_unit || ''}</strong></span>` : ''}
          </div>
          <div style="font-size: 9px; color: #64748b; display: flex; justify-content: space-between;">
            <span>Precision: ${evt.geographic_precision || 'approximate'}</span>
            <span>${new Date(evt.event_timestamp).toLocaleTimeString()}</span>
          </div>
        </div>
      `, { className: 'dark-leaflet-popup' })

      marker.on('click', () => {
        if (onSelectEvent) onSelectEvent(evt)
      })

      eventsLayerRef.current?.addLayer(marker)
    })
  }, [events, layers.events, selectedEventId, onSelectEvent])

  // Sync Layer Visibility with toggles
  useEffect(() => {
    if (!mapInstanceRef.current) return
    if (zonesLayerRef.current) {
      if (layers.zones && !mapInstanceRef.current.hasLayer(zonesLayerRef.current)) mapInstanceRef.current.addLayer(zonesLayerRef.current)
      if (!layers.zones && mapInstanceRef.current.hasLayer(zonesLayerRef.current)) mapInstanceRef.current.removeLayer(zonesLayerRef.current)
    }
    if (hotspotsLayerRef.current) {
      if (layers.hotspots && !mapInstanceRef.current.hasLayer(hotspotsLayerRef.current)) mapInstanceRef.current.addLayer(hotspotsLayerRef.current)
      if (!layers.hotspots && mapInstanceRef.current.hasLayer(hotspotsLayerRef.current)) mapInstanceRef.current.removeLayer(hotspotsLayerRef.current)
    }
    if (hospitalsLayerRef.current) {
      if (layers.hospitals && !mapInstanceRef.current.hasLayer(hospitalsLayerRef.current)) mapInstanceRef.current.addLayer(hospitalsLayerRef.current)
      if (!layers.hospitals && mapInstanceRef.current.hasLayer(hospitalsLayerRef.current)) mapInstanceRef.current.removeLayer(hospitalsLayerRef.current)
    }
    if (hydrologyLayerRef.current) {
      if (layers.hydrology && !mapInstanceRef.current.hasLayer(hydrologyLayerRef.current)) mapInstanceRef.current.addLayer(hydrologyLayerRef.current)
      if (!layers.hydrology && mapInstanceRef.current.hasLayer(hydrologyLayerRef.current)) mapInstanceRef.current.removeLayer(hydrologyLayerRef.current)
    }
  }, [layers])

  const resetToNagpur = () => {
    if (mapInstanceRef.current) {
      mapInstanceRef.current.setView(DEFAULT_CENTER, 12, { animate: true })
    }
    if (onResetView) onResetView()
  }

  return (
    <div className="map-wrapper" style={{ width: '100%', height: '100%', position: 'relative' }}>
      <div ref={mapContainerRef} style={{ width: '100%', height: '100%', borderRadius: '12px' }} />

      {/* Layer Controls Bar */}
      <div style={{
        position: 'absolute', top: '12px', right: '12px', zIndex: 1000,
        background: '#0f172ae8', border: '1px solid #334155', borderRadius: '8px',
        padding: '8px 12px', display: 'flex', flexDirection: 'column', gap: '6px',
        backdropFilter: 'blur(8px)', boxShadow: '0 8px 24px rgba(0,0,0,0.5)',
        fontSize: '11px', color: '#e2e8f0', minWidth: '170px'
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid #334155', paddingBottom: '4px', marginBottom: '2px' }}>
          <strong style={{ fontSize: '10px', textTransform: 'uppercase', letterSpacing: '0.6px', color: '#38bdf8' }}>
            GIS Layers
          </strong>
          <button
            onClick={resetToNagpur}
            style={{
              background: '#1e293b', border: '1px solid #475569', color: '#94a3b8',
              fontSize: '9px', padding: '2px 6px', borderRadius: '4px', cursor: 'pointer'
            }}
            title="Reset map view to Nagpur Urban Center"
          >
            Reset View
          </button>
        </div>

        <label style={{ display: 'flex', alignItems: 'center', gap: '6px', cursor: 'pointer' }}>
          <input
            type="checkbox"
            checked={layers.zones}
            onChange={e => setLayers(l => ({ ...l, zones: e.target.checked }))}
          />
          <span style={{ width: '8px', height: '8px', background: '#0284c7', borderRadius: '2px', display: 'inline-block' }} />
          NMC 10 Zones
        </label>

        <label style={{ display: 'flex', alignItems: 'center', gap: '6px', cursor: 'pointer' }}>
          <input
            type="checkbox"
            checked={layers.hotspots}
            onChange={e => setLayers(l => ({ ...l, hotspots: e.target.checked }))}
          />
          <span style={{ width: '8px', height: '8px', background: '#f43f5e', borderRadius: '50%', display: 'inline-block' }} />
          Flood Hotspots
        </label>

        <label style={{ display: 'flex', alignItems: 'center', gap: '6px', cursor: 'pointer' }}>
          <input
            type="checkbox"
            checked={layers.hospitals}
            onChange={e => setLayers(l => ({ ...l, hospitals: e.target.checked }))}
          />
          <span style={{ width: '8px', height: '8px', background: '#0ea5e9', borderRadius: '2px', display: 'inline-block' }} />
          Hospitals (GMCH/Mayo)
        </label>

        <label style={{ display: 'flex', alignItems: 'center', gap: '6px', cursor: 'pointer' }}>
          <input
            type="checkbox"
            checked={layers.hydrology}
            onChange={e => setLayers(l => ({ ...l, hydrology: e.target.checked }))}
          />
          <span style={{ width: '8px', height: '8px', background: '#38bdf8', borderRadius: '2px', display: 'inline-block' }} />
          River Canals (Nag/Pili/Pora)
        </label>

        <label style={{ display: 'flex', alignItems: 'center', gap: '6px', cursor: 'pointer' }}>
          <input
            type="checkbox"
            checked={layers.events}
            onChange={e => setLayers(l => ({ ...l, events: e.target.checked }))}
          />
          <span style={{ width: '8px', height: '8px', background: '#ec4899', borderRadius: '50%', display: 'inline-block' }} />
          Active Observations
        </label>
      </div>

      {/* Map Legend Footer */}
      <div style={{
        position: 'absolute', bottom: '12px', left: '12px', zIndex: 1000,
        background: '#0f172ae8', border: '1px solid #334155', borderRadius: '6px',
        padding: '5px 10px', fontSize: '10px', color: '#94a3b8',
        display: 'flex', gap: '14px', alignItems: 'center', backdropFilter: 'blur(8px)'
      }}>
        <span><strong style={{ color: '#38bdf8' }}>Click Zone Polygon:</strong> Select Subregion Detail</span>
        <span><strong style={{ color: '#f43f5e' }}>Hotspot:</strong> Submersion Risk</span>
        <span><strong style={{ color: '#0ea5e9' }}>Cross:</strong> Emergency Care Hub</span>
      </div>
    </div>
  )
}
