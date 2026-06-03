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

try:
    from zoneinfo import ZoneInfo
    TZ = ZoneInfo("America/Anchorage")
except Exception:  # pragma: no cover
    TZ = None

# --------------------------------------------------------------------------
# CONFIG
# --------------------------------------------------------------------------

# IMPORTANT: confirm the current-season service name before going live.
# 2023 and 2024 are verified; the 2026 season is almost certainly the name
# below. To check: browse the org's directory and look for the newest
#   Summer_Meal_Site_Finder_<year>_WFL1
# at https://services1.arcgis.com/RLQu0rK7h4kbsBq5/arcgis/rest/services
SERVICE_URL = os.environ.get("SERVICE_URL") or (
    "https://services1.arcgis.com/RLQu0rK7h4kbsBq5/arcgis/rest/services/"
    "Summer_Meal_Site_Finder_2026_WFL1/FeatureServer/0/query"
)

OUT_DIR = os.environ.get("OUT_DIR", "docs")

# Scope = the Municipality of Anchorage. The user asked for "Anchorage only";
# because the MOA includes these communities, they are included by default.
# To restrict to the city proper, set SCOPE_CITIES = {"anchorage"}.
SCOPE_CITIES = {
    "anchorage", "eagle river", "chugiak", "girdwood", "indian",
    "bird creek", "peters creek", "jber",
    "joint base elmendorf-richardson", "elmendorf", "fort richardson",
}

OFFICIAL_FINDER = "https://www.fns.usda.gov/sfsp/sitefinder"
STATE_AGENCY = "https://education.alaska.gov/cnp"  # AK Child Nutrition Programs
HUNGER_HOTLINE = "1-866-348-6479"

OUTFIELDS = ",".join([
    "Site_Name", "Site_Address1", "Site_Address2", "Site_City", "Site_State",
    "Site_Zip", "Site_Phone", "Sponsoring_Organization", "Service_Model",
    "Days_of_operation", "Breakfast_Time", "Lunch_Time", "Snack_Time_AM",
    "Snack_Time_PM", "Dinner_Supper_Time", "StartDateText", "EndDateText",
    "End_date", "Comments", "RecordStatus", "Site_Location",
])

MEAL_FIELDS = [
    ("Breakfast_Time", "Breakfast"),
    ("Lunch_Time", "Lunch"),
    ("Snack_Time_AM", "Morning snack"),
    ("Snack_Time_PM", "Afternoon snack"),
    ("Dinner_Supper_Time", "Dinner"),
]

DAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday",
             "Friday", "Saturday", "Sunday"]

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

def fetch_records():
    """Return a list of attribute dicts, paging through transfer limits."""
    mock = os.environ.get("MOCK_DATA")
    if mock:
        with open(mock, encoding="utf-8") as fh:
            payload = json.load(fh)
        return [f["attributes"] for f in payload.get("features", [])]

    base = {
        "where": "Site_State='AK'",
        "outFields": OUTFIELDS,
        "returnGeometry": "false",
        "orderByFields": "Site_Name",
        "resultRecordCount": "2000",
        "f": "json",
    }
    out, offset = [], 0
    while True:
        params = dict(base, resultOffset=str(offset))
        url = SERVICE_URL + "?" + urlencode(params)
        req = Request(url, headers={"User-Agent": "anchorage-summer-meals/1.0"})
        with urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        if "error" in data:
            raise RuntimeError(f"ArcGIS error: {data['error']}")
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
    return result


def parse_text_date(s, today):
    if not s:
        return None
    s = s.strip()
    for fmt in ("%m/%d/%Y", "%m/%d/%y", "%B %d, %Y", "%b %d, %Y",
                "%B %d %Y", "%b %d %Y", "%m-%d-%Y", "%Y-%m-%d", "%m/%d"):
        try:
            d = datetime.strptime(s, fmt)
            if fmt == "%m/%d":
                d = d.replace(year=today.year)
            return d.date()
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

