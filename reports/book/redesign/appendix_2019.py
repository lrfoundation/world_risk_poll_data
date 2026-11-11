"""Read the appendices of the 2019 volume from its PDF, as content markup.

The volume has three: the questionnaire, the references by chapter and the regions. They are set in one
column on upright pages, in a design of their own: titles in 28 point, headings in blue, questions in
bold with a blue number, tables of answer codes under a blue band, and two lists of regions set between
rules. The tables are read from their rules, as appendix_2021.py reads those of the 2021 reports;
everything else is read by its type.

    python reports/book/redesign/appendix_2019.py          # prints the markup, for checking by eye

assemble_2019.py adds it to the last of the four reports.
"""

import json
import re

import pymupdf

from appendix_2021 import grid, line_text, merge, tables
from core_2021 import PDFS, rich

PDF = "core_world_risk_poll_2019.pdf"
FIRST, LAST = 183, 213              # the pages of the appendices, counted from 0 (182 is their opening photograph)
BLUE = (0.30, 0.60, 0.83)           # the rules of a table and the band over its columns
TOP, BOTTOM = 70, 812               # the running head and the page number lie outside these


def blue(colour):
    """The blue of a question's number and of a heading, as the colour of type."""
    return colour >> 16 < 0x60 and 0x80 < (colour >> 8) & 0xFF < 0xA8 and colour & 0xFF > 0xC0


def style_of(line):
    """What a line is, from the type of its longest span."""
    spans = [s for s in line["spans"] if s["text"].strip()]
    main = max(spans, key=lambda s: len(s["text"].strip()))
    font, size = main["font"], round(main["size"], 1)
    if font.startswith("Calmetta"):
        return "part" if size >= 25 else "skip"
    if "Bold" in font and size >= 13.5:
        return "h1"
    if "Bold" in font and 11.5 <= size <= 12.5:
        return "question"
    if 11.5 <= size <= 12.5:
        return "said"               # type as large as a question, not bold: what the interviewer does
    if 9.5 <= size <= 10.5:
        return "p"
    if "SemiBold" in font and 8.5 <= size <= 9.5:
        return "name"               # the name of a region, beside its countries
    return "skip"


def join_urls(text):
    """Web addresses that the page breaks across lines, joined up again."""
    while True:
        joined = re.sub(r"(https?://\S*(?:[/_.=?&-]|%20)) (?=[\w%#])(?![A-Z][a-z]+ )", r"\1", text)
        if joined == text:
            # the last figures of an address that ends the reference, set on a line of their own
            return re.sub(r"(https?://\S*\d) (\d+)$", r"\1\2", text)
        text = joined


def pieces(line, edges):
    """A line of type as the pieces set apart on it: the cells of a table's row, which the PDF may hold as one line."""
    out = []
    for span in line["spans"]:
        if not span["text"].strip():
            continue
        last = out[-1] if out else None
        if last and span["bbox"][0] - last["bbox"][2] < 12 and not any(last["bbox"][2] - 1 < edge < span["bbox"][0] + 1 for edge in edges):
            last["spans"].append(span)
            last["bbox"] = (last["bbox"][0], min(last["bbox"][1], span["bbox"][1]), span["bbox"][2], max(last["bbox"][3], span["bbox"][3]))
        else:
            out.append(dict(spans=[span], bbox=tuple(span["bbox"])))
    return out


def tidy(spec):
    """A table as the original means it, where the rules alone do not say."""
    width = len(spec["rows"][0])
    columns = spec["columns"]
    # a row's code and its name are set as one line, across the rule between their columns
    if columns and width > 2 and not columns[0] and not columns[1]:
        for row in spec["rows"]:
            code = re.match(r"(L\d+[A-Z]) (.+)$", row[0])
            if code:
                row[0], row[1] = code.group(1), (code.group(2) + " " + row[1]).strip()
    # the last lines of a deep row, read as a row of their own
    rows = []
    for row in spec["rows"]:
        filled = [k for k, cell in enumerate(row) if cell]
        if rows and len(filled) == 1 and filled[0] > 0 and width > 2:
            rows[-1][filled[0]] = (rows[-1][filled[0]] + " " + row[filled[0]]).strip()
        else:
            rows.append(row)
    spec["rows"] = rows
    # a scale from 00 to 10: the words for its two ends stand over its first and last numbers
    if columns and "00" in rows[0] and "10" in rows[0] and "Very likely" in columns:
        columns[columns.index("Very likely")] = ""
        columns[rows[0].index("10")] = "Very likely"
    if width > 8:
        spec["tight"] = True
    return spec


