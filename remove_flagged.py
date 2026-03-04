#!/usr/bin/env python3
"""Remove 16 flagged tenements from the timeline map:
- 4 Pilbara/NT outliers (in Event 8): E52/3718, E52/3719, E47/5019, E80/5313
- 3 expired Burracoppin (in Event 8): E70/3637, E70/3638, E70/5029
- 2 expired British Hill (in Event 4): P77/3309, P77/3310
- 2 expired North Ironcap (in Event 6): E77/39, P77/953
- 4 far-east baseline: E31/1409, E31/1410, E31/1411, E31/1440
- 1 far-north baseline: E29/638
"""
import json, re, math

HTML_PATH = "/Users/alfredlewis/Documents/Forrestania Resources/frs_tenement_timeline_map.html"
AUGMENTED_PATH = "/Users/alfredlewis/Documents/Forrestania Resources/ingestion/processed/maps/frs_tenements_augmented.geojson"

# All 16 tenements to remove
REMOVE_IDS = {
    # Pilbara/NT outliers (Event 8 - Burracoppin)
    "E52/3718", "E52/3719", "E47/5019", "E80/5313",
    # Expired Burracoppin (Event 8)
    "E70/3637", "E70/3638", "E70/5029",
    # Expired British Hill (Event 4)
    "P77/3309", "P77/3310",
    # Expired North Ironcap (Event 6)
    "E77/39", "P77/953",
    # Far-east baseline
    "E31/1409", "E31/1410", "E31/1411", "E31/1440",
    # Far-north baseline
    "E29/638",
}

def polygon_area_km2(coords):
    """Compute area using the Shoelace formula with latitude-adjusted degrees."""
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
    area_km2 = area * km_per_deg_lat * km_per_deg_lon
    return area_km2

# Read HTML
with open(HTML_PATH, "r", encoding="utf-8") as f:
    html = f.read()

print(f"HTML size: {len(html):,} chars")

# Extract EVENTS
m = re.search(r"const EVENTS = (\[.*?\]);\s*$", html, re.MULTILINE)
if not m:
    raise RuntimeError("Could not find EVENTS")
events = json.loads(m.group(1))
print(f"Found {len(events)} events")

# Extract GEOJSON (line-based search)
lines = html.split("\n")
geojson_line_idx = None
for i, line in enumerate(lines):
    if line.strip().startswith("const GEOJSON ="):
        geojson_line_idx = i
        break
if geojson_line_idx is None:
    raise RuntimeError("Could not find GEOJSON line")

geojson_str = lines[geojson_line_idx].strip()
geojson_str = geojson_str[len("const GEOJSON = "):]
if geojson_str.endswith(";"):
    geojson_str = geojson_str[:-1]
geojson = json.loads(geojson_str)
print(f"Found {len(geojson['features'])} GeoJSON features")

# --- Remove features from GEOJSON ---
original_count = len(geojson["features"])
kept_features = []
removed_features = []
for f in geojson["features"]:
    tid = f["properties"].get("TENEMENT_ID") or f["properties"].get("tenement_id") or ""
    if tid in REMOVE_IDS:
        removed_features.append(tid)
    else:
        kept_features.append(f)

geojson["features"] = kept_features
print(f"Removed {len(removed_features)} features: {sorted(removed_features)}")
print(f"Remaining: {len(kept_features)} features")

# Build area lookup for remaining features
area_by_id = {}
for f in kept_features:
    tid = f["properties"].get("TENEMENT_ID") or f["properties"].get("tenement_id") or ""
    area_by_id[tid] = polygon_area_km2(f["geometry"]["coordinates"])

# --- Update EVENTS ---
# Collect ALL tenement_ids referenced by ALL events (to determine baseline)
all_event_ids = set()
for evt in events:
    for tid in (evt.get("tenement_ids") or []):
        all_event_ids.add(tid)

# Remove flagged IDs from events
events_modified = []
for i, evt in enumerate(events):
    old_ids = evt.get("tenement_ids") or []
    old_new = evt.get("new_ids") or []

    new_ids_list = [tid for tid in old_ids if tid not in REMOVE_IDS]
    new_new_list = [tid for tid in old_new if tid not in REMOVE_IDS]

    removed_from_event = set(old_ids) - set(new_ids_list)
    if removed_from_event:
        events_modified.append(f"  Event {i} ({evt['title'][:40]}): removed {sorted(removed_from_event)}")

    evt["tenement_ids"] = new_ids_list
    evt["new_ids"] = new_new_list

