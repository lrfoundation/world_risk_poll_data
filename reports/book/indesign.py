"""Write an InDesign file (IDML) of a built book or report.

    python reports/book/indesign.py                                   # the coffee table book, from output/book.html
    python reports/book/indesign.py output/redesign/2019_risk_at_work.html

writes output/indesign/<name>/ with

    <name>.idml        the document: one page to a spread, the page size of the HTML
    Links/             the artwork the document places: one PDF of each page's
                       grounds, rules and blocks, and one PDF for each chart and map
    Document fonts/    the DM Sans files the text is set in

and zips the folder as output/indesign/<name>_indesign.zip.

How it works. The HTML is opened in Chrome three times. The first pass reads
the layout: every block of text with its position, type and colour, and every
chart. The second prints each page with that text and those charts left out,
which gives the page's artwork. The third prints each chart on its own. The
IDML then places the artwork at the back of each page, the charts over it, and
the text as live text frames with paragraph styles, so the words can be edited
in InDesign and the charts moved or replaced.

Text in a chart stays part of the chart's PDF. Blocks of text that follow one
another in a column are one story in one frame. InDesign breaks lines a little
differently from a browser, so frames grow with their text (auto-size, height
only) and a line may break at a different word.

Links are written as relative paths (Links/...). If InDesign reports them
missing on opening, use Links > Relink to Folder and choose the Links folder.

Needs PyMuPDF and a Chrome or Chromium. Build the HTML first (build.py).
"""

import json
import re
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape, quoteattr

import pymupdf

HERE = Path(__file__).resolve().parent
OUT = HERE / "output"
CACHE = HERE / ".cache"
NS = 'xmlns:idPkg="http://ns.adobe.com/AdobeInDesign/idml/1.0/packaging" DOMVersion="15.0"'
HEAD = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
STYLES = {400: "Regular", 500: "Medium", 600: "SemiBold", 700: "Bold", 800: "ExtraBold", 900: "Black"}
# SVG drawings that stay part of a page's artwork (they sit under other things, or are marks, not charts).
IN_ARTWORK = ".cover svg, .logo svg, svg.edge, .end svg"

