#!/usr/bin/env python3
"""
Apply light theme and add Edna May mill marker to the timeline map.
"""

HTML_PATH = "/Users/alfredlewis/Documents/Forrestania Resources/frs_tenement_timeline_map.html"

with open(HTML_PATH, "r", encoding="utf-8") as f:
    html = f.read()

print(f"Read HTML: {len(html):,} chars")

# ═══════════════════════════════════════════
# CHANGE 1: CSS colour replacements (dark → light)
# ═══════════════════════════════════════════

replacements = [
    # Body background and text
    ("background:#0a0e17;color:#e0e6ed", "background:#ffffff;color:#1f2328"),

    # Leaflet container background
    (".leaflet-container{background:#0d1117}", ".leaflet-container{background:#f8f9fa}"),

    # Event card overlay
    ("background:rgba(13,17,23,0.95);border:1px solid #30363d;border-radius:12px;padding:20px;z-index:1000;backdrop-filter:blur(12px);box-shadow:0 8px 32px rgba(0,0,0,0.4)",
     "background:rgba(255,255,255,0.96);border:1px solid #d0d7de;border-radius:12px;padding:20px;z-index:1000;backdrop-filter:blur(12px);box-shadow:0 8px 32px rgba(0,0,0,0.1)"),

    # Event card date
    ("#event-card .date{font-size:12px;color:#8b949e;",
     "#event-card .date{font-size:12px;color:#57606a;"),

    # Event card title
    ("color:#f0f6fc;margin-bottom:10px", "color:#1f2328;margin-bottom:10px"),

    # Strategic impact
    ("color:#b1bac4;line-height:1.6;margin-bottom:12px;padding:10px;background:rgba(48,54,61,0.4)",
     "color:#57606a;line-height:1.6;margin-bottom:12px;padding:10px;background:rgba(208,215,222,0.3)"),

    # Meta item background
    ("#event-card .meta-item{background:rgba(48,54,61,0.6)",
     "#event-card .meta-item{background:rgba(208,215,222,0.4)"),

    # Meta label
    ("#event-card .meta-item .label{color:#8b949e;",
     "#event-card .meta-item .label{color:#57606a;"),

    # Meta value
    ("#event-card .meta-item .value{color:#e6edf3;",
     "#event-card .meta-item .value{color:#1f2328;"),

    # Kula badge text (keep dark on orange)
    # Phase badge text on orange/gold — keep #0d1117 (dark text on bright badge)

    # Timeline bar
    ("background:rgba(13,17,23,0.98);border-top:1px solid #30363d;z-index:1000",
     "background:rgba(255,255,255,0.98);border-top:1px solid #d0d7de;z-index:1000"),

    # Timeline nav buttons
    ("border:1px solid #30363d;background:transparent;color:#8b949e;font-size:11px",
     "border:1px solid #d0d7de;background:transparent;color:#57606a;font-size:11px"),

    # Timeline nav hover
    (".tl-nav:hover{color:#e6edf3;border-color:#58a6ff",
     ".tl-nav:hover{color:#1f2328;border-color:#58a6ff"),

    # Timeline track
    ("background:#21262d;border-radius:1px", "background:#d0d7de;border-radius:1px"),

    # Date markers
    ("color:#484f58;transform:translateX(-50%)", "color:#8c959f;transform:translateX(-50%)"),

    # Play button hover (white text on blue fill)
    ("#play-btn:hover{background:#58a6ff;color:#0d1117}",
     "#play-btn:hover{background:#58a6ff;color:#ffffff}"),

    # Play button playing hover
    ("#play-btn.playing:hover{background:#f85149;color:#0d1117}",
     "#play-btn.playing:hover{background:#f85149;color:#ffffff}"),

    # Speed button
    ("border:1px solid #30363d;background:#161b22;color:#8b949e;font-size:10px",
     "border:1px solid #d0d7de;background:#ffffff;color:#57606a;font-size:10px"),

    # Speed button hover
    ("#speed-btn:hover{color:#e6edf3;border-color:#58a6ff}",
     "#speed-btn:hover{color:#1f2328;border-color:#58a6ff}"),

    # Separator
    ("background:#21262d;flex-shrink:0;margin:0 4px", "background:#d0d7de;flex-shrink:0;margin:0 4px"),

    # Tooltip
    ("background:rgba(22,27,34,0.97);color:#e6edf3;border:1px solid #30363d;border-radius:8px;padding:8px 12px;font-size:11px;z-index:2000;pointer-events:none;opacity:0;transition:opacity 0.15s;max-width:280px;box-shadow:0 4px 16px rgba(0,0,0,0.5)",
     "background:rgba(255,255,255,0.97);color:#1f2328;border:1px solid #d0d7de;border-radius:8px;padding:8px 12px;font-size:11px;z-index:2000;pointer-events:none;opacity:0;transition:opacity 0.15s;max-width:280px;box-shadow:0 4px 16px rgba(0,0,0,0.12)"),

    # Tooltip date
    ("#tl-tooltip .tt-date{color:#8b949e;", "#tl-tooltip .tt-date{color:#57606a;"),

    # Map legend
    ("background:rgba(13,17,23,0.92);border:1px solid #30363d;border-radius:8px;padding:8px 12px;font-size:10px;color:#8b949e;z-index:999;display:flex;flex-direction:column;gap:4px}",
     "background:rgba(255,255,255,0.92);border:1px solid #d0d7de;border-radius:8px;padding:8px 12px;font-size:10px;color:#57606a;z-index:999;display:flex;flex-direction:column;gap:4px}"),

    # Legend dash
    ("border-top:2px dashed #8b949e;", "border-top:2px dashed #8c959f;"),

    # Step counter
    ("bottom:62px;left:16px;background:rgba(13,17,23,0.92);border:1px solid #30363d;border-radius:8px;padding:6px 12px;font-size:11px;color:#8b949e",
     "bottom:62px;left:16px;background:rgba(255,255,255,0.92);border:1px solid #d0d7de;border-radius:8px;padding:6px 12px;font-size:11px;color:#57606a"),

    # Popup
    (".leaflet-popup-content-wrapper{background:#161b22;color:#e6edf3;border:1px solid #30363d;border-radius:8px}",
     ".leaflet-popup-content-wrapper{background:#ffffff;color:#1f2328;border:1px solid #d0d7de;border-radius:8px}"),

    (".leaflet-popup-tip{background:#161b22}", ".leaflet-popup-tip{background:#ffffff}"),

    # Scrollbar
    ("::-webkit-scrollbar-thumb{background:#30363d;border-radius:3px}",
     "::-webkit-scrollbar-thumb{background:#d0d7de;border-radius:3px}"),

    ("::-webkit-scrollbar-thumb:hover{background:#484f58}",
     "::-webkit-scrollbar-thumb:hover{background:#8c959f}"),

    # Ore transport label background
    ("background: rgba(13,17,23,0.9);", "background: rgba(255,255,255,0.9);"),

    # Summary stat
    (".summary-stat {\n  background: rgba(48,54,61,0.6);",
     ".summary-stat {\n  background: rgba(208,215,222,0.4);"),

    ("  border: 1px solid #30363d;\n}\n.summary-stat .stat-value",
     "  border: 1px solid #d0d7de;\n}\n.summary-stat .stat-value"),

    ("  color: #f0f6fc;\n  line-height: 1.2;\n}\n.summary-stat .stat-label",
     "  color: #1f2328;\n  line-height: 1.2;\n}\n.summary-stat .stat-label"),

    ("  color: #8b949e;\n  text-transform: uppercase;\n  letter-spacing: 0.5px;\n  margin-top: 4px;\n}\n.summary-closing",
     "  color: #57606a;\n  text-transform: uppercase;\n  letter-spacing: 0.5px;\n  margin-top: 4px;\n}\n.summary-closing"),

    ("  color: #b1bac4;\n  font-style: italic;",
     "  color: #57606a;\n  font-style: italic;"),

    ("  background: rgba(48,54,61,0.3);\n  border-radius: 8px;\n  border-left: 3px solid #d29922;\n}",
     "  background: rgba(208,215,222,0.2);\n  border-radius: 8px;\n  border-left: 3px solid #d29922;\n}"),

    # Geraghty star
    ("  color: #f0f6fc;\n  pointer-events: none;\n  text-shadow: 0 0 4px rgba(137,87,229,0.6);",
     "  color: #1f2328;\n  pointer-events: none;\n  text-shadow: 0 0 4px rgba(137,87,229,0.6);"),
]

