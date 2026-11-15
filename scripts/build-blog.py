#!/usr/bin/env python3
"""Build the mlinternasjonal.no blog from Grok article fields.

Mechanical templating only. Article titles, descriptions and bodies are
copied verbatim from the Grok raw files / parsed.json. UI strings are
taken only from existing Grok ui-labels (willymartinez) or from copy
already on this site. Missing labels are omitted, never invented.
"""
from __future__ import annotations

import html
import json
import re
import sys
from pathlib import Path

from PIL import Image

ROOT = Path("/workspace/ml-internasjonal-prod")
SRC = Path("/workspace/blogs-grok-2026-11-14/ml-internasjonal")
COVERS_SRC = SRC / "covers"
COVERS_DST = ROOT / "assets/img/blog"
SITE = "https://mlinternasjonal.no"
ORG = "ML Internasjonal Handel"

# Verbatim Grok UI labels from willymartinez content/blog/ui-labels.json
# (same Grok batch / existing Grok ui-labels file).
UI = {
    "nb": {"nav": "Blogg", "heading": "Blogg", "back": "Tilbake til blogg"},
    "en": {"nav": "Blog", "heading": "Blog", "back": "Back to blog"},
    "es": {"nav": "Blog", "heading": "Blog", "back": "Volver al blog"},
}

# Index intro, index meta, FAQ heading and related heading have no
# Grok or verbatim source that fits this site, so they are omitted.
MISSING_LABELS = [
    "index_meta_nb",
    "index_meta_en",
    "index_meta_es",
    "index_intro_nb",
    "index_intro_en",
    "index_intro_es",
    "faq_heading_nb",
    "faq_heading_en",
    "faq_heading_es",
    "related_heading_nb",
    "related_heading_en",
    "related_heading_es",
]

# Standalone heading lines written by Grok in the article bodies.
HEADING_LINES = {
    "Introducción",
    "Introduction",
    "Introduksjon",
    "Innledning",
    "Descargo",
    "Disclaimer",
    "Ansvarsfraskrivelse",
    "Fraskrivelse",
    "Nota",
    "Note",
}

KNOWN_FIELDS = [
    "slug",
    "keyword",
    "titulo",
    "titulo_seo",
    "meta",
    "nivel",
    "clase",
    "resumen",
    "enlaces_internos",
    "h2_h3",
    "faq",
    "portada_prompt",
]
MULTILINE = {"enlaces_internos", "h2_h3", "faq"}
FIELD_RE = re.compile(r"^(" + "|".join(KNOWN_FIELDS) + r"):[ \t]?(.*)$")

