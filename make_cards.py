#!/usr/bin/env python3
"""
make_cards.py - build printable A6 "recipe cards" from the practicals database.

Each experiment gets one card: the front is the student procedure, the back is
the technician kit list. Cards are laid out 4-up on A4 and the backs are
mirrored so that printing duplex (flip on long edge) lines each back up with
its front.

    pip install reportlab
    python make_cards.py                         # every experiment -> cards.pdf
    python make_cards.py --level GCSE            # only GCSE (matches GCSE/A-Level too)
    python make_cards.py --board AQA --required  # AQA required practicals only
    python make_cards.py --ids GCSE-01 GCSE-04 --out my-cards.pdf

Text that does not fit is shrunk, then truncated with an ellipsis, so check
long experiments before printing a class set.
"""
import argparse
import csv
from collections import defaultdict
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas

HERE = Path(__file__).parent
PAGE_W, PAGE_H = A4
CARD_W, CARD_H = PAGE_W / 2, PAGE_H / 2
M = 7 * mm  # inner margin
LEVEL_COLOURS = {"GCSE": "#2a78d6", "A-Level": "#d97706", "GCSE/A-Level": "#059669"}
BOARDS = {"AQA": "AQA req'd", "OCR": "OCR req'd", "Edexcel": "Edexcel req'd"}

# DejaVu covers the ✓ ★ ° Δ symbols in the data; fall back to Helvetica if absent.
FONT, BOLD = "Helvetica", "Helvetica-Bold"
try:
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    import reportlab, os
    for cand in ["/usr/share/fonts/truetype/dejavu", "/Library/Fonts", os.path.expanduser("~/Library/Fonts")]:
        reg, bold = Path(cand) / "DejaVuSans.ttf", Path(cand) / "DejaVuSans-Bold.ttf"
        if reg.exists() and bold.exists():
            pdfmetrics.registerFont(TTFont("DejaVu", str(reg)))
            pdfmetrics.registerFont(TTFont("DejaVu-Bold", str(bold)))
            FONT, BOLD = "DejaVu", "DejaVu-Bold"
            break
except Exception:
    pass


def wrap(text, font, size, width):
    lines = []
    for para in str(text).split("\n"):
        words, line = para.split(), ""
        for w in words:
            trial = f"{line} {w}".strip()
            if stringWidth(trial, font, size) <= width:
                line = trial
            else:
                if line:
                    lines.append(line)
                line = w
        lines.append(line)
    return lines


def method_steps(method):
    """'1. Do this. 2. Do that.' -> ['1. Do this.', '2. Do that.']"""
    import re
    parts = re.split(r"\s(?=\d{1,2}\.\s)", method.strip())
    return "\n".join(p.strip() for p in parts if p.strip())


def draw_block(c, x, y, width, bottom, sections, size):
    """Draw (heading, body) sections top-down. Returns True if everything fitted."""
    lead = size * 1.25
    for head, body in sections:
        if not body:
            continue
        if y - lead < bottom:
            return False
        c.setFont(BOLD, size)
        c.drawString(x, y - size, head)
        y -= lead
        for ln in wrap(body, FONT, size, width):
            if y - lead < bottom:
                c.setFont(FONT, size)
                c.drawString(x, y - size, "…")
                return False
            c.setFont(FONT, size)
            c.drawString(x, y - size, ln)
            y -= lead
        y -= lead * 0.4
    return True


def fit_sections(c, x, top, width, bottom, sections, sizes=(8, 7.5, 7, 6.5, 6)):
    for s in sizes:
        c.saveState()
        probe = canvas.Canvas("/dev/null")  # dry run on a throwaway canvas
        if draw_block(probe, x, top, width, bottom, sections, s):
            c.restoreState()
            draw_block(c, x, top, width, bottom, sections, s)
            return
        c.restoreState()
    draw_block(c, x, top, width, bottom, sections, sizes[-1])


