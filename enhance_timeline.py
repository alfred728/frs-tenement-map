#!/usr/bin/env python3
"""
enhance_timeline.py
Adds three enhancements to frs_tenement_timeline_map.html:
1. Glowing ore transport line (Gibraltar → Westgold Higginsville) on event 28
2. Lake Johnston mill marker from event 12 onward
3. Narrative improvements + summary Event 30
"""

import json, re, os

HTML_PATH = os.path.join(os.path.dirname(__file__), "frs_tenement_timeline_map.html")

with open(HTML_PATH, "r", encoding="utf-8") as f:
    html = f.read()

# ────────────────────────────────────────────────────────────────
# 1. PARSE AND MODIFY EVENTS JSON
# ────────────────────────────────────────────────────────────────

# Find EVENTS line
m = re.search(r"const EVENTS = (\[.*?\]);\s*$", html, re.MULTILINE)
if not m:
    raise RuntimeError("Could not find EVENTS array in HTML")
events_str = m.group(1)
events = json.loads(events_str)
print(f"Parsed {len(events)} events")

# ── Narrative overrides ──

# Event 11 (idx=11): Bid Implementation Deed — strengthen
events[11]["strategic_impact"] = (
    "Formal legal commitment to an off-market takeover bid for all KGD shares. "
    "If successful, FRS absorbs Kula\u2019s Mt Palmer (M77/406) \u2014 a historic high-grade "
    "underground gold mine \u2014 plus Johnson Range (M77/1263) and the Westonia exploration "
    "licences adjacent to Ramelius\u2019 Edna May Gold Mine. These assets complete a "
    "hub-and-spoke network stretching from Coolgardie to Southern Cross, with multiple "
    "mining leases already approved and ready for scheduling into a centralised "
    "processing pathway."
)

# Event 16 (idx=16): Takeover bid launched — strengthen
events[16]["strategic_impact"] = (
    "Bidder\u2019s Statement dispatched to KGD shareholders. The Kula tenement portfolio "
    "is the missing piece that connects the Coolgardie\u2013Southern Cross corridor: "
    "Mt Palmer feeds high-grade underground ore, Johnson Range adds oxide targets, "
    "and the Westonia ELs provide near-mill exploration upside around Edna May. "
    "Completing this acquisition transforms FRS from a scattered explorer into a "
    "mine-to-mill operator with a clear production pathway through Lake Johnston."
)

# Event 27 (idx=27): Mt Dimer completion — strengthen
events[27]["strategic_impact"] = (
    "Goldzone deal formally completes. Mt Dimer, Mt Jackson and Johnson Range are now "
    "fully within FRS tenure, forming the eastern feeder network for the Lake Johnston "
    "processing plant. Mt Dimer hosts historic gold workings with shallow oxide targets "
    "suitable for open-pit mining \u2014 the lowest-cost feed source for a start-up "
    "operation. Combined with the western feeder projects (British Hill, North Ironcap, "
    "Burracoppin), FRS now has ore sources surrounding the mill from multiple directions."
)

# ── Phase transition thesis statements (prepend to first event of each phase) ──

thesis = {
    4: (  # Event 4, idx=4 — Phase 2 start
        "With the right leadership in place, FRS begins an aggressive acquisition sprint "
        "\u2014 buying gold projects at a fraction of in-ground resource value while the "
        "market re-rates the stock. "
    ),
    9: (  # Event 9, idx=9 — Phase 3 start
        "The Kula relationship pivots from a tenement deal to a full corporate takeover "
        "\u2014 FRS bids to absorb Kula Gold\u2019s entire tenement portfolio, adding Mt Palmer, "
        "Johnson Range and strategic Westonia ground in a single stroke. "
    ),
    12: (  # Event 12, idx=12 — Phase 4 start
        "Tenements without processing infrastructure are just acreage. Lake Johnston "
        "transforms FRS from explorer to future producer \u2014 a 1.5 Mtpa plant, licensed "
        "to 2041, at the centre of the hub-and-spoke network. "
    ),
    25: (  # Event 25, idx=25 — Phase 5 start
        "With mill, tenements and capital secured, FRS executes the final steps to "
        "production \u2014 consolidating ownership, completing acquisitions and signing the "
        "first ore sale. "
    ),
}

for idx, prefix in thesis.items():
    events[idx]["strategic_impact"] = prefix + events[idx]["strategic_impact"]

