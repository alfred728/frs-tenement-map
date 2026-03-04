#!/usr/bin/env python3
"""
Rebuild FRS baseline tenements correctly.
Current state: HTML has 61 acquired features, 0 baseline.
This script extracts FRS-registered tenements directly from the KMZ by matching
on holder name, then filters to get only baseline ones.
"""
import json, re, math, csv, zipfile
from xml.etree.ElementTree import iterparse

HTML_PATH = "/Users/alfredlewis/Documents/Forrestania Resources/frs_tenement_timeline_map.html"
AUGMENTED_PATH = "/Users/alfredlewis/Documents/Forrestania Resources/ingestion/processed/maps/frs_tenements_augmented.geojson"
CSV_PATH = "/Users/alfredlewis/Documents/Forrestania Resources/ingestion/processed/maps/source/csv/CurrentTenements.csv"
KMZ_LIVE = "/Users/alfredlewis/Documents/Forrestania Resources/ingestion/processed/maps/source/kml/Tenements_Live.kmz"
KMZ_PENDING = "/Users/alfredlewis/Documents/Forrestania Resources/ingestion/processed/maps/source/kml/Tenements_Pending.kmz"

# IDs to exclude (previously removed)
EXCLUDED_IDS = {
    "E52/3718", "E52/3719", "E47/5019", "E80/5313",
    "E70/3637", "E70/3638", "E70/5029",
    "P77/3309", "P77/3310",
    "E77/39", "P77/953",
    "E31/1409", "E31/1410", "E31/1411", "E31/1440",
    "E29/638",
}

def normalize_fmt_id(fmt_id):
    """Convert KML 'Formatted Tenement ID' like 'E 29/1158' or 'E 77/1773-I' to 'E29/1158' or 'E77/1773'."""
    fmt_id = fmt_id.strip()
    # Remove -I suffix
    if fmt_id.endswith('-I'):
        fmt_id = fmt_id[:-2]
    # Remove space between type letters and district number
    # E 29/1158 -> E29/1158
    parts = fmt_id.split(' ', 1)
    if len(parts) == 2:
        return parts[0] + parts[1]
    return fmt_id

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

def extract_frs_from_kmz(kmz_path, exclude_ids, existing_ids):
    """Extract all FRS-holder tenements from KMZ with their polygons."""
    features = []
    current_data = {}
    current_coords = None

    with zipfile.ZipFile(kmz_path) as zf:
        kml_name = [n for n in zf.namelist() if n.endswith('.kml')][0]
        with zf.open(kml_name) as f:
            for event, elem in iterparse(f, events=('end',)):
                tag = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag

                if tag == 'SimpleData':
                    name = elem.get('name', '')
                    val = (elem.text or '').strip()
                    current_data[name] = val

                elif tag == 'coordinates' and elem.text:
                    coords_text = elem.text.strip()
                    ring = []
                    for pt in coords_text.split():
                        parts = pt.split(',')
                        if len(parts) >= 2:
                            ring.append([float(parts[0]), float(parts[1])])
                    if len(ring) >= 3:
                        current_coords = ring

                elif tag == 'Placemark':
                    holder1 = current_data.get('Tenement Holder 1', '').upper()
                    all_holders = current_data.get('All Tenement Holders', '').upper()

                    if 'FORRESTANIA RESOURCES' in holder1 or 'FORRESTANIA RESOURCES' in all_holders:
                        fmt_id = current_data.get('Formatted Tenement ID', '')
                        norm_id = normalize_fmt_id(fmt_id)

                        if norm_id and norm_id not in exclude_ids and norm_id not in existing_ids and current_coords:
                            features.append({
                                "type": "Feature",
                                "properties": {
                                    "TENEMENT_ID": norm_id,
                                    "tenement_id": norm_id,
                                    "source": "DMIRS_FRS_baseline"
                                },
                                "geometry": {
                                    "type": "Polygon",
                                    "coordinates": [current_coords]
                                }
                            })

                    current_data = {}
                    current_coords = None

                elem.clear()

    return features

# --- Step 1: Read current HTML ---
print("Step 1: Reading HTML...")
with open(HTML_PATH, "r", encoding="utf-8") as f:
    html = f.read()

m = re.search(r"const EVENTS = (\[.*?\]);\s*$", html, re.MULTILINE)
events = json.loads(m.group(1))

lines_list = html.split("\n")
geojson_line_idx = None
for i, line in enumerate(lines_list):
    if line.strip().startswith("const GEOJSON ="):
        geojson_line_idx = i
        break

geojson_str = lines_list[geojson_line_idx].strip()[len("const GEOJSON = "):]
if geojson_str.endswith(";"):
    geojson_str = geojson_str[:-1]
