"""Charts for the book, drawn as SVG to the World Risk Poll 2026 chart rules.

The rules come from wrp_style.py as recorded in the brand notes: DM Sans, ink
text, axis lines on the left and bottom only, dotted grey gridlines at the
labelled values, bars with a rounded free end and a white gap between
neighbours, the key above the plot with square swatches rounded on the left,
value labels in the heaviest weight, and no title inside the image. Sizes are
scaled up from the report figures because the charts are placed larger here.
Value labels take the series colour where that colour is dark enough to read
(fuchsia, green, navy, purple, red) and ink otherwise.
"""

from html import escape

INK, GRID = "#231F20", "#BDBDBD"
DARK = {"#E3076E", "#00785C", "#0D2240", "#7B50DE", "#BF153D"}
FS = 22          # category and key text
FS_AXIS = 20     # value axis
FS_VALUE = 24    # value labels


def luminance(colour):
    """Relative luminance of a #RRGGBB colour, 0 (black) to 1 (white)."""
    parts = [int(colour[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    r, g, b = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in parts]
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def is_dark(colour):
    return colour.upper() in DARK or luminance(colour) < 0.2


def text_on(colour):
    """Text colour for a label printed on top of a fill."""
    return "#FFFFFF" if is_dark(colour) else INK


def label_colour(colour):
    """Value labels take the series colour only where it passes contrast on white."""
    return colour if is_dark(colour) else INK


def width_of(text, size, bold=False):
    return len(text) * size * (0.6 if bold else 0.53)


def wrap(text, size, max_width, bold=True):
    words, lines, line = text.split(), [], ""
    for word in words:
        trial = f"{line} {word}".strip()
        if line and width_of(trial, size, bold) > max_width:
            lines.append(line)
            line = word
        else:
            line = trial
    return lines + [line]


def fmt(value, decimals=0):
    return f"{value:.{decimals}f}"


def nice_max(top, percent):
    for step in (5, 10, 20, 25):
        if top / step <= 5.01:
            vmax = step * -(-top // step)
            if vmax - top < step * 0.12:
                vmax += step
            return (min(vmax, 100) if percent else vmax), step
    return 100, 20


def _txt(x, y, s, size=FS, weight=400, anchor="start", fill=INK):
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" font-weight="{weight}" '
            f'text-anchor="{anchor}" fill="{fill}">{escape(str(s))}</text>')


def _bar(x, y, w, h, colour, r=7):
    """A horizontal bar from x, rounded at the free (right) end."""
    r = min(r, h / 2, max(w, 0.1))
    return (f'<path d="M{x:.1f},{y:.1f}h{w - r:.1f}a{r},{r} 0 0 1 {r},{r}v{h - 2 * r:.1f}'
            f'a{r},{r} 0 0 1 -{r},{r}h-{w - r:.1f}z" fill="{colour}"/>')


def _key_rows(entries, x, width):
    """The key's entries in rows that fit the width: [[(name, colour, x)]]."""
    s, rows, at = 20, [[]], x
    for name, colour in entries:
        w = s + 10 + width_of(name, FS)
        if rows[-1] and width and at + w > width:
            rows.append([])
            at = x
        rows[-1].append((name, colour, at))
        at += w + 34
    return rows


def _key_origin(entries, x, width):
    """Where the key starts: at x, moved left if that makes it fit on one row, at the left edge if it needs several."""
    total = sum(64 + width_of(name, FS) for name, _ in entries) - 34
    if width and x + total > width:
        return max(0, width - total) if total <= width else 0
    return x


def key_height(entries, x, width):
    """Extra height a key needs beyond its first row."""
    return 30 * (len(_key_rows(entries, _key_origin(entries, x, width), width)) - 1)


def _key(entries, x, y, width=None):
    """Key above the plot: square swatches with the two left corners rounded. Long keys run onto further rows."""
    out, s = [], 20
    x = _key_origin(entries, x, width)
    for i, row in enumerate(_key_rows(entries, x, width)):
        for name, colour, at in row:
            top = y + 30 * i
            out.append(f'<path d="M{at + 5},{top}h{s - 5}v{s}h-{s - 5}a5,5 0 0 1 -5,-5v-{s - 10}a5,5 0 0 1 5,-5z" fill="{colour}"/>')
            out.append(_txt(at + s + 10, top + s - 3, name))
    return "".join(out)


def _frame(width, height, body):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}" '
            f'font-family="DM Sans, WRP Scripts, sans-serif" role="img">{body}</svg>')


