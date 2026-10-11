"""Génère les visuels du profil dans le style du portfolio alexalloukoutou.pro.

Usage : python scripts/build.py   (fonttools et brotli requis)

Chaque visuel existe en version claire et sombre (assets/light, assets/dark). Les polices Geist et
Geist Mono du portfolio sont embarquées, réduites aux caractères utilisés, pour un rendu identique
sur GitHub. Les textes sont mesurés avec les métriques réelles des polices pour les retours à la ligne.
"""

import base64
import html
import io
from pathlib import Path

from fontTools import subset
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / 'scripts'
W = 880

# Contenu

PILLS = ['Élève ingénieur · ENSAE Paris', 'Statistique & data science']
NAME_LINES = ['ALLOUKOUTOU', 'Tundé Lionel Alex']
NAME = ' '.join(NAME_LINES)
BIO = ('Je transforme des données en décisions : enquêtes, économétrie, '
       'modélisation statistique et machine learning.')
FACTS = [
    ('Basé à', 'France', False),
    ('Site', 'alexalloukoutou.pro', True),
    ('LinkedIn', 'Profil ↗', True),
    ('Blog', 'Articles ↗', True),
]

BUTTONS = {
    'contact': ('Me contacter →', True),
    'portfolio': ('Voir le portfolio', False),
    'blog': ('Lire le blog', False),
    'linkedin': ('LinkedIn ↗', False),
}

SKILLS = [
    ('Statistique & économétrie', ['R', 'Stata', 'Modélisation statistique', 'Économétrie', 'Séries temporelles', 'Quarto', 'LaTeX']),
    ('Data science', ['Python', 'Machine Learning', 'Deep Learning', 'PyTorch', 'TensorFlow', 'scikit-learn', 'SQL', 'Streamlit']),
    ('Collecte & traitement', ['Enquêtes', 'CSPro', 'ODK', 'KoboCollect', 'Excel avancé', 'Power Query', 'Git']),
]

PROJECTS = [
    dict(slug='mnist', category='Data', title='Classification MNIST',
         summary='Réseau convolutif écrit de zéro pour reconnaître des chiffres manuscrits : 99,73 % de précision, démo Streamlit.',
         tech=['Python', 'PyTorch', 'OpenCV', 'Streamlit']),
    dict(slug='cifar', category='Data', title='Classification CIFAR-10',
         summary='Deux approches comparées sur les images CIFAR-10 : k plus proches voisins sur descripteurs HOG et réseau convolutif.',
         tech=['Python', 'TensorFlow', 'FAISS', 'Streamlit']),
    dict(slug='econometrie', category='Stats', title='Économétrie : Sierra Leone',
         summary='Économétrie du modèle linéaire appliquée à des données de la Sierra Leone : estimation, tests et diagnostics.',
         tech=['R', 'Quarto', 'LaTeX']),
    dict(slug='anova', category='Stats', title='ANOVA en psychologie',
         summary="Analyse de variance appliquée à une étude psychologique, de l'exploration des données à l'interprétation.",
         tech=['R', 'Quarto', 'LaTeX']),
    dict(slug='deep-learning', category='Data', title='Carnets de deep learning',
         summary='Carnets Jupyter sur les bases du deep learning : optimisation et régularisation des réseaux.',
         tech=['Python', 'Jupyter']),
    dict(slug='guide-r', category='Stats', title='Guide de R',
         summary="Guide complet d'utilisation de R pour la statistique, des premiers pas aux analyses courantes.",
         tech=['R', 'LaTeX']),
]

ARTICLE = dict(
    title='Avant le graphique, la question : construire un indicateur qui aide vraiment à décider',
    excerpt=('Un tableau de bord ne commence pas par un choix de couleurs. Il commence par une décision '
             'à éclairer, un indicateur précisément défini et des données vérifiées.'),
    date='10 oct. 2026',
)

SECTIONS = {
    'competences': ('01', 'Compétences', 'Les outils avec lesquels je travaille au quotidien, de la collecte des données à leur analyse.'),
    'projets': ('02', 'Projets', "Des projets en statistique et data science, de l'analyse de données aux applications concrètes."),
    'articles': ('03', 'Derniers articles', None),
    'contributions': ('04', 'Contributions', 'Mon activité sur GitHub, mise à jour chaque nuit.'),
}

# Couleurs (zinc de Tailwind, comme le portfolio)

