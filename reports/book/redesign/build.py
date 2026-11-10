"""Re-set a published report in the format of the 2025 poll's reports.

    python reports/book/redesign/build.py 2019_risk_at_work

Reads content/<key>.md (the report's text, in the markup described in
README.md) and writes ../output/redesign/<key>.html and .pdf: 1920 by 1080
pages with the furniture of the World Risk Poll 2026 reports. Text flows in two
columns; the browser breaks the columns and a short script in the page turns
them into pages, numbers them and fills in the contents list.

Charts are drawn from the report's published_figures.csv by finding ID, as in
the coffee table book. A chart that cannot be redrawn from the files in this
repository is placed as a picture of the original and listed in the report's
"Notes on this edition".
"""

import base64
import json
import re
import subprocess
import sys
from html import escape
from pathlib import Path

HERE = Path(__file__).resolve().parent
BOOK = HERE.parent
sys.path.insert(0, str(BOOK))
sys.path.insert(0, str(BOOK.parent))

import charts  # noqa: E402
import maps  # noqa: E402
from build import CACHE, GEOJSON, OUT, fetch  # noqa: E402
from figures import Figures  # noqa: E402
from worldmap import World, class_of, classes  # noqa: E402

FUCHSIA, GREEN, TEAL, ORANGE, PURPLE, LIME, GREY, NAVY = "#E3076E", "#00785C", "#00A7B3", "#F07800", "#7B50DE", "#8CAB00", "#BDBDBD", "#0D2240"
SERIES = [FUCHSIA, GREEN, TEAL, ORANGE, PURPLE, LIME]
NAMED = dict(fuchsia=FUCHSIA, green=GREEN, teal=TEAL, orange=ORANGE, purple=PURPLE, lime=LIME, grey=GREY, navy="#1A3D6D")
FONT_CSS = ("https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,400;0,9..40,500;0,9..40,600;0,9..40,700;0,9..40,800;0,9..40,900;"
            "1,9..40,400;1,9..40,600;1,9..40,700")
EXTRA_CSS = ("https://fonts.googleapis.com/css2?family=Noto+Sans:wght@600&family=Noto+Sans+SC:wght@600&family=Noto+Sans+Arabic:wght@600"
             "&text=%D1%80%D0%B8%D1%81%D0%BA%E9%A3%8E%E9%99%A9%D9%85%D8%AE%D8%A7%D8%B7%D8%B1%D8%A9")
SCALE = 0.6          # charts are drawn at the coffee table book's size and placed at this scale
CHART_W = 1300       # which makes them 780 px wide, the width of a text column
NO_DATA = "#EFEFEF"


def font_faces():
    css = fetch(FONT_CSS, CACHE / "dm-sans-report.css").read_text(encoding="utf-8")
    faces = []
    for block in re.findall(r"@font-face\s*{(.*?)}", css, flags=re.S):
        style = re.search(r"font-style:\s*(\w+)", block).group(1)
        weight = re.search(r"font-weight:\s*(\d+)", block).group(1)
        url = re.search(r"url\((https://[^)]+\.ttf)\)", block).group(1)
        path = fetch(url, CACHE / f"DMSans-{style}-{weight}.ttf")
        faces.append(f'@font-face {{ font-family: "DM Sans"; font-style: {style}; font-weight: {weight}; src: url("{path.as_uri()}") format("truetype"); }}')
    # The few words of other scripts that the reports print (chart labels in Russian, Chinese and Arabic): only those glyphs are fetched.
    extra = fetch(EXTRA_CSS, CACHE / "extra-scripts.css").read_text(encoding="utf-8")
    for i, block in enumerate(re.findall(r"@font-face\s*{(.*?)}", extra, flags=re.S)):
        url = re.search(r"url\((https://[^)]+)\)", block).group(1)
        path = fetch(url, CACHE / f"extra-scripts-{i}.ttf")
        faces.append(f'@font-face {{ font-family: "WRP Scripts"; font-weight: 100 900; src: url("{path.as_uri()}") format("truetype"); }}')
    return "\n".join(faces)


