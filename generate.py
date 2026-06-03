#!/usr/bin/env python3
"""
Build a static, accessible "Free Summer Meals in Anchorage" page from the
public USDA-FNS Summer Meals Site Finder feature service.

Outputs (into ./docs by default, the GitHub Pages source folder):
  - index.html   accessible, mobile-first page (Today view + full week)
  - sites.txt    plain-text version (low-bandwidth / copy-paste / SMS body)
  - data.json    the cleaned, filtered records (handy for reuse)

No third-party dependencies. Standard library only, so the GitHub Action
needs no `pip install` step.

Configuration is via environment variables (all optional):
  SERVICE_URL   full .../FeatureServer/0/query endpoint for the CURRENT season
  OUT_DIR       output directory (default: docs)
  MOCK_DATA     path to a local JSON file shaped like an ArcGIS query response
                (used for offline testing/preview; skips the network)
"""

import os
import re
import sys
import json
import html
from datetime import datetime, date
from urllib.parse import urlencode, quote
from urllib.request import urlopen, Request

import i18n  # first-party page-chrome translations (data only, no third-party)

try:
    from zoneinfo import ZoneInfo
    TZ = ZoneInfo("America/Anchorage")
except Exception:  # pragma: no cover
    TZ = None

# --------------------------------------------------------------------------
# CONFIG
# --------------------------------------------------------------------------

# IMPORTANT: confirm the current-season service before going live.
# Verified live on 2026-06-03 by listing the org's service directory
#   https://services1.arcgis.com/RLQu0rK7h4kbsBq5/arcgis/rest/services
# The older "Summer_Meal_Site_Finder_<year>_WFL1" naming was dropped; the only
# service carrying real, Season=2026 Alaska data is the one below. Its name
# still says "(Testing)" on USDA's side -- see README/CLAUDE.md for the open
# question. Because this is read from the SERVICE_URL repo variable, swapping
# to a renamed production endpoint later is a one-line change (no code edit).
SERVICE_URL = os.environ.get("SERVICE_URL") or (
    "https://services1.arcgis.com/RLQu0rK7h4kbsBq5/arcgis/rest/services/"
    "Summer_Meals_Site_Finder_2026_(Testing)/FeatureServer/0/query"
)

OUT_DIR = os.environ.get("OUT_DIR", "docs")

# Scope = the Municipality of Anchorage. The user asked for "Anchorage only";
# because the MOA includes these communities, they are included by default.
# To restrict to the city proper, set SCOPE_CITIES = {"anchorage"}.
SCOPE_CITIES = {
    "anchorage", "eagle river", "chugiak", "girdwood", "indian",
    "bird creek", "peters creek", "jber",
    "joint base elmendorf-richardson", "elmendorf", "fort richardson",
    # Misspellings seen in the live feed (city is hand-entered). Keep these so
    # real Anchorage sites aren't silently dropped from scope.
    "anchroage", "anchorage ", "ancorage",
}

# Correct obvious city typos for DISPLAY only (the feed is hand-entered). Scope
# matching tolerates these regardless via the entries above.
CITY_FIXES = {
    "anchroage": "Anchorage",
    "ancorage": "Anchorage",
    "anchorage ": "Anchorage",
}

OFFICIAL_FINDER = "https://www.fns.usda.gov/sfsp/sitefinder"
STATE_AGENCY = "https://education.alaska.gov/cnp"  # AK Child Nutrition Programs
HUNGER_HOTLINE = "1-866-348-6479"

# Public canonical origin (the custom domain set via docs/CNAME). Used for
# canonical/hreflang/Open Graph absolute URLs. Override with SITE_URL env if the
# domain changes.
SITE_URL = os.environ.get("SITE_URL", "https://summermeals.codeforanchorage.org")
REPO_URL = "https://github.com/codeforanchorage/summer-meals-anchorage"
ISSUES_URL = REPO_URL + "/issues"

# og:locale values per page language (best-effort region pairing).
OG_LOCALE = {"en": "en_US", "es": "es_US", "hmn": "hmn",
             "sm": "sm_WS", "tl": "tl_PH"}

# Fields we want, all site-level and safe. We deliberately do NOT request the
# personal contact name/phone columns (Contact_First_Name, Contact_Last_Name,
# Contact_Phone, Ext) so PII never enters the build.
#
# The fetch intersects this list with the fields the live layer actually
# exposes, because ArcGIS returns ZERO features if you ask for a field that
# does not exist. Meal-time and season-date columns have drifted between
# seasons (e.g. "Lunch_Time" vs "Lunch_Time2", "StartDateText" vs the epoch
# "Start_date"), so we request every known variant and let normalize() pick the
# first populated one.
DESIRED_FIELDS = [
    "Site_Name", "Site_Address1", "Site_Address2", "Site_City", "Site_State",
    "Site_Zip", "Site_Phone", "Sponsoring_Organization", "Service_Model",
    "Site_Type", "Days_of_operation", "Comments", "RecordStatus",
    "Site_Location",
    "Breakfast_Time", "Lunch_Time", "Snack_Time_AM", "Snack_Time_PM",
    "Dinner_Supper_Time",
    "Breakfast_Time2", "Lunch_Time2", "Snack_Time_AM2", "Snack_Time_PM2",
    "Dinner_Supper_Time2",
    "StartDateText", "EndDateText", "Start_date", "End_date",
]

