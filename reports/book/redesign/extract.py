"""Draft the text of a published report from its PDF, ready to be checked by hand.

    python reports/book/redesign/extract.py 2019 87 111 > draft.md

The draft uses the markup that build.py reads (see README.md). It keeps the
published wording: lines are joined into paragraphs, footnote markers become
[^n], and chart captions become [chart n] lines. Chart contents are left out,
because charts are redrawn from published_figures.csv. Every draft needs a
read-through against the PDF: reading order and paragraph joins are guesses.

One function per report family, since each family set its type differently.
"""

import re
import sys
from pathlib import Path

import pymupdf

PDFS = Path(__file__).resolve().parent.parent / ".cache" / "pdfs"


def classify_2019(font, size, colour):
    if font.startswith("Calmetta") and size >= 20:
        return "title"
    if font.startswith("SourceSansPro-Bold") and "Italic" not in font and size >= 13:
        return "h1" if colour == 0x3B8EDF else "box"
    if "BoldItalic" in font and size >= 10.5:
        return "lead"
    if font.startswith("SourceSansPro-Bold") and 10.5 <= size < 13:
        return "h2"
    if font.startswith("Calmetta") and 8.5 <= size <= 10.5:
        return "chart"
    if font.startswith("SourceSansPro") and "Italic" in font and size <= 8.5:
        return "note"
    if font.startswith("AktivGrotesk"):
        return "fn"
    if font.startswith("SourceSansPro") and 9.8 <= size <= 10.2 and colour == 0x2D2A26:
        return "p"
    return None


def block_text(block, body_size):
    """A block's text, with superscript figures turned into [^n] markers."""
    lines = []
    for line in block["lines"]:
        parts = []
        for span in line["spans"]:
            text = span["text"]
            small = span["size"] < body_size * 0.75
            if body_size and small and re.fullmatch(r"\s*[\d,\s]+\s*", text) and text.strip():
                text = "".join(f"[^{n}]" for n in re.findall(r"\d+", text))
            parts.append(text)
        lines.append("".join(parts).strip())
    text = " ".join(line for line in lines if line)
    text = text.replace("\t", " ").replace("\x07", " ").replace("\u00ad", "")
    return re.sub(r"\s+", " ", text).strip()


def page_blocks(page, classify, top=60, bottom=800, middle=270):
    """Classified text blocks of a page in reading order."""
    found = []
    for block in page.get_text("dict")["blocks"]:
        if "lines" not in block:
            continue
        spans = [s for line in block["lines"] for s in line["spans"] if s["text"].strip()]
        if not spans:
            continue
        main = max(spans, key=lambda s: len(s["text"]))
        kind = classify(main["font"], round(main["size"], 1), main["color"])
        x0, y0, x1, y1 = block["bbox"]
        if not kind or y0 < top or y0 > bottom:
            continue
        body = main["size"] if kind in ("p", "lead", "h1", "h2", "box") else 0
        found.append(dict(kind=kind, text=block_text(block, body), x0=x0, y0=y0, x1=x1, wide=x1 - x0 > 300))
    # Bands: a full-width block ends the two-column band above it.
    found.sort(key=lambda b: b["y0"])
    ordered, band = [], []

    def flush():
        ordered.extend(sorted(band, key=lambda b: (b["x0"] >= middle, b["y0"])))
        band.clear()

    for b in found:
        if b["wide"] and b["x0"] < middle:
            flush()
            ordered.append(b)
        else:
            band.append(b)
    flush()
    return ordered


def split_footnotes(text, expected):
    """Split a footnote block into (number, text), given the next expected number."""
    notes, rest = [], text
    while True:
        m = re.match(rf"{expected}\s+", rest)
        if not m:
            break
        rest = rest[m.end():]
        nxt = re.search(rf"(?<=[\s/]){expected + 1}\s+(?=\S)", rest)
        body, rest = (rest[:nxt.start()], rest[nxt.start():]) if nxt else (rest, "")
        notes.append((expected, body.strip()))
        expected += 1
    return notes, expected


def draft(doc, first, last, classify=classify_2019):
    out, notes, expected = [], [], None
    for index in range(first, last + 1):
        out.append(f"<!-- page {doc[index].get_label() or index + 1} -->")
        for b in page_blocks(doc[index], classify):
            kind, text = b["kind"], b["text"]
            if kind == "fn":
                if expected is None:
                    expected = int(re.match(r"\d+", text).group())
                got, expected = split_footnotes(text, expected)
                notes += got
            elif kind == "title":
                out.append(f"<!-- title: {text} -->")
            elif kind == "h1":
                out.append(f"# {text}")
            elif kind in ("h2", "box"):
                out.append(f"## {text}")
            elif kind == "lead":
                out.append(f"> {text}")
            elif kind == "chart":
                m = re.fullmatch(r"(Chart|Table) (\d+\.\d+)", text)
                if m:
                    out.append(f"[{m.group(1).lower()} {m.group(2)}]")
                elif out and out[-1].startswith(("[chart", "[table")) and not re.fullmatch(r"[\d\s.%]+", text):
                    out[-1] += f" {text}"
            elif kind == "note":
                out.append(f"<!-- note: {text} -->")
            elif text.startswith("•"):
                out.append("- " + text.lstrip("• ").strip())
            else:
                previous = next((o for o in reversed(out) if not o.startswith("<!--")), "")
                unfinished = previous and not previous.startswith(("#", ">", "[", "-")) and not re.search(r"[.!?:’”'\")](\[\^\d+\])*$", previous)
                if unfinished and text[:1].islower():
                    at = len(out) - 1 - next(i for i, o in enumerate(reversed(out)) if not o.startswith("<!--"))
                    out[at] += " " + text
                else:
                    out.append(text)
    out.append("")
    out += [f"[^{n}]: {text}" for n, text in notes]
    return "\n\n".join(out) + "\n"


if __name__ == "__main__":
    year, first, last = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
    name = {"2019": "core_world_risk_poll_2019.pdf"}[year]
    sys.stdout.write(draft(pymupdf.open(PDFS / name), first, last))
