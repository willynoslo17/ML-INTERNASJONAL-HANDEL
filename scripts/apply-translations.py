#!/usr/bin/env python3
"""Build full language pages from Grok translation chunks.

Reads /workspace/ml-traducir/<lang>/chunk-0N.md (key<TAB>text, same keys as
the English chunks in /workspace/ml-traducir/chunk-0N.md) and writes pages
under <lang>/..., plus hreflang alternates and sitemap entries.

Never creates or translates blog pages. The Blog menu item on a generated
page points at the existing English blog (/en/blog/).

Usage:
  python3 scripts/apply-translations.py --lang pt
  python3 scripts/apply-translations.py --all
  python3 scripts/apply-translations.py --lang pt --dry-run
  python3 scripts/apply-translations.py --lang pt --chunks-dir /workspace/ml-traducir/pt
  python3 scripts/apply-translations.py --self-test

Does not invent missing strings: untranslated keys stay in English and are
reported. Does not deploy.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from bs4 import BeautifulSoup, NavigableString

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from languages import (  # noqa: E402
    LANGUAGES,
    PAGE_GROUPS,
    SITE,
    by_key,
    href_for,
    menu_link,
)

EN_CHUNKS = Path("/workspace/ml-traducir")
DEFAULT_LANG_CHUNKS = Path("/workspace/ml-traducir")
# Pages that may be generated. Blog is absent on purpose.
EN_PAGES = {
    "home": ROOT / "en/index.html",
    "who": ROOT / "en/who-we-are/index.html",
    "what": ROOT / "en/what-we-do/index.html",
    "cookies": ROOT / "en/cookies/index.html",
    "privacy": ROOT / "en/privacy/index.html",
    "terms": ROOT / "en/terms/index.html",
    "affiliate": ROOT / "en/affiliate-disclosure/index.html",
}

# Asset version is taken from the current English home page.
_ASSET_RE = re.compile(r"site\.(?:css|js)\?v=([^\"&]+)")


def load_chunks(directory: Path) -> dict[str, str]:
    data: dict[str, str] = {}
    files = sorted(directory.glob("chunk-*.md"))
    if not files:
        raise FileNotFoundError(f"No chunk-*.md files in {directory}")
    for path in files:
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip() or line.startswith("#"):
                continue
            if "\t" not in line:
                continue
            key, text = line.split("\t", 1)
            data[key.strip()] = text
    return data


def asset_version() -> str:
    text = (ROOT / "en/index.html").read_text(encoding="utf-8")
    found = _ASSET_RE.findall(text)
    return found[0] if found else "20261118g"


def soup_of(path: Path) -> BeautifulSoup:
    return BeautifulSoup(path.read_text(encoding="utf-8"), "lxml")


def first(soup: BeautifulSoup, selector: str):
    return soup.select_one(selector)


def set_attr(soup: BeautifulSoup, selector: str, attr: str, value: str, warn: list, key: str) -> None:
    el = first(soup, selector)
    if el is None:
        warn.append(f"missing selector {selector} for {key}")
        return
    el[attr] = value


def set_text(el, value: str) -> None:
    """Replace visible text, keeping a mailto, <code> or <strong> if still present."""
    if el is None:
        return
    # Collect existing special nodes
    mail = el.find("a", href=re.compile(r"^mailto:"))
    code = el.find("code")
    strong = el.find("strong")
    ext = el.find("a", href=re.compile(r"^https?://"))
    el.clear()
    remaining = value
    # Wrap legal name in <strong> if it was strong before and still appears.
    if strong and strong.get_text(strip=True) and strong.get_text(strip=True) in remaining:
        name = strong.get_text(strip=True)
        before, after = remaining.split(name, 1)
        if before:
            el.append(before)
        tag = soup_new("strong")
        tag.string = name
        el.append(tag)
        remaining = after
    if mail and "info@mlinternasjonal.no" in remaining:
        before, after = remaining.split("info@mlinternasjonal.no", 1)
        if before:
            el.append(before)
        a = soup_new("a", href="mailto:info@mlinternasjonal.no")
        a.string = "info@mlinternasjonal.no"
        el.append(a)
        remaining = after
    if code and code.get_text() and code.get_text() in remaining:
        token = code.get_text()
        before, after = remaining.split(token, 1)
        if before:
            el.append(before)
        c = soup_new("code")
        c.string = token
        el.append(c)
        remaining = after
    if ext and ext.get_text(strip=True) and ext.get_text(strip=True) in remaining:
        label = ext.get_text(strip=True)
        before, after = remaining.split(label, 1)
        if before:
            el.append(before)
        a = soup_new("a", href=ext.get("href"), rel=ext.get("rel"), target=ext.get("target"))
        a.string = label
        el.append(a)
        remaining = after
    if remaining:
        el.append(remaining)


def soup_new(name: str, **attrs):
    # Built against a throwaway soup so we can construct tags without a context.
    tag = BeautifulSoup("", "lxml").new_tag(name, **{k: v for k, v in attrs.items() if v is not None})
    return tag


def apply_key(soup: BeautifulSoup, selector: str, key: str, trans: dict, warn: list, attr: str | None = None, index: int = 0, optional: bool = False) -> None:
    if key not in trans:
        warn.append(f"missing key {key}")
        return
    els = soup.select(selector)
    if not els or index >= len(els):
        if not optional:
            warn.append(f"missing selector {selector}[{index}] for {key}")
        return
    el = els[index]
    if attr:
        el[attr] = trans[key]
    else:
        set_text(el, trans[key])


def rewrite_en_urls(soup: BeautifulSoup, lang: dict) -> None:
    """Point internal /en/ links at this language, except the blog."""
    prefix = f"/{lang['path']}"
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if href.startswith("/en/blog") or href == "/en/blog/" or href.startswith("/en/blog/"):
            a["href"] = "/en/blog/" if href.rstrip("/").endswith("blog") or "/en/blog/" == href or href.rstrip("/") == "/en/blog" else "/en/blog/" + href.split("/en/blog/")[-1]
            # Always keep blog on the English site; do not mint /pt/blog/.
            if href == "/en/blog/" or href.rstrip("/") == "/en/blog":
                a["href"] = "/en/blog/"
            else:
                # deep blog links also stay on /en/blog/...
                a["href"] = href
            continue
        if href.startswith("/en/"):
            a["href"] = prefix + href[3:]  # /en/foo -> /pt/foo
        elif href == "/en":
            a["href"] = prefix + "/"
    for tag in soup.find_all("link", href=True):
        rel = tag.get("rel") or []
        if "stylesheet" in rel or "icon" in rel or "apple-touch-icon" in rel:
            continue
        href = tag["href"]
        if href.startswith("https://mlinternasjonal.no/en/"):
            tag["href"] = SITE + prefix + href[len("https://mlinternasjonal.no/en"):]
        elif href.startswith("/en/"):
            tag["href"] = prefix + href[3:]
    for tag in soup.find_all(attrs={"content": True}):
        val = tag["content"]
        if isinstance(val, str) and val.startswith("https://mlinternasjonal.no/en"):
            tag["content"] = SITE + prefix + val[len("https://mlinternasjonal.no/en"):]


def set_head(soup: BeautifulSoup, lang: dict, page_id: str, trans: dict, warn: list) -> None:
    html = soup.find("html")
    html["lang"] = lang["html_lang"]
    if lang["dir"] == "rtl":
        html["dir"] = "rtl"
    elif html.has_attr("dir"):
        del html["dir"]

    group = next(g for g in PAGE_GROUPS if g["id"] == page_id) if page_id in {g["id"] for g in PAGE_GROUPS} else None
    slug = group["out"] if group else "/"
    if page_id == "affiliate":
        slug = "/affiliate-disclosure/"
    path = f"/{lang['path']}{slug}"
    url = SITE + path

    # Canonical and locales
    can = soup.find("link", rel="canonical")
    if can:
        can["href"] = url
    for prop, val in {
        "og:url": url,
        "og:locale": lang["og_locale"],
    }.items():
        tag = soup.find("meta", attrs={"property": prop})
        if tag:
            tag["content"] = val

    # Replace alternate links with the full 19 + x-default, pointing at
    # equivalent pages for no/en/es and at language roots for placeholders
    # unless those languages have been fully built (detected by caller).
    for tag in list(soup.find_all("link", rel="alternate")):
        tag.decompose()
    head = soup.head
    # Insert after canonical if possible
    anchor = can
    for item in LANGUAGES:
        href = equivalent_href(item["key"], page_id, built=None)
        tag = soup.new_tag("link", rel="alternate", hreflang=item["hreflang"], href=SITE + href)
        if anchor:
            anchor.insert_after(tag)
            anchor = tag
        else:
            head.append(tag)
    tag = soup.new_tag("link", rel="alternate", hreflang="x-default", href=SITE + "/")
    if anchor:
        anchor.insert_after(tag)
    else:
        head.append(tag)


def equivalent_href(lang_key: str, page_id: str, built: set[str] | None) -> str:
    """URL path for a language version of this page.

    Fully built languages (or no/en/es) get the equivalent slug.
    Placeholders get the language root. Blog is never built.
    """
    lang = by_key(lang_key)
    if lang_key in {"no", "en", "es"}:
        if page_id == "affiliate":
            return {"no": "/affiliate-disclosure/", "en": "/en/affiliate-disclosure/", "es": "/es/aviso-afiliados/"}[lang_key]
        group = next(g for g in PAGE_GROUPS if g["id"] == page_id)
        return group[lang_key]
    if built is not None and lang_key not in built and page_id != "home":
        return href_for(lang)
    if page_id == "affiliate":
        if built is not None and lang_key not in built:
            return href_for(lang)
        return f"/{lang['path']}/affiliate-disclosure/"
    group = next((g for g in PAGE_GROUPS if g["id"] == page_id), None)
    if not group:
        return href_for(lang)
    return f"/{lang['path']}{group['out']}"


def rebuild_lang_menu(soup: BeautifulSoup, current_key: str, page_id: str, built: set[str] | None) -> None:
    menu = soup.select_one("[data-lang-menu]")
    if not menu:
        return
    menu.clear()
    menu.append("\n      ")
    for item in LANGUAGES:
        href = equivalent_href(item["key"], page_id, built)
        current = item["key"] == current_key
        attrs = {
            "href": href,
            "hreflang": item["hreflang"],
            "lang": item["html_lang"],
        }
        if current:
            attrs["class"] = "is-current"
            attrs["aria-current"] = "true"
        if item["dir"] == "rtl":
            attrs["dir"] = "rtl"
        a = soup.new_tag("a", **attrs)
        # flags as literal HTML
        flag = BeautifulSoup(item["flag"], "lxml")
        svg = flag.find("svg")
        if svg:
            a.append(svg.extract())
        code = soup.new_tag("span", **{"class": "lang-code"})
        code.string = item["code"]
        name = soup.new_tag("span", **{"class": "lang-name"})
        name.string = item["name"]
        a.append(code)
        a.append(name)
        menu.append(a)
        menu.append("\n      ")
    # Toggle flag + code for current language
    lang = by_key(current_key)
    btn = soup.select_one("[data-lang-toggle]")
    if btn:
        btn["aria-label"] = lang["aria"]
        # replace inner flag + label
        btn.clear()
        flag = BeautifulSoup(lang["flag"], "lxml")
        svg = flag.find("svg")
        if svg:
            btn.append(svg.extract())
        span = soup.new_tag("span")
        span.string = lang["code"]
        btn.append(span)
    menu_wrap = soup.select_one("[data-lang-menu]")
    if menu_wrap and menu_wrap.has_attr("aria-label"):
        menu_wrap["aria-label"] = lang["aria"]
    # Brand href
    brand = soup.select_one("a.brand")
    if brand:
        brand["href"] = href_for(lang)


def apply_common(soup: BeautifulSoup, trans: dict, warn: list) -> None:
    apply_key(soup, "a.skip, .skip", "nav.skip", trans, warn, optional=True)
    apply_key(soup, ".nav-toggle .sr-only, .nav-toggle .visually-hidden", "nav.menu", trans, warn, optional=True)
    apply_key(soup, "nav.site-nav", "nav.aria_label", trans, warn, attr="aria-label", optional=True)
    # Menu items by href pattern (English template)
    apply_key(soup, 'nav.site-nav a[href*="who-we-are"]', "nav.who_we_are", trans, warn, optional=True)
    apply_key(soup, 'nav.site-nav a[href*="what-we-do"]', "nav.what_we_do", trans, warn, optional=True)
    apply_key(soup, 'nav.site-nav a[href="#services"], nav.site-nav a[href*="service"]', "nav.services", trans, warn, optional=True)
    apply_key(soup, 'nav.site-nav a[href="#sectors"], nav.site-nav a[href*="sector"]', "nav.sectors", trans, warn, optional=True)
    apply_key(soup, 'nav.site-nav a[href*="blog"]', "nav.blog", trans, warn, optional=True)
    apply_key(soup, 'nav.site-nav a[href="#contact"], nav.site-nav a[href*="contact"]', "nav.contact", trans, warn, optional=True)
    apply_key(soup, "a.brand img, img.brand-logo", "brand.logo.alt", trans, warn, attr="alt")
    apply_key(soup, ".footer-tagline, p.footer-tagline", "footer.tagline", trans, warn, optional=True)
    apply_key(soup, "p.social-label, .social-label", "footer.follow", trans, warn)
    apply_key(soup, "nav.social-links", "footer.social.aria", trans, warn, attr="aria-label")
    for sel, key in [
        ('nav.social-links a[href*="linkedin"]', "footer.social.linkedin"),
        ('nav.social-links a[href*="facebook"]', "footer.social.facebook"),
        ('nav.social-links a[href*="instagram"]', "footer.social.instagram"),
    ]:
        apply_key(soup, sel, key, trans, warn, attr="aria-label")
    # Footer legal heading + links (main footer grid)
    legal_heading = soup.select_one(".footer-grid strong")
    # first strong is company name, second block has Legal
    strongs = soup.select(".footer-grid strong")
    if strongs:
        set_text(strongs[0], trans.get("footer.company_name", strongs[0].get_text()))
        if "footer.company_name" not in trans:
            warn.append("missing key footer.company_name")
    if len(strongs) > 1:
        set_text(strongs[1], trans.get("footer.legal.heading", strongs[1].get_text()))
    apply_key(soup, '.footer-grid a[href*="privacy"], .footer-grid a[href*="privacidad"], .footer-grid a[href*="personvern"]', "footer.legal.privacy", trans, warn, optional=True)
    apply_key(soup, '.footer-grid a[href*="cookie"]', "footer.legal.cookies", trans, warn, optional=True)
    apply_key(soup, '.footer-grid a[href*="terms"], .footer-grid a[href*="terminos"], .footer-grid a[href*="vilkar"]', "footer.legal.terms", trans, warn, optional=True)
    # Address / org lines in the footer (spans)
    spans = soup.select(".footer-grid span")
    # typically address, org
    if len(spans) >= 1 and "footer.address" in trans:
        set_text(spans[0], trans["footer.address"])
    if len(spans) >= 2 and "footer.org" in trans:
        set_text(spans[1], trans["footer.org"])
    apply_key(soup, '.footer-grid a[href^="mailto:"]', "footer.email", trans, warn, optional=True)
    legal_spans = soup.select(".footer-legal span")
    if legal_spans and "footer.copyright" in trans:
        set_text(legal_spans[0], trans["footer.copyright"])
    if len(legal_spans) > 1 and "footer.domain" in trans:
        set_text(legal_spans[1], trans["footer.domain"])
    # Cookie banner (in-page)
    apply_key(soup, "#cookie-banner, .cookie-banner", "cookie.banner.aria", trans, warn, attr="aria-label")
    apply_key(soup, ".cookie-banner p", "cookie.banner.text", trans, warn)
    apply_key(soup, "[data-cookie-accept]", "cookie.banner.accept", trans, warn)
    apply_key(soup, "[data-cookie-reject]", "cookie.banner.reject", trans, warn)
    apply_key(soup, ".cookie-actions a, .cookie-banner a[href*='cookie']", "cookie.banner.policy", trans, warn)


def apply_home(soup: BeautifulSoup, trans: dict, warn: list) -> None:
    apply_key(soup, "title", "home.meta.title", trans, warn)
    apply_key(soup, 'meta[name="description"]', "home.meta.description", trans, warn, attr="content")
    apply_key(soup, 'meta[property="og:title"]', "home.meta.og_title", trans, warn, attr="content")
    apply_key(soup, 'meta[property="og:description"]', "home.meta.og_description", trans, warn, attr="content")
    apply_key(soup, 'meta[property="og:site_name"]', "home.meta.og_site_name", trans, warn, attr="content")
    apply_key(soup, 'meta[name="twitter:title"]', "home.meta.twitter_title", trans, warn, attr="content")
    apply_key(soup, 'meta[name="twitter:description"]', "home.meta.twitter_description", trans, warn, attr="content")
    apply_key(soup, ".hero-copy .eyebrow, .hero .eyebrow", "home.hero.eyebrow", trans, warn)
    apply_key(soup, ".hero-copy h1, .hero h1", "home.hero.title", trans, warn)
    apply_key(soup, ".hero-copy .lede, .hero .lede", "home.hero.lede", trans, warn)
    apply_key(soup, ".hero-copy .actions a, .hero .actions a, .hero-copy .actions .btn", "home.hero.cta", trans, warn)
    apply_key(soup, "#services .section-head .eyebrow", "home.services.eyebrow", trans, warn)
    apply_key(soup, "#services .section-head h2", "home.services.title", trans, warn)
    apply_key(soup, "#services .section-head .lede", "home.services.lede", trans, warn)
    service_keys = ["sourcing", "representation", "matching", "import_export", "business_development"]
    cards = soup.select("#services li.card, #services .cards li")
    for i, sk in enumerate(service_keys):
        if i >= len(cards):
            warn.append(f"missing service card {sk}")
            continue
        h = cards[i].find("h3")
        p = cards[i].find("p")
        img = cards[i].find("img")
        if h and f"home.services.{sk}.title" in trans:
            set_text(h, trans[f"home.services.{sk}.title"])
        if p and f"home.services.{sk}.body" in trans:
            set_text(p, trans[f"home.services.{sk}.body"])
        if img and f"home.services.{sk}.alt" in trans:
            img["alt"] = trans[f"home.services.{sk}.alt"]
    apply_key(soup, "#sectors .section-head .eyebrow", "home.sectors.eyebrow", trans, warn)
    apply_key(soup, "#sectors .section-head h2", "home.sectors.title", trans, warn)
    apply_key(soup, "#sectors .section-head .lede", "home.sectors.lede", trans, warn)
    sector_keys = ["agriculture", "fisheries", "mining", "oil_gas", "renewable", "electronics", "industrial", "construction"]
    sectors = soup.select("#sectors .sectors-grid li")
    for i, sk in enumerate(sector_keys):
        if i >= len(sectors):
            warn.append(f"missing sector {sk}")
            continue
        h = sectors[i].find("h3")
        p = sectors[i].find("p")
        img = sectors[i].find("img")
        if h and f"home.sectors.{sk}.title" in trans:
            set_text(h, trans[f"home.sectors.{sk}.title"])
        if p and f"home.sectors.{sk}.body" in trans:
            set_text(p, trans[f"home.sectors.{sk}.body"])
        if img and f"home.sectors.{sk}.alt" in trans:
            img["alt"] = trans[f"home.sectors.{sk}.alt"]
    apply_key(soup, "#contact .eyebrow", "home.contact.eyebrow", trans, warn)
    apply_key(soup, "#contact h2", "home.contact.title", trans, warn)
    # lede is the first .lede in the contact card; email is a following p or a
    apply_key(soup, "#contact .lede", "home.contact.lede", trans, warn)
    apply_key(soup, "label[for='sector']", "form.sector.label", trans, warn)
    apply_key(soup, "label[for='service']", "form.service.label", trans, warn)
    apply_key(soup, "label[for='name']", "form.name.label", trans, warn)
    apply_key(soup, "label[for='company']", "form.company.label", trans, warn)
    apply_key(soup, "label[for='country']", "form.country.label", trans, warn)
    apply_key(soup, "label[for='email']", "form.email.label", trans, warn)
    apply_key(soup, "label[for='consulta']", "form.inquiry.label", trans, warn)
    apply_key(soup, "#contact-form button[type='submit']", "form.submit", trans, warn)
    # options: first is placeholder, then 8 sectors / 5 services — keep option values
    sector_opts = soup.select("select#sector option")
    sector_opt_keys = ["placeholder", "agriculture", "fisheries", "mining", "oil_gas", "renewable", "electronics", "industrial", "construction"]
    for i, ok in enumerate(sector_opt_keys):
        key = f"form.sector.{ok}"
        if i < len(sector_opts) and key in trans:
            set_text(sector_opts[i], trans[key])
        elif key not in trans:
            warn.append(f"missing key {key}")
    service_opts = soup.select("select#service option")
    service_opt_keys = ["placeholder", "sourcing", "representation", "matching", "import_export", "business_development"]
    for i, ok in enumerate(service_opt_keys):
        key = f"form.service.{ok}"
        if i < len(service_opts) and key in trans:
            set_text(service_opts[i], trans[key])
        elif key not in trans:
            warn.append(f"missing key {key}")
    # JSON-LD description
    for script in soup.find_all("script", attrs={"type": "application/ld+json"}):
        if script.string and "og_description" in " ".join(trans):
            desc = trans.get("home.meta.og_description")
            if desc:
                script.string = re.sub(
                    r'"description"\s*:\s*".*?"',
                    lambda m: '"description": ' + _json_str(desc),
                    script.string,
                    count=1,
                )


def _json_str(text: str) -> str:
    import json
    return json.dumps(text, ensure_ascii=False)


def apply_who(soup: BeautifulSoup, trans: dict, warn: list) -> None:
    apply_key(soup, "title", "who.meta.title", trans, warn)
    apply_key(soup, 'meta[name="description"]', "who.meta.description", trans, warn, attr="content")
    apply_key(soup, 'meta[property="og:title"]', "who.meta.og_title", trans, warn, attr="content")
    apply_key(soup, 'meta[property="og:description"]', "who.meta.og_description", trans, warn, attr="content")
    apply_key(soup, "main h1", "who.title", trans, warn)
    ps = soup.select("main p")
    if ps:
        if "who.p1" in trans:
            set_text(ps[0], trans["who.p1"])
        if len(ps) > 1 and "who.p2" in trans:
            set_text(ps[1], trans["who.p2"])
    apply_key(soup, "main h2", "who.values.title", trans, warn)
    items = soup.select("main ul.value-list li, main ul li")
    for i, key in enumerate(["who.values.delivery", "who.values.clarity", "who.values.continuity"]):
        if i < len(items) and key in trans:
            set_text(items[i], trans[key])
        elif key not in trans:
            warn.append(f"missing key {key}")


def apply_what(soup: BeautifulSoup, trans: dict, warn: list) -> None:
    apply_key(soup, "title", "what.meta.title", trans, warn)
    apply_key(soup, 'meta[name="description"]', "what.meta.description", trans, warn, attr="content")
    apply_key(soup, 'meta[property="og:title"]', "what.meta.og_title", trans, warn, attr="content")
    apply_key(soup, 'meta[property="og:description"]', "what.meta.og_description", trans, warn, attr="content")
    apply_key(soup, "main h1", "what.title", trans, warn)
    apply_key(soup, "main > p, main p", "what.lede", trans, warn)
    apply_key(soup, "main h2", "what.process.title", trans, warn)
    items = soup.select("main ul.process-list li, main ul li")
    for i in range(1, 7):
        key = f"what.process.{i}"
        if i - 1 < len(items) and key in trans:
            set_text(items[i - 1], trans[key])
        elif key not in trans:
            warn.append(f"missing key {key}")


def apply_legal_shell(soup: BeautifulSoup, trans: dict, warn: list, prefix: str, title_is: str) -> None:
    apply_key(soup, "a.back", "legal.back" if prefix != "legal.affiliate" else "legal.affiliate.back", trans, warn)
    if prefix != "legal.affiliate":
        apply_key(soup, ".eyebrow, main .eyebrow", "legal.eyebrow", trans, warn)
    apply_key(soup, "main h1", f"{prefix}.title", trans, warn)
    apply_key(soup, "title", f"{prefix}.meta.title" if prefix != "legal.affiliate" else "legal.affiliate.meta.title", trans, warn)
    if prefix != "legal.affiliate":
        apply_key(soup, 'meta[name="description"]', f"{prefix}.meta.description", trans, warn, attr="content")
        apply_key(soup, 'meta[property="og:title"]', f"{prefix}.og_title", trans, warn, attr="content")


def apply_cookies(soup: BeautifulSoup, trans: dict, warn: list) -> None:
    apply_legal_shell(soup, trans, warn, "legal.cookies", "Cookie policy")
    ps = soup.select("main p")
    # 0 updated, 1 body, 2 pixel, 3 contact, 4 controller, maybe button in a p
    mapping = [
        (0, "legal.cookies.updated"),
        (1, "legal.cookies.body"),
        (2, "legal.cookies.pixel"),
        (3, "legal.cookies.contact"),
        (4, "legal.cookies.controller"),
    ]
    for idx, key in mapping:
        if idx < len(ps) and key in trans:
            set_text(ps[idx], trans[key])
        elif key not in trans:
            warn.append(f"missing key {key}")
    apply_key(soup, "[data-cookie-reset]", "legal.cookies.change_choice", trans, warn)


def apply_privacy(soup: BeautifulSoup, trans: dict, warn: list) -> None:
    apply_legal_shell(soup, trans, warn, "legal.privacy", "Privacy policy")
    # After back/eyebrow/h1: first real content p is updated, then intro
    ps = [p for p in soup.select("main > p") if not p.find("button")]
    # intro may contain a stray nested footer-tagline in the EN source; we
    # replace the whole intended intro from the clean key.
    if ps and "legal.privacy.updated" in trans:
        set_text(ps[0], trans["legal.privacy.updated"])
    # The intro is messy in EN HTML (nested tagline). Replace the following
    # sibling mess with a single clean paragraph.
    h1 = soup.select_one("main h1")
    intro_el = None
    if h1:
        # skip updated p, next p is intro (possibly broken)
        nxt = h1.find_next_sibling("p")
        if nxt:
            nxt = nxt.find_next_sibling("p")
            intro_el = nxt
    if intro_el is not None and "legal.privacy.intro" in trans:
        stray = intro_el.find("p", class_="footer-tagline")
        if stray:
            stray.decompose()
        set_text(intro_el, trans["legal.privacy.intro"])
        sib = intro_el.next_sibling
        while sib is not None:
            nxt = sib.next_sibling
            name = getattr(sib, "name", None)
            if name == "h2":
                break
            classes = sib.get("class") if name else None
            text = sib if isinstance(sib, NavigableString) else ""
            if name == "p" and classes and "footer-tagline" in classes:
                sib.decompose()
            elif isinstance(sib, NavigableString) and (
                not str(sib).strip() or "org. no." in str(sib) or "processes personal data" in str(sib)
                or "trata datos" in str(sib) or "behandler personopplysninger" in str(sib)
            ):
                sib.extract()
            else:
                break
            sib = nxt
    for n in range(1, 9):
        apply_key(soup, "main h2", f"legal.privacy.{n}.title", trans, warn, index=n - 1)
    # section bodies / lists in document order after each h2
    h2s = soup.select("main h2")
    body_keys = {
        1: ["legal.privacy.1.body"],
        2: [f"legal.privacy.2.item{i}" for i in range(1, 6)],
        3: [f"legal.privacy.3.item{i}" for i in range(1, 5)],
        4: ["legal.privacy.4.body"],
        5: ["legal.privacy.5.body"],
        6: ["legal.privacy.6.body"],
        7: ["legal.privacy.7.body"],
        8: ["legal.privacy.8.body"],
    }
    for n, keys in body_keys.items():
        if n - 1 >= len(h2s):
            continue
        block = h2s[n - 1]
        sib = block.find_next_sibling()
        if sib and sib.name == "ul":
            lis = sib.find_all("li", recursive=False)
            for i, key in enumerate(keys):
                if i < len(lis) and key in trans:
                    set_text(lis[i], trans[key])
                elif key not in trans:
                    warn.append(f"missing key {key}")
        elif sib and sib.name == "p":
            if keys and keys[0] in trans:
                set_text(sib, trans[keys[0]])
            elif keys:
                warn.append(f"missing key {keys[0]}")


def apply_terms(soup: BeautifulSoup, trans: dict, warn: list) -> None:
    apply_legal_shell(soup, trans, warn, "legal.terms", "Terms of use")
    ps = soup.select("main > p")
    if ps and "legal.terms.updated" in trans:
        set_text(ps[0], trans["legal.terms.updated"])
    if len(ps) > 1 and "legal.terms.intro" in trans:
        set_text(ps[1], trans["legal.terms.intro"])
    for n in range(1, 8):
        apply_key(soup, "main h2", f"legal.terms.{n}.title", trans, warn, index=n - 1)
    # bodies follow each h2
    h2s = soup.select("main h2")
    for n, h in enumerate(h2s, 1):
        key = f"legal.terms.{n}.body"
        sib = h.find_next_sibling("p")
        if sib and key in trans:
            set_text(sib, trans[key])
        elif key not in trans:
            warn.append(f"missing key {key}")


def apply_affiliate(soup: BeautifulSoup, trans: dict, warn: list) -> None:
    apply_key(soup, "title", "legal.affiliate.meta.title", trans, warn)
    apply_key(soup, "a.back", "legal.affiliate.back", trans, warn)
    apply_key(soup, "main h1", "legal.affiliate.title", trans, warn)
    apply_key(soup, "main p", "legal.affiliate.body", trans, warn)


APPLIERS = {
    "home": apply_home,
    "who": apply_who,
    "what": apply_what,
    "cookies": apply_cookies,
    "privacy": apply_privacy,
    "terms": apply_terms,
    "affiliate": apply_affiliate,
}

OUT_SLUG = {
    "home": "/",
    "who": "/who-we-are/",
    "what": "/what-we-do/",
    "cookies": "/cookies/",
    "privacy": "/privacy/",
    "terms": "/terms/",
    "affiliate": "/affiliate-disclosure/",
}


def build_language(lang_key: str, trans: dict, built: set[str], dest_root: Path, dry: bool) -> list[str]:
    lang = by_key(lang_key)
    warn: list[str] = []
    used_keys: set[str] = set()
    # Track keys referenced by wrapping apply_key — we also record below.
    for page_id, src in EN_PAGES.items():
        if not src.exists():
            warn.append(f"missing EN template {src}")
            continue
        soup = soup_of(src)
        apply_common(soup, trans, warn)
        APPLIERS[page_id](soup, trans, warn)
        rewrite_en_urls(soup, lang)
        set_head(soup, lang, page_id, trans, warn)
        rebuild_lang_menu(soup, lang_key, page_id, built | {lang_key})
        # Cookie policy href should be this language
        for a in soup.select(".cookie-actions a, .cookie-banner a"):
            href = a.get("href") or ""
            if "cookie" in href:
                a["href"] = f"/{lang['path']}/cookies/"
        slug = OUT_SLUG[page_id]
        out = dest_root / lang["path"] / (slug.lstrip("/") + ("index.html" if slug.endswith("/") or slug == "/" else "/index.html"))
        if slug == "/":
            out = dest_root / lang["path"] / "index.html"
        # affiliate stays noindex
        if page_id == "affiliate":
            robots = soup.find("meta", attrs={"name": "robots"})
            if robots:
                robots["content"] = "noindex,nofollow"
        html = str(soup)
        # BeautifulSoup may add <html>/<body> wrappers around fragments; we
        # started from a full document, lxml keeps doctype sometimes missing.
        if not html.lstrip().lower().startswith("<!doctype"):
            html = "<!doctype html>\n" + html
        if dry:
            print(f"  DRY {out.relative_to(dest_root)} ({len(html)} bytes)")
        else:
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(html, encoding="utf-8")
            print(f"  wrote {out.relative_to(dest_root)}")
    return warn


def update_site_js(lang_key: str, trans: dict, dry: bool, warn: list) -> None:
    """If cookie/form keys exist, write a real COOKIE_COPY / messages entry."""
    js_path = ROOT / "assets/site.js"
    js = js_path.read_text(encoding="utf-8")
    lang = by_key(lang_key)
    needed = ["cookie.banner.text", "cookie.banner.accept", "cookie.banner.reject", "cookie.banner.policy"]
    if all(k in trans for k in needed):
        href = f"/{lang['path']}/cookies/"
        block = (
            f'    {js_key(lang_key)}: {{\n'
            f'      text: {js_str(trans["cookie.banner.text"])},\n'
            f'      accept: {js_str(trans["cookie.banner.accept"])},\n'
            f'      reject: {js_str(trans["cookie.banner.reject"])},\n'
            f'      policy: {js_str(trans["cookie.banner.policy"])},\n'
            f'      policyHref: {js_str(href)},\n'
            f'    }},\n'
        )
        # Insert before the closing of COOKIE_COPY if not already a real entry.
        needle = f"COOKIE_COPY{js_assign(lang_key)}"
        # Replace alias with a comment that a real entry exists, and add entry
        # inside the object (before the closing }; of COOKIE_COPY).
        obj_end = js.find("  };\n\n  COOKIE_COPY.")
        if obj_end == -1:
            warn.append("could not find COOKIE_COPY object end")
        else:
            if f"{js_key(lang_key)}:" not in js[js.find("const COOKIE_COPY"):obj_end]:
                js = js[:obj_end] + block + js[obj_end:]
            # remove alias assignment if present
            js = re.sub(
                rf"\n  COOKIE_COPY{re.escape(js_assign(lang_key))} = COOKIE_COPY\.en;",
                "",
                js,
            )
    form_needed = ["form.status.sending", "form.status.ok", "form.status.error"]
    if all(k in trans for k in form_needed):
        entry = (
            f'      {js_key(lang_key)}: {{\n'
            f'        sending: {js_str(trans["form.status.sending"])},\n'
            f'        ok: {js_str(trans["form.status.ok"])},\n'
            f'        err: {js_str(trans["form.status.error"])},\n'
            f'      }},\n'
        )
        m = re.search(r"const messages = \{[\s\S]*?es: \{[\s\S]*?\},\n    \};", js)
        if m and f"{js_key(lang_key)}:" not in m.group(0):
            insert_at = m.end() - 6  # before };
            # find last }; of messages more carefully
            end = m.end()
            js = js[: m.end() - 4] + entry + "    };" + js[m.end():]
            # that's fragile; do a simpler replace of the es block closing
        messages_es = """      es: {
        sending: \"Enviando…\",
        ok: \"Gracias por tu mensaje. Te contactaremos pronto.\",
        err: \"No se pudo enviar el mensaje. Inténtalo de nuevo o escríbenos a info@mlinternasjonal.no.\",
      },
    };"""
        if messages_es in js and f"{js_key(lang_key)}:" not in js[js.find("const messages"):js.find("const messages")+800]:
            js = js.replace(
                messages_es,
                messages_es.replace("    };", entry + "    };"),
                1,
            )
    if dry:
        print("  DRY site.js cookie/form update")
        return
    js_path.write_text(js, encoding="utf-8")


def js_key(lang_key: str) -> str:
    return f'"{lang_key}"' if "-" in lang_key else lang_key


def js_assign(lang_key: str) -> str:
    return f'["{lang_key}"]' if "-" in lang_key else f".{lang_key}"


def js_str(text: str) -> str:
    import json
    return json.dumps(text, ensure_ascii=False)


def update_sitemap(lang_key: str, dry: bool) -> None:
    """Add xhtml alternates and loc entries for fully built (non-blog) pages."""
    path = ROOT / "sitemap.xml"
    xml = path.read_text(encoding="utf-8")
    lang = by_key(lang_key)
    changed = False
    for group in PAGE_GROUPS:
        loc = SITE + f"/{lang['path']}{group['out']}"
        if loc in xml:
            # still ensure alternate exists on the no/en/es entries
            pass
        else:
            # insert a new <url> block before </urlset>
            alts = []
            for item in LANGUAGES:
                # only no/en/es plus this lang in the new block? include all full ones
                href = SITE + equivalent_href(item["key"], group["id"], built={lang_key, "no", "en", "es"})
                alts.append(f'    <xhtml:link rel="alternate" hreflang="{item["hreflang"]}" href="{href}"/>')
            alts.append(f'    <xhtml:link rel="alternate" hreflang="x-default" href="{SITE}/"/>')
            block = (
                "  <url>\n"
                f"    <loc>{loc}</loc>\n"
                + "\n".join(alts) + "\n"
                f"    <changefreq>{group['changefreq']}</changefreq>\n"
                f"    <priority>{group['priority']}</priority>\n"
                "  </url>\n"
            )
            xml = xml.replace("</urlset>", block + "</urlset>")
            changed = True
        # Add this language as an alternate on the no/en/es loc blocks
        for existing in (group["no"], group["en"], group["es"]):
            existing_loc = SITE + existing
            needle = f"<loc>{existing_loc}</loc>"
            alt = f'<xhtml:link rel="alternate" hreflang="{lang["hreflang"]}" href="{loc}"/>'
            if needle in xml and alt not in xml:
                xml = xml.replace(needle, needle + "\n    " + alt, 1)
                changed = True
    if changed and not dry:
        path.write_text(xml, encoding="utf-8")
        print(f"  updated sitemap.xml for {lang_key}")
    elif changed:
        print(f"  DRY sitemap.xml update for {lang_key}")


def update_existing_hreflang(lang_key: str, dry: bool) -> None:
    """Add rel=alternate on NO/EN/ES (non-blog) pages for a newly built language."""
    lang = by_key(lang_key)
    for group in PAGE_GROUPS:
        href = SITE + f"/{lang['path']}{group['out']}"
        tag = f'<link rel="alternate" hreflang="{lang["hreflang"]}" href="{href}">'
        for rel_key in ("no", "en", "es"):
            rel_path = group[rel_key]
            file = ROOT / ("index.html" if rel_path == "/" else rel_path.lstrip("/") + ("index.html" if rel_path.endswith("/") else "/index.html"))
            # /en/ -> en/index.html already handled
            if rel_path == "/":
                file = ROOT / "index.html"
            elif rel_path.endswith("/"):
                file = ROOT / rel_path.lstrip("/") / "index.html"
            if not file.exists():
                continue
            text = file.read_text(encoding="utf-8")
            if tag in text:
                continue
            # insert before x-default if present, else after last alternate
            if 'hreflang="x-default"' in text:
                new = text.replace(
                    '<link rel="alternate" hreflang="x-default"',
                    tag + "\n  " + '<link rel="alternate" hreflang="x-default"',
                    1,
                )
            elif "rel=\"alternate\"" in text:
                # after last alternate line
                lines = text.splitlines()
                last = max(i for i, ln in enumerate(lines) if "rel=\"alternate\"" in ln)
                lines.insert(last + 1, "  " + tag)
                new = "\n".join(lines) + ("\n" if text.endswith("\n") else "")
            else:
                continue
            if not dry:
                file.write_text(new, encoding="utf-8")
            else:
                print(f"  DRY hreflang on {file.relative_to(ROOT)}")


def detect_built(dest_root: Path) -> set[str]:
    built = {"no", "en", "es"}
    for lang in LANGUAGES:
        if lang["key"] in built:
            continue
        # A language is "fully built" if who-we-are exists (placeholders only have index.html).
        if (dest_root / lang["path"] / "who-we-are" / "index.html").exists():
            built.add(lang["key"])
    return built


def self_test() -> int:
    """Apply the English source chunks into a temp tree as a mapping check."""
    import tempfile
    trans = load_chunks(EN_CHUNKS)
    dest = Path("/tmp/ml-i18n-self-test")
    if dest.exists():
        import shutil
        shutil.rmtree(dest)
    dest.mkdir()
    warn = build_language("pt", trans, {"no", "en", "es", "pt"}, dest, dry=False)
    # Must not write a blog tree
    if list(dest.rglob("blog/**/*.html")) or (dest / "pt/blog").exists():
        print("FAIL: script wrote a blog language version")
        return 1
    home = (dest / "pt/index.html").read_text(encoding="utf-8")
    checks = [
        ("hero title", "International trade that gets done." in home),
        ("19 langs", home.count('class="lang-code"') == 19),
        ("PT current", 'aria-current="true"' in home and "Português" in home),
        ("blog href stays EN", 'href="/en/blog/"' in home and "/pt/blog" not in home),
        ("spain flag", "#AA151B" in home),
        ("peru flag on QU", "#D91023" in home),
        ("no doctype missing", home.lstrip().lower().startswith("<!doctype")),
        ("lang pt", 'lang="pt"' in home[:200]),
    ]
    ok = True
    for name, passed in checks:
        print(("OK  " if passed else "FAIL"), name)
        ok = ok and passed
    # unused EN keys that are not blog.* 
    # (we don't try to assert every key landed)
    if warn:
        # Filter expected 'missing selector' on pages that don't have a full header
        interesting = [w for w in warn if not w.startswith("missing selector nav.") and "nav.menu" not in w and "nav.skip" not in w and "nav.aria" not in w]
        print(f"{len(warn)} warnings ({len(interesting)} not nav-related). Sample:")
        for w in warn[:25]:
            print("  -", w)
    print("self-test", "passed" if ok else "failed", "->", dest)
    return 0 if ok else 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--lang", help="Language key, e.g. pt, fr, zh, zh-tw, ar")
    parser.add_argument("--all", action="store_true", help="Build every language that has a chunks folder")
    parser.add_argument("--chunks-dir", type=Path, help="Folder of chunk-*.md (default /workspace/ml-traducir/<lang>/)")
    parser.add_argument("--out-dir", type=Path, default=ROOT, help="Site root to write into (default: the repo)")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--self-test", action="store_true", help="Apply English chunks into /tmp as Português to verify mapping")
    parser.add_argument("--skip-sitemap", action="store_true")
    parser.add_argument("--skip-js", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        return self_test()

    keys: list[str] = []
    if args.all:
        for lang in LANGUAGES:
            if lang["key"] in {"no", "en", "es"}:
                continue
            folder = DEFAULT_LANG_CHUNKS / lang["key"]
            if folder.is_dir() and any(folder.glob("chunk-*.md")):
                keys.append(lang["key"])
        if not keys:
            print("No translation folders found under", DEFAULT_LANG_CHUNKS)
            print("Expected e.g. /workspace/ml-traducir/pt/chunk-01.md")
            return 0
    elif args.lang:
        keys = [args.lang]
    else:
        parser.error("pass --lang, --all or --self-test")

    overall_ok = True
    for lang_key in keys:
        try:
            by_key(lang_key)
        except KeyError:
            print(f"Unknown language {lang_key}")
            return 2
        chunks_dir = args.chunks_dir or (DEFAULT_LANG_CHUNKS / lang_key)
        print(f"== {lang_key} from {chunks_dir} ==")
        try:
            trans = load_chunks(chunks_dir)
        except FileNotFoundError as exc:
            print(exc)
            overall_ok = False
            continue
        built = detect_built(args.out_dir)
        warn = build_language(lang_key, trans, built, args.out_dir, args.dry_run)
        if not args.skip_js and args.out_dir == ROOT:
            update_site_js(lang_key, trans, args.dry_run, warn)
        if not args.skip_sitemap and args.out_dir == ROOT:
            update_sitemap(lang_key, args.dry_run)
            update_existing_hreflang(lang_key, args.dry_run)
        if warn:
            print(f"{len(warn)} warnings:")
            for w in warn:
                print("  -", w)
        # Never write blog trees
        if (args.out_dir / by_key(lang_key)["path"] / "blog").exists():
            print("ERROR: blog language folder was created; removing is required. Blogs must not be translated.")
            overall_ok = False
    return 0 if overall_ok else 1


if __name__ == "__main__":
    sys.exit(main())