# Each meal: a display label plus the candidate field names to try, in order.
MEAL_FIELDS = [
    (("Breakfast_Time", "Breakfast_Time2"), "Breakfast"),
    (("Lunch_Time", "Lunch_Time2"), "Lunch"),
    (("Snack_Time_AM", "Snack_Time_AM2"), "Morning snack"),
    (("Snack_Time_PM", "Snack_Time_PM2"), "Afternoon snack"),
    (("Dinner_Supper_Time", "Dinner_Supper_Time2"), "Dinner"),
]

DAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday",
             "Friday", "Saturday", "Sunday"]
DAY_ABBR = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

# Compact day codes used by the live feed, e.g. "M,T,W,TH,F" or "SA".
# Order of checking matters when these are matched as whole comma-separated
# tokens: "TH" is Thursday (not Tuesday), "SA"/"SU" are the weekend.
DAY_CODES = {
    "m": 0, "mo": 0,
    "t": 1, "tu": 1,
    "w": 2, "we": 2,
    "th": 3, "r": 3,
    "f": 4,
    "sa": 5,
    "su": 6,
}

ABBR = {
    "monday": 0, "mon": 0,
    "tuesday": 1, "tues": 1, "tue": 1,
    "wednesday": 2, "weds": 2, "wed": 2,
    "thursday": 3, "thurs": 3, "thur": 3, "thu": 3,
    "friday": 4, "fri": 4,
    "saturday": 5, "sat": 5,
    "sunday": 6, "sun": 6,
}
_DAYWORD = (r"monday|tuesday|wednesday|thursday|friday|saturday|sunday"
            r"|mon|tues|tue|weds|wed|thurs|thur|thu|fri|sat|sun")

# --------------------------------------------------------------------------
# DATA FETCH
# --------------------------------------------------------------------------

UA = {"User-Agent": "anchorage-summer-meals/1.0"}


def _get_json(url):
    req = Request(url, headers=UA)
    with urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    if isinstance(data, dict) and "error" in data:
        raise RuntimeError(f"ArcGIS error: {data['error']}")
    return data


def available_fields():
    """Field names the live layer exposes (the layer URL is SERVICE_URL minus
    the trailing '/query'). Used to avoid requesting a field that doesn't exist
    -- ArcGIS returns zero features if any requested outField is unknown."""
    layer_url = re.sub(r"/query/?$", "", SERVICE_URL)
    meta = _get_json(layer_url + "?f=json")
    return {f["name"] for f in meta.get("fields", [])}


def fetch_records():
    """Return a list of attribute dicts, paging through transfer limits."""
    mock = os.environ.get("MOCK_DATA")
    if mock:
        with open(mock, encoding="utf-8") as fh:
            payload = json.load(fh)
        return [f["attributes"] for f in payload.get("features", [])]

    have = available_fields()
    fields = [f for f in DESIRED_FIELDS if f in have]
    if "Site_State" not in have or "Site_City" not in have:
        raise RuntimeError(
            "Service is missing expected fields (Site_State/Site_City). "
            f"Got: {sorted(have)[:20]}... -- check SERVICE_URL.")

    base = {
        "where": "Site_State='AK'",
        "outFields": ",".join(fields),
        "returnGeometry": "false",
        "orderByFields": "Site_Name",
        "resultRecordCount": "2000",
        "f": "json",
    }
    out, offset = [], 0
    while True:
        params = dict(base, resultOffset=str(offset))
        data = _get_json(SERVICE_URL + "?" + urlencode(params))
        feats = data.get("features", [])
        out.extend(f["attributes"] for f in feats)
        if data.get("exceededTransferLimit") and feats:
            offset += len(feats)
            continue
        break
    return out

# --------------------------------------------------------------------------
# PARSING HELPERS
# --------------------------------------------------------------------------

