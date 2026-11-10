"""Read the text of a core report of the 2021 poll from its PDF.

The four core reports of the 2021 poll (A Changed World?, A Resilient World?,
A Digital World, Safe at Work?) share one design: A4 pages, text mostly in one
column in Source Sans Pro Light 10, headings in pink, charts under a white-on-pink
"Chart 1.1" label. stream() turns pages into a list of typed items in reading
order; assemble_2021.py arranges them as a content file.

    python reports/book/redesign/core_2021.py core_a_changed_world.pdf 10 13

prints the items of pages 10 to 13 (counted from 0), for checking by eye.
"""

import re
import sys
from pathlib import Path

import pymupdf

PDFS = Path(__file__).resolve().parent.parent / ".cache" / "pdfs"
PINK = (0xEA1B78, 0xE4116F, 0xE4066F, 0xE5006E)


def kind_of(span):
    """What a block is, from the type of its longest span."""
    font, size, colour = span["font"], round(span["size"], 1), span["color"]
    if font.startswith("FinalSix"):
        if size >= 25:
            return "part"           # "Chapter 1", "Preface", "Appendix 1: ..."
        if size >= 18:
            return "title"          # a chapter's title; "Introduction"; "Concluding remarks"
        if 8.5 <= size <= 9.5:
            return "label" if colour == 0xFFFFFF else "caption"
        return None
    if not font.startswith("SourceSansPro"):
        return None
    semi = "SemiBold" in font or "Semibold" in font
    if semi and 13.5 <= size <= 14.5:
        return "h1"
    if semi and 11.5 <= size <= 12.5:
        return "h2"
    if font.endswith(("-Italic", "-It")) and (size >= 15 or (10.2 <= size <= 11 and colour in PINK)):
        return "quote"              # a sentence of the text, repeated large beside a picture
    if 9.8 <= size <= 10.2 and colour == 0 and "Bold" not in font and not semi:
        return "p"
    if semi and 9.8 <= size <= 10.2 and colour == 0:
        return "sub"                # a second line of title over a chart or table
    if semi and 9.8 <= size <= 10.6 and colour in PINK:
        return "name"               # the name under the portrait in the preface
    if font == "SourceSansPro-Regular" and 7.9 <= size <= 8.1:
        return "small"              # the small print under a chart
    if "Light" in font and 6.9 <= size <= 7.6:
        return "fn"
    return None


def rich(block, body=10.0):
    """A block's text with **bold**, *italic* and [^n] footnote marks, lines joined into one."""
    runs = []                       # [style, text]
    for line in block["lines"]:
        if runs and runs[-1][1]:
            # lines are joined with a space, except after a slash or a hyphen that ends the line
            end = runs[-1][1].rstrip()
            runs[-1][1] = end if end.endswith("/") or re.search(r"\w-$", end) else end + " "
        for span in line["spans"]:
            text = span["text"].replace("\t", " ").replace("­", "").replace("\xa0", " ")
            font = span["font"]
            if body and span["color"] == 0xFFFFFF:
                continue                # white type left behind in a paragraph: it does not print
            if span["size"] < body * 0.75 and re.fullmatch(r"\s*[\d,\s]+\s*", text) and text.strip():
                style, text = "", "".join(f"[^{n}]" for n in re.findall(r"\d+", text))
            elif "Itali" in font or font.endswith("-It"):
                style = "*"
            elif "Light" not in font and abs(span["size"] - body) < 0.6:
                style = "**"
            else:
                style = ""
            if runs and runs[-1][0] == style:
                runs[-1][1] += text
            else:
                runs.append([style, text])
    # A whole block in one style is the block's own style (a heading, a question), not emphasis.
    styles = {style for style, text in runs if text.strip() and not text.startswith("[^")}
    out = ""
    for style, text in runs:
        if not style or len(styles) == 1 or not text.strip():
            out += text
        else:
            lead, core, tail = re.match(r"(\s*)(.*?)(\s*)$", text, flags=re.S).groups()
            out += f"{lead}{style}{core}{style}{tail}"
    out = out.replace("ﬀ", "ff").replace("ﬁ", "fi").replace("ﬂ", "fl")
    out = re.sub(r"\*\* \*\*|\*\*\*\*", " ", out)
    return re.sub(r"\s+", " ", out).strip(), (styles.pop() if len(styles) == 1 else "")


def lines_of(block):
    return [re.sub(r"\s+", " ", "".join(s["text"] for s in line["spans"]).replace("\t", " ")).strip() for line in block["lines"]]


