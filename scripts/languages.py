#!/usr/bin/env python3
"""Language catalog for mlinternasjonal.no.

19 languages in dropdown order. Flag SVGs are 16x12, matching the site
header. This module is imported by apply-translations.py and by the
one-off updater that inserts placeholder languages.

Blog pages are never given language versions.
"""
from __future__ import annotations

import math

SITE = "https://mlinternasjonal.no"


def _svg(inner: str) -> str:
    return (
        '<svg class="lang-flag" viewBox="0 0 16 12" width="20" height="15" '
        'aria-hidden="true" focusable="false">' + inner + "</svg>"
    )


def _star(cx: float, cy: float, ro: float, ri: float | None = None, n: int = 5, rot: float | None = None) -> str:
    if ri is None:
        ri = ro * 0.4
    if rot is None:
        rot = -math.pi / 2
    pts = []
    for i in range(n * 2):
        r = ro if i % 2 == 0 else ri
        a = rot + i * math.pi / n
        pts.append(f"{cx + r * math.cos(a):.2f},{cy + r * math.sin(a):.2f}")
    return f'<polygon points="{" ".join(pts)}" fill="#FFDE00"/>'


# Existing flags already in the HTML; kept here so new pages can reuse them.
FLAG_NO = _svg(
    '<rect width="16" height="12" fill="#BA0C2F"/>'
    '<rect x="4.36" width="2.91" height="12" fill="#fff"/>'
    '<rect y="4.5" width="16" height="3" fill="#fff"/>'
    '<rect x="5.09" width="1.45" height="12" fill="#00205B"/>'
    '<rect y="5.25" width="16" height="1.5" fill="#00205B"/>'
)
FLAG_EN = _svg(
    '<rect width="16" height="12" fill="#012169"/>'
    '<path d="M0 0l16 12M16 0L0 12" stroke="#fff" stroke-width="2.4"/>'
    '<path d="M0 0l16 12M16 0L0 12" stroke="#C8102E" stroke-width="1.2"/>'
    '<path d="M8 0v12M0 6h16" stroke="#fff" stroke-width="4"/>'
    '<path d="M8 0v12M0 6h16" stroke="#C8102E" stroke-width="2.4"/>'
)
FLAG_ES = _svg(
    '<rect width="16" height="12" fill="#AA151B"/>'
    '<rect y="3" width="16" height="6" fill="#F1BF00"/>'
)
FLAG_PE = _svg(
    '<rect width="16" height="12" fill="#D91023"/>'
    '<rect x="5.33" width="5.34" height="12" fill="#fff"/>'
)
FLAG_DA = _svg(
    '<rect width="16" height="12" fill="#C8102E"/>'
    '<rect x="4.5" width="2" height="12" fill="#fff"/>'
    '<rect y="5" width="16" height="2" fill="#fff"/>'
)
FLAG_DE = _svg(
    '<rect width="16" height="4" fill="#000"/>'
    '<rect y="4" width="16" height="4" fill="#D00"/>'
    '<rect y="8" width="16" height="4" fill="#FFCE00"/>'
)
FLAG_NL = _svg(
    '<rect width="16" height="4" fill="#AE1C28"/>'
    '<rect y="4" width="16" height="4" fill="#fff"/>'
    '<rect y="8" width="16" height="4" fill="#21468B"/>'
)
FLAG_SV = _svg(
    '<rect width="16" height="12" fill="#006AA7"/>'
    '<rect x="5" width="2" height="12" fill="#FECC00"/>'
    '<rect y="5" width="16" height="2" fill="#FECC00"/>'
)

