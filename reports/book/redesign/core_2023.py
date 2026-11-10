"""Read the text of a report of the 2023 poll from its PDF.

The six reports of the 2023 poll (published in 2024 and 2025) share one design:
landscape pages of 842 by 595 points, two columns of DM Sans 8, section titles
in pink 20, headings in navy 14 and 10, charts under a bold black title with a
teal mark beside it, boxes on a grey ground, notes at the foot of a column
marked i, ii, iii, and numbered references at the back.

The PDFs hold DM Sans as one variable font, so a bold span has the same font
name as a regular one. weight() tells them apart by width: the same words set
bold are about 4% wider than the regular face would make them.

read() turns pages into a list of typed items in reading order (left column,
then right); assemble_2023.py arranges them as a content file.

    python reports/book/redesign/core_2023.py core_a_world_of_waste.pdf 5 8

prints the items of pages 5 to 8 (counted from 0), for checking by eye.
"""

import re
import sys
from pathlib import Path

import pymupdf

BOOK = Path(__file__).resolve().parent.parent
PDFS = BOOK / ".cache" / "pdfs"
FACES = {}
GUTTER = 421                    # a line that starts left of this is in the left column
TOP, BOTTOM = 30, 572           # page furniture lies outside these
NAVY = (0x163240, 0x41647E, 0x17E7E, 0x3E3F)
ROMAN = r"(?=[ivx])(?:x{0,2}(?:ix|iv|v?i{0,3}))"
FIGURE = r"(?:Appendix )?(Chart|Table|Figure|Map) (\d+(?:\.\d+)?[a-z]?)[.:]?\s"


def face(italic):
    """The regular or italic face of DM Sans, for measuring (build.py downloads both)."""
    name = "italic" if italic else "normal"
    if name not in FACES:
        FACES[name] = pymupdf.Font(fontfile=str(BOOK / ".cache" / f"DMSans-{name}-400.ttf"))
    return FACES[name]


def weight(span):
    """How much wider a span's letters are than the regular face would set them: about 1.0 regular, 1.04 bold.

    Measured letter by letter, so that the wider word spaces of justified text do not count.
    """
    return span.get("weight")


def measured(span):
    """A span of the page's raw text as a plain span, with its text and its weight."""
    font = face("Italic" in span["font"])
    got = expected = 0.0
    letters = 0
    for ch in span["chars"]:
        if ch["c"].isalpha():
            letters += 1
            got += ch["bbox"][2] - ch["bbox"][0]
            expected += font.glyph_advance(ord(ch["c"])) * span["size"]
    out = {k: v for k, v in span.items() if k != "chars"}
    out["text"] = "".join(ch["c"] for ch in span["chars"])
    out["weight"] = got / expected if letters >= 5 and expected else None
    return out


def tiny(spans):
    """True for a bullet or a note mark on its own."""
    text = "".join(s["text"] for s in spans).strip()
    return len(text) <= 2 or (max(s["size"] for s in spans) < 5.5 and re.fullmatch(rf"[\d,\s]+|{ROMAN}(?:,\s*{ROMAN})*", text) is not None)


def numeral(spans):
    return spans[0]["size"] >= 21 and spans[0]["color"] == 0xFFFFFF


def shape(spans):
    main = max(spans, key=lambda s: len(s["text"].strip()))
    return dict(spans=spans, x0=min(s["bbox"][0] for s in spans), x1=max(s["bbox"][2] for s in spans), y0=main["bbox"][1], y1=main["bbox"][3],
                size=main["size"], tiny=tiny(spans))


def lines_of(page):
    """The lines of a page: spans that share a baseline and sit side by side, however the PDF groups them."""
    parts = []
    for block in page.get_text("rawdict")["blocks"]:
        for line in block.get("lines", []):
            if abs(line["dir"][0] - 1) > 0.01:
                continue                                  # type set on its side: the name of a chart's axis
            run = []
            for span in line["spans"]:
                span = measured(span)
                if not span["text"].strip():
                    continue
                if run and span["bbox"][0] - run[-1]["bbox"][2] > 28:
                    parts.append(run)
                    run = []
                run.append(span)
            if run:
                parts.append(run)
    lines = []
    for run in sorted(parts, key=lambda r: (min(s["bbox"][1] for s in r), r[0]["bbox"][0])):
        new = shape(run)
        # a note mark, or a bullet, that the PDF holds apart from its line
        for line in lines:
            reach = min(new["y1"], line["y1"]) - max(new["y0"], line["y0"])
            near = -2 <= new["x0"] - line["x1"] < 26 or -2 <= line["x0"] - new["x1"] < 26
            if (near and (new["tiny"] or line["tiny"]) and not numeral(run) and not numeral(line["spans"]) and (line["x0"] < GUTTER) == (new["x0"] < GUTTER)
                    and reach > 0.5 * min(new["y1"] - new["y0"], line["y1"] - line["y0"])):
                line.update(shape(sorted(line["spans"] + run, key=lambda s: s["bbox"][0])))
                break
        else:
            lines.append(new)
    return lines


