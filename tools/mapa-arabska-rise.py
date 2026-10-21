"""Add Czech labels and a legend to the caliphate expansion map.

docs/assets/mapy/expanze-chalifatu.svg is the unlabelled public-domain map from Wikimedia Commons;
this writes arabska-rise-750.svg next to it: python tools/mapa-arabska-rise.py
"""
from pathlib import Path

MAPY = Path(__file__).resolve().parent.parent / "docs/assets/mapy"
s = (MAPY / "expanze-chalifatu.svg").read_text()

# (x, y, text, anchor) in map coordinates; a dot marks a city
CITIES = [(525, 292, "Mekka", "start"), (510, 258, "Medína", "start"), (498, 160, "Damašek", "start"),
          (565, 170, "Bagdád", "start"), (424, 98, "Konstantinopol", "end")]
REGIONS = [(585, 330, "Arábie", 15), (130, 105, "Španělsko", 12), (470, 122, "Byzantská říše", 10),
           (175, 22, "Franská říše", 10), (812, 238, "řeka Indus", 10)]
LEGEND = [("#a1584e", "za Mohameda (622–632)"), ("#ef9070", "první chalífové (632–661)"),
          ("#fad07d", "do roku 750")]

out = ['<g transform="translate(392.687 131.198)" font-family="DejaVu Sans, Verdana, sans-serif" font-weight="bold"'
       ' paint-order="stroke" stroke="white" stroke-width="3" stroke-linejoin="round">']
for x, y, t, size in REGIONS:
    out.append(f'<text x="{x}" y="{y}" font-size="{size}" text-anchor="middle" fill="#333">{t}</text>')
for x, y, t, anchor in CITIES:
    dx = 6 if anchor == "start" else -6
    out.append(f'<circle cx="{x}" cy="{y}" r="3.2" fill="black" stroke-width="1.5"/>'
               f'<text x="{x + dx}" y="{y + 4}" font-size="11" text-anchor="{anchor}" fill="black">{t}</text>')
# Poitiers 732: where the Franks stopped the advance into Europe
out.append('<path d="M 128,92 L 140,40" fill="none" stroke="#b5352b" stroke-width="2.5" stroke-dasharray="5 3"/>'
           '<path d="M 136,38 L 144,30 M 144,38 L 136,30" stroke="#b5352b" stroke-width="3"/>'
           '<text x="150" y="42" font-size="11" fill="#b5352b">Poitiers 732</text>')
out.append('<rect x="10" y="318" width="210" height="84" rx="4" fill="white" stroke="#555" stroke-width="1"/>'
           '<text x="20" y="336" font-size="11" stroke="none">Arabská říše rostla:</text>')
for n, (color, label) in enumerate(LEGEND):
    y = 346 + n * 18
    out.append(f'<rect x="20" y="{y}" width="20" height="12" fill="{color}" stroke="#555" stroke-width=".6"/>'
               f'<text x="48" y="{y + 10}" font-size="10.5" font-weight="normal" stroke="none">{label}</text>')
out.append("</g>")

i = s.rfind("</svg>")
(MAPY / "arabska-rise-750.svg").write_text(s[:i] + "\n".join(out) + s[i:])