def frames(page, labels):
    """The charts of a page as (x0, top, x1, bottom).

    Each chart sits between two pink rules: one at its label, one under it. A chart whose
    closing rule is on the next page runs to the foot of this one.
    """
    rules = []
    for g in page.get_drawings():
        r, c = g["rect"], g.get("color")
        if r.width > 300 and r.height < 3 and c and abs(c[0] - 0.918) < 0.02 and abs(c[1] - 0.104) < 0.03 and 60 < r.y0 < 800:
            rules.append((r.y0, r.x0, r.x1))
    rules.sort()
    tops = [rule for rule in rules if any(abs(rule[0] - y - 12) < 14 and rule[1] - 10 < x < rule[2] for x, y in labels)]
    out = []
    for y0, x0, x1 in tops:
        below = [rule[0] for rule in rules if rule[0] > y0 + 5]
        out.append((x0, y0 - 16, x1, below[0] if below and below[0] not in [t[0] for t in tops] else (below[0] - 20 if below else 800)))
    return out


def page_items(page, index, top=55, bottom=800):
    found, notes = [], []
    charts = None
    for block in page.get_text("dict")["blocks"]:
        spans = [s for line in block.get("lines", []) for s in line["spans"] if s["text"].strip()]
        if not spans:
            continue
        boxes = [line["bbox"] for line in block["lines"] if "".join(s["text"] for s in line["spans"]).strip()]
        x0, y0, x1, y1 = min(b[0] for b in boxes), min(b[1] for b in boxes), max(b[2] for b in boxes), max(b[3] for b in boxes)
        if y0 < top or y0 > bottom:
            continue
        # The longest span decides, except that a paragraph may open with a long bold run.
        main = max(spans, key=lambda s: len(s["text"]))
        kind = kind_of(main)
        if kind is None:
            continue
        if kind == "sub":
            # a paragraph that is mostly bold is still a paragraph
            light = [s for s in spans if "Light" in s["font"] and 9.8 <= s["size"] <= 10.2]
            if sum(len(s["text"]) for s in light) >= 20:
                kind, main = "p", max(light, key=lambda s: len(s["text"]))
        item = dict(kind=kind, page=index, x0=x0, y0=y0, x1=x1, y1=y1, wide=x1 - x0 > 300)
        if kind == "small":
            item["lines"] = [line for line in lines_of(block) if line]
            item["text"] = " ".join(item["lines"])
        elif kind == "fn":
            item["text"] = rich(block, body=main["size"])[0].replace("*", "")
        else:
            item["text"], item["style"] = rich(block, body=main["size"] if kind == "p" else 0)
        if not item["text"]:
            continue
        (notes if kind == "fn" else found).append(item)

    charts = frames(page, [(b["x0"], b["y0"]) for b in found if b["kind"] == "label"])
    for b in found:
        b["frame"] = next((f for f in charts if f[1] <= b["y0"] <= f[3] and f[0] - 10 < b["x0"] < f[2]), None)

    # Reading order: a full-width block ends the band of columns above it.
    found.sort(key=lambda b: b["y0"])
    ordered, band = [], []

    def flush():
        columns = []
        for b in sorted(band, key=lambda b: b["x0"]):
            if columns and b["x0"] - columns[-1][0]["x0"] < 120:
                columns[-1].append(b)
            else:
                columns.append([b])
        for column in columns:
            ordered.extend(sorted(column, key=lambda b: b["y0"]))
        band.clear()

    for b in found:
        if b["wide"]:
            flush()
            ordered.append(b)
        else:
            band.append(b)
    flush()
    notes.sort(key=lambda b: (b["x0"] > 300, b["y0"]))
    return ordered, notes


def stream(doc, first, last):
    """(items, footnotes) of pages first to last, counted from 0."""
    items, raw = [], []
    for index in range(first, last + 1):
        ordered, notes = page_items(doc[index], index)
        items += ordered
        raw += notes
    footnotes, expected = {}, None
    for note in raw:
        text = note["text"]
        if expected is None:
            expected = int(re.match(r"\d+", text).group())
        while text:
            # A block may open with the end of the previous note, and may hold several notes.
            start = re.search(rf"(?:^|(?<=\s)){expected} +(?=\S)", text)
            carried = text[:start.start()] if start else text
            if carried.strip() and footnotes:
                footnotes[expected - 1] += " " + carried.strip()
            if not start:
                break
            text = text[start.end():]
            following = re.search(rf"(?<=\s){expected + 1} +(?=[A-Z‘“\"'(])", text)
            footnotes[expected] = (text[:following.start()] if following else text).strip()
            text = text[following.start():] if following else ""
            expected += 1
    return items, footnotes

if __name__ == "__main__":
    document = pymupdf.open(PDFS / sys.argv[1])
    got, fns = stream(document, int(sys.argv[2]), int(sys.argv[3]))
    for it in got:
        print(f'{it["page"]:>3} {it["kind"]:<8}{"#" if it["frame"] else " "} {round(it["x0"]):>4} {round(it["y0"]):>4}  {it["text"][:150]}')
    for n, text in fns.items():
        print(f"[^{n}] {text[:150]}")
