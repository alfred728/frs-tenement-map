#!/usr/bin/env python3
"""
Fix 6 mis-assigned tenements in Event 14 (Kula Gold).

These are GOZI/Goldzone tenements that were incorrectly added to the Kula event.
They should be in Event 33 (Goldzone completion) based on the Q2 FY26 quarterly
tenement schedule which lists them under GOZI holder with Goldzone project names.

Actions:
- Move 5 GOZI tenements from Event 14 to Event 33: E16/0580, E77/2301, E77/2435, M57/0661, P77/4372
- Remove duplicate E16/0624 from Event 14 (already exists as E16/624 in Event 33)
- Recalculate cum_tenements
"""

import json
from pathlib import Path

HTML_PATH = Path(__file__).parent / "frs_tenement_timeline_map.html"

# Tenements to move from Event 14 (Kula) to Event 33 (Goldzone)
MOVE_TO_GOLDZONE = {'E16/0580', 'E77/2301', 'E77/2435', 'M57/0661', 'P77/4372'}

# Duplicate to remove entirely (E16/624 already in Event 33)
REMOVE_DUPLICATE = {'E16/0624'}

ALL_REMOVE_FROM_KULA = MOVE_TO_GOLDZONE | REMOVE_DUPLICATE


def main():
    print(f"Reading {HTML_PATH.name}...")
    html = HTML_PATH.read_text(encoding='utf-8')
    lines = html.split('\n')

    # Find EVENTS line
    events_line_idx = None
    for i, line in enumerate(lines):
        if 'const EVENTS' in line and events_line_idx is None:
            events_line_idx = i

    ev_line = lines[events_line_idx]
    ev_prefix = ev_line[:ev_line.index('[')]
    ev_json_str = ev_line[len(ev_prefix):].rstrip().rstrip(';')
    events = json.loads(ev_json_str)

    # Find Kula event (idx 14)
    kula_idx = None
    goldzone_idx = None
    for i, e in enumerate(events):
        if e.get('idx') == 14:
            kula_idx = i
        if e.get('idx') == 33:
            goldzone_idx = i

    print(f"  Kula event at array position {kula_idx}, idx={events[kula_idx]['idx']}")
    print(f"  Goldzone event at array position {goldzone_idx}, idx={events[goldzone_idx]['idx']}")

    kula = events[kula_idx]
    goldzone = events[goldzone_idx]

    print(f"\n  Kula before: {len(kula['tenement_ids'])} tenement IDs")
    print(f"  Goldzone before: {len(goldzone['tenement_ids'])} tenement IDs")

    # Remove from Kula
    removed = [tid for tid in kula['tenement_ids'] if tid in ALL_REMOVE_FROM_KULA]
    kula['tenement_ids'] = [tid for tid in kula['tenement_ids'] if tid not in ALL_REMOVE_FROM_KULA]
    print(f"\n  Removed from Kula: {sorted(removed)}")

    # Add to Goldzone (only the MOVE ones, not the duplicate)
    existing_goldzone = set(goldzone['tenement_ids'])
    added = []
    for tid in sorted(MOVE_TO_GOLDZONE):
        if tid not in existing_goldzone:
            goldzone['tenement_ids'].append(tid)
            added.append(tid)
    print(f"  Added to Goldzone: {sorted(added)}")

    print(f"\n  Kula after: {len(kula['tenement_ids'])} tenement IDs")
    print(f"  Goldzone after: {len(goldzone['tenement_ids'])} tenement IDs")

    # Recalculate cum_tenements for all events
    for i in range(len(events)):
        if i == 0:
            events[i]['cum_tenements'] = len(events[i]['tenement_ids'])
        else:
            events[i]['cum_tenements'] = events[i-1].get('cum_tenements', 0) + len(events[i]['tenement_ids'])

    # Write back
    ev_json = json.dumps(events, separators=(',', ':'), ensure_ascii=False)
    lines[events_line_idx] = f"{ev_prefix}{ev_json};"

    HTML_PATH.write_text('\n'.join(lines), encoding='utf-8')
    print(f"\nWritten to {HTML_PATH.name}")


if __name__ == '__main__':
    main()