def parse_days(text):
    """Best-effort: return a set of weekday indices (Mon=0 .. Sun=6)."""
    if not text:
        return set()
    t = text.lower()
    if re.search(r"\b(daily|everyday|every day|7\s*days|all week)\b", t):
        return set(range(7))
    result = set()
    if re.search(r"\bweekdays?\b", t):
        result.update({0, 1, 2, 3, 4})
    if re.search(r"\bweekends?\b", t):
        result.update({5, 6})
    # explicit ranges: "Mon-Fri", "Monday through Saturday", "Tue to Thu"
    rng = rf"({_DAYWORD})s?\s*(?:-|\u2013|\u2014|to|thru|through)\s*({_DAYWORD})s?"
    for m in re.finditer(rng, t):
        a, b = ABBR[m.group(1)], ABBR[m.group(2)]
        i = a
        for _ in range(7):
            result.add(i)
            if i == b:
                break
            i = (i + 1) % 7
    # individual day tokens
    for m in re.finditer(rf"({_DAYWORD})s?", t):
        result.add(ABBR[m.group(1)])
    # common compact forms
    if re.search(r"\bm\s*[-\u2013]\s*f\b", t):
        result.update({0, 1, 2, 3, 4})
    if re.search(r"\bm\s*[-\u2013]\s*th\b", t):
        result.update({0, 1, 2, 3})
    if re.search(r"\bmwf\b", t):
        result.update({0, 2, 4})
    if re.search(r"\b(tth|t/th|t-th)\b", t):
        result.update({1, 3})
    # Compact comma/slash-separated letter codes: "M,T,W,TH,F", "SA", "M/W/F".
    # Only whole tokens are matched (split on separators) so day words handled
    # above aren't double-counted and stray letters in prose can't leak in.
    for tok in re.split(r"[,/;|]+", t):
        tok = tok.strip().strip(".").replace(" ", "")
        if tok in DAY_CODES:
            result.add(DAY_CODES[tok])
    return result


def format_days(days, raw, abbr=DAY_ABBR):
    """Human-readable day list from a parsed set, collapsing runs into ranges
    like 'Mon–Fri'. Falls back to the raw feed text if nothing parsed.
    `abbr` is the 7-long list of weekday abbreviations (localizable)."""
    if not days:
        return raw
    idxs = sorted(days)
    runs, start, prev = [], idxs[0], idxs[0]
    for i in idxs[1:]:
        if i == prev + 1:
            prev = i
            continue
        runs.append((start, prev))
        start = prev = i
    runs.append((start, prev))
    parts = []
    for a, b in runs:
        if a == b:
            parts.append(abbr[a])
        elif b == a + 1:
            parts.append(abbr[a])
            parts.append(abbr[b])
        else:
            parts.append(f"{abbr[a]}–{abbr[b]}")
    return ", ".join(parts)


