#!/usr/bin/env python3
"""Remove 80 non-FRS baseline tenements:
- 70 IGO Forrestania Limited tenements
- 10 third-party tenements (Outback Minerals, Bradley, MH Gold, Montague/SQM, Allen)
Keeps: 48 FRS + 2 joint FRS/Dynamic Metals = 50 genuine FRS baseline
"""
import json, re, math, csv

HTML_PATH = "/Users/alfredlewis/Documents/Forrestania Resources/frs_tenement_timeline_map.html"
AUGMENTED_PATH = "/Users/alfredlewis/Documents/Forrestania Resources/ingestion/processed/maps/frs_tenements_augmented.geojson"
CSV_PATH = "/Users/alfredlewis/Documents/Forrestania Resources/ingestion/processed/maps/source/csv/CurrentTenements.csv"

def normalize_csv_id(raw_id):
    """Convert CSV format 'M  7700098' to our format 'M77/98'."""
    raw_id = raw_id.strip()
    # Extract type letters, then digits
    i = 0
    while i < len(raw_id) and raw_id[i].isalpha():
        i += 1
    ttype = raw_id[:i]
    digits = raw_id[i:].strip()
    if len(digits) < 3:
        return raw_id
    district = digits[:2]
    seq = str(int(digits[2:]))  # strip leading zeros
    return f"{ttype}{district}/{seq}"

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

# --- Step 1: Build the list of FRS-owned tenement IDs from DMIRS ---
frs_ids = set()
with open(CSV_PATH, "r", encoding="latin-1") as f:
    reader = csv.DictReader(f)
    for row in reader:
        holder = row.get("REGISTERED_HOLDER", "")
        if "FORRESTANIA RESOURCES" in holder.upper():
            norm_id = normalize_csv_id(row["TENEMENT_ID"])
            frs_ids.add(norm_id)

print(f"FRS-registered tenements in DMIRS: {len(frs_ids)}")

# Also include Dynamic Metals joint holdings (E77/2701, E77/2887 are FRS co-held)
# These will be caught because holder contains "FORRESTANIA RESOURCES"

# --- Step 2: Read HTML ---
with open(HTML_PATH, "r", encoding="utf-8") as f:
    html = f.read()

print(f"HTML size: {len(html):,} chars")

# Extract EVENTS
m = re.search(r"const EVENTS = (\[.*?\]);\s*$", html, re.MULTILINE)
if not m:
    raise RuntimeError("Could not find EVENTS")
events = json.loads(m.group(1))

# Extract GEOJSON
lines_list = html.split("\n")
geojson_line_idx = None
for i, line in enumerate(lines_list):
    if line.strip().startswith("const GEOJSON ="):
        geojson_line_idx = i
        break
if geojson_line_idx is None:
    raise RuntimeError("Could not find GEOJSON line")

geojson_str = lines_list[geojson_line_idx].strip()[len("const GEOJSON = "):]
if geojson_str.endswith(";"):
    geojson_str = geojson_str[:-1]
geojson = json.loads(geojson_str)
print(f"Current features: {len(geojson['features'])}")

# --- Step 3: Identify which features to keep ---
# All event-acquired tenements stay
all_event_ids = set()
for evt in events:
    for tid in (evt.get("tenement_ids") or []):
        all_event_ids.add(tid)

kept_features = []
removed_features = []
removed_owners = {}

for f in geojson["features"]:
    tid = f["properties"].get("TENEMENT_ID") or f["properties"].get("tenement_id") or ""

    if tid in all_event_ids:
        # Acquired via story event — always keep
        kept_features.append(f)
    elif tid in frs_ids:
        # Baseline AND FRS-registered — keep
        kept_features.append(f)
    else:
        # Baseline but NOT FRS-registered — remove
        removed_features.append(tid)
        # Try to find the owner from CSV
        removed_owners[tid] = "unknown"
        kept_features_pass = False

if not removed_features:
    # Need to re-check - maybe the logic above has a bug
    print("WARNING: No features to remove!")
else:
    print(f"\nRemoving {len(removed_features)} non-FRS baseline features:")
    for tid in sorted(removed_features):
        print(f"  {tid}")