# China: red field, five yellow stars (official positions scaled 16x12 from 30x20).
_sx, _sy = 16 / 30, 12 / 20
FLAG_CN = _svg(
    '<rect width="16" height="12" fill="#EE1C25"/>'
    + _star(5 * _sx, 5 * _sy, 3 * _sx, 1.2 * _sx)
    + _star(10 * _sx, 2 * _sy, 1 * _sx, 0.4 * _sx, rot=math.radians(18))
    + _star(12 * _sx, 4 * _sy, 1 * _sx, 0.4 * _sx, rot=math.radians(-36))
    + _star(12 * _sx, 7 * _sy, 1 * _sx, 0.4 * _sx, rot=math.radians(-18))
    + _star(10 * _sx, 9 * _sy, 1 * _sx, 0.4 * _sx, rot=math.radians(0))
)

# Taiwan: red field, blue canton, white 12-ray sun.
_sun = _star(4, 3, 1.85, 0.7, n=12, rot=-math.pi / 2).replace('fill="#FFDE00"', 'fill="#fff"')
FLAG_TW = _svg(
    '<rect width="16" height="12" fill="#FE0000"/>'
    '<rect width="8" height="6" fill="#000095"/>'
    + _sun
    + '<circle cx="4" cy="3" r="0.85" fill="#000095"/>'
    + '<circle cx="4" cy="3" r="0.65" fill="#fff"/>'
)

FLAG_JP = _svg(
    '<rect width="16" height="12" fill="#fff"/>'
    '<circle cx="8" cy="6" r="3.6" fill="#BC002D"/>'
)

FLAG_VN = _svg(
    '<rect width="16" height="12" fill="#DA251D"/>'
    + _star(8, 6, 3.2, 1.25)
)

FLAG_IN = _svg(
    '<rect width="16" height="4" fill="#FF9933"/>'
    '<rect y="4" width="16" height="4" fill="#fff"/>'
    '<rect y="8" width="16" height="4" fill="#138808"/>'
    '<circle cx="8" cy="6" r="1.45" fill="none" stroke="#000088" stroke-width="0.35"/>'
    '<circle cx="8" cy="6" r="0.25" fill="#000088"/>'
    + "".join(
        f'<line x1="8" y1="6" x2="{8 + 1.3 * math.cos(i * math.pi / 12):.2f}" '
        f'y2="{6 + 1.3 * math.sin(i * math.pi / 12):.2f}" stroke="#000088" stroke-width="0.15"/>'
        for i in range(24)
    )
)

# South Korea: white field, taegeuk, four trigrams (simplified at this size).
FLAG_KR = _svg(
    '<rect width="16" height="12" fill="#fff"/>'
    '<circle cx="8" cy="6" r="2.35" fill="#CD2E3A"/>'
    '<path d="M8 6a1.175 1.175 0 0 0-2.35 0 2.35 2.35 0 0 0 2.35 2.35 1.175 1.175 0 0 0 0-2.35 1.175 1.175 0 0 1 0-2.35z" fill="#0047A0"/>'
    # gun (top-left, 3 unbroken)
    '<g stroke="#000" stroke-width="0.42" stroke-linecap="butt">'
    '<path d="M2.2 2.35l2.3-1.35M2.05 3.05l2.3-1.35M1.9 3.75l2.3-1.35"/>'
    # gon (bottom-right, 3 broken)
    '<path d="M11.5 10.15l1.0-.58M13.0 9.28l1.0-.58M11.65 10.85l1.0-.58M13.15 9.98l1.0-.58M11.8 11.55l1.0-.58M13.3 10.68l1.0-.58"/>'
    # ri (top-right, broken / unbroken / broken)
    '<path d="M12.55 2.35l1.0-.58M14.05 1.48l1.0-.58M12.7 3.75l1.0-.58M14.2 2.88l1.0-.58"/>'
    '<path d="M12.55 3.05l2.3-1.35"/>'
    # gam (bottom-left, unbroken / broken / unbroken)
    '<path d="M2.2 9.35l2.3 1.35M2.35 10.75l2.3 1.35"/>'
    '<path d="M2.2 10.05l1.0 .58M3.7 10.92l1.0 .58"/>'
    "</g>"
)