count = 0
for old, new in replacements:
    if old in html:
        html = html.replace(old, new)
        count += 1
    else:
        print(f"  WARNING: not found: {old[:60]}...")

print(f"Applied {count}/{len(replacements)} CSS replacements")

# ═══════════════════════════════════════════
# CHANGE 2: Tile layer dark → light
# ═══════════════════════════════════════════

html = html.replace(
    "basemaps.cartocdn.com/dark_all/",
    "basemaps.cartocdn.com/light_all/"
)
print("Changed tile layer to light_all")

# ═══════════════════════════════════════════
# CHANGE 3: Polygon styles for light basemap
# ═══════════════════════════════════════════

# Baseline style
html = html.replace(
    "? {color:'#6e7681',weight:1.2,dashArray:'6 4',fillColor:'#8b949e',fillOpacity:0.15,opacity:0.55}\n"
    "    : {color:'#6e7681',weight:1.4,fillColor:'#8b949e',fillOpacity:0.22,opacity:0.6};",
    "? {color:'#8c959f',weight:1.2,dashArray:'6 4',fillColor:'#8c959f',fillOpacity:0.12,opacity:0.6}\n"
    "    : {color:'#8c959f',weight:1.4,fillColor:'#8c959f',fillOpacity:0.18,opacity:0.65};"
)