# Runs in the page. MODE is "read" (leave the layout as JSON in the page), "art" (hide what was read) or "figs"
# (one page for each chart, with only the chart showing).
READER = r"""
(async () => {
  await document.fonts.ready;
  const ctx = document.createElement('canvas').getContext('2d');
  const parse = c => { const m = (c.match(/-?[\d.]+(e-?\d+)?/g) || [0, 0, 0, 0]).map(Number); return [m[0], m[1], m[2], m.length > 3 ? m[3] : 1]; };
  const shown = el => { const cs = getComputedStyle(el); return cs.display !== 'none' && cs.visibility !== 'hidden' && cs.opacity !== '0'; };
  const inline = el => ['inline', 'contents'].includes(getComputedStyle(el).display);
  const ground = el => {
    const stack = [];
    for (let e = el; e && e.nodeType === 1; e = e.parentElement) {
      const c = parse(getComputedStyle(e).backgroundColor);
      if (c[3] > 0) { stack.push(c); if (c[3] === 1) break; }
    }
    let base = [255, 255, 255];
    for (const c of stack.reverse()) base = base.map((b, i) => b * (1 - c[3]) + c[i] * c[3]);
    return base;
  };
  const ink = el => {
    const c = parse(getComputedStyle(el).color);
    let a = c[3];
    for (let e = el; e && e.nodeType === 1; e = e.parentElement) a *= parseFloat(getComputedStyle(e).opacity);
    if (a > 0.995) return c.slice(0, 3).map(Math.round);
    const g = ground(el);
    return c.slice(0, 3).map((v, i) => Math.round(v * a + g[i] * (1 - a)));
  };
  const styleOf = el => {
    const cs = getComputedStyle(el), size = parseFloat(cs.fontSize);
    let shift = 0;
    if (cs.verticalAlign === 'super') shift = size * 0.4; else if (cs.verticalAlign === 'sub') shift = -size * 0.2;
    else if (cs.verticalAlign.endsWith('px')) shift = parseFloat(cs.verticalAlign);
    return {font: cs.fontFamily.split(',')[0].replace(/["']/g, '').trim(), size, weight: parseInt(cs.fontWeight) || 400, italic: cs.fontStyle === 'italic',
            color: ink(el), track: cs.letterSpacing === 'normal' ? 0 : parseFloat(cs.letterSpacing), caps: cs.textTransform === 'uppercase', shift,
            pre: cs.whiteSpace.startsWith('pre')};
  };
  const ownText = el => {
    for (const n of el.childNodes) {
      if (n.nodeType === 3 && n.nodeValue.trim()) return true;
      if (n.nodeType === 1 && !(n instanceof SVGElement) && n.tagName !== 'BR' && shown(n) && inline(n) && n.textContent.trim()) return true;
    }
    return false;
  };
  const runs = (el, out) => {
    for (const n of el.childNodes) {
      if (n.nodeType === 3) out.push({t: n.nodeValue, s: styleOf(el)});
      else if (n.nodeType === 1) {
        if (n instanceof SVGElement || !shown(n)) continue;
        if (n.tagName === 'BR') { out.push({br: 1}); continue; }
        const block = !inline(n);
        if (block) out.push({br: 2});
        runs(n, out);
        if (block) out.push({br: 2});
      }
    }
    return out;
  };
  let figures = 0, parents = new Map();
  const metrics = el => {
    const cs = getComputedStyle(el);
    ctx.font = `${cs.fontStyle} ${cs.fontWeight} ${cs.fontSize} ${cs.fontFamily}`;
    const m = ctx.measureText('Hg');
    return [m.fontBoundingBoxAscent, m.fontBoundingBoxDescent];
  };
  const textNodes = root => {
    const out = [], it = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
    for (let n = it.nextNode(); n; n = it.nextNode()) if (n.nodeValue.trim() && !n.parentElement.closest('svg') && shown(n.parentElement)) out.push(n);
    return out;
  };
  const charBox = (node, last) => {
    const text = node.nodeValue, k = last ? text.length - 1 - text.split('').reverse().findIndex(c => c.trim()) : text.search(/\S/);
    const range = document.createRange();
    range.setStart(node, k);
    range.setEnd(node, k + 1);
    return range.getBoundingClientRect();
  };
  // el: the element that holds the text. within: the block it sits in, when el is only the inline part of that block.
  const block = (el, origin, within) => {
    el.classList.add('idml-text');
    const outer = within || el, cs = getComputedStyle(outer), r = outer.getBoundingClientRect();
    const pad = k => parseFloat(cs['padding' + k]) + parseFloat(cs['border' + k + 'Width']);
    const nodes = textNodes(el), rects = [];
    for (const node of nodes) {
      const range = document.createRange();
      range.selectNodeContents(node);
      rects.push(...[...range.getClientRects()].filter(q => q.width > 0.5 && q.height > 0.5));
    }
    if (!rects.length) return null;
    const tops = [];
    for (const q of rects) if (!tops.some(t => Math.abs(t - (q.top + q.bottom) / 2) < q.height * 0.6)) tops.push((q.top + q.bottom) / 2);
    const [asc, desc] = metrics(el);
    const own = getComputedStyle(el), lh = own.lineHeight === 'normal' ? asc + desc : parseFloat(own.lineHeight);
    const first = charBox(nodes[0], false), last = charBox(nodes[nodes.length - 1], true);
    const firstBase = first.top + metrics(nodes[0].parentElement)[0] - origin.top;
    const lastBase = last.bottom - metrics(nodes[nodes.length - 1].parentElement)[1] - origin.top;
    const tx0 = Math.min(...rects.map(q => q.left)) - origin.left, tx1 = Math.max(...rects.map(q => q.right)) - origin.left;
    let x = r.left + pad('Left') - origin.left, w = r.width - pad('Left') - pad('Right');
    let y = r.top + pad('Top') - origin.top, h = r.height - pad('Top') - pad('Bottom');
    if (within) { y = firstBase - asc; h = lastBase + desc - y; }
    if (!parents.has(outer.parentElement)) parents.set(outer.parentElement, parents.size);
    const align = {center: 'center', right: 'right', end: 'right', justify: 'justify'}[cs.textAlign] || 'left';
    return {kind: 'text', x, y, w, h, lh, align, lines: tops.length, parent: within ? -1 : parents.get(outer.parentElement),
            first: firstBase, last: lastBase, desc, tx0, tx1, indent: first.left - origin.left - x,
            cols: Math.round((tx1 - tx0) / Math.max(w, 1) + 0.35),
            tag: el.tagName.toLowerCase(), cls: (within || el).className.replace('idml-text', '').trim(), base: styleOf(el), runs: runs(el, [])};
  };
  const walk = (el, origin, items) => {
    if (el instanceof SVGElement) {
      if (el.tagName.toLowerCase() !== 'svg' || el.matches(IN_ARTWORK) || !shown(el)) return;
      const r = el.getBoundingClientRect();
      if (r.width < 2 || r.height < 2) return;
      el.classList.add('idml-fig');
      el.dataset.idml = figures;
      const x0 = Math.max(0, r.left - origin.left), y0 = Math.max(0, r.top - origin.top);
      const x1 = Math.min(origin.width, r.right - origin.left), y1 = Math.min(origin.height, r.bottom - origin.top);
      items.push({kind: 'fig', n: figures++, x: x0, y: y0, w: x1 - x0, h: y1 - y0, label: el.getAttribute('aria-label') || ''});
      return;
    }
    if (!shown(el)) return;
    if (!ownText(el)) { for (const c of [...el.children]) walk(c, origin, items); return; }
    const isBlock = n => n.nodeType === 1 && (n instanceof SVGElement || (n.tagName !== 'BR' && shown(n) && !inline(n) && (n.textContent.trim() || n.querySelector('svg'))));
    if (![...el.childNodes].some(isBlock)) { const b = block(el, origin); if (b) items.push(b); return; }
    // Text and blocks side by side in one element: each run of text between the blocks is set on its own.
    let group = [];
    const flush = () => {
      if (group.some(n => n.textContent.trim())) {
        const span = document.createElement('span');
        group[0].before(span);
        group.forEach(n => span.appendChild(n));
        const b = block(span, origin, el);
        if (b) items.push(b);
      }
      group = [];
    };
    for (const n of [...el.childNodes]) {
      if (isBlock(n)) { flush(); walk(n, origin, items); }
      else if (n.nodeType === 3 || (n.nodeType === 1 && shown(n))) group.push(n);
    }
    flush();
  };
  const sections = [...document.querySelectorAll('.page')];
  const pages = sections.map(section => {
    const origin = section.getBoundingClientRect(), items = [];
    walk(section, origin, items);
    return {w: origin.width, h: origin.height, items};
  });
  const css = document.createElement('style');
  if (MODE === 'read') {
    const holder = document.createElement('script');
    holder.type = 'application/json';
    holder.id = 'idml-data';
    holder.textContent = JSON.stringify(pages).replace(/</g, '\\u003c');
    document.body.appendChild(holder);
  } else if (MODE === 'art') {
    css.textContent = '.idml-text, .idml-text * { -webkit-text-fill-color: transparent !important; text-shadow: none !important; text-decoration-color: transparent !important; }'
      + '.idml-text::before, .idml-text::after, .idml-text *::before, .idml-text *::after { -webkit-text-fill-color: currentcolor !important; }'
      + 'svg.idml-fig { visibility: hidden !important; }';
  } else {
    const made = [];
    sections.forEach(section => {
      for (const svg of section.querySelectorAll('svg.idml-fig')) {
        const copy = section.cloneNode(true);
        copy.querySelector(`svg[data-idml="${svg.dataset.idml}"]`).classList.add('idml-keep');
        made.push(copy);
      }
    });
    sections.forEach(section => section.remove());
    made.forEach(copy => document.body.appendChild(copy));
    css.textContent = '.page { background: none !important; } .page::before, .page::after { display: none !important; }'
      + '.page * { visibility: hidden !important; } .page svg.idml-keep, .page svg.idml-keep * { visibility: visible !important; }';
  }
  document.head.appendChild(css);
  document.documentElement.dataset.idml = 'done';
})();
"""