def parse_text_date(s, today):
    if not s:
        return None
    s = s.strip()
    # Bare "M/D" with no year: attach the current year explicitly (avoids the
    # ambiguous-default-year deprecation in Python 3.14+).
    m = re.fullmatch(r"(\d{1,2})/(\d{1,2})", s)
    if m:
        try:
            return date(today.year, int(m.group(1)), int(m.group(2)))
        except ValueError:
            return None
    for fmt in ("%m/%d/%Y", "%m/%d/%y", "%B %d, %Y", "%b %d, %Y",
                "%B %d %Y", "%b %d %Y", "%m-%d-%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return None


def parse_epoch_date(ms):
    if ms in (None, ""):
        return None
    try:
        return datetime.fromtimestamp(int(ms) / 1000, TZ).date()
    except Exception:
        return None


def digits(s):
    return re.sub(r"\D", "", s or "")


def clean(s):
    s = (s or "").strip()
    return "" if s.lower() in {"", "n/a", "na", "none", "null"} else s

# --------------------------------------------------------------------------
# RECORD NORMALIZATION
# --------------------------------------------------------------------------

def fmt_date(d):
    """Short, locale-independent date text (e.g. 'Jun 2'). Year omitted."""
    return f"{d:%b} {d.day}" if d else ""


def model_info(raw_model):
    """Map a Service_Model value to (display_label, css_class).

    The live feed uses 'CONGREGATE' / 'NON-CONGREGATE PICK UP'; older sample
    data uses 'Eat On-Site' / 'Meals To Go'. We normalize both to friendly,
    plain-language labels and a tag class. Empty -> ("", "")."""
    m = clean(raw_model)
    if not m:
        return "", ""
    low = m.lower()
    # Check to-go first: "NON-CONGREGATE" contains the substring "congregate".
    if any(k in low for k in ("non-congregate", "non congregate", "to go",
                              "to-go", "pick up", "pick-up", "pickup", "grab")):
        return "Grab & go / pick-up", "togo"
    if any(k in low for k in ("congregate", "on-site", "on site", "eat")):
        return "Eat on-site", "onsite"
    return m, "onsite"


def first_value(raw, fields):
    """First non-empty cleaned value among candidate field names."""
    for f in fields:
        v = clean(raw.get(f))
        if v:
            return v
    return ""


def normalize(raw, today):
    city = clean(raw.get("Site_City"))
    city = CITY_FIXES.get(city.lower(), city)
    model_label, model_cls = model_info(clean(raw.get("Service_Model")))
    days_raw = clean(raw.get("Days_of_operation"))
    days = parse_days(days_raw)

    start_text = clean(raw.get("StartDateText"))
    end_text = clean(raw.get("EndDateText"))
    start_date = (parse_text_date(start_text, today)
                  or parse_epoch_date(raw.get("Start_date")))
    end_date = (parse_epoch_date(raw.get("End_date"))
                or parse_text_date(end_text, today))
    if not start_text and start_date:
        start_text = fmt_date(start_date)
    if not end_text and end_date:
        end_text = fmt_date(end_date)

    rec = {
        "name": clean(raw.get("Site_Name")) or "Summer meal site",
        "addr1": clean(raw.get("Site_Address1")),
        "addr2": clean(raw.get("Site_Address2")),
        "city": city,
        "zip": clean(raw.get("Site_Zip")),
        "phone": clean(raw.get("Site_Phone")),
        "sponsor": clean(raw.get("Sponsoring_Organization")),
        "model": model_label,
        "model_class": model_cls,
        "days_raw": days_raw,
        "days_display": format_days(days, days_raw),
        "comments": clean(raw.get("Comments")),
        # Site_Location is usually a generic enum ("Fixed"/"Mobile") that just
        # duplicates the model tag -- only surface it when it's a real note.
        "location_note": ("" if clean(raw.get("Site_Location")).lower()
                          in {"fixed", "mobile", "stationary"}
                          else clean(raw.get("Site_Location"))),
        "start_text": start_text,
        "end_text": end_text,
    }
    rec["meals"] = [(lbl, first_value(raw, fields))
                    for fields, lbl in MEAL_FIELDS if first_value(raw, fields)]
    rec["days"] = days
    rec["start_date"] = start_date
    rec["end_date"] = end_date
    return rec


def in_scope(rec):
    return rec["city"].lower() in SCOPE_CITIES


def status(rec, today):
    """Return 'ended', 'upcoming', or 'active'."""
    if rec["end_date"] and today > rec["end_date"]:
        return "ended"
    if rec["start_date"] and today < rec["start_date"]:
        return "upcoming"
    return "active"

# --------------------------------------------------------------------------
# RENDERING — shared bits
# --------------------------------------------------------------------------

esc = html.escape


def maps_url(rec):
    q = ", ".join(p for p in [rec["addr1"], rec["city"], "AK", rec["zip"]] if p)
    return "https://www.google.com/maps/search/?api=1&query=" + quote(q)


def nbsp_phone(s):
    """Keep a phone number from wrapping mid-number: non-breaking spaces and
    non-breaking hyphens for the *visible* text only (the tel: href is plain)."""
    return (s or "").replace("-", "‑").replace(" ", " ")


def tel_link(phone):
    d = digits(phone)
    if len(d) == 10:
        return "+1" + d
    if len(d) == 11 and d.startswith("1"):
        return "+" + d
    return d


def address_line(rec):
    parts = [rec["addr1"]]
    if rec["addr2"]:
        parts.append(rec["addr2"])
    tail = " ".join(p for p in [rec["city"], "AK", rec["zip"]] if p)
    if tail:
        parts.append(tail)
    return ", ".join(p for p in parts if p)

# --------------------------------------------------------------------------
# RENDERING — HTML
# --------------------------------------------------------------------------

CSS = """
:root{
  --bg:#fbf6ee; --surface:#ffffff; --ink:#1b1a17; --muted:#5b5750;
  --line:#e7ddcd; --primary:#0b6b7a; --primary-ink:#06464f;
  --today:#15803d; --today-bg:#e7f6ec; --today-line:#bfe6cc;
  --onsite-bg:#d8f0f4; --onsite-ink:#0c5563;
  --togo-bg:#fcebd2; --togo-ink:#8a4b00;
  --focus:#0b6b7a;
}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{
  margin:0; background:var(--bg); color:var(--ink);
  font-family:ui-rounded,"SF Pro Rounded","Segoe UI",system-ui,-apple-system,Roboto,Helvetica,Arial,sans-serif;
  font-size:18px; line-height:1.5;
}
.wrap{max-width:680px; margin:0 auto; padding:0 18px 64px}
a{color:var(--primary-ink)}
a:focus-visible,button:focus-visible{outline:3px solid var(--focus); outline-offset:2px; border-radius:6px}
.skip{position:absolute; left:-9999px; top:0; background:#fff; padding:12px 16px; border:2px solid var(--primary)}
.skip:focus{left:8px; top:8px; z-index:10}

header{padding:28px 0 8px}
h1{
  font-family:Georgia,"Iowan Old Style","Times New Roman",serif;
  font-size:2rem; line-height:1.12; letter-spacing:-.01em; margin:0 0 10px;
  color:var(--primary-ink);
}
.sub{margin:0 0 14px; font-size:1.08rem}
.updated{
  margin:0; font-size:.92rem; color:var(--muted);
  border-top:1px solid var(--line); padding-top:12px;
}
.updated strong{color:var(--today)}

h2{
  font-family:Georgia,"Iowan Old Style",serif; font-size:1.4rem;
  margin:36px 0 4px; color:var(--ink);
}
.section-note{margin:0 0 14px; color:var(--muted); font-size:.95rem}
h3.day{
  margin:26px 0 10px; font-size:1.12rem; letter-spacing:.02em;
  text-transform:uppercase; color:var(--primary-ink);
  border-bottom:2px solid var(--line); padding-bottom:6px;
}

.site{
  background:var(--surface); border:1px solid var(--line);
  border-left:5px solid var(--primary); border-radius:12px;
  padding:16px 16px 14px; margin:0 0 14px;
  box-shadow:0 1px 0 rgba(27,26,23,.04);
  animation:rise .4s ease both;
}
#today .site{border-left-color:var(--today)}
.site h3.name,.site h4.name{margin:0 0 8px; font-size:1.16rem; line-height:1.25}
.tags{margin:0 0 10px; display:flex; flex-wrap:wrap; gap:6px}
.tag{font-size:.8rem; font-weight:600; padding:3px 10px; border-radius:999px}
.tag.onsite{background:var(--onsite-bg); color:var(--onsite-ink)}
.tag.togo{background:var(--togo-bg); color:var(--togo-ink)}
.row{margin:6px 0; font-size:1rem}
.row .lbl{font-weight:600}
address{font-style:normal; margin:6px 0}
.meals{margin:8px 0 6px; padding-left:1.1em}
.meals li{margin:2px 0}
.actions{display:flex; flex-wrap:wrap; gap:10px; margin-top:12px}
.btn{
  display:inline-block; min-height:44px; line-height:1.2;
  padding:11px 16px; border-radius:10px; text-decoration:none; font-weight:600;
}
.btn.call{background:var(--today); color:#fff}
.btn.map{background:#fff; color:var(--primary-ink); border:2px solid var(--primary)}
.comment{margin:10px 0 0; color:var(--muted); font-size:.95rem}

.empty{background:#fff;border:1px dashed var(--line);border-radius:12px;padding:18px;color:var(--muted)}
.callout{background:var(--today-bg);border:1px solid var(--today-line);border-radius:12px;padding:14px 16px;margin:16px 0}

footer{margin-top:40px; border-top:1px solid var(--line); padding-top:20px;
  font-size:.92rem; color:var(--muted)}
footer a{color:var(--primary-ink)}
footer p{margin:8px 0}

.langbar{display:flex; flex-wrap:wrap; gap:6px; align-items:center;
  padding:14px 0 2px; font-size:.9rem}
.langbar .lbl{color:var(--muted); margin-right:2px}
.langbar a{display:inline-block; min-height:38px; line-height:1.2;
  padding:8px 12px; border-radius:999px; border:1px solid var(--line);
  background:#fff; text-decoration:none}
.langbar a[aria-current="page"]{background:var(--primary); color:#fff;
  border-color:var(--primary)}
.review{background:var(--togo-bg); color:var(--togo-ink);
  border:1px solid #e6c590; border-radius:10px; padding:10px 14px;
  margin:14px 0 0; font-size:.92rem}
.review a{color:var(--togo-ink); font-weight:600}
#accessibility h2{font-size:1.2rem}

@keyframes rise{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:none}}
@media (prefers-reduced-motion:reduce){.site{animation:none}}
@media (min-width:560px){h1{font-size:2.4rem}}
"""


def render_site(rec, level, S):
    """Render one site card. `S` is the active locale's string table; only the
    chrome (labels/buttons/day + meal names) is localized -- the site's own
    name, address, times and comments are shown verbatim as USDA provides."""
    tag_cls = rec["model_class"] or "onsite"
    model_label = S["models"].get(rec["model"], rec["model"])
    days_disp = format_days(rec["days"], rec["days_raw"], S["days_abbr"])
    parts = ['<article class="site">']
    parts.append(f'<h{level} class="name">{esc(rec["name"])}</h{level}>')
    if model_label:
        parts.append(f'<p class="tags"><span class="tag {tag_cls}">{esc(model_label)}</span></p>')
    addr = address_line(rec)
    if addr:
        parts.append(f'<address>{esc(addr)}</address>')
    if rec["location_note"]:
        parts.append(f'<p class="row">{esc(rec["location_note"])}</p>')
    if days_disp:
        parts.append(f'<p class="row"><span class="lbl">{esc(S["open_label"])}</span> {esc(days_disp)}</p>')
    if rec["meals"]:
        items = "".join(f'<li>{esc(S["meals"].get(lbl, lbl))}: {esc(val)}</li>'
                        for lbl, val in rec["meals"])
        parts.append(f'<ul class="meals">{items}</ul>')
    if rec["start_text"] or rec["end_text"]:
        span = " \u2013 ".join(x for x in [rec["start_text"], rec["end_text"]] if x)
        parts.append(f'<p class="row"><span class="lbl">{esc(S["dates_label"])}</span> {esc(span)}</p>')
    actions = []
    if digits(rec["phone"]):
        actions.append(f'<a class="btn call" href="tel:{esc(tel_link(rec["phone"]))}">{esc(S["call"])} {esc(nbsp_phone(rec["phone"]))}</a>')
    if addr:
        actions.append(f'<a class="btn map" href="{esc(maps_url(rec))}">{esc(S["directions"])}</a>')
    if actions:
        parts.append(f'<p class="actions">{"".join(actions)}</p>')
    if rec["comments"]:
        parts.append(f'<p class="comment">{esc(rec["comments"])}</p>')
    parts.append("</article>")
    return "".join(parts)


def page_path(code):
    """Site-root-relative path for a locale page ('/' for English)."""
    return "/" if code == "en" else f"/{code}/"


def render_langbar(locales, active_code, S):
    parts = [f'<nav class="langbar" aria-label="{esc(S["lang_label"])}">']
    parts.append(f'<span class="lbl">{esc(S["lang_label"])}:</span>')
    for loc in locales:
        cur = ' aria-current="page"' if loc["code"] == active_code else ""
        parts.append(
            f'<a href="{page_path(loc["code"])}" lang="{loc["code"]}" '
            f'hreflang="{loc["code"]}"{cur}>{esc(loc["name"])}</a>')
    parts.append("</nav>")
    return "".join(parts)


def render_head_meta(S, active_code, locales):
    """Icons, canonical/hreflang alternates, and Open Graph / Twitter cards."""
    here = SITE_URL + page_path(active_code)
    og_img = SITE_URL + "/og-image.png"
    m = []
    m.append('<link rel="icon" href="/favicon.svg" type="image/svg+xml">')
    m.append('<link rel="icon" href="/favicon.ico" sizes="32x32">')
    m.append('<link rel="apple-touch-icon" href="/apple-touch-icon.png">')
    m.append('<link rel="manifest" href="/site.webmanifest">')
    m.append(f'<link rel="canonical" href="{esc(here)}">')
    for loc in locales:
        alt = SITE_URL + page_path(loc["code"])
        m.append(f'<link rel="alternate" hreflang="{loc["code"]}" href="{esc(alt)}">')
    m.append(f'<link rel="alternate" hreflang="x-default" href="{esc(SITE_URL)}/">')
    m.append('<meta property="og:type" content="website">')
    m.append('<meta property="og:site_name" content="Anchorage Summer Meals">')
    m.append(f'<meta property="og:title" content="{esc(S["title"])}">')
    m.append(f'<meta property="og:description" content="{esc(S["sub"])}">')
    m.append(f'<meta property="og:url" content="{esc(here)}">')
    m.append(f'<meta property="og:image" content="{esc(og_img)}">')
    m.append('<meta property="og:image:width" content="1200">')
    m.append('<meta property="og:image:height" content="630">')
    m.append(f'<meta property="og:image:alt" content="{esc(S["title"])}">')
    m.append(f'<meta property="og:locale" content="{OG_LOCALE.get(active_code, "en_US")}">')
    m.append('<meta name="twitter:card" content="summary_large_image">')
    m.append(f'<meta name="twitter:title" content="{esc(S["title"])}">')
    m.append(f'<meta name="twitter:description" content="{esc(S["sub"])}">')
    m.append(f'<meta name="twitter:image" content="{esc(og_img)}">')
    return "".join(m)


def render_html(S, locales, active_code, today_idx, today_sites,
                by_day, varies, upcoming, stamp):
    weekday = S["days"][today_idx]
    out = []
    out.append(f'<!DOCTYPE html><html lang="{S["html_lang"]}"><head>')
    out.append('<meta charset="utf-8">')
    out.append('<meta name="viewport" content="width=device-width, initial-scale=1">')
    out.append('<meta name="theme-color" content="#0b6b7a">')
    out.append(f'<meta name="description" content="{esc(S["meta_desc"])}">')
    out.append(f'<title>{esc(S["title"])}</title>')
    out.append(render_head_meta(S, active_code, locales))
    out.append(f'<style>{CSS}</style>')
    out.append('</head><body><div class="wrap">')
    out.append(f'<a class="skip" href="#today">{esc(S["skip"])}</a>')

    out.append('<header>')
    out.append(render_langbar(locales, active_code, S))
    if S["review_note"]:
        out.append(f'<p class="review" role="note">{esc(S["review_note"])} '
                   f'<a href="/" lang="en" hreflang="en">English</a></p>')
    out.append(f'<h1>{esc(S["h1"])}</h1>')
    out.append(f'<p class="sub">{esc(S["sub"])}</p>')
    open_n = len(today_sites)
    count = (S["open_today_one"] if open_n == 1
             else S["open_today_many"]).format(n=open_n)
    out.append(f'<p class="updated">{esc(S["updated"])} {esc(stamp)} \u00b7 '
               f'<strong>{esc(count)}</strong></p>')
    out.append('</header><main>')

    # TODAY
    out.append('<section id="today" aria-labelledby="today-h">')
    out.append(f'<h2 id="today-h">{esc(S["today_h"])} \u2014 {esc(weekday)}</h2>')
    if today_sites:
        note = (S["today_note_one"] if len(today_sites) == 1
                else S["today_note_many"]).format(n=len(today_sites))
        out.append(f'<p class="section-note">{esc(note)}</p>')
        for r in today_sites:
            out.append(render_site(r, 3, S))
    else:
        out.append(f'<div class="empty">{esc(S["today_empty"])}</div>')
    out.append('</section>')

    # FULL WEEK
    out.append('<section id="week" aria-labelledby="week-h">')
    out.append(f'<h2 id="week-h">{esc(S["week_h"])}</h2>')
    out.append(f'<p class="section-note">{esc(S["week_note"])}</p>')
    any_week = False
    for i in range(7):
        sites = by_day[i]
        if not sites:
            continue
        any_week = True
        out.append(f'<h3 class="day">{esc(S["days"][i])}</h3>')
        for r in sites:
            out.append(render_site(r, 4, S))
    if not any_week:
        out.append(f'<div class="empty">{esc(S["week_empty"])}</div>')
    out.append('</section>')

    # DAYS VARY
    if varies:
        out.append('<section id="varies" aria-labelledby="varies-h">')
        out.append(f'<h2 id="varies-h">{esc(S["varies_h"])}</h2>')
        out.append(f'<p class="section-note">{esc(S["varies_note"])}</p>')
        for r in varies:
            out.append(render_site(r, 3, S))
        out.append('</section>')

    # UPCOMING
    if upcoming:
        out.append('<section id="soon" aria-labelledby="soon-h">')
        out.append(f'<h2 id="soon-h">{esc(S["soon_h"])}</h2>')
        items = "".join(
            f'<li>{esc(r["name"])}'
            + (f' \u2014 {esc(S["soon_starts"])} {esc(r["start_text"])}'
               if r["start_text"] else "")
            + '</li>' for r in upcoming)
        out.append(f'<ul>{items}</ul>')
        out.append('</section>')

    # ACCESSIBILITY STATEMENT
    out.append('<section id="accessibility" aria-labelledby="a11y-h">')
    out.append(f'<h2 id="a11y-h">{esc(S["a11y_h"])}</h2>')
    out.append(f'<p class="section-note">{esc(S["a11y_text"])} '
               f'<a href="{ISSUES_URL}">'
               'github.com/codeforanchorage/summer-meals-anchorage</a></p>')
    out.append('</section>')

    out.append('</main>')

    # FOOTER
    out.append('<footer>')
    out.append(f'<p><strong>{esc(S["foot_doublecheck_strong"])}</strong> '
               f'{esc(S["foot_doublecheck"])}</p>')
    finder = f'<a href="{OFFICIAL_FINDER}">USDA Summer Meals Site Finder</a>'
    agency = f'<a href="{STATE_AGENCY}">Alaska Child Nutrition Programs</a>'
    out.append('<p>' + S["foot_official"].format(finder=finder, agency=agency) + '</p>')
    phone = (f'<a href="tel:+1{digits(HUNGER_HOTLINE)}">'
             f'{esc(nbsp_phone(HUNGER_HOTLINE))}</a>')
    out.append('<p>' + S["foot_help"].format(phone=phone) + '</p>')
    out.append(f'<p>{esc(S["foot_source"])}</p>')
    out.append('</footer>')

    out.append('</div></body></html>')
    return "".join(out)

# --------------------------------------------------------------------------
# RENDERING — plain text
# --------------------------------------------------------------------------

def render_text(today, today_idx, today_sites, by_day, varies, upcoming, stamp):
    L = []
    L.append("FREE SUMMER MEALS \u2014 ANCHORAGE")
    L.append(f"Updated {stamp}")
    L.append("Free breakfast, lunch & snacks for anyone 18 and under. No sign-up, no cost.")
    L.append("")

    def block(r, indent="  "):
        out = [r["name"]]
        addr = address_line(r)
        if addr:
            out.append(indent + addr)
        meta = []
        if r["model"]:
            meta.append(r["model"])
        if r["days_display"]:
            meta.append("Open: " + r["days_display"])
        if meta:
            out.append(indent + " | ".join(meta))
        for lbl, val in r["meals"]:
            out.append(indent + f"{lbl}: {val}")
        if r["phone"]:
            out.append(indent + "Phone: " + r["phone"])
        if r["comments"]:
            out.append(indent + r["comments"])
        return "\n".join(out)

    L.append(f"=== OPEN TODAY ({DAY_NAMES[today_idx].upper()}) ===")
    L.append("")
    if today_sites:
        for r in today_sites:
            L.append(block(r))
            L.append("")
    else:
        L.append("No sites listed as open today. See the full week below.")
        L.append("")

    L.append("=== FULL WEEK ===")
    for i, dname in enumerate(DAY_NAMES):
        if not by_day[i]:
            continue
        L.append("")
        L.append(f"-- {dname.upper()} --")
        for r in by_day[i]:
            L.append(block(r))
    if varies:
        L.append("")
        L.append("-- OTHER SITES (CALL FOR DAYS) --")
        for r in varies:
            L.append(block(r))
    if upcoming:
        L.append("")
        L.append("-- OPENING SOON --")
        for r in upcoming:
            s = r["name"] + (f" (starts {r['start_text']})" if r["start_text"] else "")
            L.append("  " + s)
    L.append("")
    L.append(f"Official map: {OFFICIAL_FINDER}")
    L.append(f"Hunger Hotline: {HUNGER_HOTLINE}")
    L.append("Community-built page; not an official USDA website.")
    return "\n".join(L) + "\n"

# --------------------------------------------------------------------------
# MAIN
# --------------------------------------------------------------------------

def sort_key(r):
    return r["name"].lower()


def main():
    now = datetime.now(TZ) if TZ else datetime.now()
    today = now.date()
    today_idx = today.weekday()
    stamp = now.strftime("%A, %B %-d, %Y at %-I:%M %p AKT") if os.name != "nt" \
        else now.strftime("%A, %B %d, %Y")

    raw = fetch_records()
    print(f"Fetched {len(raw)} AK records")

    recs = [normalize(r, today) for r in raw]
    recs = [r for r in recs if in_scope(r)]
    print(f"{len(recs)} in Anchorage scope")

    active, varies, upcoming = [], [], []
    for r in recs:
        st = status(r, today)
        if st == "ended":
            continue
        if st == "upcoming":
            upcoming.append(r)
            continue
        if r["days"]:
            active.append(r)
        else:
            varies.append(r)

    today_sites = sorted([r for r in active if today_idx in r["days"]], key=sort_key)
    by_day = [sorted([r for r in active if i in r["days"]], key=sort_key)
              for i in range(7)]
    varies.sort(key=sort_key)
    upcoming.sort(key=sort_key)

    print(f"Open today: {len(today_sites)} | active: {len(active)} | "
          f"varies: {len(varies)} | upcoming: {len(upcoming)}")

    os.makedirs(OUT_DIR, exist_ok=True)

    # One HTML page per locale: English at the root (docs/index.html), each
    # other language under docs/<code>/index.html. Only the page chrome is
    # localized; the listings themselves stay as USDA provides.
    locales = i18n.LOCALES
    for loc in locales:
        code = loc["code"]
        S = i18n.STRINGS[code]
        html_doc = render_html(S, locales, code, today_idx, today_sites,
                               by_day, varies, upcoming, stamp)
        if code == "en":
            dest = os.path.join(OUT_DIR, "index.html")
        else:
            os.makedirs(os.path.join(OUT_DIR, code), exist_ok=True)
            dest = os.path.join(OUT_DIR, code, "index.html")
        with open(dest, "w", encoding="utf-8") as fh:
            fh.write(html_doc)

    # Plain-text + JSON are emitted once at the root (English) -- the txt is the
    # low-bandwidth / SMS body.
    txt_doc = render_text(today, today_idx, today_sites, by_day, varies, upcoming, stamp)
    with open(os.path.join(OUT_DIR, "sites.txt"), "w", encoding="utf-8") as fh:
        fh.write(txt_doc)
    with open(os.path.join(OUT_DIR, "data.json"), "w", encoding="utf-8") as fh:
        json.dump([{k: (sorted(v) if k == "days" else v)
                    for k, v in r.items() if k not in ("start_date", "end_date")}
                   for r in active + varies], fh, indent=2, default=str)
    # Ensure GitHub Pages serves files as-is (no Jekyll processing)
    open(os.path.join(OUT_DIR, ".nojekyll"), "w").close()
    print(f"Wrote {OUT_DIR}/index.html (+ {len(locales)-1} locales), "
          "sites.txt, data.json")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # keep the last good page if a build fails
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
