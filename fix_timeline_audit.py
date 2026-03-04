#!/usr/bin/env python3
"""
FRS Timeline Audit Fix Script
Fixes all issues identified in the comprehensive audit:
1. Date corrections (5 events)
2. ACE Group naming update
3. Split Geraghty/Hodgins event
4. Add 7 missing material events
"""
import json, re, sys

MAP_FILE = '/Users/alfredlewis/Documents/Forrestania Resources/frs_tenement_timeline_map.html'

# Read the file
with open(MAP_FILE) as f:
    lines = f.readlines()

# Find and parse the EVENTS line (line 290, 0-indexed = 289)
events_line_idx = None
for i, line in enumerate(lines):
    if line.strip().startswith('const EVENTS = '):
        events_line_idx = i
        break

if events_line_idx is None:
    print("ERROR: Could not find EVENTS line")
    sys.exit(1)

print(f"Found EVENTS on line {events_line_idx + 1}")

raw = lines[events_line_idx].strip()
json_str = raw[len('const EVENTS = '):]
if json_str.endswith(';'):
    json_str = json_str[:-1]

events = json.loads(json_str)
print(f"Parsed {len(events)} events")

# ═══════════════════════════════════════════════════════════
# FIX 1: Date corrections
# ═══════════════════════════════════════════════════════════
date_fixes = {
    # (old_date, title_fragment): new_date
}

for e in events:
    # Event 12: Kula BID 2025-10-13 → 2025-10-14
    if e['date'] == '2025-10-13' and 'Bid Implementation Deed' in e['title']:
        print(f"  FIX DATE: Kula BID {e['date']} → 2025-10-14")
        e['date'] = '2025-10-14'

    # Event 13: Horizon announcement 2025-11-13 → 2025-11-14
    if e['date'] == '2025-11-13' and 'Horizon Minerals' in e['title']:
        print(f"  FIX DATE: Horizon {e['date']} → 2025-11-14")
        e['date'] = '2025-11-14'

    # Event 14: Lake Johnston 2025-11-17 → 2025-11-18
    if e['date'] == '2025-11-17' and 'Lake Johnston acquisition HOA' in e['title']:
        print(f"  FIX DATE: Lake Johnston {e['date']} → 2025-11-18")
        e['date'] = '2025-11-18'

    # Event 19: Kula unconditional 2025-12-22 → 2025-12-23
    if e['date'] == '2025-12-22' and 'unconditional' in e['title']:
        print(f"  FIX DATE: Kula unconditional {e['date']} → 2025-12-23")
        e['date'] = '2025-12-23'

# ═══════════════════════════════════════════════════════════
# FIX 2: ACE Group naming → formal SGH/Wroxby
# ═══════════════════════════════════════════════════════════
for e in events:
    if 'ACE Group' in e['title']:
        old_title = e['title']
        e['title'] = 'Wroxby Pty Ltd (Australian Capital Equity / SGH) + Timothy Roberts / Goodoil emerge as substantial shareholders'
        e['strategic_impact'] = e['strategic_impact'].replace(
            'Wroxby Pty Ltd (ACE Group/Stokes)',
            'Wroxby Pty Ltd (Australian Capital Equity / SGH Limited)'
        )
        print(f"  FIX NAMING: ACE Group → Wroxby Pty Ltd (Australian Capital Equity / SGH)")

# ═══════════════════════════════════════════════════════════
# FIX 3: Split Geraghty/Hodgins event
# ═══════════════════════════════════════════════════════════
split_idx = None
for i, e in enumerate(events):
    if 'Geraghty transitions to Executive Chairman' in e['title'] and 'Hodgins' in e['title']:
        split_idx = i
        break

if split_idx is not None:
    old_event = events[split_idx]

    # Update Geraghty event (keep in place, fix date to 2025-11-18)
    old_event['date'] = '2025-11-18'
    old_event['title'] = 'David Geraghty transitions to Executive Chairman'
    old_event['strategic_impact'] = (
        "Operational shift: FRS moves from acquisition-building to hands-on development. "
        "Geraghty (ex-MinRes metallurgical engineer, 30+ years experience) transitions from "
        "Non-Executive Chairman to Executive Chairman effective 17 November 2025. "
        "$500K/annum package (subject to shareholder approval; willing to take in equity) "
        "signals institutional executive standard."
    )
    print(f"  SPLIT: Geraghty event updated → 2025-11-18")

    # Create new Hodgins event
    hodgins_event = {
        "idx": 0,  # Will be recalculated
        "date": "2025-12-05",
        "phase": 4,
        "phase_name": "Infrastructure Play",
        "phase_full": "4 – Infrastructure Play – Lake Johnston",
        "title": "Brett Hodgins appointed Technical Director",
        "strategic_impact": (
            "Senior mining professional with 25+ years experience across iron ore, gold, copper and coal "
            "appointed Technical Director effective 8 December 2025. NED of Beacon Minerals (Jaurdi Gold "
            "Project, directly neighbouring FRS's Bonnie Vale projects) and Redstone Resources. Previously "
            "President & CEO of Central Iron Ore for over a decade. Board now has both corporate (Geraghty) "
            "and technical (Hodgins) development leadership for the transition to gold production."
        ),
        "tenement_ids": [],
        "missing_ids": [],
        "new_ids": [],
        "tenements_added_story": 0,
        "counterparties": "",
        "consideration": "",
        "project": "",
        "confidence": "high",
        "cum_tenements": old_event['cum_tenements'],
        "cum_area_km2": old_event['cum_area_km2'],
        "is_kula": False
    }
    events.append(hodgins_event)
    print(f"  SPLIT: New Hodgins event created → 2025-12-05")

