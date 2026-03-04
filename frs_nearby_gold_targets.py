#!/usr/bin/env python3
"""
Export nearby gold targets analysis to CSV for spreadsheet viewing.
Uses ONLY the latest resource estimate period per site (not historical cumulative).
"""

import csv
import json
import math
import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path

BASE = Path("/Users/alfredlewis/Documents/Forrestania Resources")
MINEDEX = BASE / "ingestion/processed/maps/source/minedex"
MAP_HTML = BASE / "frs_tenement_timeline_map.html"
OUTPUT = BASE / "frs_nearby_gold_targets.csv"
SEARCH_RADIUS_KM = 50

# Mill / processing plant coordinates
EDNA_MAY_MILL = (-31.305, 118.698)
LAKE_JOHNSTON_PLANT = (-32.208405, 120.489175)


def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    return R * 2 * math.asin(math.sqrt(a))


def parse_date(s):
    """Parse dd/mm/yyyy date string, return datetime or None."""
    s = (s or '').strip()
    if not s:
        return None
    for fmt in ('%d/%m/%Y', '%Y-%m-%d', '%d/%m/%y'):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    return None


def extract_frs_clusters():
    with open(MAP_HTML) as f:
        html = f.read()
    m = re.search(r'const GEOJSON\s*=\s*(\{.*?\});', html, re.DOTALL)
    geo = json.loads(m.group(1))
    tenements = []
    for feat in geo['features']:
        tid = feat['properties'].get('tenement_id', '')
        geom = feat['geometry']
        coords = []
        if geom['type'] == 'Polygon':
            coords = geom['coordinates'][0]
        elif geom['type'] == 'MultiPolygon':
            for poly in geom['coordinates']:
                coords.extend(poly[0])
        if coords:
            clat = sum(c[1] for c in coords) / len(coords)
            clon = sum(c[0] for c in coords) / len(coords)
            tenements.append({'id': tid, 'lat': clat, 'lon': clon})
    clusters = defaultdict(list)
    for t in tenements:
        parts = t['id'].split('/')
        prefix = parts[0] if parts else ''
        district = re.sub(r'[A-Z]+', '', prefix)
        clusters[district].append(t)
    result = {}
    for dist, tlist in clusters.items():
        clat = sum(t['lat'] for t in tlist) / len(tlist)
        clon = sum(t['lon'] for t in tlist) / len(tlist)
        result[dist] = {'centroid_lat': clat, 'centroid_lon': clon, 'count': len(tlist)}
    return result


def min_dist_to_frs(lat, lon, clusters):
    best = float('inf')
    best_cluster = None
    for dist, info in clusters.items():
        d = haversine_km(lat, lon, info['centroid_lat'], info['centroid_lon'])
        if d < best:
            best = d
            best_cluster = dist
    return best, best_cluster


clusters = extract_frs_clusters()

# ── Load ALL resource estimates (with dates) ──
estimates = []
with open(MINEDEX / "ResourceEstimates.csv", newline='', encoding='utf-8-sig') as f:
    for row in csv.DictReader(f):
        try:
            lat, lon = float(row['Latitude']), float(row['Longitude'])
        except (ValueError, KeyError):
            continue
        try: qty = float(row.get('EstimateQuantity', 0))
        except: qty = 0
        try: grade = float(row.get('Grade', 0))
        except: grade = 0
        try: contained_oz = float(row.get('AlternativeContainedCommodity', 0))
        except: contained_oz = 0

        if 'Gold' not in (row.get('EstimateCommodity', '') or '') and \
           'Au' not in (row.get('EstimateComoditityAbbreviation', '') or ''):
            continue

        d, cl = min_dist_to_frs(lat, lon, clusters)
        if d <= SEARCH_RADIUS_KM:
            start_date = parse_date(row.get('StartDate', ''))
            end_date = parse_date(row.get('EndDate', ''))

            estimates.append({
                'site_code': row.get('SiteCode', ''),
                'site_name': row.get('SiteName', '') or row.get('ShortTitle', ''),
                'short_title': row.get('ShortTitle', ''),
                'site_type': row.get('SiteType', ''),
                'stage': row.get('SiteStage', ''),
                'commodity': row.get('EstimateCommodity', ''),
                'category': row.get('ResourceCategory', ''),
                'status': row.get('ResourceStatus', ''),
                'estimate_type': row.get('EstimateType', ''),
                'reporting_code': row.get('ReportingCode', ''),
                'quantity_mt': qty,
                'grade': grade,
                'grade_unit': row.get('GradeUnit', ''),
                'contained_oz': contained_oz,
                'project': row.get('ProjectShortName', ''),
                'project_code': row.get('ProjectCode', ''),
                'lat': lat, 'lon': lon,
                'distance_km': d,
                'nearest_frs_cluster': cl,
                'start_date': start_date,
                'end_date': end_date,
                'start_date_str': row.get('StartDate', ''),
                'end_date_str': row.get('EndDate', ''),
            })