LANGS = {
    "es": {
        "html_lang": "es",
        "og_locale": "es_ES",
        "index_path": "/es/blog/",
        "article_tpl": "/es/blog/{slug}/",
        "home": "/es/",
        "skip_href": "#contenido",
        "skip_text": "Saltar al contenido",
        "nav_aria": "Principal",
        "menu": "Menú",
        "contact_href": "/es/#contacto",
        "contact_label": "Contacto",
        "footer_pages": "Páginas",
        "footer_legal": "Legal",
        "services_href": "/es/#servicios",
        "services_label": "Servicios",
        "sectors_href": "/es/#sectores",
        "sectors_label": "Sectores",
        "privacy": ("/es/privacidad/", "Privacidad"),
        "cookies": ("/es/cookies/", "Cookies"),
        "terms": ("/es/terminos/", "Términos"),
        "addr_country": "Noruega",
        "org_line": "N.º org. 935 407 095 IVA",
        "hreflang": "es",
        "home_file": "es/index.html",
        "header_contact": '<a href="#contacto">Contacto</a>',
        "footer_contact_close": "      <a href=\"#contacto\">Contacto</a>\n    </div>",
    },
    "en": {
        "html_lang": "en",
        "og_locale": "en_GB",
        "index_path": "/en/blog/",
        "article_tpl": "/en/blog/{slug}/",
        "home": "/en/",
        "skip_href": "#content",
        "skip_text": "Skip to content",
        "nav_aria": "Main",
        "menu": "Menu",
        "contact_href": "/en/#contact",
        "contact_label": "Contact",
        "footer_pages": "Pages",
        "footer_legal": "Legal",
        "services_href": "/en/#services",
        "services_label": "Services",
        "sectors_href": "/en/#sectors",
        "sectors_label": "Sectors",
        "privacy": ("/en/privacy/", "Privacy"),
        "cookies": ("/en/cookies/", "Cookies"),
        "terms": ("/en/terms/", "Terms"),
        "addr_country": "Norway",
        "org_line": "Org. no. 935 407 095 VAT",
        "hreflang": "en",
        "home_file": "en/index.html",
        "header_contact": '<a href="#contact">Contact</a>',
        "footer_contact_close": "      <a href=\"#contact\">Contact</a>\n    </div>",
    },
    "nb": {
        "html_lang": "no",
        "og_locale": "nb_NO",
        "index_path": "/blogg/",
        "article_tpl": "/blogg/{slug}/",
        "home": "/",
        "skip_href": "#innhold",
        "skip_text": "Hopp til innhold",
        "nav_aria": "Hovedmeny",
        "menu": "Meny",
        "contact_href": "/#kontakt",
        "contact_label": "Kontakt",
        "footer_pages": "Sider",
        "footer_legal": "Juridisk",
        "services_href": "/#tjenester",
        "services_label": "Tjenester",
        "sectors_href": "/#sektorer",
        "sectors_label": "Sektorer",
        "privacy": ("/personvern/", "Personvern"),
        "cookies": ("/cookies/", "Cookies"),
        "terms": ("/vilkar/", "Vilkår"),
        "addr_country": "Norge",
        "org_line": "Org.nr 935 407 095 MVA",
        "hreflang": "no",
        "home_file": "index.html",
        "header_contact": '<a href="#kontakt">Kontakt</a>',
        "footer_contact_close": "      <a href=\"#kontakt\">Kontakt</a>\n    </div>",
    },
}

HOME_HTML = {
    "es": (ROOT / "es/index.html").read_text(encoding="utf-8"),
    "en": (ROOT / "en/index.html").read_text(encoding="utf-8"),
    "nb": (ROOT / "index.html").read_text(encoding="utf-8"),
}


def article_path(lang: str, slug: str) -> str:
    return LANGS[lang]["article_tpl"].format(slug=slug)


def parse_raw(text: str) -> list[dict]:
    if not (text or "").strip():
        return []
    parts = re.split(r"^=== ARTÍCULO\s+(\d+)\s*===[ \t]*\n", text, flags=re.M)
    arts = []
    for i in range(1, len(parts), 2):
        lines = parts[i + 1].splitlines()
        fields: dict[str, str] = {}
        i_ln = 0
        while i_ln < len(lines):
            if not (lines[i_ln].strip() or ""):
                j = i_ln
                while j < len(lines) and not (lines[j].strip() or ""):
                    j += 1
                if j < len(lines) and FIELD_RE.match(lines[j]):
                    i_ln = j
                    continue
                break
            m = FIELD_RE.match(lines[i_ln])
            if not m:
                break
            name, rest = m.group(1), m.group(2)
            if name in MULTILINE:
                acc = []
                if rest.strip():
                    acc.append(rest)
                i_ln += 1
                while i_ln < len(lines) and not FIELD_RE.match(lines[i_ln]):
                    acc.append(lines[i_ln])
                    i_ln += 1
                while acc and acc[-1].strip() == "":
                    acc.pop()
                fields[name] = "\n".join(acc).rstrip()
            else:
                fields[name] = rest.strip()
                i_ln += 1
        remaining = lines[i_ln:]
        while remaining and remaining[0].strip() == "":
            remaining = remaining[1:]
        art = {"index": int(parts[i])}
        for k in KNOWN_FIELDS:
            art[k] = fields.get(k, "")
        art["body"] = "\n".join(remaining).rstrip()
        art["slug"] = (art.get("slug") or "").strip()
        arts.append(art)
    return arts