def main_span(line):
    spans = [s for s in line["spans"] if s["size"] >= 0.7 * line["size"]]
    return max(spans or line["spans"], key=lambda s: len(s["text"].strip()))


def kind_of(line):
    """What a line is, from the type of its longest span."""
    span = main_span(line)
    size, colour, italic = round(span["size"], 1), span["color"], "Italic" in span["font"]
    text = "".join(s["text"] for s in line["spans"]).strip()
    if size >= 21 and colour == 0xFFFFFF and re.fullmatch(r"\d+\.", text):
        return "number"             # a chapter's number, white on a pink tab
    if 19.5 <= size <= 20.5 and colour >> 16 > 0xD0 and (colour >> 8) & 0xFF < 0x40:
        return "title"
    if 17 <= size <= 19 and italic:
        return "quote"              # a sentence of the text, repeated large
    if 13.5 <= size <= 14.5:
        return "h1"
    if 11.5 <= size <= 12.5 and colour in NAVY:
        return "h2"
    if "SC700" in span["font"]:
        return "boxtitle"
    if 9.5 <= size <= 10.5:
        if colour in NAVY:
            return "h2"
        if colour == 0xFFFFFF and line["y0"] < 60:
            return None
        return "figtitle" if (weight(span) or 1.04) > 1.03 else "p"
    if 7.8 <= size <= 8.2:
        return "p"
    if 4.8 <= size <= 5.1 and colour != 0x747171:
        return "small"
    if 4 < size < 7.8:
        return "letter"             # the lettering of a chart or a table
    return None


def rich(lines, plain=False):
    """The text of a paragraph's lines with **bold**, *italic* and [^n] note marks."""
    runs = []
    for line in lines:
        if runs and runs[-1][1]:
            end = runs[-1][1].rstrip()
            runs[-1][1] = end if end.endswith("/") or re.search(r"\w-$", end) and not re.search(r"\s[-–]$", end) else end + " "
        bold, before = False, None
        for span in line["spans"]:
            text = span["text"].replace("\t", " ").replace("\xad", "").replace("\xa0", " ")
            if before is not None and span["bbox"][0] - before["bbox"][2] > 0.18 * span["size"] and not before["text"].endswith((" ", "\t")) and not text.startswith(" "):
                text = " " + text               # set apart without a space character
            before = span
            mark = text.strip()
            if span["size"] < 0.7 * line["size"] and mark and re.fullmatch(rf"[\d,\s]+|{ROMAN}(?:,\s*{ROMAN})*", mark):
                style, text = "", "".join(f"[^{n}]" for n in re.findall(r"\w+", mark))
            else:
                w = weight(span)
                bold = bold if w is None else w > 1.03
                style = ("*" if "Italic" in span["font"] else "") + ("**" if bold else "")
            if runs and (runs[-1][0] == style or not text.strip()):
                runs[-1][1] += text
            else:
                runs.append([style, text])
    styles = {style for style, text in runs if text.strip() and not text.startswith("[^")}
    out = ""
    for style, text in runs:
        if plain or not style or len(styles) == 1 or not text.strip():
            out += text
        else:
            lead, core, tail = re.match(r"(\s*)(.*?)(\s*)$", text, flags=re.S).groups()
            out += f"{lead}{style}{core}{style[::-1]}{tail}"
    out = out.replace("ﬀ", "ff").replace("ﬁ", "fi").replace("ﬂ", "fl")
    out = re.sub(r"(\*+) (\1)(?=\S)", " ", out)
    out = re.sub(r"^\s*_\s+", "", out)                  # a rule drawn with an underscore
    return re.sub(r"\s+", " ", out).strip(), (styles.pop() if len(styles) == 1 else "")