def lists(page):
    """The page's tables, with a list of regions (rules across, a name and its countries) given its two columns."""
    out = []
    down = [g["rect"] for g in page.get_drawings() if g["rect"].width < 1.5 and g["rect"].height > 5 and g.get("color")
            and all(abs(a - b) < 0.05 for a, b in zip(g["color"], BLUE))]
    for table in tables(page, BLUE, BLUE):
        if len(table["y"]) <= 2 and len(table["x"]) <= 2:
            continue                # one rule on its own: the line to write an answer on
        # the last row has no rule under it: the rules between the columns run to its foot
        foot = max((r.y1 for r in down if table["x0"] - 2 <= r.x0 <= table["x1"] + 2 and table["top"] - 2 <= r.y0 <= table["bottom"] + 2), default=0)
        if foot > table["bottom"] + 5:
            table["y"].append(foot)
            table["bottom"] = foot
        between = [r.x0 for r in down if table["x0"] + 4 < r.x0 < table["x1"] - 4 and table["top"] - 2 <= r.y0 <= table["bottom"] + 2]
        if between:
            table["x"] = merge([table["x0"], table["x1"]] + between, 3)      # the rules between the columns say where the columns are
        if table["head"] is None:
            # no band: the first rule is the top of the first row
            table["y"] = table["y"][1:]
            table["top"] = table["y"][0]
        if len(table["x"]) == 2:
            inside = [l for b in page.get_text("dict")["blocks"] for l in b.get("lines", [])
                      if line_text(l) and table["top"] < l["bbox"][1] < table["bottom"] and style_of(l) == "p"]
            if inside:
                table["x"].insert(1, min(l["bbox"][0] for l in inside) - 3)
        out.append(table)
    return out


def page_blocks(page):
    """The page as markup blocks, from the top down."""
    found = lists(page)
    held = [[] for _ in found]
    out = []
    for block in page.get_text("dict")["blocks"]:
        outside = []
        for line in block.get("lines", []):
            if not line_text(line) or not TOP <= line["bbox"][1] <= BOTTOM or style_of(line) == "skip":
                continue
            x, y = (line["bbox"][0] + line["bbox"][2]) / 2, (line["bbox"][1] + line["bbox"][3]) / 2
            k = next((k for k, t in enumerate(found) if t["top"] - 1 <= y <= t["bottom"] + 1 and t["x0"] - 4 <= x <= t["x1"] + 4), None)
            if k is None:
                outside.append(line)
            else:
                held[k] += pieces(line, found[k]["x"])
        run, kind = [], None

        def flush():
            if not run:
                return
            text, _ = rich(dict(lines=run), body=10.0 if kind == "p" else 0)
            text = re.sub(r"(?<![\w*])(\w{1,2})\*(?=\w[^*]*\*)", r"*\1", text)       # italics that the PDF opens a letter late
            put = lambda markup: out.append((run[0]["bbox"][1], markup))
            if kind == "part":
                put("::back " + text)
            elif kind == "h1":
                put("## " + text)
            elif kind == "question":
                number = re.match(r"((?:\d+|[A-Z]{1,3}\d*)(?:\.\d+)*[A-Z]?\.?)\s+(.*)", text)
                put(f"?{number.group(1)} {number.group(2)}" if number and blue(run[0]["spans"][0]["color"]) else "**" + text + "**")
            elif kind == "said" or re.match(r"\((?:INTERVIEWER|Interviewer|If |Allow )|Write in:", text):
                put("?> " + text)
            else:
                put(join_urls(text))

        for line in outside:
            now = style_of(line)
            first = next(s for s in line["spans"] if s["text"].strip())
            starts = now == "question" and blue(first["color"]) and "Bold" in first["font"]
            apart = run and line["bbox"][1] - run[-1]["bbox"][3] > 0.45 * first["size"]
            if now != kind or starts or (apart and kind in ("p", "said")):
                flush()
                run, kind = [], now
            run.append(line)
        flush()
    for table, lines in zip(found, held):
        spec = grid(table, lines)
        if spec["rows"]:
            out.append((table["top"], "```grid\n" + json.dumps(tidy(spec), ensure_ascii=False) + "\n```"))
    return [markup for _, markup in sorted(out, key=lambda item: item[0])]


def read(doc, first=FIRST, last=LAST):
    """The markup blocks of the appendices."""
    blocks = []
    for index in range(first, last + 1):
        got = page_blocks(doc[index])
        # a paragraph or a reference that the page breaks is joined to its other half
        if blocks and got and re.match(r"[a-z(]", got[0]) and re.search(r"[\w,;/]$", blocks[-1]) and not blocks[-1].startswith(("#", "?", ":", "`", "*")):
            blocks[-1] = join_urls(blocks[-1] + " " + got.pop(0))
        # so is a table that runs on over the page
        if blocks and got and blocks[-1].startswith("```grid") and got[0].startswith("```grid"):
            a, b = (json.loads(t.split("\n", 1)[1].rsplit("```", 1)[0]) for t in (blocks[-1], got[0]))
            if a["columns"] and b["columns"] is None and len(b["rows"][0]) == len(a["rows"][0]):
                a["rows"] += b["rows"]
                blocks[-1] = "```grid\n" + json.dumps(a, ensure_ascii=False) + "\n```"
                got.pop(0)
        blocks += got
    return blocks


if __name__ == "__main__":
    for block in read(pymupdf.open(PDFS / PDF)):
        if block.startswith("```grid"):
            table = json.loads(block.split("\n", 1)[1].rsplit("```", 1)[0])
            print(f'   GRID {table["columns"]} {len(table["rows"])} rows: {str(table["rows"][0])[:70]} … {str(table["rows"][-1])[:60]}')
        else:
            print(block[:150] + ("…" if len(block) > 150 else ""))
