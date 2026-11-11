"""Bind the re-set reports and the reports of the 2025 poll as one landscape book.

    python reports/book/redesign/bind.py            # writes output/redesign/World_Risk_Poll_reports_2019_to_2025.pdf
    python reports/book/redesign/bind.py --screen   # also writes a smaller copy for reading on screen
    python reports/book/redesign/bind.py --indesign # also writes the book as a set of InDesign documents

The book is a title page, a page about the book, the contents, an opening chapter
that reads across the polls (content/across_the_waves.md, written for this
edition), and then the four polls in order. Each poll opens with a page of its
own and each report follows whole, cover first, so a report is a chapter. The reports of the 2019, 2021 and
2023 polls are the re-set ones (build each with build.py first); the five
reports of the 2025 poll are the published PDFs, placed as they are.

Every report keeps its own page numbers. The book's page number is added at
the foot of each page, in the middle, where every report leaves the footer
empty; covers carry none. The PDF has a bookmark for each poll and report.

With --indesign the book is also written to output/indesign/<name>/ as one IDML
for each part of it, numbered in the order they are bound: the front pages, the
opening chapter, an opening page for each poll, and each report. indesign.py makes them, so the
text of the re-set reports is live; the reports of the 2025 poll are placed a
page to a page from their PDFs. Each document's pages are numbered from their
place in the book, and the book's page number sits on a layer of its own.

Needs PyMuPDF, a Chrome or Chromium, and the DM Sans files that build.py downloads.
"""

import argparse
import importlib.util
import json
import shutil
import sys
from html import escape
from pathlib import Path

import pymupdf

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from build import CACHE, OUT  # noqa: E402  (the coffee table book's build.py)
from content import REPORTS, WAVES  # noqa: E402

# The report builder in this folder is also called build.py, so it is loaded under another name.
_spec = importlib.util.spec_from_file_location("report_build", HERE / "build.py")
report_build = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(report_build)
font_faces, print_pdf = report_build.font_faces, report_build.print_pdf

TITLE = "World Risk Poll: the reports, 2019 to 2025"
NAME = "World_Risk_Poll_reports_2019_to_2025"
NAVY = (0x0E / 255, 0x22 / 255, 0x40 / 255)

OPENING = "across_the_waves"         # the chapter that reads across the polls, bound before the first of them

# The reports of each poll, in the order they were published. The 2025 poll's are keys of content.REPORTS.
BOOK = {
    2019: ["2019_feeling_safe", "2019_risk_at_work", "2019_climate_food_water", "2019_technology"],
    2021: ["2021_a_changed_world", "2021_a_resilient_world", "2021_a_digital_world", "2021_safe_at_work",
           "2021_focus_violence_and_harassment", "2021_focus_fossil_fuels", "2021_focus_critical_infrastructure"],
    2023: ["2023_resilience_in_a_changing_world", "2023_a_world_of_waste", "2023_engineering_safer_workplaces",
           "2023_what_the_world_worries_about", "2023_focus_ocean_workers", "2023_focus_migration"],
    2025: ["alone_together", "the_quiet_hazards", "a_resilient_life", "from_alert_to_agency", "after_the_storm"],
}
ABOUT = [
    "This volume brings together the reports of the Lloyd’s Register Foundation World Risk Poll, from the first poll in 2019 "
    "to the poll of 2025: {reports} reports from four polls, each one a chapter. An opening chapter, written for this "
    "edition from the figures the reports publish, reads across the four polls.",
    "The reports were published over six years in four different designs. Here the reports of the 2019, 2021 and 2023 polls "
    "are re-set in the format of the World Risk Poll 2026 reports, so that the volume reads as one book. Their text is the "
    "published text, word for word, and their charts are redrawn from the published values in the 2026 chart style. Where a "
    "chart could not be redrawn from published values it is placed as a picture of the original. The notes at the back of each "
    "report record every change, and every query about the original.",
    "The 2019 poll was published as a single volume. It appears here as four reports, each with an introduction and a "
    "conclusion written for this edition and marked as such. The five reports of the 2025 poll are reproduced as published.",
    "Each report keeps its own contents, page numbers and references. The page numbers in the contents of this book are the "
    "book’s own, printed in the middle of the foot of each page.",
]
NOTES = {
    2019: "One volume in the original; four reports here",
    2021: "Four core reports and three Focus On reports",
    2023: "Four core reports and two Focus On reports",
    2025: "Five core reports, reproduced as published",
}


