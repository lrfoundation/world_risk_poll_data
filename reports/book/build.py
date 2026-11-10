"""Build the World Risk Poll coffee table book.

    python reports/book/build.py          # writes output/book.html and FIGURES.md
    python reports/book/build.py --pdf    # also prints output/World_Risk_Poll_22_reports.pdf

The text and charts use the published figures in each report's
published_figures.csv (see content.py). The maps are computed from the public
wave files (see maps.py). The PDF is printed by a Chrome, Chromium or Edge that
is already installed; without one, open output/book.html in a browser and print
to PDF with no margins and background graphics on.
"""

import argparse
import shutil
import subprocess
import sys
import urllib.request
from html import escape
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))

import charts  # noqa: E402
import maps  # noqa: E402
from content import INK, NAVY, REPORTS, SPLIT_2019, WAVES  # noqa: E402
from figures import Figures, statuses  # noqa: E402
from worldmap import World, class_of, classes, mix  # noqa: E402
from wrp import load_wave  # noqa: E402

OUT = HERE / "output"
CACHE = HERE / ".cache"
BOOK = "World Risk Poll: 22 reports, 2019 to 2025"
GEOJSON = "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_110m_admin_0_countries.geojson"
FONT_CSS = "https://fonts.googleapis.com/css2?family=DM+Sans:opsz,wght@9..40,400;9..40,500;9..40,600;9..40,700;9..40,800;9..40,900"
NO_DATA = "#EFEFEF"


# ---------------------------------------------------------------- assets

def fetch(url, path, agent="Mozilla/4.0"):
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        request = urllib.request.Request(url, headers={"User-Agent": agent})
        with urllib.request.urlopen(request, timeout=60) as response:
            path.write_bytes(response.read())
    return path


def font_faces():
    """DM Sans as static files, one per weight, downloaded once from Google Fonts."""
    import re
    css = fetch(FONT_CSS, CACHE / "dm-sans.css").read_text(encoding="utf-8")
    faces = []
    for weight, url in re.findall(r"font-weight:\s*(\d+);.*?url\((https://[^)]+\.ttf)\)", css, flags=re.S):
        path = fetch(url, CACHE / f"DMSans-{weight}.ttf")
        faces.append(f'@font-face {{ font-family: "DM Sans"; font-weight: {weight}; src: url("{path.as_uri()}") format("truetype"); }}')
    return "\n".join(faces)


# ---------------------------------------------------------------- helpers

def big(text):
    """A headline number, with its unit set smaller: 34%, 667 million."""
    for unit in ("%", " million", " billion"):
        if text.endswith(unit):
            return f'{escape(text[:-len(unit)])}<small>{escape(unit)}</small>'
    return escape(text)


def stat_value(fig, fid, pattern=None):
    value = fig.text(fid)
    if pattern:
        return pattern.replace("{v}", value)
    return value + ("%" if fig.row(fid)["unit"] == "pct" else "")


def title_html(title):
    if title[-1] in "?!.":
        return f'{escape(title[:-1])}<span class="dot">{escape(title[-1])}</span>'
    return f'{escape(title)}<span class="dot">.</span>'


def foot(number, label=BOOK):
    return f'<div class="foot"><span><i class="tick"></i>{escape(label)}</span><b class="num">{number}</b></div>'


def head(report, section):
    kind = "Focus On" if report["type"] == "focus_on" else "Core report"
    return (f'<div class="head"><span class="eyebrow">{escape(section)}</span>'
            f'<span class="where">{escape(WAVES[report["wave"]]["brand"])} · {kind} · {escape(report["title"])}</span></div>')


# ---------------------------------------------------------------- pages

