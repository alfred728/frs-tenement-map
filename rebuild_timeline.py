#!/usr/bin/env python3
"""Rebuild frs_tenement_timeline_map.html with:
  1. Pre-existing baseline tenements (grey, always visible)
  2. Horizontal timeline bar replacing bottom panel
  3. Ore transport line (Gibraltar → Westgold Higginsville) on event 28+
  4. Lake Johnston mill marker from event 12+
  5. Narrative improvements + summary Event 30
"""

SRC = '/Users/alfredlewis/Documents/Forrestania Resources/frs_tenement_timeline_map.html'

# ── Read existing data lines (dynamic search) ──
with open(SRC) as f:
    lines = f.readlines()

events_line = None
geojson_line = None
for line in lines:
    stripped = line.rstrip()
    if stripped.startswith('const EVENTS ='):
        events_line = stripped
    elif stripped.startswith('const GEOJSON ='):
        geojson_line = stripped
if not events_line or not geojson_line:
    raise RuntimeError("Could not find EVENTS or GEOJSON lines in HTML")

# ── CSS ──
CSS = """\
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:#0a0e17;color:#e0e6ed;overflow:hidden;height:100vh}
#map{position:absolute;top:0;left:0;right:0;bottom:56px;z-index:1}
.leaflet-container{background:#0d1117}

/* Event card overlay */
#event-card{position:absolute;top:16px;right:16px;width:400px;max-height:calc(100vh - 88px);overflow-y:auto;background:rgba(13,17,23,0.95);border:1px solid #30363d;border-radius:12px;padding:20px;z-index:1000;backdrop-filter:blur(12px);box-shadow:0 8px 32px rgba(0,0,0,0.4);transition:border-color 0.3s,box-shadow 0.3s}
#event-card.kula{border-color:#f0883e;box-shadow:0 8px 32px rgba(240,136,62,0.3)}
#event-card .date{font-size:12px;color:#8b949e;text-transform:uppercase;letter-spacing:1.5px;margin-bottom:4px}
#event-card .title{font-size:16px;font-weight:600;color:#f0f6fc;margin-bottom:10px;line-height:1.4}
#event-card .title.kula{color:#f0883e}
#event-card .strategic-impact{font-size:12px;color:#b1bac4;line-height:1.6;margin-bottom:12px;padding:10px;background:rgba(48,54,61,0.4);border-radius:8px;border-left:3px solid var(--phase-color,#58a6ff)}
#event-card .meta{display:grid;grid-template-columns:1fr 1fr;gap:8px;font-size:12px}
#event-card .meta-item{background:rgba(48,54,61,0.6);padding:8px 10px;border-radius:6px}
#event-card .meta-item .label{color:#8b949e;font-size:10px;text-transform:uppercase;letter-spacing:0.5px}
#event-card .meta-item .value{color:#e6edf3;font-weight:500;margin-top:2px}
#event-card .meta-item.wide{grid-column:1/-1}
.phase-badge{display:inline-block;font-size:10px;font-weight:700;padding:2px 10px;border-radius:10px;margin-right:6px;vertical-align:middle;letter-spacing:0.3px}
.kula-badge{display:inline-block;background:#f0883e;color:#0d1117;font-size:9px;font-weight:700;padding:2px 6px;border-radius:8px;margin-left:6px;vertical-align:middle}
.phase-1{background:#8957e5;color:#fff}
.phase-2{background:#238636;color:#fff}
.phase-3{background:#f0883e;color:#0d1117}
.phase-4{background:#1f6feb;color:#fff}
.phase-5{background:#d29922;color:#0d1117}

/* Timeline bar */
#timeline-bar{position:absolute;bottom:0;left:0;right:0;height:56px;background:rgba(13,17,23,0.98);border-top:1px solid #30363d;z-index:1000;display:flex;align-items:center;padding:0 10px;gap:0}
.tl-nav{width:28px;height:28px;display:flex;align-items:center;justify-content:center;border-radius:50%;border:1px solid #30363d;background:transparent;color:#8b949e;font-size:11px;cursor:pointer;flex-shrink:0;transition:all 0.2s;user-select:none}
.tl-nav:hover{color:#e6edf3;border-color:#58a6ff;background:rgba(88,166,255,0.1)}
.tl-track-wrap{flex:1;position:relative;height:56px;overflow:visible;margin:0 10px}
.tl-track{position:absolute;left:0;right:0;top:50%;height:2px;background:#21262d;border-radius:1px;transform:translateY(-50%)}
.tl-node{position:absolute;width:12px;height:12px;border-radius:50%;cursor:pointer;transform:translate(-50%,-50%);top:0;transition:all 0.2s;z-index:2;border:2px solid transparent}
.tl-node:hover{transform:translate(-50%,-50%) scale(1.4);z-index:5}
.tl-node.active{width:16px;height:16px;box-shadow:0 0 12px var(--node-color);z-index:4;border-color:rgba(255,255,255,0.6)}
.tl-node.kula-node{border-color:#f0883e}
.tl-node.filtered-out{opacity:0.15;pointer-events:none}
.tl-date-marker{position:absolute;top:4px;font-size:9px;color:#484f58;transform:translateX(-50%);white-space:nowrap;pointer-events:none;letter-spacing:0.3px}

/* Timeline controls */
.tl-controls{display:flex;align-items:center;gap:6px;flex-shrink:0;margin-left:6px}
#play-btn{width:32px;height:32px;border-radius:50%;border:2px solid #58a6ff;background:transparent;color:#58a6ff;font-size:14px;cursor:pointer;display:flex;align-items:center;justify-content:center;transition:all 0.2s;flex-shrink:0}
#play-btn:hover{background:#58a6ff;color:#0d1117}
#play-btn.playing{border-color:#f85149;color:#f85149}
#play-btn.playing:hover{background:#f85149;color:#0d1117}
#speed-btn{padding:2px 8px;border-radius:4px;border:1px solid #30363d;background:#161b22;color:#8b949e;font-size:10px;cursor:pointer;flex-shrink:0}
#speed-btn:hover{color:#e6edf3;border-color:#58a6ff}

/* Filter pills */
.tl-filters{display:flex;align-items:center;gap:4px;margin-left:6px;flex-shrink:0}
.tl-filter{width:18px;height:18px;border-radius:50%;cursor:pointer;border:2px solid transparent;transition:all 0.15s;opacity:0.4}
.tl-filter.active{opacity:1;border-color:rgba(255,255,255,0.3)}
.tl-filter:hover{opacity:1;transform:scale(1.15)}
.tl-sep{width:1px;height:28px;background:#21262d;flex-shrink:0;margin:0 4px}

/* Phase progress bar */
#phase-bar{position:absolute;top:0;left:0;right:420px;height:4px;z-index:1001;display:flex}
.phase-segment{height:100%;transition:opacity 0.3s}

/* Tooltip */
#tl-tooltip{position:fixed;background:rgba(22,27,34,0.97);color:#e6edf3;border:1px solid #30363d;border-radius:8px;padding:8px 12px;font-size:11px;z-index:2000;pointer-events:none;opacity:0;transition:opacity 0.15s;max-width:280px;box-shadow:0 4px 16px rgba(0,0,0,0.5)}
#tl-tooltip .tt-date{color:#8b949e;font-size:9px;margin-bottom:2px}
#tl-tooltip .tt-title{font-weight:600;line-height:1.3}
#tl-tooltip .tt-phase{display:inline-block;font-size:8px;font-weight:700;padding:1px 6px;border-radius:6px;margin-top:3px}

/* Map legend */
#map-legend{position:absolute;bottom:62px;right:16px;background:rgba(13,17,23,0.92);border:1px solid #30363d;border-radius:8px;padding:8px 12px;font-size:10px;color:#8b949e;z-index:999;display:flex;flex-direction:column;gap:4px}
#map-legend .legend-item{display:flex;align-items:center;gap:8px}
#map-legend .legend-swatch{width:16px;height:10px;border-radius:2px;flex-shrink:0}
#map-legend .legend-dash{width:16px;height:0;border-top:2px dashed #8b949e;flex-shrink:0}

/* Step counter */
#step-counter{position:absolute;bottom:62px;left:16px;background:rgba(13,17,23,0.92);border:1px solid #30363d;border-radius:8px;padding:6px 12px;font-size:11px;color:#8b949e;z-index:999}
#step-counter .step-num{color:#58a6ff;font-weight:600}

/* Leaflet popup */
.leaflet-popup-content-wrapper{background:#161b22;color:#e6edf3;border:1px solid #30363d;border-radius:8px}
.leaflet-popup-tip{background:#161b22}
.leaflet-popup-content{font-size:12px;line-height:1.5}

::-webkit-scrollbar{width:6px}
::-webkit-scrollbar-track{background:transparent}
::-webkit-scrollbar-thumb{background:#30363d;border-radius:3px}
::-webkit-scrollbar-thumb:hover{background:#484f58}

/* Ore transport line */
@keyframes ore-flow {
  from { stroke-dashoffset: 40; }
  to { stroke-dashoffset: 0; }
}
@keyframes ore-glow-pulse {
  0%, 100% { opacity: 0.4; }
  50% { opacity: 0.8; }
}
.ore-transport-line {
  stroke: #d29922;
  animation: ore-flow 1.5s linear infinite;
}
.ore-transport-glow {
  stroke: #d29922;
  filter: blur(4px);
  animation: ore-glow-pulse 2s ease-in-out infinite;
}
.ore-transport-label {
  background: rgba(13,17,23,0.9);
  border: 1px solid #d29922;
  color: #d29922;
  padding: 2px 8px;
  border-radius: 6px;
  font-size: 10px;
  font-weight: 600;
  white-space: nowrap;
  letter-spacing: 0.3px;
  box-shadow: 0 0 8px rgba(210,153,34,0.3);
}

/* Mill marker */
.mill-marker-icon {
  width: 28px;
  height: 28px;
  border-radius: 6px;
  border: 2px solid #1f6feb;
  background: rgba(31,111,235,0.25);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  line-height: 1;
  box-shadow: 0 0 10px rgba(31,111,235,0.4);
  cursor: pointer;
}

/* Summary card */
.summary-header {
  font-size: 14px;
  font-weight: 700;
  color: #d29922;
  text-align: center;
  margin-bottom: 12px;
  letter-spacing: 0.5px;
  text-transform: uppercase;
}
.summary-stats {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
  margin-bottom: 14px;
}
.summary-stat {
  background: rgba(48,54,61,0.6);
  padding: 12px 10px;
  border-radius: 8px;
  text-align: center;
  border: 1px solid #30363d;
}
.summary-stat .stat-value {
  font-size: 22px;
  font-weight: 700;
  color: #f0f6fc;
  line-height: 1.2;
}
.summary-stat .stat-label {
  font-size: 10px;
  color: #8b949e;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-top: 4px;
}
.summary-closing {
  font-size: 11px;
  color: #b1bac4;
  font-style: italic;
  line-height: 1.6;
  text-align: center;
  padding: 10px;
  background: rgba(48,54,61,0.3);
  border-radius: 8px;
  border-left: 3px solid #d29922;
}

/* Geraghty star marker */
.tl-node.geraghty-star::after {
  content: '\\2605';
  position: absolute;
  top: -14px;
  left: 50%;
  transform: translateX(-50%);
  font-size: 10px;
  color: #f0f6fc;
  pointer-events: none;
  text-shadow: 0 0 4px rgba(137,87,229,0.6);
}"""