THEMES = {
    'light': dict(text='#09090b', muted='#52525b', eyebrow='#71717a', border='#e4e4e7', card='#ffffff',
                  chip='#f4f4f5', chip_text='#3f3f46', placeholder='#f4f4f5', number='#d4d4d8', hero='#09090b',
                  primary='#09090b', primary_text='#ffffff', outline='#d4d4d8', outline_text='#09090b'),
    'dark': dict(text='#ffffff', muted='#a1a1aa', eyebrow='#a1a1aa', border='#27272a', card='#18181b',
                 chip='#27272a', chip_text='#d4d4d8', placeholder='#27272a', number='#52525b', hero='#18181b',
                 primary='#ffffff', primary_text='#09090b', outline='#3f3f46', outline_text='#ffffff'),
}
HERO = dict(pill='#3f3f46', pill_text='#d4d4d8', bio='#d4d4d8', label='#a1a1aa', value='#f4f4f5', rule='#27272a', underline='#52525b')
TECH = '#71717a'

# Polices

SANS_FILE = SCRIPTS / 'fonts' / 'geist.woff2'
MONO_FILE = SCRIPTS / 'fonts' / 'geist-mono.woff2'
USED = set()


class Face:
    """Métriques d'une graisse donnée d'une police variable."""

    def __init__(self, path, weight):
        font = instantiateVariableFont(TTFont(path), {'wght': weight})
        self.upm = font['head'].unitsPerEm
        self.cmap = font.getBestCmap()
        self.hmtx = font['hmtx']

    def width(self, s, size, tracking=0.0):
        units = sum(self.hmtx[self.cmap[ord(c)]][0] if ord(c) in self.cmap else self.upm * 0.6 for c in s)
        return units * size / self.upm + tracking * size * len(s)


SANS = {w: Face(SANS_FILE, w) for w in (400, 500, 600)}
MONO = {w: Face(MONO_FILE, w) for w in (300, 400, 500)}


def wrap(s, face, size, width, tracking=0.0, max_lines=None):
    lines, line = [], ''
    for word in s.split():
        candidate = f'{line} {word}'.strip()
        if line and face.width(candidate, size, tracking) > width:
            lines.append(line)
            line = word
        else:
            line = candidate
    lines.append(line)
    if max_lines and len(lines) > max_lines:
        lines = lines[:max_lines]
        while face.width(lines[-1] + '…', size, tracking) > width:
            lines[-1] = lines[-1].rsplit(' ', 1)[0]
        lines[-1] = lines[-1].rstrip(' ,.:;') + '…'
    return lines


def font_data(path):
    opts = subset.Options()
    opts.flavor = 'woff2'
    opts.layout_features = ['*']
    font = subset.load_font(str(path), opts)
    subsetter = subset.Subsetter(opts)
    subsetter.populate(text=''.join(sorted(USED)) + ' ')
    subsetter.subset(font)
    buffer = io.BytesIO()
    subset.save_font(font, buffer, opts)
    return base64.b64encode(buffer.getvalue()).decode()


# Primitives SVG

def text(x, y, s, size, fill, mono=False, weight=400, tracking=0.0, anchor=None):
    USED.update(s)
    attrs = f' letter-spacing="{tracking * size:.2f}"' if tracking else ''
    attrs += f' text-anchor="{anchor}"' if anchor else ''
    return (f'<text x="{x:.1f}" y="{y:.1f}" class="{"m" if mono else "s"}" font-size="{size}" '
            f'font-weight="{weight}" fill="{fill}"{attrs}>{html.escape(s)}</text>')


def baseline(top, line_height, size):
    """Ligne de base d'un texte centré dans sa hauteur de ligne."""
    return top + line_height / 2 + size * 0.36


def rect(x, y, w, h, r, fill='none', stroke=None):
    s = f' stroke="{stroke}"' if stroke else ''
    return f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{r}" fill="{fill}"{s}/>'


def hline(x1, x2, y, color):
    return f'<line x1="{x1:.1f}" y1="{y:.1f}" x2="{x2:.1f}" y2="{y:.1f}" stroke="{color}"/>'


def rise(content, delay):
    return f'<g class="r" style="animation-delay:{delay:.2f}s">{content}</g>'


def document(width, height, body, label):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width:.0f}" height="{height:.0f}" '
            f'viewBox="0 0 {width:.0f} {height:.0f}" role="img" aria-label="{html.escape(label)}">'
            f'<style>/*FONTS*/.s{{font-family:"Geist",ui-sans-serif,system-ui,sans-serif}}'
            f'.m{{font-family:"Geist Mono",ui-monospace,SFMono-Regular,monospace}}'
            f'.r{{opacity:0;animation:r .6s cubic-bezier(.2,.8,.2,1) forwards}}'
            f'@keyframes r{{from{{opacity:0;transform:translateY(6px)}}to{{opacity:1;transform:none}}}}'
            f'@media (prefers-reduced-motion:reduce){{.r{{opacity:1;animation:none}}}}</style>'
            f'{body}</svg>\n')


