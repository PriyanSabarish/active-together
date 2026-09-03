<template>
  <div class="place-map" :style="{ height }">
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

function pinIcon(warn) {
  return L.divIcon({
    className: 'map-pin' + (warn ? ' warn' : ''),
    html: '<svg width="22" height="30" viewBox="0 0 14 20"><path d="M1 7 C1 3.5 3.7 1 7 1 C10.3 1 13 3.5 13 7 C13 11 7 19 7 19 C7 19 1 11 1 7 Z" fill="currentColor"/><circle cx="7" cy="7" r="2.3" fill="#F1EFE8"/></svg>',
    iconSize: [22, 30],
    iconAnchor: [11, 30],
    popupAnchor: [0, -28]
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
      color: '#3B6D11',
      weight: 2,
      opacity: 0.9,
      dashArray: '6 5',
      fillColor: '#639922',
      fillOpacity: 0.1
    }).addTo(layer)
  }

  for (const p of props.places) {
    if (p.latitude == null || p.longitude == null) continue
    const m = L.marker(toLatLng(p), { icon: pinIcon(p.badge?.type === 'warn'), title: p.name }).addTo(layer)
    m.bindTooltip(p.name, { direction: 'top', offset: [0, -28] })
    m.on('click', () => emit('select', p.id))
    bounds.push(toLatLng(p))
  }

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
  border-radius: 14px;
  overflow: hidden;
  background: var(--paper);
  position: relative;
}

.place-map-canvas { width: 100%; height: 100%; }

.place-map .leaflet-control-attribution {
  font-size: 8px;
  background: rgba(255, 255, 255, 0.7);
}

.map-you span {
  display: block;
  width: 14px;
  height: 14px;
  border-radius: 50%;
  background: #3B6D11;
  border: 3px solid #FFFFFF;
  box-shadow: 0 0 0 2px rgba(59, 109, 17, 0.35);
}

.map-pin { color: #3B6D11; }
.map-pin.warn { color: #854F0B; }
.map-pin svg { filter: drop-shadow(0 1px 1px rgba(0, 0, 0, 0.25)); }
</style>
