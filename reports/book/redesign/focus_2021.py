"""Assemble the content files of the Focus On reports of the 2021 poll.

    python reports/book/redesign/focus_2021.py 2021_focus_critical_infrastructure

The three Focus On reports re-set here share one design: pages of 1920 by 1280 points,
text in two columns in Source Sans Pro Regular 21, pink headings, charts under a
white-on-pink "Chart 1" label, a cover that carries the summary ("What the data tells
us", "What we can do about it"), an introduction beside a headline figure, and numbered
references on the last page. They have no chapters.

read() turns the pages into typed items in reading order; assemble() arranges them as
content/<report>.md: the summary as the front section, the introduction on the opening
page with the headline figure, the rest as one run of text under the original headings,
the references as numbered notes and the "About" texts as the back section. Every chart
gets its specification from PLANS and its title, question text and source line from the PDF.
"""

import json
import re
import sys
from pathlib import Path

import pymupdf

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from assemble_2019 import open_ended  # noqa: E402
from assemble_2021 import SCATTER, Ids  # noqa: E402

PINK = (0xE4066F, 0xE5006E, 0xE21470, 0xE1116F)
SUBSCRIPT = str.maketrans("0123456789", "₀₁₂₃₄₅₆₇₈₉")
TOP, BOTTOM = 45, 1228          # page furniture sits above and below these lines
PLANS = {}


def plan(key, **fields):
    PLANS[key] = fields


# ---------------------------------------------------------------- reading the PDF

def kind_of(span):
    """What a block is, from the type of its longest span."""
    font, size, colour = span["font"], span["size"], span["color"]
    if font.startswith("FinalSix"):
        weight = font.split("-")[-1]
        if weight == "Bold" and colour in PINK and 28 <= size <= 50:
            return "h"
        if weight == "Bold" and 17.5 <= size <= 18.5 and colour == 0:
            return "title"
        if weight in ("Medium", "Black", "Heavy") and 43.5 <= size <= 44.5:
            return "quote"              # a quotation set large in the text column
        if 70 <= size <= 76:
            return "statement"          # a sentence that has a page to itself
        return None
    if font.startswith("SourceSansPro"):
        if 20.5 <= size <= 21.5 or 23.5 <= size <= 24.5:
            return "p"
        if "Italic" in font and 13.5 <= size <= 14.5:
            return "small"              # the question text under a chart
        if font.endswith("-Regular") and 13.5 <= size <= 14.5 and colour == 0:
            return "foot"               # a note at the foot of a column, marked with an asterisk
    return None


def rich(lines, body, bold=lambda span: "Bold" in span["font"]):
    """Lines of spans as text with **bold**, *italic*, [^n] reference marks and subscripts."""
    runs = []
    for line in lines:
        if runs and runs[-1][1]:
            end = runs[-1][1].rstrip()
            runs[-1][1] = end if end.endswith("/") or re.search(r"\w-$", end) else end + " "
        base = max((s["origin"][1] for s in line["spans"] if s["size"] > body * 0.75), default=None)
        for span in line["spans"]:
            text = span["text"].replace("\t", " ").replace("\xad", "").replace("\xa0", " ")
            if span["size"] < body * 0.75 and re.fullmatch(r"\s*[\d,\s]+\s*", text) and text.strip():
                if base is not None and span["origin"][1] > base + 1:
                    style, text = None, text.strip().translate(SUBSCRIPT)                 # CO2
                else:
                    style, text = None, "".join(f"[^{n}]" for n in re.findall(r"\d+", text))
            elif "Itali" in span["font"]:
                style = "*"
            elif bold(span):
                style = "**"
            else:
                style = ""
            text = text.replace("*", "\\*")
            if style is None:               # a mark that belongs to the word before it
                if runs:
                    runs[-1][1] = runs[-1][1].rstrip() + text
                else:
                    runs.append(["", text])
            elif runs and runs[-1][0] == style:
                runs[-1][1] += text
            else:
                runs.append([style, text])
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
    out = re.sub(r"(?<![\w*\\])([A-Za-z])\*(?=\w)", r"*\1", out)          # a title in italics whose first letter the original left upright
    return re.sub(r"\s+", " ", out).strip()


def box_of(lines):
    boxes = [line["bbox"] for line in lines]
    return min(b[0] for b in boxes), min(b[1] for b in boxes), max(b[2] for b in boxes), max(b[3] for b in boxes)