def eyebrow(x, y, s, color):
    return text(x, y, s.upper(), 11, color, mono=True, weight=500, tracking=0.14)


# Visuels

def hero(t):
    pad, gap = 40, 40
    inner = W - 2 * pad
    left = (inner - gap) * 8 / 12
    right = inner - gap - left
    aside_x = pad + left + gap
    parts, y, x = [], pad, pad

    for pill in PILLS:
        w = MONO[400].width(pill, 11.2) + 24
        parts.append(rise(rect(x, y + 0.5, w, 24, 12, stroke=HERO['pill'])
                          + text(x + 12, baseline(y, 25, 11.2), pill, 11.2, HERO['pill_text'], mono=True), 0.05))
        x += w + 8
    y += 25 + 20

    size, lh = 46, 46 * 1.2
    for i, line in enumerate(NAME_LINES):
        parts.append(rise(text(pad, baseline(y, lh, size), line, size, '#ffffff', weight=600, tracking=-0.025), 0.12 + i * 0.06))
        y += lh
    y += 14

    size, lh = 17, 17 * 1.625
    for line in wrap(BIO, SANS[400], size, left):
        parts.append(rise(text(pad, baseline(y, lh, size), line, size, HERO['bio']), 0.3))
        y += lh

    row = 41
    content = max(y - pad, row * len(FACTS))
    height = 2 * pad + content
    top = height - pad - row * len(FACTS)
    facts = [hline(aside_x, aside_x + right, top + 0.5, HERO['rule'])]
    for i, (label, value, link) in enumerate(FACTS):
        ry = top + i * row
        by = baseline(ry, row, 14)
        facts.append(text(aside_x, by, label, 14, HERO['label']))
        facts.append(text(aside_x + right, by, value, 14, HERO['value'], anchor='end'))
        if link:
            w = SANS[400].width(value, 14)
            facts.append(hline(aside_x + right - w, aside_x + right, by + 4.5, HERO['underline']))
        facts.append(hline(aside_x, aside_x + right, ry + row + 0.5, HERO['rule']))
    parts.append(rise(''.join(facts), 0.4))

    body = rect(0, 0, W, height, 12, fill=t['hero']) + ''.join(parts)
    return document(W, height, body, f'{NAME} : {BIO}')


def button(t, label, primary):
    size, px, h = 14, 16, 40
    w = SANS[600 if primary else 500].width(label, size) + 2 * px
    if primary:
        body = rect(0, 0, w, h, 6, fill=t['primary']) + text(px, baseline(0, h, size), label, size, t['primary_text'], weight=600)
    else:
        body = rect(0.5, 0.5, w - 1, h - 1, 6, stroke=t['outline']) + text(px, baseline(0, h, size), label, size, t['outline_text'], weight=500)
    return document(w, h, body, label)


def section(t, number, title, intro):
    parts = [hline(0, W, 0.5, t['border'])]
    y = 36
    parts.append(eyebrow(0, baseline(y, 16, 11), number, t['eyebrow']))
    y += 16 + 8
    parts.append(text(0, baseline(y, 42, 34), title, 34, t['text'], weight=600, tracking=-0.025))
    y += 42
    if intro:
        y += 10
        for line in wrap(intro, SANS[400], 14, W):
            parts.append(text(0, baseline(y, 22.75, 14), line, 14, t['muted']))
            y += 22.75
    return document(W, y + 20, rise(''.join(parts), 0.05), title)


def skills(t):
    gap, pad = 12, 16
    cw = (W - 2 * gap) / 3
    layouts = []
    for title, items in SKILLS:
        chips, x, y = [], pad, pad + 20 + 12
        for item in items:
            w = MONO[400].width(item, 11.2) + 20
            if x + w > cw - pad and x > pad:
                x, y = pad, y + 30
            chips.append((x, y, w, item))
            x += w + 6
        layouts.append((title, chips, y + 24 + pad))
    height = max(h for _, _, h in layouts)
    body = []
    for i, (title, chips, _) in enumerate(layouts):
        ox = i * (cw + gap)
        card = [rect(ox + 0.5, 0.5, cw - 1, height - 1, 8, fill=t['card'], stroke=t['border']),
                text(ox + pad, baseline(pad, 20, 14), title, 14, t['text'], weight=600)]
        for x, y, w, item in chips:
            card.append(rect(ox + x, y, w, 24, 12, fill=t['chip']))
            card.append(text(ox + x + 10, baseline(y, 24, 11.2), item, 11.2, t['chip_text'], mono=True))
        body.append(rise(''.join(card), 0.08 + i * 0.08))
    return document(W, height + 1, ''.join(body), 'Compétences : ' + ', '.join(i for _, items in SKILLS for i in items))


