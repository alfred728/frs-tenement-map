#!/usr/bin/env python3
"""
FRS Tenement Map Audit Fix Script
Applies all corrections identified in the tenement audit:
1. Removes 7 invalid tenements from GeoJSON
2. Creates Bradley acquisition event
3. Adds missing tenement IDs to Event 10 (Burracoppin) and Event 4 (IMD Gold)
4. Creates organic ground pegging event
5. Moves post-story tenements from baseline to events
"""

import json
import re
import sys
from pathlib import Path

HTML_PATH = Path(__file__).parent / "frs_tenement_timeline_map.html"

# === CONFIGURATION ===

# 7 tenements to REMOVE from GeoJSON (not FRS-owned)
REMOVE_IDS = {
    "E77/1400", "E77/2099", "M77/1066", "M77/1080",
    "M77/99", "M77/219", "P29/2729"
}

# Bradley acquisition (5 Aug 2025) - 3 tenements
BRADLEY_EVENT = {
    "idx": 99,  # placeholder, will be reindexed
    "date": "2025-08-05",
    "phase": 2,
    "phase_name": "Phase 2",
    "phase_full": "Phase 2 \u2014 Targeted Acquisitions",
    "title": "Bradley tenement acquisition \u2014 3 Bonnie Vale area applications",
    "strategic_impact": "FRS acquired 2 exploration licence applications and 1 prospecting licence application from Joseph Robert Bradley for $20,000 cash plus a 1.5% NSR royalty, consolidating ground around Bonnie Vale. Completed 20 November 2025.",
    "tenement_ids": ["E15/2016", "E15/2024", "P15/6878"],
    "missing_ids": [],
    "new_ids": [],
    "tenements_added_story": 3,
    "counterparties": "Joseph Robert Bradley",
    "consideration": "$20,000 + 1.5% NSR",
    "project": "Bonnie Vale",
    "confidence": "high",
    "cum_tenements": 0,  # will be recalculated
    "cum_area_km2": 0,   # will be recalculated
    "is_kula": False,
    "cum_oz": 0           # will be recalculated
}

# Event 10 (Burracoppin) - 4 missing tenement IDs to add
BURRACOPPIN_MISSING = ["E47/5019", "E52/3718", "E52/3719", "E80/5313"]

# Event 4 (IMD Gold) - 3 missing L77 licence IDs to add
IMD_GOLD_MISSING = ["L77/221", "L77/223", "L77/224"]

# Organic ground pegging event (~Sep 2025) - 20 tenements
ORGANIC_EVENT = {
    "idx": 99,  # placeholder
    "date": "2025-09-15",
    "phase": 2,
    "phase_name": "Phase 2",
    "phase_full": "Phase 2 \u2014 Targeted Acquisitions",
    "title": "Organic ground pegging \u2014 20 tenement applications across Forrestania, Southern Cross, Westonia & Eastern Goldfields",
    "strategic_impact": "FRS proactively pegged 20 new tenement applications around its newly acquired projects, expanding its footprint in the Southern Cross, Westonia, Bonnie Vale and Eastern Goldfields regions. This systematic land consolidation followed the British Hill, North Ironcap and Kula Gold Westonia acquisitions.",
    "tenement_ids": [
        "E77/3316", "E77/3337", "E77/3339", "E77/3340", "E77/3341",
        "E77/3347", "E77/3352", "E15/2143", "P16/3563", "E29/1307",
        "E29/1308", "E31/1440", "E70/6753", "E77/3344", "E77/3345",
        "E77/3346", "E77/3348", "E77/3349", "E77/3350", "E77/3351"
    ],
    "missing_ids": [],
    "new_ids": [],
    "tenements_added_story": 20,
    "counterparties": "",
    "consideration": "Application fees only",
    "project": "Multiple",
    "confidence": "high",
    "cum_tenements": 0,
    "cum_area_km2": 0,
    "is_kula": False,
    "cum_oz": 0
}