# ── Add Event 30 (summary) ──
event_30 = {
    "idx": 29,
    "date": "2026-02-19",
    "phase": 5,
    "phase_name": "Production Readiness",
    "phase_full": "5 \u2013 Production Readiness",
    "title": "Consolidation Complete \u2014 The Forrestania Hub",
    "strategic_impact": "",
    "tenement_ids": [],
    "missing_ids": [],
    "new_ids": [],
    "tenements_added_story": 0,
    "counterparties": "",
    "consideration": "",
    "project": "",
    "confidence": "high",
    "cum_tenements": 64,
    "cum_area_km2": 1286.0,
    "is_kula": False,
    "is_summary": True
}
events.append(event_30)
print(f"Events now: {len(events)}")

# Re-serialise
new_events_str = json.dumps(events, ensure_ascii=False)
html = html.replace(events_str, new_events_str)

# ────────────────────────────────────────────────────────────────
# 2. ADD NEW CSS (before </style>)
# ────────────────────────────────────────────────────────────────

NEW_CSS = """
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
"""

html = html.replace("</style>", NEW_CSS + "</style>")

# ────────────────────────────────────────────────────────────────
# 3. ADD LEGEND ENTRY for processing plant
# ────────────────────────────────────────────────────────────────

legend_insert = (
    '<div class="legend-item"><div class="legend-dash"></div>Approximate location (surrendered)</div>\n'
    '  <div class="legend-item"><div class="legend-swatch" style="background:rgba(31,111,235,0.25);border:2px solid #1f6feb;border-radius:3px"></div>Processing plant</div>\n'
    '  <div class="legend-item"><div class="legend-swatch" style="background:#d29922;border:1px solid #d29922;height:3px;border-radius:2px;margin:3.5px 0"></div>Ore transport route</div>'
)
html = html.replace(
    '<div class="legend-item"><div class="legend-dash"></div>Approximate location (surrendered)</div>',
    legend_insert
)

# ────────────────────────────────────────────────────────────────
# 4. ADD JS: Transport line + Mill marker INIT (after baselineAreaKm2)
# ────────────────────────────────────────────────────────────────

INIT_JS = """
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
    html: '\\u2699',
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
"""

html = html.replace(
    "baselineAreaKm2 = Math.round(baselineAreaKm2);",
    "baselineAreaKm2 = Math.round(baselineAreaKm2);\n" + INIT_JS
)

# ────────────────────────────────────────────────────────────────
# 5. MODIFY goToStep: baseline branch — hide features
# ────────────────────────────────────────────────────────────────

html = html.replace(
    "    currentStep = -1;\n    updateUI();\n    var bounds = L.latLngBounds([]);\n    baselineIds.forEach",
    "    currentStep = -1;\n    hideOreTransport();\n    hideMillMarker();\n    updateUI();\n    var bounds = L.latLngBounds([]);\n    baselineIds.forEach"
)

# ────────────────────────────────────────────────────────────────
# 6. MODIFY goToStep: after currentStep = idx — show/hide features + summary zoom
# ────────────────────────────────────────────────────────────────

# Replace the block starting with "currentStep = idx;" up to "updateUI();\n}"
# We need to insert feature show/hide logic and handle the summary event zoom

old_goto_tail = """  currentStep = idx;
  var evt = EVENTS[currentStep];

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
  }
  updateUI();
}"""

new_goto_tail = """  currentStep = idx;
  var evt = EVENTS[currentStep];

  // Show/hide mill marker (visible from event 12 onward)
  if (currentStep >= 12) showMillMarker(); else hideMillMarker();

  // Show/hide ore transport line (visible on events 28+ i.e. Westgold OPA and summary)
  if (currentStep >= 28) showOreTransport(); else hideOreTransport();

  // Summary event: zoom to full extent
  if (evt.is_summary) {
    var allBounds = L.latLngBounds([]);
    Object.values(tenementLayers).forEach(function(l) {
      if (l._visible) try { allBounds.extend(l.getBounds()); } catch(ex) {}
    });
    if (millMarkerVisible) allBounds.extend(millMarker.getLatLng());
    if (oreTransportVisible) allBounds.extend(oreTransportLine.getBounds());
    if (allBounds.isValid()) map.flyToBounds(allBounds.pad(0.15), {duration: 1.5});
    updateUI();
    return;
  }

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
  }
  updateUI();
}"""