def chrome():
    names = ["google-chrome", "chromium", "chromium-browser", "chrome", "msedge"]
    browser = next((shutil.which(n) for n in names if shutil.which(n)), None)
    if not browser:
        sys.exit("No Chrome, Chromium or Edge found")
    return [browser, "--headless=new", "--no-sandbox", "--disable-gpu", "--no-pdf-header-footer", "--virtual-time-budget=30000"]


def with_reader(html, mode):
    script = f"<script>const MODE = {json.dumps(mode)}, IN_ARTWORK = {json.dumps(IN_ARTWORK)};{READER}</script>"
    return html.replace("</body>", script + "</body>")


def read_layout(html_path, work):
    """The three passes: (pages of the layout, the artwork PDF, the PDF of charts)."""
    html = html_path.read_text(encoding="utf-8")
    paths = {}
    for mode in ("read", "art", "figs"):
        paths[mode] = work / f"_{mode}.html"
        paths[mode].write_text(with_reader(html, mode), encoding="utf-8")
    dom = subprocess.run(chrome() + ["--dump-dom", paths["read"].as_uri()], check=True, capture_output=True).stdout.decode("utf-8")
    data = re.search(r'<script type="application/json" id="idml-data">(.*?)</script>', dom, re.S)
    if not data:
        sys.exit("the layout could not be read from the page")
    pages = json.loads(data.group(1))
    pdfs = {}
    for mode in ("art", "figs"):
        pdfs[mode] = work / f"_{mode}.pdf"
        subprocess.run(chrome() + [f"--print-to-pdf={pdfs[mode]}", paths[mode].as_uri()], check=True, capture_output=True)
    return pages, pymupdf.open(pdfs["art"]), pymupdf.open(pdfs["figs"])


