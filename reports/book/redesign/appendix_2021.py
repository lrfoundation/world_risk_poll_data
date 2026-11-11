"""Read the appendices of a core report of the 2021 poll from its PDF, as content markup.

The appendices are the questionnaire (questions, the interviewer's instructions
and tables of answer codes), the list of regions, the references by chapter,
and in two reports a methodology with its own tables. The tables are drawn as
grids of pale rules under a pink band, so a table is read from its rules: the
rules give the rows and columns, and the type that falls in a cell is the
cell's text. Everything else is read by its type, as core_2021.py does.

    python reports/book/redesign/appendix_2021.py core_a_changed_world.pdf 51 57

prints the markup of pages 51 to 57 (counted from 0), for checking by eye.
assemble_2021.py adds it to the report's content file.
"""

import json
import re
import sys

import pymupdf

from core_2021 import PDFS, PINK, kind_of, rich

RULE = (0.966, 0.660, 0.770)        # the pale rules of a table (the reports differ a little)
BAND = (0.918, 0.104, 0.470)        # the band over a table's columns


def pink(colour):
    """The reports' pink, as the colour of type (an integer)."""
    return colour in PINK or (colour >> 16 > 0xD8 and (colour >> 8) & 0xFF < 0x30 and 0x58 < colour & 0xFF < 0x90)


def near(colour, target, by=0.05):
    return colour is not None and all(abs(a - b) < by for a, b in zip(colour, target))


def merge(values, by=1.5):
    """Sorted values with those closer than `by` to the one before them left out."""
    out = []
    for v in sorted(values):
        if not out or v - out[-1] > by:
            out.append(v)
    return out


def tables(page, rule=RULE, band=BAND):
    """The tables of a page: dict(x=[column edges], y=[row edges], head=(top, bottom) or None), from the drawn rules.

    rule, band: the colours of the rules and of the band over the columns (the 2019 volume draws both in blue).
    """
    across, bands = [], []
    for g in page.get_drawings():
        r = g["rect"]
        if near(g.get("color"), rule) and r.height < 1 and r.width > 8:
            across.append((r.y0, r.x0, r.x1))
        elif near(g.get("fill"), band) and r.width > 60 and 8 < r.height < 80 and r.y0 > 60:
            bands.append((r.y0, r.y1, r.x0, r.x1))
    across.sort()
    groups = []                     # runs of rules that follow one another closely and overlap sideways
    for y, x0, x1 in across:
        group = next((g for g in groups if y - g["y"][-1] < 90 and x0 <= g["x1"] + 3 and x1 >= g["x0"] - 3
                      and not any(g["y"][-1] + 2 < b[0] < y for b in bands)), None)
        if group is None:
            group = dict(y=[], xs=[], x0=x0, x1=x1)
            groups.append(group)
        group["y"].append(y)
        group["xs"] += [x0, x1]
        group["x0"], group["x1"] = min(group["x0"], x0), max(group["x1"], x1)
    out = []
    for group in groups:
        ys, xs = merge(group["y"]), merge(group["xs"], 4)
        over = next((b for b in bands if abs(b[1] - ys[0]) < 6 or (b[0] < ys[0] and ys[0] - b[1] < 30 and b[2] < group["x1"] and b[3] > group["x0"])), None)
        head = None
        if over:
            head = (over[0], min(over[1], ys[0]) if over[1] - ys[0] < 6 else over[1])
            if ys[0] - over[1] > 6:
                ys.insert(0, over[1])
        else:
            # no band: the first row starts a line's height above the first rule
            ys.insert(0, ys[0] - (ys[1] - ys[0] if len(ys) > 1 else 20))
        out.append(dict(x=xs, y=ys, head=head, top=head[0] if head else ys[0], bottom=ys[-1], x0=xs[0], x1=xs[-1]))
    # a table whose last row has no rule under it: the row is as deep as the one above
    lines = [l["bbox"] for b in page.get_text("dict")["blocks"] for l in b.get("lines", []) if line_text(l)]
    for table in out:
        if len(table["y"]) < 3 or len(table["x"]) < 3:
            continue
        deep = table["y"][-1] - table["y"][-2]
        under = [b for b in lines if table["bottom"] < (b[1] + b[3]) / 2 < table["bottom"] + deep and table["x0"] < b[0] and b[2] < table["x1"] + 4]
        if len({sum(1 for edge in table["x"][1:-1] if b[0] + 2 > edge) for b in under}) >= 2 and deep < 40:      # type in two columns or more: a row
            table["y"].append(table["bottom"] + deep)
            table["bottom"] += deep
    return out


def line_text(line):
    return re.sub(r"\s+", " ", "".join(s["text"] for s in line["spans"]).replace("\t", " ").replace("\xa0", " ")).strip()


