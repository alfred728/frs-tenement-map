#!/usr/bin/env python3
"""
FRS Target Analysis — Who owns the gold resources near FRS tenements?
=====================================================================
Focuses on:
  1. Every nearby gold resource matched to its owner(s)
  2. Smaller / care-and-maintenance / undeveloped projects (potential targets)
  3. Resources on tenements FRS already holds or borders
"""

import csv
import json
import math
import re
from collections import defaultdict
from pathlib import Path

BASE = Path("/Users/alfredlewis/Documents/Forrestania Resources")
MINEDEX = BASE / "ingestion/processed/maps/source/minedex"
CSV_DIR = BASE / "ingestion/processed/maps/source/csv"
MAP_HTML = BASE / "frs_tenement_timeline_map.html"
SEARCH_RADIUS_KM = 50


def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    return R * 2 * math.asin(math.sqrt(a))


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
        result[dist] = {
            'centroid_lat': clat, 'centroid_lon': clon,
            'count': len(tlist),
            'tenement_ids': [t['id'] for t in tlist],
        }
    return result


def load_sites():
    sites = {}
    with open(MINEDEX / "Sites.csv", newline='', encoding='utf-8-sig') as f:
        for row in csv.DictReader(f):
            try:
                lat, lon = float(row['Latitude']), float(row['Longitude'])
            except (ValueError, KeyError):
                continue
            code = row.get('SiteCode', '')
            if code not in sites:
                sites[code] = {
                    'code': code,
                    'name': row.get('ShortTitle', '') or row.get('Title', ''),
                    'title': row.get('Title', ''),
                    'type': row.get('Type', ''),
                    'subtype': row.get('SubType', ''),
                    'stage': row.get('Stage', ''),
                    'commodities': row.get('Commodities', ''),
                    'target_commodity': row.get('TargetCommodityGroups', ''),
                    'project': row.get('ProjectTitle', ''),
                    'project_code': row.get('ProjectCode', ''),
                    'lat': lat, 'lon': lon,
                }
    return sites


def load_resource_estimates():
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
            estimates.append({
                'site_code': row.get('SiteCode', ''),
                'site_name': row.get('SiteName', '') or row.get('ShortTitle', ''),
                'short_title': row.get('ShortTitle', ''),
                'site_type': row.get('SiteType', ''),
                'stage': row.get('SiteStage', ''),
                'commodity': row.get('EstimateCommodity', ''),
                'commodity_abbr': row.get('EstimateComoditityAbbreviation', ''),
                'category': row.get('ResourceCategory', ''),
                'status': row.get('ResourceStatus', ''),
                'reporting_code': row.get('ReportingCode', ''),
                'quantity_mt': qty,
                'grade': grade,
                'grade_unit': row.get('GradeUnit', ''),
                'contained_oz': contained_oz,
                'project': row.get('ProjectShortName', ''),
                'project_code': row.get('ProjectCode', ''),
                'lat': lat, 'lon': lon,
                'primary_commodity': row.get('SitePrimaryCommodity', ''),
            })
    return estimates


def load_project_owners():
    owners = defaultdict(list)
    with open(MINEDEX / "ProjectsOwners.csv", newline='', encoding='utf-8-sig') as f:
        for row in csv.DictReader(f):
            owners[row.get('ProjectCode', '')].append({
                'name': row.get('OwnerName', ''),
                'pct': row.get('HoldingPct', ''),
                'project': row.get('ProjectTitle', ''),
            })
    return owners


def load_site_tenements():
    links = defaultdict(list)
    with open(MINEDEX / "SiteTenements.csv", newline='', encoding='utf-8-sig') as f:
        for row in csv.DictReader(f):
            code = row.get('SiteCode', '')
            ten = row.get('TenementCode', '').strip()
            status = row.get('Status', '')
            links[code].append({'tenement': ten, 'status': status})
    return links


def normalise_tenement_id(raw):
    """Normalise tenement codes like 'E  7700219' -> 'E77/219' and 'M 1500128' -> 'M15/128'."""
    raw = raw.strip()
    m = re.match(r'^([A-Z]+)\s*(\d{2,3})(\d{4,5})$', raw)
    if m:
        prefix = m.group(1)
        dist = m.group(2).lstrip('0') or '0'
        num = m.group(3).lstrip('0') or '0'
        return f"{prefix}{dist}/{num}"
    return raw


# ═══════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════

clusters = extract_frs_clusters()
frs_tenement_ids = set()
for info in clusters.values():
    frs_tenement_ids.update(info['tenement_ids'])

sites = load_sites()
estimates = load_resource_estimates()
owners = load_project_owners()
site_tens = load_site_tenements()

# Build normalised FRS ID lookup
frs_ids_normalised = set(frs_tenement_ids)

# Find distance of each site to nearest FRS cluster
def min_dist_to_frs(lat, lon):
    best = float('inf')
    best_cluster = None
    for dist, info in clusters.items():
        d = haversine_km(lat, lon, info['centroid_lat'], info['centroid_lon'])
        if d < best:
            best = d
            best_cluster = dist
    return best, best_cluster