# ---------------------------------------------------------------- text

def paragraphs(block):
    """A block's runs as paragraphs: [[(text, style)]], white space collapsed as the browser does."""
    out, line = [], []
    for run in block["runs"]:
        if "br" in run:
            if run["br"] == 2:
                if line:
                    out.append(line)
                line = []
            elif line:
                line.append((" ", line[-1][1]))
            continue
        text = run["t"] if run["s"]["pre"] else re.sub(r"\s+", " ", run["t"])
        if run["s"]["pre"]:
            text = text.replace("\n", " ")
        if not line or line[-1][0].endswith((" ", " ")):
            text = text.lstrip(" ")
        if text:
            line.append((text, run["s"]))
    if line:
        out.append(line)
    cleaned = []
    for line in out:
        line[-1] = (line[-1][0].rstrip(" "), line[-1][1])
        line = [(t, s) for t, s in line if t]
        if line:
            cleaned.append(line)
    return cleaned


def stories(items):
    """Text blocks that follow one another down a column become one story; the rest stay on their own."""
    out = []
    for item in items:
        if item["kind"] != "text":
            out.append(item)
            continue
        paras = paragraphs(item)
        if not paras:
            continue
        entry = dict(item, paras=[dict(runs=p, lh=item["lh"], align=item["align"], before=0, tag=item["tag"], cls=item["cls"]) for p in paras])
        if item["indent"] > 1 and item["align"] == "left":
            # the text starts after a mark that is drawn with the artwork (a tick, a swatch of a key)
            entry["paras"][0]["LeftIndent" if item["lines"] <= 1 else "FirstLineIndent"] = round(item["indent"], 2)
        last = out[-1] if out and out[-1]["kind"] == "text" else None
        gap = item["first"] - last["last"] - item["lh"] if last else 0
        if (last and last["parent"] == item["parent"] and abs(last["x"] - item["x"]) < 1.5 and abs(last["w"] - item["w"]) < 1.5
                and item["y"] >= last["y"] + last["h"] - 1 and gap < 90 and last["cols"] == 1 and item["cols"] == 1):
            entry["paras"][0]["before"] = max(0, round(gap, 2))
            last["paras"] += entry["paras"]
            last["h"] = item["y"] + item["h"] - last["y"]
            last["last"] = item["last"]
            last["lines"] += item["lines"]
            last["desc"] = item["desc"]
            last["tx0"], last["tx1"] = min(last["tx0"], item["tx0"]), max(last["tx1"], item["tx1"])
        else:
            out.append(entry)
    return out