FLAG_TH = _svg(
    '<rect width="16" height="12" fill="#A51931"/>'
    '<rect y="2" width="16" height="8" fill="#F4F5F8"/>'
    '<rect y="4" width="16" height="4" fill="#2D2A4A"/>'
)

# United Arab Emirates (requested for Arabic).
FLAG_AE = _svg(
    '<rect width="16" height="4" fill="#00732F"/>'
    '<rect y="4" width="16" height="4" fill="#fff"/>'
    '<rect y="8" width="16" height="4" fill="#000"/>'
    '<rect width="4.2" height="12" fill="#FF0000"/>'
)

# Malaysia: 14 stripes, blue canton, yellow crescent and 14-point star.
_stripes = "".join(
    f'<rect y="{i * 12 / 14:.3f}" width="16" height="{12 / 14:.3f}" fill="{"#CC0001" if i % 2 == 0 else "#fff"}"/>'
    for i in range(14)
)
_ms_star = _star(6.15, 3, 1.55, 0.62, n=14, rot=-math.pi / 2).replace('fill="#FFDE00"', 'fill="#FFCC00"')
FLAG_MY = _svg(
    _stripes
    + '<rect width="8" height="6" fill="#010066"/>'
    + '<circle cx="4.55" cy="3" r="1.55" fill="#FFCC00"/>'
    + '<circle cx="5.05" cy="3" r="1.25" fill="#010066"/>'
    + _ms_star
)

FLAG_FI = _svg(
    '<rect width="16" height="12" fill="#fff"/>'
    '<rect x="5" width="2" height="12" fill="#002F6C"/>'
    '<rect y="5" width="16" height="2" fill="#002F6C"/>'
)

FLAG_IS = _svg(
    '<rect width="16" height="12" fill="#02529C"/>'
    '<rect x="4.36" width="2.91" height="12" fill="#fff"/>'
    '<rect y="4.5" width="16" height="3" fill="#fff"/>'
    '<rect x="5.09" width="1.45" height="12" fill="#DC1E35"/>'
    '<rect y="5.25" width="16" height="1.5" fill="#DC1E35"/>'
)

FLAG_PT = _svg(
    '<rect width="16" height="12" fill="#FF0000"/>'
    '<rect width="6.4" height="12" fill="#006600"/>'
    '<circle cx="6.4" cy="6" r="2.15" fill="#FFD700"/>'
    '<circle cx="6.4" cy="6" r="1.55" fill="#FF0000"/>'
    '<circle cx="6.4" cy="6" r="1.05" fill="#fff"/>'
    '<rect x="5.85" y="5.15" width="1.1" height="1.7" fill="#FF0000"/>'
)

FLAG_FR = _svg(
    '<rect width="5.33" height="12" fill="#002654"/>'
    '<rect x="5.33" width="5.34" height="12" fill="#fff"/>'
    '<rect x="10.67" width="5.33" height="12" fill="#ED2939"/>'
)

FLAG_IT = _svg(
    '<rect width="5.33" height="12" fill="#009246"/>'
    '<rect x="5.33" width="5.34" height="12" fill="#fff"/>'
    '<rect x="10.67" width="5.33" height="12" fill="#CE2B37"/>'
)

