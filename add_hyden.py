#!/usr/bin/env python3
"""
add_hyden.py — Add 8 Hyden Project tenements to the timeline map:
1. Merge polygon features into the embedded GEOJSON
2. Add tenement_ids to Event 5 (Hyden Project Holdings binding option)
"""

import json, re, os

HTML_PATH = os.path.join(os.path.dirname(__file__), "frs_tenement_timeline_map.html")
FULL_LIST = os.path.join(os.path.dirname(__file__), "ingestion/processed/maps/claude_handoff/full_tenement_list.geojson")
AUGMENTED = os.path.join(os.path.dirname(__file__), "ingestion/processed/maps/frs_tenements_augmented.geojson")

HYDEN_IDS = ["M77/1310", "E77/2207", "E77/2219", "E77/2220", "E77/2239", "E77/2460", "E77/2711", "P77/4534"]

# ── Load full tenement list to get Hyden polygons ──
with open(FULL_LIST) as f:
    full = json.load(f)

hyden_features = []
for feat in full["features"]:
    tid = feat["properties"].get("tenement_id", "")
    if tid in HYDEN_IDS:
        # Ensure consistent properties for the timeline map
        props = feat["properties"]
        if "tenement_display" not in props:
            props["tenement_display"] = tid
        if "is_approximate" not in props:
            props["is_approximate"] = False
        hyden_features.append(feat)

print(f"Extracted {len(hyden_features)} Hyden polygon features")

# ── Also update the augmented GeoJSON file on disk ──
with open(AUGMENTED) as f:
    augmented = json.load(f)

existing_ids = {feat["properties"].get("tenement_id", "") for feat in augmented["features"]}
added_to_augmented = 0
for hf in hyden_features:
    if hf["properties"]["tenement_id"] not in existing_ids:
        augmented["features"].append(hf)
        added_to_augmented += 1

with open(AUGMENTED, "w") as f:
    json.dump(augmented, f)
print(f"Added {added_to_augmented} features to augmented GeoJSON ({len(augmented['features'])} total)")

# ── Now update the HTML ──
with open(HTML_PATH, "r", encoding="utf-8") as f:
    html = f.read()

# 1. Parse and modify EVENTS
m_events = re.search(r"const EVENTS = (\[.*?\]);\s*$", html, re.MULTILINE)
if not m_events:
    raise RuntimeError("Could not find EVENTS array")
events = json.loads(m_events.group(1))
print(f"Parsed {len(events)} events")

# Update Event 5 (idx=5): Hyden Project Holdings binding option
evt5 = events[5]
print(f"Event 5: {evt5['title'][:60]}")
print(f"  Before: tenement_ids={evt5['tenement_ids']}, new_ids={evt5['new_ids']}")

evt5["tenement_ids"] = HYDEN_IDS
evt5["new_ids"] = HYDEN_IDS
evt5["tenements_added_story"] = 8

# Update cum_tenements and cum_area_km2 for event 5 and all subsequent events
# Event 4 has cum_tenements=4, event 5 now adds 8 → 12
# We need to add 8 to all events from idx 5 onward
for i in range(5, len(events)):
    events[i]["cum_tenements"] += 8

print(f"  After: tenement_ids={evt5['tenement_ids']}, new_ids={evt5['new_ids']}")
print(f"  cum_tenements chain: {[events[i]['cum_tenements'] for i in range(4, 10)]}")

# Serialise updated EVENTS
new_events_str = json.dumps(events, ensure_ascii=False)
html = html.replace(m_events.group(1), new_events_str)

# 2. Parse and modify GEOJSON (add Hyden features)
# The GEOJSON line is ~115K chars, need to find it by line search
lines = html.split('\n')
geo_line_idx = None
for li, line in enumerate(lines):
    if line.startswith('const GEOJSON ='):
        geo_line_idx = li
        break
if geo_line_idx is None:
    raise RuntimeError("Could not find GEOJSON line")
geo_line = lines[geo_line_idx].rstrip()
# Strip the "const GEOJSON = " prefix and trailing ";"
geo_json_str = geo_line[len('const GEOJSON = '):]
if geo_json_str.endswith(';'):
    geo_json_str = geo_json_str[:-1]
geojson = json.loads(geo_json_str)
print(f"GeoJSON features before: {len(geojson['features'])}")

geo_ids = {feat["properties"].get("tenement_id", "") for feat in geojson["features"]}
added = 0
for hf in hyden_features:
    if hf["properties"]["tenement_id"] not in geo_ids:
        geojson["features"].append(hf)
        added += 1

print(f"Added {added} Hyden features → {len(geojson['features'])} total")

new_geo_str = json.dumps(geojson, ensure_ascii=False)
lines[geo_line_idx] = 'const GEOJSON = ' + new_geo_str + ';\n'
html = '\n'.join(lines)

# 3. Write output
with open(HTML_PATH, "w", encoding="utf-8") as f:
    f.write(html)

print(f"\nDone! Wrote {len(html):,} chars")
print(f"Events: {len(events)}, GeoJSON features: {len(geojson['features'])}")

# Verify cum_area_km2 — we didn't update it since we need the actual polygon areas
# The map computes area dynamically from the polygons, so the card's "Total Area"
# will be correct. The cum_area_km2 field is used in the card too, let me check...
# Actually cum_area_km2 in the event data is used for the "Total Area" display.
# We need to compute the Hyden area and add it. Let me calculate from the polygons.
import math
def polygon_area_km2(coords):
    ring = coords[0] if coords else []
    if len(ring) < 3:
        return 0
    lat_mid = sum(c[1] for c in ring) / len(ring)
    k_lat = 111.32
    k_lon = 111.32 * math.cos(math.radians(lat_mid))
    a = 0
    for i in range(len(ring)):
        j = (i + 1) % len(ring)
        a += ring[i][0] * k_lon * ring[j][1] * k_lat - ring[j][0] * k_lon * ring[i][1] * k_lat
    return abs(a) / 2

total_hyden_area = 0
for hf in hyden_features:
    geo = hf["geometry"]
    if geo["type"] == "Polygon":
        total_hyden_area += polygon_area_km2(geo["coordinates"])
    elif geo["type"] == "MultiPolygon":
        for poly_coords in geo["coordinates"]:
            total_hyden_area += polygon_area_km2(poly_coords)

print(f"\nHyden total area: {total_hyden_area:.1f} km²")
print("Need to add this to cum_area_km2 for events 5+ in a second pass...")

# Re-read and update cum_area_km2
with open(HTML_PATH, "r", encoding="utf-8") as f:
    html = f.read()

m2 = re.search(r"const EVENTS = (\[.*?\]);\s*$", html, re.MULTILINE)
events = json.loads(m2.group(1))

for i in range(5, len(events)):
    events[i]["cum_area_km2"] = round(events[i]["cum_area_km2"] + total_hyden_area, 1)

print(f"cum_area_km2 chain: {[events[i]['cum_area_km2'] for i in range(4, 10)]}")

new_events_str2 = json.dumps(events, ensure_ascii=False)
html = html.replace(m2.group(1), new_events_str2)

with open(HTML_PATH, "w", encoding="utf-8") as f:
    f.write(html)

print(f"Final write: {len(html):,} chars")