def duotone(png):
    """A photograph in the fuchsia duotone of the 2026 covers, as JPEG bytes."""
    import io
    from PIL import Image, ImageOps
    grey = ImageOps.autocontrast(Image.open(io.BytesIO(png)).convert("L"), cutoff=1)
    out = io.BytesIO()
    ImageOps.colorize(grey, black="#33051F", mid="#A8356F", white="#F6D3E1").save(out, "JPEG", quality=88)
    return out.getvalue()


# ---------------------------------------------------------------- reading the content file

def parse(path):
    text = path.read_text(encoding="utf-8")
    _, head, body = text.split("---", 2)
    meta = json.loads(head)
    notes, sections, new = {}, [], False
    section = flow = None
    for chunk in re.split(r"\n\s*\n", body.strip()):
        chunk = chunk.rstrip()
        note = re.match(r"\[\^(\w+)\]:\s*(.*)", chunk, flags=re.S)
        if note:
            notes[note.group(1)] = note.group(2).strip()
        elif chunk.startswith("::new"):
            new = True
        elif chunk.startswith("::endnew"):
            new = False
        elif chunk.startswith(("::front ", "::back ")):
            kind, title = chunk[2:].split(" ", 1)
            flow = dict(title=title, blocks=[])
            section = dict(kind=kind, title=title, flows=[flow], new=False)
            sections.append(section)
        elif chunk.startswith("::chapter "):
            title, big, caption = [part.strip() for part in chunk[10:].split("|")]
            flow = None
            section = dict(kind="chapter", title=title, big=big, caption=caption, opener=[], flows=[], new=False)
            sections.append(section)
        elif chunk.startswith("# "):
            flow = dict(title=chunk[2:], blocks=[])
            section["flows"].append(flow)
        elif flow is None:
            section["opener"].append(chunk)
        else:
            if new and not flow["blocks"]:
                section["new"] = True
            flow["blocks"].append(chunk)
    return meta, sections, notes


# ---------------------------------------------------------------- the report