# Dropdown order. path is the URL prefix (no leading language folder for Norwegian).
# code is the visible label in the toggle/menu.
# key is the stable language id used in folders, pageLang(), and translation dirs.
LANGUAGES = [
    {"key": "no", "code": "NO", "path": "", "hreflang": "no", "html_lang": "no", "dir": "ltr", "name": "Norsk", "aria": "Språk: Norsk", "og_locale": "nb_NO", "flag": FLAG_NO, "full": True},
    {"key": "sv", "code": "SV", "path": "sv", "hreflang": "sv", "html_lang": "sv", "dir": "ltr", "name": "Svenska", "aria": "Språk: Svenska", "og_locale": "sv_SE", "flag": FLAG_SV, "full": True},
    {"key": "da", "code": "DA", "path": "da", "hreflang": "da", "html_lang": "da", "dir": "ltr", "name": "Dansk", "aria": "Sprog: Dansk", "og_locale": "da_DK", "flag": FLAG_DA, "full": True},
    {"key": "fi", "code": "FI", "path": "fi", "hreflang": "fi", "html_lang": "fi", "dir": "ltr", "name": "Suomi", "aria": "Language: Suomi", "og_locale": "fi_FI", "flag": FLAG_FI, "full": True},
    {"key": "is", "code": "IS", "path": "is", "hreflang": "is", "html_lang": "is", "dir": "ltr", "name": "Íslenska", "aria": "Language: Íslenska", "og_locale": "is_IS", "flag": FLAG_IS, "full": True},
    {"key": "en", "code": "EN", "path": "en", "hreflang": "en", "html_lang": "en", "dir": "ltr", "name": "English", "aria": "Language: English", "og_locale": "en_GB", "flag": FLAG_EN, "full": True},
    {"key": "es", "code": "ES", "path": "es", "hreflang": "es", "html_lang": "es", "dir": "ltr", "name": "Español", "aria": "Idioma: Español", "og_locale": "es_ES", "flag": FLAG_ES, "full": True},
    {"key": "fr", "code": "FR", "path": "fr", "hreflang": "fr", "html_lang": "fr", "dir": "ltr", "name": "Français", "aria": "Language: Français", "og_locale": "fr_FR", "flag": FLAG_FR, "full": True},
    {"key": "it", "code": "IT", "path": "it", "hreflang": "it", "html_lang": "it", "dir": "ltr", "name": "Italiano", "aria": "Language: Italiano", "og_locale": "it_IT", "flag": FLAG_IT, "full": True},
    {"key": "de", "code": "DE", "path": "de", "hreflang": "de", "html_lang": "de", "dir": "ltr", "name": "Deutsch", "aria": "Sprache: Deutsch", "og_locale": "de_DE", "flag": FLAG_DE, "full": True},
    {"key": "nl", "code": "NL", "path": "nl", "hreflang": "nl", "html_lang": "nl", "dir": "ltr", "name": "Nederlands", "aria": "Taal: Nederlands", "og_locale": "nl_NL", "flag": FLAG_NL, "full": True},
    {"key": "pt", "code": "PT", "path": "pt", "hreflang": "pt", "html_lang": "pt", "dir": "ltr", "name": "Português", "aria": "Language: Português", "og_locale": "pt_PT", "flag": FLAG_PT, "full": True},
    {"key": "qu", "code": "QU", "path": "qu", "hreflang": "qu", "html_lang": "qu", "dir": "ltr", "name": "Runasimi", "aria": "Simi: Runasimi", "og_locale": "es_PE", "flag": FLAG_PE, "full": True},
    {"key": "zh", "code": "ZH", "path": "zh", "hreflang": "zh-Hans", "html_lang": "zh-Hans", "dir": "ltr", "name": "简体中文", "aria": "Language: 简体中文", "og_locale": "zh_CN", "flag": FLAG_CN, "full": True},
    {"key": "ja", "code": "JA", "path": "ja", "hreflang": "ja", "html_lang": "ja", "dir": "ltr", "name": "日本語", "aria": "Language: 日本語", "og_locale": "ja_JP", "flag": FLAG_JP, "full": True},
    {"key": "ko", "code": "KO", "path": "ko", "hreflang": "ko", "html_lang": "ko", "dir": "ltr", "name": "한국어", "aria": "Language: 한국어", "og_locale": "ko_KR", "flag": FLAG_KR, "full": True},
    {"key": "zh-tw", "code": "ZH-TW", "path": "zh-tw", "hreflang": "zh-Hant", "html_lang": "zh-Hant", "dir": "ltr", "name": "繁體中文", "aria": "Language: 繁體中文", "og_locale": "zh_TW", "flag": FLAG_TW, "full": True},
    {"key": "vi", "code": "VI", "path": "vi", "hreflang": "vi", "html_lang": "vi", "dir": "ltr", "name": "Tiếng Việt", "aria": "Language: Tiếng Việt", "og_locale": "vi_VN", "flag": FLAG_VN, "full": True},
    {"key": "th", "code": "TH", "path": "th", "hreflang": "th", "html_lang": "th", "dir": "ltr", "name": "ไทย", "aria": "Language: ไทย", "og_locale": "th_TH", "flag": FLAG_TH, "full": True},
    {"key": "hi", "code": "HI", "path": "hi", "hreflang": "hi", "html_lang": "hi", "dir": "ltr", "name": "हिन्दी", "aria": "Language: हिन्दी", "og_locale": "hi_IN", "flag": FLAG_IN, "full": True},
    {"key": "ms", "code": "MS", "path": "ms", "hreflang": "ms", "html_lang": "ms", "dir": "ltr", "name": "Bahasa Melayu", "aria": "Language: Bahasa Melayu", "og_locale": "ms_MY", "flag": FLAG_MY, "full": True},
    {"key": "ar", "code": "AR", "path": "ar", "hreflang": "ar", "html_lang": "ar", "dir": "rtl", "name": "العربية", "aria": "Language: العربية", "og_locale": "ar_AE", "flag": FLAG_AE, "full": True},
]