geojson = json.loads(geojson_str)
print(f"  Current features: {len(geojson['features'])}")

# Get all existing IDs (acquired + any remaining baseline)
existing_ids = set()
for f in geojson["features"]:
    tid = f["properties"].get("TENEMENT_ID") or f["properties"].get("tenement_id") or ""
    existing_ids.add(tid)

all_event_ids = set()
for evt in events:
    for tid in (evt.get("tenement_ids") or []):
        all_event_ids.add(tid)

print(f"  Existing IDs: {len(existing_ids)}")
print(f"  Event IDs: {len(all_event_ids)}")

# --- Step 2: Extract FRS features from KMZ ---
print("\nStep 2: Extracting FRS features from KMZ...")
# Exclude: previously removed + already in map + acquired (we only want baseline)
all_exclude = EXCLUDED_IDS | existing_ids | all_event_ids

frs_live = extract_frs_from_kmz(KMZ_LIVE, all_exclude, existing_ids)
print(f"  Found in Live KMZ: {len(frs_live)}")

# Update existing_ids with what we found
for f in frs_live:
    existing_ids.add(f["properties"]["TENEMENT_ID"])

frs_pending = extract_frs_from_kmz(KMZ_PENDING, all_exclude, existing_ids)
print(f"  Found in Pending KMZ: {len(frs_pending)}")

all_new = frs_live + frs_pending
print(f"  Total new baseline features: {len(all_new)}")
for f in sorted(all_new, key=lambda x: x["properties"]["TENEMENT_ID"]):
    print(f"    {f['properties']['TENEMENT_ID']}")

# --- Step 3: Add to GeoJSON ---
geojson["features"].extend(all_new)
print(f"\n  Total features now: {len(geojson['features'])}")

# --- Step 4: Recalculate areas ---
area_by_id = {}
for f in geojson["features"]:
    tid = f["properties"].get("TENEMENT_ID") or f["properties"].get("tenement_id") or ""
    area_by_id[tid] = polygon_area_km2(f["geometry"]["coordinates"])

all_feature_ids = set()
for f in geojson["features"]:
    tid = f["properties"].get("TENEMENT_ID") or f["properties"].get("tenement_id") or ""
    all_feature_ids.add(tid)

baseline_ids = all_feature_ids - all_event_ids
baseline_area = sum(area_by_id.get(tid, 0) for tid in baseline_ids)
print(f"\n  Baseline: {len(baseline_ids)} tenements, {baseline_area:.1f} km²")

# Recalculate cum_area_km2 (acquired only)
acquired_so_far = set()
for i, evt in enumerate(events):
    for tid in (evt.get("tenement_ids") or []):
        acquired_so_far.add(tid)
    acquired_area = sum(area_by_id.get(tid, 0) for tid in acquired_so_far)
    evt["cum_area_km2"] = round(acquired_area, 1)

print(f"  Final acquired area: {events[-1]['cum_area_km2']} km²")
print(f"  Total at step 29: {events[-1]['cum_area_km2'] + baseline_area:.1f} km²")

# --- Step 5: Write back to HTML ---
print("\nStep 5: Writing HTML...")
new_events_json = json.dumps(events, separators=(",", ":"))
html = html.replace(m.group(0), f"const EVENTS = {new_events_json};")

new_geojson_json = json.dumps(geojson, separators=(",", ":"))
lines_list = html.split("\n")
lines_list[geojson_line_idx] = f"const GEOJSON = {new_geojson_json};"
html = "\n".join(lines_list)

# Update baselineAreaKm2
old_baseline_pattern = re.search(r"baselineAreaKm2\s*=\s*Math\.round\(\s*[\d.]+\s*\)", html)
if old_baseline_pattern:
    html = html[:old_baseline_pattern.start()] + f"baselineAreaKm2 = Math.round({baseline_area:.1f})" + html[old_baseline_pattern.end():]

with open(HTML_PATH, "w", encoding="utf-8") as f:
    f.write(html)
print(f"  HTML: {len(html):,} chars")

# Update augmented GeoJSON
try:
    with open(AUGMENTED_PATH, "r", encoding="utf-8") as f:
        aug = json.load(f)
    aug["features"].extend(all_new)
    with open(AUGMENTED_PATH, "w", encoding="utf-8") as f:
        json.dump(aug, f)
    print(f"  Augmented GeoJSON: {len(aug['features'])} features")
except Exception as e:
    print(f"  Warning: {e}")

print(f"\nDone! Added {len(all_new)} FRS baseline tenements.")
print(f"Final: {len(geojson['features'])} total features ({len(baseline_ids)} baseline + {len(all_event_ids)} acquired)")
