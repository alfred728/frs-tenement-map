#!/usr/bin/env python3
"""Fix cum_area_km2 to NOT include baseline area (the UI adds it separately)."""
import json, re, math

HTML_PATH = "/Users/alfredlewis/Documents/Forrestania Resources/frs_tenement_timeline_map.html"

def polygon_area_km2(coords):
    ring = coords[0]
    if isinstance(ring[0][0], list):
        ring = ring[0]
    n = len(ring)
    if n < 3:
        return 0.0
    area = 0.0
    for i in range(n):
        j = (i + 1) % n
        lon_i, lat_i = ring[i][0], ring[i][1]
        lon_j, lat_j = ring[j][0], ring[j][1]
        area += lon_i * lat_j - lon_j * lat_i
    area = abs(area) / 2.0
    avg_lat = sum(c[1] for c in ring) / n
    km_per_deg_lat = 111.32
    km_per_deg_lon = 111.32 * math.cos(math.radians(avg_lat))
    return area * km_per_deg_lat * km_per_deg_lon

with open(HTML_PATH, "r", encoding="utf-8") as f:
    html = f.read()

# Extract EVENTS
m = re.search(r"const EVENTS = (\[.*?\]);\s*$", html, re.MULTILINE)
events = json.loads(m.group(1))

# Extract GEOJSON
lines = html.split("\n")
geojson_line_idx = None
for i, line in enumerate(lines):
    if line.strip().startswith("const GEOJSON ="):
        geojson_line_idx = i
        break

geojson_str = lines[geojson_line_idx].strip()[len("const GEOJSON = "):]
if geojson_str.endswith(";"):
    geojson_str = geojson_str[:-1]
geojson = json.loads(geojson_str)

# Build area lookup
area_by_id = {}
for f in geojson["features"]:
    tid = f["properties"].get("TENEMENT_ID") or f["properties"].get("tenement_id") or ""
    area_by_id[tid] = polygon_area_km2(f["geometry"]["coordinates"])

# Recalculate cum_area_km2 as ONLY acquired area (no baseline)
acquired_so_far = set()
for i, evt in enumerate(events):
    for tid in (evt.get("tenement_ids") or []):
        acquired_so_far.add(tid)
    acquired_area = sum(area_by_id.get(tid, 0) for tid in acquired_so_far)

    old_area = evt.get("cum_area_km2", 0)
    evt["cum_area_km2"] = round(acquired_area, 1)

    if abs(old_area - acquired_area) > 0.5:
        print(f"  Event {i}: area {old_area} → {round(acquired_area, 1)}")

# Write back EVENTS only
new_events_json = json.dumps(events, separators=(",", ":"))
html = html.replace(m.group(0), f"const EVENTS = {new_events_json};")

with open(HTML_PATH, "w", encoding="utf-8") as f:
    f.write(html)

print(f"\nFixed. Final event 28 cum_area: {events[-1]['cum_area_km2']} km² (acquired only)")
print("UI will add baselineAreaKm2 on top for total display.")