def parse_faq(block) -> list[dict]:
    if not block:
        return []
    if isinstance(block, list):
        out = []
        for item in block:
            q = (item.get("p") or item.get("q") or "").strip()
            a = (item.get("r") or item.get("a") or "").strip()
            if q and a:
                out.append({"q": q, "a": a})
        return out
    items = []
    current = None
    for line in str(block).splitlines():
        m = re.match(r"^-+\s*P:\s*(.*)$", line.strip())
        if m:
            if current:
                items.append(current)
            current = {"q": m.group(1).strip(), "a": ""}
            continue
        m = re.match(r"^R:\s*(.*)$", line.strip())
        if m and current is not None:
            current["a"] = m.group(1).strip()
            continue
        if current is not None and line.strip():
            if current["a"]:
                current["a"] += " " + line.strip()
            else:
                current["q"] += " " + line.strip()
    if current:
        items.append(current)
    return [x for x in items if x.get("q") and x.get("a")]


def parse_enlaces(block) -> list[tuple[str, str]]:
    if not block:
        return []
    if isinstance(block, list):
        out = []
        for item in block:
            if isinstance(item, dict):
                href = (item.get("href") or "").strip()
                anchor = (item.get("anchor") or href).strip()
                if href:
                    out.append((href, anchor))
            elif isinstance(item, (list, tuple)) and len(item) >= 2:
                out.append((str(item[0]).strip(), str(item[1]).strip()))
        return out
    out = []
    for line in str(block).splitlines():
        s = line.strip()
        if not s:
            continue
        s = re.sub(r"^-\s*", "", s)
        m = re.match(r"^(\S+)\s+[—–-]\s+(.+)$", s)
        if m:
            out.append((m.group(1).strip(), m.group(2).strip()))
        else:
            out.append((s, s))
    return out


def normalize_art(art: dict, lang: str) -> dict:
    if not art["slug"] or not art["titulo"] or not art["body"].strip():
        raise SystemExit(f"incomplete {lang} article: {art.get('slug')!r}")
    art["faq"] = parse_faq(art.get("faq"))
    art["enlaces_internos"] = parse_enlaces(art.get("enlaces_internos"))
    art["titulo_seo"] = art.get("titulo_seo") or art["titulo"]
    art["meta"] = art.get("meta") or ""
    art["resumen"] = art.get("resumen") or ""
    return art


def load_parts(filenames: list) -> list[dict]:
    """Parse each raw file on its own so a part preamble cannot leak into the previous article."""
    arts = []
    for name in filenames:
        path = SRC / name
        if not path.exists():
            raise SystemExit(f"missing {path}")
        arts.extend(parse_raw(path.read_text(encoding="utf-8")))
    return arts


def load_translated(lang: str) -> list[dict]:
    files = [f"raw-{lang}-part{n}.txt" for n in range(1, 7)]
    return [normalize_art(art, lang) for art in load_parts(files)]


def load_es() -> list[dict]:
    files = [f"raw-part{n}.txt" for n in (1, 2, 3)]
    return [normalize_art(art, "es") for art in load_parts(files)]


def load_all() -> dict[str, list[dict]]:
    es = load_es()
    en = load_translated("en")
    nb = load_translated("nb")
    if not (len(es) == len(en) == len(nb) == 30):
        raise SystemExit(f"expected 30 articles per language, got es={len(es)} en={len(en)} nb={len(nb)}")
    es_slugs = [a["slug"] for a in es]
    for lang, arts in (("en", en), ("nb", nb)):
        slugs = [a["slug"] for a in arts]
        if slugs != es_slugs:
            if set(slugs) != set(es_slugs):
                raise SystemExit(f"{lang} slugs do not match ES")
            by = {a["slug"]: a for a in arts}
            arts[:] = [by[s] for s in es_slugs]
    return {"es": es, "en": en, "nb": nb}


def cookie_banner(lang: str) -> str:
    m = re.search(r'<div id="cookie-banner".*?</div>\s*</div>', HOME_HTML[lang], re.S)
    if not m:
        raise SystemExit("cookie banner missing for " + lang)
    return m.group(0)


def siblings_for(current_url: str) -> dict[str, str]:
    for L in LANGS.values():
        if current_url == L["index_path"]:
            return {c: LANGS[c]["index_path"] for c in LANGS}
    m = re.search(r"/(?:es/blog|en/blog|blogg)/([^/]+)/?$", current_url)
    if m:
        slug = m.group(1)
        return {c: article_path(c, slug) for c in LANGS}
    raise SystemExit("cannot map siblings for " + current_url)


