#!/usr/bin/env python3
"""
Add two new acquisitions to the timeline map:
1. Enrich existing Event 27 (Goldzone Mt Dimer completion) with tenement IDs
2. Insert new MacPhersons Reward event (Feb 16) between current events 27 and 28
3. Extract polygon geometries from DMIRS KMZ files
4. Recalculate cumulative metrics
"""
import json, re, math, zipfile
from xml.etree.ElementTree import iterparse

HTML_PATH = "/Users/alfredlewis/Documents/Forrestania Resources/frs_tenement_timeline_map.html"
KMZ_LIVE = "/Users/alfredlewis/Documents/Forrestania Resources/ingestion/processed/maps/source/kml/Tenements_Live.kmz"
KMZ_PENDING = "/Users/alfredlewis/Documents/Forrestania Resources/ingestion/processed/maps/source/kml/Tenements_Pending.kmz"

# ── Tenement IDs for each acquisition ──
# Goldzone Mt Dimer / Mt Jackson / Johnson Range (enriching existing event 27)
GOLDZONE_IDS = [
    "E15/1764", "E16/624",
    "E77/2742", "E77/2749", "E77/2750",
    "E77/3005", "E77/3125",
    "M77/1295", "M77/1299",
    "P15/6720", "P77/4611"
]

# MacPhersons Reward (new event)
# Normalize: M15/0040 → M15/40, L15/0312 → L15/312, etc.
MACPHERSONS_IDS = [
    "M15/40", "M15/128", "M15/133", "M15/147", "M15/148", "M15/1808",
    "P15/6071", "P15/6085",
    "L15/312", "L15/352", "L15/355", "L15/375"
]

ALL_NEW_IDS = set(GOLDZONE_IDS + MACPHERSONS_IDS)

def normalize_fmt_id(fmt_id):
    """Convert KML 'Formatted Tenement ID' like 'E 29/1158' or 'M 15/40' to 'E29/1158' or 'M15/40'."""
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
print(f"  {len(events)} events")

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
print(f"  Need polygons for {len(needed_ids)} new IDs: {sorted(needed_ids)}")

# ── Step 2: Extract polygons from KMZ ──
print("\nStep 2: Extracting polygons from KMZ...")
found_live = extract_tenements_from_kmz(KMZ_LIVE, needed_ids)
print(f"  Found in Live: {len(found_live)}")

remaining = needed_ids - set(found_live.keys())
if remaining:
    print(f"  Searching Pending for {len(remaining)} remaining...")
    found_pending = extract_tenements_from_kmz(KMZ_PENDING, remaining)
    print(f"  Found in Pending: {len(found_pending)}")
    found_live.update(found_pending)

still_missing = needed_ids - set(found_live.keys())
if still_missing:
    print(f"  WARNING: {len(still_missing)} not found: {sorted(still_missing)}")

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

# ── Step 3: Update Event 27 (Goldzone) with tenement IDs ──
print("\nStep 3: Enriching Event 27 (Goldzone)...")
evt27 = events[27]
print(f"  Current title: {evt27['title'][:60]}")
print(f"  Current tenement_ids: {evt27.get('tenement_ids', [])}")

evt27["title"] = "Mt Dimer, Mt Jackson & Johnson Range acquisition completes (Goldzone Investments)"
evt27["strategic_impact"] = (
    "Goldzone deal formally completes \u2014 conditions precedent satisfied. FRS now holds 100% of the mineral rights "
    "(excluding iron ore) across three Eastern Goldfields project areas: Mt Dimer, Mt Jackson, and Johnson Range. "
    "Original terms: $600K cash + $3.55M in shares at completion, plus up to $3M in JORC resource milestones. "
    "Tenements are strategically positioned in proven gold corridors near the wholly-owned Lake Johnston 1.5 Mtpa "
    "processing plant, strengthening the medium-term feed pipeline toward gold production."
)
evt27["tenement_ids"] = GOLDZONE_IDS
evt27["new_ids"] = GOLDZONE_IDS
evt27["tenements_added_story"] = len(GOLDZONE_IDS)
evt27["counterparties"] = "Goldzone Investments Pty Ltd"
evt27["consideration"] = "$600K cash + $3.55M in shares + up to $3M milestones"
evt27["project"] = "Mt Dimer / Mt Jackson / Johnson Range"
evt27["confidence"] = "high"
print(f"  Updated with {len(GOLDZONE_IDS)} tenement IDs")