def _value_axis(x0, x1, y_top, y_bottom, vmax, step, unit):
    out, v = [], 0
    while v <= vmax + 1e-9:
        x = x0 + (x1 - x0) * v / vmax
        if v:
            out.append(f'<line x1="{x:.1f}" y1="{y_top}" x2="{x:.1f}" y2="{y_bottom}" stroke="{GRID}" stroke-width="1" stroke-dasharray="1 5" stroke-linecap="round"/>')
        out.append(f'<line x1="{x:.1f}" y1="{y_bottom}" x2="{x:.1f}" y2="{y_bottom + 7}" stroke="{INK}" stroke-width="1.5"/>')
        out.append(_txt(x, y_bottom + 32, f"{v:g}{unit}", FS_AXIS, anchor="middle"))
        v += step
    out.append(f'<line x1="{x0}" y1="{y_bottom}" x2="{x1:.1f}" y2="{y_bottom}" stroke="{INK}" stroke-width="1.5"/>')
    out.append(f'<line x1="{x0}" y1="{y_top}" x2="{x0}" y2="{y_bottom}" stroke="{INK}" stroke-width="1.5"/>')
    return "".join(out)


def _labels(rows, size, max_width):
    wrapped = [wrap(label, size, max_width) for label, _ in rows]
    widest = max(width_of(line, size, True) for lines in wrapped for line in lines)
    return wrapped, min(widest, max_width)


def _category(lines, x, y_mid):
    y = y_mid - (len(lines) - 1) * 13 + 8
    return "".join(_txt(x, y + i * 26, line, FS, 600, "end") for i, line in enumerate(lines))


def hbar(rows, width, height, colour, unit="%", decimals=0, highlight=None, highlight_colour="#0D2240", colours=None, key=None, label_width=0.34):
    """One bar per row. rows: [(label, value)]. colours gives a colour per row, with a key above."""
    wrapped, label_w = _labels(rows, FS, width * label_width)
    x0, x1 = label_w + 22, width - 96
    top, bottom = (64 if key else 10), height - 48
    vmax, step = nice_max(max(v for _, v in rows), unit == "%")
    band = (bottom - top) / len(rows)
    thick = min(80, band * 0.64)
    out = [_value_axis(x0, x1, top, bottom, vmax, step, unit)]
    if key:
        out.append(_key(key, x0 - 14, 4, width))
    for i, ((label, value), lines) in enumerate(zip(rows, wrapped)):
        y_mid = top + band * (i + 0.5)
        fill = colours[i] if colours else (highlight_colour if label == highlight else colour)
        w = (x1 - x0) * value / vmax
        out.append(_bar(x0 + 0.75, y_mid - thick / 2, w, thick, fill))
        out.append(_txt(x0 + w + 12, y_mid + 9, fmt(value, decimals) + unit, FS_VALUE, 900, fill=label_colour(fill)))
        out.append(_category(lines, x0 - 16, y_mid))
    return _frame(width, height, "".join(out))


def grouped(rows, series, width, height, unit="%", decimals=0):
    """Several bars per row. rows: [(label, [values])]; series: [(name, colour)]."""
    wrapped, label_w = _labels(rows, FS, width * 0.34)
    x0, x1 = label_w + 22, width - 96
    top, bottom = 64, height - 48
    vmax, step = nice_max(max(v for _, vs in rows for v in vs), unit == "%")
    band = (bottom - top) / len(rows)
    n = len(series)
    thick = min(46, band * 0.76 / n)
    out = [_key(series, x0 - 14, 4, width), _value_axis(x0, x1, top, bottom, vmax, step, unit)]
    for i, ((label, values), lines) in enumerate(zip(rows, wrapped)):
        y_mid = top + band * (i + 0.5)
        y = y_mid - (n * thick + (n - 1) * 2) / 2
        for value, (_, colour) in zip(values, series):
            w = (x1 - x0) * value / vmax
            out.append(_bar(x0 + 0.75, y, w, thick, colour))
            out.append(_txt(x0 + w + 12, y + thick / 2 + 9, fmt(value, decimals) + unit, FS_VALUE, 900, fill=label_colour(colour)))
            y += thick + 2
        out.append(_category(lines, x0 - 16, y_mid))
    return _frame(width, height, "".join(out))