def hreflang_links(current_url: str) -> str:
    targets = siblings_for(current_url)
    return "\n".join([
        f'  <link rel="alternate" hreflang="no" href="{SITE}{targets["nb"]}">',
        f'  <link rel="alternate" hreflang="en" href="{SITE}{targets["en"]}">',
        f'  <link rel="alternate" hreflang="es" href="{SITE}{targets["es"]}">',
        f'  <link rel="alternate" hreflang="x-default" href="{SITE}{targets["nb"]}">',
    ])


def header(lang: str, current_url: str) -> str:
    L = LANGS[lang]
    sib = siblings_for(current_url)
    nav = UI[lang]["nav"]

    def lang_a(code: str, label: str) -> str:
        href = sib[code]
        is_cur = href == current_url
        cls = ' class="active"' if is_cur else ""
        cur = ' aria-current="page"' if is_cur else ""
        return (
            f'<a{cls} href="{href}" hreflang="{LANGS[code]["hreflang"]}" '
            f'lang="{LANGS[code]["html_lang"]}"{cur}>{label}</a>'
        )

    on_blog = current_url == L["index_path"] or current_url.startswith(L["index_path"])
    blog_cur = ' aria-current="page"' if on_blog else ""
    return (
        f'<a class="skip" href="{L["skip_href"]}">{L["skip_text"]}</a>\n'
        f'<header class="site-header is-stuck">\n'
        f'  <div class="bar wrap">\n'
        f'    <a class="brand" href="{L["home"]}"><img src="/brand/logo-white.svg" alt="{ORG}" width="563" height="104"></a>\n'
        f'    <button class="nav-toggle" type="button" aria-expanded="false" aria-controls="site-nav">\n'
        f'      <span class="nav-toggle-bars" aria-hidden="true"></span>\n'
        f'      <span class="sr-only">{L["menu"]}</span>\n'
        f'    </button>\n'
        f'    <nav class="site-nav" id="site-nav" aria-label="{L["nav_aria"]}">\n'
        f'      <a href="{L["contact_href"]}">{L["contact_label"]}</a>\n'
        f'      <a href="{L["index_path"]}"{blog_cur}>{html.escape(nav)}</a>\n'
        f'    </nav>\n'
        f'    <div class="langs">\n'
        f'      {lang_a("nb", "NO")}\n'
        f'      {lang_a("en", "EN")}\n'
        f'      {lang_a("es", "ES")}\n'
        f'    </div>\n'
        f'  </div>\n'
        f'</header>'
    )


def footer(lang: str) -> str:
    L = LANGS[lang]
    pr, prl = L["privacy"]
    ck, ckl = L["cookies"]
    te, tel = L["terms"]
    nav = html.escape(UI[lang]["nav"])
    return (
        "<footer>\n"
        "  <div class=\"footer-grid\">\n"
        "    <div>\n"
        "      <strong>MARTINEZ LOZANO INTERNASJONAL HANDEL (ENK)</strong>\n"
        f"      <span>Norbygata 19, 0187 Oslo, {L['addr_country']}</span>\n"
        f"      <span>{L['org_line']}</span>\n"
        "      <a href=\"mailto:info@mlinternasjonal.no\">info@mlinternasjonal.no</a>\n"
        "      <a class=\"btn whatsapp\" href=\"https://wa.me/4792211752\" target=\"_blank\" rel=\"noopener noreferrer\">WhatsApp</a>\n"
        "    </div>\n"
        "    <div>\n"
        f"      <strong>{L['footer_pages']}</strong>\n"
        f"      <a href=\"{L['services_href']}\">{L['services_label']}</a>\n"
        f"      <a href=\"{L['sectors_href']}\">{L['sectors_label']}</a>\n"
        f"      <a href=\"{L['contact_href']}\">{L['contact_label']}</a>\n"
        f"      <a href=\"{L['index_path']}\">{nav}</a>\n"
        "    </div>\n"
        "    <div>\n"
        f"      <strong>{L['footer_legal']}</strong>\n"
        f"      <a href=\"{pr}\">{prl}</a>\n"
        f"      <a href=\"{ck}\">{ckl}</a>\n"
        f"      <a href=\"{te}\">{tel}</a>\n"
        "    </div>\n"
        "  </div>\n"
        "  <div class=\"footer-legal\">\n"
        "    <span>© 2026 MARTINEZ LOZANO INTERNASJONAL HANDEL (ENK)</span>\n"
        "    <span>mlinternasjonal.no</span>\n"
        "  </div>\n"
        "</footer>\n"
        f"{cookie_banner(lang)}\n"
        "<script src=\"/assets/site.js\" defer></script>"
    )