# ── Gold resource estimates near FRS ──
gold_estimates = []
for est in estimates:
    if 'Gold' not in (est.get('commodity', '') or '') and 'Au' not in (est.get('commodity_abbr', '') or ''):
        continue
    d, cl = min_dist_to_frs(est['lat'], est['lon'])
    if d <= SEARCH_RADIUS_KM:
        est['distance_km'] = d
        est['nearest_cluster'] = cl
        gold_estimates.append(est)

# Aggregate by site
site_agg = defaultdict(lambda: {'estimates': [], 'total_oz': 0, 'total_mt': 0})
for est in gold_estimates:
    key = est['short_title'] or est['site_name']
    site_agg[key]['estimates'].append(est)
    site_agg[key]['total_oz'] += est['contained_oz']
    site_agg[key]['total_mt'] += est['quantity_mt']

# Build full site records
site_records = []
for site_name, data in site_agg.items():
    ests = data['estimates']
    total_mt = sum(e['quantity_mt'] for e in ests if e['quantity_mt'] > 0)
    avg_grade = (sum(e['grade'] * e['quantity_mt'] for e in ests if e['quantity_mt'] > 0)
                 / max(total_mt, 0.001))

    proj_code = ests[0].get('project_code', '')
    owner_list = owners.get(proj_code, [])

    # Check if any site tenements overlap with FRS
    site_code = ests[0].get('site_code', '')
    site_ten_list = site_tens.get(site_code, [])
    normalised_site_tens = [normalise_tenement_id(st['tenement']) for st in site_ten_list]
    overlapping = [t for t in normalised_site_tens if t in frs_ids_normalised]
    live_tens = [st for st in site_ten_list if st['status'] == 'Live']

    site_records.append({
        'name': site_name,
        'site_code': site_code,
        'project': ests[0].get('project', ''),
        'project_code': proj_code,
        'stage': ests[0].get('stage', ''),
        'total_oz': data['total_oz'],
        'total_mt': total_mt,
        'avg_grade': avg_grade,
        'distance_km': min(e['distance_km'] for e in ests),
        'nearest_cluster': ests[0].get('nearest_cluster', ''),
        'owners': owner_list,
        'owner_names': [o['name'] for o in owner_list if o['name']],
        'categories': list(set(e['category'] for e in ests)),
        'statuses': list(set(e['status'] for e in ests)),
        'n_estimates': len(ests),
        'overlapping_frs': overlapping,
        'live_tenements': len(live_tens),
        'all_tenements': normalised_site_tens,
        'lat': ests[0]['lat'],
        'lon': ests[0]['lon'],
    })

site_records.sort(key=lambda x: x['total_oz'], reverse=True)


# ═══════════════════════════════════════════════════════
# OUTPUT
# ═══════════════════════════════════════════════════════

print("=" * 100)
print("GOLD RESOURCES NEAR FRS — WITH OWNERSHIP")
print("=" * 100)
print(f"{'#':<4} {'Site':<28} {'Project':<28} {'Oz Au':>14} {'Mt':>8} {'g/t':>6} "
      f"{'km':>5} {'Stage':<18} {'Owner(s)'}")
print("-" * 160)

for i, sr in enumerate(site_records, 1):
    owner_str = '; '.join(
        f"{o['name']} ({o['pct']}%)" if o['pct'] and o['pct'] != 'Unknown' else o['name']
        for o in sr['owners'] if o['name']
    ) or 'Unknown / no MINEDEX owner'

    overlap_flag = " ** ON FRS TENEMENT **" if sr['overlapping_frs'] else ""

    print(f"{i:<4} {sr['name'][:27]:<28} {sr['project'][:27]:<28} "
          f"{sr['total_oz']:>14,.0f} {sr['total_mt']:>8.3f} {sr['avg_grade']:>6.2f} "
          f"{sr['distance_km']:>5.1f} {sr['stage'][:17]:<18} {owner_str[:60]}{overlap_flag}")


# ── Focus on targetable resources ──
print("\n\n" + "=" * 100)
print("POTENTIAL FRS TARGETS — Undeveloped / Care & Maintenance / Shut gold resources")
print("Filtered to: < 30km from FRS, > 1,000 oz Au, NOT major producers")
print("=" * 100)

MAJOR_COMPANIES = {
    'Northern Star Resources Ltd', 'Northern Star (Klv) Pty Ltd',
    'Northern Star (Saracen Kalgoorlie) Pty Ltd',
    'Northern Star (HBJ) Pty Ltd', 'Northern Star (South Kalgoorlie) Pty Ltd',
    'Northern Star (Hampton Gold Mining Areas) Limited',
    'Northern Star (Kanowna) Pty Limited',
    'Evolution Mining Limited', 'Newmont Corporation',
    'Gold Fields Limited', 'Barrick Gold Corp.',
    'Saracen Mineral Holdings Ltd',
}

