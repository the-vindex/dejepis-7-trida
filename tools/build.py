"""Build the GitHub Pages site in docs/ from the Markdown in ucivo/ and procvicovani/.

    uv run --with markdown python tools/build.py

Markdown is the source; every docs/*.html page and docs/dejepis-7-trida.md (the single-file
version for AI assistants) are generated. Edit the .md files, then rebuild.
"""
import html
import re
from pathlib import Path

import markdown

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
SITE = "https://the-vindex.github.io/dejepis-7-trida/"
AI_FILE = "dejepis-7-trida.md"

# chapter file stem -> card subtitle, in teaching order
CHAPTERS = {
    "franska-rise": "Chlodvík, Karlovci a rozdělení říše",
    "byzantska-rise": "Justinián, Hagia Sofia a věrozvěsti",
    "arabska-rise-a-islam": "Mohamed, islám a arabská expanze",
    "stredoveka-spolecnost": "Duchovenstvo, šlechta, poddaní a kláštery",
    "velke-schizma": "Rozkol západní a východní církve",
    "svata-rise-rimska": "Otoni, kurfiřti a české království",
}
EXTRAS = {  # procvicovani/*.md rendered as pages
    "pametovy-hrad": "Obrazová cesta Franskou a Byzantskou říší",
    "casova-osa": "Všechny letopočty na jednom místě",
}

PAGE = """<!doctype html><html lang="cs"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title} — Dějepis 7. třída</title><link rel="stylesheet" href="style.css"></head>
<body><header><a href="index.html">{back}</a><span>{tag}</span></header>
<main>{body}</main></body></html>
"""


def md_to_html(text):
    text = text.replace("](../docs/", "](")
    out = markdown.markdown(text, extensions=["tables", "md_in_html"])
    # paragraphs holding only images become a row of captioned figures
    def figures(m):
        imgs = re.findall(r'<img alt="([^"]*)" src="([^"]*)"\s*/?>', m.group(1))
        figs = "".join(
            f'<figure><a href="{src}" target="_blank"><img loading="lazy" src="{src}" alt="{alt}"></a>'
            f"<figcaption>{alt}</figcaption></figure>" for alt, src in imgs)
        return f'<div class="figs">{figs}</div>'
    out = re.sub(r"<p>((?:\s*<img [^>]*>\s*)+)</p>", figures, out)
    out = out.replace('<details>', '<details class="sesit">')
    return out


def title_of(text):
    return re.search(r"^# (.+)$", text, re.M).group(1).strip()


def strip_images(text):
    text = re.sub(r"^!\[[^\]]*\]\([^)]*\)\n?", "", text, flags=re.M)
    text = re.sub(r"\n## Zápis ze sešitu\n.*?</details>\n", "\n", text, flags=re.S)
    return re.sub(r"\n{3,}", "\n\n", text)


def quiz_items(text):
    items = re.findall(r"^### \d+\. (.+?)\n+\*\*Odpověď:\*\* (.+)$", text, re.M)
    items += re.findall(r"^\d+\. (.+?) — \*\*(.+?)\*\*$", text, re.M)
    return items


def render_page(path, back="← Přehled"):
    text = path.read_text()
    page = PAGE.format(title=html.escape(title_of(text)), back=back, tag="Dějepis • 7. třída",
                       body=f"<article>{md_to_html(text)}</article>")
    (DOCS / f"{path.stem}.html").write_text(page)


def main():
    for stem in CHAPTERS:
        render_page(ROOT / "ucivo" / f"{stem}.md")
    for stem in EXTRAS:
        render_page(ROOT / "procvicovani" / f"{stem}.md")

    cards = "".join(
        f'<a class="card" href="{stem}.html"><h2>{html.escape(title_of((ROOT / folder / f"{stem}.md").read_text()))}</h2>'
        f'<p class="muted">{sub} →</p></a>'
        for folder, group in (("ucivo", CHAPTERS), ("procvicovani", EXTRAS)) for stem, sub in group.items())
    quiz = "".join(
        f"<details><summary>{i}. {html.escape(q)}</summary><p>{html.escape(a)}</p></details>"
        for i, (q, a) in enumerate(quiz_items((ROOT / "procvicovani/otazky-a-odpovedi.md").read_text()), 1))
    pages = sorted(DOCS.glob("assets/sesit-*.jpg"))
    gallery = "".join(
        f'<a href="assets/{p.name}" target="_blank"><img loading="lazy" src="assets/{p.name}" alt="Sešit, stránka {int(p.stem[-2:])}">'
        f"<span>Stránka {int(p.stem[-2:])}</span></a>" for p in pages)
    body = f"""<h1>Uč se dějepis s příběhy</h1>
<p>Přehled učiva podle školního sešitu: ověřené vysvětlení, obrázky a procvičování na jednom místě.</p>
<section class="cards">{cards}</section>
<h2>Procvičování – odpověz z hlavy</h2>
<p>Otevři si otázku a teprve pak odhal odpověď.</p>
<div class="quiz">{quiz}</div>
<h2>Zápis ze sešitu</h2>
<details class="sesit"><summary>Fotky všech {len(pages)} stránek sešitu</summary><div class="gallery">{gallery}</div></details>
<section class="ai"><h2>Pro AI</h2>
<p>Celé učivo, časová osa a otázky jsou i v jednom souboru Markdown:
<a href="{AI_FILE}">{AI_FILE}</a>. Pošli odkaz ChatGPT nebo Claudovi a napiš třeba
„Vyzkoušej mě z tohohle učiva, ptej se po jedné otázce.“</p>
<p class="muted"><code>{SITE}{AI_FILE}</code></p></section>"""
    (DOCS / "index.html").write_text(
        PAGE.format(title="Přehled", back="Dějepis • 7. třída", tag="Frankové · Byzanc · Středověk", body=body).replace(
            "<title>Přehled — Dějepis 7. třída</title>", "<title>Dějepis 7. třída – výuka</title>"))

    parts = [f"""# Dějepis – 7. třída: učivo pro AI asistenta

Studijní podklady pro 7. třídu (ZŠ, Česko) podle školního sešitu, s historickými opravami.
Pokud tě někdo požádá o vyzkoušení: ptej se po jedné otázce, počkej na odpověď, oprav ji
a vysvětli krátce a česky. Web s obrázky: {SITE}
"""]
    for stem in CHAPTERS:
        parts.append(strip_images((ROOT / "ucivo" / f"{stem}.md").read_text()))
    for name in ("casova-osa", "otazky-a-odpovedi", "pametove-pomucky"):
        parts.append(strip_images((ROOT / "procvicovani" / f"{name}.md").read_text()))
    ai = "\n\n".join(p.strip() for p in parts) + "\n"
    ai = re.sub(r"^(#{1,5}) ", lambda m: "#" + m.group(1) + " " if m.start() else m.group(0), ai, flags=re.M)
    (DOCS / AI_FILE).write_text(ai)
    (DOCS / "llms.txt").write_text(
        f"# Dějepis 7. třída\n\n> Studijní podklady pro 7. třídu ZŠ.\n\n- [Celé učivo v Markdownu]({SITE}{AI_FILE})\n")


if __name__ == "__main__":
    main()
