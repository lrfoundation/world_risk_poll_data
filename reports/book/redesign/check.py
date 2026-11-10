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
    return re.sub(r"[^a-z]", "", text.lower().replace("­", ""))


def main():
    key, pages = sys.argv[1], [int(a) for a in sys.argv[2:]]
    _, head, body = (HERE / "content" / f"{key}.md").read_text(encoding="utf-8").split("---", 2)
    meta = json.loads(head)
    doc = pymupdf.open(HERE.parent / ".cache" / "pdfs" / meta["pdf"])
    spans = list(zip(pages[::2], pages[1::2]))
    top, bottom = meta.get("margins", (0, 10000))       # page furniture above and below these lines is left out

    def page_text(page):
        return " ".join(b[4] for b in page.get_text("blocks") if top <= b[1] <= bottom and b[6] == 0)

    source = letters(" ".join(page_text(doc[i]) for i in range(0, max(b for _, b in spans) + 1)))

    new, ours, sentences, missing = False, [], 0, []
    for chunk in re.split(r"\n\s*\n", body.strip()):
        chunk = chunk.strip()
        if chunk.startswith("::new"):
            new = True
        elif chunk.startswith("::endnew"):
            new = False
        elif chunk.startswith("```chart"):
            spec = json.loads(chunk.split("\n", 1)[1].rsplit("```", 1)[0])
            ours.append(" ".join(str(spec.get(k, "")) for k in ("title", "subtitle", "question", "note")))
        elif not new and not chunk.startswith("::"):
            ours.append(chunk)
            if chunk.startswith("[^"):
                continue
            text = re.sub(r"^(#+ |> |- |\d+\. )", "", re.sub(r"\[\^\w+\]", "", chunk)).replace("**", "")
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
                text = " ".join("".join(s["text"] for s in line["spans"]) for line in lines)
                size = max((s["size"] for line in lines for s in line["spans"]), default=0)
                text = re.sub(r"^Survey questions?: ", "", text.strip())
                if len(letters(text)) < 40 or size < 6.5 or text.startswith(RUNNING_HEAD) or "All rights reserved" in text:
                    continue                      # chart labels, page furniture
                if not re.search(r"[.?!:;,]", text) and len(letters(text)) < 90:
                    continue                      # axis and key labels
                found = sum(letters(part) in content for part in re.split(r"(?<=[.?!])\s+", text) if len(letters(part)) > 25)
                parts = sum(len(letters(part)) > 25 for part in re.split(r"(?<=[.?!])\s+", text))
                if parts and found < parts:
                    lost.append((index, found, parts, text))
    print(f"{len(lost)} blocks of the PDF with text that is not in the content file")
    for index, found, parts, text in lost:
        print(f"   PDF page index {index}: {parts - found} of {parts} sentences missing: {text[:150]}")


if __name__ == "__main__":
    main()