def boxes_of(page):
    """The grey grounds of a page's boxes. A ground drawn in two pieces, one over the other, is one box."""
    out = []
    for g in page.get_drawings():
        fill, r = g.get("fill"), g["rect"]
        if fill and r.width > 150 and r.height > 40 and max(fill) - min(fill) < 0.08 and 0.78 < fill[0] < 0.93 and not (r.width > 700 and r.height > 500):   # (not a tint over a whole page)
            out.append([r.x0, r.y0, r.x1, r.y1])
    out.sort(key=lambda b: (b[0] >= GUTTER, b[1]))
    merged = []
    for b in out:
        last = merged[-1] if merged else None
        if last and (last[0] >= GUTTER) == (b[0] >= GUTTER) and b[1] <= last[3] + 14 and min(last[2], b[2]) - max(last[0], b[0]) > 0.6 * min(last[2] - last[0], b[2] - b[0]):
            last[:] = [min(last[0], b[0]), min(last[1], b[1]), max(last[2], b[2]), max(last[3], b[3])]
        else:
            merged.append(b)
    return [tuple(b) for b in merged]


def marker(line):
    """The mark that opens a list entry and the line without it: ("- " | "-- " | "3. ", line), or None."""
    spans = line["spans"]
    first = spans[0]["text"].strip()
    rest = None
    if len(spans) > 1 and first in ("•", "●", "-", "–"):
        mark, rest = ("-- " if first in "-–" else "- "), spans[1:]
    elif len(spans) > 1 and re.fullmatch(r"\d+\.", first) and (spans[0]["color"] != spans[1]["color"] or "\t" in spans[0]["text"] + spans[1]["text"]):
        mark, rest = first + " ", spans[1:]
    else:
        m = re.match(r"\s*(?:([•●])|(\d+)\.(?=\t))\s*", spans[0]["text"])
        if not m or m.end() >= len(spans[0]["text"]):
            return None
        mark = "- " if m.group(1) else m.group(2) + ". "
        share = 1 - m.end() / len(spans[0]["text"])
        x1 = spans[0]["bbox"][2]
        x0 = x1 - (x1 - spans[0]["bbox"][0]) * share
        rest = [dict(spans[0], text=spans[0]["text"][m.end():], bbox=(x0, spans[0]["bbox"][1], x1, spans[0]["bbox"][3]))] + spans[1:]
    return mark, dict(line, spans=rest, x0=rest[0]["bbox"][0])


