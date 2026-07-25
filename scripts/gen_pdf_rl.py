"""Generate Hevy training report PDF using reportlab."""
import glob, os, datetime, textwrap, sys
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor, white, black
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, PageBreak
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

# -- Colours ------------------------------------------------------------------
NAVY   = HexColor("#1a2744")
BLUE   = HexColor("#4a90ff")
LBLUE  = HexColor("#7eb3ff")
GREEN  = HexColor("#22c55e")
AMBER  = HexColor("#f59e0b")
RED    = HexColor("#ef4444")
CARD   = HexColor("#f8faff")
BGCOL  = HexColor("#f0f4f8")
DARK   = HexColor("#374151")
MID    = HexColor("#6b7280")

# -- Unicode sanitizer --------------------------------------------------------
_MAP = str.maketrans({
    "|": "|",  "┃": "|",  "║": "|",
    "─": "-",  "━": "-",  "═": "=",
    "┌": "+",  "┐": "+",  "└": "+",  "┘": "+",
    "├": "+",  "┤": "+",  "┬": "+",  "┴": "+",  "┼": "+",
    "╠": "+",  "╣": "+",  "╦": "+",  "╩": "+",  "╬": "+",
    "→": "->", "←": "<-", "↑": "^",  "↓": "v",
    "≥": ">=", "≤": "<=", "·": ".",
    "•": "*",  "●": "*",  "–": "-",  "—": "--",
    "×": "x",  "°": "deg",
    "‘": "'", "’": "'", "“": '"', "”": '"',
    "…": "...",
})

def S(text):
    """Sanitize text for reportlab (XML-safe + ASCII)."""
    t = str(text).translate(_MAP)
    t = t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return t

# -- Locate files -------------------------------------------------------------
report_files = sorted(glob.glob("report_*.txt"), reverse=True)
if not report_files:
    print("No report file found"); sys.exit(1)

report_path = report_files[0]
today       = datetime.date.today()
pdf_name    = f"hevy_report_{today}.pdf"

with open(report_path, encoding="utf-8") as f:
    raw_lines = f.read().splitlines()

# -- Styles -------------------------------------------------------------------
styles = getSampleStyleSheet()

def mkstyle(name, **kw):
    return ParagraphStyle(name, **kw)

style_body = mkstyle("body",
    fontName="Helvetica", fontSize=9.5, leading=13,
    textColor=DARK, spaceAfter=2)

style_mono = mkstyle("mono",
    fontName="Courier", fontSize=8, leading=11,
    textColor=DARK, backColor=CARD,
    leftIndent=4, spaceAfter=1)

style_section = mkstyle("section",
    fontName="Helvetica-Bold", fontSize=11,
    textColor=white, backColor=NAVY,
    spaceAfter=4, spaceBefore=8,
    leftIndent=4, leading=16)

style_bullet = mkstyle("bullet",
    fontName="Helvetica", fontSize=9, leading=12,
    textColor=DARK, leftIndent=12, spaceAfter=2,
    bulletText="*", bulletIndent=4)

style_title = mkstyle("title",
    fontName="Helvetica-Bold", fontSize=26,
    textColor=white, alignment=TA_CENTER, leading=32)

style_subtitle = mkstyle("subtitle",
    fontName="Helvetica", fontSize=12,
    textColor=LBLUE, alignment=TA_CENTER, leading=16)

style_label = mkstyle("label",
    fontName="Helvetica-Bold", fontSize=9,
    textColor=LBLUE, alignment=TA_CENTER,
    leading=12, spaceAfter=0)

# -- Title page ---------------------------------------------------------------
def build_title_page(date_range):
    elems = []
    elems.append(Spacer(1, 48*mm))
    elems.append(Paragraph("HEVY TRAINING INTELLIGENCE", style_label))
    elems.append(Spacer(1, 2*mm))
    elems.append(Paragraph("30-Day Analysis Report", style_title))
    elems.append(Spacer(1, 3*mm))
    elems.append(Paragraph(S(date_range), style_subtitle))
    elems.append(Spacer(1, 16*mm))

    profile_data = [
        ["Name", "Ganesh"],
        ["Profile", "44M  |  181 cm  |  87 kg -> 79 kg"],
        ["Goal", "Body Recomposition -- Fat loss, muscle preservation"],
        ["Pace", "0.5 kg/week  |  15% calorie deficit"],
        ["Generated", str(today)],
    ]
    tbl = Table(profile_data, colWidths=[40*mm, 110*mm])
    tbl.setStyle(TableStyle([
        ("FONTNAME",  (0,0), (-1,-1), "Helvetica"),
        ("FONTNAME",  (0,0), (0,-1),  "Helvetica-Bold"),
        ("FONTSIZE",  (0,0), (-1,-1), 9),
        ("TEXTCOLOR", (0,0), (0,-1),  NAVY),
        ("TEXTCOLOR", (1,0), (1,-1),  DARK),
        ("BACKGROUND",(0,0), (-1,-1), CARD),
        ("ROWBACKGROUNDS", (0,0), (-1,-1), [CARD, white]),
        ("BOX",       (0,0), (-1,-1), 0.5, HexColor("#dce4f5")),
        ("INNERGRID", (0,0), (-1,-1), 0.3, HexColor("#e5eaf5")),
        ("LEFTPADDING",  (0,0),(-1,-1), 8),
        ("RIGHTPADDING", (0,0),(-1,-1), 8),
        ("TOPPADDING",   (0,0),(-1,-1), 5),
        ("BOTTOMPADDING",(0,0),(-1,-1), 5),
    ]))
    elems.append(tbl)
    elems.append(PageBreak())
    return elems

