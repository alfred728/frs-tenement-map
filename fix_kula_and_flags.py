#!/usr/bin/env python3
"""
Fix Kula/GOZI event completeness + add DMIRS-only baseline flagging.

1. Extract 30 available Kula/GOZI polygon features from full_tenement_list.geojson
2. Add them to the HTML's inline GeoJSON
3. Add the missing tenement IDs to Event 15 (Kula acquisition)
4. Mark 10 DMIRS-only baseline tenements with _dmirs_only property

EL0822/24 (Malawi) is excluded — international licence, not relevant to WA map.
"""

import json
from pathlib import Path

HTML_PATH = Path(__file__).parent / "frs_tenement_timeline_map.html"
SOURCE_PATH = Path(__file__).parent / "ingestion" / "processed" / "maps" / "claude_handoff" / "full_tenement_list.geojson"

# Missing Kula direct tenements (excluding EL0822/24 — international)
KULA_DIRECT_MISSING = [
    'E77/2621', 'M77/0406', 'P77/4527', 'M77/1302', 'L77/0359',
    'E77/3231', 'E70/5660', 'E70/5452', 'E70/6603', 'E70/6626',
    'E70/6627', 'E28/3029'
]

# Missing GOZI subsidiary tenements
GOZI_MISSING = [
    'E15/1803', 'E15/1814', 'E15/2015', 'E16/0580', 'E16/0624',
    'E77/2301', 'E77/2435', 'E77/2554', 'E77/2636', 'E77/2758',
    'E77/2791', 'E77/2792', 'E77/2793', 'E77/2802', 'E77/2803',
    'E77/2814', 'E77/2822', 'E77/2865', 'E77/2866', 'E77/3193',
    'M57/0661', 'M77/1286', 'P26/4435', 'P77/4372', 'P77/4598'
]

ALL_KULA_MISSING = set(KULA_DIRECT_MISSING + GOZI_MISSING)

# 10 DMIRS-only baseline tenements that should get dashed borders
DMIRS_ONLY_IDS = {
    'E15/2159', 'E29/1321', 'E63/2557', 'E63/2558', 'E63/2559',
    'P16/3580', 'P16/3585', 'P16/3586', 'P16/3590', 'P77/4717'
}


