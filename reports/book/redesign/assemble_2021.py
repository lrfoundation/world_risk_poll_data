"""Assemble the content files of the core reports of the 2021 poll.

    python reports/book/redesign/assemble_2021.py 2021_a_changed_world

Each of these reports stays one report, with its own preface, executive summary,
chapters and concluding remarks, in the original order. core_2021.py reads the
PDF; this script arranges what it finds as content/<report>.md, gives every
chart its specification from PLANS, and takes each chart's title, question text
and notes from the PDF. A chart with no specification yet is placed as a picture
of the original, so a draft is complete from the first run.
"""

import csv
import json
import re
import sys
from pathlib import Path

import pymupdf

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import core_2021  # noqa: E402
from assemble_2019 import REGIONS as REGIONS_2019, join_urls, open_ended  # noqa: E402

REGIONS = dict(REGIONS_2019, eastern_africa="Eastern Africa", latin_america="Latin America & Caribbean")
NOTE_STARTS = r"(\*|†|Don’t know|Don't know|Due to rounding|Values under|Note:|Total may|Percentages may)"
PREFIX = {"Chart": "", "Table": "T", "Map": "M"}


class Ids:
    """The finding IDs of one report, in the order of its CSV (the printed order of each chart)."""

    def __init__(self, folder):
        with open(HERE.parents[1] / folder / "published_figures.csv", encoding="utf-8") as f:
            self.ids = [row["finding_id"] for row in csv.DictReader(f)]

    def keys(self, prefix, suffix="", names=None):
        """The middle parts of the IDs that start with prefix and end with suffix, in CSV order."""
        out = []
        for fid in self.ids:
            if fid.startswith(prefix) and fid.endswith(suffix):
                key = fid[len(prefix):len(fid) - len(suffix)]
                if key not in out and (names is None or key in names):
                    out.append(key)
        return out

    def regions(self, prefix, suffixes):
        """Rows by region: [label, [prefix + region + _suffix, ...]], or [label, id] when suffixes is None."""
        keys = self.keys(prefix, "_" + suffixes[0] if suffixes else "", REGIONS)
        assert keys, prefix
        return [[REGIONS[k], [f"{prefix}{k}_{s}" for s in suffixes] if suffixes else f"{prefix}{k}"] for k in keys]

    def named(self, prefix, suffix, names):
        """[(label, key)] for the keys between prefix and suffix, in CSV order."""
        return [(names[k], k) for k in self.keys(prefix, suffix, names)]

    def check(self, spec):
        """Every finding ID a specification names must be in the CSV."""
        def walk(value):
            if isinstance(value, str) and re.fullmatch(r"[CTMX]\d\w*", value):
                assert value in self.ids, f"no finding {value}"
            elif isinstance(value, (list, tuple)):
                for v in value:
                    walk(v)
        for field in ("rows", "panels", "top", "bottom", "lists"):
            walk(spec.get(field, []))


SAFE3_KEYS = ("more", "same", "less")
SAFE4 = dict(series=["More safe", "About as safe", "Less safe", "Don’t know/refused"], colours=["green", "teal", "fuchsia", "grey"])
THREAT4 = dict(series=["Very serious threat", "Somewhat serious threat", "Not a threat at all", "Don’t know/refused"], colours=["fuchsia", "green", "teal", "grey"])
RISKS = {
    "road": "Road-related accidents/injuries", "crime": "Crime/violence", "health": "Personal health (non-Covid-19)", "covid": "Covid-19/coronavirus related",
    "none": "Nothing/no risks", "financial": "Financial: not having enough money", "economic": "Economic: unemployment, high prices", "other": "Other",
    "climate": "Climate change or severe weather", "work": "Work-related injuries", "war": "War/terrorism", "politics": "Politics/corruption",
    "non_road": "Non-road transportation injuries", "cooking": "Cooking or other household accidents/injuries", "mental": "Mental stress/exhaustion",
    "disasters": "Non-weather-related natural disasters", "drugs": "Drugs/alcohol/smoking", "hunger": "Hunger/lack of food", "pollution": "Pollution",
    "water": "Unsafe water supply", "internet": "Internet/technology-related risks", "food": "Unsafe or contaminated food", "drowning": "Drowning",
}
RISK_COLUMNS = dict(RISKS, health="Personal health, non-Covid-19")
T1_2 = ("covid", "health", "road", "crime", "financial", "economic", "cooking", "none")
MONEY = {"comfortable": "living comfortably", "getting_by": "getting by", "difficult": "finding it difficult", "very_difficult": "finding it very difficult"}
AGES = {"15_29": "Age 15-29", "30_49": "Age 30-49", "50_64": "Age 50-64", "65plus": "Age 65+"}
QUINTILES = {"bottom": "Bottom 20% income", "second": "Second 20%", "middle": "Middle 20%", "fourth": "Fourth 20%", "top": "Top 20% income"}
EDUCATION = {"primary": "Primary education or less (0-8 years)", "secondary": "Secondary education (9-15 years)", "post_secondary": "Post-secondary education (16 years or more)"}
SCATTER = "the original plots every country without printing its value"
COUNTRIES = {
    "AFG": "Afghanistan", "ALB": "Albania", "AUS": "Australia", "AUT": "Austria", "BGD": "Bangladesh", "BIH": "Bosnia and Herzegovina", "BOL": "Bolivia", "BRA": "Brazil",
    "CHE": "Switzerland", "CMR": "Cameroon", "COG": "Congo Brazzaville", "COL": "Colombia", "DEU": "Germany", "ECU": "Ecuador", "EGY": "Egypt", "EST": "Estonia",
    "GAB": "Gabon", "GIN": "Guinea", "HND": "Honduras", "IDN": "Indonesia", "IND": "India", "IRQ": "Iraq", "KEN": "Kenya", "KHM": "Cambodia", "LAO": "Laos",
    "LBN": "Lebanon", "MAR": "Morocco", "MEX": "Mexico", "MLI": "Mali", "MNG": "Mongolia", "MOZ": "Mozambique", "MYS": "Malaysia", "NGA": "Nigeria", "NIC": "Nicaragua",
    "NZL": "New Zealand", "PAN": "Panama", "PHL": "Philippines", "PRY": "Paraguay", "ROU": "Romania", "RUS": "Russia", "SEN": "Senegal", "SLE": "Sierra Leone",
    "TGO": "Togo", "THA": "Thailand", "UGA": "Uganda", "USA": "United States", "VEN": "Venezuela", "VNM": "Vietnam", "ZMB": "Zambia", "ZWE": "Zimbabwe",
}
INCOME4 = {"low_income": "Low-income countries", "lower_middle": "Lower-middle-income countries", "upper_middle": "Upper-middle-income countries", "high_income": "High-income countries"}
NEEDS = {"electricity": "Gone without electricity", "water": "Been without clean drinking water", "food": "Been unable to obtain food because of shortages",
         "medical": "Been unable to obtain medical assistance or medicine", "telephone": "Been unable to access a telephone"}
NOT_PRINTED = "Values the original does not print"

PLANS = {}


def urls(text):
    """Web addresses that the PDF broke across lines, joined up again."""
    text = join_urls(text)
    while True:
        joined = re.sub(r"(https?://\S*(?:[/_-]|%20)) (?=[\w%])", r"\1", text)
        if joined == text:
            return text
        text = joined


def plan(key, **fields):
    PLANS[key] = fields


# ---------------------------------------------------------------- from items to content blocks