def project_cards(t):
    cw, pad, thumb = 280, 16, 112
    text_w = cw - 2 * pad
    blocks = []
    for p in PROJECTS:
        title = wrap(p['title'], SANS[600], 18, text_w, -0.025)
        summary = wrap(p['summary'], SANS[400], 14, text_w, max_lines=3)
        tech = wrap(' · '.join(p['tech']), MONO[400], 11.2, text_w)
        blocks.append((p, title, summary, tech))
    content = max(16 + 8 + len(ti) * 28 + 8 + len(s) * 22.75 + 16 + len(te) * 17 for _, ti, s, te in blocks)
    height = thumb + pad + max(content, 192 - 2 * pad) + pad
    cards = {}
    for index, (p, title, summary, tech) in enumerate(blocks, start=1):
        body = [f'<clipPath id="c"><rect x="0" y="0" width="{cw}" height="{height:.1f}" rx="8"/></clipPath>',
                '<g clip-path="url(#c)">', rect(0, 0, cw, height, 0, fill=t['card']),
                rect(0, 0, cw, thumb, 0, fill=t['placeholder']),
                eyebrow(pad, thumb - pad, p['category'], t['eyebrow']),
                text(cw - pad, thumb - pad + 2, f'{index:02d}', 30, t['number'], mono=True, weight=300, anchor='end'),
                hline(0, cw, thumb + 0.5, t['border']), '</g>',
                rect(0.5, 0.5, cw - 1, height - 1, 8, stroke=t['border'])]
        y = thumb + pad
        body.append(eyebrow(pad, baseline(y, 16, 11), p['category'], t['eyebrow']))
        y += 16 + 8
        for line in title:
            body.append(text(pad, baseline(y, 28, 18), line, 18, t['text'], weight=600, tracking=-0.025))
            y += 28
        y += 8
        for line in summary:
            body.append(text(pad, baseline(y, 22.75, 14), line, 14, t['muted']))
            y += 22.75
        y = height - pad - len(tech) * 17
        for line in tech:
            body.append(text(pad, baseline(y, 17, 11.2), line, 11.2, TECH, mono=True))
            y += 17
        cards[p['slug']] = document(cw, height, rise(''.join(body), 0.05 + (index - 1) % 3 * 0.08),
                                    f"{p['title']} : {p['summary']}")
    return cards


def article(t):
    date_w, num_w, gap = 120, 32, 24
    col = num_w + gap
    text_w = W - col - gap - date_w
    title = wrap(ARTICLE['title'], SANS[600], 16, text_w, -0.025)
    excerpt = wrap(ARTICLE['excerpt'], SANS[400], 14, text_w, max_lines=2)
    y0 = 24
    first = baseline(y0, 24, 16)
    parts = [hline(0, W, 0.5, t['border']),
             text(0, first, '01', 12, t['eyebrow'], mono=True),
             text(W - date_w, first, ARTICLE['date'], 12, t['eyebrow'], mono=True)]
    y = y0
    for line in title:
        parts.append(text(col, baseline(y, 24, 16), line, 16, t['text'], weight=600, tracking=-0.025))
        y += 24
    y += 4
    for line in excerpt:
        parts.append(text(col, baseline(y, 20, 14), line, 14, t['muted']))
        y += 20
    height = y + 24
    parts.append(hline(0, W, height - 0.5, t['border']))
    return document(W, height, rise(''.join(parts), 0.05), f"{ARTICLE['title']} : {ARTICLE['excerpt']}")


# Écriture

def build():
    files = {}
    for name, t in THEMES.items():
        files[f'{name}/hero.svg'] = hero(t)
        for key, (label, primary) in BUTTONS.items():
            files[f'{name}/button-{key}.svg'] = button(t, label, primary)
        for key, (number, title, intro) in SECTIONS.items():
            files[f'{name}/section-{key}.svg'] = section(t, number, title, intro)
        files[f'{name}/skills.svg'] = skills(t)
        for slug, svg in project_cards(t).items():
            files[f'{name}/project-{slug}.svg'] = svg
        files[f'{name}/article.svg'] = article(t)

    fonts = (f'@font-face{{font-family:"Geist";font-weight:100 900;src:url(data:font/woff2;base64,{font_data(SANS_FILE)}) format("woff2")}}'
             f'@font-face{{font-family:"Geist Mono";font-weight:100 900;src:url(data:font/woff2;base64,{font_data(MONO_FILE)}) format("woff2")}}')
    for path, svg in files.items():
        target = ROOT / 'assets' / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(svg.replace('/*FONTS*/', fonts), encoding='utf-8')
    print(f'{len(files)} visuels générés dans assets/')


if __name__ == '__main__':
    build()