def reports_of(year):
    """[(title for the contents, the report's PDF)] of one poll."""
    out = []
    for key in BOOK[year]:
        if year == 2025:
            r = next(r for r in REPORTS if r["key"] == key)
            out.append((r["title"], r["subtitle"], CACHE / "pdfs" / f"core_{key}.pdf"))
        else:
            meta = json.loads((HERE / "content" / f"{key}.md").read_text(encoding="utf-8").split("---")[1])
            out.append((meta["title"], meta["subtitle"], OUT / "redesign" / f"{key}.pdf"))
    return out


def label(title, subtitle):
    return f"{title}: {subtitle}" if title == "Focus On" else title


def plan():
    """The book as a list of pages, and where each poll and report starts (page numbers from 1)."""
    pages = [dict(kind="designed", what="cover"), dict(kind="designed", what="about"), dict(kind="designed", what="contents")]
    path = OUT / "redesign" / f"{OPENING}.pdf"
    if not path.exists():
        sys.exit(f"missing {path}: build the opening chapter first (build.py {OPENING})")
    meta = json.loads((HERE / "content" / f"{OPENING}.md").read_text(encoding="utf-8").split("---")[1])
    doc = pymupdf.open(path)
    opening = dict(title=meta["title"], subtitle=meta["subtitle"], page=len(pages) + 1, length=len(doc))
    pages += [dict(kind="report", path=path, index=k, cover=False) for k in range(len(doc))]
    doc.close()
    polls = []
    for year in BOOK:
        pages.append(dict(kind="designed", what="poll", year=year))
        poll = dict(year=year, page=len(pages), reports=[])
        for title, subtitle, path in reports_of(year):
            if not path.exists():
                sys.exit(f"missing {path}: build the report (build.py) or download the published PDFs (bound.py) first")
            doc = pymupdf.open(path)
            poll["reports"].append(dict(title=title, subtitle=subtitle, page=len(pages) + 1, length=len(doc)))
            pages += [dict(kind="report", path=path, index=k) for k in range(len(doc))]
            doc.close()
        polls.append(poll)
    return pages, polls, opening


def chrome():
    line = "World Risk Poll  ||  The reports, 2019 to 2025"
    return ('<div class="rule top"></div><div class="rule bottom"></div>'
            f'<div class="credit">Copyright © 2026 Lloyd’s Register Foundation. All rights reserved.<br>{line}</div>')


