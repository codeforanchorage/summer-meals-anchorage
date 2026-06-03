# Free Summer Meals in Anchorage

A tiny, fast, accessible web page that lists USDA Summer Food Service Program
sites in the Municipality of Anchorage — what's **open today** at the top, and
the **full week** below. Built to be shared by text message with a large
audience.

**Live:** https://summermeals.codeforanchorage.org

![Screenshot of the page on a phone: a language switcher, the title “Free Summer
Meals in Anchorage”, an “Open today — Wednesday” heading, and a site card for
Bartlett High School with address, hours, and Call / Directions buttons.](docs/screenshot.png)

It rebuilds itself every morning from the public USDA-FNS Summer Meals Site
Finder data feed. No servers, no database — just a static page on GitHub Pages.

## How it works

```
GitHub Action (daily)  ->  generate.py queries the USDA feature service
                       ->  filters to Anchorage + currently-open sites
                       ->  writes docs/index.html (+ one page per language),
                           docs/sites.txt, docs/data.json
                       ->  deploys docs/ to GitHub Pages
```

Because the page is pre-rendered static HTML on a CDN, a burst of traffic from
an SMS blast to tens of thousands of people is a non-issue, and it loads fast on
a weak mobile connection even if the USDA service is slow that minute.

`generate.py` uses the **Python standard library only** — the Action needs no
`pip install` step. (The accessibility/asset tooling below is dev-only.)

## Setup

1. Create the repo and add these files.
2. In **Settings → Pages**, set **Source = GitHub Actions**.
3. Set a repo **variable** `SERVICE_URL` (Settings → Secrets and variables →
   Actions → Variables) to the current season's query endpoint — see below.
4. Go to **Actions**, enable workflows, and run **Build summer meals page**
   once. After it finishes, the page is live at the URL in the `deploy` step.
   It then rebuilds automatically every morning (≈5 AM Alaska time).

### Confirm the data endpoint first

The feed is **versioned by season and the schema drifts between years**, so
confirm the endpoint before each season. Browse the org's service directory:

```
https://services1.arcgis.com/RLQu0rK7h4kbsBq5/arcgis/rest/services
```

As of June 2026 the current-season service is:

```
https://services1.arcgis.com/RLQu0rK7h4kbsBq5/arcgis/rest/services/Summer_Meals_Site_Finder_2026_(Testing)/FeatureServer/0/query
```

This is the only service carrying real, `Season=2026` Alaska data. ⚠️ **Its
name still says “(Testing)” on USDA's side** — before the SMS launch, confirm
with USDA-FNS / Alaska Child Nutrition Programs whether a renamed production
endpoint will appear. If it does, just update the `SERVICE_URL` variable; no
code change is needed (the parser is schema-tolerant — see `CLAUDE.md`).

## Customizing

Everything tunable lives at the top of `generate.py`:

- **`SCOPE_CITIES`** — defaults to the whole Municipality of Anchorage (includes
  Eagle River, Chugiak, Girdwood, etc.). For the city proper only, set this to
  `{"anchorage"}`.
- **`SERVICE_URL` / `SITE_URL`** — the season's query endpoint and the public
  canonical origin (the custom domain). Both also read from env / repo vars.
- **`STATE_AGENCY` / `OFFICIAL_FINDER` / `HUNGER_HOTLINE`** — footer links.

## Languages

The **page chrome** (headings, labels, footer — not the site data) is available
in English, **Spanish, Hmong, Samoan, and Tagalog**, generated as
`docs/<lang>/index.html` with a language switcher at the top of each page.

> ⚠️ The non-English translations are **machine-drafted and need human review.**
> Each non-English page shows a visible “awaiting human review” banner. Route
> them through the Municipality of Anchorage's language-access resources (or a
> qualified community translator) before launch, then clear the banner by
> setting `needs_review`/`review_note` in `i18n.py`. Add a language by appending
> to `LOCALES` and `STRINGS` there.

## Accessibility

The page targets **WCAG 2.1 AA**. The built pages report **zero** violations
from axe-core and pa11y, **100** on Lighthouse's accessibility category, and
pass `html-validate`. There's a short accessibility statement on every page.
Please re-audit after template changes (see below).

## Test it offline

No network needed — render from the included sample data (which exercises both
the legacy and the 2026 feed schemas):

```bash
MOCK_DATA=mock.json python generate.py
```

Run the unit tests (standard-library `unittest`, no pytest):

```bash
python -m unittest
```

> On Windows the interpreter is `python` (not `python3`).

## Dev tooling (optional, not part of the runtime)

```bash
npm install                 # html-validate, pa11y, puppeteer, png-to-ico
npm run serve               # serve docs/ at http://localhost:8000
npm run validate            # html-validate on all locale pages
npm run a11y                # pa11y WCAG2AA (axe + HTML_CodeSniffer)
npm run make-assets         # regenerate icons + OG image from docs/favicon.svg
```

## Custom domain for the SMS link

The page is served at **`summermeals.codeforanchorage.org`** via the `docs/CNAME`
file. A branded link is friendlier in a text and far less likely to be caught by
carrier spam filters than a generic shortener — and you can repoint it later
without re-texting anyone. Set the DNS record per GitHub's custom-domain docs.

## Notes / caveats

- **PII:** the source data carries individual contact names and personal phone
  numbers. This page shows only the **site** name, address, and site phone — the
  fetch doesn't even request the personal columns.
- **Accuracy:** data is submitted by the state and updated by USDA; sites only
  appear once they've opened for the season. The page always links to the
  official finder and the Alaska Child Nutrition Programs office for corrections.
- **Day parsing:** `Days_of_operation` is free text *and* compact letter codes
  (e.g. `M,T,W,TH,F`, `Mon-Fri`, `Daily`). The parser handles both and renders
  friendly ranges (`Mon–Fri`). Sites whose days can't be parsed confidently are
  shown in an “Other sites (call for days)” section rather than guessed into a
  weekday — and the raw text is always displayed.
- This is a community-built page, not an official USDA website.

## Files

| File | Purpose |
|------|---------|
| `generate.py` | Fetches, filters, and renders the pages (stdlib only) |
| `i18n.py` | Page-chrome translations (first-party data) |
| `test_generate.py` | Unit tests (`python -m unittest`) |
| `mock.json` | Sample data for offline testing (legacy + 2026 schema) |
| `tools/make-assets.mjs` | Dev-only icon + OG-image generator |
| `.github/workflows/update.yml` | Daily rebuild + deploy |
| `docs/index.html` | Generated English page (Pages serves this folder) |
| `docs/<lang>/index.html` | Generated per-language pages |
| `docs/sites.txt` | Generated plain-text version |
| `docs/data.json` | Generated cleaned data |
| `docs/favicon.svg`, `og-image.png`, … | Icons + social-share card |