# Post-story organic apps (Nov-Dec 2025) - 3 tenements
POST_STORY_ORGANIC = {
    "idx": 99,
    "date": "2025-12-01",
    "phase": 5,
    "phase_name": "Phase 5",
    "phase_full": "Phase 5 \u2014 Capital & Cornerstone",
    "title": "Additional organic tenement applications \u2014 Jaurdi, Leake & exploration",
    "strategic_impact": "FRS continued to expand organically with 3 additional tenement applications in the Jaurdi, Leake and exploration areas.",
    "tenement_ids": ["E16/675", "E63/2549", "E77/3046"],
    "missing_ids": [],
    "new_ids": [],
    "tenements_added_story": 3,
    "counterparties": "",
    "consideration": "Application fees only",
    "project": "Multiple",
    "confidence": "high",
    "cum_tenements": 0,
    "cum_area_km2": 0,
    "is_kula": False,
    "cum_oz": 0
}


def extract_json_var(html_lines, var_name, line_idx):
    """Extract a JSON variable from a specific line."""
    line = html_lines[line_idx]
    # Match: const VARNAME = <JSON>;
    pattern = rf'const\s+{var_name}\s*=\s*'
    match = re.search(pattern, line)
    if not match:
        print(f"ERROR: Could not find 'const {var_name}' on line {line_idx + 1}")
        sys.exit(1)

    start = match.end()
    # Find the matching end (the JSON ends with ; at end of line)
    json_str = line[start:].rstrip().rstrip(';')
    return json.loads(json_str), start