print(f"Loaded {len(estimates)} gold estimate records within {SEARCH_RADIUS_KM}km")

# ── Load owners ──
owners = defaultdict(list)
with open(MINEDEX / "ProjectsOwners.csv", newline='', encoding='utf-8-sig') as f:
    for row in csv.DictReader(f):
        owners[row.get('ProjectCode', '')].append({
            'name': row.get('OwnerName', ''),
            'pct': row.get('HoldingPct', ''),
        })

# ── Group by site_code, then pick ONLY the latest reporting period ──
#
# MINEDEX stores every historical estimate. Each estimate has a StartDate and
# EndDate representing the reporting period. For a given site, estimates sharing
# the same StartDate belong to the same reporting period (Measured + Indicated +
# Inferred resource rows, plus Proved + Probable reserve rows).
#
# Strategy:
#   1. For each site_code, find the maximum StartDate (= most recent estimate period)
#   2. Keep only "Resource" category rows from that period (not Reserves, to avoid
#      double-counting since reserves are a subset of resources)
#   3. If a site has NO Resource rows at the latest date, fall back to Reserve rows
#   4. Sum the kept rows for total oz / Mt / grade

site_all = defaultdict(list)
for est in estimates:
    site_all[est['site_code']].append(est)

rows_out = []
for site_code, all_ests in site_all.items():
    # Find the latest StartDate across all estimates for this site
    dated = [e for e in all_ests if e['start_date'] is not None]
    if not dated:
        # No dates at all — use all estimates as-is (rare edge case)
        latest_ests = all_ests
        estimate_date_str = 'Unknown'
    else:
        max_start = max(e['start_date'] for e in dated)
        # Keep rows from the latest start date
        latest_ests = [e for e in dated if e['start_date'] == max_start]
        estimate_date_str = max_start.strftime('%d/%m/%Y')

        # If there are no Resource rows at this date, broaden slightly:
        # some sites report Resources and Reserves on slightly different start dates
        resource_rows = [e for e in latest_ests if e['category'] == 'Resource']
        if not resource_rows:
            # Try the second-most-recent start date for Resources
            resource_dates = sorted(set(e['start_date'] for e in dated if e['category'] == 'Resource'), reverse=True)
            if resource_dates:
                latest_res_date = resource_dates[0]
                resource_rows = [e for e in dated if e['start_date'] == latest_res_date and e['category'] == 'Resource']
                latest_ests = resource_rows
                estimate_date_str = latest_res_date.strftime('%d/%m/%Y')

    # Prefer Resource rows (Measured + Indicated + Inferred) to avoid double-counting
    resource_rows = [e for e in latest_ests if e['category'] == 'Resource']
    if resource_rows:
        keep = resource_rows
    else:
        # Only reserves available
        keep = [e for e in latest_ests if e['category'] == 'Reserve']
    if not keep:
        keep = latest_ests  # fallback

    # Compute aggregates from the latest-period rows only
    total_oz = sum(e['contained_oz'] for e in keep)
    total_mt = sum(e['quantity_mt'] for e in keep if e['quantity_mt'] > 0)
    avg_grade = (sum(e['grade'] * e['quantity_mt'] for e in keep if e['quantity_mt'] > 0)
                 / max(total_mt, 0.001))
    categories = ', '.join(sorted(set(e['category'] for e in keep)))
    statuses = ', '.join(sorted(set(e['status'] for e in keep)))

    # Use first estimate for metadata
    ref = all_ests[0]
    site_name = ref['short_title'] or ref['site_name']
    proj_code = ref.get('project_code', '')
    owner_list = owners.get(proj_code, [])
    owner_str = '; '.join(
        f"{o['name']} ({o['pct']}%)" if o['pct'] and o['pct'] != 'Unknown' else o['name']
        for o in owner_list if o['name']
    ) or ''
    primary_owner = next((o['name'] for o in owner_list if o['pct'] and '%' not in o['pct'] and 'Royalt' not in o['pct']),
                         owner_list[0]['name'] if owner_list else '')

    site_lat = ref['lat']
    site_lon = ref['lon']
    dist_edna_may = round(haversine_km(site_lat, site_lon, EDNA_MAY_MILL[0], EDNA_MAY_MILL[1]), 1)
    dist_lake_johnston = round(haversine_km(site_lat, site_lon, LAKE_JOHNSTON_PLANT[0], LAKE_JOHNSTON_PLANT[1]), 1)

    # Also compute the latest Reserve separately for reference
    reserve_rows = [e for e in latest_ests if e['category'] == 'Reserve']
    reserve_oz = sum(e['contained_oz'] for e in reserve_rows)
    reserve_mt = sum(e['quantity_mt'] for e in reserve_rows if e['quantity_mt'] > 0)
    reserve_grade = (sum(e['grade'] * e['quantity_mt'] for e in reserve_rows if e['quantity_mt'] > 0)
                     / max(reserve_mt, 0.001))

    rows_out.append({
        'Site': site_name,
        'Project': ref.get('project', ''),
        'Project_Code': proj_code,
        'Stage': ref.get('stage', ''),
        'Site_Type': ref.get('site_type', ''),
        'Resource_Oz_Au': round(total_oz),
        'Resource_Mt': round(total_mt, 3),
        'Resource_Grade_gpt': round(avg_grade, 2),
        'Reserve_Oz_Au': round(reserve_oz),
        'Reserve_Mt': round(reserve_mt, 3),
        'Reserve_Grade_gpt': round(reserve_grade, 2),
        'Resource_Categories': categories,
        'Resource_Statuses': statuses,
        'Estimate_Date': estimate_date_str,
        'Distance_km': round(min(e['distance_km'] for e in all_ests), 1),
        'Nearest_FRS_Cluster': ref.get('nearest_frs_cluster', ''),
        'Dist_Edna_May_Mill_km': dist_edna_may,
        'Dist_Lake_Johnston_Plant_km': dist_lake_johnston,
        'Latitude': round(site_lat, 6),
        'Longitude': round(site_lon, 6),
        'Primary_Owner': primary_owner,
        'All_Owners': owner_str,
        'N_Latest_Rows': len(keep),
        'N_Total_Historical': len(all_ests),
    })

