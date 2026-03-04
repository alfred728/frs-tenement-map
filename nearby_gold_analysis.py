#!/usr/bin/env python3
"""
Nearby Gold Resources & Competing Tenements Analysis
=====================================================
Analyses DMIRS/MINEDEX data to find:
  1. Gold deposits/mines/resources near FRS tenement clusters
  2. Other companies holding tenements in the same areas
  3. JORC resource estimates for nearby gold projects
"""

import csv
import json
import math
import re
from collections import defaultdict
from pathlib import Path

# ── Config ──
BASE = Path("/Users/alfredlewis/Documents/Forrestania Resources")
MINEDEX = BASE / "ingestion/processed/maps/source/minedex"
CSV_DIR = BASE / "ingestion/processed/maps/source/csv"
MAP_HTML = BASE / "frs_tenement_timeline_map.html"
SEARCH_RADIUS_KM = 50  # radius around each FRS cluster centroid


def haversine_km(lat1, lon1, lat2, lon2):
    """Great-circle distance in km."""
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    return R * 2 * math.asin(math.sqrt(a))


def extract_frs_tenement_clusters():
    """Extract FRS tenement centroids from map GeoJSON and cluster them."""
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

    # Simple clustering by mining district (prefix before /)
    clusters = defaultdict(list)
    for t in tenements:
        # Extract district from tenement ID (e.g. E77/2210 -> 77)
        parts = t['id'].split('/')
        prefix = parts[0] if parts else ''
        district = re.sub(r'[A-Z]+', '', prefix)
        clusters[district].append(t)

    result = {}
    for dist, tlist in clusters.items():
        clat = sum(t['lat'] for t in tlist) / len(tlist)
        clon = sum(t['lon'] for t in tlist) / len(tlist)
        result[dist] = {
            'centroid_lat': clat,
            'centroid_lon': clon,
            'count': len(tlist),
            'tenement_ids': [t['id'] for t in tlist],
        }
    return result