def stacked(rows, segments, width, height, unit="%", label_all=False, mute=()):
    """Bars that add to 100. rows: [(label, [values])]; segments: [(name, colour)]. Segments listed in mute are never labelled."""
    wrapped, label_w = _labels(rows, FS, width * 0.3)
    x0, x1 = label_w + 22, width - 30
    extra = key_height(segments, x0 - 14, width)
    height += extra
    top, bottom = 64 + extra, height - 48
    band = (bottom - top) / len(rows)
    thick = min(84, band * 0.62)
    stacked.unlabelled = []
    out = [_key(segments, x0 - 14, 4, width), _value_axis(x0, x1, top, bottom, 100, 20, unit)]
    for i, ((label, values), lines) in enumerate(zip(rows, wrapped)):
        y_mid = top + band * (i + 0.5)
        x = x0 + 0.75
        last = max(j for j, v in enumerate(values) if v > 0)
        for j, (value, (_, colour)) in enumerate(zip(values, segments)):
            if value <= 0:
                continue
            w = (x1 - x0) * value / 100
            if j == last:
                out.append(_bar(x, y_mid - thick / 2, w, thick, colour))
            else:
                out.append(f'<rect x="{x:.1f}" y="{y_mid - thick / 2:.1f}" width="{max(w - 2, 0.5):.1f}" height="{thick:.1f}" fill="{colour}"/>')
            if j not in mute and (label_all or colour.upper() != GRID):
                # the figure with its unit where there is room, the bare figure in a narrow segment, nothing in a sliver
                text = next((t for t in (f"{value:g}{unit}", f"{value:g}") if w >= width_of(t, FS_VALUE, True) + 8), None)
                if text:
                    out.append(_txt(x + w / 2, y_mid + 9, text, FS_VALUE, 900, "middle", text_on(colour)))
                else:
                    stacked.unlabelled.append(value)
            x += w
        out.append(_category(lines, x0 - 16, y_mid))
    return _frame(width, height, "".join(out))


def line(years, series, width, height, unit="%"):
    """Lines across polls. series: [(name, colour, [values])]."""
    x0, x1 = 76, width - 60
    top, bottom = 40 + 34 * len(series), height - 60
    vmax, step = nice_max(max(v for _, _, vs in series for v in vs), unit == "%")
    out = []
    for i, (name, colour, _) in enumerate(series):
        out.append(_key([(name, colour)], x0 - 14, 4 + i * 34))
    v = 0
    while v <= vmax + 1e-9:
        y = bottom - (bottom - top) * v / vmax
        if v:
            out.append(f'<line x1="{x0}" y1="{y:.1f}" x2="{x1}" y2="{y:.1f}" stroke="{GRID}" stroke-width="1" stroke-dasharray="1 5" stroke-linecap="round"/>')
        out.append(f'<line x1="{x0 - 7}" y1="{y:.1f}" x2="{x0}" y2="{y:.1f}" stroke="{INK}" stroke-width="1.5"/>')
        out.append(_txt(x0 - 14, y + 7, f"{v:g}{unit}", FS_AXIS, anchor="end"))
        v += step
    out.append(f'<line x1="{x0}" y1="{top}" x2="{x0}" y2="{bottom}" stroke="{INK}" stroke-width="1.5"/>')
    out.append(f'<line x1="{x0}" y1="{bottom}" x2="{x1}" y2="{bottom}" stroke="{INK}" stroke-width="1.5"/>')
    xs = [x0 + (x1 - x0) * (0.12 + 0.76 * i / (len(years) - 1)) for i in range(len(years))]
    for x, year in zip(xs, years):
        out.append(_txt(x, bottom + 36, year, FS, 600, "middle"))
    for name, colour, values in series:
        pts = [(x, bottom - (bottom - top) * value / vmax) for x, value in zip(xs, values)]
        out.append(f'<polyline points="{" ".join(f"{x:.1f},{y:.1f}" for x, y in pts)}" fill="none" stroke="{colour}" stroke-width="6" stroke-linecap="round" stroke-linejoin="round"/>')
        for (x, y), value in zip(pts, values):
            out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="10" fill="{colour}" stroke="#FFFFFF" stroke-width="3"/>')
            out.append(_txt(x, y - 22, f"{value:g}{unit}", FS_VALUE, 900, "middle", label_colour(colour)))
    return _frame(width, height, "".join(out))


