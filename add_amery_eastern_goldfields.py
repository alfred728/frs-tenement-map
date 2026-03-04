#!/usr/bin/env python3
"""
Add Amery Holdings / Eastern Goldfields Hub consolidation announcement to the timeline map.

Announcement: 25 February 2026 — Further Consolidation of Eastern Goldfields Hub
Two Binding HoAs with Amery Holdings Pty Ltd:

Deal 1: E25/663
  - Consideration: $125,000 in FRS shares at 5-day VWAP
  - Milestone: $150K per 10,000 oz above 30,000 oz JORC resource

Deal 2: E28/3253, E28/3284, E28/3387, E28/3350, E28/3478, E28/3334, E28/3512
         + Applications E28/3411, E28/3490, E28/3540
  - Consideration: $300,000 in FRS shares at 5-day VWAP
  - Milestone: $150K per 10,000 oz above 30,000 oz JORC resource

Total: 11 tenements, $425K in shares + JORC milestones
"""
import json, re, math, zipfile
from xml.etree.ElementTree import iterparse

HTML_PATH = "/Users/alfredlewis/Documents/Forrestania Resources/frs_tenement_timeline_map.html"
KMZ_LIVE = "/Users/alfredlewis/Documents/Forrestania Resources/ingestion/processed/maps/source/kml/Tenements_Live.kmz"
KMZ_PENDING = "/Users/alfredlewis/Documents/Forrestania Resources/ingestion/processed/maps/source/kml/Tenements_Pending.kmz"

# ── Tenement IDs from announcement ──
AMERY_IDS = [
    # Deal 1
    "E25/663",
    # Deal 2 — granted
    "E28/3253",
    "E28/3284",
    "E28/3387",
    "E28/3350",
    "E28/3478",
    "E28/3334",
    "E28/3512",
    # Deal 2 — applications
    "E28/3411",
    "E28/3490",
    "E28/3540",
]

ALL_NEW_IDS = set(AMERY_IDS)

def normalize_fmt_id(fmt_id):
    """Convert KML 'Formatted Tenement ID' like 'E 29/1158' to 'E29/1158'."""
    fmt_id = fmt_id.strip()
    if fmt_id.endswith('-I'):
        fmt_id = fmt_id[:-2]
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

def extract_tenements_from_kmz(kmz_path, target_norm_ids):
    """Extract polygon geometries for specific tenement IDs from KMZ."""
    found = {}
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
                    fmt_id = current_data.get('Formatted Tenement ID', '')
                    norm_id = normalize_fmt_id(fmt_id)

                    if norm_id in target_norm_ids and norm_id not in found and current_coords:
                        found[norm_id] = current_coords

                    current_data = {}
                    current_coords = None
                elem.clear()

    return found

# ── Step 1: Read HTML ──
print("Step 1: Reading HTML...")
with open(HTML_PATH, "r", encoding="utf-8") as f:
    html = f.read()

m = re.search(r"const EVENTS = (\[.*?\]);\s*$", html, re.MULTILINE)
if not m:
    raise RuntimeError("Could not find EVENTS")
events = json.loads(m.group(1))
print(f"  {len(events)} events (last idx: {events[-1]['idx']}, date: {events[-1]['date']})")
print(f"  Last event: {events[-1]['title'][:60]}")

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
print(f"  {len(geojson['features'])} GeoJSON features")

# Check what IDs already exist
existing_ids = set()
for f in geojson["features"]:
    tid = f["properties"].get("TENEMENT_ID") or f["properties"].get("tenement_id") or ""
    existing_ids.add(tid)

needed_ids = ALL_NEW_IDS - existing_ids
already_have = ALL_NEW_IDS & existing_ids
if already_have:
    print(f"  Already have polygons for: {sorted(already_have)}")
print(f"  Need polygons for {len(needed_ids)} new IDs: {sorted(needed_ids)}")

# ── Step 2: Extract polygons from KMZ ──
print("\nStep 2: Extracting polygons from KMZ...")
found_live = extract_tenements_from_kmz(KMZ_LIVE, needed_ids)
print(f"  Found in Live: {len(found_live)} — {sorted(found_live.keys())}")

remaining = needed_ids - set(found_live.keys())
if remaining:
    print(f"  Searching Pending for {len(remaining)} remaining: {sorted(remaining)}")
    found_pending = extract_tenements_from_kmz(KMZ_PENDING, remaining)
    print(f"  Found in Pending: {len(found_pending)} — {sorted(found_pending.keys())}")
    found_live.update(found_pending)

still_missing = needed_ids - set(found_live.keys())
if still_missing:
    print(f"  WARNING: {len(still_missing)} not found in any KMZ: {sorted(still_missing)}")

# Create GeoJSON features for new polygons
new_features = []
for tid, ring in found_live.items():
    new_features.append({
        "type": "Feature",
        "properties": {
            "TENEMENT_ID": tid,
            "tenement_id": tid,
            "source": "DMIRS_acquisition_2026"
        },
        "geometry": {
            "type": "Polygon",
            "coordinates": [ring]
        }
    })

