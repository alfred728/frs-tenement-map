#!/usr/bin/env python3
from __future__ import annotations

from datetime import date
from pathlib import Path
from xml.etree.ElementTree import Element, SubElement, tostring
from zipfile import ZIP_DEFLATED, ZipFile


NS_MAIN = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
NS_REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
NS_PKG_REL = "http://schemas.openxmlformats.org/package/2006/relationships"


def col_letter(index: int) -> str:
    value = index
    letters = []
    while value > 0:
        value, remainder = divmod(value - 1, 26)
        letters.append(chr(65 + remainder))
    return "".join(reversed(letters))


def cell_ref(row: int, col: int) -> str:
    return f"{col_letter(col)}{row}"


def add_cell(row_el: Element, row_num: int, col: int, kind: str, value: str | float | int) -> None:
    ref = cell_ref(row_num, col)
    if kind == "str":
        c = SubElement(row_el, "c", {"r": ref, "t": "inlineStr"})
        is_el = SubElement(c, "is")
        t = SubElement(is_el, "t")
        t.text = str(value)
    elif kind == "num":
        c = SubElement(row_el, "c", {"r": ref})
        v = SubElement(c, "v")
        v.text = str(value)
    elif kind == "formula":
        c = SubElement(row_el, "c", {"r": ref})
        f = SubElement(c, "f")
        f.text = str(value)
    else:
        raise ValueError(f"Unsupported cell kind: {kind}")


def build_sheet(rows: list[dict[int, tuple[str, str | float | int]]], max_col: int, max_row: int) -> bytes:
    worksheet = Element("worksheet", {"xmlns": NS_MAIN})
    SubElement(worksheet, "dimension", {"ref": f"A1:{col_letter(max_col)}{max_row}"})
    SubElement(worksheet, "sheetViews")
    SubElement(worksheet, "sheetFormatPr", {"defaultRowHeight": "15"})
    sheet_data = SubElement(worksheet, "sheetData")

    for row_num, row_cells in enumerate(rows, start=1):
        if not row_cells:
            continue
        row_el = SubElement(sheet_data, "row", {"r": str(row_num)})
        for col in sorted(row_cells):
            kind, value = row_cells[col]
            add_cell(row_el, row_num, col, kind, value)

    SubElement(worksheet, "pageMargins", {
        "left": "0.7",
        "right": "0.7",
        "top": "0.75",
        "bottom": "0.75",
        "header": "0.3",
        "footer": "0.3",
    })
    return tostring(worksheet, encoding="utf-8", xml_declaration=True)


def workbook_xml(sheet_names: list[str]) -> bytes:
    wb = Element("workbook", {"xmlns": NS_MAIN, "xmlns:r": NS_REL})
    sheets_el = SubElement(wb, "sheets")
    for i, name in enumerate(sheet_names, start=1):
        SubElement(
            sheets_el,
            "sheet",
            {"name": name, "sheetId": str(i), f"{{{NS_REL}}}id": f"rId{i}"},
        )
    return tostring(wb, encoding="utf-8", xml_declaration=True)


def workbook_rels_xml(sheet_count: int) -> bytes:
    rels = Element("Relationships", {"xmlns": NS_PKG_REL})
    for i in range(1, sheet_count + 1):
        SubElement(
            rels,
            "Relationship",
            {
                "Id": f"rId{i}",
                "Type": "http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet",
                "Target": f"worksheets/sheet{i}.xml",
            },
        )
    SubElement(
        rels,
        "Relationship",
        {
            "Id": f"rId{sheet_count + 1}",
            "Type": "http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles",
            "Target": "styles.xml",
        },
    )
    return tostring(rels, encoding="utf-8", xml_declaration=True)


