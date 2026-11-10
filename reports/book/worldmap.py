"""World maps for the book, drawn as SVG in the Equal Earth projection.

Country outlines are Natural Earth 1:110m (public domain), downloaded once by
build.py. Six surveyed places are too small for that map and are drawn as dots.
"""

import json
import math

# Places surveyed by the Poll that the 1:110m map leaves out (longitude, latitude).
SMALL = {"MLT": (14.4, 35.9), "HKG": (114.2, 22.3), "MUS": (57.6, -20.3),
         "BHR": (50.6, 26.0), "SGP": (103.8, 1.35), "COM": (43.3, -11.7)}
RECODE = {"KOS": "XKX"}  # Natural Earth code -> the Poll's COUNTRY_ISO3

A1, A2, A3, A4 = 1.340264, -0.081106, 0.000893, 0.003796
M = math.sqrt(3) / 2


def project(lon, lat):
    lam, phi = math.radians(lon), math.radians(lat)
    t = math.asin(M * math.sin(phi))
    t2 = t * t
    t6 = t2 * t2 * t2
    x = lam * math.cos(t) / (M * (A1 + 3 * A2 * t2 + t6 * (7 * A3 + 9 * A4 * t2)))
    y = t * (A1 + A2 * t2 + t6 * (A3 + A4 * t2))
    return x, -y


class World:
    def __init__(self, geojson_path):
        self.shapes = {}  # ISO3 -> list of rings of (x, y)
        features = json.loads(open(geojson_path, encoding="utf-8").read())["features"]
        for f in features:
            p = f["properties"]
            code = p["ISO_A3_EH"] if p["ISO_A3_EH"] != "-99" else p["ADM0_A3"]
            code = RECODE.get(code, code)
            if code == "ATA":
                continue
            geom = f["geometry"]
            polys = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
            rings = [[project(lon, lat) for lon, lat in ring] for poly in polys for ring in poly]
            self.shapes.setdefault(code, []).extend(rings)
        xs = [x for rings in self.shapes.values() for ring in rings for x, _ in ring]
        ys = [y for rings in self.shapes.values() for ring in rings for _, y in ring]
        self.box = (min(xs), min(ys), max(xs), max(ys))

    def fit(self, width, height):
        x0, y0, x1, y1 = self.box
        k = min(width / (x1 - x0), height / (y1 - y0))
        dx = (width - k * (x1 - x0)) / 2
        dy = (height - k * (y1 - y0)) / 2
        return lambda x, y: (dx + k * (x - x0), dy + k * (y - y0))

    def centre(self, code, place):
        """Centre of a country's largest ring, or its dot if it is a small place."""
        if code in SMALL:
            return place(*project(*SMALL[code]))
        ring = max(self.shapes[code], key=len)
        xs, ys = zip(*(place(x, y) for x, y in ring))
        return (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2

    def svg(self, width, height, fill, stroke="#FFFFFF", stroke_width=0.8, extra=""):
        """fill: function ISO3 -> (colour, opacity) for a country or a small place."""
        place = self.fit(width, height)
        out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}" role="img">']
        for code, rings in sorted(self.shapes.items()):
            d = "".join("M" + "L".join(f"{x:.1f},{y:.1f}" for x, y in (place(*pt) for pt in ring)) + "Z" for ring in rings)
            colour, opacity = fill(code)
            op = f' fill-opacity="{opacity}"' if opacity != 1 else ""
            out.append(f'<path d="{d}" fill="{colour}"{op} stroke="{stroke}" stroke-width="{stroke_width}" stroke-linejoin="round" fill-rule="evenodd"/>')
        for code, (lon, lat) in SMALL.items():
            colour, opacity = fill(code)
            if opacity and colour != "none":
                x, y = place(*project(lon, lat))
                out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="7" fill="{colour}" fill-opacity="{opacity}" stroke="{stroke}" stroke-width="1.5"/>')
        out.append(extra(place) if callable(extra) else extra)
        out.append("</svg>")
        return "".join(out)


def mix(colour, t, base="#FFFFFF"):
    """Blend base towards colour: t = 0 gives base, 1 gives colour."""
    a = [int(base[i:i + 2], 16) for i in (1, 3, 5)]
    b = [int(colour[i:i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(x + (y - x) * t):02X}" for x, y in zip(a, b))


def classes(values, colour, unit):
    """Five classes with about a fifth of the countries in each.

    Returns (breaks, colours, labels): a value v falls in class i when
    breaks[i-1] <= v < breaks[i].
    """
    ordered = sorted(values)
    cuts = []
    for q in (0.2, 0.4, 0.6, 0.8):
        cut = round(ordered[int(q * (len(ordered) - 1))])
        if cut not in cuts and ordered[0] < cut <= ordered[-1]:
            cuts.append(cut)
    steps = [0.2, 0.4, 0.6, 0.8, 1.0][-(len(cuts) + 1):]
    colours = [mix(colour, t) for t in steps]
    u = unit.strip()
    suffix = "%" if u == "%" else (" points" if u == "pts" else "")
    labels = [f"Under {cuts[0]}{suffix}"]
    labels += [f"{a} to {b - 1}{suffix}" for a, b in zip(cuts, cuts[1:])]
    labels.append(f"{cuts[-1]}{suffix} or more")
    return cuts, colours, labels


def class_of(value, cuts):
    return sum(value >= c for c in cuts)
