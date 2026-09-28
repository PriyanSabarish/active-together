<template>
  <!-- Leaflet map; optional numbered pins and a "You are here" chip for the Play list. -->
  <div class="place-map" :style="{ height }">
    <span v-if="youChip && center" class="you-chip">● You are here</span>
    <div ref="el" class="place-map-canvas" />
  </div>
</template>

<script setup>
// Leaflet + OpenStreetMap tiles. No API key needed.
//
// props.center   { latitude, longitude }   map centre / "you" marker
// props.radiusKm number | null             dashed search-radius circle
// props.places   [{ id, name, latitude, longitude, badge? }]
//                markers for candidate places; emits 'select' with the id
// props.fit      true → zoom to fit centre + places instead of a fixed zoom
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'

const props = defineProps({
  numbered: { type: Boolean, default: false },
  youChip: { type: Boolean, default: false },
  center: { type: Object, default: null },
  radiusKm: { type: Number, default: null },
  places: { type: Array, default: () => [] },
  fit: { type: Boolean, default: false },
  height: { type: String, default: '172px' },
  showYou: { type: Boolean, default: true }
})
const emit = defineEmits(['select'])

// Melbourne CBD, used before a location is chosen.
const FALLBACK = { latitude: -37.8136, longitude: 144.9631 }
const ZOOM_FOR_RADIUS = { 3: 12, 5: 11, 10: 10 }

const el = ref(null)
let map = null
let layer = null

const YOU_ICON = L.divIcon({
  className: 'map-you',
  html: '<span></span>',
  iconSize: [14, 14],
  iconAnchor: [7, 7]
})

// Pins carry their rank (1, 2, 3) so the map and the list read the same.
function pinIcon(warn, n) {
  const label = n ? `<text x="7" y="9.3" text-anchor="middle" font-size="6.5" font-weight="700" font-family="Bricolage Grotesque, system-ui" fill="#F2F1EC">${n}</text>` : '<circle cx="7" cy="7" r="2.3" fill="#F2F1EC"/>'
  return L.divIcon({
    className: 'map-pin' + (warn ? ' warn' : ''),
    html: `<svg width="26" height="36" viewBox="0 0 14 20"><path d="M1 7 C1 3.5 3.7 1 7 1 C10.3 1 13 3.5 13 7 C13 11 7 19 7 19 C7 19 1 11 1 7 Z" fill="currentColor"/>${label}</svg>`,
    iconSize: [26, 36],
    iconAnchor: [13, 36],
    popupAnchor: [0, -32]
  })
}

function toLatLng(p) {
  return [p.latitude, p.longitude]
}

function draw() {
  if (!map) return
  if (layer) layer.remove()
  layer = L.layerGroup().addTo(map)

  const centre = props.center ?? FALLBACK
  const bounds = []

  if (props.center && props.showYou) {
    L.marker(toLatLng(centre), { icon: YOU_ICON, interactive: false, keyboard: false }).addTo(layer)
    bounds.push(toLatLng(centre))
  }

  if (props.center && props.radiusKm) {
    L.circle(toLatLng(centre), {
      radius: props.radiusKm * 1000,
      color: '#2F6B36',
      weight: 2,
      opacity: 0.9,
      dashArray: '6 5',
      fillColor: '#4E8F52',
      fillOpacity: 0.1
    }).addTo(layer)
  }

  props.places.forEach((p, i) => {
    if (p.latitude == null || p.longitude == null) return
    const m = L.marker(toLatLng(p), { icon: pinIcon(p.badge?.type === 'warn', props.numbered ? i + 1 : 0), title: p.name }).addTo(layer)
    m.bindTooltip(p.name, { direction: 'top', offset: [0, -28] })
    m.on('click', () => emit('select', p.id))
    bounds.push(toLatLng(p))
  })

  if (props.fit && bounds.length > 1) {
    map.fitBounds(bounds, { padding: [28, 28], maxZoom: 16 })
  } else if (props.center && props.radiusKm) {
    map.setView(toLatLng(centre), ZOOM_FOR_RADIUS[props.radiusKm] ?? 12)
  } else {
    map.setView(toLatLng(centre), props.center ? 14 : 11)
  }
}

onMounted(() => {
  try {
    map = L.map(el.value, {
      zoomControl: false,
      attributionControl: true,
      scrollWheelZoom: false,
      dragging: true
    })
    L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 19,
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
    }).addTo(map)
    draw()
    // The map is inside a transitioning screen; recalculate once it settles.
    setTimeout(() => map && map.invalidateSize(), 250)
  } catch {
    map = null // e.g. jsdom in unit tests
  }
})

watch(() => [props.center, props.radiusKm, props.places, props.fit], draw, { deep: true })

onBeforeUnmount(() => {
  if (map) map.remove()
  map = null
})
</script>

<style>
.place-map {
  border-radius: var(--radius-card);
  overflow: hidden;
  background: var(--tint);
  box-shadow: var(--shadow-card);
  position: relative;
}

.place-map-canvas { width: 100%; height: 100%; }

.place-map .leaflet-control-attribution {
  font-size: 8px;
  font-family: var(--font-body);
  background: rgba(242, 241, 236, 0.75);
  color: var(--ink-4);
}

.place-map .leaflet-control-attribution a { color: var(--green); }

.map-you span {
  display: block;
  width: 14px;
  height: 14px;
  border-radius: 50%;
  background: var(--green);
  border: 3px solid var(--card);
  box-shadow: 0 0 0 2px rgba(47, 107, 54, 0.35);
}

.you-chip {
  position: absolute;
  left: 10px;
  bottom: 10px;
  z-index: 500;
  padding: 5px 10px;
  border-radius: 999px;
  background: var(--card);
  color: var(--ink);
  font-family: var(--font-display);
  font-size: 12px;
  font-weight: 600;
  box-shadow: var(--shadow-card);
}

.map-pin { color: var(--green); }
.map-pin.warn { color: var(--amber); }
.map-pin svg { filter: drop-shadow(0 3px 4px rgba(30, 42, 31, 0.28)); }
</style>
