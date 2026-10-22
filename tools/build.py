"""Build the GitHub Pages site in docs/ from the Markdown in ucivo/ and procvicovani/.

    uv run --with markdown python tools/build.py

Markdown is the source; every docs/*.html page and docs/dejepis-7-trida.md (the single-file
version for AI assistants) are generated. Edit the .md files, then rebuild.

    ucivo/<chapter>.md                  one topic each, complete: summary, text, mnemonic, notebook photos
    procvicovani/casova-osa.md          the timeline: one table row per event, with its lane and chapter
    procvicovani/otazky-a-odpovedi.md   questions, one `## <chapter title>` section per chapter

A test is always about one topic, so nothing mixes topics except the overview timeline.
"""
import html
import json
import re
from pathlib import Path

import markdown

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
SITE = "https://the-vindex.github.io/dejepis-7-trida/"
AI_FILE = "dejepis-7-trida.md"

# lane key in casova-osa.md -> (css class, legend name)
LANES = {"říše": ("rise", "Frankové a Svatá říše"), "byzanc": ("byz", "Byzanc a církev"),
         "islám": ("isl", "Arabové a islám"), "čechy": ("cz", "České země")}
# chapters in chronological order: stem -> (span shown above the title, lane css class)
CHAPTERS = {
    "byzantska-rise": ("476–1453", "byz"),
    "franska-rise": ("5. století – 843", "rise"),
    "arabska-rise-a-islam": ("7.–9. století", "isl"),
    "svata-rise-rimska": ("919–1356", "rise"),
    "velke-schizma": ("1054", "byz"),
    "stredoveka-spolecnost": ("celý středověk", "ink"),
}
FIX_HEADINGS = ("Ověření proti zápiskům", "Opravy z poznámek", "Pozor na častou chybu")

FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com">'
         '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
         '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Alegreya:ital,wght@0,500;0,700;0,800;1,500'
         '&family=Alegreya+Sans:ital,wght@0,400;0,500;0,700;1,400&display=swap">')

PAGE = """<!doctype html><html lang="cs"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title>{fonts}<link rel="stylesheet" href="style.css"></head>
<body class="{body_class}"><header class="top"><a class="brand" href="index.html">Dějepis 7</a>
<nav><a href="index.html#osa"{osa}>Časová osa</a><a href="opakovani.html"{rev}>Opakování</a></nav></header>
<main>{body}</main>
<footer class="foot"><a href="index.html#ai">Učivo pro AI</a></footer></body></html>
"""


def page(title, body, body_class="", active=""):
    cur = ' aria-current="page"'
    return PAGE.format(title=html.escape(title), fonts=FONTS, body_class=body_class, body=body,
                       osa=cur if active == "osa" else "", rev=cur if active == "rev" else "")


def read(rel):
    return (ROOT / rel).read_text()


def title_of(text):
    return re.search(r"^# (.+)$", text, re.M).group(1).strip()


def lead_of(text):
    return re.search(r"^> \*\*Ve zkratce:\*\* (.+)$", text, re.M).group(1)


def md_to_html(text):
    text = re.sub(r"^# .+\n", "", text, count=1).replace("](../docs/", "](")
    out = markdown.markdown(text, extensions=["tables", "md_in_html"])
    out = re.sub(r"<blockquote>\s*<p><strong>Ve zkratce:</strong>\s*(.*?)</p>\s*</blockquote>",
                 r'<p class="lead">\1</p>', out, flags=re.S)

    def figures(m):
        imgs = re.findall(r'<img alt="([^"]*)" src="([^"]*)"\s*/?>', m.group(1))
        figs = "".join(
            f'<figure><a href="{src}" target="_blank"><img loading="lazy" src="{src}" alt="{alt}"></a>'
            f"<figcaption>{alt}</figcaption></figure>" for alt, src in imgs)
        return f'<div class="figs">{figs}</div>'
    out = re.sub(r"<p>((?:\s*<img [^>]*>\s*)+)</p>", figures, out)
    out = re.sub(r"<h2>Zapamatuj si</h2>\s*(<p>.*?</p>)",
                 r'<aside class="remember"><h2>Zapamatuj si</h2>\1</aside>', out, flags=re.S)
    out = re.sub(r"<h[23]>(?:%s)</h[23]>\s*((?:<p>.*?</p>\s*)+)" % "|".join(FIX_HEADINGS),
                 r'<aside class="fix"><h2>Pozor na omyly</h2>\1</aside>', out, flags=re.S)
    # "Pro zajímavost" stays after its section's text (phones read it there); wide screens pin it beside the text
    out = re.sub(r"(<h2>[^<]*</h2>)((?:(?!<h2>).)*?)<h3>Pro zajímavost</h3>\s*(<ul>.*?</ul>)",
                 r'\1<div class="has-fact">\2<aside class="fact"><h2>Pro zajímavost</h2>\3</aside></div>', out, flags=re.S)
    out = re.sub(r"<h2>Paměťový obraz</h2>(.*?)(?=<h2>|<aside|$)",
                 r'<section class="mnemo"><h2>Paměťový obraz</h2>\1</section>', out, flags=re.S)
    return out.replace("<details>", '<details class="sesit">')