class Document:
    def __init__(self, name, pages, art, figs, folder):
        self.name, self.pages, self.art, self.figs, self.folder = name, pages, art, figs, folder
        self.width, self.height = pages[0]["w"], pages[0]["h"]
        self.colours, self.styles, self.stories, self.spreads, self.count, self.used_fonts = {}, {}, [], [], 0, set()
        (folder / "Links").mkdir(parents=True, exist_ok=True)

    def uid(self, prefix):
        self.count += 1
        return f"{prefix}{self.count:x}"

    def colour(self, rgb):
        key = tuple(int(v) for v in rgb)
        if key not in self.colours:
            self.colours[key] = f"Color/RGB {key[0]} {key[1]} {key[2]}"
        return self.colours[key]

    # ---- styles

    def font_style(self, s):
        weight = min(STYLES, key=lambda w: abs(w - s["weight"]))
        name = STYLES[weight]
        if s["italic"]:
            name = "Italic" if name == "Regular" else name + " Italic"
        return name

    def para_style(self, para):
        """The paragraph style for a paragraph, named after the type it sets: made the first time it is needed."""
        s = max(para["runs"], key=lambda r: len(r[0]))[1]          # the type most of the paragraph is set in
        key = (s["font"], round(s["size"], 2), self.font_style(s), tuple(s["color"]), round(para["lh"], 2), s["caps"], round(s["track"], 2), para["align"])
        if key not in self.styles:
            colour = "%02X%02X%02X" % tuple(s["color"])
            name = f'{key[1]:g} on {key[4]:g} {key[2]} {colour}' + (" caps" if s["caps"] else "") + ("" if para["align"] == "left" else " " + para["align"])
            self.styles[key] = dict(id=f"ParagraphStyle/{name}", name=name, s=s, lh=para["lh"], align=para["align"])
        return self.styles[key], s

    @staticmethod
    def char_attrs(s, doc):
        tracking = round(s["track"] / s["size"] * 1000) if s["size"] else 0
        doc.used_fonts.add((s["font"], doc.font_style(s)))
        return dict(FontStyle=doc.font_style(s), PointSize=f'{s["size"]:g}', FillColor=doc.colour(s["color"]), Tracking=str(tracking),
                    Capitalization="AllCaps" if s["caps"] else "Normal", BaselineShift=f'{s["shift"]:g}'), s["font"]

    def story(self, entry):
        sid = self.uid("st")
        align = dict(left="LeftAlign", center="CenterAlign", right="RightAlign", justify="LeftJustified")
        out = [f'{HEAD}<idPkg:Story {NS}><Story Self="{sid}" AppliedTOCStyle="n" TrackChanges="false" StoryTitle="$ID/" AppliedNamedGrid="n">',
               '<StoryPreference OpticalMarginAlignment="false" OpticalMarginSize="12" FrameType="TextFrameType" StoryOrientation="Horizontal" StoryDirection="LeftToRightDirection"/>']
        for k, para in enumerate(entry["paras"]):
            style, main = self.para_style(para)
            base, base_font = self.char_attrs(main, self)
            before = f' SpaceBefore="{para["before"]:g}"' if para["before"] else ""
            before += "".join(f' {k}="{para[k]:g}"' for k in ("LeftIndent", "FirstLineIndent") if para.get(k))
            out.append(f'<ParagraphStyleRange AppliedParagraphStyle={quoteattr(style["id"])}{before}>')
            for n, (text, s) in enumerate(para["runs"]):
                attrs, font = self.char_attrs(s, self)
                local = "".join(f" {a}={quoteattr(v)}" for a, v in attrs.items() if v != base[a])
                props = f'<Properties><AppliedFont type="string">{escape(font)}</AppliedFont></Properties>' if font != base_font else ""
                end = "<Br/>" if n == len(para["runs"]) - 1 and k < len(entry["paras"]) - 1 else ""
                out.append(f'<CharacterStyleRange AppliedCharacterStyle="CharacterStyle/$ID/[No character style]"{local}>{props}'
                           f"<Content>{escape(text)}</Content>{end}</CharacterStyleRange>")
            out.append("</ParagraphStyleRange>")
        out.append("</Story></idPkg:Story>")
        self.stories.append((sid, "".join(out)))
        return sid

    # ---- page items

    @staticmethod
    def path(x0, y0, x1, y1):
        points = "".join(f'<PathPointType Anchor="{x:.3f} {y:.3f}" LeftDirection="{x:.3f} {y:.3f}" RightDirection="{x:.3f} {y:.3f}"/>'
                         for x, y in ((x0, y0), (x0, y1), (x1, y1), (x1, y0)))
        return f'<Properties><PathGeometry><GeometryPathType PathOpen="false"><PathPointArray>{points}</PathPointArray></GeometryPathType></PathGeometry></Properties>'

    def placed(self, link, label, x, y, w, h):
        """A frame holding a linked PDF, at x, y on the page (the spread's origin is the middle of the page)."""
        x, top = x - self.width / 2, y - self.height / 2
        return (f'<Rectangle Self="{self.uid("rc")}" ContentType="GraphicType" Name={quoteattr(label)} ItemLayer="layer1" Visible="true" FillColor="Swatch/None" '
                f'StrokeColor="Swatch/None" StrokeWeight="0" AppliedObjectStyle="ObjectStyle/$ID/[None]" ItemTransform="1 0 0 1 0 0">'
                f'{self.path(x, top, x + w, top + h)}'
                f'<PDF Self="{self.uid("pd")}" ItemTransform="1 0 0 1 {x:.3f} {top:.3f}"><Properties><GraphicBounds Left="0" Top="0" Right="{w:.3f}" Bottom="{h:.3f}"/></Properties>'
                '<PDFAttribute PageNumber="1" PDFCrop="CropMedia" TransparentBackground="true"/>'
                f'<Link Self="{self.uid("ln")}" LinkResourceURI={quoteattr("file:Links/" + link)} LinkResourceFormat="$ID/Adobe Portable Document Format (PDF)" '
                'StoredState="Normal" LinkClassID="35906" LinkClientID="257" LinkResourceModified="false" LinkObjectModified="false" ShowInUI="true" '
                'CanEmbed="true" CanUnembed="true" CanPackage="true" ImportPolicy="NoAutoImport" ExportPolicy="NoAutoExport"/></PDF></Rectangle>')

    def frame(self, entry):
        sid = self.story(entry)
        x0, x1 = entry["x"], entry["x"] + entry["w"]
        if entry["lines"] <= len(entry["paras"]):
            # Lines that do not wrap in the browser must not wrap in InDesign either: give them room on the open side.
            slack = (entry["tx1"] - entry["tx0"]) * 0.1 + 6
            align = entry["paras"][0]["align"]
            x0, x1 = min(x0, entry["tx0"]), max(x1, entry["tx1"])
            if align == "left":
                x1 += slack
            elif align == "right":
                x0 -= slack
            else:
                x0, x1 = x0 - slack / 2, x1 + slack / 2
        x0, x1 = x0 - self.width / 2, x1 - self.width / 2
        top = entry["first"] - entry["paras"][0]["lh"] - self.height / 2
        bottom = max(entry["y"] + entry["h"], entry["last"] + entry["desc"] + 2) - self.height / 2
        label = (entry["cls"] or entry["tag"])[:60]
        return (f'<TextFrame Self="{self.uid("tf")}" ParentStory="{sid}" PreviousTextFrame="n" NextTextFrame="n" ContentType="TextType" Name={quoteattr(label)} '
                'ItemLayer="layer1" Visible="true" FillColor="Swatch/None" StrokeColor="Swatch/None" StrokeWeight="0" '
                f'AppliedObjectStyle="ObjectStyle/$ID/[None]" ItemTransform="1 0 0 1 0 0">{self.path(x0, top, x1, bottom)}'
                '<TextFramePreference TextColumnCount="1" FirstBaselineOffset="LeadingOffset" AutoSizingType="HeightOnly" AutoSizingReferencePoint="TopLeftPoint" '
                'UseNoLineBreaksForAutoSizing="false" VerticalJustification="TopAlign"><Properties><InsetSpacing type="list"><ListItem type="unit">0</ListItem>'
                '<ListItem type="unit">0</ListItem><ListItem type="unit">0</ListItem><ListItem type="unit">0</ListItem></InsetSpacing></Properties>'
                '</TextFramePreference></TextFrame>')

    def link_pdf(self, src, index, clip, name):
        """One page (or part of one) of a Chrome PDF as a link at the document's scale: Chrome prints a CSS pixel as 0.75 pt."""
        page = src[index]
        scale = page.rect.width / self.width
        x, y, w, h = clip
        out = pymupdf.open()
        out.new_page(width=w, height=h).show_pdf_page(pymupdf.Rect(0, 0, w, h), src, index,
                                                       clip=pymupdf.Rect(x * scale, y * scale, (x + w) * scale, (y + h) * scale))
        out.save(self.folder / "Links" / name, garbage=3, deflate=True)
        out.close()

    def build(self):
        fig_page = 0
        for number, page in enumerate(self.pages, 1):
            art = f"page_{number:03d}_artwork.pdf"
            self.link_pdf(self.art, number - 1, (0, 0, self.width, self.height), art)
            items = [self.placed(art, f"Page {number} artwork", 0, 0, self.width, self.height)]
            for entry in stories(page["items"]):
                if entry["kind"] == "fig":
                    name = f'page_{number:03d}_figure_{entry["n"] + 1:03d}.pdf'
                    self.link_pdf(self.figs, fig_page, (entry["x"], entry["y"], entry["w"], entry["h"]), name)
                    fig_page += 1
                    items.append(self.placed(name, entry["label"][:80] or f'Figure {entry["n"] + 1}', entry["x"], entry["y"], entry["w"], entry["h"]))
                else:
                    items.append(self.frame(entry))
            sid = self.uid("sp")
            self.spreads.append((sid, (
                f'{HEAD}<idPkg:Spread {NS}><Spread Self="{sid}" PageCount="1" BindingLocation="0" AllowPageShuffle="true" ShowMasterItems="true" '
                f'FlattenerOverride="Default" PageTransitionType="None" ItemTransform="1 0 0 1 0 {(number - 1) * (self.height + 120):g}">'
                f'<Page Self="{self.uid("pg")}" Name="{number}" GeometricBounds="0 0 {self.height:g} {self.width:g}" ItemTransform="1 0 0 1 {-self.width / 2:g} {-self.height / 2:g}" '
                'AppliedMaster="n" MasterPageTransform="1 0 0 1 0 0" UseMasterGrid="true" GridStartingPoint="TopOutside" OverrideList="" TabOrder="">'
                f'<MarginPreference ColumnCount="1" ColumnGutter="12" Top="0" Bottom="0" Left="0" Right="0" ColumnDirection="Horizontal" ColumnsPositions="0 {self.width:g}"/>'
                f'</Page>{"".join(items)}</Spread></idPkg:Spread>')))
        assert fig_page == len(self.figs), (fig_page, len(self.figs))

    # ---- the package

    def graphic(self):
        colours = "".join(f'<Color Self={quoteattr(cid)} Model="Process" Space="RGB" ColorValue="{r} {g} {b}" ColorOverride="Normal" '
                          f'Name={quoteattr(cid.split("/", 1)[1])} ColorEditable="true" ColorRemovable="true" Visible="true"/>'
                          for (r, g, b), cid in self.colours.items())
        return (f'{HEAD}<idPkg:Graphic {NS}>'
                '<Color Self="Color/Black" Model="Process" Space="CMYK" ColorValue="0 0 0 100" ColorOverride="Specialblack" Name="Black" ColorEditable="false" ColorRemovable="false" Visible="true"/>'
                '<Color Self="Color/Paper" Model="Process" Space="CMYK" ColorValue="0 0 0 0" ColorOverride="Specialpaper" Name="Paper" ColorEditable="true" ColorRemovable="false" Visible="true"/>'
                f'{colours}<Swatch Self="Swatch/None" Name="None" ColorEditable="false" ColorRemovable="false" Visible="true"/>'
                '<StrokeStyle Self="StrokeStyle/$ID/Solid" Name="$ID/Solid"/></idPkg:Graphic>')

    def styles_xml(self):
        align = dict(left="LeftAlign", center="CenterAlign", right="RightAlign", justify="LeftJustified")
        out = []
        for style in sorted(self.styles.values(), key=lambda st: (-st["s"]["size"], st["name"])):
            attrs, font = self.char_attrs(style["s"], self)
            attrs.pop("BaselineShift")
            text = "".join(f" {a}={quoteattr(v)}" for a, v in attrs.items())
            out.append(f'<ParagraphStyle Self={quoteattr(style["id"])} Name={quoteattr(style["name"])} Imported="false" NextStyle={quoteattr(style["id"])} '
                       f'Justification="{align[style["align"]]}" Hyphenation="false"{text}><Properties><BasedOn type="string">$ID/[No paragraph style]</BasedOn>'
                       f'<AppliedFont type="string">{escape(font)}</AppliedFont><Leading type="unit">{style["lh"]:g}</Leading></Properties></ParagraphStyle>')
        return (f'{HEAD}<idPkg:Styles {NS}>'
                '<RootCharacterStyleGroup Self="rootcharacter"><CharacterStyle Self="CharacterStyle/$ID/[No character style]" Imported="false" Name="$ID/[No character style]"/></RootCharacterStyleGroup>'
                '<RootParagraphStyleGroup Self="rootparagraph"><ParagraphStyle Self="ParagraphStyle/$ID/[No paragraph style]" Name="$ID/[No paragraph style]" Imported="false" '
                'FillColor="Color/Black" FontStyle="Regular" PointSize="12" Justification="LeftAlign"><Properties><Leading type="enumeration">Auto</Leading>'
                '<AppliedFont type="string">DM Sans</AppliedFont></Properties></ParagraphStyle>'
                '<ParagraphStyle Self="ParagraphStyle/$ID/NormalParagraphStyle" Name="$ID/NormalParagraphStyle" Imported="false" NextStyle="ParagraphStyle/$ID/NormalParagraphStyle">'
                '<Properties><BasedOn type="string">$ID/[No paragraph style]</BasedOn></Properties></ParagraphStyle>'
                f'{"".join(out)}</RootParagraphStyleGroup>'
                '<RootObjectStyleGroup Self="rootobject"><ObjectStyle Self="ObjectStyle/$ID/[None]" Name="$ID/[None]"/></RootObjectStyleGroup></idPkg:Styles>')

    def fonts_xml(self):
        """The faces the text uses, by family and style, with the PostScript names of the files in Document fonts."""
        used = {}
        for style in self.used_fonts:
            used.setdefault(style[0], set()).add(style[1])
        out = []
        for k, (family, names) in enumerate(sorted(used.items())):
            faces = ""
            for name in sorted(names):
                post = family.replace(" ", "") + "-" + name.replace(" ", "")
                faces += (f'<Font Self={quoteattr(f"di{k}Fontn{family} {name}")} FontFamily={quoteattr(family)} Name={quoteattr(f"{family} {name}")} '
                          f'PostScriptName={quoteattr(post)} Status="Installed" FontStyleName={quoteattr(name)} FontType="TrueType" WritingScript="0" '
                          f'FullName={quoteattr(f"{family} {name}")} FullNameNative={quoteattr(f"{family} {name}")} FontStyleNameNative={quoteattr(name)} PlatformName="$ID/" Version="Version 4.004"/>')
            out.append(f'<FontFamily Self="di{k}" Name={quoteattr(family)}>{faces}</FontFamily>')
        return f'{HEAD}<idPkg:Fonts {NS}>{"".join(out)}</idPkg:Fonts>'

    def preferences(self):
        return (f'{HEAD}<idPkg:Preferences {NS}>'
                f'<DocumentPreference PageHeight="{self.height:g}" PageWidth="{self.width:g}" PagesPerDocument="{len(self.pages)}" FacingPages="false" '
                'DocumentBleedTopOffset="0" DocumentBleedBottomOffset="0" DocumentBleedInsideOrLeftOffset="0" DocumentBleedOutsideOrRightOffset="0" '
                'PageBinding="LeftToRight" ColumnDirection="Horizontal" Intent="PrintIntent"/>'
                '<MarginPreference ColumnCount="1" ColumnGutter="12" Top="0" Bottom="0" Left="0" Right="0" ColumnDirection="Horizontal"/>'
                '<ViewPreference HorizontalMeasurementUnits="Points" VerticalMeasurementUnits="Points" RulerOrigin="PageOrigin"/></idPkg:Preferences>')

    def designmap(self):
        story_list = " ".join(sid for sid, _ in self.stories)
        parts = [f'{HEAD}<?aid style="50" type="document" readerVersion="6.0" featureSet="257" product="15.0(0)" ?>\n'
                 f'<Document {NS} Self="d" StoryList="{story_list}" Name={quoteattr(self.name)} ZeroPoint="0 0" ActiveLayer="layer1">',
                 '<idPkg:Graphic src="Resources/Graphic.xml"/><idPkg:Fonts src="Resources/Fonts.xml"/><idPkg:Styles src="Resources/Styles.xml"/><idPkg:Preferences src="Resources/Preferences.xml"/>',
                 '<Layer Self="layer1" Name="Pages" Visible="true" Locked="false" IgnoreWrap="false" ShowGuides="true" LockGuides="false" UI="true" Expendable="true" Printable="true">'
                 '<Properties><LayerColor type="enumeration">LightBlue</LayerColor></Properties></Layer>']
        parts += [f'<idPkg:Spread src="Spreads/Spread_{sid}.xml"/>' for sid, _ in self.spreads]
        parts += [f'<idPkg:Story src="Stories/Story_{sid}.xml"/>' for sid, _ in self.stories]
        parts.append("</Document>")
        return "".join(parts)

    def write(self):
        self.build()
        path = self.folder / f"{self.name}.idml"
        with zipfile.ZipFile(path, "w") as z:
            z.writestr(zipfile.ZipInfo("mimetype"), "application/vnd.adobe.indesign-idml-package", compress_type=zipfile.ZIP_STORED)
            files = {"designmap.xml": self.designmap(), "Resources/Graphic.xml": self.graphic(), "Resources/Styles.xml": self.styles_xml(),
                     "Resources/Preferences.xml": self.preferences(), "Resources/Fonts.xml": self.fonts_xml(),
                     "META-INF/container.xml": HEAD + '<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container"><rootfiles>'
                                                      '<rootfile full-path="designmap.xml" media-type="text/xml"/></rootfiles></container>'}
            files.update({f"Spreads/Spread_{sid}.xml": xml for sid, xml in self.spreads})
            files.update({f"Stories/Story_{sid}.xml": xml for sid, xml in self.stories})
            for name, xml in files.items():
                z.writestr(name, xml.encode("utf-8"), compress_type=zipfile.ZIP_DEFLATED)
        return path


