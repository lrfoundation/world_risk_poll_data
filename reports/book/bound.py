"""Build the bound volume: every published report PDF, one chapter each.

    python reports/book/bound.py            # writes output/World_Risk_Poll_reports_bound.pdf
    python reports/book/bound.py --screen   # also writes a smaller copy for reading on screen

The published PDFs are downloaded once from the addresses in
reports/report_inventory.csv into .cache/pdfs/. They are reproduced page for
page; nothing in them is redrawn. This script adds a title page, a contents
page, an opening page for each poll and each chapter (the same designs as the
coffee table book, see build.py), a running footer and the book's page numbers.

The page is A4 landscape with 3 mm bleed, and the PDF carries trim and bleed
boxes, so it can go to a printer as it is. A4 and A3 have the same proportions,
so the same file prints at either size.

The reports were published in four shapes. Landscape reports are placed one
page to a sheet. The A4 portrait reports (2019 and the 2021 core reports) are
placed two pages to a sheet, as the pages face each other in print. The 2019
report was published as one volume; its ten chapters are grouped into four
(SPLIT_2019 in content.py) and its appendices follow the fourth.

Needs PyMuPDF (pip install pymupdf) and a Chrome, Chromium or Edge.
"""

import argparse
import csv
import sys
import urllib.request
from html import escape
from pathlib import Path

import pymupdf

import build
from build import CACHE, HERE, OUT, Book, big, foot, font_faces, print_pdf, stat_value, title_html
from content import REPORTS, SPLIT_2019, WAVES
from figures import Figures

TITLE = "World Risk Poll: the reports, 2019 to 2025"
PDFS = CACHE / "pdfs"

# Page geometry, in points. The designed pages are drawn at 1920 by 1369 px,
# which has the proportions of the page with its bleed.
MM = 72 / 25.4
TRIM_W, TRIM_H, BLEED = 297 * MM, 210 * MM, 3 * MM
TOP, BOTTOM, OUTER, INNER = 22, 40, 28, 48      # margins around a reproduced page
MUTED, KEYLINE = (0.37, 0.36, 0.36), (0.74, 0.74, 0.74)

# The 2019 report, as 0-based pages of its PDF: (first, last) inclusive.
FRONT_2019 = (0, 16)                             # cover to the introduction
CHAPTERS_2019 = {1: (17, 30), 2: (31, 53), 3: (54, 71), 4: (72, 86), 5: (87, 111), 6: (112, 125),
                 7: (126, 140), 8: (141, 152), 9: (153, 170), 10: (171, 182)}
APPENDICES_2019 = (183, 214)


def rgb(colour):
    return tuple(int(colour[i:i + 2], 16) / 255 for i in (1, 3, 5))


def inventory():
    with open(HERE.parent / "report_inventory.csv", encoding="utf-8") as f:
        return {row["folder"]: row for row in csv.DictReader(f)}