def pieces(page):
    """The page's blocks of text. The PDF sometimes holds neighbours from two columns as one block: those are split."""
    for block in page.get_text("dict")["blocks"]:
        run = []
        for line in block.get("lines", []):
            if not "".join(s["text"] for s in line["spans"]).strip():
                continue
            if run and (abs(line["bbox"][0] - run[-1]["bbox"][0]) > 150 or line["bbox"][1] < run[-1]["bbox"][1] - 5):
                yield run
                run = []
            run.append(line)
        if run:
            yield run


def page_items(page, index):
    """The items of one page in reading order: columns from left to right, each from the top."""
    found, titles, groups, inserts, cites = [], [], {}, [], []
    for lines in pieces(page):
        spans = [s for line in lines for s in line["spans"] if s["text"].strip()]
        x0, y0, x1, y1 = box_of(lines)
        if y0 < TOP or y0 > BOTTOM:
            continue
        item = dict(page=index, x0=x0, y0=y0, x1=x1, y1=y1)
        label = next((s for s in spans if s["font"] == "FinalSix-Bold" and 21 <= s["size"] <= 23 and re.match(r"(Chart|Table) \d+", s["text"].strip())), None)
        main = max(spans, key=lambda s: len(s["text"]))
        kind = "label" if label else kind_of(main)
        if kind == "label":
            rest = [dict(line, spans=[s for s in line["spans"] if s is not label]) for line in lines]
            item.update(kind="label", text=label["text"].strip(), title=rich([line for line in rest if line["spans"]], 18, bold=lambda s: False))
        elif kind == "title":
            titles.append(dict(item, text=rich(lines, 18, bold=lambda s: False)))
            continue
        elif kind in ("quote", "statement"):
            groups.setdefault(kind, []).extend(lines)
            continue
        elif kind == "p":
            item.update(kind="p", text=rich(lines, main["size"], bold=lambda s: "Bold" in s["font"]), white=main["color"] == 0xFFFFFF)
        elif kind == "h":
            item.update(kind="h", text=rich(lines, main["size"], bold=lambda s: False))
            if len(re.sub(r"[^A-Za-z]", "", item["text"])) < 4:
                continue                # a figure printed on a map
        elif kind == "small":
            # the mark of a reference is in smaller type at the end of a line
            texts = []
            for line in lines:
                text = "".join(f"[^{s['text'].strip()}]" if s["size"] < 10 and s["text"].strip().isdigit() else s["text"] for s in line["spans"])
                texts.append(re.sub(r"\s+", " ", text.replace("\t", " ")).strip())
            item.update(kind="small", lines=texts)
        elif kind == "foot":
            text = rich(lines, main["size"], bold=lambda s: False)
            if not text.startswith("\\*"):
                continue
            item.update(kind="foot", text=text)
        else:
            if main["font"] == "SourceSansPro-Regular" and round(main["size"]) == 18 and spans[0]["text"].strip().startswith("..."):
                inserts.append(dict(item, text=rich(lines, 18)))            # the words inside the brackets of a quotation
            elif main["font"] == "SourceSansPro-Italic" and round(main["size"]) == 16:
                cites.append(dict(item, text=rich(lines, 16, bold=lambda s: False).replace("*", "")))
            continue
        found.append(item)

    # A chart's title is beside its label: in the label's own block, in the block next to it, or in both.
    for item in found:
        if item["kind"] == "label":
            near = [t for t in titles if item["x0"] < t["x0"] < item["x0"] + 160 and abs((t["y0"] + t["y1"]) / 2 - (item["y0"] + item["y1"]) / 2) < 45]
            item["title"] = " ".join([item["title"]] + [t["text"] for t in sorted(near, key=lambda t: t["y0"])]).strip()
            assert item["title"], (index, item["text"], [t["text"] for t in titles])

    # A quotation or a statement set large is one item, whatever blocks the PDF holds it in.
    for kind, lines in groups.items():
        lines.sort(key=lambda line: (round(line["bbox"][1] / 8), line["bbox"][0]))
        x0, y0, x1, y1 = box_of(lines)
        text = rich(lines, lines[0]["spans"][0]["size"], bold=lambda s: s["font"].split("-")[-1] in ("Black", "Bold") or (s["color"] in PINK and len(s["text"].strip()) > 1))
        item = dict(kind=kind, page=index, x0=x0, y0=y0, x1=x1, y1=y1, text=text)
        if kind == "quote":
            for insert in inserts:
                assert re.search(r"\[\s+\]", item["text"]), item["text"]
                item["text"] = re.sub(r"\[\s+\]", "[" + insert["text"] + "]", item["text"])
            below = [c for c in cites if 0 <= c["y0"] - y1 < 40 and x0 - 20 < c["x0"] < x1]
            if below:
                item["cite"] = below[0]["text"]
        found.append(item)

    # Reading order: a block across the page ends the columns above it.
    found.sort(key=lambda b: b["y0"])
    flow = [b for b in found if b["kind"] != "small"]
    ordered, band = [], []

    def flush():
        columns = []
        for b in sorted(band, key=lambda b: b["x0"]):
            if columns and b["x0"] - columns[-1][0]["x0"] < 250:
                columns[-1].append(b)
            else:
                columns.append([b])
        columns = [sorted(column, key=lambda b: b["y0"]) for column in columns]
        late = []
        for c, column in enumerate(columns[:-1]):
            # a heading at the foot of a column, below everything in the columns to its right, is read after them
            if column[-1]["kind"] == "h" and all(b["y1"] < column[-1]["y0"] for other in columns[c + 1:] for b in other):
                late.append(column.pop())
        for column in columns:
            ordered.extend(column)
        ordered.extend(late)
        band.clear()

    for b in flow:
        if b["kind"] in ("p", "h") and b["x1"] - b["x0"] > 1000:
            flush()
            ordered.append(b)
        else:
            band.append(b)
    flush()

    # The question text goes to the chart it stands nearest to, among the charts that start above it.
    labels = [b for b in ordered if b["kind"] == "label"]
    for small in (b for b in found if b["kind"] == "small"):
        if not labels:
            continue
        above = [l for l in labels if l["y0"] < small["y0"]] or labels
        home = min(above, key=lambda l: (abs(l["x0"] - small["x0"]) > 400, small["y0"] - l["y0"]))
        home.setdefault("small", []).extend(small["lines"])
    return ordered


