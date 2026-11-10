"""Assemble the content files of the reports of the 2023 poll.

    python reports/book/redesign/assemble_2023.py 2023_resilience_in_a_changing_world

Each report stays one report, with its own foreword, executive summary, chapters
and conclusion, in the original order. core_2023.py reads the PDF; this script
arranges what it finds as content/<report>.md, gives every chart its
specification from the plan in plans_2023.py, and takes each chart's title,
question text and notes from the PDF. A chart with no specification yet is
placed as a picture of the original, so a draft is complete from the first run.
"""

import json
import re
import sys
from pathlib import Path

import pymupdf

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import core_2023  # noqa: E402
from assemble_2019 import open_ended  # noqa: E402
from assemble_2021 import Ids, dump, opening, urls  # noqa: E402

PLANS = {}
SKIP = ("Contents", "List of figures", "List of Figures")
PREFIX = {"Chart": "", "Table": "T", "Figure": "F", "Map": "M"}


def plan(key, **fields):
    PLANS[key] = fields


def sections(items, chapters=()):
    """The report as sections: each pink title, with whether it is a chapter, and the items under it.

    A chapter carries a number in the original; a report whose sections have no numbers names its chapters in its plan.
    """
    out, current = [], None
    for item in items:
        if item["kind"] == "number":
            continue
        if item["kind"] == "title":
            numbered = any(i["kind"] == "number" and i["page"] == item["page"] and abs(i["y0"] - item["y0"]) < 14 for i in items)
            m = re.match(r"(\d+)\.\s+", item["text"])
            current = dict(title=item["text"][m.end():] if m else item["text"], chapter=numbered or bool(m) or item["text"] in chapters, items=[], page=item["page"])
            out.append(current)
        elif current is not None:
            current["items"].append(item)
    return out


def references(items):
    """{number: text} from the numbered list at the back."""
    notes, number = {}, None
    for item in items:
        if item["kind"] not in ("small", "p", "letter"):
            continue
        text = (item.get("mark") or "") + item["text"].replace("*", "")       # (the number may have been read as the mark of a list)
        m = re.match(r"(\d+)\.?\s+", text)
        if m and int(m.group(1)) == len(notes) + 1:
            number = int(m.group(1))
            notes[number] = text[m.end():]
        elif number is not None:
            notes[number] += " " + text
    return {n: urls(re.sub(r"(?<=[\w/.]) (?=(?:com|org|net|uk|int|edu|gov)\b[/.])|(?<=www\.) ", "", text)) for n, text in notes.items()}


def small_print(lines):
    """(question, note) of the small print under a chart."""
    question, note = [], []
    quoted = re.match(r"“([^”]+\?)”\s*", lines[0]) if lines else None
    if quoted:                              # small print that opens with the question in quotation marks: the rest is the note
        question, lines = [quoted.group(1)], [lines[0][quoted.end():]] + list(lines[1:])
    for text in (part for line in lines for part in re.split(r"\s+(?=Notes?: )", line) if part):
        m = re.match(r"(?:Survey|Poll) questions?(?: \d{4}(?:, \d{4})*)?:\s*", text)
        if m and not text[:m.end()].rstrip(": ").endswith(("question", "questions")):
            note.append(text)               # "Survey question 2019: ...": the wording of another year, kept whole
        elif m:
            question.append(text[m.end():])
        elif question and not note and text.rstrip().endswith("?"):
            question.append(text)           # a second question, on a line of its own
        else:
            note.append(text)
    return " ".join(question).strip(), " ".join(note).strip()


def letters(text):
    return re.sub(r"[^a-z0-9]", "", text.lower().replace("&", "and").replace("ﬁ", "fi").replace("ﬂ", "fl"))


def warn(block, page):
    """Say which of a redrawn chart's labels are not lettering of the original chart's page."""
    if block["kind"] in ("original", "heading"):
        return
    there = letters(page.get_text())
    labels = list(block.get("series", [])) + list(block.get("columns", [])) + [g[0] for g in block.get("groups", [])]
    for part in block.get("parts", [block]):
        labels += [r[0] for r in part.get("rows", [])] + [part.get("heading", "")]
        for title, groups in part.get("panels", []):
            labels += [title] + [g[0] for g in groups]
    missing = [label for label in dict.fromkeys(labels) if label and "{" not in label and letters(label) not in there]
    if missing:
        print(f"   {block['as']} {block['number']}: labels that are not on the original's page: {missing}")