def load_minedex_sites():
    """Load MINEDEX Sites.csv with coordinates."""
    sites = []
    with open(MINEDEX / "Sites.csv", newline='', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                lat = float(row['Latitude'])
                lon = float(row['Longitude'])
            except (ValueError, KeyError):
                continue
            sites.append({
                'code': row.get('SiteCode', ''),
                'name': row.get('ShortTitle', '') or row.get('Title', ''),
                'title': row.get('Title', ''),
                'type': row.get('Type', ''),
                'subtype': row.get('SubType', ''),
                'stage': row.get('Stage', ''),
                'commodities': row.get('Commodities', ''),
                'commodity_groups': row.get('CommodityGroups', ''),
                'target_commodity': row.get('TargetCommodityGroups', ''),
                'project': row.get('ProjectTitle', ''),
                'project_code': row.get('ProjectCode', ''),
                'lat': lat,
                'lon': lon,
                'mineralization': row.get('MineralizationStyle', ''),
                'district': row.get('DistrictName', '').strip(),
                'mapsheet': row.get('MapSheetName250k', ''),
            })
    return sites


def load_resource_estimates():
    """Load MINEDEX ResourceEstimates.csv."""
    estimates = []
    with open(MINEDEX / "ResourceEstimates.csv", newline='', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                lat = float(row['Latitude'])
                lon = float(row['Longitude'])
            except (ValueError, KeyError):
                continue
            try:
                qty = float(row.get('EstimateQuantity', 0))
            except ValueError:
                qty = 0
            try:
                grade = float(row.get('Grade', 0))
            except ValueError:
                grade = 0
            try:
                contained_oz = float(row.get('AlternativeContainedCommodity', 0))
            except ValueError:
                contained_oz = 0

            estimates.append({
                'code': row.get('ResourceCode', ''),
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
                'quantity_unit': row.get('EstimateQuantityUnit', ''),
                'grade': grade,
                'grade_unit': row.get('GradeUnit', ''),
                'contained_oz': contained_oz,
                'contained_unit': row.get('AlternativeContainedCommodityUnit', ''),
                'project': row.get('ProjectShortName', ''),
                'project_code': row.get('ProjectCode', ''),
                'lat': lat,
                'lon': lon,
            })
    return estimates


def load_project_owners():
    """Load project ownership data."""
    owners = defaultdict(list)
    with open(MINEDEX / "ProjectsOwners.csv", newline='', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            owners[row.get('ProjectCode', '')].append({
                'name': row.get('OwnerName', ''),
                'pct': row.get('HoldingPct', ''),
                'project': row.get('ProjectTitle', ''),
            })
    return owners


def load_current_tenements():
    """Load CurrentTenements.csv for holder info."""
    tenements = {}
    with open(CSV_DIR / "CurrentTenements.csv", newline='', encoding='latin-1') as f:
        reader = csv.DictReader(f)
        for row in reader:
            tid = row.get('FMT_TENID', '')
            tenements[tid] = {
                'id': tid,
                'type': row.get('TYPE', ''),
                'status': row.get('TENSTATUS', ''),
                'holder1': row.get('HOLDER1', ''),
                'all_holders': row.get('ALL_HOLDERS', ''),
                'area': row.get('LEGAL_AREA', ''),
                'unit': row.get('UNIT_OF_MEASURE', ''),
                'grant_date': row.get('GRANTDATE', ''),
                'end_date': row.get('ENDDATE', ''),
            }
    return tenements


def load_site_tenements():
    """Load SiteTenements.csv to link sites to tenement IDs."""
    links = defaultdict(list)
    with open(MINEDEX / "SiteTenements.csv", newline='', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            code = row.get('SiteCode', '')
            ten = row.get('TenementCode', '').strip()
            status = row.get('Status', '')
            links[code].append({'tenement': ten, 'status': status})
    return links


# ═══════════════════════════════════════════════════════
# MAIN ANALYSIS
# ═══════════════════════════════════════════════════════

print("=" * 80)
print("FORRESTANIA RESOURCES — NEARBY GOLD & TENEMENT ANALYSIS")
print("=" * 80)
print(f"Search radius: {SEARCH_RADIUS_KM} km around each FRS tenement cluster\n")

# 1. Load FRS clusters
clusters = extract_frs_tenement_clusters()
print(f"FRS tenement clusters (by mining district):")
for dist, info in sorted(clusters.items(), key=lambda x: x[1]['count'], reverse=True):
    print(f"  District {dist:>3s}: {info['count']:>3d} tenements  "
          f"centroid ({info['centroid_lat']:.3f}, {info['centroid_lon']:.3f})")

# 2. Load MINEDEX data
print("\nLoading MINEDEX data...")
sites = load_minedex_sites()
estimates = load_resource_estimates()
owners = load_project_owners()
site_tens = load_site_tenements()
current_tens = load_current_tenements()
print(f"  Sites: {len(sites):,}")
print(f"  Resource estimates: {len(estimates):,}")
print(f"  Current tenements: {len(current_tens):,}")

# 3. Find gold sites near FRS clusters
print("\n" + "=" * 80)
print("NEARBY GOLD DEPOSITS & MINES")
print("=" * 80)

# Deduplicate sites by code (some appear multiple times for different mineralization styles)
unique_sites = {}
for s in sites:
    key = s['code']
    if key not in unique_sites:
        unique_sites[key] = s

gold_nearby = []
for code, s in unique_sites.items():
    # Check if gold-related
    if 'GOLD' not in (s.get('target_commodity', '') or '').upper() and \
       'Au' not in (s.get('commodities', '') or '') and \
       'Gold' not in (s.get('commodities', '') or ''):
        continue

    # Check distance to any FRS cluster
    min_dist = float('inf')
    nearest_cluster = None
    for dist, info in clusters.items():
        d = haversine_km(s['lat'], s['lon'], info['centroid_lat'], info['centroid_lon'])
        if d < min_dist:
            min_dist = d
            nearest_cluster = dist

    if min_dist <= SEARCH_RADIUS_KM:
        s['distance_km'] = min_dist
        s['nearest_cluster'] = nearest_cluster
        gold_nearby.append(s)

gold_nearby.sort(key=lambda x: x['distance_km'])

# Group by project
project_sites = defaultdict(list)
for s in gold_nearby:
    proj = s.get('project', '') or 'Unknown'
    project_sites[proj].append(s)

print(f"\nFound {len(gold_nearby)} gold sites within {SEARCH_RADIUS_KM}km of FRS tenements")
print(f"Across {len(project_sites)} projects:\n")

for proj, psites in sorted(project_sites.items(), key=lambda x: min(s['distance_km'] for s in x[1])):
    closest = min(s['distance_km'] for s in psites)
    # Get owner info
    proj_code = psites[0].get('project_code', '')
    owner_info = owners.get(proj_code, [])
    owner_str = ', '.join(f"{o['name']} ({o['pct']}%)" for o in owner_info if o['name']) if owner_info else 'Unknown'

    types = set(s['type'] for s in psites)
    stages = set(s['stage'] for s in psites)
    print(f"  {proj}")
    print(f"    Sites: {len(psites)} | Types: {', '.join(types)} | Stages: {', '.join(stages)}")
    print(f"    Closest to FRS: {closest:.1f} km (district {psites[0]['nearest_cluster']})")
    print(f"    Owner(s): {owner_str}")
    # Show site names
    for s in psites[:5]:
        print(f"      - {s['name']} ({s['type']}, {s['stage']}) [{s['distance_km']:.1f}km]")
    if len(psites) > 5:
        print(f"      ... and {len(psites)-5} more sites")
    print()

# 4. Find resource estimates near FRS
print("=" * 80)
print("NEARBY GOLD RESOURCE ESTIMATES (JORC)")
print("=" * 80)

gold_estimates_nearby = []
for est in estimates:
    if 'Gold' not in (est.get('commodity', '') or '') and 'Au' not in (est.get('commodity_abbr', '') or ''):
        continue

    min_dist = float('inf')
    nearest = None
    for dist, info in clusters.items():
        d = haversine_km(est['lat'], est['lon'], info['centroid_lat'], info['centroid_lon'])
        if d < min_dist:
            min_dist = d
            nearest = dist

    if min_dist <= SEARCH_RADIUS_KM:
        est['distance_km'] = min_dist
        est['nearest_cluster'] = nearest
        gold_estimates_nearby.append(est)

# Aggregate by site
site_estimates = defaultdict(list)
for est in gold_estimates_nearby:
    site_estimates[est['short_title'] or est['site_name']].append(est)

print(f"\nFound {len(gold_estimates_nearby)} gold resource estimate records")
print(f"Across {len(site_estimates)} sites:\n")

# Sort by total contained ounces
site_totals = []
for site_name, ests in site_estimates.items():
    total_oz = sum(e['contained_oz'] for e in ests)
    total_mt = sum(e['quantity_mt'] for e in ests)
    avg_grade = sum(e['grade'] * e['quantity_mt'] for e in ests if e['quantity_mt'] > 0) / max(sum(e['quantity_mt'] for e in ests if e['quantity_mt'] > 0), 0.001)
    categories = set(e['category'] for e in ests)
    statuses = set(e['status'] for e in ests)
    min_dist = min(e['distance_km'] for e in ests)
    proj = ests[0].get('project', '')
    proj_code = ests[0].get('project_code', '')
    stage = ests[0].get('stage', '')

    site_totals.append({
        'name': site_name,
        'project': proj,
        'project_code': proj_code,
        'stage': stage,
        'total_oz': total_oz,
        'total_mt': total_mt,
        'avg_grade': avg_grade,
        'categories': categories,
        'statuses': statuses,
        'distance_km': min_dist,
        'n_estimates': len(ests),
    })

site_totals.sort(key=lambda x: x['total_oz'], reverse=True)

for st in site_totals:
    owner_info = owners.get(st['project_code'], [])
    owner_str = ', '.join(f"{o['name']}" for o in owner_info if o['name']) or 'Unknown'

    print(f"  {st['name']} ({st['project']})")
    print(f"    Total: {st['total_oz']:,.0f} oz Au | {st['total_mt']:.3f} Mt @ {st['avg_grade']:.2f} g/t")
    print(f"    Categories: {', '.join(st['categories'])} | Stage: {st['stage']}")
    print(f"    Distance to FRS: {st['distance_km']:.1f} km")
    print(f"    Owner(s): {owner_str}")
    print()

# 5. Summary of top gold resources by contained ounces
print("=" * 80)
print("TOP 20 NEARBY GOLD RESOURCES BY CONTAINED OUNCES")
print("=" * 80)
print(f"\n{'Rank':<5} {'Site':<30} {'Project':<30} {'Oz Au':>12} {'Mt':>8} {'g/t':>6} {'km':>6} {'Stage':<20}")
print("-" * 120)
for i, st in enumerate(site_totals[:20], 1):
    print(f"{i:<5} {st['name'][:29]:<30} {st['project'][:29]:<30} "
          f"{st['total_oz']:>12,.0f} {st['total_mt']:>8.3f} {st['avg_grade']:>6.2f} "
          f"{st['distance_km']:>6.1f} {st['stage'][:19]:<20}")

# 6. Nearby company analysis
print("\n" + "=" * 80)
print("COMPANIES WITH GOLD PROJECTS NEAR FRS")
print("=" * 80)

company_projects = defaultdict(list)
for st in site_totals:
    for o in owners.get(st['project_code'], []):
        if o['name']:
            company_projects[o['name']].append(st)

# Sort by total gold ounces per company
company_totals = []
for company, projs in company_projects.items():
    total_oz = sum(p['total_oz'] for p in projs)
    n_sites = len(projs)
    proj_names = list(set(p['project'] for p in projs))
    min_dist = min(p['distance_km'] for p in projs)
    company_totals.append({
        'company': company,
        'total_oz': total_oz,
        'n_sites': n_sites,
        'projects': proj_names,
        'min_distance': min_dist,
    })

company_totals.sort(key=lambda x: x['total_oz'], reverse=True)

print(f"\n{'Company':<45} {'Total Oz Au':>14} {'Sites':>6} {'Closest km':>11} {'Projects'}")
print("-" * 130)
for ct in company_totals[:30]:
    proj_str = ', '.join(ct['projects'][:3])
    if len(ct['projects']) > 3:
        proj_str += f" +{len(ct['projects'])-3} more"
    print(f"{ct['company'][:44]:<45} {ct['total_oz']:>14,.0f} {ct['n_sites']:>6} "
          f"{ct['min_distance']:>11.1f} {proj_str}")

# 7. Quick summary stats
print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)
total_nearby_oz = sum(st['total_oz'] for st in site_totals)
operating = [st for st in site_totals if 'operat' in st['stage'].lower()]
care_maint = [st for st in site_totals if 'care' in st['stage'].lower()]
undeveloped = [st for st in site_totals if 'undeveloped' in st['stage'].lower()]
print(f"  Total gold resource sites within {SEARCH_RADIUS_KM}km: {len(site_totals)}")
print(f"  Total contained gold nearby: {total_nearby_oz:,.0f} oz")
print(f"  Operating mines: {len(operating)}")
print(f"  Care & maintenance: {len(care_maint)}")
print(f"  Undeveloped deposits: {len(undeveloped)}")
print(f"  Unique companies: {len(company_totals)}")
print(f"  Largest nearby resource: {site_totals[0]['name']} ({site_totals[0]['total_oz']:,.0f} oz, {site_totals[0]['distance_km']:.1f}km)" if site_totals else "  None found")
