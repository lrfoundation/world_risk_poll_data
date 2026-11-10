"""Check a content file against the published PDF, both ways.

    python reports/book/redesign/check.py 2019_risk_at_work 87 111

1. Every sentence of the content file (outside the new writing) must be in the PDF.
2. Every block of running text on the PDF pages must be in the content file.

Text is compared as letters only, so line breaks, hyphenation at line ends,
footnote marks and chart renumbering do not count as differences. Page ranges
are 0-based and inclusive; give several pairs for a report made of several chapters.
"""

import json
import re
import sys
from pathlib import Path

import pymupdf

HERE = Path(__file__).resolve().parent
RUNNING_HEAD = "The Lloyd’s Register Foundation World Risk Poll Report 2019"


def letters(text):
    for ligature, plain in (("ﬀ", "ff"), ("ﬁ", "fi"), ("ﬂ", "fl")):
        text = text.replace(ligature, plain)
    return re.sub(r"[^a-z]", "", text.lower().replace("­", ""))


def main():
    key, pages = sys.argv[1], [int(a) for a in sys.argv[2:]]
    _, head, body = (HERE / "content" / f"{key}.md").read_text(encoding="utf-8").split("---", 2)
    meta = json.loads(head)
    doc = pymupdf.open(HERE.parent / ".cache" / "pdfs" / meta["pdf"])
    spans = list(zip(pages[::2], pages[1::2]))
    top, bottom = meta.get("margins", (0, 10000))       # page furniture above and below these lines is left out

    def page_text(page):
        # (a note mark in roman numerals, set small after a word, would read as letters of the text)
        out = []
        for block in page.get_text("dict")["blocks"]:
            if block["type"] != 0 or not top <= block["bbox"][1] <= bottom:
                continue
            for line in block["lines"]:
                size = max((s["size"] for s in line["spans"]), default=0)
                out.append("".join(s["text"] for s in line["spans"] if not (s["size"] < 0.7 * size and re.fullmatch(r"[ivx, ]+", s["text"].strip() or "-"))))
        return " ".join(out)

    source = letters(" ".join(page_text(doc[i]) for i in range(0, max(b for _, b in spans) + 1)))

    new, ours, sentences, missing, pictures = False, [meta.get("running_title", "")], 0, [], []
    for chunk in re.split(r"\n\s*\n", body.strip()):
        chunk = chunk.strip()
        if chunk.startswith("::new"):
            new = True
        elif chunk.startswith("::endnew"):
            new = False
        elif chunk.startswith("```chart"):
            spec = json.loads(chunk.split("\n", 1)[1].rsplit("```", 1)[0])
            ours.append(" ".join(str(spec.get(k, "")) for k in ("title", "subtitle", "question", "note")))
            if spec.get("kind") == "original":
                pictures.append((spec["page"], spec["clip"]))        # type inside a picture of the original is set, in the picture
            ours.append(f"{spec.get('note', '')} Poll question: {spec.get('question', '')}")        # (a report that sets its citation before the question)
            ours += [part.get("heading", "") for part in spec.get("parts", [])] + [name for name in spec.get("series", []) if isinstance(name, str)]
            ours += [row[0] for row in spec.get("rows", []) if spec.get("kind") == "line"]
            lists = [rows for _, rows in spec.get("lists", [])]         # ranked lists side by side: the original sets them row by row
            ours.append(" ".join(rows[k][0] for k in range(max(map(len, lists), default=0)) for rows in lists if k < len(rows)))
        elif chunk.startswith("```roll"):
            ours.append(" ".join(name for name, _ in json.loads(chunk.split("\n", 1)[1].rsplit("```", 1)[0])["names"]))
        elif chunk.startswith(("::chapter ", "::front ", "::back ", "::box ")):
            ours.append(chunk)                # a section's title, and the figure and caption on an opening page
        elif not new and not chunk.startswith("::"):
            ours.append(re.sub(r"\[\^[ivx]+\]", "", chunk))         # (without the marks of page notes, which the PDF's text is read without)
            if chunk.startswith("[^"):
                continue
            text = re.sub(r"^(#+ |>> |>-- |> |\^ |-- |- |\d+\. )", "", re.sub(r"\[\^\w+\]", "", chunk)).replace("**", "")
            for sentence in re.split(r"(?<=[.?!])\s+(?=[A-Z‘“])", text):
                sentences += 1
                if letters(sentence) and letters(sentence) not in source:
                    missing.append(sentence)
    print(f"{sentences} sentences in the content file; {len(missing)} not found in the PDF")
    for sentence in missing:
        print("   NOT IN PDF:", sentence[:160])

    content = letters(" ".join(ours))
    lost = []
    for first, last in spans:
        for index in range(first, last + 1):
            for block in doc[index].get_text("dict")["blocks"]:
                lines = block.get("lines", [])
                cx, cy = (block["bbox"][0] + block["bbox"][2]) / 2, (block["bbox"][1] + block["bbox"][3]) / 2
                if any(page == index and clip[0] <= cx <= clip[2] and clip[1] <= cy <= clip[3] for page, clip in pictures):
                    continue
                size = max((s["size"] for line in lines for s in line["spans"]), default=0)
                text = " ".join("".join(s["text"] for s in line["spans"] if not (s["size"] < 5 and size > 7 and re.fullmatch(r"[ivx, ]+", s["text"].strip() or "-")))
                                for line in lines)
                text = re.sub(r"^Survey questions?: |^(Chart|Table) \d+[a-z]?[.:]?\s+", "", text.strip())
                if len(letters(text)) < 40 or (size < 6.5 and not re.match(r"Notes?:|\*", text)) or text.startswith(RUNNING_HEAD) or "All rights reserved" in text or "  ||  " in text:
                    continue                      # chart labels, page furniture
                if not re.search(r"[.?!:;,]", text) and len(letters(text)) < 90:
                    continue                      # axis and key labels
                pieces = re.split(r"(?<=[.?!])\s+|\s*[•●]\s*", text)        # sentences, and the entries of a list
                found = sum(letters(part) in content for part in pieces if len(letters(part)) > 25)
                parts = sum(len(letters(part)) > 25 for part in pieces)
                if parts and found < parts:
                    lost.append((index, found, parts, text))
    print(f"{len(lost)} blocks of the PDF with text that is not in the content file")
    for index, found, parts, text in lost:
        print(f"   PDF page index {index}: {parts - found} of {parts} sentences missing: {text[:150]}")


if __name__ == "__main__":
    main()