targets = []
for sr in site_records:
    stage_lower = sr['stage'].lower()
    if stage_lower not in ('care and maintenance', 'undeveloped', 'shut', 'proposed'):
        continue
    if sr['distance_km'] > 30:
        continue
    if sr['total_oz'] < 1000:
        continue
    # Skip if owned by a major
    if any(o in MAJOR_COMPANIES for o in sr['owner_names']):
        continue
    targets.append(sr)

targets.sort(key=lambda x: x['total_oz'], reverse=True)

print(f"\nFound {len(targets)} potential target resources:\n")
print(f"{'#':<4} {'Site':<28} {'Project':<28} {'Oz Au':>14} {'Mt':>8} {'g/t':>6} "
      f"{'km':>5} {'Stage':<18} {'Owner(s)'}")
print("-" * 160)

for i, sr in enumerate(targets, 1):
    owner_str = '; '.join(
        f"{o['name']} ({o['pct']}%)" if o['pct'] and o['pct'] != 'Unknown' else o['name']
        for o in sr['owners'] if o['name']
    ) or 'Unknown / no MINEDEX owner'

    overlap_flag = " ** ON FRS TENEMENT **" if sr['overlapping_frs'] else ""

    print(f"{i:<4} {sr['name'][:27]:<28} {sr['project'][:27]:<28} "
          f"{sr['total_oz']:>14,.0f} {sr['total_mt']:>8.3f} {sr['avg_grade']:>6.2f} "
          f"{sr['distance_km']:>5.1f} {sr['stage'][:17]:<18} {owner_str[:80]}{overlap_flag}")


# ── Resources ON or OVERLAPPING FRS tenements ──
print("\n\n" + "=" * 100)
print("GOLD RESOURCES ON / OVERLAPPING FRS TENEMENTS")
print("=" * 100)

on_frs = [sr for sr in site_records if sr['overlapping_frs']]
on_frs.sort(key=lambda x: x['total_oz'], reverse=True)

if on_frs:
    print(f"\nFound {len(on_frs)} gold resources on FRS tenements:\n")
    for sr in on_frs:
        owner_str = '; '.join(o['name'] for o in sr['owners'] if o['name']) or 'Unknown'
        print(f"  {sr['name']} ({sr['project']})")
        print(f"    Resource: {sr['total_oz']:,.0f} oz Au | {sr['total_mt']:.3f} Mt @ {sr['avg_grade']:.2f} g/t")
        print(f"    Stage: {sr['stage']} | Owner: {owner_str}")
        print(f"    FRS tenements: {', '.join(sr['overlapping_frs'])}")
        print(f"    All site tenements: {', '.join(sr['all_tenements'][:10])}")
        print()
else:
    print("\nNo MINEDEX gold resource estimates directly overlapping FRS tenement IDs.")
    print("(Note: some resources may be on ground FRS acquired post-MINEDEX extract date)\n")


# ── Owner breakdown for nearby resources by project ──
print("\n" + "=" * 100)
print("DETAILED OWNERSHIP — ALL NEARBY GOLD PROJECTS WITH RESOURCES")
print("Sorted by total contained gold")
print("=" * 100)

proj_agg = defaultdict(lambda: {'sites': [], 'total_oz': 0})
for sr in site_records:
    key = sr['project'] or 'Unknown'
    proj_agg[key]['sites'].append(sr)
    proj_agg[key]['total_oz'] += sr['total_oz']
    if 'project_code' not in proj_agg[key]:
        proj_agg[key]['project_code'] = sr['project_code']

for proj_name, pdata in sorted(proj_agg.items(), key=lambda x: x[1]['total_oz'], reverse=True):
    proj_code = pdata.get('project_code', '')
    owner_list = owners.get(proj_code, [])
    psites = pdata['sites']
    min_dist = min(s['distance_km'] for s in psites)
    stages = set(s['stage'] for s in psites)

    print(f"\n  {proj_name} (code: {proj_code})")
    print(f"    Total gold: {pdata['total_oz']:,.0f} oz across {len(psites)} resource sites")
    print(f"    Closest to FRS: {min_dist:.1f} km | Stages: {', '.join(stages)}")
    print(f"    Owners:")
    if owner_list:
        for o in owner_list:
            pct = f" ({o['pct']}%)" if o['pct'] and o['pct'] != 'Unknown' else ''
            print(f"      - {o['name']}{pct}")
    else:
        print(f"      - No owner recorded in MINEDEX")

    # Show top 5 sites in this project
    top_sites = sorted(psites, key=lambda x: x['total_oz'], reverse=True)[:5]
    for s in top_sites:
        overlap = " ** FRS GROUND **" if s['overlapping_frs'] else ""
        print(f"      Site: {s['name']} — {s['total_oz']:,.0f} oz, {s['avg_grade']:.2f} g/t, "
              f"{s['stage']}, {s['distance_km']:.1f}km{overlap}")