class Book:
    def __init__(self):
        self.world = World(fetch(GEOJSON, CACHE / "ne_110m_admin_0_countries.geojson"))
        self.logo = (HERE / "assets" / "lrf-logo.svg").read_text(encoding="utf-8")
        self.used = {}
        self.pages = []      # (html with {PAGE} placeholders, wave or None)
        self.starts = {}     # report key or wave -> page number
        self.names = {}
        self.surveyed = {}
        for year in WAVES:
            d = load_wave(year, ["COUNTRY_ISO3", "Country"]).drop_duplicates()
            self.names.update(dict(zip(d.COUNTRY_ISO3, d.Country)))
            self.surveyed[year] = set(d.COUNTRY_ISO3)

    def add(self, html, cls, wave=None):
        number = len(self.pages) + 1
        wave_cls = f" w{wave}" if wave else ""
        self.pages.append(f'<section class="page {cls}{wave_cls}">{html.replace("{PAGE}", str(number))}</section>')
        return number

    # -- front matter

    def cover(self):
        art = self.world.svg(1700, 830, lambda c: ("#FFFFFF", 0.16), stroke="#E3076E", stroke_width=1)
        years = "<br>".join(str(y) for y in WAVES)
        self.add(f'<div class="map">{art}</div><div class="logo">{self.logo.replace("#e5006e", "#FFFFFF")}</div>'
                 f'<div class="years">{years}</div>'
                 '<h1>World Risk Poll</h1><h2>22 reports, 2019 to 2025</h2>'
                 "<p>The findings of the core reports and Focus On reports, in numbers, charts and maps</p>", "cover")

    def about(self):
        rows = "".join(
            f'<div class="row w{y}"><div class="yr num">{y}<span></span></div><div class="what"><b>{w["respondents"]} people, '
            f'{w["countries"]} countries and territories</b>{sum(r["wave"] == y for r in REPORTS)} reports in this book</div></div>'
            for y, w in WAVES.items())
        self.add(f'''<div class="pad about"><div><span class="eyebrow dot">About this book</span>
<h1>Four polls, 22 reports<span class="dot">.</span></h1>
<p>The Lloyd's Register Foundation World Risk Poll asks people around the world about the risks they worry about and the harm they have experienced. It is fielded by Gallup as part of the Gallup World Poll and has run four times, in 2019, 2021, 2023 and 2025, in between 121 and 142 countries and territories each time.</p>
<p>This book gathers the findings of 22 reports drawn from those four polls: 17 core reports and five Focus On reports. Each report has a few pages here: its headline finding, the numbers behind it, a chart or two and, for the core reports, a map. The 2019 poll was published as one full report. It appears here in four parts, so that it can be read alongside the four or five core reports of each later poll. The Focus On report on risk and gender is not included.</p>
<p>Every number in the text and charts is a figure from the published report, drawn from the reproduction files in the World Risk Poll data repository. The maps are the exception: they were computed for this book from the public data, with the same weights and bases as the reports.</p>
</div><div class="wavelist">{rows}</div></div>{foot("{PAGE}")}''', "w2021")

    def contents(self):
        cols = []
        for year, wave in WAVES.items():
            items = "".join(
                f'<div class="item"><div><small>{"Focus On" if r["type"] == "focus_on" else "Core report"}</small>{escape(r["title"])}</div>'
                f'<div class="pg num">{self.starts[r["key"]]}</div></div>'
                for r in REPORTS if r["wave"] == year)
            cols.append(f'<div class="col w{year}"><h2 class="num">{year}</h2><div class="brand">{escape(wave["brand"])}</div>{items}</div>')
        return (f'<div class="pad contents"><span class="eyebrow dot">Contents</span><h1>The reports<span class="dot">.</span></h1>'
                f'<div class="cols">{"".join(cols)}</div></div>{foot("{PAGE}")}')

    # -- polls and reports

    def wave_opener(self, year):
        wave = WAVES[year]
        got = self.surveyed[year]
        art = self.world.svg(1100, 600, lambda c: (wave["on"], 0.95 if c in got else 0.2), stroke=wave["colour"], stroke_width=1)
        n = sum(r["wave"] == year for r in REPORTS)
        brand = "" if wave["brand"].endswith(str(year)) else f'<div class="brand">Published as the {escape(wave["brand"])} reports</div>'
        self.starts[year] = self.add(f'''<div class="left"><span class="eyebrow">World Risk Poll · fieldwork year</span>
<div class="year num">{year}</div>{brand}<p class="blurb">{escape(wave["blurb"])}</p>
<div class="facts"><div><b class="num">{wave["respondents"]}</b><span>People</span></div>
<div><b class="num">{wave["countries"]}</b><span>Countries and territories</span></div>
<div><b class="num">{n}</b><span>Reports in this book</span></div></div></div>
<div class="maplabel"><span class="eyebrow">Where the poll was fielded</span></div><div class="map">{art}</div>{foot("{PAGE}")}''', "wave", year)

    def opener(self, r, fig, index):
        wave = WAVES[r["wave"]]
        hero = stat_value(fig, r["hero"][0], r["hero"][2] if len(r["hero"]) > 2 else None)
        kind = "Focus On" if r["type"] == "focus_on" else "Core report"
        size = "small" if len(r["title"]) > 34 else ("mid" if len(r["title"]) > 22 else "")
        subtitle = "" if r["subtitle"] == "Focus On" else f'<h2>{escape(r["subtitle"])}</h2>'
        gap = ' style="margin-bottom:44px"' if not subtitle else ""
        doi = f'<span><b>DOI</b> {escape(r["doi"])}</span>' if r.get("doi") else ""
        self.starts[r["key"]] = self.add(f'''<div class="panel"><span class="eyebrow">{escape(wave["brand"])}</span>
<div class="hero num{" long" if len(hero) > 4 else ""}">{big(hero)}</div><p class="herocap">{escape(fig.fill(r["hero"][1]))}</p>
<div class="count">Report {index} of {len(REPORTS)}</div></div>
<div class="main"><span class="eyebrow kind">{kind}</span><h1 class="{size}"{gap}>{title_html(r["title"])}</h1>{subtitle}
<p class="lede">{escape(fig.fill(r["lede"]))}</p>
<div class="meta"><span><b>Published</b> {escape(r["published"])}</span><span><b>Data</b> {r["wave"]} poll, {wave["respondents"]} people in {wave["countries"]} countries and territories</span>{doi}</div></div>
{foot("{PAGE}", "")}''', "opener", r["wave"])

    def stat(self, fig, s):
        return (f'<div class="stat"><div class="n num">{big(stat_value(fig, s[0], s[2] if len(s) > 2 else None))}</div>'
                f'<div class="c">{escape(fig.fill(s[1]))}</div></div>')

    def numbers(self, r, fig):
        four = " four" if len(r["stats"]) == 4 else ""
        body = "".join(self.stat(fig, s) for s in r["stats"])
        self.add(f'{head(r, "In numbers")}<div class="stats{four}">{body}</div>{foot("{PAGE}", r["title"])}', "numbers", r["wave"])

    def chart_svg(self, r, fig, c, width, tallest=770):
        colour = WAVES[r["wave"]]["colour"]
        unit = c.get("unit", "%")
        if c["kind"] == "hbar":
            rows = [(label, fig.number(fid)) for label, fid in c["rows"]]
            height = min(tallest, max(400, 70 + 106 * len(rows)))
            return charts.hbar(rows, width, height, colour, unit, c.get("decimals", 0), c.get("highlight"),
                               NAVY if colour != NAVY else "#E3076E")
        if c["kind"] == "grouped":
            rows = [(label, [fig.number(f) for f in fids]) for label, fids in c["rows"]]
            height = min(tallest, max(420, 130 + len(rows) * (len(c["series"]) * 52 + 56)))
            return charts.grouped(rows, c["series"], width, height, unit, c.get("decimals", 0))
        if c["kind"] == "stacked":
            rows = []
            for label, fids in c["rows"]:
                values = [fig.number(f) for f in fids]
                if c.get("remainder"):
                    values.append(max(0, 100 - sum(values)))
                rows.append((label, values))
            return charts.stacked(rows, c["segments"], width, min(tallest, max(420, 130 + 150 * len(rows))), unit)
        if c["kind"] == "line":
            series = [(name, colour_, [fig.number(f) for f in fids]) for name, colour_, fids in c["series"]]
            return charts.line(c["years"], series, width, min(tallest, 720), unit)
        raise ValueError(c["kind"])

    def chart_text(self, fig, c):
        return (f'<p class="q"><b>Question text:</b> {escape(c["question"])}</p>'
                f'<p class="note"><b>Note:</b> {escape(fig.fill(c["note"]))}</p>')

    def chart(self, r, fig, c):
        self.add(f'''{head(r, "Chart")}<div class="text"><div class="rule"></div><h3>{escape(fig.fill(c["title"]))}</h3>{self.chart_text(fig, c)}</div>
<div class="plot">{self.chart_svg(r, fig, c, 1148)}</div>{foot("{PAGE}", r["title"])}''', "chart", r["wave"])

    def focus(self, r, fig):
        c = r["charts"][0]
        side = "".join(self.stat(fig, s) for s in r["stats"])
        self.add(f'''{head(r, "In numbers")}<div class="side">{side}</div>
<div class="body"><h3>{escape(fig.fill(c["title"]))}</h3>{self.chart_svg(r, fig, c, 1160, 540)}{self.chart_text(fig, c)}</div>
{foot("{PAGE}", r["title"])}''', "focus", r["wave"])

    def map_page(self, r):
        m = r["map"]
        wave = WAVES[r["wave"]]
        if m.get("kind") == "locator":
            return self.locator(r, m)
        values = getattr(maps, m["fn"])()
        cuts, colours, labels = classes(list(values), wave["colour"], m["unit"])
        lookup = values.to_dict()
        art = self.world.svg(1300, 635, lambda c: (colours[class_of(lookup[c], cuts)], 1) if c in lookup else (NO_DATA, 1))
        key = "".join(f'<div><i style="background:{col}"></i>{escape(lab)}</div>' for col, lab in reversed(list(zip(colours, labels))))
        key += f'<div><i style="background:{NO_DATA}"></i>Not surveyed or too few answers</div>'
        unit = m["unit"]
        ordered = values.sort_values()

        def rank(part):
            # never print "-0"
            return "".join(f'<div><span>{escape(self.names[c])}</span><b class="num">{round(v) + 0}{escape(unit)}</b></div>' for c, v in part.items())
        self.add(f'''{head(r, "Map")}<h3>{escape(m["title"])}</h3><p class="sub">{escape(m["sub"])}</p><div class="map">{art}</div>
<div class="side"><div class="block key"><h4>Key</h4>{key}</div>
<div class="block rank"><h4>Highest</h4>{rank(ordered[::-1][:5])}</div>
<div class="block rank"><h4>Lowest</h4>{rank(ordered[:5])}</div></div>
<p class="src">Computed for this book from the public World Risk Poll {r["wave"]} data, with the report's weights. {len(values)} countries and territories. Dots mark places too small to draw.</p>
{foot("{PAGE}", r["title"])}''', "mapp", r["wave"])

    def locator(self, r, m):
        colour = {code: c for code, _, _, c in m["places"]}

        def labels(place):
            out = []
            for code, name, _, c in m["places"]:
                x, y = self.world.centre(code, place)
                out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="15" fill="none" stroke="{c}" stroke-width="3"/>')
                out.append(f'<text x="{x:.1f}" y="{y - 26:.1f}" font-family="DM Sans, sans-serif" font-size="22" font-weight="700" text-anchor="middle" fill="{INK}" stroke="#FFFFFF" stroke-width="5" paint-order="stroke">{escape(name)}</text>')
            return "".join(out)
        art = self.world.svg(1300, 635, lambda c: (colour[c], 1) if c in colour else (NO_DATA, 1), extra=labels)
        places = "".join(f'<div class="place"><i style="background:{c}"></i><b>{escape(name)}</b><span>{escape(region)}</span></div>'
                         for _, name, region, c in m["places"])
        self.add(f'''{head(r, "Map")}<h3>{escape(m["title"])}</h3><p class="sub">{escape(m["sub"])}</p><div class="map">{art}</div>
<div class="side"><div class="block"><h4>Country and affected regions</h4>{places}</div></div>
{foot("{PAGE}", r["title"])}''', "mapp", r["wave"])

    # -- back matter

    def notes(self):
        self.add(f'''<div class="pad back"><h1><span class="eyebrow dot" style="display:block;margin-bottom:26px">About the numbers</span>How to read this book<span class="dot">.</span></h1>
<div><h4>Published figures</h4><p>The numbers in the text and charts are the figures printed in each report. They are read from the reports' reproduction files, which list every published figure with its page and compare it with the value computed from the public data. The file FIGURES.md beside this book lists each figure used here and how closely the data reproduces it.</p>
<h4>Weights and bases</h4><p>Figures are weighted to each country's adult population, so global and regional figures count people, not countries. People who were not asked a question are left out. Those who answered don't know or refused stay in the base, which is why some shares do not add to 100.</p>
<h4>Comparing polls</h4><p>The number of countries differs between polls: 142, 121, 142 and 140. Where a report compares two polls, it uses the countries surveyed in both, so a trend figure can differ from the single-poll figure for the same question.</p></div>
<div><h4>Maps</h4><p>The maps were computed for this book from the public data files and are not published figures. A country is left blank where it was not surveyed, the question was not asked there, or fewer than {maps.MIN_N} people answered. Each map's key splits the countries into five roughly equal groups.</p>
<h4>Gallup World Poll items</h4><p>Some findings combine World Risk Poll questions with Gallup World Poll items that are not part of the public data, such as country of birth, life evaluation and the wish to migrate. Those figures are shown as published and cannot be recomputed from the public files.</p>
<h4>Where to find the data</h4><p>The data, the methodology reports and the scripts that reproduce every report are at github.com/lrfoundation/world_risk_poll_data. The World Risk Poll Data Explorer is at tools.gsec.org.uk/wrp-explorer.html, and the reports are at wrp.lrfoundation.org.uk.</p></div>
</div>{foot("{PAGE}")}''', "w2021")

    def sources(self):
        parts = {key: chapters for key, _, chapters in SPLIT_2019}
        items = []
        for r in REPORTS:
            sep = " " if r["title"].endswith("?") else ": "
            title = r["title"] + ("" if r["subtitle"] == "Focus On" or r["wave"] == 2019 else sep + r["subtitle"])
            if r["type"] == "focus_on":
                title = "Focus On: " + title
            if r["key"] in parts:
                ch = parts[r["key"]]
                where = "chapters " + ", ".join(map(str, ch[:-1])) + " and " + str(ch[-1]) if len(ch) > 1 else f"chapter {ch[0]}"
                detail = f"World Risk Poll 2019 full report, {where}. Published 2020."
            else:
                detail = f'{WAVES[r["wave"]]["brand"]}. Published {r["published"]}.' + (f' doi.org/{r["doi"]}' if r.get("doi") else "")
            items.append(f'<div class="src w{r["wave"]}"><div class="pg num">{self.starts[r["key"]]}</div><div><b>{escape(title)}</b><span>{escape(detail)}</span></div></div>')
        self.add(f'''<div class="pad"><span class="eyebrow dot">Sources</span>
<h1 style="font-size:64px;font-weight:800;letter-spacing:-.035em;margin:22px 0 0">The 22 reports<span class="dot">.</span></h1>
<p class="srcnote">The 2019 poll was published as one report, The Lloyd's Register Foundation World Risk Poll: Full report and analysis of the 2019 poll. Numbers on the left are pages of this book.</p>
<div class="sources">{"".join(items)}</div></div>{foot("{PAGE}")}''', "w2021")

    def end(self):
        art = self.world.svg(1700, 830, lambda c: ("#FFFFFF", 0.1), stroke=NAVY, stroke_width=1)
        self.add(f'<div class="map">{art}</div><div class="logo">{self.logo.replace("#e5006e", "#FFFFFF")}</div>'
                 "<p><b>Lloyd's Register Foundation World Risk Poll</b><br>wrp.lrfoundation.org.uk<br>"
                 "Data and reproduction scripts: github.com/lrfoundation/world_risk_poll_data</p>", "end")

    # -- assembly

    def build(self):
        self.cover()
        self.about()
        contents_at = len(self.pages)
        self.pages.append("")  # contents, filled in once the page numbers are known
        index = 0
        for year in WAVES:
            self.wave_opener(year)
            for r in (r for r in REPORTS if r["wave"] == year):
                index += 1
                fig = Figures(r["folder"], self.used)
                self.opener(r, fig, index)
                if r["type"] == "focus_on":
                    self.focus(r, fig)
                    continue
                self.numbers(r, fig)
                for c in r["charts"]:
                    self.chart(r, fig, c)
                self.map_page(r)
        self.notes()
        self.sources()
        self.end()
        self.pages[contents_at] = f'<section class="page w2021">{self.contents().replace("{PAGE}", str(contents_at + 1))}</section>'

    def html(self):
        css = (HERE / "book.css").read_text(encoding="utf-8")
        return ('<!doctype html><html lang="en-GB"><head><meta charset="utf-8">'
                f"<title>{escape(BOOK)}</title><style>{font_faces()}\n{css}</style></head><body>"
                + "\n".join(self.pages) + "</body></html>")

    def figures_md(self):
        lines = [
            "# Figures used in the book", "",
            "Generated by `build.py`. Do not edit by hand. One row per published figure that appears in the",
            "book's text or charts, with the value the public data gives (from the report's `RESULTS.md`) and its",
            "status. `GALLUP_ONLY` figures need Gallup World Poll data that is not public, so they are shown as",
            "published. The maps are not in this list: `maps.py` computes them from the public data.", "",
            "| Report | Finding | Page | Published | From the data | Status | What it is |", "| --- | --- | --- | --- | --- | --- | --- |",
        ]
        counts = {}
        for (folder, fid), row in sorted(self.used.items()):
            value, status = statuses(folder).get(fid, ("", "NOT_RUN"))
            counts[status] = counts.get(status, 0) + 1
            lines.append(f'| {folder.split("/")[1]} | {fid} | {row["page"]} | {row["published_value"]} | {value} | {status} | {row["description"]} |')
        summary = ", ".join(f"{n} {s}" for s, n in sorted(counts.items(), key=lambda kv: -kv[1]))
        lines[7:7] = [f"{len(self.used)} figures: {summary}.", ""]
        return "\n".join(lines) + "\n", counts