def blocks(section, charts, feet, heads, doc, wide_at=470):
    """A section's items as content blocks: strings, and dicts for charts."""
    out = []                        # [block, [notes set under it]]
    box = running = None            # the box that is open; (index in out, item) of the last paragraph of running text
    held = []                       # sentences set large beside a box, kept until the box is closed
    loose = []                      # (index in out, page) of small print set on its own

    def close():
        nonlocal box
        if box is not None:
            out.append(["::endbox", []])
            box = None
        out.extend(held)
        held.clear()

    for item in section["items"]:
        kind, text = item["kind"], item["text"]
        notes = [f"^ [^{m}] {feet[item['page']][m]}" for m in dict.fromkeys(re.findall(r"\[\^([ivx]+)\]", text)) if m in feet.get(item["page"], {})]
        ground = (item["page"], item["box"]) if item["box"] is not None else None
        if ground != box and kind != "quote":
            if ground is None:
                close()
            elif kind == "boxtitle" or box is None or not (out and running and open_ended(out[running[0]][0])):
                close()
                out.append([f"::box {text if kind == 'boxtitle' else ''}".rstrip(), notes])
                box = ground
                if kind == "boxtitle":
                    continue
            else:
                box = ground        # the same box, carried over a column
        if kind == "boxtitle":
            out.append([f"**{text}**", notes])
        elif kind in ("h1", "h2", "h3"):
            level = ("h1", "h2", "h3").index(kind)
            out.append([f"**{text}**" if box else heads[min(level, len(heads) - 1)] + text, notes])
            running = None
        elif kind == "quote":
            (held if box else out).append(["> " + text, []])
        elif kind == "small":
            out.append(["^ " + text, notes])
            loose.append((len(out) - 1, item["page"]))
        elif kind == "chart":
            m = re.match(core_2023.FIGURE, item["label"] + ". ")
            block = dict(id=PREFIX[m.group(1)] + m.group(2), number=m.group(2), title=item["title"])
            block["as"] = m.group(1)
            if item.get("subtitle"):
                block["subtitle"] = item["subtitle"]
            small = item["small"]
            if not small:
                # a chart with its small print set apart, in the other column: the small print before it on its page is its own
                mine = [k for k, page in loose if page == item["page"] and out[k] is not None]
                small = [out[k][0][2:] for k in mine]
                for k in mine:
                    out[k] = None
            question, note = small_print(small)
            if question:
                block["question"] = question
            if note:
                block["note"] = note
            spec = charts.get(block["id"])
            if spec is None:
                spec = dict(kind="original", why="it has not been redrawn yet")
                block["_todo"] = True
            if spec["kind"] == "original":
                spec = dict(dict(page=item["page"], clip=item["clip"]), **spec)
                if item["blank"] and "blank" not in spec:
                    spec["blank"] = item["blank"]
                if spec["clip"][2] - spec["clip"][0] > wide_at and "plate" not in spec and "width" not in spec:
                    spec["plate"] = True
            for field in ("title", "subtitle", "question", "note"):
                if field in spec and spec[field] is None:
                    block.pop(field, None)
            if spec.get("note_add"):
                spec = dict(spec, note=(block.get("note", "") + " " + spec["note_add"]).strip())
            block.update({k: v for k, v in spec.items() if v is not None and k not in ("note_add", "text_from", "note_from", "groups_of")})
            if spec.get("note_from"):
                block["note"] = core_2023.sentences(doc[item["page"]], spec["note_from"], (5.8, 6.2))
            warn(block, doc[item["page"]])
            out.append([block, notes])
            if spec.get("text_from"):
                # a table that is text: its rows are set as text under its title, grouped as the plan says
                rows = core_2023.entries(doc[item["page"]], spec["text_from"])
                assert len(rows) == sum(n for _, n in spec["groups_of"]), (len(rows), [r[0] for r in rows])
                for name, n in spec["groups_of"]:
                    out.append([f"### {name}", []])
                    for lead, body, bullets in rows[:n]:
                        out.append([f"- **{lead}** {body}".rstrip(), []])
                        out += [[f"-- {b}", []] for b in bullets]
                    rows = rows[n:]
        elif kind == "p":
            style = item["style"]
            if style == "*" and not box and not item["mark"] and len(text) < 160 and out and out[-1][0][:1] == ">" and isinstance(out[-1][0], str):
                # a short line in italic under a sentence set large: where the sentence is from
                if out[-1][0].startswith(">-- "):
                    out[-1][0] += " " + text
                else:
                    out.append([">-- " + text, notes])
                running = None
                continue
            if item["mark"]:
                out.append([item["mark"] + text, notes])
                running = (len(out) - 1, item)
                continue
            if running is not None:
                k, before = running
                moved = (before["page"], before["col"]) != (item["page"], item["col"])
                # (an entry of a list runs on only into text that starts in lower case: a paragraph that follows a list in the next column is a new one)
                # (and a colon closes a paragraph unless the next column carries the sentence on in lower case)
                carried = moved and text[:1].islower() and out[k][0].rstrip("*").endswith(":")
                if carried or open_ended(out[k][0].rstrip("*")) and (text[:1].islower() or (moved and not before["mark"])):
                    out[k][0] = (out[k][0].rstrip("*") + " " + text + ("*" if out[k][0].endswith("*") and not out[k][0].endswith("**") else ""))
                    out[k][1] += notes
                    running = (k, dict(item, mark=before["mark"]))
                    continue
            if style == "*" and not box:
                text = f"*{text}*"
            elif style in ("**", "***"):
                text = f"**{text}**"
            out.append([text, notes])
            running = (len(out) - 1, item)
    close()
    flat, waiting = [], []
    out = [entry for entry in out if entry is not None]
    for k, (block, notes) in enumerate(out):
        flat.append(block)
        waiting += notes
        following = out[k + 1][0] if k + 1 < len(out) else ""
        if not (isinstance(block, str) and block.startswith(("- ", "-- ")) and isinstance(following, str) and following.startswith(("- ", "-- "))):
            flat += waiting             # the notes of a list's entries are set under the whole list
            waiting = []
    return flat