if old_goto_tail not in html:
    raise RuntimeError("Could not find goToStep tail block to replace")
html = html.replace(old_goto_tail, new_goto_tail)

# ────────────────────────────────────────────────────────────────
# 7. MODIFY updateUI: add summary card rendering
# ────────────────────────────────────────────────────────────────

# After the phase-color line, before card.classList.toggle, insert summary check
old_update_block = """  var phaseColor = PHASE_COLORS[evt.phase] || '#58a6ff';
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

  // Count tenements"""

new_update_block = """  var phaseColor = PHASE_COLORS[evt.phase] || '#58a6ff';
  card.classList.toggle('kula', evt.is_kula);
  card.style.borderColor = evt.is_kula ? '#f0883e' : phaseColor;

  // ── Summary event: special card ──
  if (evt.is_summary) {
    card.style.borderColor = '#d29922';
    dateEl.innerHTML = '<span class="phase-badge phase-5">Production Readiness</span> ' + evt.date;
    titleEl.textContent = evt.title;
    titleEl.className = 'title';

    var totalTenements = baselineIds.length;
    Object.values(tenementLayers).forEach(function(l) { if (l._visible && !l._isBaseline) totalTenements++; });
    var totalArea = baselineAreaKm2;
    Object.values(tenementLayers).forEach(function(l) {
      if (l._visible && !l._isBaseline) {
        try {
          var geo = l.feature.geometry;
          if (geo.type === 'Polygon') totalArea += polygonAreaKm2(geo.coordinates);
          else if (geo.type === 'MultiPolygon') geo.coordinates.forEach(function(c) { totalArea += polygonAreaKm2(c); });
        } catch(ex) {}
      }
    });
    totalArea = Math.round(totalArea);

    impactEl.style.display = 'none';
    meta.innerHTML =
      '<div style="grid-column:1/-1"><div class="summary-header">Consolidation Thesis Validated</div></div>' +
      '<div class="summary-stats" style="grid-column:1/-1">' +
        '<div class="summary-stat"><div class="stat-value">' + totalTenements + '</div><div class="stat-label">Total Tenements</div></div>' +
        '<div class="summary-stat"><div class="stat-value">' + totalArea.toLocaleString() + '</div><div class="stat-label">Total km\\u00B2</div></div>' +
        '<div class="summary-stat"><div class="stat-value">$37M</div><div class="stat-label">Capital Raised</div></div>' +
        '<div class="summary-stat"><div class="stat-value">1.5 Mtpa</div><div class="stat-label">Mill Capacity</div></div>' +
      '</div>' +
      '<div class="summary-closing" style="grid-column:1/-1">Hub-and-spoke model: Lake Johnston mill at centre, multiple feeder projects within trucking distance, Gibraltar ore generating first revenue via Westgold toll arrangement.</div>';

    // Update timeline bar
    tlNodes.forEach(function(n,i) { n.classList.toggle('active', i === currentStep); });
    document.getElementById('step-num').textContent = String(currentStep + 1);
    document.querySelectorAll('.phase-segment').forEach(function(seg) {
      seg.style.opacity = parseInt(seg.dataset.phase) <= evt.phase ? '1' : '0.3';
    });
    return;
  }

  dateEl.innerHTML = '<span class="phase-badge phase-' + evt.phase + '">' + PHASE_NAMES[evt.phase] + '</span> ' + evt.date + (evt.is_kula ? '<span class="kula-badge">KULA</span>' : '');

  titleEl.textContent = evt.title;
  titleEl.className = 'title' + (evt.is_kula ? ' kula' : '');

  if (evt.strategic_impact) {
    impactEl.style.display = 'block';
    impactEl.style.setProperty('--phase-color', phaseColor);
    impactEl.textContent = evt.strategic_impact;
  } else { impactEl.style.display = 'none'; }

  // Count tenements"""

if old_update_block not in html:
    raise RuntimeError("Could not find updateUI block to replace")
html = html.replace(old_update_block, new_update_block)

# ────────────────────────────────────────────────────────────────
# 8. WRITE OUTPUT
# ────────────────────────────────────────────────────────────────

with open(HTML_PATH, "w", encoding="utf-8") as f:
    f.write(html)

print(f"Done! Wrote {len(html):,} chars to {HTML_PATH}")
print(f"Events: {len(events)}, last event: {events[-1]['title']}")