# Actually redo properly - the loop above has an issue
kept_features = []
removed_features = []

for f in geojson["features"]:
    tid = f["properties"].get("TENEMENT_ID") or f["properties"].get("tenement_id") or ""

    if tid in all_event_ids:
        kept_features.append(f)
    elif tid in frs_ids:
        kept_features.append(f)
    else:
        removed_features.append(tid)

geojson["features"] = kept_features
print(f"\nRemoved {len(removed_features)} non-FRS baseline tenements")
print(f"Remaining features: {len(kept_features)}")

# Count baseline vs acquired in remaining
remaining_baseline = [f for f in kept_features
                      if (f["properties"].get("TENEMENT_ID") or f["properties"].get("tenement_id") or "") not in all_event_ids]
remaining_acquired = [f for f in kept_features
                      if (f["properties"].get("TENEMENT_ID") or f["properties"].get("tenement_id") or "") in all_event_ids]
print(f"  Baseline: {len(remaining_baseline)}")
print(f"  Acquired: {len(remaining_acquired)}")

# --- Step 4: Recalculate areas ---
area_by_id = {}
for f in kept_features:
    tid = f["properties"].get("TENEMENT_ID") or f["properties"].get("tenement_id") or ""
    area_by_id[tid] = polygon_area_km2(f["geometry"]["coordinates"])

remaining_feature_ids = set()
for f in kept_features:
    tid = f["properties"].get("TENEMENT_ID") or f["properties"].get("tenement_id") or ""
    remaining_feature_ids.add(tid)

baseline_ids = remaining_feature_ids - all_event_ids
baseline_area = sum(area_by_id.get(tid, 0) for tid in baseline_ids)
print(f"\nNew baseline: {len(baseline_ids)} tenements, {baseline_area:.1f} km²")

# Recalculate cum_area_km2 (acquired area only, UI adds baseline separately)
acquired_so_far = set()
for i, evt in enumerate(events):
    for tid in (evt.get("tenement_ids") or []):
        acquired_so_far.add(tid)
    acquired_area = sum(area_by_id.get(tid, 0) for tid in acquired_so_far)
    evt["cum_area_km2"] = round(acquired_area, 1)

# cum_tenements stays the same (counts acquired only)

print(f"Final event area (acquired only): {events[-1]['cum_area_km2']} km²")
print(f"Total area at final step: {events[-1]['cum_area_km2'] + baseline_area:.1f} km²")

# --- Step 5: Write back ---
# Replace EVENTS
new_events_json = json.dumps(events, separators=(",", ":"))
html = html.replace(m.group(0), f"const EVENTS = {new_events_json};")

# Replace GEOJSON
new_geojson_json = json.dumps(geojson, separators=(",", ":"))
lines_list = html.split("\n")
lines_list[geojson_line_idx] = f"const GEOJSON = {new_geojson_json};"
html = "\n".join(lines_list)

# Update baselineAreaKm2
old_baseline_pattern = re.search(r"baselineAreaKm2\s*=\s*Math\.round\(\s*[\d.]+\s*\)", html)
if old_baseline_pattern:
    html = html[:old_baseline_pattern.start()] + f"baselineAreaKm2 = Math.round({baseline_area:.1f})" + html[old_baseline_pattern.end():]
    print(f"Updated baselineAreaKm2 = {round(baseline_area)}")

with open(HTML_PATH, "w", encoding="utf-8") as f:
    f.write(html)
print(f"\nFinal HTML: {len(html):,} chars")

# Also update augmented GeoJSON
try:
    with open(AUGMENTED_PATH, "r", encoding="utf-8") as f:
        aug = json.load(f)

    removed_set = set(removed_features)
    old_count = len(aug["features"])
    aug["features"] = [
        f for f in aug["features"]
        if (f["properties"].get("TENEMENT_ID") or f["properties"].get("tenement_id") or "") not in removed_set
    ]

    with open(AUGMENTED_PATH, "w", encoding="utf-8") as f:
        json.dump(aug, f)
    print(f"Augmented GeoJSON: {old_count} → {len(aug['features'])} features")
except Exception as e:
    print(f"Warning: could not update augmented GeoJSON: {e}")

print("\nDone!")
