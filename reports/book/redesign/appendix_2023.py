"""The appendices of Resilience in a Changing World (2023 poll): its tables, read from the page or kept as pictures.

The text of the appendices is set in the report's own design, and core_2023 reads it like any other page.
What that reader leaves out is the tables, which this module adds:

- the tables of item scores, each on a grey ground: a title, the names of the columns and the rows, read from
  where the words sit;
- the table of index values by country, set in four runs over two pages and joined here into one;
- three tables with headings set on their side or cells of several paragraphs, and one that sets two tables
  side by side, which are placed as pictures of the original.

    python reports/book/redesign/appendix_2023.py          # what the tables read as
"""
import json
import re

import pymupdf

import core_2023

GREY = (0.92, 0.94, 0.95)                    # the ground of a table of item scores
FIRST, LAST = 35, 43                         # the appendix pages, counted from 0
PICTURES = {                                 # page: clips of the tables kept as pictures
    36: [(431, 217, 802, 551)],              # Appendix Table 1: headings on their side
    37: [(40, 75, 411, 489),                 # Appendix Table 2: headings on their side
         (431, 109, 802, 482)],              # Appendix Table 3: cells of several paragraphs and lists
    40: [(40, 59, 411, 222)],                # Cover Basic Needs: two tables side by side
}
VALUES = (42, 43)                            # the pages of the table of index values
VALUE_COLUMNS = ["Country", "Data Collection Date", "Margin of Error", "Resilience Index", "Individual sub-index",
                 "Household sub-index", "Community sub-index", "Societal sub-index"]
EDGES = (0, 60, 143, 172, 208, 244, 280, 320, 372)      # where the columns of one run start, from its left edge
RUNS = (40, 431)                             # the left edge of each run on a page


def lines(words, by=2.5):
    """Words as lines: those whose baselines are within `by` points of the line's first word."""
    out = []
    for word in sorted(words, key=lambda w: (w[3], w[0])):
        if out and word[3] - out[-1][0][3] <= by:
            out[-1].append(word)
        else:
            out.append([word])
    return [sorted(line, key=lambda w: w[0]) for line in out]


def phrases(line, gap=6):
    """(x, text) of the phrases of a line: words less than `gap` points apart."""
    out = []
    for word in line:
        if out and word[0] - out[-1][2] < gap:
            out[-1][1] += " " + word[4]
        else:
            out.append([word[0], word[4], word[2]])
        out[-1][2] = word[2]
    return [(x, text) for x, text, _ in out]


def scores(page):
    """(rect, table) of each table of item scores on a page, in the order they are set."""
    out = []
    grounds = [g["rect"] for g in page.get_drawings() if g.get("fill") and all(abs(a - b) < 0.02 for a, b in zip(g["fill"], GREY)) and g["rect"].height > 30]
    for rect in sorted(grounds, key=lambda r: (r.x0 > core_2023.GUTTER, r.y0)):
        if any(pymupdf.Rect(clip).intersects(rect) for clip in PICTURES.get(page.number, ())):
            continue
        title, head, *rows = lines(page.get_text("words", clip=rect))
        columns = phrases(head)
        starts = [x for x, _ in columns]
        table = dict(title=" ".join(w[4] for w in title), columns=[text for _, text in columns], rows=[])
        for row in rows:
            cells = [[] for _ in starts]
            for word in row:
                cells[max(k for k, x in enumerate(starts) if word[0] >= x - 3 or k == 0)].append(word[4])
            cells = [" ".join(cell) for cell in cells]
            assert cells[0], (table["title"], cells)            # every row opens with its value
            table["rows"].append(cells)
        out.append((rect, table))
    return out


