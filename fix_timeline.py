#!/usr/bin/env python3
"""
fix_timeline.py — Four fixes:
1. Remove summary Event 30
2. Fix tenement display (show growing total, not static "63 baseline")
3. Add star on Geraghty's timeline node (event index 2)
4. Fix zoom: step 12 → zoom to mill, step 28 → zoom to ore transport line
"""

import json, re, os

HTML_PATH = os.path.join(os.path.dirname(__file__), "frs_tenement_timeline_map.html")

with open(HTML_PATH, "r", encoding="utf-8") as f:
    html = f.read()

# ────────────────────────────────────────────────────────────────
# 1. REMOVE EVENT 30 (summary) from EVENTS JSON
# ────────────────────────────────────────────────────────────────

m = re.search(r"const EVENTS = (\[.*?\]);\s*$", html, re.MULTILINE)
if not m:
    raise RuntimeError("Could not find EVENTS array")
events_str = m.group(1)
events = json.loads(events_str)
print(f"Parsed {len(events)} events")

# Remove the summary event (last one with is_summary)
if events[-1].get("is_summary"):
    events.pop()
    print("Removed summary Event 30")

# Also remove is_summary key from any remaining events (cleanup)
for e in events:
    e.pop("is_summary", None)

new_events_str = json.dumps(events, ensure_ascii=False)
html = html.replace(events_str, new_events_str)
print(f"Events now: {len(events)}")

# ────────────────────────────────────────────────────────────────
# 2. ADD CSS for Geraghty star
# ────────────────────────────────────────────────────────────────

STAR_CSS = """
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
}
"""

html = html.replace("</style>", STAR_CSS + "</style>")

# ────────────────────────────────────────────────────────────────
# 3. FIX: goToStep — remove is_summary zoom block
# ────────────────────────────────────────────────────────────────

# Remove the summary zoom block
old_summary_block = """  // Summary event: zoom to full extent
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

  // Highlight new tenements"""

new_after_features = """  // Highlight new tenements"""

if old_summary_block not in html:
    raise RuntimeError("Could not find summary zoom block in goToStep")
html = html.replace(old_summary_block, new_after_features)

# ────────────────────────────────────────────────────────────────
# 4. FIX: goToStep — add zoom for mill (step 12) and transport (step 28)
#    Also add zoom for events without new_ids but with special features
# ────────────────────────────────────────────────────────────────

# The current fly-to-new-tenements block ends with:
#   }
#   updateUI();
# }
# We need to add an else-branch: if no new tenements but features appeared, zoom to them

old_fly_end = """    }
  }
  updateUI();
}

function updateUI() {"""

new_fly_end = """    }
  } else {
    // No new tenements: zoom to special features if they just appeared
    if (currentStep === 12 && millMarkerVisible) {
      // Mill marker first appears — zoom to show it
      map.flyTo([-32.208, 120.489], 9, {duration: 1.0});
    } else if (currentStep === 28 && oreTransportVisible) {
      // Ore transport line first appears — zoom to show full route
      map.flyToBounds(oreTransportLine.getBounds().pad(0.4), {duration: 1.2, maxZoom: 10});
    }
  }
  updateUI();
}

function updateUI() {"""

if old_fly_end not in html:
    raise RuntimeError("Could not find fly-end block in goToStep")
html = html.replace(old_fly_end, new_fly_end)

# ────────────────────────────────────────────────────────────────
# 5. FIX: updateUI — remove is_summary card rendering
# ────────────────────────────────────────────────────────────────

old_summary_card = """  // ── Summary event: special card ──
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

  dateEl"""

new_no_summary = """  dateEl"""

if old_summary_card not in html:
    raise RuntimeError("Could not find summary card block in updateUI")
html = html.replace(old_summary_card, new_no_summary)

# ────────────────────────────────────────────────────────────────
# 6. FIX: updateUI — change tenement display to show growing total
# ────────────────────────────────────────────────────────────────

old_tenement_display = """  var mh = '';
  var tenLabel = acquired + ' acquired';
  if ((evt.new_ids||[]).length > 0) tenLabel += ' (+' + cNew.length + (aNew.length > 0 ? ' +' + aNew.length + '~' : '') + ' new)';
  tenLabel += ' \\u00B7 ' + baselineIds.length + ' baseline';
  mh += '<div class="meta-item wide"><div class="label">Tenements</div><div class="value">' + tenLabel + '</div></div>';"""

new_tenement_display = """  var mh = '';
  var total = acquired + baselineIds.length;
  var tenLabel = '' + total + ' total';
  if ((evt.new_ids||[]).length > 0) tenLabel += ' <span style="color:#238636">(+' + cNew.length + (aNew.length > 0 ? ' +' + aNew.length + '~' : '') + ' new)</span>';
  tenLabel += '<br><span style="font-size:10px;color:#8b949e">' + acquired + ' acquired \\u00B7 ' + baselineIds.length + ' pre-existing</span>';
  mh += '<div class="meta-item wide"><div class="label">Tenements</div><div class="value">' + tenLabel + '</div></div>';"""

if old_tenement_display not in html:
    raise RuntimeError("Could not find tenement display block in updateUI")
html = html.replace(old_tenement_display, new_tenement_display)

# ────────────────────────────────────────────────────────────────
# 7. FIX: buildTimeline — add geraghty-star class to node index 2
# ────────────────────────────────────────────────────────────────

old_node_class = "node.className = 'tl-node' + (evt.is_kula ? ' kula-node' : '');"
new_node_class = "node.className = 'tl-node' + (evt.is_kula ? ' kula-node' : '') + (i === 2 ? ' geraghty-star' : '');"

if old_node_class not in html:
    raise RuntimeError("Could not find node className line in buildTimeline")
html = html.replace(old_node_class, new_node_class)

# ────────────────────────────────────────────────────────────────
# 8. WRITE OUTPUT
# ────────────────────────────────────────────────────────────────

with open(HTML_PATH, "w", encoding="utf-8") as f:
    f.write(html)

print(f"Done! Wrote {len(html):,} chars")
print(f"Events: {len(events)}, last: {events[-1]['title'][:50]}")