# ═══════════════════════════════════════════════════════════
# FIX 4: Add missing material events
# ═══════════════════════════════════════════════════════════

# Helper to find cum_tenements/area from nearest existing event
def get_nearest_cum(events, target_date):
    """Get cumulative values from the nearest event before target_date"""
    best = {"cum_tenements": 0, "cum_area_km2": 0}
    for e in events:
        if e['date'] <= target_date:
            best = {"cum_tenements": e['cum_tenements'], "cum_area_km2": e['cum_area_km2']}
    return best

new_events = [
    # 1. Bonnie Vale option secured
    {
        "date": "2024-12-16",
        "phase": 1,
        "phase_name": "Leadership Reset",
        "phase_full": "1 – Leadership Reset & Strategy Pivot",
        "title": "Key tenement under option at Bonnie Vale Project (E15/1972)",
        "strategic_impact": (
            "Secured 12-month option over E15/1972 for $15,000 fee (Amery Holdings Pty Ltd). "
            "Acquisition price $35,000 payable in shares at 5-day VWAP. Tenement hosts southern "
            "extension of the Kunanalling Shear Zone, adjacent to Evolution Mining's Mungari Project. "
            "First move into the Coolgardie gold district before the board restructure."
        ),
        "tenement_ids": ["E15/1972"],
        "missing_ids": [],
        "new_ids": ["E15/1972"],
        "tenements_added_story": 1,
        "counterparties": "Amery Holdings Pty Ltd",
        "consideration": "$35,000 in shares",
        "project": "Bonnie Vale",
        "confidence": "high",
        "is_kula": False
    },
    # 2. Billy Higgins resignation
    {
        "date": "2025-06-23",
        "phase": 1,
        "phase_name": "Leadership Reset",
        "phase_full": "1 – Leadership Reset & Strategy Pivot",
        "title": "Billy Higgins resigns as Non-Executive Director",
        "strategic_impact": (
            "William (Billy) Higgins tendered his resignation to pursue other interests. "
            "Originally appointed 3 June 2021, he was instrumental in managing the Company's "
            "exploration portfolio from inception and through IPO. Departure completes the board "
            "refresh ahead of the acquisition blitz that begins in August."
        ),
        "tenement_ids": [],
        "missing_ids": [],
        "new_ids": [],
        "tenements_added_story": 0,
        "counterparties": "",
        "consideration": "",
        "project": "",
        "confidence": "high",
        "is_kula": False
    },
    # 3. Bonnie Vale gold rights binding agreement
    {
        "date": "2025-08-12",
        "phase": 2,
        "phase_name": "Acquisition Blitz",
        "phase_full": "2 – Acquisition Blitz – Gold Pipeline",
        "title": "Binding agreement for gold rights at Bonnie Vale (P15/6113, M15/1934)",
        "strategic_impact": (
            "Acquired gold rights on P15/6113 and mining lease application M15/1934, located directly "
            "north of Ada Ann gold project (E15/1632). 2.5% net smelter return royalty to vendor on "
            "completion. Consolidates FRS's Coolgardie/Bonnie Vale position adjacent to Evolution "
            "Mining's Mungari operation."
        ),
        "tenement_ids": ["P15/6113", "M15/1934"],
        "missing_ids": [],
        "new_ids": ["P15/6113", "M15/1934"],
        "tenements_added_story": 2,
        "counterparties": "",
        "consideration": "2.5% NSR royalty",
        "project": "Bonnie Vale",
        "confidence": "high",
        "is_kula": False
    },
    # 4. TG Metals 249D notice
    {
        "date": "2025-10-10",
        "phase": 3,
        "phase_name": "Kula Convergence",
        "phase_full": "3 – Kula Convergence – Takeover",
        "title": "Section 249D notice served on TG Metals (ASX: TG6); 10.3% stake acquired",
        "strategic_impact": (
            "FRS acquired a 10.3% strategic stake in TG Metals Limited at an average price of 18.2c/share "
            "and served a Section 249D notice seeking board changes. TG Metals' Lake Yindarlgooda project "
            "is in the Eastern Goldfields. On 29 October, FRS confirmed no current intention to proceed "
            "with a takeover bid. As at 31 Dec 2025, held 11.7M TG6 shares worth ~$2.33M."
        ),
        "tenement_ids": [],
        "missing_ids": [],
        "new_ids": [],
        "tenements_added_story": 0,
        "counterparties": "TG Metals Limited",
        "consideration": "~$2.1M (10.3% stake)",
        "project": "",
        "confidence": "high",
        "is_kula": False
    },
    # 5. Catalina Resources asset swap
    {
        "date": "2026-01-13",
        "phase": 4,
        "phase_name": "Infrastructure Play",
        "phase_full": "4 – Infrastructure Play – Lake Johnston",
        "title": "Catalina Resources asset swap — acquires Laverton Project, divests Breakaway Dam",
        "strategic_impact": (
            "Binding asset swap with Catalina Resources (ASX: CTN). FRS acquires 3 Laverton Exploration "
            "Licences (E38/3697, E38/3698, E38/3847) in exchange for E29/1037 (Breakaway Dam copper). "
            "FRS receives ~10% equity in CTN via 13.8M shares + 20.7M options. Adds Eastern Goldfields "
            "exposure in the Laverton gold district. Subject to shareholder approvals."
        ),
        "tenement_ids": ["E38/3697", "E38/3698", "E38/3847"],
        "missing_ids": [],
        "new_ids": ["E38/3697", "E38/3698", "E38/3847"],
        "tenements_added_story": 3,
        "counterparties": "Catalina Resources Limited",
        "consideration": "E29/1037 + 10% CTN equity",
        "project": "Laverton",
        "confidence": "high",
        "is_kula": False
    },
    # 6. Options Prospectus lodged
    {
        "date": "2026-01-28",
        "phase": 4,
        "phase_name": "Infrastructure Play",
        "phase_full": "4 – Infrastructure Play – Lake Johnston",
        "title": "Options Prospectus lodged with ASIC (up to 192.2M New Options at $0.24)",
        "strategic_impact": (
            "Prospectus offers up to 192,207,796 free attaching New Options to Eligible Placement and SPP "
            "participants (1 option for every 1.1 shares subscribed). Exercise price $0.24, 3-year expiry. "
            "If all exercised, Company would receive approximately $46.1M in additional capital. Provides "
            "further funding runway for the transition to gold production."
        ),
        "tenement_ids": [],
        "missing_ids": [],
        "new_ids": [],
        "tenements_added_story": 0,
        "counterparties": "",
        "consideration": "",
        "project": "",
        "confidence": "high",
        "is_kula": False
    },
    # 7. OzAurum Resources 19.9% investment
    {
        "date": "2026-01-30",
        "phase": 5,
        "phase_name": "Production Pathway",
        "phase_full": "5 – Production Pathway",
        "title": "19.9% strategic investment in OzAurum Resources (ASX: OZM) — $4.1M",
        "strategic_impact": (
            "Subscribed for 56.9M OzAurum shares at $0.072/share (10-day VWAP) for A$4.1M total. "
            "Cornerstone investment in OzAurum's Mulgabbie North gold project in the Eastern Goldfields, "
            "~130km NE of Kalgoorlie. Became substantial holder (19.9%) on 3 February 2026. Expands FRS's "
            "strategic footprint via equity stakes alongside direct tenement acquisitions."
        ),
        "tenement_ids": [],
        "missing_ids": [],
        "new_ids": [],
        "tenements_added_story": 0,
        "counterparties": "OzAurum Resources Limited",
        "consideration": "$4.1M",
        "project": "Mulgabbie North",
        "confidence": "high",
        "is_kula": False
    },
]