def page_shell(lang, *, title, description, current_url, og_type, og_image, extra_head, main):
    L = LANGS[lang]
    desc_tags = ""
    if description:
        esc_desc = html.escape(description, quote=True)
        desc_tags = (
            f'  <meta name="description" content="{esc_desc}">\n'
            f'  <meta property="og:description" content="{esc_desc}">\n'
            f'  <meta name="twitter:description" content="{esc_desc}">\n'
        )
    esc_title = html.escape(title, quote=True)
    return (
        "<!doctype html>\n"
        f"<html lang=\"{L['html_lang']}\">\n"
        "<head>\n"
        "  <meta charset=\"utf-8\">\n"
        "  <meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">\n"
        f"  <title>{html.escape(title)}</title>\n"
        f"{desc_tags}"
        "  <meta name=\"theme-color\" content=\"#0b1620\">\n"
        f"  <link rel=\"canonical\" href=\"{SITE}{current_url}\">\n"
        f"{hreflang_links(current_url)}\n"
        f"  <meta property=\"og:type\" content=\"{og_type}\">\n"
        f"  <meta property=\"og:locale\" content=\"{L['og_locale']}\">\n"
        "  <meta property=\"og:locale:alternate\" content=\"nb_NO\">\n"
        "  <meta property=\"og:locale:alternate\" content=\"en_GB\">\n"
        "  <meta property=\"og:locale:alternate\" content=\"es_ES\">\n"
        f"  <meta property=\"og:url\" content=\"{SITE}{current_url}\">\n"
        f"  <meta property=\"og:title\" content=\"{esc_title}\">\n"
        f"  <meta property=\"og:site_name\" content=\"{ORG}\">\n"
        f"  <meta property=\"og:image\" content=\"{og_image}\">\n"
        "  <meta name=\"twitter:card\" content=\"summary_large_image\">\n"
        f"  <meta name=\"twitter:title\" content=\"{esc_title}\">\n"
        "  <link rel=\"icon\" href=\"/brand/favicon.svg\" type=\"image/svg+xml\">\n"
        "  <link rel=\"icon\" href=\"/brand/favicon-32.png\" type=\"image/png\" sizes=\"32x32\">\n"
        "  <link rel=\"apple-touch-icon\" href=\"/brand/apple-touch-icon.png\">\n"
        "  <link rel=\"stylesheet\" href=\"/assets/site.css\">\n"
        f"{extra_head}"
        "</head>\n"
        "<body>\n"
        f"{header(lang, current_url)}\n"
        f"{main}\n"
        f"{footer(lang)}\n"
        "</body>\n"
        "</html>\n"
    )


def body_to_html(text: str) -> str:
    lines = text.splitlines()
    out: list[str] = []
    i = 0
    n = len(lines)
    while i < n:
        line = lines[i]
        if line.startswith("### "):
            out.append("<h3>" + html.escape(line[4:].strip()) + "</h3>")
            i += 1
            continue
        if line.startswith("## "):
            out.append("<h2>" + html.escape(line[3:].strip()) + "</h2>")
            i += 1
            continue
        if line.strip() in HEADING_LINES:
            out.append("<h2>" + html.escape(line.strip()) + "</h2>")
            i += 1
            continue
        if line.startswith("- "):
            items = []
            while i < n and lines[i].startswith("- "):
                items.append("<li>" + html.escape(lines[i][2:].strip()) + "</li>")
                i += 1
            out.append("<ul>\n" + "\n".join(items) + "\n</ul>")
            continue
        if line.strip() == "":
            i += 1
            continue
        para = [line]
        i += 1
        while (
            i < n
            and lines[i].strip()
            and not lines[i].startswith("#")
            and lines[i].strip() not in HEADING_LINES
            and not lines[i].startswith("- ")
        ):
            para.append(lines[i])
            i += 1
        out.append("<p>" + html.escape(" ".join(para)) + "</p>")
    return "\n".join(out)


