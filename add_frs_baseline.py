#!/usr/bin/env python3
"""
add_frs_baseline.py — Extract 72 missing FRS-owned tenement polygons from
DMIRS KMZ files and add them to the timeline map as baseline tenements.
"""

import json, re, os, zipfile, math
from xml.etree.ElementTree import iterparse

BASE = os.path.dirname(__file__)
HTML_PATH = os.path.join(BASE, "frs_tenement_timeline_map.html")
LIVE_KMZ = os.path.join(BASE, "ingestion/processed/maps/source/kml/Tenements_Live.kmz")
PENDING_KMZ = os.path.join(BASE, "ingestion/processed/maps/source/kml/Tenements_Pending.kmz")

# The 72 missing FRS tenements (normalised IDs)
MISSING_IDS = [
    "M77/98","M77/215","M77/216","M77/284","M77/285","M77/286",
    "M74/57","M74/58","M77/329","M77/335","M77/336","M77/389","M77/399",
    "M74/64","M74/65","M77/458","M74/81","M77/543","M77/545","M77/542",
    "M77/550","L77/104","L74/11","M77/568","M77/574","M74/90","M74/91",
    "M74/92","M77/583","M77/584","M77/585","M77/582","M77/586","M77/587",
    "M77/588","M77/589","L77/141","L74/12","M77/911","M77/912","L74/25",
    "L77/182","L77/197","L74/44","L77/203","L77/204","E29/638","G70/226",
    "G70/231","L70/111","E77/1773","E74/470","E77/1865","E74/603",
    "E77/2523","E77/2524","P77/4496","P77/4497","P77/4499","P77/4500",
    "P77/4501","G77/135","L77/357","E77/3047","E77/3048","E77/3049",
    "E77/3106","E74/771","E77/3147","E74/810","E77/3213","P29/2729",
]

# Build KML-format lookup: "M77/98" -> "M 77/98" (add space after prefix letter(s))
def to_kml_id(norm_id):
    m = re.match(r'([A-Z]+)(\d+/\d+)', norm_id)
    if not m:
        return norm_id
    return f"{m.group(1)} {m.group(2)}"

kml_lookup = {}
for nid in MISSING_IDS:
    kid = to_kml_id(nid)
    kml_lookup[kid] = nid
    # Also handle -I suffix variant
    kml_lookup[kid + "-I"] = nid

print(f"Looking for {len(MISSING_IDS)} tenements...")

# ── Parse KML coordinates to GeoJSON ──
def parse_coords(coord_text):
    """Convert KML coordinate string to GeoJSON coordinate ring."""
    ring = []
    for part in coord_text.strip().split():
        vals = part.split(",")
        lon, lat = float(vals[0]), float(vals[1])
        ring.append([lon, lat])
    return ring

