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


def text_on(colour):
    """Text colour for a label printed on top of a fill."""
    return "#FFFFFF" if colour.upper() in DARK else INK


def label_colour(colour):
    """Value labels take the series colour only where it passes contrast on white."""
    return colour if colour.upper() in DARK else INK


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


def _key(entries, x, y, width=None):
    """Key above the plot: square swatches with the two left corners rounded."""
    out, s = [], 20
    total = sum(s + 10 + width_of(name, FS) + 34 for name, _ in entries) - 34
    if width and x + total > width:
        x = max(0, width - total)
    for name, colour in entries:
        out.append(f'<path d="M{x + 5},{y}h{s - 5}v{s}h-{s - 5}a5,5 0 0 1 -5,-5v-{s - 10}a5,5 0 0 1 5,-5z" fill="{colour}"/>')
        out.append(_txt(x + s + 10, y + s - 3, name))
        x += s + 10 + width_of(name, FS) + 34
    return "".join(out)


def _frame(width, height, body):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}" '
            f'font-family="DM Sans, sans-serif" role="img">{body}</svg>')


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


def hbar(rows, width, height, colour, unit="%", decimals=0, highlight=None, highlight_colour="#0D2240"):
    """One bar per row. rows: [(label, value)]."""
    wrapped, label_w = _labels(rows, FS, width * 0.34)
    x0, x1 = label_w + 22, width - 96
    top, bottom = 10, height - 48
    vmax, step = nice_max(max(v for _, v in rows), unit == "%")
    band = (bottom - top) / len(rows)
    thick = min(80, band * 0.64)
    out = [_value_axis(x0, x1, top, bottom, vmax, step, unit)]
    for i, ((label, value), lines) in enumerate(zip(rows, wrapped)):
        y_mid = top + band * (i + 0.5)
        fill = highlight_colour if label == highlight else colour
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


def stacked(rows, segments, width, height, unit="%"):
    """Bars that add to 100. rows: [(label, [values])]; segments: [(name, colour)]."""
    wrapped, label_w = _labels(rows, FS, width * 0.3)
    x0, x1 = label_w + 22, width - 30
    top, bottom = 64, height - 48
    band = (bottom - top) / len(rows)
    thick = min(84, band * 0.62)
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
            if w >= 58 and colour.upper() != GRID:
                out.append(_txt(x + w / 2, y_mid + 9, f"{value:g}{unit}", FS_VALUE, 900, "middle", text_on(colour)))
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