# Phase style - slight opacity increase
html = html.replace(
    "? {color:c,weight:1.8,dashArray:'7 4',fillColor:c,fillOpacity:0.15,opacity:0.7}\n"
    "    : {color:c,weight:1.8,fillColor:c,fillOpacity:0.25,opacity:0.7};",
    "? {color:c,weight:1.8,dashArray:'7 4',fillColor:c,fillOpacity:0.15,opacity:0.75}\n"
    "    : {color:c,weight:2.0,fillColor:c,fillOpacity:0.25,opacity:0.8};"
)

# Highlight style - white border → dark border
html = html.replace(
    "? {color:'#ffffff',weight:2,dashArray:'6 4',fillColor:c,fillOpacity:0.3,opacity:1.0}\n"
    "    : {color:'#ffffff',weight:2.5,fillColor:c,fillOpacity:0.55,opacity:1.0};",
    "? {color:'#1f2328',weight:2,dashArray:'6 4',fillColor:c,fillOpacity:0.35,opacity:1.0}\n"
    "    : {color:'#1f2328',weight:2.5,fillColor:c,fillOpacity:0.5,opacity:1.0};"
)

print("Updated polygon styles for light basemap")

# ═══════════════════════════════════════════
# CHANGE 4: Inline JS colour references
# ═══════════════════════════════════════════

# Popup approximate location text
html = html.replace(
    '<i style="color:#8b949e">Approximate location',
    '<i style="color:#57606a">Approximate location'
)

# Mill popup text
html = html.replace(
    '<i style="color:#8b949e">Emily Ann, acquired from Horizon Minerals</i>',
    '<i style="color:#57606a">Emily Ann, acquired from Horizon Minerals</i>'
)

# Baseline card date
html = html.replace(
    "color:#484f58;font-weight:600\">PRE-ACQUISITION BASELINE",
    "color:#8c959f;font-weight:600\">PRE-ACQUISITION BASELINE"
)

# Tenement count sub-text
html = html.replace(
    "'<br><span style=\"font-size:10px;color:#8b949e\">'",
    "'<br><span style=\"font-size:10px;color:#57606a\">'"
)

# Note meta text
html = html.replace(
    "style=\"color:#8b949e;font-size:10px\">' + evt.tenements_added_story",
    "style=\"color:#57606a;font-size:10px\">' + evt.tenements_added_story"
)