def designed(polls, opening):
    """The book's own pages as HTML: title page, about, contents, and an opening page for each poll."""
    logo = (HERE.parent / "assets" / "lrf-logo.svg").read_text(encoding="utf-8").replace("#e5006e", "#FFFFFF")
    count = sum(len(p["reports"]) for p in polls)
    years = "".join(f"<span>{poll['year']}</span>" for poll in polls)
    cover = (f'<section class="page cover"><div class="photo"></div><div class="years">{years}</div><div class="panel"></div>'
             '<svg class="edge" viewBox="0 0 1920 1080"><line x1="606.7" y1="0" x2="932.9" y2="1080" stroke="#E3076E" stroke-width="3"/></svg>'
             f'<div class="logo">{logo}</div><div class="wrp">World Risk Poll</div><div class="rep">Reports 2019 to 2025</div>'
             f'<div class="name"><b>The reports of four polls</b><br>{count} reports in one volume</div>'
             '<div class="series">Lloyd’s Register Foundation</div><div class="gallup">Powered by <b>GALLUP</b></div></section>')
    about = "".join(f"<p>{escape(p.format(reports=count))}</p>" for p in ABOUT)
    about = f'<section class="page body">{chrome()}<div class="window"><div class="flow"><h1>About this book</h1>{about}</div></div></section>'
    rows = (f'<div class="row top bookrow first"><span><b>{escape(opening["title"])}:</b> {escape(opening["subtitle"])}</span>'
            f'<span class="n">{opening["page"]}</span></div>')
    for n, poll in enumerate(polls, 1):
        brand = WAVES[poll["year"]]["brand"]
        poll_of = "" if brand.endswith(str(poll["year"])) else f', the {poll["year"]} poll'
        rows += (f'<div class="row chapter"><span>Part {n}: {escape(brand)}{poll_of}</span>'
                 f'<span class="n">{poll["page"]}</span></div>')
        for r in poll["reports"]:
            name = f'<b>{escape(r["title"])}{"" if r["title"][-1] in "?!" or not r["subtitle"] else ":"}</b> {escape(r["subtitle"])}'
            rows += f'<div class="row top bookrow"><span>{name}</span><span class="n">{r["page"]}</span></div>'
    contents = (f'<section class="page body">{chrome()}<div class="window"><div class="flow">'
                f'<h1>Contents</h1><div class="toc">{rows}</div></div></div></section>')
    openers = []
    for n, poll in enumerate(polls, 1):
        wave = WAVES[poll["year"]]
        listing = "".join(f'<p class="in">{escape(label(r["title"], r["subtitle"]))}</p>' for r in poll["reports"])
        openers.append(
            f'<section class="page opener">{chrome()}<div class="block"></div><div class="logo">{logo}</div>'
            f'<div class="left"><div class="chap">Part {n}</div><h1>{escape(wave["brand"])}</h1>'
            f'<div class="text"><p>{escape(NOTES[poll["year"]])}, from page {poll["reports"][0]["page"]} of this book.</p>{listing}</div></div>'
            f'<div class="big single"><span>{poll["year"]}</span></div>'
            f'<div class="cap">the year of the poll: <strong>{wave["respondents"]}</strong> people interviewed in '
            f'<strong>{wave["countries"]}</strong> countries</div></section>')
    css = (HERE / "report.css").read_text(encoding="utf-8")
    extra = (".toc .row.bookrow { font-size: 17px; line-height: 27px; font-style: normal; } .toc .row.bookrow b { font-weight: 700; }"
             ".toc .row.chapter { font-size: 17px; line-height: 27px; margin-top: 26px; color: var(--fuchsia); }"
             ".toc .row.bookrow.first { margin-top: 26px; }"
             ".opener .text p.in { margin: 0 0 6px; font-weight: 700; }"
             ".cover .years { position: absolute; right: 116px; top: 896px; white-space: nowrap; color: #fff; opacity: 0.3;"
             " font-size: 76px; line-height: 84px; font-weight: 800; letter-spacing: -0.03em; } .cover .years span { margin-left: 36px; }")
    html = ('<!doctype html><html lang="en-GB"><head><meta charset="utf-8">'
            f'<title>{escape(TITLE)}</title><style>{font_faces()}\n{css}\n{extra}</style></head><body>'
            + "\n".join([cover, about, contents] + openers) + "</body></html>")
    out = OUT / "redesign"
    out.mkdir(parents=True, exist_ok=True)
    html_path, pdf_path = out / "_book_pages.html", out / "_book_pages.pdf"
    html_path.write_text(html, encoding="utf-8")
    print_pdf(html_path, pdf_path)
    doc = pymupdf.open(pdf_path)
    assert len(doc) == 3 + len(polls), f"{len(doc)} designed pages, expected {3 + len(polls)}: one of them overflows"
    return doc


def folio(page, number, font):
    """The book's page number, in the middle of the foot of the page, set like the credit lines beside it."""
    text, size, track = f"BOOK PAGE {number}", 9, 0.9
    width = sum(font.text_length(c, size) + track for c in text) - track
    x = 960 - width / 2
    for c in text:
        page.insert_text((x, 1060), c, fontname="dmfolio", fontsize=size, color=NAVY)
        x += font.text_length(c, size) + track


READ_ME = """World Risk Poll: the reports, 2019 to 2025, as InDesign documents (IDML, InDesign 2020 or later).

The documents are numbered in the order they are bound: the front pages, the opening chapter that reads across
the polls, then for each poll an opening page and its reports. To work on them as one book, make an InDesign
book (File > New > Book) and add them in that order.

Page numbers. Each document's pages are numbered from their place in the book: the first page of each starts
at the number listed at the end of this file (Layout > Numbering & Section Options > Start Page Numbering at).
The book's page number at the foot of each page is live (BOOK PAGE and a current page number marker) and sits
on a layer called Book page numbers. Hide that layer to use a report on its own. Covers carry no number.
The contents page lists the same numbers as text.

Text. In the re-set reports of the 2019, 2021 and 2023 polls the text is live and carries paragraph styles
named after the type they set; text that runs from one column or page to the next is threaded. Each page's
grounds, rules and blocks are one placed PDF at the back of the page, and each chart is a placed PDF of its own.
The five reports of the 2025 poll are placed whole from their published PDFs, one file for each page.

Links. Every placed file is in Links, in a folder named after its document. If InDesign reports missing links,
choose Links > Relink to Folder and pick that folder. The text is set in DM Sans; the files are in Document fonts.
"""


