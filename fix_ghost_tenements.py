#!/usr/bin/env python3
"""
Remove 3 ghost tenements from GeoJSON that belong to MacPhersons Reward Pty Ltd,
NOT to FRS. These have uppercase TENEMENT_ID properties (from KMZ extraction)
and are invisible in the browser but inflate baseline counts.

M15/1921 - MacPhersons Reward Pty Ltd (Pending)
M15/1925 - MacPhersons Reward Pty Ltd (Pending)
P15/6409 - MacPhersons Reward Pty Ltd (Pending)
"""

import json
import re
from pathlib import Path

HTML_PATH = Path(__file__).parent / "frs_tenement_timeline_map.html"

GHOST_IDS = {"M15/1921", "M15/1925", "P15/6409"}


def main():
    print(f"Reading {HTML_PATH}...")
    html = HTML_PATH.read_text(encoding='utf-8')
    lines = html.split('\n')

    # Find GEOJSON line
    geojson_line = None
    for i, line in enumerate(lines):
        if 'const GEOJSON' in line and geojson_line is None:
            geojson_line = i

    print(f"GEOJSON on line {geojson_line + 1}")

    # Parse GEOJSON
    geojson_prefix = lines[geojson_line][:lines[geojson_line].index('{')]
    geojson_json_str = lines[geojson_line][len(geojson_prefix):].rstrip().rstrip(';')
    geojson = json.loads(geojson_json_str)
    before = len(geojson['features'])
    print(f"Parsed {before} GeoJSON features")

    # Remove ghost features - check both tenement_id and TENEMENT_ID
    geojson['features'] = [
        f for f in geojson['features']
        if f['properties'].get('tenement_id', f['properties'].get('TENEMENT_ID', '')) not in GHOST_IDS
    ]

    removed = before - len(geojson['features'])
    print(f"Removed {removed} ghost features (expected 3)")

    # Write back
    geojson_json = json.dumps(geojson, separators=(',', ':'), ensure_ascii=False)
    lines[geojson_line] = f"{geojson_prefix}{geojson_json};"

    HTML_PATH.write_text('\n'.join(lines), encoding='utf-8')
    print(f"Written to {HTML_PATH}")
    print(f"GeoJSON features: {len(geojson['features'])} (was {before})")


if __name__ == '__main__':
    main()