def faq_jsonld(faq: list) -> str:
    entities = []
    for item in faq:
        entities.append({
            "@type": "Question",
            "name": item["q"],
            "acceptedAnswer": {"@type": "Answer", "text": item["a"]},
        })
    return json.dumps({"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": entities}, ensure_ascii=False, indent=2)


def article_jsonld(art, lang, url, image) -> str:
    L = LANGS[lang]
    data = {
        "@context": "https://schema.org",
        "@type": "BlogPosting",
        "headline": art["titulo"],
        "description": art["meta"],
        "image": image,
        "inLanguage": L["html_lang"],
        "mainEntityOfPage": SITE + url,
        "author": {
            "@type": "Organization",
            "name": ORG,
            "legalName": "MARTINEZ LOZANO INTERNASJONAL HANDEL (ENK)",
            "url": SITE + L["home"],
        },
        "publisher": {
            "@type": "Organization",
            "name": ORG,
            "legalName": "MARTINEZ LOZANO INTERNASJONAL HANDEL (ENK)",
            "url": SITE + "/",
            "logo": SITE + "/brand/logo-black.svg",
        },
    }
    return json.dumps(data, ensure_ascii=False, indent=2)


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not content.endswith("\n"):
        content += "\n"
    path.write_text(content, encoding="utf-8")


def cover_picture(slug: str, alt: str, cls: str, loading: str | None) -> str:
    jpg = f"/assets/img/blog/{slug}.jpg"
    webp = f"/assets/img/blog/{slug}.webp"
    load = f' loading="{loading}"' if loading else ""
    cls_attr = f' class="{cls}"' if cls else ""
    esc_alt = html.escape(alt, quote=True)
    return (
        f'<picture>\n'
        f'      <source type="image/webp" srcset="{webp}">\n'
        f'      <img{cls_attr} src="{jpg}" alt="{esc_alt}" width="1280" height="720"{load}>\n'
        f'    </picture>'
    )


def optimize_covers(slugs: list[str]) -> None:
    COVERS_DST.mkdir(parents=True, exist_ok=True)
    for slug in slugs:
        src = COVERS_SRC / f"{slug}.jpg"
        if not src.exists():
            raise SystemExit("missing cover " + str(src))
        im = Image.open(src)
        if im.mode != "RGB":
            im = im.convert("RGB")
        w, h = im.size
        if w > 1600:
            nh = round(h * 1600 / w)
            im = im.resize((1600, nh), Image.Resampling.LANCZOS)
            w, h = im.size
        jpg_path = COVERS_DST / f"{slug}.jpg"
        webp_path = COVERS_DST / f"{slug}.webp"
        im.save(jpg_path, "JPEG", quality=82, optimize=True, progressive=True)
        im.save(webp_path, "WEBP", quality=80, method=6)


def inject_home_nav() -> None:
    for lang, L in LANGS.items():
        path = ROOT / L["home_file"]
        t = path.read_text(encoding="utf-8")
        href = L["index_path"]
        label = html.escape(UI[lang]["nav"])
        blog_a = f'<a href="{href}">{label}</a>'
        if href in t and blog_a in t:
            continue
        if t.count(L["header_contact"]) < 2:
            raise SystemExit("unexpected contact link count in " + str(path))
        header_new = L["header_contact"] + "\n      " + blog_a
        t = t.replace(L["header_contact"], header_new, 1)
        footer_new = f"      {L['header_contact']}\n      {blog_a}\n    </div>"
        if L["footer_contact_close"] not in t:
            raise SystemExit("footer contact block missing in " + str(path))
        t = t.replace(L["footer_contact_close"], footer_new, 1)
        path.write_text(t, encoding="utf-8")