# ── Step 4: Insert MacPhersons Reward as new event ──
print("\nStep 4: Inserting MacPhersons Reward event...")

macphersons_event = {
    "idx": 28,
    "date": "2026-02-16",
    "phase": 5,
    "phase_name": "Production Readiness",
    "phase_full": "5 \u2013 Production Readiness",
    "title": "MacPhersons Reward acquisition binding HoA (Beacon Minerals / BCN)",
    "strategic_impact": (
        "Binding HoA to acquire 100% of MacPhersons Reward Pty Ltd from Beacon Mining (ASX:BCN subsidiary) "
        "for $5M cash + 36M FRS shares at $0.38 (~$18.68M total). MacPhersons holds six granted Mining Leases, "
        "two PLs and four Misc Licences in the Coolgardie gold district with historic production of ~60K oz @ 2.94 g/t. "
        "Consolidates granted mining tenure directly south of FRS's existing Coolgardie Hub (including recently "
        "acquired Gibraltar), supporting the transition from explorer to near-term producer with proximity to "
        "multiple processing plants (Three Mile Hill, Greenfields, Burbanks)."
    ),
    "tenement_ids": MACPHERSONS_IDS,
    "missing_ids": ["P15/6409", "M15/1921", "M15/1925"],
    "new_ids": MACPHERSONS_IDS,
    "tenements_added_story": len(MACPHERSONS_IDS),
    "counterparties": "Beacon Mining Pty Ltd (Beacon Minerals Limited, ASX:BCN)",
    "consideration": "$5M cash + 36M shares @ $0.38 (~$18.68M total)",
    "project": "MacPhersons Reward (Coolgardie Hub)",
    "confidence": "high",
    "cum_tenements": 0,  # Will recalculate
    "cum_area_km2": 0,   # Will recalculate
    "is_kula": False
}

# Insert at position 28 (between current 27 and 28)
# Current event 28 (Westgold OPA, Feb 19) becomes 29
events.insert(28, macphersons_event)

# Renumber idx
for i, evt in enumerate(events):
    evt["idx"] = i

print(f"  Inserted at idx 28. Total events: {len(events)}")
print(f"  Event 29 is now: {events[29]['title'][:50]}")

# ── Step 5: Recalculate cumulative metrics ──
print("\nStep 5: Recalculating cumulative metrics...")

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
print(f"  Baseline: {len(baseline_ids)} tenements, {baseline_area:.1f} km²")

# Recalculate cum_tenements and cum_area_km2
acquired_so_far = set()
for i, evt in enumerate(events):
    for tid in (evt.get("tenement_ids") or []):
        acquired_so_far.add(tid)
    evt["cum_tenements"] = len(acquired_so_far)
    acquired_area = sum(area_by_id.get(tid, 0) for tid in acquired_so_far)
    evt["cum_area_km2"] = round(acquired_area, 1)

print(f"  Final event: {events[-1]['cum_tenements']} acquired, {events[-1]['cum_area_km2']} km² acquired area")
print(f"  Total at final step: {events[-1]['cum_area_km2'] + baseline_area:.1f} km²")

# ── Step 6: Update goToStep references ──
# The ore transport was on step 28, now it's step 29
# The mill marker was >= 12, stays the same
print("\nStep 6: Updating goToStep step references...")

# Ore transport: currentStep >= 28 → currentStep >= 29
html_before = html
html = html.replace(
    "if (currentStep >= 28) showOreTransport(); else hideOreTransport();",
    "if (currentStep >= 29) showOreTransport(); else hideOreTransport();"
)
if html != html_before:
    print("  Updated ore transport: >= 28 → >= 29")

# Zoom to transport: currentStep === 28 → currentStep === 29
html = html.replace(
    "} else if (currentStep === 28 && oreTransportVisible) {",
    "} else if (currentStep === 29 && oreTransportVisible) {"
)

# ── Step 7: Write back to HTML ──
print("\nStep 7: Writing HTML...")

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

with open(HTML_PATH, "w", encoding="utf-8") as f:
    f.write(html)

print(f"  HTML: {len(html):,} chars")
print(f"  Features: {len(geojson['features'])}")
print(f"  Events: {len(events)}")
print(f"\nDone!")
