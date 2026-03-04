#!/usr/bin/env python3
"""
Add Nearby Resources feature to FRS timeline map.
1. Rename existing "Resources" button to "FRS Resources"
2. Add new "Nearby" button showing all gold resources within 200km of Edna May or Lake Johnston
3. Inject NEARBY_RESOURCES constant from CSV
4. Add panel, markers, and toggle logic
"""
import json, csv, re

MAP_FILE = '/Users/alfredlewis/Documents/Forrestania Resources/frs_tenement_timeline_map.html'
CSV_FILE = '/Users/alfredlewis/Documents/Forrestania Resources/frs_nearby_gold_targets.csv'

# ═══════════════════════════════════════════════════════════
# 1. Parse CSV and build nearby resources
# ═══════════════════════════════════════════════════════════
with open(CSV_FILE) as f:
    reader = csv.DictReader(f)
    rows = list(reader)

nearby = []
seen_coords = {}  # Deduplicate overlapping sites - keep largest

for r in rows:
    try:
        d_edna = float(r['Dist_Edna_May_Mill_km']) if r['Dist_Edna_May_Mill_km'] else 9999
        d_lj = float(r['Dist_Lake_Johnston_Plant_km']) if r['Dist_Lake_Johnston_Plant_km'] else 9999
        oz = int(float(r['Resource_Oz_Au'])) if r['Resource_Oz_Au'] else 0
        if min(d_edna, d_lj) <= 200 and oz > 0:
            lat = round(float(r['Latitude']), 4)
            lon = round(float(r['Longitude']), 4)
            mt = round(float(r['Resource_Mt']), 2) if r['Resource_Mt'] else 0
            grade = round(float(r['Resource_Grade_gpt']), 2) if r['Resource_Grade_gpt'] else 0
            dist = round(min(d_edna, d_lj), 1)
            nearest = 'Edna May' if d_edna < d_lj else 'Lake Johnston'

            # Shorten owner names
            owner = r['Primary_Owner']
            owner = owner.replace(' Resources Ltd', '').replace(' Resources Limited', '')
            owner = owner.replace(' Mining Limited', '').replace(' Mining Ltd', '')
            owner = owner.replace(' Pty Ltd', '').replace(' Pty Limited', '')
            owner = owner.replace(' Limited', '').replace(' Ltd', '')
            owner = owner.replace('Northern Star', 'NST').replace('Evolution', 'EVN')
            owner = owner.replace('Ramelius', 'RMS').replace('Westgold', 'WGX')

            # Stage shortcode
            stage_map = {
                'Operating': 'op', 'Proposed': 'pr', 'Undeveloped': 'ud',
                'Care and Maintenance': 'cm', 'Shut': 'sh'
            }
            stage = stage_map.get(r['Stage'], 'ot')

            entry = {
                'n': r['Site'],
                'oz': oz,
                'mt': mt,
                'g': grade,
                'la': lat,
                'lo': lon,
                'ow': owner,
                'st': stage,
                'dk': dist,
                'nr': nearest
            }

            # Dedup by coordinates - keep largest
            coord_key = f"{lat},{lon}"
            if coord_key in seen_coords:
                if oz > seen_coords[coord_key]['oz']:
                    seen_coords[coord_key] = entry
            else:
                seen_coords[coord_key] = entry
    except Exception as ex:
        pass

nearby = sorted(seen_coords.values(), key=lambda x: -x['oz'])

print(f"Parsed {len(rows)} CSV rows -> {len(nearby)} unique nearby resources (deduped by location)")
print(f"Total oz: {sum(r['oz'] for r in nearby):,}")

# ═══════════════════════════════════════════════════════════
# 2. Read HTML file
# ═══════════════════════════════════════════════════════════
with open(MAP_FILE) as f:
    content = f.read()

# ═══════════════════════════════════════════════════════════
# 3. Rename existing button: "Resources" -> "FRS Resources"
# ═══════════════════════════════════════════════════════════
content = content.replace(
    'title="Show gold resource deposits">Resources</button>',
    'title="Show FRS gold resource deposits">FRS Resources</button>'
)
content = content.replace(
    "resourcesBtn.textContent = 'Hide Resources';",
    "resourcesBtn.textContent = 'Hide FRS';",
)
content = content.replace(
    "resourcesBtn.textContent = 'Resources';",
    "resourcesBtn.textContent = 'FRS Resources';",
)
print("  Renamed Resources -> FRS Resources")