class Report:
    def __init__(self, key):
        self.meta, self.sections, self.notes = parse(HERE / "content" / f"{key}.md")
        self.fig = Figures(self.meta["folder"], {})
        self.world = World(fetch(GEOJSON, CACHE / "ne_110m_admin_0_countries.geojson"))
        self.logo = (BOOK / "assets" / "lrf-logo.svg").read_text(encoding="utf-8")
        self.figures = []        # (label, title, anchor)
        self.why, self.small, self.renumbering = {}, None, True
        self.queries = []
        self.originals = set()
        self.counts = {"Chart": 0, "Table": 0}
        self.chapter = 0
        self.anchors = 0
        self.pdf = None

    # -- text

    def inline(self, text):
        # Chart and table numbers of the original become this report's numbers, except in text written for this edition.
        for old, new in (self.meta.get("renumber", {}).items() if self.renumbering else ()):
            text = text.replace(old, new)
        text = escape(text, quote=False)
        text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
        text = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"<em>\1</em>", text)
        text = re.sub(r"(https?://\S+?)(?=[.,;)]?(\s|$))", lambda m: f'<span class="url">{m.group(1)}</span>', text)
        return re.sub(r"((?:\[\^\w+\])+)", lambda m: '<sup class="ref">' + ", ".join(re.findall(r"\[\^(\w+)\]", m.group(1))) + "</sup>", text)

    def anchor(self):
        self.anchors += 1
        return f"a{self.anchors}"

    def source_pdf(self):
        if self.pdf is None:
            import pymupdf
            self.pdf = pymupdf.open(CACHE / "pdfs" / self.meta["pdf"])
        return self.pdf

    # -- figures

    def number(self, spec):
        kind = spec.get("as") or ("Table" if spec["kind"] == "table" or spec.get("table") else "Chart")
        self.counts[kind] = self.counts.get(kind, 0) + 1
        if spec.get("number"):
            return f"{kind} {spec['number']}"          # the number the original gives it
        if self.meta.get("numbering") == "chapter":
            return f"{kind} {self.chapter}.{self.counts[kind]}"
        return f"{kind} {self.counts[kind]}"

    def series(self, spec, names=None):
        """(name, colour) for each series: the spec's named colours, or the palette in order."""
        names = spec["series"] if names is None else names
        return list(zip(names, [NAMED.get(c, c) for c in spec["colours"]] if spec.get("colours") else SERIES))

    def values(self, ids):
        """Published values by finding ID; null stays None (a value the original does not show)."""
        return [self.fig.number(i) if i else None for i in ids]

    def label(self, text):
        """A row label; {finding_id} in it is replaced by that published value."""
        return re.sub(r"\{(\w+)\}", lambda m: self.fig.text(m.group(1)), text)

    def drawing(self, spec):
        charts.ZERO = spec.get("zero")          # "<0.5" where the original prints that for a value that rounds to nought
        try:
            return self.draw(spec)
        finally:
            charts.ZERO = None

    def draw(self, spec):
        kind = spec["kind"]
        unit = spec.get("unit", "%")
        if kind == "hbar":
            rows = [(r[0], self.fig.number(r[1])) for r in spec["rows"]]
            n = len(rows)
            height = 70 + (84 if n <= 8 else 74 if n <= 12 else 62 if n <= 16 else 54) * n
            key = colours = None
            if spec.get("key"):
                palette = dict(self.series(spec, spec["key"]))
                key, colours = list(palette.items()), [palette[r[2]] for r in spec["rows"]]
                height += 54
            elif spec.get("grey"):
                colours = [GREY if r[0] in spec["grey"] else FUCHSIA for r in spec["rows"]]
            return charts.scaled(charts.hbar(rows, CHART_W, height, FUCHSIA, unit=unit, colours=colours, key=key, label_width=spec.get("label_width", 0.34)), SCALE)
        if kind == "grouped":
            rows = [(label, self.values(ids)) for label, ids in spec["rows"]]
            series = self.series(spec)
            height = min(1260, 120 + len(rows) * (len(series) * 46 + 40))
            return charts.scaled(charts.grouped(rows, series, CHART_W, height, unit=unit), SCALE)
        if kind == "stacked":
            # An id of null is a segment the original draws but does not label. With "rest", what is left of 100 is drawn
            # as one pale segment under that name, without a figure.
            series, rows = self.series(spec), []
            for label, ids in spec["rows"]:
                values = [self.fig.number(i) if i else 0 for i in ids]
                rows.append((self.label(label), values + ([max(0, 100 - sum(values))] if spec.get("rest") else [])))
            if spec.get("rest"):
                series.append((spec["rest"], "#E9E9E9"))
            n = len(rows)
            height = 130 + (120 if n <= 6 else 88 if n <= 9 else 66) * n
            mute = (len(series) - 1,) if spec.get("rest") else ()
            svg = charts.scaled(charts.stacked(rows, series, CHART_W, height, unit=unit, label_all=True, mute=mute), SCALE)
            if charts.stacked.unlabelled:
                self.small = f"Segments of {max(charts.stacked.unlabelled):g}{unit} or less are too narrow to label."
            return svg
        if kind == "matrix":
            rows = [(label, self.values(ids)) for label, ids in spec["rows"]]
            row_height = 74 if len(rows) <= 6 else 58 if len(rows) <= 12 else 50
            return charts.scaled(charts.matrix(rows, spec["columns"], CHART_W, row_height, unit=unit, decimals=spec.get("decimals", 0),
                                               plain=tuple(spec.get("plain", ())), groups=spec.get("groups"), signed=tuple(spec.get("signed", ()))), SCALE)
        if kind == "stacked_pair":
            # Two sets of stacked bars side by side; a fourth entry in a row is the finding shown as text at the right.
            rows = []
            for label, first, second, *rest in spec["rows"]:
                text = None
                if rest and rest[0]:
                    value = self.fig.number(rest[0])
                    unit_ = spec.get("extra_unit", "")
                    text = ("+" if value > 0 else "−" if value < 0 else "") + f"{abs(value):g}" + (unit_[:-1] if unit_.endswith("pts") and abs(value) == 1 else unit_)
                rows.append((label, self.values(first), self.values(second), text))
            row_height = 58 if len(rows) <= 12 else 50
            svg = charts.scaled(charts.stacked_pair(rows, self.series(spec), spec["panels"], CHART_W, row_height, unit=unit, extra=spec.get("extra")), SCALE)
            if charts.stacked_pair.unlabelled:
                self.small = f"Segments of {max(charts.stacked_pair.unlabelled):g}{unit} or less are too narrow to label."
            return svg
        if kind == "region_map":
            return self.region_map(spec)
        if kind == "heading":
            return ""
        if kind == "vgrouped":
            panels = [(title, [(label, self.values(ids)) for label, ids in groups]) for title, groups in spec["panels"]]
            height = spec.get("panel_height", 520) * len(panels)
            return charts.scaled(charts.vgrouped(panels, self.series(spec), CHART_W, height, unit=unit), SCALE)
        if kind == "dumbbell":
            rows = [(label, self.values(ids[1:]), self.fig.number(ids[0])) for label, ids in spec["rows"]]
            series = self.series(spec, spec["series"][1:])
            return charts.scaled(charts.dumbbell(rows, series, CHART_W, 112 + 62 * len(rows), spec["series"][0], unit=unit,
                                                 total_unit=spec.get("total_unit")), SCALE)
        if kind == "map":
            return self.map(spec)
        if kind == "table":
            head = "".join(f"<th>{escape(c)}</th>" for c in spec["columns"])
            body = "".join(f"<tr><td>{escape(label)}</td>" + "".join(f"<td>{self.fig.text(f)}%</td>" for f in ([fid] if isinstance(fid, str) else fid)) + "</tr>"
                           for label, fid in spec["rows"])
            wide = " wide" if len(spec["columns"]) > 2 else ""
            return f'<table class="data{wide}"><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>'
        if kind == "original":
            import pymupdf
            page = self.source_pdf()[spec["page"]]
            png = page.get_pixmap(matrix=pymupdf.Matrix(4, 4), clip=pymupdf.Rect(*spec["clip"])).tobytes("png")
            return f'<img class="original" style="width:{spec.get("width", 780)}px" src="data:image/png;base64,{base64.b64encode(png).decode()}" alt="">'
        raise ValueError(kind)

    def map(self, spec):
        values = getattr(maps, spec["fn"])().to_dict()
        cuts, colours, labels = classes(values.values(), FUCHSIA, "%")

        def fill(code):
            return (colours[class_of(values[code], cuts)], 1) if code in values else (NO_DATA, 1)

        art = self.world.svg(780, 400, fill)
        key = "".join(f'<span><i style="background:{c}"></i>{escape(label)}</span>' for c, label in zip(reversed(colours), reversed(labels)))
        key += f'<span><i style="background:{NO_DATA}"></i>Not surveyed or too few answers</span>'

        def ranked(title, rows):
            items = "".join(f"<div><span>{escape(name)}</span><b>{self.fig.text(fid)}%</b></div>" for name, fid in rows)
            return f'<div class="rank"><h6>{title}</h6>{items}</div>'

        return (f'<div class="mapkey">{key}</div>{art}<div class="ranks">{ranked("Top 3", spec["top"])}{ranked("Bottom 3", spec["bottom"])}</div>')

    def region_map(self, spec):
        """Part of the world, with the countries the original names shaded by their published values."""
        from worldmap import SMALL, mix, project
        values = {code: self.fig.number(fid) for _, code, fid in spec["rows"]}
        lon0, lat0, lon1, lat1 = spec["box"]
        (xa, ya), (xb, yb) = project(lon0, lat1), project(lon1, lat0)
        width = 470
        k = width / (xb - xa)
        height = round(k * (yb - ya))
        top = max(values.values())

        def place(x, y):
            return k * (x - xa), k * (y - ya)

        def shade(code):
            return mix(FUCHSIA, 0.18 + 0.82 * values[code] / top) if code in values else NO_DATA

        out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}" role="img" '
               'font-family="DM Sans, sans-serif">']
        for code, rings in sorted(self.world.shapes.items()):
            d = "".join("M" + "L".join(f"{x:.1f},{y:.1f}" for x, y in (place(*pt) for pt in ring)) + "Z" for ring in rings)
            out.append(f'<path d="{d}" fill="{shade(code)}" stroke="#FFFFFF" stroke-width="0.8" stroke-linejoin="round" fill-rule="evenodd"/>')
        for code in values:
            if code in SMALL:
                x, y = place(*project(*SMALL[code]))
                out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="6" fill="{shade(code)}" stroke="#FFFFFF" stroke-width="1.5"/>')
        for name, code, fid in spec["rows"]:
            x, y = self.world.centre(code, place)
            dx, dy = spec.get("nudge", {}).get(code, (0, 0))
            out.append(f'<text x="{x + dx:.1f}" y="{y + dy + 5:.1f}" font-size="15" font-weight="900" text-anchor="middle" fill="#231F20" '
                       f'stroke="#FFFFFF" stroke-width="3.5" paint-order="stroke" stroke-linejoin="round">{self.fig.text(fid)}%</text>')
        out.append("</svg>")
        ranked = sorted(spec["rows"], key=lambda r: -values[r[1]])
        items = "".join(f"<div><span>{escape(name)}</span><b>{self.fig.text(fid)}%</b></div>" for name, _, fid in ranked)
        return f'<div class="regionmap">{"".join(out)}<div class="rank">{items}</div></div>'

    def figure(self, spec):
        label = self.number(spec)
        anchor = self.anchor()
        title = spec["title"]
        self.figures.append((label, title, anchor))
        if spec["kind"] == "original":
            self.originals.add(label)
            self.why[label] = spec.get("why", "the data behind the original is not in the public files")
        self.small = None
        art = self.drawing(spec)
        if spec.get("query"):
            self.queries.append(f"{label}. {spec['query']}")
        notes = []
        if spec.get("question"):
            notes.append(f'<p><b>Question text:</b> {self.inline(spec["question"])}</p>')
        if spec.get("note"):
            notes.append(f'<p><b>Note:</b> {self.inline(spec["note"])}</p>')
        if self.small:
            notes.append(f"<p><b>Note:</b> {self.small}</p>")
        if spec["kind"] == "map":
            notes.append("<p><b>Note:</b> Country shading was computed for this edition from the public " + str(self.meta["wave"]) + " data, in five groups of about equal size. "
                         "The countries named are the published figures.</p>")
        subtitle = f'<p class="sub">{self.inline(spec["subtitle"])}</p>' if spec.get("subtitle") else ""
        cls = "fig" + (" tall" if spec.get("tall") else "") + (" inline" if spec["kind"] == "table" else "") + (" head" if spec["kind"] == "heading" else "")
        return (f'<figure class="{cls}" id="{anchor}"><h4>{label}. {self.inline(title)}</h4>{subtitle}'
                f'<div class="art">{art}</div><div class="notes">{"".join(notes)}</div></figure>')

    # -- blocks

    def blocks(self, chunks):
        out, i = [], 0
        while i < len(chunks):
            chunk = chunks[i]
            if chunk.startswith("```chart"):
                out.append(self.figure(json.loads(chunk.split("\n", 1)[1].rsplit("```", 1)[0])))
            elif chunk.startswith("::column"):
                out.append('<div class="colbreak"></div>')
            elif chunk.startswith("## "):
                out.append(f"<h2>{self.inline(chunk[3:])}</h2>")
            elif chunk.startswith("### "):
                out.append(f"<h3>{self.inline(chunk[4:])}</h3>")
            elif chunk.startswith("> "):
                out.append(f'<p class="lead">{self.inline(chunk[2:])}</p>')
            elif chunk.startswith("- "):
                items = []
                while i < len(chunks) and (chunks[i].startswith("- ") or re.match(r"\s+A\. ", chunks[i])):
                    if chunks[i].startswith("- "):
                        items.append(self.inline(chunks[i][2:]))
                    else:
                        options = re.split(r"\s(?=[B-H]\. )", chunks[i].strip())
                        items[-1] += '<span class="options">' + "".join(f"<span>{self.inline(o)}</span>" for o in options) + "</span>"
                    i += 1
                out.append("<ul>" + "".join(f"<li>{item}</li>" for item in items) + "</ul>")
                continue
            elif re.match(r"\d+\. ", chunk):
                items, first = [], int(chunk.split(". ", 1)[0])
                while i < len(chunks) and re.match(r"\d+\. ", chunks[i]):
                    items.append(self.inline(chunks[i].split(". ", 1)[1]))
                    i += 1
                out.append(f'<ol class="findings" style="counter-reset: finding {first - 1}">' + "".join(f"<li>{item}</li>" for item in items) + "</ol>")
                continue
            else:
                out.append(f"<p>{self.inline(chunk)}</p>")
            i += 1
        return "".join(out)

    # -- pages

    def chrome(self):
        m = self.meta
        line = f'{m["brand"]}  ||  {m["title"]}  ||  {m.get("running", "Re-set in 2026 from the full report of the 2019 poll")}'
        return (f'<div class="rule top"></div><div class="rule bottom"></div><div class="credit">{escape(m["copyright"])}<br>{escape(line)}</div>'
                '<div class="pn"></div>')

    def flow_page(self, html, numbering, anchor=None):
        ident = f' id="{anchor}"' if anchor else ""
        return (f'<section class="page body" data-num="{numbering}"{ident}>{self.chrome()}'
                f'<div class="window"><div class="flow">{html}</div></div></section>')

    def cover(self):
        m = self.meta
        photo = ""
        if m.get("cover_image"):
            import pymupdf
            doc = self.source_pdf()
            xref = doc[m["cover_image"][0]].get_images()[m["cover_image"][1]][0]
            pix = pymupdf.Pixmap(doc, xref)
            if pix.n - pix.alpha >= 4:
                pix = pymupdf.Pixmap(pymupdf.csRGB, pix)
            photo = f'<img src="data:image/jpeg;base64,{base64.b64encode(duotone(pix.tobytes("png"))).decode()}" alt="">'
        return (f'<section class="page cover" data-num="none"><div class="photo">{photo}</div><div class="panel"></div>'
                '<svg class="edge" viewBox="0 0 1920 1080"><line x1="606.7" y1="0" x2="932.9" y2="1080" stroke="#E3076E" stroke-width="3"/></svg>'
                f'<div class="logo">{self.logo.replace("#e5006e", "#FFFFFF")}</div>'
                f'<div class="wrp">World Risk Poll</div><div class="rep">Report {m["wave"]}</div>'
                f'<div class="name"><b>{escape(m["title"])}{"" if m["title"][-1] in "?!" else ":"}</b><br>{escape(m["subtitle"])}</div>'
                f'<div class="series">{escape(m["series"])}</div><div class="gallup">Powered by <b>GALLUP</b></div></section>')

    def opener(self, section, number, anchor):
        text = "".join(f"<p>{self.inline(c)}</p>" for c in section["opener"])
        parts = section["big"].split(" in ")
        if len(parts) == 2:
            size = "two" if len(parts[0] + parts[1]) <= 2 else "three"
            big = f'<div class="big {size}"><span>{parts[0]}</span><i>in</i><span>{parts[1]}</span></div>'
        else:
            big = f'<div class="big single"><span>{escape(section["big"])}</span></div>'
        return (f'<section class="page opener" data-num="main" id="{anchor}">{self.chrome()}<div class="block"></div>'
                f'<div class="logo">{self.logo.replace("#e5006e", "#FFFFFF")}</div>'
                f'<div class="left"><div class="chap">Chapter {number}</div><h1>{self.inline(section["title"])}</h1><div class="text">{text}</div></div>'
                f'{big}<div class="cap">{self.inline(section["caption"])}</div></section>')

    def build(self):
        pages, toc = [], []
        tag = '<span class="newtag">New for this edition</span>'
        body, chapter, numbering = [], 0, "front"
        for section in self.sections:
            if section["kind"] == "chapter":
                chapter += 1
                self.chapter = chapter
                if self.meta.get("numbering") == "chapter":
                    self.counts = {"Chart": 0, "Table": 0}
                numbering = "main"
                anchor = self.anchor()
                toc.append(("chapter", f"Chapter {chapter}", section["title"], anchor))
                body.append(self.opener(section, chapter, anchor))
            html = ""
            for index, flow in enumerate(section["flows"]):
                anchor = self.anchor()
                new = tag if section["new"] and index == 0 else ""
                level = "sub" if section["kind"] == "chapter" else "top"
                toc.append((level, "", flow["title"], anchor))
                self.renumbering = not section["new"]
                html += f'<h1 id="{anchor}">{self.inline(flow["title"])}</h1>{new}' + self.blocks(flow["blocks"])
                self.renumbering = True
            body.append(self.flow_page(html, numbering if section["kind"] != "back" else "main"))
        # Back matter made here: references, then notes on this edition.
        if self.notes:
            anchor = self.anchor()
            toc.append(("top", "", "References", anchor))
            refs = "".join(f'<li value="{n}">{self.inline(text)}</li>' for n, text in self.notes.items())
            body.append(self.flow_page(f'<h1 id="{anchor}">References</h1><ol class="refs">{refs}</ol>', "main"))
        anchor = self.anchor()
        toc.append(("top", "", "Notes on this edition", anchor))
        body.append(self.flow_page(self.edition_notes(tag, anchor), "main"))

        rows = ""
        for level, label, title, anchor in toc:
            if level == "chapter":
                rows += f'<div class="row chapter"><span>{label}: {self.inline(title)}</span><span class="n" data-ref="{anchor}"></span></div>'
            else:
                rows += f'<div class="row {level}"><span>{self.inline(title)}</span><span class="n" data-ref="{anchor}"></span></div>'
        figures = "".join(f'<div class="row figrow"><span><b>{label}.</b> {self.inline(title)}</span><span class="n" data-ref="{anchor}"></span></div>'
                          for label, title, anchor in self.figures)
        contents = (f'<h1>Contents</h1><div class="toc">{rows}</div>'
                    f'<h1>List of figures</h1><div class="toc">{figures}</div>')
        # Contents sits after the first front section, as in the 2026 reports' front matter.
        front = [p for p in body if 'data-num="front"' in p]
        rest = [p for p in body if 'data-num="front"' not in p]
        lead = 0 if self.meta.get("contents_first") else 1
        pages = [self.cover()] + front[:lead] + [self.flow_page(contents, "front")] + front[lead:] + rest
        return pages

    def edition_notes(self, tag, anchor):
        m = self.meta
        self.renumbering = False
        charts_ = [label for label, _, _ in self.figures if label.startswith("Chart")]
        out = [f'<h1 id="{anchor}">Notes on this edition</h1>{tag}',
               f"<p><b>Source.</b> {escape(m['source'])}. The text is reproduced word for word, apart from the changes listed here.</p>"]
        if m.get("numbering") == "sequential" and m.get("renumber"):
            pairs = "; ".join(f"‘{old.strip()}n’ in the original is ‘{new.strip()} n’ here" for old, new in m["renumber"].items())
            out.append(f"<p><b>Numbering.</b> Charts and tables are numbered in one sequence for this report ({len(charts_)} charts, "
                       f"{self.counts['Table']} table): {pairs}. {m.get('references', 'References keep the numbers of the original footnotes.')}</p>")
        elif m.get("numbering_note"):
            out.append(f"<p><b>Numbering.</b> {self.inline(m['numbering_note'])}</p>")
        if m.get("edits"):
            out.append("<p><b>Wording and headings.</b></p><ul>" + "".join(f"<li>{self.inline(e)}</li>" for e in m["edits"]) + "</ul>")
        out.append("<p><b>Charts.</b> Charts are redrawn from the values printed in the original, in the chart style of the World Risk Poll 2026 reports. "
                   "Chart titles and question texts are the original ones.</p>")
        if m.get("chart_note"):
            out.append(f"<p>{self.inline(m['chart_note'])}</p>")
        reasons = {}
        for label, _, _ in self.figures:
            if label in self.originals:
                reasons.setdefault(self.why[label], []).append(label)
        for why, labels in reasons.items():
            numbers = [label.replace("Chart ", "") for label in labels]
            names = labels[0] if len(labels) == 1 else "Charts " + ", ".join(numbers[:-1]) + " and " + numbers[-1]
            verb = "is placed as a picture" if len(labels) == 1 else "are placed as pictures"
            out.append(f"<p><b>{names}</b> {verb} of the original, because {why}.</p>")
        if m.get("pending"):
            out.append(f"<p><b>Not yet set.</b> {self.inline(m['pending'])}</p>")
        for query in self.queries + m.get("queries", []):
            out.append(f"<p><b>Query.</b> {self.inline(query)}</p>")
        self.renumbering = True
        return "".join(out)

    def html(self):
        css = (HERE / "report.css").read_text(encoding="utf-8")
        script = (HERE / "paginate.js").read_text(encoding="utf-8")
        pages = self.build()
        return ('<!doctype html><html lang="en-GB"><head><meta charset="utf-8">'
                f'<title>{escape(self.meta["title"])}</title><style>{font_faces()}\n{css}</style></head><body>'
                + "\n".join(pages) + f"<script>{script}</script></body></html>")