def extract_from_kmz(kmz_path, lookup, found_features):
    """Stream-parse a KMZ file and extract matching placemarks."""
    ns = "{http://www.opengis.net/kml/2.2}"

    with zipfile.ZipFile(kmz_path) as z:
        kml_name = [n for n in z.namelist() if n.endswith('.kml')][0]
        print(f"  Parsing {kml_name} from {os.path.basename(kmz_path)}...")

        with z.open(kml_name) as kml_file:
            current_name = None
            in_placemark = False
            placemark_data = None
            count = 0

            for event, elem in iterparse(kml_file, events=["start", "end"]):
                tag = elem.tag.replace(ns, "")

                if event == "start" and tag == "Placemark":
                    in_placemark = True
                    placemark_data = {"coords": [], "name": None}

                elif event == "end" and tag == "name" and in_placemark:
                    placemark_data["name"] = elem.text.strip() if elem.text else ""

                elif event == "end" and tag == "coordinates" and in_placemark:
                    if elem.text:
                        placemark_data["coords"].append(parse_coords(elem.text))

                elif event == "end" and tag == "Placemark":
                    name = placemark_data["name"]
                    if name in lookup and lookup[name] not in found_features:
                        norm_id = lookup[name]
                        rings = placemark_data["coords"]

                        if len(rings) == 1:
                            geometry = {"type": "Polygon", "coordinates": rings}
                        else:
                            geometry = {"type": "MultiPolygon", "coordinates": [[r] for r in rings]}

                        # Determine lease type from ID
                        prefix = re.match(r'[A-Z]+', norm_id).group()
                        type_names = {
                            "M": "Mining Lease", "E": "Exploration Licence",
                            "P": "Prospecting Licence", "L": "Miscellaneous Licence",
                            "G": "General Purpose Lease"
                        }

                        feature = {
                            "type": "Feature",
                            "properties": {
                                "tenement_id": norm_id,
                                "tenement_display": norm_id,
                                "lease_type": type_names.get(prefix, ""),
                                "is_approximate": False,
                            },
                            "geometry": geometry
                        }
                        found_features[norm_id] = feature
                        count += 1

                    in_placemark = False
                    placemark_data = None

                    # Clear element to save memory
                    elem.clear()
                elif event == "end":
                    elem.clear()

    print(f"  Found {count} tenements in {os.path.basename(kmz_path)}")

# ── Extract polygons from KMZ files ──
found = {}
extract_from_kmz(LIVE_KMZ, kml_lookup, found)
extract_from_kmz(PENDING_KMZ, kml_lookup, found)

print(f"\nTotal found: {len(found)} / {len(MISSING_IDS)}")
missing = set(MISSING_IDS) - set(found.keys())
if missing:
    print(f"Still missing: {missing}")

# ── Load existing HTML and add features ──
with open(HTML_PATH, "r", encoding="utf-8") as f:
    html = f.read()

# Find and parse GEOJSON line
lines = html.split('\n')
geo_line_idx = None
for li, line in enumerate(lines):
    if line.startswith('const GEOJSON ='):
        geo_line_idx = li
        break
if geo_line_idx is None:
    raise RuntimeError("Could not find GEOJSON line")

geo_line = lines[geo_line_idx].rstrip()
geo_json_str = geo_line[len('const GEOJSON = '):]
if geo_json_str.endswith(';'):
    geo_json_str = geo_json_str[:-1]
geojson = json.loads(geo_json_str)
print(f"\nGeoJSON features before: {len(geojson['features'])}")

# Check for duplicates
existing_ids = {feat["properties"].get("tenement_id", "") for feat in geojson["features"]}
added = 0
for nid, feat in found.items():
    if nid not in existing_ids:
        geojson["features"].append(feat)
        added += 1
    else:
        print(f"  Skipping {nid} (already in GeoJSON)")

print(f"Added {added} new features → {len(geojson['features'])} total")

# Rebuild the GEOJSON line
new_geo_str = json.dumps(geojson, ensure_ascii=False)
lines[geo_line_idx] = 'const GEOJSON = ' + new_geo_str + ';'
html = '\n'.join(lines)

# Write output
with open(HTML_PATH, "w", encoding="utf-8") as f:
    f.write(html)

print(f"\nDone! Wrote {len(html):,} chars to HTML")
print(f"Total GeoJSON features: {len(geojson['features'])}")

# Also update the augmented GeoJSON on disk
AUGMENTED = os.path.join(BASE, "ingestion/processed/maps/frs_tenements_augmented.geojson")
with open(AUGMENTED) as f:
    aug = json.load(f)
aug_ids = {feat["properties"].get("tenement_id", "") for feat in aug["features"]}
aug_added = 0
for nid, feat in found.items():
    if nid not in aug_ids:
        aug["features"].append(feat)
        aug_added += 1
with open(AUGMENTED, "w") as f:
    json.dump(aug, f)
print(f"Also added {aug_added} features to augmented GeoJSON ({len(aug['features'])} total)")