def main():
    # --- Load source polygons ---
    print(f"Loading source polygons from {SOURCE_PATH.name}...")
    with open(SOURCE_PATH) as f:
        source = json.load(f)

    source_features = {}
    for feat in source['features']:
        tid = feat['properties'].get('tenement_id', feat['properties'].get('TENEMENT_ID', ''))
        if tid in ALL_KULA_MISSING:
            # Normalize properties
            props = dict(feat['properties'])
            if 'tenement_id' not in props and 'TENEMENT_ID' in props:
                props['tenement_id'] = props['TENEMENT_ID']
            feat['properties'] = props
            source_features[tid] = feat

    found_ids = set(source_features.keys())
    missing_ids = ALL_KULA_MISSING - found_ids
    print(f"  Found {len(found_ids)}/{len(ALL_KULA_MISSING)} Kula/GOZI polygons in source")
    if missing_ids:
        print(f"  Missing from source: {sorted(missing_ids)}")

    # --- Read HTML ---
    print(f"\nReading {HTML_PATH.name}...")
    html = HTML_PATH.read_text(encoding='utf-8')
    lines = html.split('\n')

    # Find GEOJSON and EVENTS lines
    geojson_line_idx = None
    events_line_idx = None
    for i, line in enumerate(lines):
        if 'const GEOJSON' in line and geojson_line_idx is None:
            geojson_line_idx = i
        if 'const EVENTS' in line and events_line_idx is None:
            events_line_idx = i

    print(f"  GEOJSON on line {geojson_line_idx + 1}, EVENTS on line {events_line_idx + 1}")

    # --- Parse GEOJSON ---
    geo_line = lines[geojson_line_idx]
    geo_prefix = geo_line[:geo_line.index('{')]
    geo_json_str = geo_line[len(geo_prefix):].rstrip().rstrip(';')
    geojson = json.loads(geo_json_str)
    before_features = len(geojson['features'])

    # Check which Kula/GOZI IDs are already in GeoJSON
    existing_geo_ids = set()
    for f in geojson['features']:
        tid = f['properties'].get('tenement_id', f['properties'].get('TENEMENT_ID', ''))
        if tid:
            existing_geo_ids.add(tid)

    # Add only features not already in GeoJSON
    added = 0
    for tid, feat in source_features.items():
        if tid not in existing_geo_ids:
            geojson['features'].append(feat)
            added += 1
            print(f"  + Added polygon: {tid}")
        else:
            print(f"  ~ Already in GeoJSON: {tid}")

    print(f"\n  GeoJSON: {before_features} → {len(geojson['features'])} features (+{added})")

    # --- Mark DMIRS-only tenements ---
    dmirs_marked = 0
    for f in geojson['features']:
        tid = f['properties'].get('tenement_id', f['properties'].get('TENEMENT_ID', ''))
        if tid in DMIRS_ONLY_IDS:
            f['properties']['dmirs_only'] = True
            dmirs_marked += 1

    print(f"  Marked {dmirs_marked} features as dmirs_only")

    # Write back GEOJSON
    geo_json = json.dumps(geojson, separators=(',', ':'), ensure_ascii=False)
    lines[geojson_line_idx] = f"{geo_prefix}{geo_json};"

    # --- Parse EVENTS ---
    ev_line = lines[events_line_idx]
    ev_prefix = ev_line[:ev_line.index('[')]
    ev_json_str = ev_line[len(ev_prefix):].rstrip().rstrip(';')
    events = json.loads(ev_json_str)

    # Find Event 15 (Kula acquisition — idx 14 or search by title)
    kula_event = None
    kula_event_idx = None
    for i, e in enumerate(events):
        if 'kula' in e.get('title', '').lower() and 'acquisition' in e.get('title', '').lower():
            kula_event = e
            kula_event_idx = i
            break

    if kula_event is None:
        print("\nERROR: Could not find Kula acquisition event!")
        return

    print(f"\n  Found Kula event at index {kula_event_idx}: {kula_event['title'][:60]}")
    print(f"  Current tenement_ids: {len(kula_event['tenement_ids'])}")

    # Add missing IDs to Kula event
    existing_event_ids = set(kula_event['tenement_ids'])
    new_ids_for_kula = []

    # Also check ALL events to avoid duplicating IDs already in other events
    all_event_ids = set()
    for e in events:
        for tid in e.get('tenement_ids', []):
            all_event_ids.add(tid)

    for tid in sorted(ALL_KULA_MISSING):
        if tid not in all_event_ids:
            new_ids_for_kula.append(tid)
        elif tid in existing_event_ids:
            pass  # already in Kula event
        else:
            print(f"  ! {tid} already in another event, skipping")

    kula_event['tenement_ids'].extend(new_ids_for_kula)
    print(f"  Added {len(new_ids_for_kula)} IDs to Kula event → {len(kula_event['tenement_ids'])} total")

    # Recalculate cum_tenements from this event forward
    for i in range(kula_event_idx, len(events)):
        if i == 0:
            events[i]['cum_tenements'] = len(events[i]['tenement_ids'])
        else:
            events[i]['cum_tenements'] = events[i-1].get('cum_tenements', 0) + len(events[i]['tenement_ids'])

    # Write back EVENTS
    ev_json = json.dumps(events, separators=(',', ':'), ensure_ascii=False)
    lines[events_line_idx] = f"{ev_prefix}{ev_json};"

    # --- Write HTML ---
    HTML_PATH.write_text('\n'.join(lines), encoding='utf-8')
    print(f"\nWritten to {HTML_PATH.name}")
    print(f"  GeoJSON: {len(geojson['features'])} features")
    print(f"  Events: {len(events)}")
    print(f"  Kula event now has {len(kula_event['tenement_ids'])} tenement IDs")

    # Verify: count tenements without polygon in Kula event
    no_poly = [tid for tid in kula_event['tenement_ids'] if tid not in existing_geo_ids and tid not in found_ids]
    if no_poly:
        print(f"  Note: {len(no_poly)} Kula tenement IDs still have no polygon: {sorted(no_poly)}")


if __name__ == '__main__':
    main()