def page_items(page, index, small_text=False, box_gap=12.3):
    """(items in reading order, {mark: note at the foot of the page}) of one page.

    small_text: the page's text is set in 7 point (a closing page). box_gap: the most that two lines of one
    paragraph in a box are apart (the boxes of the core reports are set on 11 points, those of the 2026 Focus On on 13).
    """
    grounds = boxes_of(page)
    columns = ([], [])
    for line in lines_of(page):
        if line["y0"] < TOP or line["y0"] > BOTTOM:
            continue
        kind = kind_of(line)
        if kind is None:
            continue
        cx, cy = (line["x0"] + min(line["x1"], line["x0"] + 60)) / 2, (line["y0"] + line["y1"]) / 2
        line["box"] = next((b for b in grounds if b[0] - 2 <= cx <= b[2] and b[1] - 2 <= cy <= b[3] + 2), None)
        if (small_text or line["box"]) and kind == "letter" and 6.9 <= line["size"] <= 7.1 and not re.fullmatch(r"[\d%.,+\-−\s]*", "".join(s["text"] for s in line["spans"])):
            kind = "p"                      # text set in 7 point: a closing page, or the text of a box
        line["kind"] = kind
        columns[line["x0"] >= GUTTER].append(line)

    items, notes = [], {}
    for col, lines in enumerate(columns):
        lines.sort(key=lambda l: (l["y0"], l["x0"]))
        paras, footing, lettering = [], False, []
        for line in lines:
            kind = line["kind"]
            text = "".join(s["text"] for s in line["spans"]).strip()
            if kind == "letter" and 5.4 <= line["size"] <= 6.6:
                # small print set a little larger than usual: a survey question under a chart, and the lines that follow it
                before = paras[-1]["lines"][-1] if paras and paras[-1]["kind"] == "small" else None
                light = "Light" in main_span(line)["font"]         # (the small print of the 2026 Focus On: 6 point, in the light face)
                if light or re.match(r"\*?(Survey|Poll) questions?( \d{4}(, \d{4})*)?:|Notes?:", text) or (before is not None and abs(before["size"] - line["size"]) < 0.3
                                                                    and 0 < line["y0"] - before["y0"] < 2.1 * line["size"] and not footing):
                    kind = line["kind"] = "small"
            if kind == "small" and re.match(r"<?[\d.]+%?\s*\|", text):
                kind = line["kind"] = "letter"          # a value and its change beside a bar ("16% | +3pp"), set as small as the notes
            if kind == "letter":
                lettering.append(dict(kind=kind, lines=[line], box=line["box"], indent=line["x0"], mark=None))
                continue
            if kind == "small":
                if re.match(rf"{ROMAN}\s+[-–]\s", text):
                    footing = True
                if footing:
                    kind = line["kind"] = "foot"
            last = paras[-1] if paras else None
            gap = line["y0"] - last["lines"][-1]["y0"] if last else 0
            limit = {"p": 11.5 if line["size"] < 7.5 else box_gap if line["box"] else 16.5, "small": 8.5, "foot": 9.5, "letter": 0}.get(kind, 1.6 * line["size"])
            mark = marker(line) if kind == "p" else None
            new_note = kind == "foot" and re.match(rf"{ROMAN}\s+[-–]\s", text)
            same = (last is not None and last["kind"] == kind and last["box"] == line["box"] and 0 <= gap <= limit and not mark and not new_note
                    and not (kind == "p" and line["x0"] < last["indent"] - 6)
                    and not (kind == "small" and re.match(r"Survey questions?:|Poll questions?:|\*|Source", text) and gap > 5.2))
            if kind == "figtitle" and last is not None and last["kind"] == "figtitle" and not re.match(FIGURE, text) and 0 <= gap <= 16:
                same = True
            if same:
                last["lines"].append(line)
                if len(last["lines"]) == 2:
                    last["indent"] = line["x0"]
            else:
                para = dict(kind=kind, lines=[line], box=line["box"], indent=line["x0"], mark=None)
                if mark:
                    para.update(mark=mark[0], lines=[mark[1]], indent=mark[1]["x0"])
                paras.append(para)
        for para in paras + lettering:
            ls = para["lines"]
            item = dict(kind=para["kind"], page=index, col=col, x0=min(l["x0"] for l in ls), y0=ls[0]["y0"], x1=max(l["x1"] for l in ls), y1=ls[-1]["y1"],
                        box=para["box"], mark=para["mark"], size=ls[0]["size"])
            item["text"], item["style"] = rich(ls, plain=para["kind"] != "p")
            if para["kind"] == "quote":
                item["text"] = item["text"].strip("“”\" ")
            if para["kind"] == "foot":
                m = re.match(rf"({ROMAN})\s+[-–]\s+", item["text"])
                if m:
                    notes[m.group(1)] = item["text"][m.end():]
                elif notes:
                    notes[list(notes)[-1]] += " " + item["text"]
            if item["text"]:
                items.append(item)
    return items, notes