# ── HTML Body ──
HTML_BODY = """\
<div id="phase-bar"></div>
<div id="map"></div>
<div id="event-card">
  <div class="date" id="card-date">&ndash;</div>
  <div class="title" id="card-title">Forrestania Resources &mdash; Starting Position</div>
  <div class="strategic-impact" id="card-impact" style="display:none"></div>
  <div class="meta" id="card-meta"></div>
</div>
<div id="timeline-bar">
  <div class="tl-nav tl-prev" title="Previous">&#9664;</div>
  <div class="tl-track-wrap">
    <div class="tl-track" id="tl-track"></div>
  </div>
  <div class="tl-nav tl-next" title="Next">&#9654;</div>
  <div class="tl-sep"></div>
  <div class="tl-controls">
    <button id="play-btn" title="Play / Pause (Space)">&#9654;</button>
    <button id="speed-btn" title="Playback speed">1&times;</button>
  </div>
  <div class="tl-sep"></div>
  <div class="tl-filters" id="tl-filters"></div>
</div>
<div id="map-legend">
  <div class="legend-item"><div class="legend-swatch" style="background:#8b949e;border:1px solid #6e7681;opacity:0.7"></div>Pre-existing tenements</div>
  <div class="legend-item"><div class="legend-swatch" style="background:#238636;border:1px solid #238636"></div>Acquired tenements</div>
  <div class="legend-item"><div class="legend-dash"></div>Approximate location (surrendered)</div>
  <div class="legend-item"><div class="legend-swatch" style="background:rgba(31,111,235,0.25);border:2px solid #1f6feb;border-radius:3px"></div>Processing plant</div>
  <div class="legend-item"><div class="legend-swatch" style="background:#d29922;border:1px solid #d29922;height:3px;border-radius:2px;margin:3.5px 0"></div>Ore transport route</div>
</div>
<div id="step-counter"><span class="step-num" id="step-num">0</span> / <span id="step-total">30</span></div>
<div id="tl-tooltip"></div>"""