def normalize(raw, today):
    city = clean(raw.get("Site_City"))
    rec = {
        "name": clean(raw.get("Site_Name")) or "Summer meal site",
        "addr1": clean(raw.get("Site_Address1")),
        "addr2": clean(raw.get("Site_Address2")),
        "city": city,
        "zip": clean(raw.get("Site_Zip")),
        "phone": clean(raw.get("Site_Phone")),
        "sponsor": clean(raw.get("Sponsoring_Organization")),
        "model": clean(raw.get("Service_Model")),
        "days_raw": clean(raw.get("Days_of_operation")),
        "comments": clean(raw.get("Comments")),
        "location_note": clean(raw.get("Site_Location")),
        "start_text": clean(raw.get("StartDateText")),
        "end_text": clean(raw.get("EndDateText")),
    }
    rec["meals"] = [(label, clean(raw.get(f)))
                    for f, label in MEAL_FIELDS if clean(raw.get(f))]
    rec["days"] = parse_days(rec["days_raw"])
    rec["start_date"] = parse_text_date(rec["start_text"], today)
    rec["end_date"] = (parse_epoch_date(raw.get("End_date"))
                       or parse_text_date(rec["end_text"], today))
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

@keyframes rise{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:none}}
@media (prefers-reduced-motion:reduce){.site{animation:none}}
@media (min-width:560px){h1{font-size:2.4rem}}
"""


def render_site(rec, level):
    tag_cls = "togo" if "to go" in rec["model"].lower() or "to-go" in rec["model"].lower() else "onsite"
    parts = [f'<article class="site">']
    parts.append(f'<h{level} class="name">{esc(rec["name"])}</h{level}>')
    if rec["model"]:
        parts.append(f'<p class="tags"><span class="tag {tag_cls}">{esc(rec["model"])}</span></p>')
    addr = address_line(rec)
    if addr:
        parts.append(f'<address>{esc(addr)}</address>')
    if rec["location_note"]:
        parts.append(f'<p class="row">{esc(rec["location_note"])}</p>')
    if rec["days_raw"]:
        parts.append(f'<p class="row"><span class="lbl">Open:</span> {esc(rec["days_raw"])}</p>')
    if rec["meals"]:
        items = "".join(f'<li>{esc(lbl)}: {esc(val)}</li>' for lbl, val in rec["meals"])
        parts.append(f'<ul class="meals">{items}</ul>')
    if rec["start_text"] or rec["end_text"]:
        span = " \u2013 ".join(x for x in [rec["start_text"], rec["end_text"]] if x)
        parts.append(f'<p class="row"><span class="lbl">Dates:</span> {esc(span)}</p>')
    actions = []
    if digits(rec["phone"]):
        actions.append(f'<a class="btn call" href="tel:{esc(tel_link(rec["phone"]))}">Call {esc(rec["phone"])}</a>')
    if addr:
        actions.append(f'<a class="btn map" href="{esc(maps_url(rec))}">Directions</a>')
    if actions:
        parts.append(f'<p class="actions">{"".join(actions)}</p>')
    if rec["comments"]:
        parts.append(f'<p class="comment">{esc(rec["comments"])}</p>')
    parts.append("</article>")
    return "".join(parts)


def render_html(today, today_idx, today_sites, by_day, varies, upcoming, stamp):
    weekday = DAY_NAMES[today_idx]
    out = []
    out.append('<!doctype html><html lang="en"><head>')
    out.append('<meta charset="utf-8">')
    out.append('<meta name="viewport" content="width=device-width, initial-scale=1">')
    out.append('<meta name="theme-color" content="#0b6b7a">')
    out.append('<meta name="description" content="Free summer meals for kids 18 and under in Anchorage, Alaska. See sites open today and all week.">')
    out.append('<title>Free Summer Meals in Anchorage</title>')
    out.append(f'<style>{CSS}</style>')
    out.append('</head><body><div class="wrap">')
    out.append('<a class="skip" href="#today">Skip to today\u2019s meals</a>')

    out.append('<header>')
    out.append('<h1>Free Summer Meals in Anchorage</h1>')
    out.append('<p class="sub">Free breakfast, lunch, and snacks for anyone 18 and under. '
               'No sign-up, no ID, and no cost.</p>')
    open_n = len(today_sites)
    out.append(f'<p class="updated">Updated {esc(stamp)} \u00b7 '
               f'<strong>{open_n} site{"s" if open_n != 1 else ""} open today</strong></p>')
    out.append('</header><main>')

    # TODAY
    out.append('<section id="today" aria-labelledby="today-h">')
    out.append(f'<h2 id="today-h">Open today \u2014 {weekday}</h2>')
    if today_sites:
        out.append(f'<p class="section-note">{len(today_sites)} location'
                   f'{"s" if len(today_sites)!=1 else ""} serving meals today.</p>')
        for r in today_sites:
            out.append(render_site(r, 3))
    else:
        out.append('<div class="empty">No sites are listed as open today. '
                   'Check the full week below, or some sites may not have reported '
                   'their hours yet.</div>')
    out.append('</section>')

    # FULL WEEK
    out.append('<section id="week" aria-labelledby="week-h">')
    out.append('<h2 id="week-h">Full week</h2>')
    out.append('<p class="section-note">All Anchorage sites, grouped by the days they serve.</p>')
    any_week = False
    for i, dname in enumerate(DAY_NAMES):
        sites = by_day[i]
        if not sites:
            continue
        any_week = True
        out.append(f'<h3 class="day">{dname}</h3>')
        for r in sites:
            out.append(render_site(r, 4))
    if not any_week:
        out.append('<div class="empty">No weekly schedules are available right now.</div>')
    out.append('</section>')

    # DAYS VARY
    if varies:
        out.append('<section id="varies" aria-labelledby="varies-h">')
        out.append('<h2 id="varies-h">Other sites (call for days)</h2>')
        out.append('<p class="section-note">These sites are active but didn\u2019t list '
                   'clear weekly days \u2014 check the note or call to confirm.</p>')
        for r in varies:
            out.append(render_site(r, 3))
        out.append('</section>')

    # UPCOMING
    if upcoming:
        out.append('<section id="soon" aria-labelledby="soon-h">')
        out.append('<h2 id="soon-h">Opening soon</h2>')
        items = "".join(
            f'<li>{esc(r["name"])}'
            + (f' \u2014 starts {esc(r["start_text"])}' if r["start_text"] else "")
            + '</li>' for r in upcoming)
        out.append(f'<ul>{items}</ul>')
        out.append('</section>')

    out.append('</main>')

    # FOOTER
    out.append('<footer>')
    out.append('<p><strong>Always good to double-check.</strong> Sites are added and '
               'updated through the summer, and hours can change. This page is rebuilt '
               'automatically from the USDA data feed.</p>')
    out.append(f'<p>Official map: <a href="{OFFICIAL_FINDER}">USDA Summer Meals Site Finder</a>. '
               f'Report a wrong listing to the <a href="{STATE_AGENCY}">Alaska Child Nutrition Programs</a>.</p>')
    out.append(f'<p>Need more help? Call the USDA National Hunger Hotline at '
               f'<a href="tel:+1{digits(HUNGER_HOTLINE)}">{HUNGER_HOTLINE}</a> '
               '(Mon\u2013Fri, 7 a.m.\u20137 p.m. Alaska time).</p>')
    out.append('<p>Data source: USDA Food and Nutrition Service. This is a community-built '
               'page and is not an official USDA website.</p>')
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
        if r["days_raw"]:
            meta.append("Open: " + r["days_raw"])
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
    html_doc = render_html(today, today_idx, today_sites, by_day, varies, upcoming, stamp)
    txt_doc = render_text(today, today_idx, today_sites, by_day, varies, upcoming, stamp)

    with open(os.path.join(OUT_DIR, "index.html"), "w", encoding="utf-8") as fh:
        fh.write(html_doc)
    with open(os.path.join(OUT_DIR, "sites.txt"), "w", encoding="utf-8") as fh:
        fh.write(txt_doc)
    with open(os.path.join(OUT_DIR, "data.json"), "w", encoding="utf-8") as fh:
        json.dump([{k: (sorted(v) if k == "days" else v)
                    for k, v in r.items() if k not in ("start_date", "end_date")}
                   for r in active + varies], fh, indent=2, default=str)
    # Ensure GitHub Pages serves files as-is (no Jekyll processing)
    open(os.path.join(OUT_DIR, ".nojekyll"), "w").close()
    print(f"Wrote {OUT_DIR}/index.html, sites.txt, data.json")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # keep the last good page if a build fails
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