def references(page):
    """(numbered references, the "About" texts) of the last page."""
    notes, about, number = {}, [], None
    for lines in sorted(pieces(page), key=lambda lines: (lines[0]["bbox"][0] > 900, lines[0]["bbox"][1])):
        block = {"bbox": box_of(lines)}
        if not TOP < block["bbox"][1] < BOTTOM:
            continue
        main = max((s for line in lines for s in line["spans"]), key=lambda s: len(s["text"]))
        if main["font"].startswith("FinalSix"):
            continue
        text = rich(lines, main["size"], bold=lambda s: "SemiBold" in s["font"])
        if "SemiBold" in main["font"] and "**" not in text:
            text = f"**{text}**"
        if block["bbox"][0] < 900:
            start = re.match(r"(\d+) +(?=\S)", text)
            if start:
                number = int(start.group(1))
                notes[number] = text[start.end():]
            else:
                notes[number] += " " + text
        else:
            about.append(text)
    return notes, about


def read(doc):
    items = []
    for index in range(len(doc) - 1):
        items += page_items(doc[index], index)
    return items


# ---------------------------------------------------------------- from items to a content file

def small_print(lines):
    """(question text, source line) of the small print under a chart."""
    text = [line for line in lines if not re.fullmatch(r"Survey questions?:?", line)]
    source = [line for line in text if re.match(r"Additional data|Locations extracted", line)]
    return " ".join(line for line in text if line not in source), " ".join(source)