# ── JavaScript ──
# Using a regular string; \uXXXX escapes will be interpreted by Python as Unicode chars (fine for output)
JS_CODE = """
const PHASE_COLORS = {1:'#8957e5',2:'#238636',3:'#f0883e',4:'#1f6feb',5:'#d29922'};
const PHASE_NAMES = {1:'Leadership Reset',2:'Acquisition Blitz',3:'Kula Convergence',4:'Infrastructure Play',5:'Production Readiness'};

// ── Styles ──
function baselineStyle(isApprox) {
  return isApprox
    ? {color:'#6e7681',weight:1.2,dashArray:'6 4',fillColor:'#8b949e',fillOpacity:0.15,opacity:0.55}
    : {color:'#6e7681',weight:1.4,fillColor:'#8b949e',fillOpacity:0.22,opacity:0.6};
}
function phaseStyle(phase, isApprox) {
  const c = PHASE_COLORS[phase] || '#58a6ff';
  return isApprox
    ? {color:c,weight:1.8,dashArray:'7 4',fillColor:c,fillOpacity:0.15,opacity:0.7}
    : {color:c,weight:1.8,fillColor:c,fillOpacity:0.25,opacity:0.7};
}
function highlightStyle(phase, isApprox) {
  const c = PHASE_COLORS[phase] || '#58a6ff';
  return isApprox
    ? {color:'#ffffff',weight:2,dashArray:'6 4',fillColor:c,fillOpacity:0.3,opacity:1.0}
    : {color:'#ffffff',weight:2.5,fillColor:c,fillOpacity:0.55,opacity:1.0};
}

// ── Area helper (Shoelace with latitude correction) ──
function polygonAreaKm2(coords) {
  const ring = coords[0];
  if (!ring || ring.length < 3) return 0;
  const latMid = ring.reduce(function(s,c){return s+c[1];},0) / ring.length;
  const kLat = 111.32, kLon = 111.32 * Math.cos(latMid * Math.PI / 180);
  var a = 0;
  for (var i = 0; i < ring.length; i++) {
    var j = (i+1) % ring.length;
    a += ring[i][0]*kLon * ring[j][1]*kLat - ring[j][0]*kLon * ring[i][1]*kLat;
  }
  return Math.abs(a) / 2;
}

// ── Map init ──
const map = L.map('map',{center:[-31.5,120.5],zoom:7,zoomControl:false,attributionControl:false});
L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png',{maxZoom:18,subdomains:'abcd'}).addTo(map);
L.control.zoom({position:'topleft'}).addTo(map);

// ── Load GeoJSON ──
const tenementLayers = {};
L.geoJSON(GEOJSON, {
  style: function(feature) { return {fillOpacity:0,opacity:0,weight:0}; },
  onEachFeature: function(feature, layer) {
    var tid = feature.properties.tenement_id;
    if (tid) tenementLayers[tid] = layer;
    var isApprox = feature.properties.is_approximate;
    var popup = '<b>' + (feature.properties.tenement_display || tid) + '</b>';
    if (isApprox) popup += '<br><i style="color:#8b949e">Approximate location \\u2014 surrendered post-acquisition</i><br>' + (feature.properties.approx_notes || '');
    if (feature.properties.lease_type) popup += '<br>' + feature.properties.lease_type;
    if (feature.properties.project_hints) popup += '<br><i>' + feature.properties.project_hints + '</i>';
    if (feature.properties.resource_oz_au) popup += '<br>Resource: ' + feature.properties.resource_oz_au + ' oz Au';
    layer.bindPopup(popup);
    layer._visible = false;
    layer._phase = 0;
    layer._isApprox = !!isApprox;
    layer._isBaseline = false;
  }
}).addTo(map);

// ── Compute baseline tenement IDs ──
var storyTenementIds = {};
EVENTS.forEach(function(e) {
  (e.tenement_ids || []).forEach(function(id) { storyTenementIds[id] = true; });
});
var baselineIds = Object.keys(tenementLayers).filter(function(id) { return !storyTenementIds[id]; });

// Show baseline tenements with grey style
var baselineAreaKm2 = 0;
baselineIds.forEach(function(tid) {
  var layer = tenementLayers[tid];
  if (layer) {
    layer.setStyle(baselineStyle(layer._isApprox));
    layer._visible = true;
    layer._phase = 0;
    layer._isBaseline = true;
    try {
      var geo = layer.feature.geometry;
      if (geo.type === 'Polygon') baselineAreaKm2 += polygonAreaKm2(geo.coordinates);
      else if (geo.type === 'MultiPolygon') geo.coordinates.forEach(function(c) { baselineAreaKm2 += polygonAreaKm2(c); });
    } catch(ex) {}
  }
});
baselineAreaKm2 = Math.round(baselineAreaKm2);

// ── Ore Transport Line (Gibraltar → Westgold Higginsville) ──
var oreCoords = [[-31.042, 120.967], [-31.740, 121.725]];
var oreTransportGlow = L.polyline(oreCoords, {
  color: '#d29922', weight: 10, opacity: 0.4, className: 'ore-transport-glow'
});
var oreTransportLine = L.polyline(oreCoords, {
  color: '#d29922', weight: 3, opacity: 0.9, dashArray: '12 8', className: 'ore-transport-line'
});
var oreLabelStart = L.marker([-31.042, 120.967], {
  icon: L.divIcon({className: 'ore-transport-label', html: 'Gibraltar Stockpile', iconSize: [110, 20], iconAnchor: [55, -6]}),
  interactive: false
});
var oreLabelEnd = L.marker([-31.740, 121.725], {
  icon: L.divIcon({className: 'ore-transport-label', html: 'Westgold Mill', iconSize: [85, 20], iconAnchor: [42, 28]}),
  interactive: false
});
var oreTransportVisible = false;
function showOreTransport() {
  if (!oreTransportVisible) {
    oreTransportGlow.addTo(map);
    oreTransportLine.addTo(map);
    oreLabelStart.addTo(map);
    oreLabelEnd.addTo(map);
    oreTransportVisible = true;
  }
}
function hideOreTransport() {
  if (oreTransportVisible) {
    map.removeLayer(oreTransportGlow);
    map.removeLayer(oreTransportLine);
    map.removeLayer(oreLabelStart);
    map.removeLayer(oreLabelEnd);
    oreTransportVisible = false;
  }
}

// ── Lake Johnston Mill Marker ──
var millMarker = L.marker([-32.208405, 120.489175], {
  icon: L.divIcon({
    className: 'mill-marker-icon',
    html: '\u2699',
    iconSize: [28, 28],
    iconAnchor: [14, 14]
  }),
  zIndexOffset: 500
});
millMarker.bindPopup(
  '<b>Lake Johnston Processing Plant</b><br>' +
  '1.5 Mtpa comminution & flotation<br>' +
  '<i style="color:#8b949e">Emily Ann, acquired from Horizon Minerals</i>'
);
var millMarkerVisible = false;
function showMillMarker() {
  if (!millMarkerVisible) {
    millMarker.addTo(map);
    millMarkerVisible = true;
  }
}
function hideMillMarker() {
  if (millMarkerVisible) {
    map.removeLayer(millMarker);
    millMarkerVisible = false;
  }
}

// ── State ──
var currentStep = -1, playing = false, playTimer = null;
var playSpeed = 2500;
var speeds = [3500,2500,1500,800];
var speedIdx = 1, highlightTimer = null;
var activeFilters = {1:true,2:true,3:true,4:true,5:true};

function isActive(p) { return activeFilters[p]; }

// ── Phase bar (top thin stripe) ──
var phaseBar = document.getElementById('phase-bar');
var phaseCounts = {};
EVENTS.forEach(function(e) { phaseCounts[e.phase] = (phaseCounts[e.phase]||0)+1; });
[1,2,3,4,5].forEach(function(p) {
  if (phaseCounts[p]) {
    var seg = document.createElement('div');
    seg.className = 'phase-segment';
    seg.style.cssText = 'flex:'+phaseCounts[p]+';background:'+PHASE_COLORS[p]+';opacity:0.3';
    seg.dataset.phase = p;
    phaseBar.appendChild(seg);
  }
});

// ── Timeline bar: build nodes ──
var tlTrack = document.getElementById('tl-track');
var tlNodes = [];
var tooltip = document.getElementById('tl-tooltip');

function computeNodePositions() {
  var wrap = document.querySelector('.tl-track-wrap');
  var wrapWidth = wrap.clientWidth;
  var pad = 16, minGap = 18;
  var usable = wrapWidth - pad * 2;

  var dates = EVENTS.map(function(e) { return new Date(e.date).getTime(); });
  var minD = Math.min.apply(null, dates), maxD = Math.max.apply(null, dates);
  var range = maxD - minD || 1;

  // Proportional positions
  var pos = dates.map(function(d) { return pad + ((d - minD) / range) * usable; });

  // Forward pass: enforce minimum gap
  for (var i = 1; i < pos.length; i++) {
    if (pos[i] - pos[i-1] < minGap) pos[i] = pos[i-1] + minGap;
  }

  // Backward pass: if last node exceeds right bound, compress from right
  var maxPos = wrapWidth - pad;
  if (pos[pos.length - 1] > maxPos) {
    pos[pos.length - 1] = maxPos;
    for (var i = pos.length - 2; i >= 0; i--) {
      if (pos[i] > pos[i + 1] - minGap) pos[i] = pos[i + 1] - minGap;
    }
  }

  // Ensure first node is within bounds
  if (pos[0] < pad) {
    var shift = pad - pos[0];
    for (var k = 0; k < pos.length; k++) pos[k] += shift;
  }

  return pos;
}

function buildTimeline() {
  // Clear existing
  var existing = tlTrack.querySelectorAll('.tl-node');
  for (var e = 0; e < existing.length; e++) existing[e].remove();
  var markers = document.querySelectorAll('.tl-date-marker');
  for (var m = 0; m < markers.length; m++) markers[m].remove();
  tlNodes = [];

  var positions = computeNodePositions();

  EVENTS.forEach(function(evt, i) {
    var node = document.createElement('div');
    node.className = 'tl-node' + (evt.is_kula ? ' kula-node' : '') + (i === 2 ? ' geraghty-star' : '');
    node.style.left = positions[i] + 'px';
    node.style.background = PHASE_COLORS[evt.phase];
    node.style.setProperty('--node-color', PHASE_COLORS[evt.phase]);
    node.dataset.idx = i;
    node.dataset.phase = evt.phase;
    node.addEventListener('click', (function(idx) {
      return function() { if (playing) stopPlay(); goToStep(idx); };
    })(i));
    node.addEventListener('mouseenter', (function(ev, idx) {
      return function(e) { showTooltip(e, ev, idx); };
    })(evt, i));
    node.addEventListener('mouseleave', hideTooltip);
    tlTrack.appendChild(node);
    tlNodes.push(node);
  });

  addDateMarkers(positions);
}

function addDateMarkers(positions) {
  var wrap = document.querySelector('.tl-track-wrap');
  var months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
  var seen = {};
  var markerData = [];

  EVENTS.forEach(function(evt, i) {
    var d = new Date(evt.date);
    var key = d.getFullYear() + '-' + String(d.getMonth()+1);
    if (!seen[key]) {
      seen[key] = true;
      var label = months[d.getMonth()];
      // Show year for first marker, January, or last marker
      if (markerData.length === 0 || d.getMonth() === 0)
        label += " '" + String(d.getFullYear()).slice(2);
      markerData.push({label: label, x: positions[i]});
    }
  });

  // Ensure last event gets a marker
  var lastEvt = EVENTS[EVENTS.length - 1];
  var lastD = new Date(lastEvt.date);
  var lastKey = lastD.getFullYear() + '-' + String(lastD.getMonth()+1);
  if (!seen[lastKey]) {
    markerData.push({label: months[lastD.getMonth()] + " '" + String(lastD.getFullYear()).slice(2), x: positions[positions.length-1]});
  }

  // Render, skipping overlapping (min 45px gap)
  var lastX = -100;
  markerData.forEach(function(md) {
    if (md.x - lastX < 45) return;
    var el = document.createElement('div');
    el.className = 'tl-date-marker';
    el.textContent = md.label;
    el.style.left = md.x + 'px';
    wrap.appendChild(el);
    lastX = md.x;
  });
}

function showTooltip(e, evt, idx) {
  var phaseColor = PHASE_COLORS[evt.phase];
  var darkText = (evt.phase === 3 || evt.phase === 5);
  tooltip.innerHTML = '<div class="tt-date">' + evt.date + '</div>' +
    '<div class="tt-title">' + evt.title + '</div>' +
    '<div class="tt-phase" style="background:' + phaseColor + ';color:' + (darkText ? '#0d1117' : '#fff') + '">' + PHASE_NAMES[evt.phase] + '</div>';
  tooltip.style.opacity = '1';
  var rect = e.target.getBoundingClientRect();
  var ttW = 280;
  var left = rect.left + rect.width/2 - ttW/2;
  left = Math.max(8, Math.min(left, window.innerWidth - ttW - 8));
  tooltip.style.left = left + 'px';
  tooltip.style.top = (rect.top - tooltip.offsetHeight - 10) + 'px';
}

function hideTooltip() { tooltip.style.opacity = '0'; }

// ── Filters ──
var filtersDiv = document.getElementById('tl-filters');
[1,2,3,4,5].forEach(function(p) {
  var btn = document.createElement('div');
  btn.className = 'tl-filter active';
  btn.style.background = PHASE_COLORS[p];
  btn.dataset.phase = p;
  btn.title = PHASE_NAMES[p] + ' (' + (phaseCounts[p]||0) + ')';
  btn.addEventListener('click', function() {
    btn.classList.toggle('active');
    activeFilters[p] = btn.classList.contains('active');
    applyFilters();
  });
  filtersDiv.appendChild(btn);
});

// ── Core: show/hide tenements ──
function showTenements(ids, phase) {
  (ids||[]).forEach(function(tid) {
    var layer = tenementLayers[tid];
    if (layer) { layer.setStyle(phaseStyle(phase, layer._isApprox)); layer._visible = true; layer._phase = phase; }
  });
}

// ── Navigation ──
function goToStep(idx) {
  if (idx < -1 || idx >= EVENTS.length) return;
  if (highlightTimer) { clearTimeout(highlightTimer); highlightTimer = null; }

  if (idx === -1) {
    // Reset to baseline only
    Object.values(tenementLayers).forEach(function(l) {
      if (l._isBaseline) {
        l.setStyle(baselineStyle(l._isApprox));
        l._visible = true;
      } else {
        l.setStyle({fillOpacity:0,opacity:0,weight:0});
        l._visible = false;
        l._phase = 0;
      }
    });
    currentStep = -1;
    hideOreTransport();
    hideMillMarker();
    updateUI();
    var bounds = L.latLngBounds([]);
    baselineIds.forEach(function(tid) { if(tenementLayers[tid]) try{bounds.extend(tenementLayers[tid].getBounds());}catch(ex){} });
    if (bounds.isValid()) map.flyToBounds(bounds.pad(0.1),{duration:1.0});
    return;
  }

  if (idx > currentStep) {
    for (var i = Math.max(0, currentStep+1); i <= idx; i++)
      showTenements(EVENTS[i].tenement_ids, EVENTS[i].phase);
  } else if (idx < currentStep) {
    // Reset non-baseline, replay
    Object.values(tenementLayers).forEach(function(l) {
      if (!l._isBaseline) {
        l.setStyle({fillOpacity:0,opacity:0,weight:0});
        l._visible = false;
        l._phase = 0;
      }
    });
    for (var j = 0; j <= idx; j++)
      showTenements(EVENTS[j].tenement_ids, EVENTS[j].phase);
  }
  currentStep = idx;
  var evt = EVENTS[currentStep];

  // Show/hide mill marker (visible from event 12 onward)
  if (currentStep >= 12) showMillMarker(); else hideMillMarker();

  // Show/hide ore transport line (visible on events 28+ i.e. Westgold OPA and summary)
  if (currentStep >= 28) showOreTransport(); else hideOreTransport();

  // Highlight new tenements
  if (evt.new_ids && evt.new_ids.length > 0) {
    Object.values(tenementLayers).forEach(function(l) {
      if (l._visible && !l._isBaseline) l.setStyle(phaseStyle(l._phase, l._isApprox));
    });
    evt.new_ids.forEach(function(tid) {
      var layer = tenementLayers[tid];
      if (layer) layer.setStyle(highlightStyle(evt.phase, layer._isApprox));
    });
    highlightTimer = setTimeout(function() {
      evt.new_ids.forEach(function(tid) {
        var layer = tenementLayers[tid];
        if (layer && layer._visible) layer.setStyle(phaseStyle(layer._phase, layer._isApprox));
      });
    }, 2200);

    // Fly to new tenements
    var confirmedNew = evt.new_ids.filter(function(id) { return tenementLayers[id] && !tenementLayers[id]._isApprox; });
    var flyIds = confirmedNew.length > 0 ? confirmedNew : evt.new_ids;
    var bounds2 = L.latLngBounds([]);
    flyIds.forEach(function(tid) { if(tenementLayers[tid]) bounds2.extend(tenementLayers[tid].getBounds()); });
    if (bounds2.isValid()) {
      var latSpan = bounds2.getNorth()-bounds2.getSouth(), lonSpan = bounds2.getEast()-bounds2.getWest();
      if (latSpan > 3 || lonSpan > 3) map.flyTo(bounds2.getCenter(), 7, {duration:1.2});
      else map.flyToBounds(bounds2.pad(0.4), {duration:1.2, maxZoom:11});
    }
  } else {
    // No new tenements: zoom to special features if they just appeared
    if (currentStep === 12 && millMarkerVisible) {
      map.flyTo([-32.208, 120.489], 9, {duration: 1.0});
    } else if (currentStep === 28 && oreTransportVisible) {
      map.flyToBounds(oreTransportLine.getBounds().pad(0.4), {duration: 1.2, maxZoom: 10});
    }
  }
  updateUI();
}

function updateUI() {
  var card = document.getElementById('event-card');
  var titleEl = document.getElementById('card-title');
  var dateEl = document.getElementById('card-date');
  var impactEl = document.getElementById('card-impact');
  var meta = document.getElementById('card-meta');

  if (currentStep === -1) {
    card.classList.remove('kula');
    card.style.borderColor = '#484f58';
    dateEl.innerHTML = '<span style="color:#484f58;font-weight:600">PRE-ACQUISITION BASELINE</span>';
    titleEl.textContent = 'Forrestania Resources \\u2014 Starting Position';
    titleEl.className = 'title';
    impactEl.style.display = 'block';
    impactEl.style.setProperty('--phase-color', '#484f58');
    impactEl.textContent = baselineIds.length + ' tenements held prior to the strategic acquisition campaign beginning September 2024. Click any dot on the timeline below, or press play to watch the story unfold.';
    var bm = '';
    bm += '<div class="meta-item"><div class="label">Baseline Tenements</div><div class="value">' + baselineIds.length + '</div></div>';
    bm += '<div class="meta-item"><div class="label">Baseline Area</div><div class="value">' + baselineAreaKm2.toLocaleString() + ' km\\u00B2</div></div>';
    meta.innerHTML = bm;
    tlNodes.forEach(function(n) { n.classList.remove('active'); });
    document.getElementById('step-num').textContent = '0';
    document.querySelectorAll('.phase-segment').forEach(function(s) { s.style.opacity = '0.3'; });
    return;
  }

  var evt = EVENTS[currentStep];
  var phaseColor = PHASE_COLORS[evt.phase] || '#58a6ff';
  card.classList.toggle('kula', evt.is_kula);
  card.style.borderColor = evt.is_kula ? '#f0883e' : phaseColor;

  dateEl.innerHTML = '<span class="phase-badge phase-' + evt.phase + '">' + PHASE_NAMES[evt.phase] + '</span> ' + evt.date + (evt.is_kula ? '<span class="kula-badge">KULA</span>' : '');

  titleEl.textContent = evt.title;
  titleEl.className = 'title' + (evt.is_kula ? ' kula' : '');

  if (evt.strategic_impact) {
    impactEl.style.display = 'block';
    impactEl.style.setProperty('--phase-color', phaseColor);
    impactEl.textContent = evt.strategic_impact;
  } else { impactEl.style.display = 'none'; }

  // Count tenements
  var cNew = (evt.new_ids||[]).filter(function(id) { return !tenementLayers[id] || !tenementLayers[id]._isApprox; });
  var aNew = (evt.new_ids||[]).filter(function(id) { return tenementLayers[id] && tenementLayers[id]._isApprox; });
  var acqVisible = 0, approxVis = 0;
  Object.values(tenementLayers).forEach(function(l) {
    if (l._visible && !l._isBaseline) {
      if (l._isApprox) approxVis++; else acqVisible++;
    }
  });
  var acquired = acqVisible + approxVis;

  var mh = '';
  var total = acquired + baselineIds.length;
  var tenLabel = '' + total + ' total';
  if ((evt.new_ids||[]).length > 0) tenLabel += ' <span style="color:#238636">(+' + cNew.length + (aNew.length > 0 ? ' +' + aNew.length + '~' : '') + ' new)</span>';
  tenLabel += '<br><span style="font-size:10px;color:#8b949e">' + acquired + ' acquired \\u00B7 ' + baselineIds.length + ' pre-existing</span>';
  mh += '<div class="meta-item wide"><div class="label">Tenements</div><div class="value">' + tenLabel + '</div></div>';
  mh += '<div class="meta-item"><div class="label">Total Area</div><div class="value">' + (evt.cum_area_km2 + baselineAreaKm2).toLocaleString() + ' km\\u00B2</div></div>';
  if (evt.project) mh += '<div class="meta-item"><div class="label">Project</div><div class="value">' + evt.project + '</div></div>';
  if (evt.counterparties) mh += '<div class="meta-item"><div class="label">Counterparty</div><div class="value">' + evt.counterparties + '</div></div>';
  if (evt.consideration) mh += '<div class="meta-item wide"><div class="label">Consideration</div><div class="value">' + evt.consideration + '</div></div>';
  if (evt.tenements_added_story > 0 && (evt.new_ids||[]).length === 0) {
    mh += '<div class="meta-item wide"><div class="label">Note</div><div class="value" style="color:#8b949e;font-size:10px">' + evt.tenements_added_story + ' tenements per story (infrastructure \\u2014 no polygon data)</div></div>';
  }
  if (aNew.length > 0) {
    mh += '<div class="meta-item wide"><div class="label" style="color:#d29922">~ Approximate</div><div class="value" style="color:#8b949e;font-size:10px">' + aNew.length + ' tenement(s) shown at estimated location (surrendered post-acquisition)</div></div>';
  }
  if (evt.confidence) {
    var cc = evt.confidence.indexOf('high') === 0 ? '#238636' : evt.confidence.indexOf('medium') === 0 ? '#d29922' : '#8b949e';
    mh += '<div class="meta-item"><div class="label">Confidence</div><div class="value" style="color:' + cc + '">' + evt.confidence + '</div></div>';
  }
  meta.innerHTML = mh;

  // Update timeline bar
  tlNodes.forEach(function(n,i) { n.classList.toggle('active', i === currentStep); });
  document.getElementById('step-num').textContent = String(currentStep + 1);

  // Phase bar
  document.querySelectorAll('.phase-segment').forEach(function(seg) {
    seg.style.opacity = parseInt(seg.dataset.phase) <= evt.phase ? '1' : '0.3';
  });
}

// ── Playback ──
function stopPlay() {
  playing = false;
  var btn = document.getElementById('play-btn');
  btn.innerHTML = '\\u25B6';
  btn.classList.remove('playing');
  if (playTimer) { clearTimeout(playTimer); playTimer = null; }
}

function togglePlay() {
  if (playing) { stopPlay(); return; }
  playing = true;
  var btn = document.getElementById('play-btn');
  btn.innerHTML = '\\u23F8';
  btn.classList.add('playing');
  advancePlay();
}

function advancePlay() {
  if (!playing) return;
  var next = currentStep + 1;
  while (next < EVENTS.length && !activeFilters[EVENTS[next].phase]) next++;
  if (next >= EVENTS.length) { stopPlay(); return; }
  goToStep(next);
  playTimer = setTimeout(advancePlay, playSpeed);
}

function applyFilters() {
  tlNodes.forEach(function(node, i) {
    node.classList.toggle('filtered-out', !activeFilters[EVENTS[i].phase]);
  });
}

// ── Event handlers ──
document.getElementById('play-btn').addEventListener('click', togglePlay);
document.getElementById('speed-btn').addEventListener('click', function() {
  speedIdx = (speedIdx+1) % speeds.length;
  playSpeed = speeds[speedIdx];
  document.getElementById('speed-btn').textContent = ['0.5\\u00D7','1\\u00D7','2\\u00D7','4\\u00D7'][speedIdx];
});

document.querySelector('.tl-prev').addEventListener('click', function() {
  if (playing) stopPlay();
  var prev = currentStep - 1;
  while (prev >= 0 && !activeFilters[EVENTS[prev].phase]) prev--;
  if (prev >= -1) goToStep(prev);
});

document.querySelector('.tl-next').addEventListener('click', function() {
  if (playing) stopPlay();
  var next = currentStep + 1;
  while (next < EVENTS.length && !activeFilters[EVENTS[next].phase]) next++;
  if (next < EVENTS.length) goToStep(next);
});

document.addEventListener('keydown', function(e) {
  if (e.target.tagName === 'INPUT') return;
  if (e.code === 'Space') { e.preventDefault(); togglePlay(); }
  else if (e.code === 'ArrowRight') {
    e.preventDefault(); if (playing) stopPlay();
    var next = currentStep+1;
    while(next<EVENTS.length && !activeFilters[EVENTS[next].phase]) next++;
    if(next<EVENTS.length) goToStep(next);
  } else if (e.code === 'ArrowLeft') {
    e.preventDefault(); if (playing) stopPlay();
    var prev = currentStep-1;
    while(prev>=0 && !activeFilters[EVENTS[prev].phase]) prev--;
    if(prev>=-1) goToStep(prev);
  } else if (e.code === 'Home') { e.preventDefault(); goToStep(-1); }
  else if (e.code === 'End') { e.preventDefault(); goToStep(EVENTS.length-1); }
});

// ── Responsive resize ──
var resizeTimer;
window.addEventListener('resize', function() {
  clearTimeout(resizeTimer);
  resizeTimer = setTimeout(function() {
    var positions = computeNodePositions();
    tlNodes.forEach(function(node, i) { node.style.left = positions[i] + 'px'; });
    var oldMarkers = document.querySelectorAll('.tl-date-marker');
    for (var m = 0; m < oldMarkers.length; m++) oldMarkers[m].remove();
    addDateMarkers(positions);
  }, 150);
});

// ── Init ──
document.getElementById('step-total').textContent = EVENTS.length;
buildTimeline();

// Set initial map bounds to baseline tenements only
var baseBounds = L.latLngBounds([]);
baselineIds.forEach(function(tid) {
  if (tenementLayers[tid]) try { baseBounds.extend(tenementLayers[tid].getBounds()); } catch(ex) {}
});
if (baseBounds.isValid()) map.fitBounds(baseBounds.pad(0.15));

// Show baseline card
updateUI();
"""

# ── Assemble output ──
head = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Forrestania Resources \u2013 Strategic Story Timeline</title>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<style>
"""

mid = """
</style>
</head>
<body>
"""

script_open = "\n<script>\n"
script_close = "\n</script>\n</body>\n</html>\n"

output = head + CSS + mid + HTML_BODY + script_open + events_line + "\n" + geojson_line + "\n" + JS_CODE + script_close

with open(SRC, 'w') as f:
    f.write(output)

print(f"Written {len(output):,} chars to {SRC}")
print(f"Baseline IDs = all GeoJSON tenements not in EVENTS (computed at runtime)")
print("Done!")