def indesign_set(polls, opening):
    """The book as InDesign documents in one folder, in the order they are bound."""
    import indesign
    folder = OUT / "indesign" / NAME
    if folder.exists():
        shutil.rmtree(folder)
    folder.mkdir(parents=True)
    own = OUT / "redesign" / "_book_pages.html"
    parts = [("front_pages", own, {0, 1, 2}, 1, True),            # name, source, pages of the source, book page, opens with a cover
             (OPENING, OUT / "redesign" / f"{OPENING}.html", None, opening["page"], False)]
    for n, poll in enumerate(polls):
        parts.append((f"part_{n + 1}_the_{poll['year']}_poll", own, {3 + n}, poll["page"], False))
        for key, report in zip(BOOK[poll["year"]], poll["reports"]):
            if poll["year"] == 2025:
                parts.append((f"2025_{key}", CACHE / "pdfs" / f"core_{key}.pdf", None, report["page"], True))
            else:
                parts.append((key, OUT / "redesign" / f"{key}.html", None, report["page"], True))
    listing = []
    for k, (name, source, only, page, cover) in enumerate(parts):
        name = f"{k:02d}_{name}"
        line = indesign.export(source, name, folder, links=f"Links/{name}", only=only, folio=page, cover=cover)
        print(line.replace(str(OUT) + "/", ""))
        listing.append(f"    {name + '.idml':52s} {line.split(',')[0].replace('1 pages', '1 page'):>9s}, from book page {page}")
    indesign.fonts_folder(folder)
    (folder / "READ ME.txt").write_text(READ_ME + "\nThe documents, and the book page each one starts on:\n\n" + "\n".join(listing) + "\n", encoding="utf-8")
    archive = shutil.make_archive(str(OUT / "indesign" / f"{NAME}_indesign"), "zip", folder.parent, folder.name)
    print(f"{len(parts)} InDesign documents -> {archive} ({Path(archive).stat().st_size / 1e6:.0f} MB)")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--screen", action="store_true", help="also write a smaller copy with images at 110 dpi")
    parser.add_argument("--indesign", action="store_true", help="also write the book as a set of InDesign documents (IDML)")
    args = parser.parse_args()
    pages, polls, opening = plan()
    own = designed(polls, opening)
    font_file = CACHE / "DMSans-600.ttf"
    font = pymupdf.Font(fontfile=str(font_file))
    out, drawn, sources = pymupdf.open(), 0, {}
    for number, spec in enumerate(pages, 1):
        page = out.new_page(width=1920, height=1080)
        if spec["kind"] == "designed":
            page.show_pdf_page(page.rect, own, drawn)
            drawn += 1
            covered = spec["what"] == "cover"
        else:
            src = sources.setdefault(spec["path"], pymupdf.open(spec["path"]))
            page.show_pdf_page(page.rect, src, spec["index"])
            covered = spec["index"] == 0 and spec.get("cover", True)
        if not covered:
            page.insert_font(fontname="dmfolio", fontfile=str(font_file))
            folio(page, number, font)
    toc = [[1, opening["title"], opening["page"]]]
    for n, poll in enumerate(polls, 1):
        toc.append([1, f'Part {n}: {WAVES[poll["year"]]["brand"]}', poll["page"]])
        toc += [[2, label(r["title"], r["subtitle"]), r["page"]] for r in poll["reports"]]
    out.set_toc(toc)
    out.set_metadata({"title": TITLE, "author": "Lloyd's Register Foundation"})
    out.subset_fonts()
    path = OUT / "redesign" / f"{NAME}.pdf"
    out.save(path, garbage=3, deflate=True)
    count = sum(len(p["reports"]) for p in polls)
    print(f"{len(pages)} pages, {count} reports in {len(polls)} parts -> {path} ({path.stat().st_size / 1e6:.0f} MB)")
    if args.screen:
        out.rewrite_images(dpi_threshold=130, dpi_target=110, quality=70)
        small = OUT / "redesign" / f"{NAME}_screen.pdf"
        out.save(small, garbage=3, deflate=True)
        print(f"screen copy -> {small} ({small.stat().st_size / 1e6:.0f} MB)")
    if args.indesign:
        indesign_set(polls, opening)


if __name__ == "__main__":
    sys.exit(main())