geojson["features"].extend(new_features)
print(f"  Added {len(new_features)} new features. Total: {len(geojson['features'])}")

# ── Step 3: Create new Amery/Eastern Goldfields event ──
print("\nStep 3: Creating Amery / Eastern Goldfields event...")

new_idx = len(events)  # Append at end
amery_event = {
    "idx": new_idx,
    "date": "2026-02-25",
    "phase": 5,
    "phase_name": "Production Readiness",
    "phase_full": "5 \u2013 Production Readiness",
    "title": "Eastern Goldfields Hub consolidation \u2014 11 ELs acquired from Amery Holdings",
    "strategic_impact": (
        "Two Binding HoAs with Amery Holdings Pty Ltd to consolidate the Eastern Goldfields Hub. "
        "Deal 1: E25/663 for $125K in FRS shares at 5-day VWAP. "
        "Deal 2: seven granted ELs (E28/3253, E28/3284, E28/3387, E28/3350, E28/3478, E28/3334, "
        "E28/3512) and three Applications (E28/3411, E28/3490, E28/3540) for $300K in FRS shares "
        "at 5-day VWAP. Both deals include JORC milestone payments of $150K per 10,000 oz above "
        "30,000 oz (at FRS election: cash or shares). The Eastern Goldfields Hub spans the Kalgoorlie, "
        "Kurnalpi, Burtville and Yamarna Terranes \u2014 proven gold corridors hosting major deposits "
        "(Super Pit, Paddington, Carosue Dam, Karonie). Combined $425K consideration continues the "
        "capital-preserving share-based acquisition strategy while expanding regional footprint "
        "north-east of the existing Menzies and Coolgardie hubs."
    ),
    "tenement_ids": AMERY_IDS,
    "missing_ids": list(still_missing) if still_missing else [],
    "new_ids": AMERY_IDS,
    "tenements_added_story": len(AMERY_IDS),
    "counterparties": "Amery Holdings Pty Ltd",
    "consideration": "$425K in FRS shares ($125K + $300K) + JORC milestones",
    "project": "Eastern Goldfields Hub",
    "confidence": "high",
    "cum_tenements": 0,   # Will recalculate
    "cum_area_km2": 0,    # Will recalculate
    "is_kula": False
}

events.append(amery_event)
print(f"  Inserted at idx {new_idx}. Total events: {len(events)}")

# ── Step 4: Recalculate cumulative metrics ──
print("\nStep 4: Recalculating cumulative metrics...")

# Build area lookup
area_by_id = {}
for f in geojson["features"]:
    tid = f["properties"].get("TENEMENT_ID") or f["properties"].get("tenement_id") or ""
    area_by_id[tid] = polygon_area_km2(f["geometry"]["coordinates"])

# Get all event IDs and baseline
all_event_ids = set()
for evt in events:
    for tid in (evt.get("tenement_ids") or []):
        all_event_ids.add(tid)

all_feature_ids = set()
for f in geojson["features"]:
    tid = f["properties"].get("TENEMENT_ID") or f["properties"].get("tenement_id") or ""
    all_feature_ids.add(tid)

baseline_ids = all_feature_ids - all_event_ids
baseline_area = sum(area_by_id.get(tid, 0) for tid in baseline_ids)
print(f"  Baseline: {len(baseline_ids)} tenements, {baseline_area:.1f} km\u00b2")

# Recalculate cum_tenements and cum_area_km2
acquired_so_far = set()
for i, evt in enumerate(events):
    for tid in (evt.get("tenement_ids") or []):
        acquired_so_far.add(tid)
    evt["cum_tenements"] = len(acquired_so_far)
    acquired_area = sum(area_by_id.get(tid, 0) for tid in acquired_so_far)
    evt["cum_area_km2"] = round(acquired_area, 1)

print(f"  Final event: {events[-1]['cum_tenements']} acquired tenements, {events[-1]['cum_area_km2']} km\u00b2 acquired area")
print(f"  Total at final step: {events[-1]['cum_area_km2'] + baseline_area:.1f} km\u00b2 (incl baseline)")

# Report new areas
for tid in AMERY_IDS:
    area = area_by_id.get(tid, 0)
    status = "\u2713" if area > 0 else "\u2717 NO POLYGON"
    print(f"    {tid}: {area:.1f} km\u00b2 {status}")

# ── Step 5: Write back to HTML ──
print("\nStep 5: Writing HTML...")

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
    print(f"  Updated baselineAreaKm2 to {baseline_area:.1f}")

with open(HTML_PATH, "w", encoding="utf-8") as f:
    f.write(html)

print(f"  HTML: {len(html):,} chars")
print(f"  Features: {len(geojson['features'])}")
print(f"  Events: {len(events)}")
print(f"\nDone! Amery / Eastern Goldfields event added as step {new_idx + 1}/{len(events)}")