def timeline():
    # an event can belong to two lanes and two topics ("říše, islám"); the first one is its home
    rows = re.findall(r"^\| ([\d–]+) \| (.+?) \| ([^|]+?) \| ([^|]+?) \|$", read("procvicovani/casova-osa.md"), re.M)
    events = []
    for y, t, ls, cs in rows:
        lanes = [LANES[x.strip()][0] for x in ls.split(",")]
        chapters = [x.strip() for x in cs.split(",")]
        events.append({"year": y, "text": t, "lane": lanes[0], "lanes": lanes, "chapter": chapters[0], "chapters": chapters})
    return events


def topic_link(stem):
    return f'<a href="{stem}.html">{html.escape(title_of(read(f"ucivo/{stem}.md")))}</a>'


def questions():
    out = {}
    for sec in re.split(r"^## ", read("procvicovani/otazky-a-odpovedi.md"), flags=re.M)[1:]:
        title = sec.splitlines()[0].strip()
        out[title] = re.findall(r"^\d+\. (.+?) — \*\*(.+?)\*\*$", sec, re.M)
    return out


def chips(events, stem):
    out = ""
    for e in events:
        others = [c for c in e["chapters"] if c != stem]
        also = f'<span class="also">i v tématu {", ".join(topic_link(c) for c in others)}</span>' if others else ""
        lane = CHAPTERS[stem][1] if CHAPTERS[stem][1] in e["lanes"] else e["lane"]  # colour of this topic where it fits
        out += f'<li class="{lane}"><b>{e["year"]}</b> {html.escape(e["text"])}{also}</li>'
    return out


def quiz_html(items):
    return "".join(f'<details class="q"><summary>{html.escape(q)}</summary><p>{html.escape(a)}</p></details>'
                   for q, a in items)


def build_chapters(events, qs):
    stems = list(CHAPTERS)
    for i, stem in enumerate(stems):
        text = read(f"ucivo/{stem}.md")
        title = title_of(text)
        span, lane = CHAPTERS[stem]
        body = md_to_html(text)
        sesit = ""
        if "<h2>Zápis ze sešitu</h2>" in body:
            body, sesit = body.split("<h2>Zápis ze sešitu</h2>", 1)
            sesit = '<section class="notebook"><h2>Zápis ze sešitu</h2>' + sesit + "</section>"
        mine = [e for e in events if stem in e["chapters"]]
        dates = f'<ol class="chips" aria-label="Letopočty tématu">{chips(mine, stem)}</ol>' if mine else ""
        quiz = (f'<section class="quiz"><h2>Vyzkoušej se</h2><p class="hint">Odpověz nahlas, teprve pak otevři odpověď. '
                f'<a href="opakovani.html#{stem}">Procvičit náhodně</a></p>{quiz_html(qs[title])}</section>') if qs.get(title) else ""
        pn = '<nav class="pager" aria-label="Další témata">'
        if i:
            pn += f'<a class="prev" href="{stems[i-1]}.html"><small>Předchozí téma</small>{html.escape(title_of(read(f"ucivo/{stems[i-1]}.md")))}</a>'
        else:
            pn += "<span></span>"
        if i + 1 < len(stems):
            pn += f'<a class="next" href="{stems[i+1]}.html"><small>Další téma</small>{html.escape(title_of(read(f"ucivo/{stems[i+1]}.md")))}</a>'
        pn += "</nav>"
        head = f'<header class="chapter-head"><p class="span">{span}</p><h1>{html.escape(title)}</h1></header>'
        lead, body = body.split("</p>", 1) if body.startswith('<p class="lead">') else ("", body)
        lead = lead + "</p>" if lead else ""
        art = f'<article class="chapter">{head}{lead}{dates}{body}{quiz}{sesit}</article>{pn}'
        (DOCS / f"{stem}.html").write_text(page(f"{title} – Dějepis 7", art, f"lane-{lane}"))