def print_pdf(html_path, pdf_path):
    import shutil
    browser = next(shutil.which(n) for n in ["google-chrome", "chromium", "chromium-browser", "chrome", "msedge"] if shutil.which(n))
    subprocess.run([browser, "--headless=new", "--no-sandbox", "--disable-gpu", "--no-pdf-header-footer", "--virtual-time-budget=20000",
                    f"--print-to-pdf={pdf_path}", html_path.as_uri()], check=True, capture_output=True)
    # Chrome writes 1440 by 810 pt pages (CSS pixels); the 2026 reports are 1920 by 1080 pt.
    import pymupdf
    small, full = pymupdf.open(pdf_path), pymupdf.open()
    for index in range(len(small)):
        full.new_page(width=1920, height=1080).show_pdf_page(pymupdf.Rect(0, 0, 1920, 1080), small, index)
    data = full.tobytes(garbage=4, deflate=True)
    small.close()
    Path(pdf_path).write_bytes(data)


def main():
    key = sys.argv[1]
    report = Report(key)
    report.meta.setdefault("brand", f"World Risk Poll {report.meta['wave']}")
    out = OUT / "redesign"
    out.mkdir(parents=True, exist_ok=True)
    html_path, pdf_path = out / f"{key}.html", out / f"{key}.pdf"
    html_path.write_text(report.html(), encoding="utf-8")
    print_pdf(html_path, pdf_path)
    print(f"{len(report.figures)} figures -> {pdf_path}")


if __name__ == "__main__":
    main()
