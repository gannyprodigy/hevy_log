# Step 4: PDF Generation & Commit

## 4a — Install dependency
```bash
pip install fpdf2 --quiet
```

## 4b — Write and run the PDF generator

Write the following Python script to `/tmp/gen_pdf.py`, filling in the dynamic values (DATE, date range) from the actual files present. Then run it with `python3 /tmp/gen_pdf.py`.

The output PDF must be named `hevy_report_YYYY-MM-DD.pdf` (today's date).

```python
import glob, os, datetime, textwrap
from fpdf import FPDF

# ── Unicode → Latin-1 sanitizer (fpdf2 built-in fonts are Latin-1 only) ──────
_UNICODE_MAP = str.maketrans({
    "\u2502": "|",  "\u2503": "|",  "\u2551": "|",   # │ ┃ ║ → |
    "\u2500": "-",  "\u2501": "-",  "\u2550": "=",   # ─ ━ ═ → - =
    "\u250c": "+",  "\u2510": "+",  "\u2514": "+",  "\u2518": "+",  # corners → +
    "\u251c": "+",  "\u2524": "+",  "\u252c": "+",  "\u2534": "+",  "\u253c": "+",  # junctions
    "\u2560": "+",  "\u2563": "+",  "\u2566": "+",  "\u2569": "+",  "\u256c": "+",  # double-line junctions
    "\u2192": "->", "\u2190": "<-", "\u2191": "^",  "\u2193": "v",  # arrows
    "\u2265": ">=", "\u2264": "<=", "\u00b7": ".",                   # math
    "\u2022": "*",  "\u25cf": "*",  "\u2013": "-",  "\u2014": "--", # bullets, dashes
    "\u00d7": "x",  "\u00b0": "deg",                                  # misc
})

def sanitize(text):
    return text.translate(_UNICODE_MAP).encode("latin-1", errors="replace").decode("latin-1")

# ── Locate files ─────────────────────────────────────────────────────────────
report_files = sorted(glob.glob("report_*.txt"), reverse=True)
if not report_files:
    print("No report file found"); exit(1)

report_path = report_files[0]
today       = datetime.date.today()
pdf_name    = f"hevy_report_{today}.pdf"

with open(report_path, encoding="utf-8") as f:
    report_text = f.read()

lines = report_text.splitlines()

# ── Detect section headers (ALL CAPS lines or lines starting with ###) ───────
def is_section_header(line):
    stripped = line.strip()
    return (
        stripped.isupper() and len(stripped) > 3
    ) or stripped.startswith("###") or (
        stripped.startswith("#") and not stripped.startswith("##")
    )

def clean_header(line):
    return line.strip().lstrip("#").strip()

# ── PDF class ─────────────────────────────────────────────────────────────────
class HevyPDF(FPDF):
    def __init__(self):
        super().__init__()
        self.set_margins(18, 18, 18)
        self.set_auto_page_break(auto=True, margin=22)

    def header(self):
        if self.page_no() == 1:
            return
        # Thin top accent bar
        self.set_fill_color(26, 39, 68)       # dark navy
        self.rect(0, 0, 210, 8, "F")
        self.set_y(12)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(120, 120, 120)
        self.cell(0, 5, f"Hevy Training Report - Ganesh - {today}", align="R", ln=True)
        self.ln(2)

    def footer(self):
        self.set_y(-14)
        self.set_draw_color(200, 200, 200)
        self.line(18, self.get_y(), 192, self.get_y())
        self.ln(1)
        self.set_font("Helvetica", "I", 7.5)
        self.set_text_color(150, 150, 150)
        self.cell(0, 5, f"Page {self.page_no()}  |  Generated {today}  |  Confidential - Ganesh", align="C")

    def title_page(self, date_range):
        self.add_page()
        self.set_auto_page_break(False)   # prevent bottom bar from spilling to page 2
        # Full-width navy header block
        self.set_fill_color(26, 39, 68)
        self.rect(0, 0, 210, 80, "F")

        # Logo-style top text
        self.set_y(18)
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(100, 160, 255)
        self.cell(0, 7, "HEVY TRAINING INTELLIGENCE", align="C", ln=True)

        # Main title
        self.set_font("Helvetica", "B", 28)
        self.set_text_color(255, 255, 255)
        self.cell(0, 14, "30-Day Analysis Report", align="C", ln=True)

        # Subtitle
        self.set_font("Helvetica", "", 12)
        self.set_text_color(180, 210, 255)
        self.cell(0, 8, date_range, align="C", ln=True)

        # White card area
        self.set_y(90)
        self.set_text_color(40, 40, 40)

        # Profile card
        self.set_fill_color(245, 247, 252)
        self.set_draw_color(220, 228, 245)
        self.rect(30, 95, 150, 48, "FD")

        self.set_y(102)
        self.set_font("Helvetica", "B", 11)
        self.set_text_color(26, 39, 68)
        self.cell(0, 8, "ATHLETE PROFILE", align="C", ln=True)

        self.set_font("Helvetica", "", 10)
        self.set_text_color(60, 60, 60)
        profile_lines = [
            ("Name", "Ganesh"),
            ("Profile", "44M  |  181 cm  |  87 kg → 79 kg"),
            ("Goal", "Body Recomposition — Fat loss, muscle preservation"),
            ("Pace", "0.5 kg/week  |  15% calorie deficit"),
        ]
        for label, value in profile_lines:
            self.set_x(38)
            self.set_font("Helvetica", "B", 9)
            self.set_text_color(26, 39, 68)
            self.cell(32, 6, f"{label}:", ln=False)
            self.set_font("Helvetica", "", 9)
            self.set_text_color(50, 50, 50)
            self.cell(0, 6, value, ln=True)

        # Generated date
        self.set_y(158)
        self.set_font("Helvetica", "I", 9)
        self.set_text_color(130, 130, 130)
        self.cell(0, 6, f"Generated on {today}", align="C", ln=True)

        # Decorative bottom bar
        self.set_fill_color(74, 144, 255)
        self.rect(0, 280, 210, 17, "F")
        self.set_y(284)
        self.set_font("Helvetica", "B", 8)
        self.set_text_color(255, 255, 255)
        self.cell(0, 6, "POWERED BY HEVY AGENT  *  CLAUDE AI", align="C")
        self.set_auto_page_break(True, 22)   # restore for content pages

    def section_header(self, text):
        self.ln(4)
        # Coloured band
        self.set_fill_color(26, 39, 68)
        self.set_text_color(255, 255, 255)
        self.set_font("Helvetica", "B", 11)
        self.cell(0, 8, f"  {text}", ln=True, fill=True)
        self.set_text_color(40, 40, 40)
        self.ln(2)

    def subsection_header(self, text):
        self.ln(2)
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(26, 39, 68)
        self.set_draw_color(74, 144, 255)
        self.line(18, self.get_y() + 4, 60, self.get_y() + 4)
        self.cell(0, 7, f"  {text}", ln=True)
        self.set_text_color(40, 40, 40)

    def body_line(self, text):
        self.set_font("Helvetica", "", 9.5)
        self.set_text_color(40, 40, 40)
        stripped = text.strip()
        # Skip horizontal-rule lines (--- / === / --- from markdown)
        if stripped and all(c in "-=~" for c in stripped):
            return
        # Indent bullet lines
        if stripped.startswith(("-", "•", "*")):
            content = stripped.lstrip("-•* ").strip()
            if not content:          # bare "-" with no text — skip
                return
            self.set_x(22)
            self.set_font("Helvetica", "", 9)
            self.set_text_color(26, 39, 68)
            self.cell(4, 5, "*", ln=False)
            self.set_text_color(50, 50, 50)
            self.multi_cell(0, 5, sanitize(content))
        elif stripped.startswith("|"):
            # Table row — monospaced
            self.set_font("Courier", "", 8)
            self.set_x(18)
            self.set_fill_color(245, 247, 252)
            self.cell(0, 5, sanitize(stripped), ln=True, fill=True)
        elif stripped == "":
            self.ln(2)
        else:
            for chunk in textwrap.wrap(sanitize(text), width=100) or [""]:
                self.set_x(18)
                self.multi_cell(0, 5.5, chunk)

# ── Build PDF ─────────────────────────────────────────────────────────────────
pdf = HevyPDF()
pdf.set_title(f"Hevy 30-Day Report — Ganesh — {today}")
pdf.set_author("Hevy Agent")

# Extract date range from first lines of report
date_range = f"30-Day Period ending {today}"
for line in lines[:5]:
    if "Period" in line or "period" in line or "to" in line.lower():
        date_range = line.strip().replace("Period :", "").replace("Period:", "").strip()
        break

pdf.title_page(date_range)
pdf.add_page()   # first content page (title page is page 1)

for line in lines:
    stripped = line.strip()
    if not stripped:
        pdf.ln(1)
        continue
    if is_section_header(line):
        pdf.section_header(clean_header(line))
    elif stripped.startswith("##"):
        pdf.subsection_header(clean_header(line))
    else:
        pdf.body_line(line)

pdf.output(pdf_name)
print(f"PDF written: {pdf_name}  ({os.path.getsize(pdf_name):,} bytes)")
```

## 4c — Verify the PDF was created
```bash
ls -lh hevy_report_*.pdf
```

If the PDF is 0 bytes or missing, print the error from gen_pdf.py and stop.

## 4d — Commit and push all files

Run these commands exactly (no `git config` calls — identity is set via env vars):

```bash
git checkout main 2>/dev/null || true

GIT_AUTHOR_NAME=Bot GIT_AUTHOR_EMAIL=x@x.com GIT_COMMITTER_NAME=Bot GIT_COMMITTER_EMAIL=x@x.com \
  git add -A

GIT_AUTHOR_NAME=Bot GIT_AUTHOR_EMAIL=x@x.com GIT_COMMITTER_NAME=Bot GIT_COMMITTER_EMAIL=x@x.com \
  git diff --cached --quiet || \
  GIT_AUTHOR_NAME=Bot GIT_AUTHOR_EMAIL=x@x.com GIT_COMMITTER_NAME=Bot GIT_COMMITTER_EMAIL=x@x.com \
  git commit -m "report-$(date +%F)"

git push https://${GH_PAT}@github.com/gannyprodigy/hevy_log.git HEAD:main
```

Confirm the push succeeded and list the files committed.