def main():
    html_path = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else OUT / "book.html"
    name = "World_Risk_Poll_22_reports" if html_path.name == "book.html" else html_path.stem
    folder = OUT / "indesign" / name
    if folder.exists():
        shutil.rmtree(folder)
    work = OUT / "indesign" / "_work"
    work.mkdir(parents=True, exist_ok=True)
    pages, art, figs = read_layout(html_path, work)
    doc = Document(name, pages, art, figs, folder)
    path = doc.write()
    fonts = folder / "Document fonts"
    fonts.mkdir(exist_ok=True)
    for ttf in sorted(CACHE.glob("DMSans-*.ttf")):
        if re.fullmatch(r"DMSans-(italic-)?\d+\.ttf", ttf.name):
            shutil.copy(ttf, fonts / ttf.name)
    (folder / "READ ME.txt").write_text(
        f"{name}.idml opens in InDesign 2020 or later.\n\n"
        "Text is live and carries paragraph styles named after the type they set. Each page's grounds, rules and blocks are one placed PDF\n"
        "at the back of the page (Links/page_NNN_artwork.pdf), and each chart or map is a placed PDF of its own.\n\n"
        "If InDesign reports missing links, choose Links > Relink to Folder and pick the Links folder beside the IDML.\n"
        "The text is set in DM Sans; the files are in Document fonts.\n", encoding="utf-8")
    archive = shutil.make_archive(str(OUT / "indesign" / f"{name}_indesign"), "zip", folder.parent, folder.name)
    frames = sum(xml.count("<TextFrame ") for _, xml in doc.spreads)
    print(f"{len(pages)} pages, {frames} text frames, {len(doc.styles)} paragraph styles, {len(figs)} charts -> {path}\n{archive}")


if __name__ == "__main__":
    main()