# Approximate meta text
html = html.replace(
    "style=\"color:#8b949e;font-size:10px\">' + aNew.length",
    "style=\"color:#57606a;font-size:10px\">' + aNew.length"
)

# Confidence "low" color
html = html.replace(
    "conf === 'low' ? '#8b949e'",
    "conf === 'low' ? '#57606a'"
)

print("Updated inline JS colours")

# ═══════════════════════════════════════════
# CHANGE 5: Add Edna May marker CSS
# ═══════════════════════════════════════════

ednamay_css = """
/* Edna May marker (third-party landmark) */
.ednamay-marker-icon {
  width: 28px;
  height: 28px;
  border-radius: 6px;
  border: 2px solid #d29922;
  background: rgba(210,153,34,0.25);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  line-height: 1;
  box-shadow: 0 0 10px rgba(210,153,34,0.4);
  cursor: pointer;
}
"""

# Insert after the mill-marker-icon closing brace
html = html.replace(
    "  cursor: pointer;\n}\n\n/* Summary card */",
    "  cursor: pointer;\n}" + ednamay_css + "\n/* Summary card */"
)
print("Added Edna May CSS class")

# ═══════════════════════════════════════════
# CHANGE 6: Add Edna May marker JS
# ═══════════════════════════════════════════

ednamay_js = """
// ── Edna May Gold Mine Marker (Ramelius Resources — third-party landmark, always visible) ──
var ednaMayMarker = L.marker([-31.293, 118.862], {
  icon: L.divIcon({
    className: 'ednamay-marker-icon',
    html: '\\u2699',
    iconSize: [28, 28],
    iconAnchor: [14, 14]
  }),
  zIndexOffset: 500
});
ednaMayMarker.bindPopup(
  '<b>Edna May Gold Mine</b><br>' +
  'Ramelius Resources (ASX: RMS)<br>' +
  '<i style="color:#57606a">Processing plant ~27km east of Burracoppin</i>'
);
ednaMayMarker.addTo(map);
"""

# Insert after hideMillMarker function
html = html.replace(
    "function hideMillMarker() {\n  if (millMarkerVisible) {\n    map.removeLayer(millMarker);\n    millMarkerVisible = false;\n  }\n}",
    "function hideMillMarker() {\n  if (millMarkerVisible) {\n    map.removeLayer(millMarker);\n    millMarkerVisible = false;\n  }\n}" + ednamay_js
)
print("Added Edna May JS marker (always visible)")

# ═══════════════════════════════════════════
# CHANGE 7: Add legend entry for Edna May
# ═══════════════════════════════════════════

html = html.replace(
    '<div class="legend-item"><div class="legend-swatch" style="background:#d29922;border:1px solid #d29922;height:3px;border-radius:2px;margin:3.5px 0"></div>Ore transport route</div>',
    '<div class="legend-item"><div class="legend-swatch" style="background:#d29922;border:1px solid #d29922;height:3px;border-radius:2px;margin:3.5px 0"></div>Ore transport route</div>\n  <div class="legend-item"><div class="legend-swatch" style="background:rgba(210,153,34,0.25);border:2px solid #d29922;border-radius:3px"></div>Third-party mine / mill</div>'
)

# Also update baseline swatch for light theme
html = html.replace(
    'style="background:#8b949e;border:1px solid #6e7681;opacity:0.7"',
    'style="background:#8c959f;border:1px solid #8c959f;opacity:0.7"'
)

print("Updated legend")

# ═══════════════════════════════════════════
# CHANGE 8: Baseline card border colour in JS
# ═══════════════════════════════════════════

# The baseline card uses phase-color CSS var set to #484f58
html = html.replace(
    "cardEl.style.setProperty('--phase-color', '#484f58');",
    "cardEl.style.setProperty('--phase-color', '#8c959f');"
)

print("Updated baseline card border colour")

# ═══════════════════════════════════════════
# Write output
# ═══════════════════════════════════════════

with open(HTML_PATH, "w", encoding="utf-8") as f:
    f.write(html)

print(f"\nDone! Output: {len(html):,} chars")