def root_rels_xml() -> bytes:
    rels = Element("Relationships", {"xmlns": NS_PKG_REL})
    SubElement(
        rels,
        "Relationship",
        {
            "Id": "rId1",
            "Type": "http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument",
            "Target": "xl/workbook.xml",
        },
    )
    SubElement(
        rels,
        "Relationship",
        {
            "Id": "rId2",
            "Type": "http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties",
            "Target": "docProps/core.xml",
        },
    )
    SubElement(
        rels,
        "Relationship",
        {
            "Id": "rId3",
            "Type": "http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties",
            "Target": "docProps/app.xml",
        },
    )
    return tostring(rels, encoding="utf-8", xml_declaration=True)


def content_types_xml(sheet_count: int) -> bytes:
    types = Element("Types", {"xmlns": "http://schemas.openxmlformats.org/package/2006/content-types"})
    SubElement(types, "Default", {"Extension": "rels", "ContentType": "application/vnd.openxmlformats-package.relationships+xml"})
    SubElement(types, "Default", {"Extension": "xml", "ContentType": "application/xml"})
    SubElement(
        types,
        "Override",
        {
            "PartName": "/xl/workbook.xml",
            "ContentType": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml",
        },
    )
    for i in range(1, sheet_count + 1):
        SubElement(
            types,
            "Override",
            {
                "PartName": f"/xl/worksheets/sheet{i}.xml",
                "ContentType": "application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml",
            },
        )
    SubElement(
        types,
        "Override",
        {
            "PartName": "/xl/styles.xml",
            "ContentType": "application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml",
        },
    )
    SubElement(
        types,
        "Override",
        {
            "PartName": "/docProps/core.xml",
            "ContentType": "application/vnd.openxmlformats-package.core-properties+xml",
        },
    )
    SubElement(
        types,
        "Override",
        {
            "PartName": "/docProps/app.xml",
            "ContentType": "application/vnd.openxmlformats-officedocument.extended-properties+xml",
        },
    )
    return tostring(types, encoding="utf-8", xml_declaration=True)


def minimal_styles_xml() -> bytes:
    xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
  <fonts count="1"><font><sz val="11"/><name val="Calibri"/></font></fonts>
  <fills count="1"><fill><patternFill patternType="none"/></fill></fills>
  <borders count="1"><border/></borders>
  <cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>
  <cellXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/></cellXfs>
  <cellStyles count="1"><cellStyle name="Normal" xfId="0" builtinId="0"/></cellStyles>
</styleSheet>
"""
    return xml.encode("utf-8")


def core_props_xml() -> bytes:
    today = date.today().isoformat()
    xml = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties"
 xmlns:dc="http://purl.org/dc/elements/1.1/"
 xmlns:dcterms="http://purl.org/dc/terms/"
 xmlns:dcmitype="http://purl.org/dc/dcmitype/"
 xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <dc:title>FRS Cash Requirement Model</dc:title>
  <dc:creator>Codex</dc:creator>
  <cp:lastModifiedBy>Codex</cp:lastModifiedBy>
  <dcterms:created xsi:type="dcterms:W3CDTF">{today}T00:00:00Z</dcterms:created>
  <dcterms:modified xsi:type="dcterms:W3CDTF">{today}T00:00:00Z</dcterms:modified>
</cp:coreProperties>
"""
    return xml.encode("utf-8")


def app_props_xml() -> bytes:
    xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties"
 xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes">
  <Application>Codex</Application>