def grid(table, lines):
    """The table's cells from the lines of type that fall inside it."""
    def column(x):
        return max(0, sum(1 for edge in table["x"][1:-1] if x > edge))

    columns = len(table["x"]) - 1
    head = [[] for _ in range(columns)]
    rows = [[[] for _ in range(columns)] for _ in range(len(table["y"]) - 1)]
    for line in sorted(lines, key=lambda l: (l["bbox"][1], l["bbox"][0])):
        text = line_text(line)
        if not text:
            continue
        x, y = (line["bbox"][0] + line["bbox"][2]) / 2, (line["bbox"][1] + line["bbox"][3]) / 2
        # a cell's text is placed by where it starts when it is set from the left, by its middle when it is centred
        c = column(line["bbox"][0] + 2) if column(line["bbox"][0] + 2) == column(x) or line["bbox"][2] - line["bbox"][0] > 60 else column(x)
        if table["head"] and y < table["head"][1] + 1:
            head[c].append(text)
            continue
        r = max(0, min(len(rows) - 1, sum(1 for edge in table["y"][1:-1] if y > edge)))
        rows[r][c].append(text)
    join = lambda parts: re.sub(r"(\w)- (\w)", r"\1-\2", " ".join(parts).replace("\xad ", "").replace("\xad", ""))
    body = [[join(cell) for cell in row] for row in rows]
    body = [row for row in body if any(row)]
    spec = dict(columns=[join(cell) for cell in head] if table["head"] else None, rows=body)
    # columns that are empty throughout (a rule that only divides the band) are left out
    keep = [c for c in range(columns) if any(row[c] for row in body) or (spec["columns"] and spec["columns"][c])]
    spec["rows"] = [[row[c] for c in keep] for row in body]
    if spec["columns"]:
        spec["columns"] = [spec["columns"][c] for c in keep]
    return spec


def titled(spec):
    """A table whose band holds one title and whose first row names the columns: the title is the table's own."""
    heads = [c for c in (spec["columns"] or []) if c]
    if len(heads) == 1 and len(spec["columns"]) > 1 and spec["rows"] and not any(re.fullmatch(r"[\d.]+", cell) for cell in spec["rows"][0]) \
            and heads[0] != "CIRCLE ONE RESPONSE:":
        return dict(title=heads[0], columns=spec["rows"][0], rows=spec["rows"][1:])
    return spec


def bullet(text):
    """The original's bullets and dashes as list markup."""
    text = re.sub(r"^\*\*•\s*(.*?)\*\*", r"• **\1**", text)
    if re.match(r"(\*\*-\*\*|[-–])\s+\S", text):
        return "-- " + re.sub(r"^(\*\*-\*\*|[-–])\s+", "", text)
    if text.startswith("•"):
        return "- " + text[1:].strip()
    return text


def style_of(line):
    """The type a line is mostly set in: (name of the style, the span)."""
    spans = [s for s in line["spans"] if s["text"].strip()]
    main = max(spans, key=lambda s: len(s["text"].strip()))
    font, size, colour = main["font"], round(main["size"], 1), main["color"]
    italic = "Itali" in font or font.endswith("-It")
    if font.startswith("FinalSix") and size >= 25:
        return "part"
    if font.startswith("FinalSix"):
        return "skip"
    semi = "SemiBold" in font or "Semibold" in font or font.endswith("-Bold")
    if italic and pink(colour):
        return "instruction"
    if italic and 9.5 <= size <= 11:
        return "read"
    if semi and size >= 13.5:
        return "h1"
    if semi and size >= 11.5:
        return "h2"
    if semi and 9.5 <= size <= 11:
        return "question"
    if 9.5 <= size <= 11.2:
        return "p"
    if 6.5 <= size <= 8.2:
        return "fn"
    return "skip"


def in_order(items):
    """Items (x0, y, x1, markup) in reading order: a full-width item ends the band of columns above it."""
    ordered, band = [], []

    def flush():
        left = sorted((i for i in band if i[0] < 300), key=lambda i: i[1])
        right = sorted((i for i in band if i[0] >= 300), key=lambda i: i[1])
        ordered.extend(left + right)
        band.clear()

    for item in sorted(items, key=lambda i: i[1]):
        if item[0] < 300 and item[2] > 330:
            flush()
            ordered.append(item)
        else:
            band.append(item)
    flush()
    return [item[3] for item in ordered]