def build_index(events):
    legend = "".join(f'<li class="{c}">{n}</li>' for c, n in LANES.values())
    order = [c for c, _ in LANES.values()]
    rows, century = [], None
    for e in events:
        c = (int(re.match(r"\d+", e["year"]).group()) - 1) // 100 + 1
        if c != century:
            century = c
            rows.append(f'<li class="century"><span>{c}. století</span></li>')
        idx = [order.index(l) for l in e["lanes"]]
        dots = "".join(f'<i class="dot {l}" style="--lane:{i}"></i>' for l, i in zip(e["lanes"], idx))
        if len(idx) > 1:  # where two stories cross, bridge their lanes
            dots = f'<i class="bridge" style="--a:{min(idx)};--b:{max(idx)}"></i>' + dots
        text = f'<a href="{e["chapter"]}.html">{html.escape(e["text"])}</a>'
        if len(e["chapters"]) > 1:
            text = (f'<span class="what">{html.escape(e["text"])}'
                    f'<span class="also">témata {", ".join(topic_link(c) for c in e["chapters"])}</span></span>')
        rows.append(f'<li class="ev {e["lane"]}"><span class="year">{e["year"]}</span>'
                    f'<span class="lanes">{dots}</span>{text}</li>')
    topics = ""
    for stem, (span, lane) in CHAPTERS.items():
        text = read(f"ucivo/{stem}.md")
        topics += (f'<li class="{lane}"><a href="{stem}.html"><span class="span">{span}</span>'
                   f'<strong>{html.escape(title_of(text))}</strong><span class="sum">{html.escape(lead_of(text))}</span></a></li>')
    body = f"""<section class="intro"><h1>Od pádu Říma po pád Konstantinopole</h1>
<p>Dějepis 7. třídy: tisíc let mezi roky 476 a 1453. Každé téma má vlastní stránku s výkladem, letopočty a otázkami. Na časové ose vidíš, jak jdou po sobě.</p></section>
<section class="topics"><h2>Témata</h2><ol class="topic-list">{topics}</ol></section>
<section id="osa" class="osa-wrap"><h2>Časová osa</h2><p class="hint">Klikni na událost a otevře se téma, kde je vysvětlená.</p>
<ul class="legend">{legend}</ul><ol class="osa">{''.join(rows)}</ol></section>
<section id="ai" class="ai"><h2>Pro AI</h2>
<p>Celé učivo, časová osa a otázky jsou i v jednom souboru Markdown:
<a href="{AI_FILE}">{AI_FILE}</a>. Pošli odkaz ChatGPT nebo Claudovi a napiš třeba
„Vyzkoušej mě z Franské říše, ptej se po jedné otázce.“</p>
<p class="url">{SITE}{AI_FILE}</p></section>"""
    (DOCS / "index.html").write_text(page("Dějepis 7. třída – od pádu Říma po pád Konstantinopole", body, "home", "osa"))


