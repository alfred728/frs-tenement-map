#!/usr/bin/env python3
"""
Rebuild the timeline map HTML from the edited CSV.
Reads your edits from frs_timeline_events_editable.csv and injects them
back into frs_tenement_timeline_map.html.

Usage:
  python3 rebuild_map_from_csv.py

The original tenement data (polygons, IDs, etc.) is preserved — only the
text fields you edited in the CSV get updated.
"""
import re, json, csv
from pathlib import Path

BASE = Path("/Users/alfredlewis/Documents/Forrestania Resources")
MAP_HTML = BASE / "frs_tenement_timeline_map.html"
CSV_FILE = BASE / "frs_timeline_events_editable.csv"
BACKUP_JSON = BASE / "frs_timeline_events_backup.json"

# 1. Load the current events from the HTML (to preserve tenement_ids, etc.)
with open(MAP_HTML) as f:
    html = f.read()

m = re.search(r'const EVENTS\s*=\s*(\[.*?\]);\s*\n', html, re.DOTALL)
if not m:
    raise RuntimeError("Could not find EVENTS in the HTML file")
original_events = json.loads(m.group(1))

# Index by idx for easy lookup
events_by_idx = {e['idx']: e for e in original_events}

# 2. Read the edited CSV
edits = []
with open(CSV_FILE, newline='', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    for row in reader:
        edits.append(row)

print(f"Read {len(edits)} events from CSV")

# 3. Apply edits to the original events (preserving all non-CSV fields)
PHASE_FULL_MAP = {
    1: "1 \u2013 Leadership Reset & Strategy Pivot",
    2: "2 \u2013 Acquisition Blitz",
    3: "3 \u2013 Kula Convergence",
    4: "4 \u2013 Infrastructure Play",
    5: "5 \u2013 Production Readiness",
}

updated_events = []
for row in edits:
    idx = int(row['idx'])
    orig = events_by_idx.get(idx)
    if not orig:
        print(f"  WARNING: idx {idx} not found in original events, skipping")
        continue

    # Update editable fields from CSV
    orig['date'] = row.get('date', orig['date']).strip()
    orig['phase'] = int(row.get('phase', orig['phase']))
    orig['phase_name'] = row.get('phase_name', orig['phase_name']).strip()
    orig['phase_full'] = PHASE_FULL_MAP.get(orig['phase'], orig.get('phase_full', ''))
    orig['title'] = row.get('title', orig['title']).strip()
    orig['strategic_impact'] = row.get('strategic_impact', orig['strategic_impact']).strip()
    orig['counterparties'] = row.get('counterparties', orig['counterparties']).strip()
    orig['consideration'] = row.get('consideration', orig['consideration']).strip()
    orig['project'] = row.get('project', orig['project']).strip()
    orig['confidence'] = row.get('confidence', orig['confidence']).strip()

    is_kula_raw = row.get('is_kula', str(orig['is_kula'])).strip().lower()
    orig['is_kula'] = is_kula_raw in ('true', '1', 'yes')

    updated_events.append(orig)

# Sort by idx to maintain order
updated_events.sort(key=lambda e: e['idx'])

# 4. Replace the EVENTS in the HTML
new_events_json = json.dumps(updated_events, ensure_ascii=False)
new_html = html[:m.start(1)] + new_events_json + html[m.end(1):]

# 5. Write back
with open(MAP_HTML, 'w') as f:
    f.write(new_html)

print(f"Updated {len(updated_events)} events in {MAP_HTML.name}")
print("Refresh the map in your browser to see the changes.")