def sections(items):
    out, current = [], None
    for item in items:
        text = item["text"]
        if item["kind"] == "part":
            chapter = re.fullmatch(r"Chapter (\d+)", text)
            after = any(s["kind"] == "chapter" for s in out)
            current = dict(kind="chapter" if chapter else "back" if after else "front", title=None if chapter else text, items=[])
            out.append(current)
        elif item["kind"] == "title":
            if current and current["kind"] == "chapter" and current["title"] is None:
                current["title"] = text
            else:
                seen_chapter = any(s["kind"] == "chapter" for s in out)
                current = dict(kind="back" if seen_chapter else "front", title=text, items=[])
                out.append(current)
        elif current is not None:
            current["items"].append(item)
    return out


def small_print(lines):
    """(question text, notes) of the small print under a chart."""
    question, notes = [], []
    for line in lines:
        (notes if notes or re.match(NOTE_STARTS, line) else question).append(line)
    text = re.sub(r"^Survey questions?: ?", "", " ".join(question))
    return text.strip(), " ".join(notes).strip()


def content(section, charts, doc, drop=(), heads=("# ", "## "), flat=False):
    """A section's items as content blocks (strings, and dicts for charts).

    heads are the marks for the section's levels of heading, largest first. A section whose
    largest heading is the 12-point one uses its bold lines of text as the level below.
    """
    out, chart, last_small, entry = [], None, None, None
    levels = ["h1", "h2", "sub"] if any(i["kind"] == "h1" for i in section["items"]) else ["h2", "sub"]
    if flat:
        levels = ["h2", "sub"]              # a report whose pink headings ("Conclusions") rank with its black ones
    for item in section["items"]:
        kind, text = item["kind"], item["text"]
        inside = chart is not None and item["frame"] is not None and item["page"] == chart["_page"]
        if text in drop:
            continue
        if kind == "label":
            m = re.fullmatch(r"(Chart|Table|Map) (\d+\.\d+)", text)
            assert m, text
            chart = dict(id=PREFIX[m.group(1)] + m.group(2), number=m.group(2), _page=item["page"], _box=[item["x0"], item["y0"], item["x1"], item["y1"], item["y1"]])
            chart["as"] = m.group(1)
            chart["_frame"] = item["frame"]
            last_small = None
            out.append(chart)
        elif kind == "caption":
            if chart is None or not inside:
                continue
            if "title" not in chart:
                chart["title"] = text
                chart["_box"][0] = min(chart["_box"][0], item["x0"])
            else:
                chart["subtitle"] = (chart.get("subtitle", "") + " " + text).strip()
            chart["_box"][3] = chart["_box"][4] = item["y1"] + 2
        elif kind == "sub" and inside:
            chart["subtitle"] = (chart.get("subtitle", "") + " " + text).strip()
            chart["_box"][3] = chart["_box"][4] = item["y1"] + 2
        elif kind == "small":
            if chart is None:
                continue
            below = last_small is not None and item["page"] == last_small["page"] and 0 <= item["y0"] - last_small["y1"] < 8
            if text.startswith("Survey question") or below or (inside and re.match(NOTE_STARTS, text)):
                question, notes = small_print(item["lines"])
                if not text.startswith("Survey question"):
                    question, notes = "", text
                if question:
                    chart["question"] = (chart.get("question", "") + " " + question).strip()
                if notes:
                    chart["note"] = (chart.get("note", "") + " " + notes).strip()
                if last_small is None:
                    chart["_bottom"] = item["y0"] - 3
                last_small = item
        elif kind in ("h1", "h2") or (kind == "sub" and not inside):
            level = levels.index(kind) if kind in levels else 0
            out.append(heads[level] + text if level < len(heads) else f"**{text}**")
        elif kind == "quote":
            if not inside:
                out.append("> " + text.strip("“”\" "))
        elif kind == "p":
            if inside:
                continue                         # the lettering of the chart, which the specification draws
            text = re.sub(r"^\*\*([•-])\*\* ?|^\*\*([•-]) ", lambda m: f"{m.group(1)} " if m.group(1) else f"{m.group(2)} **", text)
            bullet = re.match(r"[•-] ", text) or re.match(r"• ?", text)
            finding = re.match(r"(\d+)\) ?", text)
            style = item.get("style", "")
            if bullet or finding:
                body = text[(bullet or finding).end():]
                if style == "*":
                    body = f"*{body}*"
                elif style == "**" and finding:
                    body = f"**{body}**"
                # a dash marks a point under the bullet before it
                out.append(("-- " if text.startswith("-") else "- " if bullet else f"{finding.group(1)}. ") + body)
                entry = item
                continue
            # The rest of a list entry that the PDF holds as a block of its own: indented under the entry, on the next line.
            if (entry is not None and out and isinstance(out[-1], str) and out[-1].startswith("-") and item["page"] == entry["page"]
                    and item["x0"] > entry["x0"] + 5 and -2 <= item["y0"] - entry["y1"] < 8):
                out[-1] += " " + text
                entry = dict(entry, y1=item["y1"])
                continue
            # A paragraph the original broke over a page, a column or a chart: put it back together.
            k = next((k for k in range(len(out) - 1, -1, -1) if isinstance(out[k], str)), None)
            if k is not None and not out[k].startswith(("#", ">", "*")) and open_ended(out[k].rstrip("*")) and style != "*":
                # (a list item with no full stop is only continued by text that starts in lower case)
                if text[:1].islower() or (not out[k + 1:] and not re.match(r"- |\d+\. ", out[k])):
                    out[k] += " " + text
                    continue
            out.append(f"*{text}*" if style == "*" else text)
    # A chart with no specification yet is a picture of the original.
    for block in out:
        if isinstance(block, dict):
            box, page, frame = block.pop("_box"), block.pop("_page"), block.pop("_frame")
            bottom = block.pop("_bottom", frame[3] - 3)
            spec = charts.get(block["id"])
            if spec is None:
                spec = dict(kind="original", why="it has not been redrawn yet")
                block["_todo"] = True
            if spec["kind"] == "original" and "clip" not in spec:
                # the picture runs from under the chart's title to the top of its small print, or to the rule that closes the chart
                spec = dict(spec, page=page, clip=[round(frame[0] - 3), round(box[4]), round(frame[2] + 3), round(bottom)])
            for field in ("title", "subtitle", "question", "note"):
                if field in spec and spec[field] is None:
                    block.pop(field, None)
            block.update({k: v for k, v in spec.items() if v is not None})
            if spec.get("subtitle") and block.get("title", "").endswith(spec["subtitle"]):
                block["title"] = block["title"][:-len(spec["subtitle"])].strip()       # the PDF sets both in one block
    return out