def build_review(events, qs):
    topics = []
    for stem, (span, lane) in CHAPTERS.items():
        title = title_of(read(f"ucivo/{stem}.md"))
        topics.append({"id": stem, "title": title, "lane": lane,
                       "q": [{"q": q, "a": a} for q, a in qs.get(title, [])],
                       "dates": [{"y": e["year"], "t": e["text"]} for e in events if stem in e["chapters"]]})
    tabs = "".join(f'<a class="tab {t["lane"]}" href="#{t["id"]}" data-id="{t["id"]}">{html.escape(t["title"])}</a>' for t in topics)
    body = f"""<section class="intro"><h1>Opakování</h1>
<p>Test bývá z jednoho tématu, tak si ho vyber. Otázky chodí náhodně a jen z vybraného tématu.</p></section>
<nav class="tabs" aria-label="Téma">{tabs}</nav>
<section class="drill" aria-live="polite"><h2 id="dt"></h2>
<div class="drill-card"><p class="drill-n" id="dn"></p><p class="drill-q" id="dq"></p><p class="drill-a" id="da" hidden></p></div>
<div class="drill-btns"><button id="show" type="button">Ukázat odpověď</button><button id="next" type="button" class="ghost">Další otázka</button></div>
<p class="hint"><a id="dlink" href="#">Otevřít celé téma</a></p></section>
<section class="dates" id="dates-wrap"><h2>Kartičky s letopočty</h2><p class="hint">Řekni, co se v daném roce stalo, a otoč kartičku.</p><div class="date-grid" id="dates"></div></section>
<script>
const T={json.dumps(topics, ensure_ascii=False)};
const $=id=>document.getElementById(id);let cur,order=[],pos=0;
function shuffle(n){{const a=[...Array(n).keys()];for(let i=n-1;i>0;i--){{const j=Math.floor(Math.random()*(i+1));[a[i],a[j]]=[a[j],a[i]]}}return a}}
function ask(){{if(pos>=order.length){{order=shuffle(cur.q.length);pos=0}}const x=cur.q[order[pos]];
$('dn').textContent=`Otázka ${{pos+1}} z ${{cur.q.length}}`;$('dq').textContent=x.q;$('da').textContent=x.a;$('da').hidden=true;$('show').disabled=false;pos++}}
function pick(id){{cur=T.find(t=>t.id===id)||T[0];order=shuffle(cur.q.length);pos=0;
document.body.dataset.lane=cur.lane;$('dt').textContent=cur.title;$('dlink').href=cur.id+'.html';
document.querySelectorAll('.tab').forEach(a=>a.toggleAttribute('aria-current',a.dataset.id===cur.id));
$('dates').innerHTML=cur.dates.map(d=>`<details class="card-date"><summary>${{d.y}}</summary><p>${{d.t}}</p></details>`).join('');
$('dates-wrap').hidden=!cur.dates.length;ask()}}
$('show').onclick=()=>{{$('da').hidden=false;$('show').disabled=true}};$('next').onclick=ask;
addEventListener('hashchange',()=>pick(location.hash.slice(1)));pick(location.hash.slice(1));
</script>"""
    (DOCS / "opakovani.html").write_text(page("Opakování – Dějepis 7", body, "review", "rev"))


def strip_images(text):
    text = re.sub(r"^!\[[^\]]*\]\([^)]*\)\n?", "", text, flags=re.M)
    text = re.sub(r"\n## Zápis ze sešitu\n.*?</details>\n", "\n", text, flags=re.S)
    return re.sub(r"\n{3,}", "\n\n", text)


def build_ai():
    parts = [f"""# Dějepis – 7. třída: učivo pro AI asistenta

Studijní podklady pro 7. třídu (ZŠ, Česko) podle školního sešitu, s historickými opravami.
Test je vždy z jednoho tématu (jedné kapitoly níže). Pokud tě někdo požádá o vyzkoušení,
zeptej se z jakého tématu, ptej se po jedné otázce, počkej na odpověď, oprav ji a vysvětli
krátce a česky. Web s obrázky: {SITE}
"""]
    parts += [strip_images(read(f"ucivo/{s}.md")) for s in CHAPTERS]
    parts += [strip_images(read(f"procvicovani/{n}.md")) for n in ("casova-osa", "otazky-a-odpovedi")]
    ai = "\n\n".join(p.strip() for p in parts) + "\n"
    ai = re.sub(r"^(#{1,5}) ", lambda m: "#" + m.group(1) + " " if m.start() else m.group(0), ai, flags=re.M)
    (DOCS / AI_FILE).write_text(ai)
    (DOCS / "llms.txt").write_text(
        f"# Dějepis 7. třída\n\n> Studijní podklady pro 7. třídu ZŠ.\n\n- [Celé učivo v Markdownu]({SITE}{AI_FILE})\n")


def main():
    events, qs = timeline(), questions()
    titles = {title_of(read(f"ucivo/{s}.md")) for s in CHAPTERS}
    assert set(qs) <= titles, f"question sections without a chapter: {set(qs) - titles}"
    assert {e["chapter"] for e in events} <= set(CHAPTERS), "timeline row points at an unknown chapter"
    for old in ("casova-osa.html", "pametovy-hrad.html"):
        (DOCS / old).unlink(missing_ok=True)
    build_chapters(events, qs)
    build_index(events)
    build_review(events, qs)
    build_ai()


if __name__ == "__main__":
    main()