def vgrouped(panels, series, width, height, unit="%"):
    """Upright bars in groups, one panel above another.

    panels: [(panel title, [(group label, [values])])]; series: [(name, colour)].
    """
    x0, x1 = 86, width - 20
    top = 70
    gap = 34
    panel_h = (height - top - gap * (len(panels) - 1)) / len(panels)
    vmax, step = nice_max(max(v for _, groups in panels for _, vs in groups for v in vs), unit == "%")
    out = [_key(series, x0 - 14, 4, width)]
    for p, (title, groups) in enumerate(panels):
        y_top = top + p * (panel_h + gap) + (34 if title else 0)
        lines = [wrap(label, FS, (x1 - x0) / len(groups) - 14) for label, _ in groups]
        y_bottom = top + p * (panel_h + gap) + panel_h - 18 - 26 * max(len(l) for l in lines)
        if title:
            out.append(_txt(x0, y_top - 14, title, FS, 800))
        v = 0
        while v <= vmax + 1e-9:
            y = y_bottom - (y_bottom - y_top) * v / vmax
            if v:
                out.append(f'<line x1="{x0}" y1="{y:.1f}" x2="{x1}" y2="{y:.1f}" stroke="{GRID}" stroke-width="1" stroke-dasharray="1 5" stroke-linecap="round"/>')
            out.append(f'<line x1="{x0 - 7}" y1="{y:.1f}" x2="{x0}" y2="{y:.1f}" stroke="{INK}" stroke-width="1.5"/>')
            out.append(_txt(x0 - 14, y + 7, f"{v:g}{unit}", FS_AXIS, anchor="end"))
            v += step
        slot = (x1 - x0) / len(groups)
        n = len(series)
        bar = min(64, slot * 0.84 / n)
        for g, (label, values) in enumerate(groups):
            x = x0 + slot * (g + 0.5) - (n * bar + (n - 1) * 2) / 2
            for value, (_, colour) in zip(values, series):
                h = (y_bottom - y_top) * value / vmax
                r = min(7, bar / 2, max(h, 0.1))
                out.append(f'<path d="M{x:.1f},{y_bottom:.1f}v-{h - r:.1f}a{r},{r} 0 0 1 {r},-{r}h{bar - 2 * r:.1f}a{r},{r} 0 0 1 {r},{r}v{h - r:.1f}z" fill="{colour}"/>')
                size = FS_VALUE if bar >= 54 else FS_VALUE - 5
                out.append(_txt(x + bar / 2, y_bottom - h - 9, f"{value:g}", size, 900, "middle", label_colour(colour)))
                x += bar + 2
            for k, line in enumerate(lines[g]):
                out.append(_txt(x0 + slot * (g + 0.5), y_bottom + 32 + 26 * k, line, FS, 600, "middle"))
        out.append(f'<line x1="{x0}" y1="{y_top}" x2="{x0}" y2="{y_bottom}" stroke="{INK}" stroke-width="1.5"/>')
        out.append(f'<line x1="{x0}" y1="{y_bottom}" x2="{x1}" y2="{y_bottom}" stroke="{INK}" stroke-width="1.5"/>')
    return _frame(width, height, "".join(out))