rows_out.sort(key=lambda x: x['Resource_Oz_Au'], reverse=True)

fieldnames = ['Site', 'Project', 'Project_Code', 'Stage', 'Site_Type',
              'Resource_Oz_Au', 'Resource_Mt', 'Resource_Grade_gpt',
              'Reserve_Oz_Au', 'Reserve_Mt', 'Reserve_Grade_gpt',
              'Resource_Categories', 'Resource_Statuses', 'Estimate_Date',
              'Distance_km', 'Nearest_FRS_Cluster',
              'Dist_Edna_May_Mill_km', 'Dist_Lake_Johnston_Plant_km',
              'Latitude', 'Longitude',
              'Primary_Owner', 'All_Owners', 'N_Latest_Rows', 'N_Total_Historical']

with open(OUTPUT, 'w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows_out)

print(f"Exported {len(rows_out)} gold resource sites to {OUTPUT}")

# ── Sanity check: print Edna May to verify ──
edna = [r for r in rows_out if 'Edna May' in r['Site'] or 'Greenfinch' in r['Site'] or 'Golden Point' in r['Site']]
print("\n=== EDNA MAY VERIFICATION ===")
for r in edna:
    print(f"  {r['Site']}: Resource {r['Resource_Oz_Au']:,} oz ({r['Resource_Mt']} Mt @ {r['Resource_Grade_gpt']} g/t) "
          f"| Reserve {r['Reserve_Oz_Au']:,} oz | Date: {r['Estimate_Date']}")