def append_css() -> None:
    css_path = ROOT / "assets/site.css"
    marker = "/* Blog section */"
    extra = "\n" + marker + """
.blog-page {
  padding-top: calc(var(--header) + clamp(2.8rem, 6vw, 4.5rem));
  max-width: 52rem;
}
.blog-index {
  max-width: var(--max);
  margin-inline: auto;
}
.blog-cover,
.blog-page picture:has(.blog-cover) {
  display: block;
  width: 100%;
  margin: 0 0 1.5rem;
}
.blog-cover {
  aspect-ratio: 16 / 9;
  width: 100%;
  object-fit: cover;
  border-radius: var(--radius);
  background: var(--ink);
}
.blog-index-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(16.5rem, 1fr));
  gap: 1.5rem;
  margin: 2rem 0 3rem;
}
.blog-card {
  background: var(--card);
  border-radius: var(--radius);
  overflow: hidden;
  text-decoration: none;
  color: inherit;
  border: 1px solid var(--rule);
  display: flex;
  flex-direction: column;
}
.blog-card:hover {
  color: inherit;
  box-shadow: 0 8px 24px rgba(11, 22, 32, 0.08);
}
.blog-card img {
  aspect-ratio: 16 / 9;
  object-fit: cover;
  width: 100%;
  background: var(--ink);
}
.blog-card .card-body {
  padding: 1rem 1.1rem 1.2rem;
}
.blog-card h2 {
  font-size: 1.15rem;
  letter-spacing: -0.02em;
  margin: 0 0 0.45rem;
}
.blog-card p {
  color: var(--muted);
  font-size: 0.95rem;
  margin: 0;
}
.blog-article ul {
  margin: 0 0 1em;
  padding-left: 1.2rem;
}
.blog-faq {
  margin-top: 2.5rem;
}
.blog-faq dt {
  font-weight: 600;
  color: var(--ink);
  margin-top: 1rem;
}
.blog-faq dd {
  margin: 0.35rem 0 0;
  color: var(--muted);
}
.blog-links {
  margin-top: 2rem;
}
.blog-links ul {
  padding-left: 1.2rem;
}
"""
    css = css_path.read_text(encoding="utf-8")
    if marker in css:
        css = css.split(marker)[0].rstrip() + "\n"
    # Drop a previous staging-only marker if present (should not be in prod).
    staging = "/* Blog section (staging) */"
    if staging in css:
        css = css.split(staging)[0].rstrip() + "\n"
    css_path.write_text(css + extra, encoding="utf-8")


def sitemap_urls(arts: list) -> str:
    existing = (ROOT / "sitemap.xml").read_text(encoding="utf-8")
    for marker in ("  <!-- blog -->", "  <!-- blog (staging) -->"):
        if marker in existing:
            existing = existing.split(marker)[0].rstrip()
    existing = existing.replace("</urlset>", "").rstrip()

    def block(loc: str, alts: dict, freq: str, prio: str) -> str:
        links = "\n".join(
            f'    <xhtml:link rel="alternate" hreflang="{hl}" href="{SITE}{path}"/>'
            for hl, path in (("no", alts["nb"]), ("en", alts["en"]), ("es", alts["es"]), ("x-default", alts["nb"]))
        )
        return (
            "  <url>\n"
            f"    <loc>{SITE}{loc}</loc>\n"
            f"{links}\n"
            f"    <changefreq>{freq}</changefreq>\n"
            f"    <priority>{prio}</priority>\n"
            "  </url>"
        )

    chunks = [existing, "", "  <!-- blog -->"]
    index_alts = {c: LANGS[c]["index_path"] for c in LANGS}
    for code in ("nb", "en", "es"):
        chunks.append(block(index_alts[code], index_alts, "weekly", "0.8"))
    for art in arts:
        slug = art["slug"]
        alts = {c: article_path(c, slug) for c in LANGS}
        for code in ("nb", "en", "es"):
            chunks.append(block(alts[code], alts, "monthly", "0.7"))
    chunks.append("</urlset>\n")
    return "\n".join(chunks)


