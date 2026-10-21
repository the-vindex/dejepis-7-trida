"""Draw the Holy Roman Empire (c. 962) over the Verdun 843 map.

docs/assets/mapy/verdunska-smlouva-843.svg is the unmodified Wikimedia Commons map; this writes
svata-rise-rimska-962.svg next to it: uv run --with shapely python tools/mapa-svata-rise.py
"""
import re
from pathlib import Path
from shapely.geometry import Polygon
from shapely.ops import unary_union
MAPY = Path(__file__).resolve().parent.parent / "docs/assets/mapy"
s = (MAPY / "verdunska-smlouva-843.svg").read_text()

def poly(pid):
    i = s.index(f'id="{pid}"'); blk = s[s.rfind("<path", 0, i):s.find(">", i)]
    d = re.search(r'\sd="([^"]*)"', blk).group(1)
    pts = [tuple(map(float, p)) for p in re.findall(r"(-?[\d.]+)[ ,](-?[\d.]+)", d)]
    return Polygon(pts).buffer(0)

east, middle, papal, dependent = (poly(p) for p in ("path1873", "path2760", "path7190", "path4527"))
# Burgundy and Provence (the western part of Lothar's middle kingdom) joined the empire only in 1033
burgundy = Polygon([(200, 272), (322, 272), (340, 300), (336, 340), (318, 380), (310, 430), (200, 430)])
empire = unary_union([east, middle.difference(burgundy)]).difference(papal).buffer(0.6).buffer(-0.6)
bohemia = Polygon([(430, 188), (482, 190), (508, 200), (522, 216), (516, 240), (496, 254), (470, 258), (440, 250)]).intersection(dependent)

def d(g):
    gs = getattr(g, "geoms", [g])
    return " ".join("M " + " L ".join(f"{x:.1f},{y:.1f}" for x, y in p.exterior.coords) + " Z" for p in gs if p.area > 20)

layer = f'''
<defs><pattern id="hre-hatch" width="7" height="7" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
<rect width="7" height="7" fill="#c4161c" fill-opacity=".10"/><line x1="0" y1="0" x2="0" y2="7" stroke="#c4161c" stroke-width="2" stroke-opacity=".45"/></pattern></defs>
<g id="svata-rise-rimska">
<path d="{d(empire)}" fill="url(#hre-hatch)" stroke="#c4161c" stroke-width="4" stroke-linejoin="round"/>
<path d="{d(bohemia)}" fill="url(#hre-hatch)" stroke="#c4161c" stroke-width="2.5" stroke-dasharray="6 4" stroke-linejoin="round"/>
<g font-family="DejaVu Sans, Bitstream Vera Sans, sans-serif" font-weight="bold" font-size="12">
<rect x="494" y="4" width="162" height="70" rx="4" fill="white" stroke="black"/>
<rect x="501" y="13" width="24" height="15" fill="url(#hre-hatch)" stroke="#c4161c" stroke-width="3"/>
<text x="531" y="21" font-size="11">Svatá říše římská</text><text x="531" y="33" font-size="9.5" font-weight="normal">kolem roku 962</text>
<rect x="501" y="46" width="24" height="15" fill="url(#hre-hatch)" stroke="#c4161c" stroke-width="2" stroke-dasharray="5 3"/>
<text x="531" y="54" font-size="11">České knížectví</text><text x="531" y="66" font-size="9.5" font-weight="normal">patřilo k říši</text>
</g></g>
'''
# overlay above the coloured lands, below the labels (first <text>)
i = s.index("<text"); i = s.rfind("\n", 0, i)
(MAPY / "svata-rise-rimska-962.svg").write_text(s[:i] + layer + s[i:])