# ═══════════════════════════════════════════════════════════
# 4. Add new button HTML (after resources-btn)
# ═══════════════════════════════════════════════════════════
content = content.replace(
    '<button id="resources-btn" title="Show FRS gold resource deposits">FRS Resources</button>',
    '<button id="resources-btn" title="Show FRS gold resource deposits">FRS Resources</button>\n'
    '    <button id="nearby-btn" title="Show all gold resources within 200km">Nearby</button>'
)
print("  Added Nearby button HTML")

# ═══════════════════════════════════════════════════════════
# 5. Add CSS for nearby button and panel
# ═══════════════════════════════════════════════════════════
nearby_css = """
#nearby-btn{padding:3px 10px;border-radius:4px;border:1px solid #d0d7de;background:#ffffff;color:#57606a;font-size:10px;cursor:pointer;flex-shrink:0;transition:all 0.2s;white-space:nowrap}
#nearby-btn:hover{color:#1f2328;border-color:#1f6feb;background:rgba(31,111,235,0.06)}
#nearby-btn.active{border-color:#1f6feb;color:#fff;background:#1f6feb;font-weight:600}
#nearby-panel{position:absolute;top:16px;right:16px;width:420px;max-height:calc(100vh - 88px);overflow-y:auto;background:rgba(255,255,255,0.97);border:2px solid #1f6feb;border-radius:12px;padding:20px;z-index:1001;backdrop-filter:blur(12px);box-shadow:0 8px 32px rgba(31,111,235,0.2);display:none}
#nearby-panel .np-header{font-size:10px;color:#1f6feb;text-transform:uppercase;letter-spacing:1.5px;font-weight:700;margin-bottom:4px}
#nearby-panel .np-title{font-size:16px;font-weight:700;color:#1f2328;margin-bottom:4px}
#nearby-panel .np-subtitle{font-size:11px;color:#57606a;margin-bottom:12px}
#nearby-panel .np-summary{display:grid;grid-template-columns:1fr 1fr 1fr;gap:6px;margin-bottom:10px;font-size:11px}
#nearby-panel .np-stat{background:rgba(31,111,235,0.08);padding:6px 8px;border-radius:6px;text-align:center}
#nearby-panel .np-stat .val{font-size:15px;font-weight:700;color:#1f2328}
#nearby-panel .np-stat .lbl{color:#57606a;font-size:9px;text-transform:uppercase;letter-spacing:0.5px}
#nearby-panel .np-filters{display:flex;gap:4px;margin-bottom:10px;flex-wrap:wrap}
#nearby-panel .np-pill{padding:2px 8px;border-radius:10px;font-size:9px;font-weight:600;cursor:pointer;border:1.5px solid transparent;transition:all 0.15s;opacity:0.5}
#nearby-panel .np-pill.active{opacity:1;border-color:rgba(0,0,0,0.15)}
#nearby-panel .np-list{list-style:none;padding:0;margin:0}
#nearby-panel .np-row{display:flex;align-items:center;gap:6px;padding:6px 8px;border-radius:6px;cursor:pointer;transition:background 0.15s;border-bottom:1px solid rgba(208,215,222,0.3)}
#nearby-panel .np-row:hover{background:rgba(31,111,235,0.06)}
#nearby-panel .np-row .np-dot{width:8px;height:8px;border-radius:50%;flex-shrink:0}
#nearby-panel .np-row .np-info{flex:1;min-width:0}
#nearby-panel .np-row .np-name{font-size:11px;font-weight:600;color:#1f2328;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
#nearby-panel .np-row .np-detail{font-size:9px;color:#57606a}
#nearby-panel .np-row .np-oz{font-size:11px;font-weight:700;color:#1f2328;white-space:nowrap}
#nearby-panel .np-row .np-dist{font-size:9px;color:#8c959f;white-space:nowrap}
"""

# Insert CSS before the resource-marker class
content = content.replace(
    '.resource-marker{',
    nearby_css + '.resource-marker{'
)
print("  Added Nearby CSS")

# ═══════════════════════════════════════════════════════════
# 6. Add nearby panel HTML (after resource-panel div)
# ═══════════════════════════════════════════════════════════
nearby_html = """<div id="nearby-panel">
  <div class="np-header">REGIONAL GOLD LANDSCAPE</div>
  <div class="np-title">Nearby Resources (200km)</div>
  <div class="np-subtitle">Gold deposits near Edna May and Lake Johnston mills - click to zoom</div>
  <div class="np-summary" id="np-summary"></div>
  <div class="np-filters" id="np-filters"></div>
  <ul class="np-list" id="np-list"></ul>
</div>"""