def extent(page, chart, items, floor):
    """Where a chart's drawing lies on its page, as [x0, y0, x1, y1], and the rectangles in it to blank out.

    It runs from under the title to floor (the top of the chart's small print, or of the next text in
    the column), and is then drawn in to what is actually there. A chart with marks across the gutter
    takes both columns.
    """
    col = chart["col"]
    edges = (22, GUTTER - 4) if col == 0 else (GUTTER + 1, 818)
    marks = [fitz_rect(g["rect"]) for g in page.get_drawings()]
    marks += [tuple(i["bbox"]) for i in page.get_image_info() if i["bbox"][3] - i["bbox"][1] < 90]

    def inside(r, x0, x1):
        return (r[0] >= x0 - 2 and r[2] <= x1 + 2 and r[1] >= chart["y1"] - 2 and r[3] <= floor + 2
                and (r[2] - r[0]) * (r[3] - r[1]) < 0.9 * (x1 - x0) * (floor - chart["y1"]))

    wide = col == 0 and (any(r[0] < GUTTER - 16 and r[2] > GUTTER + 24 and inside(r, 22, 818) for r in marks)
                         or any(i["kind"] == "used" and i["col"] == 1 and chart["y1"] < i["y0"] < floor for i in items))
    blank = []
    if wide:
        edges = (22, 818)
        blank = [[round(i["x0"] - 4), round(i["y0"] - 3), 818, round(i["y1"] + 3)] for i in items
                 if i["col"] == 1 and i["kind"] not in ("letter", "foot") and i["y1"] > chart["y1"] and i["y0"] < floor]
    found = [r for r in marks if inside(r, *edges)]
    found += [(i["x0"], i["y0"], i["x1"], i["y1"]) for i in items
              if i["kind"] in ("letter", "used") and edges[0] <= i["x0"] <= edges[1] and chart["y1"] - 1 <= i["y0"] <= floor]
    if not found:
        return [edges[0], round(chart["y1"]), edges[1], round(floor)], blank
    box = [max(edges[0], min(r[0] for r in found) - 5), max(chart["y1"] + 1, min(r[1] for r in found) - 4),
           min(edges[1], max(r[2] for r in found) + 5), min(floor, max(r[3] for r in found) + 4)]
    if box[3] - box[1] < 40:
        box = [edges[0], chart["y1"] + 1, edges[1], floor]          # nothing drawn that can be found: all the room there is
    return [round(v) for v in box], [b for b in blank if b[1] < box[3] and b[3] > box[1]]


def entries(page, clip, size=(6.8, 7.4)):
    """The text set inside a table, as [[lead, text, [bullets]]]: an entry opens with a lead in pink, bullets hang under it."""
    out, where = [], None
    for line in sorted(lines_of(page), key=lambda l: (l["y0"], l["x0"])):
        if not (clip[0] <= line["x0"] <= clip[2] and clip[1] <= line["y0"] <= clip[3] and size[0] <= line["size"] <= size[1]):
            continue
        spans = line["spans"]
        if spans[0]["text"].strip() in ("•", "●"):
            out[-1][2].append(rich([dict(line, spans=spans[1:])], plain=True)[0])
            where = "bullet"
        elif spans[0]["color"] != 0 and main_span(line)["color"] == 0 or (len(spans) == 1 and spans[0]["color"] != 0 and spans[0]["text"].strip().endswith(":")):
            lead = "".join(s["text"] for s in spans if s["color"] != 0).strip()
            out.append([lead, rich([dict(line, spans=[s for s in spans if s["color"] == 0])], plain=True)[0] if any(s["color"] == 0 for s in spans) else "", []])
            where = "entry"
        elif where == "bullet":
            out[-1][2][-1] += " " + rich([line], plain=True)[0]
        elif out:
            out[-1][1] = (out[-1][1] + " " + rich([line], plain=True)[0]).strip()
    return out


def sentences(page, clip, size):
    """The lines of one size inside a rectangle, as one run of text."""
    lines = [l for l in sorted(lines_of(page), key=lambda l: (l["y0"], l["x0"]))
             if clip[0] <= l["x0"] <= clip[2] and clip[1] <= l["y0"] <= clip[3] and size[0] <= l["size"] <= size[1]]
    return rich(lines, plain=True)[0]


def fitz_rect(r):
    return (r.x0, r.y0, r.x1, r.y1)


def headed(item, items, label, page):
    """Make a chart of a heading: the form of the Focus On reports of 2025 and 2026, whose charts carry no numbers.

    The heading is the chart's title; a paragraph in italic under it describes the chart; the chart follows, and under
    it, in 7 point, the report's own citation and the question text. The chart takes the number the plan gives it.
    """
    column = sorted((i for i in items if i["col"] == item["col"] and i["y0"] > item["y1"] - 1), key=lambda i: i["y0"])
    text = [i for i in column if i["kind"] != "letter"]
    describes = text[0] if text and text[0]["kind"] == "p" and text[0]["style"] == "*" and text[0]["y0"] - item["y1"] < 30 else None
    after = text[1:] if describes else text
    end = after[0]["y0"] if after else BOTTOM
    small = [i for i in column if i["kind"] == "letter" and 6.9 <= i["size"] <= 7.08 and i["y0"] < end]
    lines = []
    for i in small:
        i["kind"] = "used"
        if lines and not re.match(r"(Poll|Survey) questions?:|Note|Callout|\*", i["text"]):
            lines[-1] += " " + i["text"]
        else:
            lines.append(i["text"])
    if describes:
        describes["kind"] = "used"
    top = dict(item, y1=describes["y1"] if describes else item["y1"])
    floor = (small[0]["y0"] if small else end) - 2
    item.update(kind="chart", label=label, title=item["text"], small=[re.sub(r"\s+", " ", line).strip() for line in lines],
                subtitle=describes["text"].strip("*") if describes else "")
    item["clip"], item["blank"] = extent(page, top, items, floor)