if events_modified:
    print("Modified events:")
    for em in events_modified:
        print(em)

# Recalculate cum_tenements and cum_area_km2 for all events
# baseline IDs = feature IDs NOT in any event's tenement_ids
remaining_event_ids = set()
for evt in events:
    for tid in (evt.get("tenement_ids") or []):
        remaining_event_ids.add(tid)

remaining_feature_ids = set()
for f in kept_features:
    tid = f["properties"].get("TENEMENT_ID") or f["properties"].get("tenement_id") or ""
    remaining_feature_ids.add(tid)

baseline_ids = remaining_feature_ids - remaining_event_ids
baseline_area = sum(area_by_id.get(tid, 0) for tid in baseline_ids)
print(f"\nBaseline: {len(baseline_ids)} tenements, {baseline_area:.1f} km²")

# Recalculate cumulative values
acquired_so_far = set()
for i, evt in enumerate(events):
    for tid in (evt.get("tenement_ids") or []):
        acquired_so_far.add(tid)
    cum_acquired = len(acquired_so_far)
    cum_area = baseline_area + sum(area_by_id.get(tid, 0) for tid in acquired_so_far)

    old_cum = evt.get("cum_tenements", 0)
    old_area = evt.get("cum_area_km2", 0)

    evt["cum_tenements"] = cum_acquired
    evt["cum_area_km2"] = round(cum_area, 1)

    if old_cum != cum_acquired or abs(old_area - cum_area) > 0.5:
        print(f"  Event {i}: tenements {old_cum} → {cum_acquired}, area {old_area} → {round(cum_area, 1)}")

# --- Write back to HTML ---
# Replace EVENTS
new_events_json = json.dumps(events, separators=(",", ":"))
old_events_match = m.group(0)
new_events_line = f"const EVENTS = {new_events_json};"
html = html.replace(old_events_match, new_events_line)

# Replace GEOJSON line
new_geojson_json = json.dumps(geojson, separators=(",", ":"))
new_geojson_line = f"const GEOJSON = {new_geojson_json};"
lines = html.split("\n")
lines[geojson_line_idx] = new_geojson_line
html = "\n".join(lines)

# Also update baselineAreaKm2 in the JS
# Find the line: var baselineAreaKm2 = Math.round(...)
old_baseline_pattern = re.search(r"baselineAreaKm2\s*=\s*Math\.round\(\s*[\d.]+\s*\)", html)
if old_baseline_pattern:
    html = html[:old_baseline_pattern.start()] + f"baselineAreaKm2 = Math.round({baseline_area:.1f})" + html[old_baseline_pattern.end():]
    print(f"Updated baselineAreaKm2 = {round(baseline_area)}")

# Update baseline count if hardcoded
# Look for pattern like: baselineIds.length should compute dynamically, but check
old_baseline_count = re.search(r"var\s+baselineCount\s*=\s*\d+", html)
if old_baseline_count:
    html = html[:old_baseline_count.start()] + f"var baselineCount = {len(baseline_ids)}" + html[old_baseline_count.end():]

with open(HTML_PATH, "w", encoding="utf-8") as f:
    f.write(html)

print(f"\nFinal HTML: {len(html):,} chars")
print(f"Total features: {len(kept_features)}")
print(f"Baseline: {len(baseline_ids)}")
print(f"Acquired: {len(remaining_event_ids)}")

# Also update augmented GeoJSON
try:
    with open(AUGMENTED_PATH, "r", encoding="utf-8") as f:
        aug = json.load(f)

    old_aug_count = len(aug["features"])
    aug["features"] = [
        f for f in aug["features"]
        if (f["properties"].get("TENEMENT_ID") or f["properties"].get("tenement_id") or "") not in REMOVE_IDS
    ]
    new_aug_count = len(aug["features"])

    with open(AUGMENTED_PATH, "w", encoding="utf-8") as f:
        json.dump(aug, f)

    print(f"\nAugmented GeoJSON: {old_aug_count} → {new_aug_count} features")
except Exception as e:
    print(f"Warning: could not update augmented GeoJSON: {e}")

print("\nDone! Removed 16 flagged tenements successfully.")