NEW_KEYS = ["sv", "da", "fi", "is", "fr", "it", "de", "nl", "pt", "qu", "zh", "ja", "ko", "zh-tw", "vi", "th", "hi", "ms", "ar"]


# Page groups for hreflang and sitemap. Blog is intentionally absent.
# "out" is the slug under each new language folder.
PAGE_GROUPS = [
    {"id": "home", "no": "/", "en": "/en/", "es": "/es/", "out": "/", "priority": "0.9", "changefreq": "weekly"},
    {"id": "who", "no": "/om-oss/", "en": "/en/who-we-are/", "es": "/es/quienes-somos/", "out": "/who-we-are/", "priority": "0.8", "changefreq": "monthly"},
    {"id": "what", "no": "/hva-vi-gjor/", "en": "/en/what-we-do/", "es": "/es/que-hacemos/", "out": "/what-we-do/", "priority": "0.8", "changefreq": "monthly"},
    {"id": "cookies", "no": "/cookies/", "en": "/en/cookies/", "es": "/es/cookies/", "out": "/cookies/", "priority": "0.4", "changefreq": "yearly"},
    {"id": "privacy", "no": "/personvern/", "en": "/en/privacy/", "es": "/es/privacidad/", "out": "/privacy/", "priority": "0.4", "changefreq": "yearly"},
    {"id": "terms", "no": "/vilkar/", "en": "/en/terms/", "es": "/es/terminos/", "out": "/terms/", "priority": "0.4", "changefreq": "yearly"},
]


def by_key(key: str) -> dict:
    for lang in LANGUAGES:
        if lang["key"] == key:
            return lang
    raise KeyError(key)


def href_for(lang: dict) -> str:
    return f"/{lang['path']}/" if lang["path"] else "/"


def menu_link(lang: dict, current_key: str | None = None) -> str:
    current = lang["key"] == current_key
    attrs = f'href="{href_for(lang)}" hreflang="{lang["hreflang"]}" lang="{lang["html_lang"]}"'
    if current:
        attrs += ' class="is-current" aria-current="true"'
    # Do not set dir=rtl on the menu link itself: that flips a single row
    # inside an otherwise LTR dropdown. RTL is applied on the Arabic page
    # via <html dir="rtl">.
    return (
        f"<a {attrs}>{lang['flag']}"
        f'<span class="lang-code">{lang["code"]}</span>'
        f'<span class="lang-name">{lang["name"]}</span></a>'
    )


def menu_links(current_key: str | None = None, from_sv: bool = False) -> str:
    langs = LANGUAGES
    if from_sv:
        langs = [l for l in LANGUAGES if l["key"] in NEW_KEYS]
    return "\n      ".join(menu_link(l, current_key) for l in langs)