def blocks_of(items, charts):
    out = []
    for item in items:
        kind = item["kind"]
        if kind == "h":
            out.append("## " + item["text"])
        elif kind == "label":
            m = re.fullmatch(r"(Chart|Table) (\d+)", item["text"])
            block = {"id": ("T" if m.group(1) == "Table" else "") + m.group(2), "number": m.group(2), "as": m.group(1), "title": item["title"]}
            question, source = small_print(item.get("small", []))
            if question:
                block["question"] = question
            if source:
                block["note"] = source
            spec = dict(charts[block["id"]])
            if spec["kind"] == "original":
                spec["page"] = item["page"]
            for field in ("question", "note"):
                if field in spec and spec[field] is None:
                    block.pop(field, None)
                    del spec[field]
            if spec.get("note") and block.get("note"):
                spec["note"] = spec["note"] + " " + block["note"]
            block.update(spec)
            out.append(block)
        elif kind == "statement":
            out.append(">> " + item["text"])
        elif kind == "quote":
            out.append(">> " + item["text"])
            if item.get("cite"):
                out.append(">-- " + item["cite"])
        elif kind == "foot":
            out.append("^ " + item["text"])
        elif kind == "p":
            text = item["text"]
            if text.startswith("• "):
                out.append("- " + text[2:].strip())
                continue
            # A paragraph the original broke over a column, a page or a chart: put it back together.
            k = next((k for k in range(len(out) - 1, -1, -1) if isinstance(out[k], str) and not out[k].startswith((">", "^"))), None)
            if k is not None and not out[k].startswith(("#", "- ")) and open_ended(out[k]):
                out[k] += " " + text
                continue
            out.append(text)
    return out