def values(doc):
    """The table of index values by country: one row for each country, in the order of the four runs."""
    rows = []
    for index in VALUES:
        words = doc[index].get_text("words")
        for left in RUNS:
            edges = [left + e for e in EDGES]
            mine = [w for w in words if edges[0] - 2 <= w[0] < edges[-1] and w[3] < core_2023.BOTTOM]
            top = max(w[3] for w in mine if w[4] == "sub-index") + 1
            mine = [w for w in mine if w[1] > top]
            column = lambda w: max(k for k, x in enumerate(edges[:-1]) if w[0] >= x - 2 or k == 0)
            centre = lambda w: (w[1] + w[3]) / 2
            anchors = sorted((w for w in mine if column(w) == 2 and re.fullmatch(r"\d+\.\d", w[4])), key=centre)
            found = [[[] for _ in VALUE_COLUMNS] for _ in anchors]
            for word in mine:
                row = min(range(len(anchors)), key=lambda k: abs(centre(anchors[k]) - centre(word)))
                found[row][column(word)].append(word)
            for cells in found:
                rows.append([" ".join(w[4] for line in lines(cell) for w in line) for cell in cells])
    assert all(all(row) for row in rows), [row for row in rows if not all(row)]
    return dict(columns=VALUE_COLUMNS, rows=rows, tight=True, keep=[1])       # (a date stays on one line)


def grid(spec):
    return "```grid\n" + json.dumps(spec, ensure_ascii=False) + "\n```"


def picture(index, clip):
    w, h = clip[2] - clip[0], clip[3] - clip[1]
    spec = dict(kind="original", page=index, clip=list(clip), width=round(min(780, 760 * w / h)), bare=True)
    return "```chart\n" + json.dumps(spec, ensure_ascii=False, indent=1) + "\n```"


def raw(index, clip, block):
    """A block that is ready, as an item of the reader: it takes its place by its page, column and height."""
    return dict(kind="raw", text="", block=block, page=index, col=int(clip[0] > core_2023.GUTTER), x0=clip[0], y0=clip[1], y1=clip[3],
                clip=tuple(clip), box=None, mark=None, style="")


def leads(page):
    """The words that open a line in pink, as large as the text: the name of what the line defines."""
    out = []
    for block in page.get_text("dict")["blocks"]:
        for line in block.get("lines", []):
            run = ""
            for span in line["spans"]:
                colour = span["color"]
                if not (7.8 <= span["size"] <= 8.2 and colour >> 16 > 0xD0 and (colour >> 8) & 0xFF < 0x40):
                    break
                run += span["text"]
            if run.strip():
                out.append(re.sub(r"\s+", " ", run).strip())
    return out


def tables(doc):
    """The tables of the appendices as items."""
    out = []
    for index in range(FIRST, LAST + 1):
        out += [raw(index, clip, picture(index, clip)) for clip in PICTURES.get(index, ())]
        out += [raw(index, tuple(rect), grid(table)) for rect, table in scores(doc[index])]
    out.append(raw(VALUES[0], (40, 78, 411, 575), grid(values(doc))))
    return out


def place(items, doc):
    """The report's items with the tables of the appendices in their places.

    Text that the reader took from inside a table is dropped, and a line's opening words in pink are set bold.
    """
    extra = tables(doc)
    inside = lambda i, e: i["page"] == e["page"] and e["clip"][0] - 2 <= i["x0"] <= e["clip"][2] and e["clip"][1] - 2 <= (i["y0"] + i["y1"]) / 2 <= e["clip"][3] + 2
    out = [i for i in items if not any(inside(i, e) for e in extra)]
    for index in range(FIRST, LAST + 1):
        pink = leads(doc[index])
        for item in out:
            if item["page"] != index or item["kind"] != "p" or item["text"].startswith("*"):
                continue
            lead = next((text for text in pink if item["text"].startswith(text)), None)
            if lead and lead == item["text"]:
                item["style"] = "**"
            elif lead:
                item["text"] = f'**{lead}**{item["text"][len(lead):]}'
    order = lambda i: (i["page"], i["col"], i["y0"])
    for e in sorted(extra, key=order):
        at = next((n for n, i in enumerate(out) if FIRST <= i["page"] and order(i) > order(e)), len(out))
        out.insert(at, e)
    return out


if __name__ == "__main__":
    document = pymupdf.open(core_2023.PDFS / "core_resilience_in_a_changing_world.pdf")
    for number in range(FIRST, LAST + 1):
        for where, got in scores(document[number]):
            print(number, round(where.x0), round(where.y0), got["title"], got["columns"], len(got["rows"]), got["rows"][0], got["rows"][-1])
    table = values(document)
    print(len(table["rows"]), "countries")
    for line in table["rows"][:3] + [r for r in table["rows"] if len(r[0]) > 22] + table["rows"][-2:]:
        print("  ", line)