def dumbbell(rows, series, width, height, total=None, unit="%", total_unit=None):
    """Two values per row as dots joined by a line, with an optional total column.

    rows: [(label, [first, second], total value or None)]; series: [(name, colour)] for the two dots.
    """
    wrapped, label_w = _labels([(r[0], 0) for r in rows], FS, width * 0.3)
    column = 150 if total else 0
    x0, x1 = label_w + 22, width - 60 - column
    top, bottom = 64, height - 48
    vmax, step = nice_max(max(v for r in rows for v in r[1]), unit == "%")
    band = (bottom - top) / len(rows)
    out = [_key(series, x0 - 14, 4, width), _value_axis(x0, x1, top, bottom, vmax, step, unit)]
    if total:
        out.append(_txt(width - 4, 22, total, FS, 700, "end"))
    for i, (row, lines) in enumerate(zip(rows, wrapped)):
        y = top + band * (i + 0.5)
        xs = [x0 + (x1 - x0) * v / vmax for v in row[1]]
        out.append(f'<line x1="{min(xs):.1f}" y1="{y:.1f}" x2="{max(xs):.1f}" y2="{y:.1f}" stroke="{GRID}" stroke-width="5" stroke-linecap="round"/>')
        low = 0 if xs[0] <= xs[1] else 1
        for j, (x, value, (_, colour)) in enumerate(zip(xs, row[1], series)):
            out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="11" fill="{colour}" stroke="#FFFFFF" stroke-width="2.5"/>')
            left = j == low and xs[0] != xs[1]
            out.append(_txt(x - 18 if left else x + 18, y + 8, f"{value:g}{unit}", FS_VALUE - 3, 900, "end" if left else "start", label_colour(colour)))
        if total and len(row) > 2 and row[2] is not None:
            out.append(_txt(width - 4, y + 8, f"{row[2]:g}{unit if total_unit is None else total_unit}", FS_VALUE - 3, 900, "end"))
        out.append(_category(lines, x0 - 16, y))
    return _frame(width, height, "".join(out))


def matrix(rows, columns, width, row_height=58, unit="%", decimals=0, low="#FBE6F0", high="#E3076E"):
    """A table of values, each cell shaded from light to dark by its value. rows: [(label, [values])]; columns: [names]."""
    wrapped, label_w = _labels(rows, FS, width * (0.27 if len(columns) < 7 else 0.2))
    x0 = label_w + 22
    cell = (width - x0) / len(columns)
    size = FS - 2 if len(columns) < 7 else FS - 4
    heads = [[line.replace("/ ", "/") for line in wrap(name.replace("/", "/ "), size * 0.86, cell - 6)] for name in columns]
    top = 14 + 25 * max(len(h) for h in heads)
    height = top + row_height * len(rows) + 6
    values = [v for _, vs in rows for v in vs]
    vmin, vmax = min(values), max(values)
    a, b = [int(low[i:i + 2], 16) for i in (1, 3, 5)], [int(high[i:i + 2], 16) for i in (1, 3, 5)]
    out = []
    for j, lines in enumerate(heads):
        y = top - 12 - 25 * (len(lines) - 1)
        out += [_txt(x0 + cell * (j + 0.5), y + 25 * k, line, size, 700, "middle") for k, line in enumerate(lines)]
    for i, ((label, vs), lines) in enumerate(zip(rows, wrapped)):
        y = top + row_height * i
        for j, value in enumerate(vs):
            t = (value - vmin) / (vmax - vmin) if vmax > vmin else 1
            fill = "#" + "".join(f"{round(a[k] + (b[k] - a[k]) * t):02X}" for k in range(3))
            out.append(f'<rect x="{x0 + cell * j + 2:.1f}" y="{y + 2:.1f}" width="{cell - 4:.1f}" height="{row_height - 4:.1f}" rx="5" fill="{fill}"/>')
            ink = "#FFFFFF" if luminance(fill) < 0.24 else INK
            out.append(_txt(x0 + cell * (j + 0.5), y + row_height / 2 + 9, fmt(value, decimals) + unit, FS_VALUE, 900, "middle", ink))
        out.append(_category(lines, x0 - 16, y + row_height / 2))
    return _frame(width, height, "".join(out))


def scaled(svg, k):
    """The same drawing at k times the size (charts are drawn large, then placed smaller)."""
    import re
    head = re.match(r'<svg [^>]*viewBox="0 0 ([\d.]+) ([\d.]+)" width="[\d.]+" height="[\d.]+"', svg)
    w, h = float(head.group(1)), float(head.group(2))
    return svg.replace(f'width="{head.group(1)}" height="{head.group(2)}"', f'width="{w * k:.1f}" height="{h * k:.1f}"', 1)
