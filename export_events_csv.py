#!/usr/bin/env python3
"""
Export timeline events from the map HTML into an editable CSV.
Edit the CSV in Numbers/Excel, then run rebuild_map_from_csv.py to update the map.
"""
import re, json, csv
from pathlib import Path

BASE = Path("/Users/alfredlewis/Documents/Forrestania Resources")
MAP_HTML = BASE / "frs_tenement_timeline_map.html"
OUTPUT = BASE / "frs_timeline_events_editable.csv"

with open(MAP_HTML) as f:
    html = f.read()

m = re.search(r'const EVENTS\s*=\s*(\[.*?\]);\s*\n', html, re.DOTALL)
events = json.loads(m.group(1))

# Also save full JSON backup
with open(BASE / "frs_timeline_events_backup.json", 'w') as f:
    json.dump(events, f, indent=2)

# Export editable fields to CSV
fieldnames = [
    'idx', 'date', 'phase', 'phase_name', 'title', 'strategic_impact',
    'counterparties', 'consideration', 'project', 'confidence', 'is_kula',
    # These are read-only reference columns (don't edit)
    'tenement_ids_count', 'new_ids_count', 'cum_tenements', 'cum_area_km2'
]

with open(OUTPUT, 'w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    for e in events:
        writer.writerow({
            'idx': e['idx'],
            'date': e['date'],
            'phase': e['phase'],
            'phase_name': e['phase_name'],
            'title': e['title'],
            'strategic_impact': e['strategic_impact'],
            'counterparties': e['counterparties'],
            'consideration': e['consideration'],
            'project': e['project'],
            'confidence': e['confidence'],
            'is_kula': e['is_kula'],
            'tenement_ids_count': len(e.get('tenement_ids', [])),
            'new_ids_count': len(e.get('new_ids', [])),
            'cum_tenements': e.get('cum_tenements', 0),
            'cum_area_km2': e.get('cum_area_km2', 0),
        })

print(f"Exported {len(events)} events to {OUTPUT}")
print(f"Backup saved to frs_timeline_events_backup.json")
print(f"\nEditable columns: title, strategic_impact, counterparties, consideration, project, confidence, date, phase, phase_name")
print(f"Reference columns (don't edit): tenement_ids_count, new_ids_count, cum_tenements, cum_area_km2")