# Add cum_tenements/area to new events
for ne in new_events:
    cum = get_nearest_cum(events, ne['date'])
    ne['cum_tenements'] = cum['cum_tenements']
    ne['cum_area_km2'] = cum['cum_area_km2']
    events.append(ne)
    print(f"  ADD: {ne['date']} — {ne['title'][:70]}")

# ═══════════════════════════════════════════════════════════
# Sort by date and re-index
# ═══════════════════════════════════════════════════════════
events.sort(key=lambda e: (e['date'], e.get('idx', 999)))
for i, e in enumerate(events):
    e['idx'] = i

print(f"\nTotal events after fixes: {len(events)}")
print("\nFinal event list:")
for e in events:
    print(f"  {e['idx']:2d}. {e['date']} | {e['title'][:80]}")

# ═══════════════════════════════════════════════════════════
# Write back to file
# ═══════════════════════════════════════════════════════════
new_events_json = json.dumps(events, ensure_ascii=False, separators=(',', ':'))
new_line = f"const EVENTS = {new_events_json};\n"

lines[events_line_idx] = new_line

with open(MAP_FILE, 'w') as f:
    f.writelines(lines)

print(f"\n✅ Written {len(events)} events back to {MAP_FILE}")
print(f"   Line {events_line_idx + 1}: {len(new_line)} chars")