def header(c, x0, y0, exp, subtitle):
    col = colors.HexColor(LEVEL_COLOURS.get(exp["Level"], "#444444"))
    c.setFillColor(col)
    c.rect(x0, y0 + CARD_H - 16 * mm, CARD_W, 16 * mm, stroke=0, fill=1)
    c.setFillColor(colors.white)
    c.setFont(BOLD, 12)
    title = exp["Title"]
    while stringWidth(title, BOLD, 12) > CARD_W - 2 * M and len(title) > 4:
        title = title[:-2]
    c.drawString(x0 + M, y0 + CARD_H - 8 * mm, title if title == exp["Title"] else title + "…")
    c.setFont(FONT, 7.5)
    boards = [b for b, col_ in BOARDS.items() if exp.get(col_, "").strip()]
    tags = [exp["ID"], exp["Level"], exp["Topic"], subtitle]
    if boards:
        tags.append("Required: " + ", ".join(boards))
    if exp.get("Freq. examined", "").strip():
        tags.append("★ often examined")
    line, size = "  ·  ".join(t for t in tags if t), 7.5
    while stringWidth(line, FONT, size) > CARD_W - 2 * M and size > 5:
        size -= 0.25
    c.setFont(FONT, size)
    c.drawString(x0 + M, y0 + CARD_H - 13 * mm, line)
    c.setFillColor(colors.black)


def front(c, x0, y0, exp):
    header(c, x0, y0, exp, "Student")
    sections = [
        ("Aim", exp["Aim"]),
        ("Variables", exp["Key variables"]),
        ("Method", method_steps(exp["Method"])),
        ("Measure", exp["Measurements"]),
        ("Analysis", exp["Analysis"]),
        ("Safety", exp["Safety"]),
    ]
    fit_sections(c, x0 + M, y0 + CARD_H - 19 * mm, CARD_W - 2 * M, y0 + M, sections)


def back(c, x0, y0, exp, kit):
    header(c, x0, y0, exp, "Technician")
    items = "\n".join(
        f"☐ {k['Item']}" + (f"  ×{k['Qty per group']}" if k["Qty per group"] else "")
        + (f"  ({k['Notes / specification']})" if k["Notes / specification"] else "")
        for k in kit
    )
    sections = [
        ("Kit per group", items or "—"),
        ("Preparation", exp.get("Technician preparation notes", "")),
        ("Time", f"{exp['Time (min)']} min" if exp.get("Time (min)") else ""),
    ]
    fit_sections(c, x0 + M, y0 + CARD_H - 19 * mm, CARD_W - 2 * M, y0 + M, sections)


def cut_marks(c):
    c.setStrokeColor(colors.HexColor("#bbbbbb"))
    c.setDash(2, 3)
    c.line(PAGE_W / 2, 0, PAGE_W / 2, PAGE_H)
    c.line(0, PAGE_H / 2, PAGE_W, PAGE_H / 2)
    c.setDash()
    c.setStrokeColor(colors.black)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data", type=Path, default=HERE / "data")
    ap.add_argument("--out", type=Path, default=Path("cards.pdf"))
    ap.add_argument("--level", help="GCSE or A-Level")
    ap.add_argument("--board", choices=BOARDS)
    ap.add_argument("--required", action="store_true", help="with --board: required practicals only")
    ap.add_argument("--ids", nargs="*", help="only these experiment IDs")
    a = ap.parse_args()

    exps = list(csv.DictReader(open(a.data / "experiments.csv", encoding="utf-8")))
    kit = defaultdict(list)
    for k in csv.DictReader(open(a.data / "equipment.csv", encoding="utf-8")):
        kit[k["Experiment ID"]].append(k)

    if a.level:
        exps = [e for e in exps if a.level.lower() in e["Level"].lower()]
    if a.board and a.required:
        exps = [e for e in exps if e[BOARDS[a.board]].strip()]
    if a.ids:
        wanted = set(a.ids)
        exps = [e for e in exps if e["ID"] in wanted]
    if not exps:
        raise SystemExit("No experiments match those filters.")

    # slot order on the page: top-left, top-right, bottom-left, bottom-right
    slots = [(0, CARD_H), (CARD_W, CARD_H), (0, 0), (CARD_W, 0)]
    mirrored = [(CARD_W, CARD_H), (0, CARD_H), (CARD_W, 0), (0, 0)]  # long-edge flip
    c = canvas.Canvas(str(a.out), pagesize=A4)
    c.setTitle("Practical recipe cards")
    for i in range(0, len(exps), 4):
        batch = exps[i:i + 4]
        for e, (x, y) in zip(batch, slots):
            front(c, x, y, e)
        cut_marks(c)
        c.showPage()
        for e, (x, y) in zip(batch, mirrored):
            back(c, x, y, e, kit[e["ID"]])
        cut_marks(c)
        c.showPage()
    c.save()
    print(f"{len(exps)} cards -> {a.out} ({(len(exps) + 3) // 4 * 2} pages, print duplex, flip on long edge)")


if __name__ == "__main__":
    main()