def main():
    print(f"Reading {HTML_PATH}...")
    html = HTML_PATH.read_text(encoding='utf-8')
    lines = html.split('\n')

    print(f"Total lines: {len(lines)}")

    # Find the EVENTS and GEOJSON lines
    events_line = None
    geojson_line = None
    for i, line in enumerate(lines):
        if 'const EVENTS' in line and events_line is None:
            events_line = i
        if 'const GEOJSON' in line and geojson_line is None:
            geojson_line = i

    print(f"EVENTS on line {events_line + 1}, GEOJSON on line {geojson_line + 1}")

    # === Parse EVENTS ===
    events_prefix = lines[events_line][:lines[events_line].index('[')]
    events_json_str = lines[events_line][len(events_prefix):].rstrip().rstrip(';')
    events = json.loads(events_json_str)
    print(f"Parsed {len(events)} events")

    # === Parse GEOJSON ===
    geojson_prefix = lines[geojson_line][:lines[geojson_line].index('{')]
    geojson_json_str = lines[geojson_line][len(geojson_prefix):].rstrip().rstrip(';')
    geojson = json.loads(geojson_json_str)
    print(f"Parsed {len(geojson['features'])} GeoJSON features")

    # === STEP 1: Remove 7 invalid tenements from GeoJSON ===
    print("\n--- Step 1: Removing 7 invalid tenements ---")
    before = len(geojson['features'])
    geojson['features'] = [
        f for f in geojson['features']
        if f['properties'].get('tenement_id', f['properties'].get('TENEMENT_ID', '')) not in REMOVE_IDS
    ]
    removed = before - len(geojson['features'])
    print(f"Removed {removed} features (expected 7)")
    if removed != 7:
        # Try alternate property name
        print("WARNING: Expected 7 removals. Checking alternate property names...")
        remaining_ids = set()
        for f in geojson['features']:
            tid = f['properties'].get('tenement_id', '')
            if not tid:
                tid = f['properties'].get('TENEMENT_ID', '')
            remaining_ids.add(tid)
        still_present = REMOVE_IDS & remaining_ids
        if still_present:
            print(f"  Still present: {still_present}")
        else:
            print(f"  All 7 confirmed removed (some may have had different property names)")

    # === STEP 2: Add missing tenement IDs to Event 10 (Burracoppin) ===
    print("\n--- Step 2: Adding 4 missing Burracoppin tenements to Event 10 ---")
    # Find Event 10 by looking for Burracoppin in title
    for evt in events:
        if 'burracoppin' in evt.get('title', '').lower() or 'first western' in evt.get('title', '').lower():
            existing = set(evt['tenement_ids'])
            for tid in BURRACOPPIN_MISSING:
                if tid not in existing:
                    evt['tenement_ids'].append(tid)
                    print(f"  Added {tid} to Event {evt['idx']}: {evt['title'][:60]}")
            # Update tenements_added_story
            evt['tenements_added_story'] = len(evt['tenement_ids'])
            break

    # === STEP 3: Add missing L77 licences to Event 4 (IMD Gold) ===
    print("\n--- Step 3: Adding 3 missing L77 licences to Event 4 ---")
    for evt in events:
        if 'british hill' in evt.get('title', '').lower() or 'imd gold' in evt.get('title', '').lower():
            existing = set(evt['tenement_ids'])
            for tid in IMD_GOLD_MISSING:
                if tid not in existing:
                    evt['tenement_ids'].append(tid)
                    print(f"  Added {tid} to Event {evt['idx']}: {evt['title'][:60]}")
            evt['tenements_added_story'] = len(evt['tenement_ids'])
            break

    # === STEP 4: Insert Bradley acquisition event ===
    print("\n--- Step 4: Inserting Bradley acquisition event ---")
    # Insert after IMD Gold (date 2025-08-01) and before the next event
    insert_idx = None
    for i, evt in enumerate(events):
        if evt['date'] > "2025-08-05":
            insert_idx = i
            break
    if insert_idx is None:
        insert_idx = len(events)

    events.insert(insert_idx, BRADLEY_EVENT)
    print(f"  Inserted Bradley event at position {insert_idx} (date: 2025-08-05)")

    # === STEP 5: Insert organic ground pegging event ===
    print("\n--- Step 5: Inserting organic ground pegging event ---")
    insert_idx = None
    for i, evt in enumerate(events):
        if evt['date'] > "2025-09-15":
            insert_idx = i
            break
    if insert_idx is None:
        insert_idx = len(events)

    events.insert(insert_idx, ORGANIC_EVENT)
    print(f"  Inserted organic event at position {insert_idx} (date: 2025-09-15)")

    # === STEP 6: Insert post-story organic apps event ===
    print("\n--- Step 6: Inserting post-story organic apps event ---")
    insert_idx = None
    for i, evt in enumerate(events):
        if evt['date'] > "2025-12-01":
            insert_idx = i
            break
    if insert_idx is None:
        insert_idx = len(events)

    events.insert(insert_idx, POST_STORY_ORGANIC)
    print(f"  Inserted post-story organic event at position {insert_idx} (date: 2025-12-01)")

    # === STEP 7: Re-index all events ===
    print("\n--- Step 7: Re-indexing events ---")
    for i, evt in enumerate(events):
        evt['idx'] = i
    print(f"  Re-indexed {len(events)} events (was {len(events) - 3})")

    # === STEP 8: Recalculate cumulative tenement counts ===
    print("\n--- Step 8: Recalculating cumulative counts ---")
    cum_tenements = 0
    for evt in events:
        cum_tenements += len(evt.get('tenement_ids', []))
        evt['cum_tenements'] = cum_tenements
    print(f"  Final cumulative tenements: {cum_tenements}")

    # === Write back ===
    print("\n--- Writing modified file ---")
    events_json = json.dumps(events, separators=(',', ':'), ensure_ascii=False)
    geojson_json = json.dumps(geojson, separators=(',', ':'), ensure_ascii=False)

    lines[events_line] = f"{events_prefix}{events_json};"
    lines[geojson_line] = f"{geojson_prefix}{geojson_json};"

    HTML_PATH.write_text('\n'.join(lines), encoding='utf-8')
    print(f"Written to {HTML_PATH}")

    # === Summary ===
    print("\n=== SUMMARY ===")
    print(f"GeoJSON features: {len(geojson['features'])} (was {before})")
    print(f"Events: {len(events)}")
    print(f"Removed tenements: {REMOVE_IDS}")

    # Count what's now in story vs baseline
    story_ids = set()
    for evt in events:
        for tid in evt.get('tenement_ids', []):
            story_ids.add(tid)

    geojson_ids = set()
    for f in geojson['features']:
        tid = f['properties'].get('tenement_id', f['properties'].get('TENEMENT_ID', ''))
        geojson_ids.add(tid)

    baseline = geojson_ids - story_ids
    print(f"Story tenement IDs: {len(story_ids)}")
    print(f"GeoJSON IDs: {len(geojson_ids)}")
    print(f"New baseline count: {len(baseline)}")
    print(f"Baseline IDs: {sorted(baseline)}")


if __name__ == '__main__':
    main()