def page_blocks(page, pictures=(), top=55, bottom=800):
    """The page as markup blocks in reading order, and its footnotes. pictures: [(clip, chart specification)] kept as pictures of the original."""
    inside = lambda box, clip: clip[0] - 2 <= (box[0] + box[2]) / 2 <= clip[2] + 2 and clip[1] - 2 <= (box[1] + box[3]) / 2 <= clip[3] + 2
    found = [t for t in tables(page) if not any(inside((t["x0"], t["top"], t["x1"], t["bottom"]), clip) for clip, _ in pictures)]
    held = [[] for _ in found]
    out, notes = [], []
    for clip, spec in pictures:
        # a picture taller than it is wide is made narrow enough to stand in a column
        width = round(min(780, 760 * (clip[2] - clip[0]) / (clip[3] - clip[1])))
        out.append((clip[0], clip[1], clip[2], "```chart\n" + json.dumps(dict(spec, kind="original", page=page.number, clip=list(clip), width=width), ensure_ascii=False, indent=1) + "\n```"))
    for block in page.get_text("dict")["blocks"]:
        lines = [l for l in block.get("lines", []) if line_text(l) and top <= l["bbox"][1] <= bottom and not all(s["color"] == 0xFFFFFF and s["size"] < 7 for s in l["spans"])
                 and not any(inside(l["bbox"], clip) for clip, _ in pictures)]
        outside = []
        for line in lines:
            x, y = (line["bbox"][0] + line["bbox"][2]) / 2, (line["bbox"][1] + line["bbox"][3]) / 2
            k = next((k for k, t in enumerate(found) if t["top"] - 1 <= y <= t["bottom"] + 1 and t["x0"] - 4 <= x <= t["x1"] + 4), None)
            if k is None:
                outside.append(line)
            else:
                held[k].append(line)
        # runs of lines in one style are one piece of text
        run, kind = [], None

        def flush():
            if not run:
                return
            text, whole = rich(dict(lines=run), body=10.0 if kind == "p" else 0)
            y = run[0]["bbox"][1]
            x0, x1 = min(l["bbox"][0] for l in run), max(l["bbox"][2] for l in run)
            text = re.sub(r"(?<![\w*])(\w{1,2})\*(?=\w[^*]*\*)", r"*\1", text)       # italics that the PDF opens a letter late
            put = lambda markup: out.append((x0, y, x1, markup))
            if kind == "part":
                put("::back " + text)
            elif kind == "h1":
                put("## " + text)
            elif kind == "h2":
                put("### " + text)
            elif kind == "question":
                number = re.match(r"((?:\d+|[A-Z]{1,3}\d*)(?:\.\d+)*[A-Z]?\.?)\s+(.*)", text)
                put(f"?{number.group(1)} {number.group(2)}" if number and pink(run[0]["spans"][0]["color"]) else "**" + text + "**")
            elif kind == "instruction":
                put("?> " + text)
            elif kind == "p":
                put(bullet(f"*{text}*" if whole == "*" else text))
            elif kind == "fn":
                notes.append((y, text.replace("*", "")))

        for line in outside:
            now = style_of(line)
            first = next(s for s in line["spans"] if s["text"].strip())
            # a number in bold pink opens a question, whatever follows it on the line
            starts = pink(first["color"]) and "Bold" in first["font"] and 9.5 <= first["size"] <= 11 and re.match(r"\s*[\dA-Z][\w.]*\s*$", first["text"])
            if starts:
                now = "question"
            elif now == "read":
                now = "p"                                       # italics inside a paragraph
            elif now == "instruction" and kind == "question" and (line["bbox"][1] - run[-1]["bbox"][1] < 3 or style_of(run[-1]) == "instruction"):
                now = "question"                                # an instruction at the end of a question's line, or one that carries a number
            if now != kind or starts:
                flush()
                run, kind = [], now
            run.append(line)
        flush()
    for table, lines in zip(found, held):
        spec = grid(table, lines)
        if spec["rows"]:
            out.append((table["x0"], table["top"], table["x1"], "```grid\n" + json.dumps(titled(spec), ensure_ascii=False) + "\n```"))
    return in_order(out), [text for _, text in sorted(notes)]


def read(doc, first, last, pictures=None):
    """The markup blocks of pages first to last (from 0), and the footnote texts found on them.

    pictures: {page: [(clip, chart specification)]} for the tables and charts kept as pictures of the original.
    """
    blocks, notes = [], []
    for index in range(first, last + 1):
        got, small = page_blocks(doc[index], (pictures or {}).get(index, ()))
        # a paragraph that the page breaks is joined to its other half
        if blocks and got and re.match(r"[a-z]", got[0]) and re.search(r"[\w,\]]$", blocks[-1]) and not blocks[-1].startswith(("#", "?", ":", "`", "-")):
            blocks[-1] += " " + got.pop(0)
        # so is a table that runs on over the page under the same band
        if blocks and got and blocks[-1].startswith("```grid") and got[0].startswith("```grid"):
            a, b = (json.loads(t.split("\n", 1)[1].rsplit("```", 1)[0]) for t in (blocks[-1], got[0]))
            if not a.get("title") and not b.get("title") and a["columns"] and b["columns"] in (None, a["columns"]) and len(b["rows"][0]) == len(a["rows"][0]):
                a["rows"] += b["rows"]
                blocks[-1] = "```grid\n" + json.dumps(a, ensure_ascii=False) + "\n```"
                got.pop(0)
        blocks += got
        notes += small
    # a title set on two lines of different lengths comes as two blocks
    for k in range(len(blocks) - 1, 0, -1):
        if blocks[k].startswith("::back ") and blocks[k - 1].startswith("::back "):
            blocks[k - 1] += " " + blocks.pop(k)[7:]
    return blocks, notes


if __name__ == "__main__":
    document = pymupdf.open(PDFS / sys.argv[1])
    got, small = read(document, int(sys.argv[2]), int(sys.argv[3]))
    for block in got:
        print(block[:400] + ("…" if len(block) > 400 else ""), end="\n\n")
    for note in small:
        print("NOTE", note[:200])