def opening(blocks, room=800):
    """Split the introduction into what its opening page holds beside the headline figure, and the rest."""
    taken = 0
    for block in blocks:
        if not isinstance(block, str) or block.startswith(("#", ">")):
            break
        height = 26 * -(-len(block) // 100) + 26
        if height > room:
            break
        room -= height
        taken += 1
    return blocks[:taken], blocks[taken:]


def dump(blocks):
    return ["```chart\n" + json.dumps(b, ensure_ascii=False, indent=1) + "\n```" if isinstance(b, dict) else b for b in blocks]


def assemble(key):
    p = PLANS[key]
    ids = Ids(p["folder"])
    for spec in p["charts"].values():
        for part in spec.get("parts", [spec]):
            ids.check(part)
        if spec.get("marker"):
            assert spec["marker"][1] in ids.ids, spec["marker"]
    doc = pymupdf.open(HERE.parent / ".cache" / "pdfs" / p["pdf"])
    items = read(doc)
    notes, about = references(doc[len(doc) - 1])

    title = f"Focus On: {p['title']}"
    meta = dict(
        key=key, wave=2021, folder=p["folder"], pdf=p["pdf"], title="Focus On", subtitle=p["title"], running_title=title,
        series=f"Focus On report of the 2021 poll, first published {p['published']}",
        source=f"World Risk Poll 2021 {title} (Lloyd's Register Foundation, {p['published']})",
        copyright="Copyright © 2023 Lloyd's Register Foundation. All rights reserved.", running=f"Re-set in 2026 from the report of {p['published']}",
        cover_image=p["cover_image"], contents_first=True, plain_opener=True, contents_h2=True, references_title="References and endnotes",
        margins=[TOP, BOTTOM], edits=p["edits"])
    for extra in ("chart_note", "queries", "pending"):
        if p.get(extra):
            meta[extra] = p[extra]

    cover = [i for i in items if i["page"] == 0]
    intro = [i for i in items if i["page"] == 1]
    body = [i for i in items if i["page"] > 1]
    assert cover[0]["kind"] == "h" and intro[0]["kind"] == "h" and intro[0]["text"] == "Introduction", (cover[0], intro[0])
    out = [f"::front {cover[0]['text']}"] + blocks_of(cover[1:], p["charts"])
    first, rest = opening(blocks_of(intro[1:], p["charts"]))
    out += [f"::chapter Introduction | {p['big']} | {p['caption']}"] + first + ["::flow"] + rest
    main = blocks_of(body, p["charts"])
    # the introduction's last paragraph does not run on into the body
    out += main
    for name, names in p.get("rolls", {}).items():
        at = out.index("## " + name)
        out.insert(at + 1, "```roll\n" + json.dumps(names(doc), ensure_ascii=False) + "\n```")

    heads = {"aboutlloydsregisterfoundation": "::back About Lloyd’s Register Foundation", "aboutgallup": "## About Gallup"}
    for text in about:
        out.append(heads.get(re.sub(r"[^a-z]", "", text.lower()), text))

    seen = {b["id"] for b in out if isinstance(b, dict)}
    assert seen == set(p["charts"]), (sorted(seen), sorted(p["charts"]))
    text = "\n\n".join(dump(out))
    for old, new in p.get("replace", {}).items():
        assert text.count(old) == 1, (text.count(old), old)
        text = text.replace(old, new)
    text = "---\n" + json.dumps(meta, ensure_ascii=False, indent=1) + "\n---\n\n" + text
    text += "\n\n" + "\n\n".join(f"[^{n}]: {body}" for n, body in sorted(notes.items())) + "\n"
    for old, new in p.get("replace_notes", {}).items():
        assert text.count(old) >= 1, old
        text = text.replace(old, new)
    (HERE / "content" / f"{key}.md").write_text(text, encoding="utf-8")
    pictures = [b["id"] for b in out if isinstance(b, dict) and b["kind"] == "original"]
    print(f"{key}.md: {len(out)} blocks, {len(seen)} charts and tables ({len(pictures)} pictures of the original: {' '.join(pictures)}), {len(notes)} references")


# ---------------------------------------------------------------- the reports

EDITS = [
    "The summary on the original's cover (‘What the data tells us’, ‘What we can do about it’) is set as the first page after the contents.",
    "The headline figure beside the introduction is set on the introduction's opening page, with its caption.",
    "The original's headings are kept as they are. The original has no chapters, so the text runs on as it does there.",
    "The references and endnotes keep their numbers. Web addresses that the original broke across lines have been joined up.",
]
GOVERNMENT = dict(series=["Favour local government", "Favour national government"], colours=["fuchsia", "navy"])
PREPAREDNESS = "Mean perceived governmental preparedness"
CI_REGIONS = (("south_eastern_asia", "South-eastern Asia"), ("south_asia", "South Asia"), ("australia_nz", "Australia and New Zealand"), ("eastern_africa", "Eastern Africa"),
              ("northern_america", "Northern America"), ("central_asia", "Central Asia"), ("north_africa", "North Africa"), ("middle_east", "Middle East"), ("east_asia", "East Asia"),
              ("northern_western_europe", "Northern/Western Europe"), ("southern_europe", "Southern Europe"), ("southern_africa", "Southern Africa"),
              ("eastern_europe", "Eastern Europe"), ("central_western_africa", "Central/Western Africa"), ("latin_america_caribbean", "Latin America and Caribbean"))
SERVICES = (("electricity", "Electricity"), ("water", "Clean water"), ("food", "Food"), ("medicine", "Medicine/medical care"), ("telephone", "Telephone"))

plan(
    "2021_focus_critical_infrastructure",
    folder="WRP_2021/focus_on_critical_infrastructure", pdf="focus_on_critical_infrastructure.pdf",
    title="Critical infrastructure resilience and perceptions of disaster preparedness", published="October 2023", cover_image=[0, 1],
    big="3 in 4", caption="people who have experienced a disaster have also lost access to critical infrastructure for more than a day.",
    edits=EDITS + [
        "The quotation from Tanzania's National Disaster Management Strategy is set large in the text, where the original has it; the words the original highlights are in bold.",
        "Chart 3 and Table 1 head a column ‘Mean percieved governmental preparedness’ in the original; the spelling is corrected here.",
    ],
    queries=[
        "Chart 4 gives Northern/Western Europe a difference of −4, while Chart 3 prints 40% for local and 37% for national government, a difference of 3. Both are as printed.",
        "Table 1 ranks disaster experience ‘of 119 countries’; the lowest rank it prints is 118th.",
    ],
    charts={
        "1": dict(kind="vgrouped", subtitle="Percent who lost access to critical infrastructure", series=["Have experienced a disaster", "Have not experienced a disaster"], colours=["fuchsia", "navy"],
                  panels=[["", [[label, [f"C1_{k}_disaster", f"C1_{k}_no_disaster"]] for k, label in SERVICES]]]),
        "2": dict(kind="original", clip=[1000, 642, 1828, 1222], why="the original plots each region without printing its value"),
        "3": dict(kind="dumbbell", tall=True, series=[PREPAREDNESS, "Local government", "National government"], colours=["fuchsia", "navy"],
                  subtitle="Preparedness of local and national government to deal with a disaster",
                  note="Only in four regions did people think that their local government was better prepared than their national government.",
                  rows=[[label, [f"C3_{k}_mean", f"C3_{k}_local", f"C3_{k}_national"]] for k, label in CI_REGIONS]),
        "T1": dict(kind="matrix", columns=[PREPAREDNESS, "Percent experienced a disaster", "Disaster experience ranking (of 119 countries)"], unit=["%", "%", "th"], plain=[2],
                   rows=[[name, [f"T1_{iso}_{c}" for c in ("mean", "disaster", "rank")]] for iso, name in (
                       ("ARE", "United Arab Emirates"), ("BGD", "Bangladesh"), ("PHL", "Philippines"), ("IDN", "Indonesia"), ("SGP", "Singapore"))]
                   + [["", None]] + [[name, [f"T1_{iso}_{c}" for c in ("mean", "disaster", "rank")]] for iso, name in (
                       ("ROU", "Romania"), ("BOL", "Bolivia"), ("PRY", "Paraguay"), ("LBN", "Lebanon"), ("AFG", "Afghanistan"))]),
        "4": dict(kind="diverging", tall=True, extra=PREPAREDNESS, marker=["Global average +{C4_global}", "C4_global"], **GOVERNMENT,
                  subtitle="Percentage point difference in preparedness to deal with a disaster between local and national government",
                  rows=[[label, f"C4_{k}", f"C4_mean_{k}"] for k, label in CI_REGIONS]),
        "5": dict(kind="hbar", unit=" pts", decimals=1, subtitle="Percentage point difference in preparedness to deal with a disaster between local and national government, in favour of national government",
                  rows=[[label, f"C5_{k}"] for k, label in (("water", "Clean water"), ("food", "Food"), ("telephone", "Telephone"), ("medicine", "Medicine/medical care"), ("electricity", "Electricity"))]),
        "6": dict(kind="diverging", tall=True, marker=["Global average +{C6_global}", "C6_global"], **GOVERNMENT,
                  subtitle="Percentage point difference in preparedness to deal with a disaster between local and national government, amongst those who have experienced a disaster and lost access to critical infrastructure",
                  rows=[[label, f"C6_{k}"] for k, label in CI_REGIONS]),
        "7": dict(kind="diverging", extra=PREPAREDNESS, marker=["Regional average +{C7_regional}", "C7_regional"], **GOVERNMENT,
                  rows=[[name, f"C7_{iso}_gap", f"C7_{iso}_mean"] for iso, name in (("MOZ", "Mozambique"), ("TZA", "Tanzania"), ("UGA", "Uganda"), ("ZWE", "Zimbabwe"),
                                                                                  ("ZMB", "Zambia"), ("KEN", "Kenya"), ("MUS", "Mauritius"))]),
    },
)

LOGO = [1826, 1108, 1920, 1280]
FIELDS = "it is a map of the regions with the oil and gas {} marked on it, and their positions are not in the public files"

plan(
    "2021_focus_fossil_fuels",
    folder="WRP_2021/focus_on_fossil_fuels_and_climate_change", pdf="focus_on_fossil_fuels_and_climate_change.pdf",
    title="Fossil fuel dependency and perceptions of climate change", published="June 2023", cover_image=[0, 1],
    big="87%", caption="of people in Chile view climate change as a ‘very serious threat’ yet **<1%** view it as the biggest threat to them personally.",
    edits=EDITS + [
        "The sentence the original sets on a page of its own (‘In all countries where energy contributes more than 50% of all exports…’) is set large in the text, in its original place.",
        "The two notes marked with an asterisk are set under the paragraphs they belong to.",
        "Charts 1, 3 and 4 run across the whole page in the original, so each has a page of its own here, after the text that discusses it.",
    ],
    pending="The charts of this report plot values for every country that the original does not print (the poll's own figures, with emissions, energy and export "
            "figures from Our World in Data and the World Bank). They can be redrawn in the 2026 style once those country values are added to the public files.",
    replace_notes={"www.canada. ca/": "www.canada.ca/"},
    charts={
        "1": dict(kind="original", plate=True, clip=[45, 440, 1880, 1140], blank=[LOGO], why=SCATTER),
        "2": dict(kind="original", clip=[50, 324, 1000, 1158], why=SCATTER),
        "3": dict(kind="original", plate=True, clip=[45, 440, 1880, 1130], blank=[LOGO], why=SCATTER),
        "4": dict(kind="original", plate=True, clip=[45, 512, 1880, 1180], blank=[LOGO], why=SCATTER),
        "5": dict(kind="original", clip=[60, 490, 950, 1005], why=SCATTER),
        "6": dict(kind="original", clip=[50, 168, 1050, 1166], width=700, why=SCATTER),
        "7": dict(kind="original", clip=[560, 146, 1305, 1158], width=560, why=FIELDS.format("fields")),
        "8": dict(kind="original", clip=[40, 458, 1085, 1222], blank=[[100, 1156, 760, 1222]], why=FIELDS.format("facilities")),
    },
)

BORN = dict(series=["Native-born", "Foreign-born"], colours=["navy", "fuchsia"])
INCOME = dict(series=["Feel comfortable with current income", "Finding it difficult on current income"], colours=["fuchsia", "navy"])
THREE = (("northern_america", "Northern America"), ("australia_nz", "Australia & New Zealand"), ("northern_western_europe", "Northern/Western Europe"))
FOUR = (("native_comfortable", "Native-born, comfortable"), ("native_difficult", "Native-born, difficult"),
        ("foreign_comfortable", "Foreign-born, comfortable"), ("foreign_difficult", "Foreign-born, difficult"))
AVERAGES = "The original also draws dotted lines for four global averages (native-born and foreign-born, comfortable and difficult) without printing their values; they are not redrawn."


def by_income(prefix):
    """Charts 5 and 6: for each region, native-born and foreign-born workers by how they feel about their income."""
    return [[f"{region}: {born}", [f"{prefix}{k}_{b}_comfortable", f"{prefix}{k}_{b}_difficult"]]
            for k, region in THREE for b, born in (("native", "native-born"), ("foreign", "foreign-born"))]


def halves(prefix, ids):
    """Charts 7 and 9: experience (top) and telling someone (bottom), by country of birth and feeling about income."""
    def rows(part):
        return [[label, [fid if fid in ids else None for fid in (f"{prefix}{part}_{k}_yes", f"{prefix}{part}_{k}_no")]] for k, label in FOUR]
    return [dict(kind="stacked", gaps=True, series=["Have experienced", "No experience"], colours=["fuchsia", "navy"], rows=rows("exp")),
            dict(kind="stacked", gaps=True, series=["Told someone", "Didn’t tell anyone"], colours=["fuchsia", "navy"], rows=rows("told"))]


def ratification(doc):
    """The list of countries on the page of concluding remarks, each with its status by the colour of its name."""
    names, key = [], []
    for block in doc[12].get_text("dict")["blocks"]:
        for line in block.get("lines", []):
            for span in line["spans"]:
                text = span["text"].strip()
                if line["bbox"][1] < 765 or not text or round(span["size"]) != 17:
                    continue
                status = 0 if span["color"] in PINK else 1 if span["color"] == 0x00A69A else None
                (key if text.startswith("Ratified") else names).append((round(line["bbox"][0] / 20), line["bbox"][1], text, status))
    out = []
    for _, _, text, status in sorted(names):
        if text[0].islower():
            out[-1][0] += " " + text            # "Bosnia / and Herzegovina"
        else:
            out.append([text, status])
    key = [[text, "fuchsia" if status == 0 else "teal"] for _, _, text, status in sorted(key, key=lambda k: k[3])]
    assert len(key) == 2 and len(out) > 180, (key, len(out))
    return dict(key=key, names=out)


VH = "WRP_2021/focus_on_violence_and_harassment_income_migration"
VH_IDS = Ids(VH).ids

plan(
    "2021_focus_violence_and_harassment",
    folder=VH, pdf="focus_on_violence_and_harassment_income_migration.pdf",
    title="The impact of income and migration on violence and harassment at work", published="April 2023", cover_image=[0, 1],
    big="22%", caption="of workers have **experienced** violence and harassment at work. This rises to **28%** for **those working outside their country of birth.**",
    edits=EDITS + [
        "The sentence the original sets on a page of its own (‘In Northern America, foreign-born workers who are struggling financially…’) is set large in the text, in its original place.",
        "Chart 1 is a map of the regions in the original, shaded from low to high; the values printed on it are drawn here as bars, from the highest to the lowest.",
        "Chart 2 plots each region's two percentages as dots in the original, without printing their values. Drawn here are the differences it does print, on the side "
        "of the group that is higher, as the original's colours show. North Africa has no difference in the original.",
        "Charts 8 and 10 are pie charts in the original; their values are drawn here as bars.",
        "Charts 5 and 6: " + AVERAGES[0].lower() + AVERAGES[1:],
        "The list of countries under ‘Convention 190 Ratification Status’ keeps the original's order and its two colours.",
    ],
    rolls={"Convention 190 Ratification Status": ratification},
    charts={
        "1": dict(kind="hbar", row=48, rows=[[label, f"C1_{k}"] for k, label in (
            ("australia_nz", "Australia & New Zealand"), ("northern_america", "Northern America"), ("northern_western_europe", "Northern/Western Europe"),
            ("central_western_africa", "Central/Western Africa"), ("southern_europe", "Southern Europe"), ("eastern_africa", "Eastern Africa"),
            ("latin_america_caribbean", "Latin America & Caribbean"), ("east_asia", "East Asia"), ("eastern_europe", "Eastern Europe"), ("middle_east", "Middle East"),
            ("southern_africa", "Southern Africa"), ("south_asia", "South Asia"), ("north_africa", "North Africa"), ("south_eastern_asia", "South-eastern Asia"),
            ("central_asia", "Central Asia"))]),
        "2": dict(kind="diverging", tall=True, signless=True, series=["Native-born higher", "Foreign-born higher"], colours=["navy", "fuchsia"],
                  subtitle="Percentage point difference",
                  rows=[[label, f"C2_{k}", None, sign] for k, label, sign in (
                      ("global", "Global", 1), ("australia_nz", "Australia and New Zealand", -1), ("northern_america", "Northern America", -1),
                      ("northern_western_europe", "Northern/Western Europe", 1), ("central_western_africa", "Central/Western Africa", -1), ("southern_europe", "Southern Europe", 1),
                      ("eastern_africa", "Eastern Africa", 1), ("latin_america_caribbean", "Latin America & Caribbean", 1), ("east_asia", "East Asia", -1),
                      ("eastern_europe", "Eastern Europe", 1), ("middle_east", "Middle East", -1), ("southern_africa", "Southern Africa", 1), ("south_asia", "South Asia", 1),
                      ("south_eastern_asia", "South-eastern Asia", 1), ("central_asia", "Central Asia", 1))]),
        "3": dict(kind="stacked", gaps=True, series=["Told someone", "Didn’t tell anyone", "Don’t know/refused"], colours=["fuchsia", "navy", "grey"],
                  rows=[[f"{region}: {born}", [f"C3_{k}_{b}_told", f"C3_{k}_{b}_didnt", None]] for k, region in THREE for b, born in (("native", "native-born"), ("foreign", "foreign-born"))]),
        "4": dict(kind="vgrouped", panel_height=440, series=["Foreign-born", "Native-born"], colours=["fuchsia", "navy"],
                  panels=[[heading, [[region, [f"C4_{k}_foreign_{c}", f"C4_{k}_native_{c}"]] for k, region in THREE]]
                          for c, heading in (("not_know", "Did not know what to do."), ("procedures", "Procedures were unclear."))]),
        "5": dict(kind="grouped", rows=by_income("C5_"), note="This 37 percentage point difference was the largest seen in any region.", **INCOME),
        "6": dict(kind="grouped", rows=by_income("C6_"), note="High experience of violence and harassment at work associated with low reporting.", **INCOME),
        "7": dict(kind="parts", parts=halves("C7_", VH_IDS)),
        "8": dict(kind="parts", parts=[
            dict(kind="stacked", heading=heading, series=["Yes", "No"], colours=["fuchsia", "navy"],
                 rows=[[born, [f"C8_{c}_{b}_yes", f"C8_{c}_{b}_no"]] for b, born in (("native", "Native-born"), ("foreign", "Foreign-born"))])
            for c, heading in (("reputation", "Fear that telling someone would harm reputation."), ("waste", "Thought that telling someone was a waste of time."))]),
        "9": dict(kind="parts", parts=halves("C9_", VH_IDS)),
        "10": dict(kind="stacked", series=["Experienced three forms", "Experienced two forms", "Experienced one form", "No experience"], colours=["fuchsia", "teal", "navy", "grey"],
                   rows=[[label, [f"C10_{k}_{c}" for c in ("three", "two", "one", "none")]] for k, label in (
                       ("native", "Native-born"), ("foreign", "Foreign-born"), ("foreign_women", "Foreign-born, women"), ("foreign_men", "Foreign-born, men"))]),
    },
)

if __name__ == "__main__":
    assemble(sys.argv[1])