def build_index(lang: str, arts: list) -> str:
    L = LANGS[lang]
    url = L["index_path"]
    main_id = L["skip_href"].lstrip("#")
    heading = UI[lang]["heading"]
    cards = []
    for art in arts:
        href = article_path(lang, art["slug"])
        title = html.escape(art["titulo"])
        lede = html.escape(art["resumen"]) if art.get("resumen") else ""
        lede_html = f"\n        <p>{lede}</p>" if lede else ""
        pic = cover_picture(art["slug"], art["titulo"], cls="", loading="lazy")
        cards.append(
            f'    <a class="blog-card" href="{href}">\n'
            f'      {pic}\n'
            f'      <div class="card-body">\n        <h2>{title}</h2>{lede_html}\n      </div>\n'
            f'    </a>'
        )
    main = (
        f'<main id="{main_id}" class="page blog-page blog-index" tabindex="-1">\n'
        f'  <h1>{html.escape(heading)}</h1>\n'
        f'  <div class="blog-index-grid">\n'
        + "\n".join(cards)
        + "\n  </div>\n</main>"
    )
    title = f'{heading} | {ORG}'
    return page_shell(
        lang,
        title=title,
        description="",
        current_url=url,
        og_type="website",
        og_image=f"{SITE}/assets/img/hero.webp",
        extra_head="",
        main=main,
    )


def build_article(lang: str, art: dict) -> str:
    L = LANGS[lang]
    slug = art["slug"]
    url = article_path(lang, slug)
    img_path = "/assets/img/blog/" + slug + ".jpg"
    img_abs = SITE + img_path
    main_id = L["skip_href"].lstrip("#")
    page_title = (art.get("titulo_seo") or art["titulo"]) + " | " + ORG
    h1 = art["titulo"]
    description = art.get("meta") or ""
    body_html = body_to_html(art["body"])
    faq = art.get("faq") or []
    faq_html = ""
    extra_parts = []
    if faq:
        dts = []
        for item in faq:
            dts.append("    <dt>" + html.escape(item["q"]) + "</dt>\n    <dd>" + html.escape(item["a"]) + "</dd>")
        # No FAQ heading: no Grok/verbatim label available.
        faq_html = (
            '  <section class="blog-faq" id="faq">\n    <dl>\n'
            + "\n".join(dts)
            + "\n    </dl>\n  </section>"
        )
        extra_parts.append('  <script type="application/ld+json">\n' + faq_jsonld(faq) + "\n  </script>\n")
    links = art.get("enlaces_internos") or []
    links_html = ""
    if links:
        lis = []
        for href, anchor in links:
            lis.append(
                "      <li><a href=\""
                + html.escape(href, quote=True)
                + "\">"
                + html.escape(anchor)
                + "</a></li>"
            )
        # No related heading: no Grok/verbatim label available.
        links_html = (
            '  <nav class="blog-links">\n    <ul>\n'
            + "\n".join(lis)
            + "\n    </ul>\n  </nav>"
        )
    extra_parts.append('  <script type="application/ld+json">\n' + article_jsonld(art, lang, url, img_abs) + "\n  </script>\n")
    pic = cover_picture(slug, h1, cls="blog-cover", loading=None)
    back = html.escape(UI[lang]["back"])
    main = (
        f'<main id="{main_id}" class="page blog-page blog-article" tabindex="-1">\n'
        f'  <a class="back" href="{L["index_path"]}">{back}</a>\n'
        f'  <h1>{html.escape(h1)}</h1>\n'
        f'  {pic}\n'
        f'  {body_html}\n'
        f"{faq_html}\n"
        f"{links_html}\n"
        "</main>"
    )
    return page_shell(
        lang,
        title=page_title,
        description=description,
        current_url=url,
        og_type="article",
        og_image=img_abs,
        extra_head="".join(extra_parts),
        main=main,
    )


def main() -> None:
    by_lang = load_all()
    slugs = [a["slug"] for a in by_lang["es"]]
    optimize_covers(slugs)
    append_css()
    inject_home_nav()
    for lang in ("es", "en", "nb"):
        arts = by_lang[lang]
        index_file = ROOT / LANGS[lang]["index_path"].lstrip("/") / "index.html"
        write(index_file, build_index(lang, arts))
        for art in arts:
            art_file = ROOT / article_path(lang, art["slug"]).lstrip("/") / "index.html"
            write(art_file, build_article(lang, art))
    (ROOT / "sitemap.xml").write_text(sitemap_urls(by_lang["es"]), encoding="utf-8")
    print("built", len(slugs), "articles x 3 langs")
    print("missing_labels:", ",".join(MISSING_LABELS))


if __name__ == "__main__":
    main()