# -- Page canvas callbacks ----------------------------------------------------
PAGE_W, PAGE_H = A4

def on_first_page(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(NAVY)
    canvas.rect(0, PAGE_H - 70*mm, PAGE_W, 70*mm, fill=1, stroke=0)
    canvas.setFillColor(BLUE)
    canvas.rect(0, 0, PAGE_W, 10*mm, fill=1, stroke=0)
    canvas.setFillColor(white)
    canvas.setFont("Helvetica-Bold", 8)
    canvas.drawCentredString(PAGE_W/2, 3.5*mm, "POWERED BY HEVY AGENT  *  CLAUDE AI")
    canvas.restoreState()

def on_later_pages(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(NAVY)
    canvas.rect(0, PAGE_H - 8*mm, PAGE_W, 8*mm, fill=1, stroke=0)
    canvas.setFillColor(MID)
    canvas.setFont("Helvetica-Oblique", 7.5)
    canvas.drawRightString(PAGE_W - 18*mm, PAGE_H - 5.5*mm,
                           f"Hevy Training Report - Ganesh - {today}")
    canvas.setStrokeColor(HexColor("#cccccc"))
    canvas.line(18*mm, 14*mm, PAGE_W - 18*mm, 14*mm)
    canvas.setFillColor(MID)
    canvas.setFont("Helvetica-Oblique", 7)
    footer = f"Page {canvas.getPageNumber()}  |  Generated {today}  |  Confidential - Ganesh"
    canvas.drawCentredString(PAGE_W/2, 10*mm, footer)
    canvas.restoreState()

# -- Parse report lines -------------------------------------------------------
def is_section_header(line):
    s = line.strip()
    if not s:
        return False
    if all(c in "=--" for c in s):
        return False
    return (s.isupper() and len(s) > 3) or s.startswith("###") or (
        s.startswith("#") and not s.startswith("##"))

def clean_header(line):
    return line.strip().lstrip("#").strip()

def parse_report(lines):
    elems = []
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if not stripped:
            elems.append(Spacer(1, 2*mm))
            i += 1
            continue

        if len(stripped) >= 4 and all(c in "=--" for c in stripped):
            elems.append(HRFlowable(width="100%", thickness=0.5,
                                    color=HexColor("#dce4f5")))
            i += 1
            continue

        if is_section_header(line):
            elems.append(Paragraph(S(clean_header(line)), style_section))
            i += 1
            continue

        if stripped.startswith("##"):
            sub = clean_header(line)
            substy = mkstyle("sub"+str(i),
                fontName="Helvetica-Bold", fontSize=10,
                textColor=NAVY, spaceBefore=4, spaceAfter=2, leading=13)
            elems.append(Paragraph(S(sub), substy))
            i += 1
            continue

        if stripped.startswith(("- ", "* ", "• ")):
            content = stripped[2:].strip()
            if content:
                elems.append(Paragraph(S(content), style_bullet))
            i += 1
            continue

        if "|" in stripped or stripped.startswith("+") or stripped.startswith("  "):
            elems.append(Paragraph(S(stripped), style_mono))
            i += 1
            continue

        elems.append(Paragraph(S(stripped), style_body))
        i += 1

    return elems

# -- Extract date range -------------------------------------------------------
date_range = f"30-Day Period ending {today}"
for line in raw_lines[:6]:
    if "Period" in line and ("to" in line or ":" in line):
        candidate = line.strip().replace("Period :", "").replace("Period:", "").strip()
        if candidate:
            date_range = candidate
        break

# -- Assemble document --------------------------------------------------------
doc = SimpleDocTemplate(
    pdf_name,
    pagesize=A4,
    leftMargin=18*mm, rightMargin=18*mm,
    topMargin=14*mm, bottomMargin=20*mm,
    title=f"Hevy 30-Day Report -- Ganesh -- {today}",
    author="Hevy Agent",
)

story = build_title_page(date_range) + parse_report(raw_lines)
doc.build(story, onFirstPage=on_first_page, onLaterPages=on_later_pages)
size = os.path.getsize(pdf_name)
print(f"PDF written: {pdf_name}  ({size:,} bytes)")