</Properties>
"""
    return xml.encode("utf-8")


def main() -> None:
    output = Path("FRS_cash_requirement_model_2026-02-23.xlsx")
    sheet_names = ["Summary", "Assumptions", "Cash_12M", "Options", "Commitments", "Sources"]

    summary = [
        {1: ("str", "FRS Cash Requirement Model (prepared 23-Feb-2026)")},
        {1: ("str", "Key outputs")},
        {1: ("str", "Indicative cash at forecast start (Mar-2026)"), 2: ("formula", "TEXT(Assumptions!B23/1000000,\"$0.000\")&\"m\""), 3: ("formula", "Assumptions!B23")},
        {1: ("str", "12M closing cash - Base case"), 2: ("formula", "TEXT(Cash_12M!L13/1000000,\"$0.000\")&\"m\""), 3: ("formula", "Cash_12M!L13")},
        {1: ("str", "12M closing cash - Incl. contingent max"), 2: ("formula", "TEXT(Cash_12M!N13/1000000,\"$0.000\")&\"m\""), 3: ("formula", "Cash_12M!N13")},
        {1: ("str", "Cash from known post-31-Dec option exercises"), 2: ("formula", "TEXT(Options!F10/1000000,\"$0.000\")&\"m\""), 3: ("formula", "Options!F10")},
        {1: ("str", "Potential cash from remaining $0.24 options"), 2: ("formula", "TEXT(Options!F13/1000000,\"$0.000\")&\"m\""), 3: ("formula", "Options!F13")},
        {1: ("str", "Potential cash from remaining $0.15 options"), 2: ("formula", "TEXT(Options!F14/1000000,\"$0.000\")&\"m\""), 3: ("formula", "Options!F14")},
        {1: ("str", "Total potential option cash"), 2: ("formula", "TEXT(Options!F15/1000000,\"$0.000\")&\"m\""), 3: ("formula", "Options!F15")},
        {},
        {1: ("str", "Notes")},
        {1: ("str", "Column B is formatted A$m text for readability; Column C remains raw A$ calculations.")},
        {1: ("str", "Model starts from reported 31-Dec-2025 cash and bridges known Jan-Feb 2026 events.")},
        {1: ("str", "Contingent milestone cash is separated from contracted cash and shown as a downside view.")},
        {1: ("str", "Polaris/Lake Johnston package and certain drilling are equity-settled and do not consume cash.")},
    ]

    assumptions = [
        {1: ("str", "Assumption"), 2: ("str", "Value (A$)"), 3: ("str", "Value (A$m)"), 4: ("str", "Comment")},
        {1: ("str", "Reported cash balance at 31-Dec-2025"), 2: ("num", 6714000), 3: ("formula", "TEXT(B2/1000000,\"$0.000\")&\"m\""), 4: ("str", "Appendix 5B item 4.6")},
        {1: ("str", "Placement Tranche 2 + SPP inflow in Jan-2026"), 2: ("num", 23000000), 3: ("formula", "TEXT(B3/1000000,\"$0.000\")&\"m\""), 4: ("str", "Quarterly: post-quarter raise total A$23m")},
        {1: ("str", "SPP component (included in line above)"), 2: ("num", 5000000), 3: ("formula", "TEXT(B4/1000000,\"$0.000\")&\"m\""), 4: ("str", "28,571,430 shares at A$0.175 on 19-Jan-2026")},
        {1: ("str", "Tranche 2 component (derived)"), 2: ("formula", "B3-B4"), 3: ("formula", "TEXT(B5/1000000,\"$0.000\")&\"m\""), 4: ("str", "Derived from total post-quarter raise less SPP")},
        {1: ("str", "Known post-31-Dec option exercise cash inflow"), 2: ("formula", "Options!F10"), 3: ("formula", "TEXT(B6/1000000,\"$0.000\")&\"m\""), 4: ("str", "Jan/Feb Appendix 2A and cleansing notices")},
        {1: ("str", "MacPhersons non-refundable deposit paid"), 2: ("num", 500000), 3: ("formula", "TEXT(B7/1000000,\"$0.000\")&\"m\""), 4: ("str", "Execution deposit disclosed 16-Feb-2026")},
        {1: ("str", "Monthly baseline operating cash burn"), 2: ("num", 991667), 3: ("formula", "TEXT(B8/1000000,\"$0.000\")&\"m\""), 4: ("str", "A$2.975m relevant outgoings per quarter / 3")},
        {1: ("str", "MacPhersons completion cash (contracted)"), 2: ("num", 4500000), 3: ("formula", "TEXT(B9/1000000,\"$0.000\")&\"m\""), 4: ("str", "Subject to conditions precedent and completion")},
        {1: ("str", "MacPhersons completion month index"), 2: ("num", 2), 3: ("str", "-"), 4: ("str", "1=Mar-26, 2=Apr-26 ...")},
        {1: ("str", "Contingent: Mt Dimer/Mt Jackson/Johnson deferred cash max"), 2: ("num", 3000000), 3: ("formula", "TEXT(B11/1000000,\"$0.000\")&\"m\""), 4: ("str", "Milestone-linked; up to A$3m across 3 project areas")},
        {1: ("str", "Contingent: Gibraltar additional cash max"), 2: ("num", 2700000), 3: ("formula", "TEXT(B12/1000000,\"$0.000\")&\"m\""), 4: ("str", "50% cash component of additional consideration cap")},
        {1: ("str", "Contingent: Aurumin JR/MD top-up cash max"), 2: ("num", 2400000), 3: ("formula", "TEXT(B13/1000000,\"$0.000\")&\"m\""), 4: ("str", "Could be cash, shares, or combination")},
        {1: ("str", "Remaining FRSAA options (exercise A$0.24)"), 2: ("num", 187976460), 3: ("formula", "TEXT(B14/1000000,\"$0.000\")&\"m\""), 4: ("str", "As per 20-Feb-2026 Appendix 2A")},
        {1: ("str", "Remaining FRSOA options (exercise A$0.15)"), 2: ("num", 20221873), 3: ("formula", "TEXT(B15/1000000,\"$0.000\")&\"m\""), 4: ("str", "As per 20-Feb-2026 Appendix 2A")},
        {},
        {1: ("str", "Derived bridge metrics")},
        {1: ("str", "Indicative cash before forecast start"), 2: ("formula", "B2+B3+B6-B7"), 3: ("formula", "TEXT(B18/1000000,\"$0.000\")&\"m\""), 4: ("str", "Starts from 31-Dec cash then adds known Jan/Feb flows")},
        {1: ("str", "Contracted outstanding cash commitments"), 2: ("formula", "B9"), 3: ("formula", "TEXT(B19/1000000,\"$0.000\")&\"m\""), 4: ("str", "Current hard obligation identified")},
        {1: ("str", "Maximum contingent cash exposure"), 2: ("formula", "B11+B12+B13"), 3: ("formula", "TEXT(B20/1000000,\"$0.000\")&\"m\""), 4: ("str", "Resource/approval/election dependent")},
    ]

    months = ["Mar-26", "Apr-26", "May-26", "Jun-26", "Jul-26", "Aug-26", "Sep-26", "Oct-26", "Nov-26", "Dec-26", "Jan-27", "Feb-27"]
    cash_sheet = [{1: ("str", "Month"), 2: ("str", "Opening (A$)"), 3: ("str", "Opening (A$m)"), 4: ("str", "Operating burn (A$)"), 5: ("str", "Operating burn (A$m)"), 6: ("str", "Contracted outflow (A$)"), 7: ("str", "Contracted outflow (A$m)"), 8: ("str", "Option inflow (A$)"), 9: ("str", "Option inflow (A$m)"), 10: ("str", "Net movement (A$)"), 11: ("str", "Net movement (A$m)"), 12: ("str", "Closing (A$)"), 13: ("str", "Closing (A$m)"), 14: ("str", "Closing incl contingent (A$)"), 15: ("str", "Closing incl contingent (A$m)")}]
    for idx, month in enumerate(months, start=2):
        month_index_formula = f"ROW()-1"
        open_formula = "Assumptions!B23" if idx == 2 else f"L{idx-1}"
        contracted_formula = f'IF({month_index_formula}=Assumptions!B10,-Assumptions!B9,0)'
        option_formula = "0"
        net_formula = f"B{idx}+D{idx}+F{idx}+H{idx}"
        close_formula = f"B{idx}+J{idx}"
        contingent_monthly = f"-(Assumptions!B11+Assumptions!B12+Assumptions!B13)/12"
        close_worst = f"B{idx}+D{idx}+F{idx}+H{idx}+{contingent_monthly}"
        cash_sheet.append({
            1: ("str", month),
            2: ("formula", open_formula),
            3: ("formula", f"TEXT(B{idx}/1000000,\"$0.000\")&\"m\""),
            4: ("formula", "-Assumptions!B8"),
            5: ("formula", f"TEXT(D{idx}/1000000,\"$0.000\")&\"m\""),
            6: ("formula", contracted_formula),
            7: ("formula", f"TEXT(F{idx}/1000000,\"$0.000\")&\"m\""),
            8: ("formula", option_formula),
            9: ("formula", f"TEXT(H{idx}/1000000,\"$0.000\")&\"m\""),
            10: ("formula", f"D{idx}+F{idx}+H{idx}"),
            11: ("formula", f"TEXT(J{idx}/1000000,\"$0.000\")&\"m\""),
            12: ("formula", close_formula),
            13: ("formula", f"TEXT(L{idx}/1000000,\"$0.000\")&\"m\""),
            14: ("formula", close_worst),
            15: ("formula", f"TEXT(N{idx}/1000000,\"$0.000\")&\"m\""),
        })

    cash_sheet.append({
        1: ("str", "Total 12M"),
        4: ("formula", "SUM(D2:D13)"),
        5: ("formula", "TEXT(D14/1000000,\"$0.000\")&\"m\""),
        6: ("formula", "SUM(F2:F13)"),
        7: ("formula", "TEXT(F14/1000000,\"$0.000\")&\"m\""),
        8: ("formula", "SUM(H2:H13)"),
        9: ("formula", "TEXT(H14/1000000,\"$0.000\")&\"m\""),
        10: ("formula", "SUM(J2:J13)"),
        11: ("formula", "TEXT(J14/1000000,\"$0.000\")&\"m\""),
        12: ("formula", "L13"),
        13: ("formula", "TEXT(L14/1000000,\"$0.000\")&\"m\""),
        14: ("formula", "N13"),
        15: ("formula", "TEXT(N14/1000000,\"$0.000\")&\"m\""),
    })

    options_sheet = [
        {1: ("str", "Date"), 2: ("str", "Instrument"), 3: ("str", "Shares issued"), 4: ("str", "Exercise price"), 5: ("str", "Cash inflow (A$)"), 6: ("str", "Cash inflow (A$m)"), 7: ("str", "Source note")},
        {1: ("str", "23-Jan-2026"), 2: ("str", "FRSOA"), 3: ("num", 1285558), 4: ("num", 0.15), 5: ("formula", "C2*D2"), 6: ("formula", "TEXT(E2/1000000,\"$0.000\")&\"m\""), 7: ("str", "Appendix 2A in Filings.pdf")},
        {1: ("str", "02-Feb-2026"), 2: ("str", "FRSOA"), 3: ("num", 85601), 4: ("num", 0.15), 5: ("formula", "C3*D3"), 6: ("formula", "TEXT(E3/1000000,\"$0.000\")&\"m\""), 7: ("str", "Cleansing statement")},
        {1: ("str", "13-Feb-2026"), 2: ("str", "FRSOA"), 3: ("num", 396000), 4: ("num", 0.15), 5: ("formula", "C4*D4"), 6: ("formula", "TEXT(E4/1000000,\"$0.000\")&\"m\""), 7: ("str", "Appendix 2A")},
        {1: ("str", "13-Feb-2026"), 2: ("str", "FRSAA"), 3: ("num", 1118521), 4: ("num", 0.24), 5: ("formula", "C5*D5"), 6: ("formula", "TEXT(E5/1000000,\"$0.000\")&\"m\""), 7: ("str", "Appendix 2A")},
        {1: ("str", "18-Feb-2026"), 2: ("str", "FRSOA"), 3: ("num", 383771), 4: ("num", 0.15), 5: ("formula", "C6*D6"), 6: ("formula", "TEXT(E6/1000000,\"$0.000\")&\"m\""), 7: ("str", "Appendix 2A")},
        {1: ("str", "18-Feb-2026"), 2: ("str", "FRSAA"), 3: ("num", 3756047), 4: ("num", 0.24), 5: ("formula", "C7*D7"), 6: ("formula", "TEXT(E7/1000000,\"$0.000\")&\"m\""), 7: ("str", "Appendix 2A")},
        {1: ("str", "20-Feb-2026"), 2: ("str", "FRSAA"), 3: ("num", 1112649), 4: ("num", 0.24), 5: ("formula", "C8*D8"), 6: ("formula", "TEXT(E8/1000000,\"$0.000\")&\"m\""), 7: ("str", "Appendix 2A")},
        {},
        {1: ("str", "Known post-31-Dec option exercise inflow total"), 5: ("formula", "SUM(E2:E8)"), 6: ("formula", "TEXT(E10/1000000,\"$0.000\")&\"m\"")},
        {},
        {1: ("str", "Remaining option cash potential"), 2: ("str", "Remaining options"), 3: ("str", "Exercise price"), 4: ("str", "Potential cash (A$)"), 5: ("str", "Exercise %)"), 6: ("str", "Scenario cash (A$m)")},
        {1: ("str", "FRSAA (0.24)"), 2: ("formula", "Assumptions!B14"), 3: ("num", 0.24), 4: ("formula", "B13*C13"), 5: ("num", 1), 6: ("formula", "D13*E13")},
        {1: ("str", "FRSOA (0.15)"), 2: ("formula", "Assumptions!B15"), 3: ("num", 0.15), 4: ("formula", "B14*C14"), 5: ("num", 1), 6: ("formula", "D14*E14")},
        {1: ("str", "Total potential"), 4: ("formula", "SUM(D13:D14)"), 6: ("formula", "TEXT(SUM(D13:D14)/1000000,\"$0.000\")&\"m\"")},
    ]
    options_sheet[12][6] = ("formula", "TEXT(D13*E13/1000000,\"$0.000\")&\"m\"")
    options_sheet[13][6] = ("formula", "TEXT(D14*E14/1000000,\"$0.000\")&\"m\"")

    commitments_sheet = [
        {1: ("str", "Item"), 2: ("str", "Cash impact (A$)"), 3: ("str", "Cash impact (A$m)"), 4: ("str", "Status"), 5: ("str", "Expected timing"), 6: ("str", "Settlement type"), 7: ("str", "Comment")},
        {1: ("str", "MacPhersons acquisition deposit"), 2: ("num", -500000), 4: ("str", "Paid"), 5: ("str", "Feb-2026"), 6: ("str", "Cash"), 7: ("str", "Non-refundable deposit on execution")},
        {1: ("str", "MacPhersons acquisition completion payment"), 2: ("num", -4500000), 4: ("str", "Outstanding"), 5: ("str", "Post-27 Mar 2026 (if conditions met)"), 6: ("str", "Cash"), 7: ("str", "Conditioned on approvals/completion")},
        {1: ("str", "Mt Dimer/Mt Jackson/Johnson milestones"), 2: ("num", -3000000), 4: ("str", "Contingent"), 5: ("str", "Resource milestone dependent"), 6: ("str", "Cash or shares"), 7: ("str", "Up to A$3m deferred consideration")},
        {1: ("str", "Gibraltar additional consideration cash component"), 2: ("num", -2700000), 4: ("str", "Contingent"), 5: ("str", "JORC milestone dependent"), 6: ("str", "Cash + shares"), 7: ("str", "Cash component can scale with milestone outcomes")},
        {1: ("str", "Aurumin JR/MD top-up"), 2: ("num", -2400000), 4: ("str", "Contingent"), 5: ("str", "Resource announcement dependent"), 6: ("str", "Cash or shares"), 7: ("str", "At company election, up to A$2.4m")},
        {1: ("str", "Lake Johnston acquisition related cost"), 2: ("num", -10000000), 4: ("str", "Historical"), 5: ("str", "Q2 FY26"), 6: ("str", "Cash"), 7: ("str", "Already reflected in 31-Dec-2025 cash balance")},
        {1: ("str", "Lake Johnston part consideration shares"), 2: ("num", 0), 4: ("str", "Issued"), 5: ("str", "19-Jan-2026"), 6: ("str", "Equity"), 7: ("str", "28,571,429 shares at A$0.175 (non-cash)")},
        {1: ("str", "Polaris crushing circuit refurbishment"), 2: ("num", 0), 4: ("str", "Committed"), 5: ("str", "Approx. 25 weeks"), 6: ("str", "Equity"), 7: ("str", "A$5m contract paid in FRS scrip")},
        {1: ("str", "Drilling services consideration shares"), 2: ("num", 0), 4: ("str", "Proposed"), 5: ("str", "04-Mar-2026"), 6: ("str", "Equity"), 7: ("str", "A$100k estimated value, final by VWAP")},
        {},
        {1: ("str", "Contracted outstanding cash (from current commitments)"), 2: ("formula", "SUM(B3)")},
        {1: ("str", "Maximum contingent additional cash exposure"), 2: ("formula", "SUM(B4:B6)")},
    ]
    for idx in range(2, len(commitments_sheet) + 1):
        if commitments_sheet[idx - 1].get(2) and commitments_sheet[idx - 1][2][0] in ("num", "formula"):
            commitments_sheet[idx - 1][3] = ("formula", f"TEXT(B{idx}/1000000,\"$0.000\")&\"m\"")
        else:
            commitments_sheet[idx - 1].setdefault(3, ("str", ""))

    sources_sheet = [
        {1: ("str", "Source filing"), 2: ("str", "Key data used")},
        {1: ("str", "Second Quarter Activities Report (29-Jan-2026)"), 2: ("str", "31-Dec cash A$6.714m; post-quarter Tranche 2 + SPP total A$23m; Lake Johnston cash outflow A$10m in quarter")},
        {1: ("str", "Notice of General Meeting (23-Feb-2026)"), 2: ("str", "Capital raising option terms; acquisition consideration terms and contingencies")},
        {1: ("str", "Appendix 2A (21-Jan-2026)"), 2: ("str", "SPP issue 28,571,430 shares at A$0.175")},
        {1: ("str", "Appendix 2A (16/19/20-Feb-2026)"), 2: ("str", "Option exercise quantities and issue prices for FRSOA and FRSAA")},
        {1: ("str", "Cleansing Statements (23-Jan-2026 and 02-Feb-2026)"), 2: ("str", "FRSOA exercise volumes")},
        {1: ("str", "Asset Acquisition release (10-Dec-2025)"), 2: ("str", "Mt Dimer/Mt Jackson/Johnston deferred milestone payment structure")},
        {1: ("str", "Asset Acquisition / Appendix 3B (16-Feb-2026)"), 2: ("str", "MacPhersons A$5m cash structure (A$0.5m deposit + A$4.5m completion)")},
        {1: ("str", "Progress Report (22-Feb-2026)"), 2: ("str", "Polaris crushing circuit A$5m paid in scrip")},
        {1: ("str", "Appendix 3B (19-Feb-2026)"), 2: ("str", "A$100k drilling services to be settled in equity")},
    ]

    sheets = [summary, assumptions, cash_sheet, options_sheet, commitments_sheet, sources_sheet]
    max_cols = [3, 4, 15, 7, 7, 2]
    max_rows = [max(len(s), 20) for s in sheets]

    with ZipFile(output, "w", compression=ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", content_types_xml(len(sheet_names)))
        zf.writestr("_rels/.rels", root_rels_xml())
        zf.writestr("docProps/core.xml", core_props_xml())
        zf.writestr("docProps/app.xml", app_props_xml())
        zf.writestr("xl/workbook.xml", workbook_xml(sheet_names))
        zf.writestr("xl/_rels/workbook.xml.rels", workbook_rels_xml(len(sheet_names)))
        zf.writestr("xl/styles.xml", minimal_styles_xml())
        for i, (sheet_rows, max_col, max_row) in enumerate(zip(sheets, max_cols, max_rows), start=1):
            zf.writestr(f"xl/worksheets/sheet{i}.xml", build_sheet(sheet_rows, max_col=max_col, max_row=max_row))

    print(output)


if __name__ == "__main__":
    main()