content = content.replace(
    '</div>\n<div id="timeline-bar"',
    '</div>\n' + nearby_html + '\n<div id="timeline-bar"'
)
print("  Added Nearby panel HTML")

# ═══════════════════════════════════════════════════════════
# 7. Inject NEARBY_RESOURCES constant + JS logic
# ═══════════════════════════════════════════════════════════
nearby_json = json.dumps(nearby, ensure_ascii=False, separators=(',', ':'))

nearby_js = f"""
// ── Nearby Gold Resources (within 200km of Edna May or Lake Johnston) ──
var NEARBY = {nearby_json};
var nearbyStageColor = {{op:"#238636",pr:"#1f6feb",ud:"#58a6ff",cm:"#d29922",sh:"#8c959f",ot:"#6e7781"}};
var nearbyStageName = {{op:"Operating",pr:"Proposed",ud:"Undeveloped",cm:"Care & Maint.",sh:"Shut",ot:"Other"}};
var nearbyVisible = false;
var nearbyMarkersGroup = L.layerGroup();
var nearbyActiveStages = {{op:true,pr:true,ud:true,cm:true,sh:true}};

// Build nearby markers
NEARBY.forEach(function(r) {{
  var col = nearbyStageColor[r.st] || '#6e7781';
  var radius = Math.max(3, Math.min(14, Math.log10(r.oz) * 2.5 - 6));
  var marker = L.circleMarker([r.la, r.lo], {{
    radius: radius, fillColor: col, fillOpacity: 0.6, color: '#fff', weight: 1, opacity: 0.8
  }});
  marker.bindPopup(
    '<div style="min-width:200px">' +
    '<div style="font-size:13px;font-weight:700;margin-bottom:3px">' + r.n + '</div>' +
    '<div style="font-size:9px;font-weight:600;display:inline-block;padding:1px 6px;border-radius:6px;background:' + col + ';color:#fff;margin-bottom:6px">' + (nearbyStageName[r.st]||'') + '</div>' +
    '<table style="font-size:11px;width:100%;border-collapse:collapse">' +
    '<tr><td style="color:#57606a;padding:2px 6px 2px 0">Resource</td><td style="font-weight:600">' + r.oz.toLocaleString() + ' oz Au</td></tr>' +
    '<tr><td style="color:#57606a;padding:2px 6px 2px 0">Tonnage</td><td>' + r.mt.toFixed(2) + ' Mt @ ' + r.g.toFixed(2) + ' g/t</td></tr>' +
    '<tr><td style="color:#57606a;padding:2px 6px 2px 0">Owner</td><td>' + r.ow + '</td></tr>' +
    '<tr><td style="color:#57606a;padding:2px 6px 2px 0">Distance</td><td>' + r.dk + ' km to ' + r.nr + '</td></tr>' +
    '</table></div>',
    {{maxWidth: 280}}
  );
  marker._nearbyData = r;
  nearbyMarkersGroup.addLayer(marker);
}});

// Build nearby panel
(function buildNearbyPanel() {{
  var totalOz = 0, count = NEARBY.length;
  NEARBY.forEach(function(r) {{ totalOz += r.oz; }});

  var summary = document.getElementById('np-summary');
  summary.innerHTML =
    '<div class="np-stat"><div class="val">' + count + '</div><div class="lbl">Deposits</div></div>' +
    '<div class="np-stat"><div class="val">' + (totalOz >= 1e6 ? (totalOz/1e6).toFixed(1) + 'M' : Math.round(totalOz/1000) + 'k') + '</div><div class="lbl">Total oz Au</div></div>' +
    '<div class="np-stat"><div class="val">200km</div><div class="lbl">Radius</div></div>';

  // Stage filter pills
  var filters = document.getElementById('np-filters');
  var stageCounts = {{}};
  NEARBY.forEach(function(r) {{ stageCounts[r.st] = (stageCounts[r.st]||0) + 1; }});
  ['op','pr','ud','cm','sh'].forEach(function(st) {{
    if (!stageCounts[st]) return;
    var pill = document.createElement('span');
    pill.className = 'np-pill active';
    pill.dataset.stage = st;
    pill.style.background = nearbyStageColor[st] + '22';
    pill.style.color = nearbyStageColor[st];
    pill.textContent = nearbyStageName[st] + ' (' + stageCounts[st] + ')';
    pill.addEventListener('click', function() {{
      nearbyActiveStages[st] = !nearbyActiveStages[st];
      pill.classList.toggle('active', nearbyActiveStages[st]);
      pill.style.opacity = nearbyActiveStages[st] ? '1' : '0.3';
      refreshNearbyList();
      refreshNearbyMarkers();
    }});
    filters.appendChild(pill);
  }});

  refreshNearbyList();
}})();

function refreshNearbyList() {{
  var list = document.getElementById('np-list');
  list.innerHTML = '';
  var filtered = NEARBY.filter(function(r) {{ return nearbyActiveStages[r.st]; }});
  filtered.forEach(function(r) {{
    var col = nearbyStageColor[r.st] || '#6e7781';
    var li = document.createElement('li');
    li.className = 'np-row';
    li.innerHTML =
      '<div class="np-dot" style="background:' + col + '"></div>' +
      '<div class="np-info">' +
        '<div class="np-name">' + r.n + '</div>' +
        '<div class="np-detail">' + r.mt.toFixed(1) + ' Mt @ ' + r.g.toFixed(1) + ' g/t - ' + r.ow + '</div>' +
      '</div>' +
      '<div class="np-oz">' + (r.oz >= 1e6 ? (r.oz/1e6).toFixed(1) + 'M' : r.oz >= 1000 ? Math.round(r.oz/1000) + 'k' : r.oz) + '</div>' +
      '<div class="np-dist">' + r.dk + 'km</div>';
    li.addEventListener('click', function() {{
      map.setView([r.la, r.lo], 12);
      nearbyMarkersGroup.eachLayer(function(m) {{
        if (m._nearbyData === r) m.openPopup();
      }});
    }});
    list.appendChild(li);
  }});
}}

function refreshNearbyMarkers() {{
  nearbyMarkersGroup.eachLayer(function(m) {{
    var r = m._nearbyData;
    if (r && !nearbyActiveStages[r.st]) {{
      m.setStyle({{fillOpacity: 0, opacity: 0}});
    }} else {{
      var col = nearbyStageColor[r.st] || '#6e7781';
      m.setStyle({{fillColor: col, fillOpacity: 0.6, color: '#fff', opacity: 0.8}});
    }}
  }});
}}

function showNearby() {{
  nearbyMarkersGroup.addTo(map);
  document.getElementById('event-card').style.display = 'none';
  document.getElementById('resource-panel').style.display = 'none';
  document.getElementById('nearby-panel').style.display = 'block';
  // If FRS resources are showing, hide them
  if (resourcesVisible) {{
    resourcesVisible = false;
    resourcesBtn.classList.remove('active');
    resourcesBtn.textContent = 'FRS Resources';
    hideResourceHighlights();
  }}
}}

function hideNearby() {{
  map.removeLayer(nearbyMarkersGroup);
  document.getElementById('nearby-panel').style.display = 'none';
  document.getElementById('event-card').style.display = '';
}}

var nearbyBtn = document.getElementById('nearby-btn');
nearbyBtn.addEventListener('click', function(e) {{
  e.stopPropagation();
  nearbyVisible = !nearbyVisible;
  nearbyBtn.classList.toggle('active', nearbyVisible);
  if (nearbyVisible) {{
    showNearby();
    nearbyBtn.textContent = 'Hide Nearby';
  }} else {{
    hideNearby();
    nearbyBtn.textContent = 'Nearby';
  }}
}});
"""

# Insert the nearby JS after the resources button event listener block
content = content.replace(
    "\n// ── State ──\nvar currentStep",
    "\n" + nearby_js + "\n// ── State ──\nvar currentStep"
)

# Also update showResourceHighlights to hide nearby panel if visible
content = content.replace(
    "function showResourceHighlights() {\n  // Highlight tenement polygons",
    "function showResourceHighlights() {\n  // Hide nearby if active\n  if (nearbyVisible) { nearbyVisible = false; nearbyBtn.classList.remove('active'); nearbyBtn.textContent = 'Nearby'; hideNearby(); }\n  // Highlight tenement polygons"
)

print(f"  Injected NEARBY_RESOURCES ({len(nearby)} entries) and JS logic")

# ═══════════════════════════════════════════════════════════
# 8. Write back
# ═══════════════════════════════════════════════════════════
with open(MAP_FILE, 'w') as f:
    f.write(content)

print(f"\n✅ All changes written to {MAP_FILE}")
print(f"   File size: {len(content):,} chars")