def report_pdf(folder, rows):
    """The published PDF for a report folder, downloaded once."""
    path = PDFS / (folder.split("/")[1] + ".pdf")
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        request = urllib.request.Request(rows[folder]["pdf_url"], headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(request, timeout=600) as response:
            path.write_bytes(response.read())
    return path


def right_hand(doc_name, index):
    """Whether a page of a portrait report is a right-hand page in print."""
    if "2019" in doc_name:
        return index in (0, 2) or (index >= 3 and index % 2 == 1)
    return index % 2 == 0   # the cover is page 1


def sheets(doc, name, indexes):
    """Group a report's pages into sheets of the book.

    A landscape page takes a sheet to itself. Portrait pages go two to a
    sheet, left-hand page on the left; a page whose partner is not next to it
    keeps its own side.
    """
    out = []
    for i in indexes:
        page = doc[i]
        box = page.trimbox
        if box.width > box.height:
            out.append([(i, "full")])
            continue
        side = "right" if right_hand(name, i) else "left"
        if side == "right" and out and len(out[-1]) == 1 and out[-1][0][1] == "left":
            out[-1].append((i, "right"))
        else:
            out.append([(i, side)])
    return out


class Bound(Book):
    """The designed pages of the bound volume, in the coffee table book's templates."""

    folio = 0

    def add(self, html, cls, wave=None):
        html = html.replace(escape(build.BOOK), escape(TITLE)).replace("Reports in this book", "Chapters in this book")
        wave_cls = f" w{wave}" if wave else ""
        self.pages.append(f'<section class="page {cls}{wave_cls}">{html.replace("{PAGE}", str(self.folio))}</section>')
        return self.folio

    def title_page(self):
        art = self.world.svg(1700, 830, lambda c: ("#FFFFFF", 0.16), stroke="#E3076E", stroke_width=1)
        years = "<br>".join(str(y) for y in WAVES)
        self.add(f'<div class="map">{art}</div><div class="logo">{self.logo.replace("#e5006e", "#FFFFFF")}</div>'
                 f'<div class="years">{years}</div>'
                 "<h1>World Risk Poll</h1><h2>The reports, 2019 to 2025</h2>"
                 "<p>The core reports and Focus On reports of the Lloyd's Register Foundation World Risk Poll, in one volume</p>", "cover")

    def about_page(self):
        rows = "".join(
            f'<div class="row w{y}"><div class="yr num">{y}<span></span></div><div class="what"><b>{w["respondents"]} people, '
            f'{w["countries"]} countries and territories</b>{sum(r["wave"] == y for r in REPORTS)} chapters in this book</div></div>'
            for y, w in WAVES.items())
        self.add(f'''<div class="pad about"><div><span class="eyebrow dot">About this book</span>
<h1>Four editions, {len(REPORTS)} chapters<span class="dot">.</span></h1>
<p>The Lloyd's Register Foundation World Risk Poll asks people around the world about the risks they worry about and the harm they have experienced. It is fielded by Gallup as part of the Gallup World Poll and has run four times, in 2019, 2021, 2023 and 2025, in between 121 and 142 countries and territories each time.</p>
<p>This volume binds together the reports published from those four editions, in {len(REPORTS)} chapters. Each chapter opens with a page written for this volume and is followed by the report as it was published, page for page. The reports were designed in different shapes over the years. Landscape reports are reproduced one page to a sheet. The portrait reports of 2019 and 2021 are reproduced two pages to a sheet, as the pages face each other in print.</p>
<p>The 2019 Poll was published as one full report. Its ten chapters are grouped here into four, by theme, so that 2019 sits alongside the four or five core reports of each later edition. The report's own page numbers show where each page came from, and its appendices follow the fourth chapter. The Focus On report on risk and gender is not included.</p>
</div><div class="wavelist">{rows}</div></div>{foot("{PAGE}", TITLE)}''', "w2021")

    def contents_page(self, chapters, extras):
        cols = []
        for year, wave in WAVES.items():
            items = ""
            for n, r in chapters:
                if r["wave"] != year:
                    continue
                kind = " · Focus On" if r["type"] == "focus_on" else ""
                items += (f'<div class="item"><div><small>Chapter {n}{kind}</small>{escape(r["title"])}</div>'
                          f'<div class="pg num">{self.starts[r["key"]]}</div></div>')
            for label, page in extras.get(year, []):
                items += f'<div class="item"><div><small>After chapter 4</small>{escape(label)}</div><div class="pg num">{page}</div></div>'
            cols.append(f'<div class="col w{year}"><h2 class="num">{year}</h2><div class="brand">{escape(wave["brand"])}</div>{items}</div>')
        self.add(f'<div class="pad contents"><span class="eyebrow dot">Contents</span><h1>The chapters<span class="dot">.</span></h1>'
                 f'<div class="cols">{"".join(cols)}</div></div>{foot("{PAGE}", TITLE)}', "", 2021)

    def chapter_opener(self, r, n, source):
        fig = Figures(r["folder"], self.used)
        wave = WAVES[r["wave"]]
        hero = stat_value(fig, r["hero"][0], r["hero"][2] if len(r["hero"]) > 2 else None)
        kind = "Focus On" if r["type"] == "focus_on" else "Core report"
        size = "small" if len(r["title"]) > 34 else ("mid" if len(r["title"]) > 22 else "")
        subtitle = "" if r["subtitle"] == "Focus On" else f'<h2>{escape(r["subtitle"])}</h2>'
        gap = ' style="margin-bottom:44px"' if not subtitle else ""
        doi = f'<span><b>DOI</b> {escape(r["doi"])}</span>' if r.get("doi") else ""
        self.add(f'''<div class="panel"><span class="eyebrow">{escape(wave["brand"])}</span>
<div class="hero num{" long" if len(hero) > 4 else ""}">{big(hero)}</div><p class="herocap">{escape(fig.fill(r["hero"][1]))}</p>
<div class="count">Chapter {n} of {len(REPORTS)}</div></div>
<div class="main"><span class="eyebrow kind">Chapter {n} · {kind}</span><h1 class="{size}"{gap}>{title_html(r["title"])}</h1>{subtitle}
<p class="lede">{escape(fig.fill(r["lede"]))}</p>
<div class="meta"><span><b>Published</b> {escape(r["published"])}</span><span><b>Reproduced</b> {escape(source)}</span>{doi}</div></div>
{foot("{PAGE}", "")}''', "opener", r["wave"])

    def appendix_opener(self):
        self.add(f'''<div class="panel"><span class="eyebrow">World Risk Poll 2019</span>
<div class="hero num">3</div><p class="herocap">appendices to the 2019 report: the questionnaire, the references and the regions</p>
<div class="count">After chapter 4</div></div>
<div class="main"><span class="eyebrow kind">2019 report</span><h1 class="mid">Appendices<span class="dot">.</span></h1>
<p class="lede">The 2019 report closes with the questionnaire put to respondents, the references for all ten of its chapters and the regional groupings used in its analysis. They cover the four preceding chapters of this book.</p>
<div class="meta"><span><b>Published</b> 2020</span><span><b>Reproduced</b> 2019 full report, appendices 1 to 3</span></div></div>
{foot("{PAGE}", "")}''', "opener", 2019)

    def end_page(self):
        self.folio = ""
        self.end()

    def html(self):
        css = (HERE / "book.css").read_text(encoding="utf-8") + (HERE / "bound.css").read_text(encoding="utf-8")
        return ('<!doctype html><html lang="en-GB"><head><meta charset="utf-8">'
                f"<title>{escape(TITLE)}</title><style>{font_faces()}\n{css}</style></head><body>"
                + "\n".join(self.pages) + "</body></html>")


def source_note(r, doc):
    if r["wave"] == 2019:
        chapters = next(ch for key, _, ch in SPLIT_2019 if key == r["key"])
        where = (", ".join(map(str, chapters[:-1])) + " and " + str(chapters[-1])) if len(chapters) > 1 else str(chapters[0])
        return f'2019 full report, chapter{"s" if len(chapters) > 1 else ""} {where}'
    return f"in full, {len(doc)} pages"


def pages_2019(key):
    chapters = next(ch for k, _, ch in SPLIT_2019 if k == key)
    indexes = []
    if 1 in chapters:
        indexes += range(FRONT_2019[0], FRONT_2019[1] + 1)
    for c in chapters:
        indexes += range(CHAPTERS_2019[c][0], CHAPTERS_2019[c][1] + 1)
    return indexes


def plan_book():
    """The book as a list of pages: designed pages, blanks and reproduced sheets."""
    rows = inventory()
    docs, plan, starts, extras = {}, [], {}, {}
    chapters = list(enumerate(REPORTS, 1))

    def designed(what, **more):
        plan.append(dict(kind="designed", what=what, **more))
        return len(plan)

    def blank():
        plan.append(dict(kind="blank"))

    def reproduce(doc_key, indexes, label, wave):
        for sheet in sheets(docs[doc_key], doc_key, indexes):
            plan.append(dict(kind="sheet", doc=doc_key, places=sheet, label=label, wave=wave))

    designed("title")
    blank()
    designed("about")
    designed("contents")
    for year, wave in WAVES.items():
        if len(plan) % 2 == 1:
            blank()                                  # each poll opens on a right-hand page
        starts[year] = designed("wave", year=year)
        for n, r in chapters:
            if r["wave"] != year:
                continue
            docs.setdefault(r["folder"], pymupdf.open(report_pdf(r["folder"], rows)))
            doc = docs[r["folder"]]
            starts[r["key"]] = designed("chapter", report=r, n=n, source=source_note(r, doc))
            indexes = pages_2019(r["key"]) if year == 2019 else range(len(doc))
            reproduce(r["folder"], indexes, f'Chapter {n} · {r["title"]}', year)
        if year == 2019:
            folder = REPORTS[0]["folder"]
            page = designed("appendices")
            extras[year] = [("Appendices to the 2019 report", page)]
            reproduce(folder, range(APPENDICES_2019[0], APPENDICES_2019[1] + 1), "2019 report · Appendices", year)
    if len(plan) % 2 == 0:
        blank()                                      # the closing page is a left-hand page
    designed("end")
    return plan, docs, starts, extras, chapters


def designed_pages(plan, starts, extras, chapters):
    """Draw the designed pages with Chrome and return them as a PDF."""
    book = Bound()
    book.starts = starts
    for number, page in enumerate(plan, 1):
        if page["kind"] != "designed":
            continue
        book.folio = number
        what = page["what"]
        if what == "title":
            book.title_page()
        elif what == "about":
            book.about_page()
        elif what == "contents":
            book.contents_page(chapters, extras)
        elif what == "wave":
            start = book.starts[page["year"]]
            book.wave_opener(page["year"])
            book.starts[page["year"]] = start
        elif what == "chapter":
            book.chapter_opener(page["report"], page["n"], page["source"])
        elif what == "appendices":
            book.appendix_opener()
        elif what == "end":
            book.end_page()
    OUT.mkdir(exist_ok=True)
    html_path, pdf_path = OUT / "bound_designed.html", OUT / "bound_designed.pdf"
    html_path.write_text(book.html(), encoding="utf-8")
    print_pdf(html_path, pdf_path)
    return pymupdf.open(pdf_path)


def place(page, src, index, rect):
    source = src[index]
    page.show_pdf_page(rect, src, index, clip=source.trimbox)
    page.draw_rect(rect, color=KEYLINE, width=0.35)


def reproduce_sheet(page, number, spec, docs, fonts):
    """Place one or two pages of a report and add the running footer."""
    src = docs[spec["doc"]]
    recto = number % 2 == 1
    left = BLEED + (INNER if recto else OUTER)
    box = pymupdf.Rect(left, BLEED + TOP, left + TRIM_W - INNER - OUTER, BLEED + TRIM_H - BOTTOM)
    first = src[spec["places"][0][0]].trimbox
    if spec["places"][0][1] == "full":
        s = min(box.width / first.width, box.height / first.height)
        w, h = first.width * s, first.height * s
        x, y = box.x0 + (box.width - w) / 2, box.y0 + (box.height - h) / 2
        place(page, src, spec["places"][0][0], pymupdf.Rect(x, y, x + w, y + h))
    else:
        s = min(box.width / (2 * first.width), box.height / first.height)
        w, h = first.width * s, first.height * s
        middle, y = box.x0 + box.width / 2, box.y0 + (box.height - h) / 2
        for index, side in spec["places"]:
            x = middle - w if side == "left" else middle
            place(page, src, index, pymupdf.Rect(x, y, x + w, y + h))

    colour = rgb(WAVES[spec["wave"]]["colour"])
    base = BLEED + TRIM_H - 17
    label = f'{WAVES[spec["wave"]]["brand"]} · {spec["label"]}'
    folio = str(number)
    bold, regular = fonts
    page.insert_font(fontname="dmb", fontfile=str(bold[1]))
    page.insert_font(fontname="dmr", fontfile=str(regular[1]))
    outer = BLEED + (TRIM_W - OUTER if recto else OUTER)
    folio_w, label_w = bold[0].text_length(folio, 9), regular[0].text_length(label, 7)
    if recto:
        page.insert_text((outer - folio_w, base), folio, fontname="dmb", fontsize=9, color=(0.14, 0.12, 0.13))
        page.insert_text((outer - folio_w - 14 - label_w, base), label, fontname="dmr", fontsize=7, color=MUTED)
        tick = outer - folio_w - 14 - label_w - 8
        page.draw_rect(pymupdf.Rect(tick - 12, base - 4.4, tick, base - 1.8), color=None, fill=colour)
    else:
        page.insert_text((outer, base), folio, fontname="dmb", fontsize=9, color=(0.14, 0.12, 0.13))
        page.insert_text((outer + folio_w + 14, base), label, fontname="dmr", fontsize=7, color=MUTED)
        tick = outer + folio_w + 14 + label_w + 8
        page.draw_rect(pymupdf.Rect(tick, base - 4.4, tick + 12, base - 1.8), color=None, fill=colour)


def assemble(plan, docs, designed, starts, extras, chapters):
    out = pymupdf.open()
    width, height = TRIM_W + 2 * BLEED, TRIM_H + 2 * BLEED
    fonts = [(pymupdf.Font(fontfile=str(CACHE / f"DMSans-{w}.ttf")), CACHE / f"DMSans-{w}.ttf") for w in (700, 400)]
    drawn = 0
    for number, spec in enumerate(plan, 1):
        page = out.new_page(width=width, height=height)
        if spec["kind"] == "designed":
            page.show_pdf_page(page.rect, designed, drawn)
            drawn += 1
        elif spec["kind"] == "sheet":
            reproduce_sheet(page, number, spec, docs, fonts)
        trim = pymupdf.Rect(BLEED, BLEED, BLEED + TRIM_W, BLEED + TRIM_H)
        page.set_trimbox(trim)
        page.set_bleedbox(page.rect)
    toc = []
    for year, wave in WAVES.items():
        toc.append([1, f'{year}: {wave["brand"]}', starts[year]])
        for n, r in chapters:
            if r["wave"] == year:
                toc.append([2, f'{n}. {r["title"]}', starts[r["key"]]])
        for label, page_number in extras.get(year, []):
            toc.append([2, label, page_number])
    out.set_toc(toc)
    out.set_metadata({"title": TITLE, "author": "Lloyd's Register Foundation"})
    out.subset_fonts()
    return out


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--screen", action="store_true", help="also write a smaller copy with images at 110 dpi")
    args = parser.parse_args()
    plan, docs, starts, extras, chapters = plan_book()
    designed = designed_pages(plan, starts, extras, chapters)
    out = assemble(plan, docs, designed, starts, extras, chapters)
    path = OUT / "World_Risk_Poll_reports_bound.pdf"
    out.save(path, garbage=3, deflate=True)
    sheets_ = sum(p["kind"] == "sheet" for p in plan)
    reproduced = sum(len(p["places"]) for p in plan if p["kind"] == "sheet")
    print(f"{len(plan)} pages: {reproduced} report pages on {sheets_} sheets, {len(chapters)} chapters -> {path} ({path.stat().st_size / 1e6:.0f} MB)")
    if args.screen:
        out.rewrite_images(dpi_threshold=130, dpi_target=110, quality=70)
        small = OUT / "World_Risk_Poll_reports_bound_screen.pdf"
        out.save(small, garbage=3, deflate=True)
        print(f"screen copy -> {small} ({small.stat().st_size / 1e6:.0f} MB)")


if __name__ == "__main__":
    sys.exit(main())