def print_pdf(html_path, pdf_path):
    names = ["google-chrome", "chromium", "chromium-browser", "chrome", "msedge"]
    fixed = [r"C:\Program Files\Google\Chrome\Application\chrome.exe", r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
             "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"]
    browser = next((shutil.which(n) for n in names if shutil.which(n)), None) or next((p for p in fixed if Path(p).exists()), None)
    if not browser:
        sys.exit("No Chrome, Chromium or Edge found: open output/book.html and print it to PDF instead.")
    subprocess.run([browser, "--headless=new", "--no-sandbox", "--disable-gpu", "--no-pdf-header-footer",
                    f"--print-to-pdf={pdf_path}", html_path.as_uri()], check=True, capture_output=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--pdf", action="store_true", help="also print the book to PDF")
    args = parser.parse_args()
    book = Book()
    book.build()
    OUT.mkdir(exist_ok=True)
    html_path = OUT / "book.html"
    html_path.write_text(book.html(), encoding="utf-8")
    table, counts = book.figures_md()
    (HERE / "FIGURES.md").write_text(table, encoding="utf-8")
    print(f"{len(book.pages)} pages, {len(book.used)} published figures {counts} -> {html_path}")
    if args.pdf:
        pdf_path = OUT / "World_Risk_Poll_22_reports.pdf"
        print_pdf(html_path, pdf_path)
        print(f"PDF -> {pdf_path}")


if __name__ == "__main__":
    main()