def read(doc, first, last, numbers=None, small_text=(), box_gap=12.3):
    """(items, page notes) of pages first to last, counted from 0. Each chart item carries its title, small print and extent.

    A chart runs from its title to its small print (the survey question and notes in 5 point), and
    whatever lies between is the chart's own lettering, which is left out of the text. A chart with no
    small print runs to the next text in its column.
    """
    out, notes = [], {}
    for index in range(first, last + 1):
        items, foot = page_items(doc[index], index, index in small_text, box_gap)
        notes[index] = foot
        for item in items:
            # (a plan may give the start of a long heading, ending in an ellipsis)
            label = next((v for k, v in (numbers or {}).items() if item["text"] == k or (k.endswith("…") and item["text"].startswith(k[:-1]))), None)
            if item["kind"] == "h2" and label:
                headed(item, items, label, doc[index])
                continue
            if item["kind"] != "figtitle":
                continue
            if item["text"] in (numbers or {}):         # a chart whose title the original prints without its number
                item["text"] = f'{numbers[item["text"]]}. {item["text"]}'
            m = re.match(FIGURE, item["text"] + " ")
            if not m:
                item["kind"] = "h3"
                continue
            below = sorted((i for i in items if i["col"] == item["col"] and i["y0"] > item["y1"] - 1 and i["kind"] != "letter"), key=lambda i: i["y0"])
            run = []
            for i in below:
                if i["kind"] in ("title", "h1", "h2", "boxtitle", "figtitle", "foot", "quote") or i["box"] != item["box"]:
                    break
                run.append(i)
            first_small = next((k for k, i in enumerate(run) if i["kind"] == "small"), None)
            small = []
            if first_small is None:
                # The head and the row names of a table are set as large as the text: what follows a table's
                # title and does not read as a paragraph is part of it, in the other column too.
                table = m.group(1) == "Table"
                cells = lambda i: i["kind"] == "p" and i["box"] == item["box"] and (
                    (i["style"] == "**" and len(i["text"]) < 60) or (table and not (len(i["text"]) > 110 and re.search(r"[.:?]\S*$", i["text"]))))
                while below and cells(below[0]):
                    below.pop(0)["kind"] = "used"
                floor = (below[0]["y0"] if below else BOTTOM - 4) - 2
                if table and item["col"] == 0:
                    for i in items:
                        if i["col"] == 1 and item["y1"] < i["y0"] < floor and cells(i) and len(i["text"]) < 110:
                            i["kind"] = "used"
            else:
                floor = run[first_small]["y0"] - 2
                for i in run[:first_small]:
                    # type as large as the text, inside the chart; a full paragraph is text set on top of a chart that fills the page (a map)
                    if not (i["kind"] == "p" and len(i["text"]) > 200 and re.search(r"[.:?]\S*$", i["text"])):
                        i["kind"] = "used"
                for i in run[first_small:]:
                    if i["kind"] != "small":
                        break
                    small.append(i["text"])
                    i["kind"] = "used"
            item.update(kind="chart", label=m.group(0).strip().rstrip(".:"), title=item["text"][m.end():].strip(), small=small)
            item["clip"], item["blank"] = extent(doc[index], item, items, floor)
        out += [i for i in items if i["kind"] not in ("letter", "used", "foot")]
    return out, notes


if __name__ == "__main__":
    document = pymupdf.open(PDFS / sys.argv[1])
    got, feet = read(document, int(sys.argv[2]), int(sys.argv[3]))
    for it in got:
        extra = f' {it["clip"]} small={it["small"]}' if it["kind"] == "chart" else ""
        print(f'{it["page"]:>3} {it["col"]} {it["kind"]:<8}{"#" if it["box"] else " "}{(it["mark"] or ""):<4}{round(it["x0"]):>4} {round(it["y0"]):>4}  {it["text"][:130]}{extra[:200]}')
    for page, marks in feet.items():
        for mark, text in marks.items():
            print(f"{page:>3} [{mark}] {text[:120]}")