def opening(title, blocks):
    """Split a chapter's blocks into what its opening page can hold and the rest.

    The opening page takes the text before the first heading or chart, as far as it fits beside the headline
    figure; a paragraph that introduces a list stays with its list. What is left over before the chapter's
    first main heading starts the text without a heading, as it does in the original.
    """
    room = 440 - 57 * max(0, -(-len(title) // 30) - 1)
    lead = next((k for k, b in enumerate(blocks) if isinstance(b, dict) or b.startswith("#")), len(blocks))
    groups = []                      # runs of blocks that stay together
    for block in blocks[:lead]:
        if block.startswith("- ") and groups:
            groups[-1].append(block)
        else:
            groups.append([block])
    taken = 0
    for group in groups:
        height = sum(22 * -(-len(b) // 120) + 26 for b in group)
        if height > room:
            break
        room -= height
        taken += len(group)
    rest = blocks[taken:]
    if rest and not (isinstance(rest[0], str) and rest[0].startswith("# ")):
        rest = ["::flow"] + rest
    return blocks[:taken] + rest


def dump(blocks):
    return ["```chart\n" + json.dumps(b, ensure_ascii=False, indent=1) + "\n```" if isinstance(b, dict) else b for b in blocks]


def assemble(key):
    p = PLANS[key]
    ids = Ids(p["folder"])
    p["charts"] = p["charts"](ids)
    for spec in p["charts"].values():
        ids.check(spec)
    doc = pymupdf.open(HERE.parent / ".cache" / "pdfs" / p["pdf"])
    items, notes = core_2021.stream(doc, *p["pages"])
    parts = sections(items)
    drop = set(p.get("drop", ()))

    edits = list(p.get("edits", []))
    meta = dict(
        key=key, wave=2021, folder=p["folder"], pdf=p["pdf"], title=p["title"], subtitle=p["subtitle"],
        series=f"Core report of the 2021 poll, first published {p['published']}",
        source=p["source"], copyright=p["copyright"], running=f"Re-set in 2026 from the report of {p['published']}",
        cover_image=p["cover_image"], numbering="chapter", contents_first=True, margins=[55, 800], edits=edits)
    for extra in ("chart_note", "queries", "pending"):
        if p.get(extra):
            meta[extra] = p[extra]

    out, todo, seen, chapter = [], [], set(), 0
    for section in parts:
        title = p.get("titles", {}).get(section["title"], section["title"])
        if section["kind"] == "chapter":
            chapter += 1
            opener = p["chapters"][chapter - 1]
            out.append(f"::chapter {title} | {opener['big']} | {opener['caption']}")
            blocks = opening(title, content(section, p["charts"], doc, drop, heads=("# ", "## "), flat=p.get("flat", False)))
        else:
            out.append(f"::{section['kind']} {title}")
            blocks = content(section, p["charts"], doc, drop, heads=("## ", "### "))
            blocks += p.get("after", {}).get(section["title"], [])
        for block in blocks:
            if isinstance(block, dict):
                seen.add(block["id"])
                if block.pop("_todo", False):
                    todo.append(block["id"])
        out += dump(blocks)
    missing = set(p["charts"]) - seen
    assert not missing, f"charts in the plan that the PDF never reached: {sorted(missing)}"

    text = "\n\n".join(out)
    for old, new in p.get("replace", {}).items():
        assert text.count(old) == 1, (text.count(old), old)
        text = text.replace(old, new)
    text = "---\n" + json.dumps(meta, ensure_ascii=False, indent=1) + "\n---\n\n" + text
    text += "\n\n" + "\n\n".join(f"[^{n}]: {urls(body)}" for n, body in sorted(notes.items())) + "\n"
    (HERE / "content" / f"{key}.md").write_text(text, encoding="utf-8")
    print(f"{key}.md: {len(out)} blocks, {len(seen)} charts ({len(todo)} still pictures of the original: {' '.join(todo)}), {len(notes)} notes")


# ---------------------------------------------------------------- the reports

plan(
    "2021_a_changed_world",
    folder="WRP_2021/core_a_changed_world", pdf="core_a_changed_world.pdf", pages=(3, 50),
    title="A Changed World?", subtitle="Perceptions and experiences of risk in the Covid age", published="July 2022",
    source="World Risk Poll 2021: A Changed World? Perceptions and experiences of risk in the Covid age (Lloyd's Register Foundation, July 2022)",
    copyright="Copyright © 2022 Lloyd's Register Foundation. All rights reserved.",
    cover_image=[10, 0],
    chapters=[
        dict(big="34%", caption="of people worldwide felt ‘less safe’ in 2021 than they did five years earlier, up from 30% in 2019"),
        dict(big="24%", caption="of people worldwide said they or someone they know had experienced serious harm from the work they did"),
        dict(big="7%", caption="of people worldwide named Covid-19 as the greatest source of risk to their safety"),
        dict(big="25%", caption="of people worldwide said they or someone they know had experienced serious harm from mental health issues, up from 20% in 2019"),
        dict(big="67%", caption="of people viewed climate change as a threat to their country, down slightly from 69% in 2019"),
    ],
    after={"Preface": ["**Dr. Ruth Boumphrey**, Chief Executive, Lloyd’s Register Foundation"]},
    edits=[
        "The headline figure on each chapter's opening page is taken from that chapter's key findings; the original opens each chapter with a photograph.",
        "The sentences set in italics beside a green bar are the ones the original repeats in large type beside its photographs, in their original places.",
        "The name under the portrait in the preface is set as a line at the end of the preface.",
        "Footnotes are gathered as numbered references at the back, with their original numbers. Web addresses that the original broke across lines have been joined up.",
    ],
    pending="The three appendices of the original (the questionnaire, the references listed again by chapter, and the list of regions) are not in this draft.",
    charts=lambda ids: {
        "1.1": dict(kind="stacked", rows=[[y, [f"C1_1_{y}_{k}" for k in ("more", "same", "less", "dk")]] for y in ("2019", "2021")], **SAFE4),
        "1.2": dict(kind="stacked_pair", panels=["2019", "2021"], extra="‘Less safe’ difference", extra_unit=" pts",
                    rows=[[label, [f"C1_2_{k}_2019_{x}" for x in SAFE3_KEYS], [f"C1_2_{k}_2021_{x}" for x in SAFE3_KEYS], f"C1_2_{k}_diff"]
                          for label, k in ids.named("C1_2_", "_diff", REGIONS)],
                    series=SAFE4["series"][:3], colours=SAFE4["colours"][:3]),
        "T1.1": dict(kind="matrix", columns=["Less safe", "About as safe", "More safe"] * 2 + ["‘Less safe’ difference"], groups=[["2019", 3], ["2021", 3], ["", 1]],
                     unit=["%"] * 6 + [" pts"], plain=[6],
                     rows=[[name, [f"T1_1_{iso}_{y}_{k}" for y in ("2019", "2021") for k in ("less", "same", "more")] + [f"T1_1_{iso}_diff"]]
                           for iso, name in (("MMR", "Myanmar"), ("ARM", "Armenia"), ("VNM", "Vietnam"), ("NGA", "Nigeria"), ("TUR", "Turkey"))]),
        "1.3": dict(kind="grouped", zero="<0.5", series=["2019", "2021"], colours=["navy", "fuchsia"],
                    rows=[[RISKS[k], [i if i in ids.ids else None for i in (f"C1_3_{k}_2019", f"C1_3_{k}_2021")]] for k in ids.keys("C1_3_", "_2021")]),
        "1.4": dict(kind="hbar", rows=[[RISKS[k], f"C1_4_{k}"] for k in ids.keys("C1_4_")]),
        "T1.2": dict(kind="matrix", zero="<0.5", columns=[RISK_COLUMNS[k] for k in T1_2],
                     rows=[[label, [f"T1_2_{k}_{c}" for c in T1_2]] for label, k in ids.named("T1_2_", "_covid", REGIONS)]),
        "1.5": dict(kind="hbar", rows=ids.regions("C1_5_", None)),
        "T2.1": dict(kind="matrix", columns=["Very worried", "Have experienced or know someone who has experienced", "Ratio"] * 2, groups=[["2019", 3], ["2021", 3]],
                     unit=["%", "%", ":1"] * 2, decimals=[0, 0, 1] * 2, plain=[2, 5],
                     rows=[[label, [i if i in ids.ids else None for i in (f"T2_1_{k}_{y}_{c}" for y in ("2019", "2021") for c in ("very_worried", "experienced", "ratio"))]]
                           for k, label in (("work", "The work you do*"), ("mental", "Mental health issues"), ("food", "The food you eat"),
                                            ("traffic", "Traffic/roadside accidents*"), ("water", "The water you drink"), ("weather", "Severe weather events"),
                                            ("crime", "Violent crime"))]),
        "2.1": dict(kind="grouped", series=["Very worried about work-related harm", "Personally experienced work-related harm"], colours=["fuchsia", "navy"],
                    rows=ids.regions("C2_1_", ["very_worried", "experienced"])),
        "2.2": dict(kind="original", why=SCATTER, subtitle="Results among employed people in each country or territory"),
        "2.3": dict(kind="vgrouped", series=[f"Among those {x}" for x in MONEY.values()],
                    panels=[["", [["Have personally experienced work-related harm in the past two years", [f"C2_3_experienced_{k}" for k in MONEY]],
                                  ["Very worried about work-related harm", [f"C2_3_very_worried_{k}" for k in MONEY]]]]]),
        "T2.2": dict(kind="matrix", columns=[x[0].upper() + x[1:] for x in MONEY.values()],
                     rows=[[label, [f"T2_2_{k}_{c}" for c in MONEY]] for label, k in ids.named("T2_2_", "_comfortable", REGIONS)]),
        "2.4": dict(kind="original", why=SCATTER),
        "3.1": dict(kind="vgrouped", series=["Personal health (non-Covid-19)", "Covid-19/coronavirus related"], colours=["navy", "fuchsia"],
                    panels=[["", [[label, [f"C3_1_{k}_health", f"C3_1_{k}_covid"]] for k, label in AGES.items()]]]),
        "T3.1": dict(kind="matrix", zero="<0.5", columns=["Overall"] + list(QUINTILES.values()),
                     rows=[[label, [f"T3_1_{k}_{c}" for c in ["overall"] + list(QUINTILES)]] for label, k in ids.named("T3_1_", "_overall", REGIONS)]),
        "3.2": dict(kind="original", why=SCATTER),
        "M3.1": dict(kind="region_map", box=[91, -11.5, 128, 29],
                     rows=[[name, iso, f"M3_1_{iso}"] for iso, name in (("MMR", "Myanmar"), ("LAO", "Laos"), ("VNM", "Vietnam"), ("THA", "Thailand"), ("PHL", "Philippines"),
                                                                       ("MYS", "Malaysia"), ("KHM", "Cambodia"), ("SGP", "Singapore"), ("IDN", "Indonesia"))]),
        "4.1": dict(kind="grouped", series=["2019", "2021"], colours=["navy", "fuchsia"],
                    rows=[[label, [f"C4_1_{k}_2019", f"C4_1_{k}_2021"]] for k, label in (("weather", "Severe weather events"), ("mental", "Mental health issues"),
                                                                                       ("crime", "Violent crime"), ("food", "Eating food"), ("water", "Drinking water"))]),
        "4.2": dict(kind="grouped", series=["2019", "2021"], colours=["navy", "fuchsia"],
                    rows=[[label, [f"C4_2_{k}_2019", f"C4_2_{k}_2021"]] for k, label in (("weather", "Severe weather events"), ("crime", "Violent crime"),
                                                                                       ("mental", "Mental health issues"), ("food", "The food you eat"), ("water", "The water you drink"))]),
        "4.3": dict(kind="original", why="the original plots every country without printing its value; the four income-group totals it does print are in the text"),
        "4.4": dict(kind="vgrouped", series=["Among those very worried about severe weather", "Among those somewhat worried", "Among those not worried about severe weather"],
                    panels=[["", [[REGIONS[k], [f"C4_4_{k}_{c}" for c in ("very", "somewhat", "not")]] for k in ids.keys("C4_4_", "_very")]]]),
        "4.5": dict(kind="grouped", series=list(QUINTILES.values()),
                    rows=[[label, [f"C4_5_{k}_{c}" for c in QUINTILES]] for k, label in (("weather", "Severe weather events"), ("work", "The work you do"), ("mental", "Mental health issues"),
                                                                                       ("road", "Road-related accidents/injuries"), ("food", "Eating food"), ("water", "Drinking water"),
                                                                                       ("crime", "Violent crime"))]),
        "5.1": dict(kind="stacked", rows=[[y, [f"C5_1_{y}_{k}" for k in ("very", "somewhat", "not", "dk")]] for y in ("2019", "2021")], **THREAT4),
        "5.2": dict(kind="stacked", rows=[[label, [f"C5_2_{k}_{c}" for c in ("very", "somewhat", "not", "dk")]] for k, label in EDUCATION.items()], **THREAT4),
        "T5.1": dict(kind="matrix", columns=["Not a threat", "Don’t know", "Total*"] * 2, groups=[["2019", 3], ["2021", 3]],
                     rows=[[label, [f"T5_1_{k}_{y}_{c}" for y in ("2019", "2021") for c in ("not", "dk", "total")]] for label, k in ids.named("T5_1_", "_2019_not", REGIONS)]),
        "5.3": dict(kind="vgrouped", series=["Among those who had experienced harm from severe weather", "Among those who know someone who experienced harm from severe weather",
                                             "Among those who neither had experienced/know someone who experienced harm from severe weather"],
                    panels=[["", [[label, [f"C5_3_{k}_{c}" for c in ("experienced", "know_someone", "neither")]]
                                  for k, label in (("total", "Total"), ("primary", "Primary education or less (0-8 years)"), ("secondary", "Secondary education (9-15 years)"),
                                                   ("post_secondary", "Post-secondary education (16+ years)"))]]]),
    },
)


def countries(ids, prefix, suffix=""):
    """[[name, finding]] for the countries of one list, in the printed order."""
    return [[COUNTRIES[k], f"{prefix}{k}{suffix}"] for k in ids.keys(prefix, suffix, COUNTRIES)]


plan(
    "2021_a_resilient_world",
    folder="WRP_2021/core_a_resilient_world", pdf="core_a_resilient_world.pdf", pages=(3, 46),
    title="A Resilient World?", subtitle="Understanding vulnerability in a changing climate", published="September 2022",
    source="World Risk Poll 2021: A Resilient World? Understanding vulnerability in a changing climate (Lloyd's Register Foundation, September 2022)",
    copyright="Copyright © 2022 Lloyd's Register Foundation. All rights reserved.",
    cover_image=[10, 0],
    chapters=[
        dict(big="52%", caption="of people worldwide said there is something they could do to protect themselves or their families from a disaster"),
        dict(big="23%", caption="of people worldwide believed their neighbours care about them ‘a lot’"),
        dict(big="0.44", caption="was the Resilience Index score of Central/Western Africa, the lowest of any region; Australia and New Zealand had the highest, at 0.66"),
        dict(big="27%", caption="of people worldwide said they had experienced a disaster caused by a natural hazard in the past five years"),
    ],
    after={"Preface": ["**Dr. Ruth Boumphrey**, Chief Executive, Lloyd’s Register Foundation"]},
    edits=[
        "The headline figure on each chapter's opening page is taken from that chapter's text; the original opens each chapter with a photograph.",
        "The name under the portrait in the preface is set as a line at the end of the preface.",
        "Footnotes are gathered as numbered references at the back, with their original numbers. Web addresses that the original broke across lines have been joined up.",
        "Chart 1.1 is a ring in the original and Chart 2.4 a row of five rings; both are drawn here as bars. Chart 4.2 is fifteen small bar charts in the original and is "
        "set here as a table of the same values.",
        "In Charts 1.3 and 2.6 the original leaves out segments under 5%. The space they take is drawn in pale grey at the end of the bar, without a figure.",
    ],
    pending="The four appendices of the original (the questionnaire, the list of regions, the Resilience Index methodology and the references listed again by chapter) "
            "are not in this draft.",
    charts=lambda ids: {
        "1.1": dict(kind="stacked", rows=[["World", [f"C1_1_{k}" for k in ("yes", "no", "depends", "dk")]]],
                    series=["Yes", "No", "It depends", "Don’t know"], colours=["teal", "fuchsia", "navy", "grey"]),
        "1.2": dict(kind="hbar", rows=ids.regions("C1_2_", None)),
        "1.3": dict(kind="stacked", gaps=NOT_PRINTED,
                    rows=[[REGIONS[k], [i if i in ids.ids else None for i in (f"C1_3_{k}_{c}" for c in ("lt_week", "week_to_month", "month_to_3", "4_plus", "dk"))]]
                          for k in ids.keys("C1_3_", "_week_to_month")],
                    series=["Less than a week", "One week to less than a month", "One month to three months", "Four months or more", "Don’t know"],
                    colours=["fuchsia", "orange", "teal", "green", "grey"]),
        "1.4": dict(kind="grouped", series=["Have internet access", "Have a mobile phone"], colours=["teal", "fuchsia"],
                    rows=[[label, [f"C1_4_{k}_internet", f"C1_4_{k}_mobile"]] for k, label in INCOME4.items()]),
        "1.5": dict(kind="grouped", series=["Among those with internet access", "Among those without internet access"], colours=["fuchsia", "teal"],
                    rows=[[label, [f"C1_5_{k}_internet", f"C1_5_{k}_no_internet"]] for k, label in INCOME4.items()]),
        "1.6": dict(kind="hbar", rows=countries(ids, "C1_6_")),
        "2.1": dict(kind="hbar", key=["World Bank country income group", "Urbanisation"], colours=["fuchsia", "navy"],
                    rows=[[label, f"C2_1_{k}", "World Bank country income group"] for k, label in INCOME4.items()]
                    + [[label, f"C2_1_{k}", "Urbanisation"] for k, label in (("rural", "Rural areas"), ("small_town", "Small towns"), ("large_city", "Large cities/suburbs"))]),
        "2.2": dict(kind="hbar", rows=ids.regions("C2_2_", None)),
        "2.3": dict(kind="original", why=SCATTER),
        "T2.1": dict(kind="lists", lists=[[head, countries(ids, f"T2_1_{k}_")] for k, head in (
            ("healthcare", "% Dissatisfied with availability of quality healthcare"), ("education", "% Dissatisfied with education system or schools"),
            ("roads", "% Dissatisfied with roads and highways"))]),
        "2.4": dict(kind="hbar", rows=[[label, f"C2_4_{k}"] for k, label in (("nationality", "Nationality/ethnic group"), ("religion", "Religion"), ("sex", "Sex"),
                                                                           ("skin", "Colour of your skin"), ("disability", "Disability"))]),
        "T2.2": dict(kind="lists", lists=[[head, countries(ids, f"T2_2_{k}_")] for k, head in (
            ("nationality", "% Nationality/ethnic group"), ("religion", "% Religion"), ("sex", "% Sex"), ("skin", "% Colour of your skin"), ("disability", "% Disability"))]),
        "2.5": dict(kind="original", why="the original shades every country on a map of the world and prints the value of only ten of them"),
        "2.6": dict(kind="stacked", gaps=NOT_PRINTED,
                    rows=[[REGIONS[k], [i if i in ids.ids else None for i in (f"C2_6_{k}_{c}" for c in ("a_lot", "somewhat", "not_at_all", "dk"))]] for k in ids.keys("C2_6_", "_a_lot")],
                    series=["A lot", "Somewhat", "Not at all", "Don’t know"], colours=["green", "teal", "fuchsia", "grey"]),
        "T2.3": dict(kind="lists", lists=[["% National government does not care ‘at all’", countries(ids, "T2_3_")[:6]],
                                          ["% National government does not care ‘at all’", countries(ids, "T2_3_")[6:]]]),
        "2.7": dict(kind="hbar", unit="", decimals=1, rows=ids.regions("C2_7_", None)),
        "2.8": dict(kind="original", why=SCATTER),
        "3.1": dict(kind="hbar", unit="", decimals=2, rows=ids.regions("C3_1_", None)),
        "3.2": dict(kind="hbar", unit="", decimals=2, key=["Sex", "Urbanisation", "Income"], colours=["teal", "navy", "fuchsia"],
                    rows=[["Men", "C3_2_men", "Sex"], ["Women", "C3_2_women", "Sex"], ["Rural areas", "C3_2_rural", "Urbanisation"],
                          ["Small towns/villages", "C3_2_small_town", "Urbanisation"], ["Large cities/suburbs", "C3_2_large_city", "Urbanisation"],
                          ["Country’s lowest income quintile", "C3_2_q1", "Income"], ["Second quintile", "C3_2_q2", "Income"], ["Third quintile", "C3_2_q3", "Income"],
                          ["Fourth quintile", "C3_2_q4", "Income"], ["Country’s highest income quintile", "C3_2_q5", "Income"]]),
        "T3.3": dict(kind="matrix", unit="", decimals=2, plain=[2], columns=["Index score, bottom income quintile", "Index score, top income quintile", "Difference"],
                     rows=[[name, [f"T3_3_{iso}_{c}" for c in ("bottom", "top", "difference")]] for name, iso in ((COUNTRIES[k], k) for k in ids.keys("T3_3_", "_bottom"))]),
        "4.1": dict(kind="hbar", decimals="g", rows=[[label, f"C4_1_{k}"] for k, label in (
            ("flood", "Flood/Heavy rain"), ("hurricane", "Hurricane/Cyclone"), ("earthquake", "Earthquake"), ("drought", "Drought"), ("wildfire", "Wildfire"),
            ("thunder", "Thunder or lightning storm"), ("tornado", "Tornado"), ("blizzard", "Blizzard or snowstorm"), ("mudslide", "Mudslide"),
            ("volcano", "Volcano eruption"), ("tsunami", "Tsunami"))]),
        "4.2": dict(kind="matrix", plain=[6],
                    columns=["Flood/heavy rain", "Hurricane/cyclone", "Earthquake", "Drought", "Wildfire", "Other", "Did not experience disaster"],
                    rows=[[REGIONS[k], [i if i in ids.ids else None for i in (f"C4_2_{k}_{c}" for c in ("flood", "hurricane", "earthquake", "drought", "wildfire", "other", "none"))]]
                          for k in ids.keys("C4_2_", "_none")]),
        "4.3": dict(kind="grouped", series=["Among those who have experienced a disaster in past five years", "Among those who have not experienced a disaster in past five years"],
                    colours=["fuchsia", "teal"], rows=[[label, [f"C4_3_{k}_disaster", f"C4_3_{k}_no_disaster"]] for k, label in NEEDS.items()]),
        "4.4": dict(kind="vgrouped", series=["Among those who have experienced a disaster in past five years", "Among those who have not experienced a disaster in past five years"],
                    colours=["fuchsia", "teal"],
                    panels=[[title, [[label, [f"C4_4_{g}_{k}_disaster", f"C4_4_{g}_{k}_no_disaster"]] for k, label in NEEDS.items()]]
                            for g, title in (("low_lower_middle", "Low/lower-middle-income countries"), ("upper_middle_high", "Upper-middle/high-income countries"))]),
        "4.5": dict(kind="hbar", rows=ids.regions("C4_5_", None)),
        "4.6": dict(kind="grouped", series=["Hospitals", "Local government", "National government"], rows=ids.regions("C4_6_", ["hospitals", "local", "national"])),
        "T4.1": dict(kind="matrix", columns=["All countries", "Low-income countries", "Lower-middle-income countries", "Upper-middle-income countries", "High-income countries"],
                     rows=[[label, [f"T4_1_{k}_{c}" for c in ("all", "low_income", "lower_middle", "upper_middle", "high_income")]] for k, label in (
                         ("local_news", "Local news, through newspapers, TV or radio"), ("weather_service", "National weather service"), ("internet", "Internet/social media"),
                         ("emergency", "Emergency services (e.g., fire dept., police, medical services)"), ("disaster_agency", "The national disaster management agency"),
                         ("religious", "Local religious leaders"), ("famous", "A famous or influential person you like"))]),
        "4.7": dict(kind="original", why=SCATTER),
        "T4.2": dict(kind="matrix", unit=["%", "%", " pts"], plain=[2],
                     columns=["Among those who had experienced a disaster", "Among those who had not experienced a disaster", "Difference"],
                     rows=[[label, [f"T4_2_{k}_{c}" for c in ("experienced", "not", "difference")]] for k, label in (
                         ("any", "Any type of natural hazard"), ("drought", "Drought"), ("wildfire", "Wildfire"), ("flood", "Flood/heavy rain"),
                         ("hurricane", "Hurricane/cyclone"), ("earthquake", "Earthquake"))]),
    },
)


AI5 = dict(series=["Mostly help", "Neither", "Don’t have an opinion", "Mostly harm", "Don’t know/refused"], colours=["teal", "lime", "orange", "fuchsia", "grey"])
AI5_KEYS = ("help", "neither", "no_opinion", "harm", "dk")
WORRY3 = dict(series=["Very worried", "Somewhat worried", "Not worried"], colours=["fuchsia", "green", "teal"], rest="Don’t know/refused")
SCHOOLING = ["Among those with primary education or less", "Among those with secondary education", "Among those with post-secondary education"]
USES = (("stolen", "Personal information being stolen"), ("companies", "Personal information being used by companies for marketing purposes without your permission"),
        ("government", "Personal information being used by the government without your permission"))
FEELINGS = (("comfortable", "‘Living comfortably’ on current income"), ("getting_by", "‘Getting by’ on current income"),
            ("difficult", "‘Finding it difficult’ on current income"), ("very_difficult", "‘Finding it very difficult’ on current income"))
PLACES = {"MUS": "Mauritius", "TUR": "Türkiye", "POL": "Poland", "HND": "Honduras", "SLV": "El Salvador", "GRC": "Greece", "USA": "United States", "JPN": "Japan",
          "HKG": "Hong Kong SAR of China", "IRN": "Iran", "KOR": "South Korea", "FIN": "Finland", "SWE": "Sweden", "CHN": "China", "DEU": "Germany", "NOR": "Norway",
          "EST": "Estonia", "DNK": "Denmark", "ISL": "Iceland", "ARE": "United Arab Emirates", "AFG": "Afghanistan", "ITA": "Italy", "ESP": "Spain", "KGZ": "Kyrgyzstan",
          "SAU": "Saudi Arabia", "NPL": "Nepal"}


def ai_rows(ids, prefix, names):
    """Rows of the five answers on artificial intelligence; an answer the original does not print is null."""
    return [[label, [i if i in ids.ids else None for i in (f"{prefix}{k}_{c}" for c in AI5_KEYS)]] for k, label in names]


plan(
    "2021_a_digital_world",
    folder="WRP_2021/core_a_digital_world", pdf="core_a_digital_world.pdf", pages=(3, 35),
    title="A Digital World", subtitle="Perceptions of risk from AI and misuse of personal data", published="November 2022",
    source="World Risk Poll 2021: A Digital World. Perceptions of risk from AI and misuse of personal data (Lloyd's Register Foundation, November 2022)",
    copyright="Copyright © 2022 Lloyd's Register Foundation. All rights reserved.",
    cover_image=[10, 0],
    chapters=[
        dict(big="39%", caption="of people worldwide believed artificial intelligence will ‘mostly help’ people in their country in the next 20 years; 28% said it will ‘mostly harm’"),
        dict(big="63%", caption="of people worldwide said they had used the internet in the past 30 days, up from 54% in 2019"),
        dict(big="44%", caption="of internet users worldwide were ‘very worried’ that their personal information could be stolen"),
    ],
    after={"Preface": ["**Dr. Ruth Boumphrey**, Chief Executive, Lloyd’s Register Foundation"]},
    edits=[
        "The headline figure on each chapter's opening page is taken from that chapter's charts; the original opens each chapter with a photograph.",
        "The name under the portrait in the preface is set as a line at the end of the preface.",
        "Footnotes are gathered as numbered references at the back, with their original numbers. Web addresses that the original broke across lines have been joined up.",
        "Map 1.1 is a map of the world shaded by region in the original; its fifteen ratios are drawn here as bars. Chart 1.7 is a ring in the original and is drawn as a bar.",
        "In the charts of views on artificial intelligence the original draws segments under 5% without a figure. Where a bar has one such segment it is drawn in its place, "
        "at what is left of 100%, also without a figure; where it has two, the space they take is drawn in pale grey at the end of the bar.",
    ],
    pending="The three appendices of the original (the questionnaire, the list of regions and the references listed again by chapter) are not in this draft.",
    charts=lambda ids: {
        "1.1": dict(kind="grouped", series=["World", "Women", "Men"], colours=["teal", "fuchsia", "navy"],
                    rows=[[label, [f"C1_1_{g}_{k}" for g in ("world", "women", "men")]] for k, label in zip(AI5_KEYS, AI5["series"])]),
        "1.2": dict(kind="stacked", gaps=NOT_PRINTED, extra="Ratio: mostly help/mostly harm", extra_decimals=1,
                    rows=[row + [f"C1_2_{k}_ratio"] for row, k in zip(ai_rows(ids, "C1_2_", [(k, REGIONS[k]) for k in ids.keys("C1_2_", "_ratio")]), ids.keys("C1_2_", "_ratio"))],
                    **AI5),
        "M1.1": dict(kind="hbar", unit="", decimals=1, rows=ids.regions("M1_1_", None)),
        "T1.1": dict(kind="matrix", unit=["%", "%", " pts", "%"], plain=[2], columns=["Mostly help", "Mostly harm", "Net ‘mostly help’*", "No opinion/don’t know"],
                     rows=[[PLACES[k], [f"T1_1_{k}_{c}" for c in ("help", "harm", "net", "no_opinion_dk")]] for k in ids.keys("T1_1_", "_net")]),
        "1.3": dict(kind="stacked", gaps=NOT_PRINTED, rows=ai_rows(ids, "C1_3_", [("access", "Have access to the internet"), ("no_access", "Do not have access to the internet")]), **AI5),
        "1.4": dict(kind="stacked", gaps=NOT_PRINTED,
                    rows=ai_rows(ids, "C1_4_", [("important", "Religion important in daily life"), ("not_important", "Religion not important in daily life")]), **AI5),
        "1.5": dict(kind="stacked", gaps=NOT_PRINTED, rows=ai_rows(ids, "C1_5_", [
            ("experienced", "Have experienced discrimination based on race/nationality, skin colour or gender"),
            ("not_experienced", "Have not experienced discrimination based on race/nationality, skin colour or gender")]), **AI5),
        "1.6": dict(kind="grouped", series=["‘Mostly harm’ among those who had experienced discrimination", "‘Mostly harm’ among those who had not experienced discrimination"],
                    colours=["fuchsia", "teal"], rows=[[PLACES[k], [f"C1_6_{k}_experienced", f"C1_6_{k}_not_experienced"]] for k in ("DNK", "NOR", "SWE")]),
        "1.7": dict(kind="stacked", rows=[["World", ["C1_7_yes", "C1_7_no", "C1_7_dk"]]],
                    series=["Yes, would feel safe", "No, would not feel safe", "Don’t know/refused"], colours=["teal", "fuchsia", "grey"]),
        "T1.2": dict(kind="lists", lists=[["% Yes, would feel safe", [[PLACES[k], f"T1_2_{k}"] for k in ids.keys("T1_2_")[:5]]],
                                          ["% Yes, would feel safe", [[PLACES[k], f"T1_2_{k}"] for k in ids.keys("T1_2_")[5:]]]]),
        "1.8": dict(kind="grouped", series=SCHOOLING, colours=["fuchsia", "teal", "navy"],
                    rows=[[label, [f"C1_8_{k}_{c}" for c in ("primary", "secondary", "post_secondary")]] for k, label in (
                        ("world", "World"), ("internet", "People who have internet access"), ("no_internet", "People who do not have internet access"))]),
        "2.1": dict(kind="grouped", series=["2019", "2021"], colours=["navy", "fuchsia"],
                    rows=[[label, [f"C2_1_{k}_2019", f"C2_1_{k}_2021"]] for k, label in (
                        ("world", "World"), ("low", "Low-income countries"), ("lower_middle", "Lower-middle-income countries"),
                        ("upper_middle", "Upper-middle-income countries"), ("high", "High-income countries"))]),
        "2.2": dict(kind="hbar", rows=ids.regions("C2_2_", None)),
        "2.3": dict(kind="grouped", series=SCHOOLING, colours=["fuchsia", "teal", "navy"],
                    rows=[[label, [f"C2_3_{k}_{c}" for c in ("primary", "secondary", "post_secondary")]] for k, label in (
                        ("world", "World"), ("south_asia", "Southern Asia"), ("central_west_africa", "Central/Western Africa"), ("east_africa", "Eastern Africa"))]),
        "2.4": dict(kind="grouped", series=["2019", "2021"], colours=["navy", "fuchsia"],
                    rows=[[label, [f"C2_4_{k}_2019", f"C2_4_{k}_2021"]] for k, label in AGES.items()]),
        "3.1": dict(kind="stacked", rows=[[label, [f"C3_1_{k}_{c}" for c in ("very", "somewhat", "not")]] for k, label in USES], **WORRY3),
        "3.2": dict(kind="stacked", rows=ids.regions("C3_2_", ["very", "somewhat", "not"]), **WORRY3),
        "3.3": dict(kind="original", why=SCATTER),
        "3.4": dict(kind="hbar", key=["Age group", "Feelings about current income"], colours=["fuchsia", "teal"],
                    rows=[[label, f"C3_4_{k}", "Age group"] for k, label in AGES.items()] + [[label, f"C3_4_{k}", "Feelings about current income"] for k, label in FEELINGS]),
        "3.5": dict(kind="grouped", series=["Companies for marketing purposes without your permission", "The government without your permission"], colours=["fuchsia", "teal"],
                    rows=ids.regions("C3_5_", ["companies", "government"])),
        "3.6": dict(kind="grouped", series=["Among those who have confidence in national government", "Among those who do not have confidence in national government"],
                    colours=["teal", "fuchsia"], rows=[[PLACES[k], [f"C3_6_{k}_confidence", f"C3_6_{k}_no_confidence"]] for k in ids.keys("C3_6_", "_no_confidence")]),
        "3.7": dict(kind="grouped", series=["Companies for marketing purposes without your permission", "The government without your permission"], colours=["fuchsia", "teal"],
                    title="Percentage of internet users ‘very worried’ about the government or companies using their online personal information, by feelings about current income",
                    subtitle=None, rows=[[label, [f"C3_7_{k}_companies", f"C3_7_{k}_government"]] for k, label in FEELINGS]),
        "3.8": dict(kind="grouped", series=["Among those who had not experienced discrimination", "Among those who had experienced one form of discrimination",
                                            "Among those who had experienced two or more forms of discrimination"], colours=["teal", "fuchsia", "navy"],
                    rows=[[label.replace("Personal information being", "Being").replace("Being stolen", "Being stolen"), [f"C3_8_{k}_{c}" for c in ("none", "one", "two_plus")]]
                          for k, label in USES]),
    },
)


SEXES = dict(series=["Male", "Female"], colours=["teal", "fuchsia"])
BIRTH = dict(series=["Native-born", "Foreign-born"], colours=["fuchsia", "teal"])
INCOME_GROUPS = (("low", "Low-income countries"), ("lower_middle", "Lower-middle-income countries"), ("upper_middle", "Upper-middle-income countries"), ("high", "High-income countries"))
FIFTHS = (("poorest", "Poorest 20%"), ("second", "Second 20%"), ("middle", "Middle 20%"), ("fourth", "Fourth 20%"), ("richest", "Richest 20%"))
FORMS = (("sexual", "Sexual"), ("psychological", "Psychological"), ("physical", "Physical"))
SCHOOL = (("tertiary", "Tertiary (16 years or more)"), ("secondary", "Secondary (8-15 years)"), ("primary", "Primary (0-8 years)"))
WORKPLACES = {"AUS": "Australia", "FIN": "Finland", "ISL": "Iceland", "NZL": "New Zealand", "DNK": "Denmark", "USA": "United States", "NOR": "Norway", "CAN": "Canada",
              "GRC": "Greece", "SWE": "Sweden", "KGZ": "Kyrgyzstan", "LBN": "Lebanon", "MYS": "Malaysia", "UZB": "Uzbekistan", "ARM": "Armenia", "IDN": "Indonesia",
              "GEO": "Georgia", "KAZ": "Kazakhstan", "PAK": "Pakistan", "TJK": "Tajikistan"}
TOP3 = {"australia_nz": "Australia and New Zealand", "central_western_africa": "Central/Western Africa", "eastern_asia": "East Asia", "northern_america": "Northern America",
        "eastern_europe": "Eastern Europe", "central_asia": "Central Asia"}
COMBINATIONS = (("psychological", "Psychological"), ("physical", "Physical"), ("sexual", "Sexual"), ("psychological_physical", "Psychological + physical"),
                ("sexual_psychological", "Sexual + psychological"), ("sexual_physical", "Sexual + physical"), ("all_three", "Sexual + physical + psychological"))


def workplace_rows(ids, fig_text):
    """Table 1.1: the ten countries with the highest and the ten with the lowest experience, each with its income group."""
    keys = ids.keys("T1_1_", "_all")
    row = lambda k: [f"{WORKPLACES[k]} ({fig_text[f'T1_1_{k}_income']})", [f"T1_1_{k}_{c}" for c in ("all", "men", "women", "diff")]]
    return [["Ten countries with highest experience", None]] + [row(k) for k in keys[:10]] + [["Ten countries with lowest experience", None]] + [row(k) for k in keys[10:]]


def published_text(folder):
    with open(HERE.parents[1] / folder / "published_figures.csv", encoding="utf-8") as f:
        return {row["finding_id"]: row["published_value"] for row in csv.DictReader(f)}


plan(
    "2021_safe_at_work",
    folder="WRP_2021/core_safe_at_work", pdf="core_safe_at_work.pdf", pages=(3, 37), flat=True,
    title="Safe at Work?", subtitle="Global experiences of violence and harassment", published="January 2023",
    source="World Risk Poll 2021: Safe at Work? Global experiences of violence and harassment (Lloyd's Register Foundation, January 2023)",
    copyright="Copyright © 2023 Lloyd's Register Foundation. All rights reserved.",
    cover_image=[9, 0],
    chapters=[
        dict(big="20.9%", caption="of people who have ever worked said they had experienced some form of violence and harassment at work in their lifetime"),
        dict(big="27.7%", caption="of those who had experienced violence and harassment at work had experienced more than one form of it"),
        dict(big="30.2%", caption="of foreign-born women said they had experienced violence and harassment in the workplace, compared with 21.5% of native-born women"),
    ],
    after={"Preface": ["**Dr. Ruth Boumphrey**, Chief Executive, Lloyd’s Register Foundation"]},
    edits=[
        "The headline figure on each chapter's opening page is taken from that chapter's text; the original opens each chapter with a photograph.",
        "The name under the portrait in the preface is set as a line at the end of the preface.",
        "Footnotes are gathered as numbered references at the back, with their original numbers. Web addresses that the original broke across lines have been joined up.",
        "Chart 1.1 is a ring in the original and is drawn as a bar. Chart 2.2 is two blocks of rectangles sized by their values, one for men and one for women; "
        "it is drawn here as paired bars. In Table 1.1 each country's World Bank income group follows its name instead of having a column of its own.",
        "Where the original draws a segment under 5% without a figure, it is drawn in its place at what is left of 100%, also without a figure.",
    ],
    queries=[
        "Chart 1.7. The key of the original reads ‘No experience of violence and harassment’ and ‘Experience of violence and harassment’, but both bars are the percentage who "
        "experienced it: the shorter one among people who had not experienced that type of discrimination, the longer one among people who had. The key is kept as printed.",
    ],
    pending="The four appendices of the original (the questionnaire, the list of regions, the methodology note and the references listed again by chapter) are not in this draft.",
    charts=lambda ids: {
        "1.1": dict(kind="stacked", gaps=NOT_PRINTED, rows=[["World", ["C1_1_no", "C1_1_last_year", "C1_1_two_five", "C1_1_five_plus", None]]],
                    series=["No", "Yes, last year", "Yes, 2-5 years ago", "Yes, 5+ years ago", "Yes, do not know"], colours=["teal", "fuchsia", "navy", "grey", "purple"]),
        "1.2": dict(kind="stacked", rows=[[label, [f"C1_2_{k}_no", f"C1_2_{k}_yes"]] for k, label in (("men", "Male"), ("women", "Female"))],
                    series=["Not experienced", "Experienced"], colours=["teal", "fuchsia"]),
        "1.3": dict(kind="grouped", rows=ids.regions("C1_3_", ["men", "women"]), **SEXES),
        "T1.1": dict(kind="matrix", decimals=1, unit=["%", "%", "%", " pts"], plain=[3], columns=["All", "Men", "Women", "Percentage point difference (women – men)"],
                     rows=workplace_rows(ids, published_text("WRP_2021/core_safe_at_work"))),
        "1.4": dict(kind="grouped", rows=[[label, [f"C1_4_{k}_men", f"C1_4_{k}_women"]] for k, label in INCOME_GROUPS], **SEXES),
        "1.5": dict(kind="grouped", rows=[[label, [f"C1_5_{k}_men", f"C1_5_{k}_women"]] for k, label in INCOME_GROUPS], **SEXES),
        "1.6": dict(kind="stacked", rows=[[label, [f"C1_6_{k}_no", f"C1_6_{k}_yes"]] for k, label in (("discrimination", "Experienced discrimination"), ("none", "No discrimination"))],
                    series=["No experience of violence and harassment", "Experience of violence and harassment"], colours=["teal", "fuchsia"]),
        "1.7": dict(kind="grouped", series=["No experience of violence and harassment", "Experience of violence and harassment"], colours=["teal", "fuchsia"],
                    rows=[[label, [f"C1_7_{k}_no", f"C1_7_{k}_yes"]] for k, label in (
                        ("gender", "Due to your gender"), ("skin", "Due to the colour of your skin"), ("nationality", "Due to your nationality/ethnic group"),
                        ("religion", "Due to your religion"), ("disability", "Due to a disability"))]),
        "1.8": dict(kind="stacked", gaps=NOT_PRINTED, rows=[[label, [f"C1_8_{k}_yes", f"C1_8_{k}_no", None]] for k, label in FORMS],
                    series=["Yes", "No", "Don’t know/refused"], colours=["fuchsia", "teal", "navy"]),
        "1.9": dict(kind="stacked", gaps=NOT_PRINTED,
                    rows=[[f"{label}: {sex}", [f"C1_9_{k}_{s}_yes", f"C1_9_{k}_{s}_no", None]] for k, label in FORMS for s, sex in (("men", "Male"), ("women", "Female"))],
                    series=["Yes", "No", "Don’t know/refused"], colours=["fuchsia", "teal", "navy"]),
        "1.10": dict(kind="stacked", gaps=NOT_PRINTED, rows=[[label, [f"C1_10_{k}_once_twice", f"C1_10_{k}_three_five", f"C1_10_{k}_more_five", None]] for k, label in FORMS],
                     series=["Once or twice", "Three to five times", "More than five times", "Don’t know/refused"], colours=["teal", "grey", "fuchsia", "navy"]),
        "T1.2": dict(kind="lists", lists=[[label, [[TOP3[r], f"T1_2_{k}_{r}"] for r in ids.keys(f"T1_2_{k}_", "", TOP3)]] for k, label in (
            ("physical", "Physical"), ("psychological", "Psychological"), ("sexual", "Sexual"))]),
        "2.1": dict(kind="stacked", rows=[[label, [f"C2_1_{k}_{c}" for c in ("one", "two", "three")]] for k, label in (("men", "Male"), ("women", "Female"))],
                    series=["One type", "Two types", "Three types"], colours=["teal", "grey", "fuchsia"]),
        "2.2": dict(kind="grouped", rows=[[label, [i if i in ids.ids else None for i in (f"C2_2_men_{k}", f"C2_2_women_{k}")]] for k, label in COMBINATIONS], decimals="g", **SEXES),
        "2.3": dict(kind="stacked", gaps=NOT_PRINTED, rows=[["Experience of discrimination", [f"C2_3_discrimination_{c}" for c in ("one", "two", "three")]],
                                                           ["No experience of discrimination", ["C2_3_none_one", "C2_3_none_two", None]]],
                    series=["One type", "Two types", "Three types"], colours=["teal", "grey", "fuchsia"]),
        "3.1": dict(kind="stacked", gaps=NOT_PRINTED, rows=[[label, [f"C3_1_{k}_none", f"C3_1_{k}_one", f"C3_1_{k}_two", None]] for k, label in SCHOOL],
                    series=["No type", "1 type", "2 types", "3 types"], colours=["navy", "teal", "grey", "fuchsia"]),
        "3.2": dict(kind="stacked", gaps=NOT_PRINTED, rows=[[label, [f"C3_2_{k}_no", f"C3_2_{k}_yes", None]] for k, label in SCHOOL],
                    series=["Didn’t tell someone", "Told someone", "Don’t know/refused"], colours=["teal", "fuchsia", "navy"]),
        "T3.1": dict(kind="matrix", columns=["Employer", "Co-worker", "Friend or family", "Trade union", "Police/community leader", "Social services"],
                     rows=[[label, [f"T3_1_{k}_{c}" for c in ("employer", "coworker", "family", "union", "police", "social")]] for k, label in SCHOOL]),
        "T3.2": dict(kind="matrix", columns=["Worried people at work would find out", "Fear for my reputation", "Waste of time"],
                     rows=[[label, [f"T3_2_{k}_{c}" for c in ("find_out", "reputation", "waste")]] for k, label in SCHOOL]),
        "3.3": dict(kind="grouped", rows=[[label, [f"C3_3_{k}_native", f"C3_3_{k}_foreign"]] for k, label in (("women", "Female"), ("men", "Male"))], **BIRTH),
        "3.4": dict(kind="grouped", rows=[[label, [f"C3_4_{k}_native", f"C3_4_{k}_foreign"]] for k, label in FIFTHS], **BIRTH),
        "3.5": dict(kind="grouped", rows=[[label, [f"C3_5_{k}_native", f"C3_5_{k}_foreign"]] for k, label in INCOME_GROUPS], **BIRTH),
        "3.6": dict(kind="grouped", rows=[[label, [f"C3_6_{k}_native", f"C3_6_{k}_foreign"]] for k, label in FIFTHS], **BIRTH),
        "3.7": dict(kind="grouped", rows=[[label, [f"C3_7_{k}_native", f"C3_7_{k}_foreign"]] for k, label in FIFTHS], **BIRTH),
        "3.8": dict(kind="grouped", rows=[[label, [f"C3_8_{k}_native", f"C3_8_{k}_foreign"]] for k, label in FIFTHS], **BIRTH),
    },
)


if __name__ == "__main__":
    assemble(sys.argv[1])