def assemble(key):
    p = PLANS[key]
    ids = Ids(p["folder"])
    charts = p["charts"](ids) if callable(p.get("charts")) else p.get("charts", {})
    for spec in charts.values():
        for part in spec.get("parts", [spec]):
            ids.check(part)
    doc = pymupdf.open(HERE.parent / ".cache" / "pdfs" / p["pdf"])
    items, feet = [], {}
    for first, last in p["pages"]:
        got, notes = core_2023.read(doc, first, last, p.get("numbers"), p.get("small_text", ()), p.get("box_gap", 12.3))
        items += [i for i in got if i["text"] not in p.get("drop", ())]
        feet.update(notes)
    for item in items:
        if item["kind"] == "title" and item["text"] in p.get("inside", ()):
            item["kind"] = "h1"                 # a title set as large as a section's, inside a section
    parts = sections(items, p.get("as_chapters", ()))

    focus = p.get("focus", False)
    kind = "Focus On report" if focus else "Core report"
    meta = dict(
        key=key, wave=2023, edition=2024, brand="World Risk Poll 2024", folder=p["folder"], pdf=p["pdf"], title=p["title"], subtitle=p.get("subtitle", ""),
        series=f"{kind} of the 2023 poll, first published {p['published']}",
        source=p["source"], copyright=p["copyright"], running=f"Re-set in 2026 from the report of {p['published']}",
        cover_image=p["cover_image"], numbering="chapter", contents_first=True, margins=[core_2023.TOP, core_2023.BOTTOM], edits=list(p.get("edits", [])))
    for extra in ("chart_note", "queries", "pending", "running_title", "numbering_note", "plain_opener", "contents_h2"):       # ("edits" is set above)
        if p.get(extra):
            meta[extra] = p[extra]

    out, todo, seen, notes, chapter = [], [], set(), {}, 0
    for section in parts:
        title = p.get("titles", {}).get(section["title"], section["title"])
        if title in SKIP or title in p.get("skip", ()):
            continue
        if title == "References":
            notes = references(section["items"])
            continue
        if section["chapter"]:
            chapter += 1
            opener = p["chapters"][chapter - 1]
            out.append(f"::chapter {title} | {opener['big']} | {opener['caption']}")
            made = opening(title, blocks(section, charts, feet, ("# ", "## ", "### "), doc))
        else:
            out.append(f"::{'back' if chapter else 'front'} {title}")
            made = blocks(section, charts, feet, ("## ", "### "), doc)
            made += p.get("after", {}).get(section["title"], [])
        for block in made:
            if isinstance(block, dict):
                seen.add(block["id"])
                if block.pop("_todo", False):
                    todo.append(block["id"])
        out += dump(made)
    missing = set(charts) - seen
    assert not missing, f"charts in the plan that the PDF never reached: {sorted(missing)}"

    text = "\n\n".join(out)
    for old, new in p.get("replace", {}).items():
        assert text.count(old) == 1, (text.count(old), old)
        text = text.replace(old, new)
    text = "---\n" + json.dumps(meta, ensure_ascii=False, indent=1) + "\n---\n\n" + text
    text += "\n\n" + "\n\n".join(f"[^{n}]: {body}" for n, body in sorted(notes.items())) + "\n"
    (HERE / "content" / f"{key}.md").write_text(text, encoding="utf-8")
    print(f"{key}.md: {len(out)} blocks, {len(seen)} charts and tables ({len(todo)} still pictures of the original: {' '.join(todo)}), {len(notes)} references")


if __name__ == "__main__":
    import assemble_2023 as assembler       # the module the plans register with
    import plans_2023  # noqa: F401
    for name in sys.argv[1:] or assembler.PLANS:
        assembler.assemble(name)
