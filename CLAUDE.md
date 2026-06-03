# CLAUDE.md — project context for AI sessions

Context for working on this repo. Read this and `README.md` before changing anything.

## What this is

A **dependency-free Python script** (`generate.py`, standard library only) that
queries the public **USDA-FNS Summer Meals Site Finder** ArcGIS feature service,
filters to the Anchorage area, and renders a static, accessible site into
`docs/`:

- `docs/index.html` — English page (Open today → full week), plus
  `docs/<lang>/index.html` for each non-English locale.
- `docs/sites.txt` — plain-text version (low-bandwidth / SMS body).
- `docs/data.json` — cleaned, filtered records.

A GitHub Action (`.github/workflows/update.yml`) rebuilds it every morning and
deploys `docs/` to GitHub Pages. The page is shared by **SMS with ~20,000
people**, so speed, reliability, and **WCAG 2.1 AA** accessibility are
first-class requirements.

## Hard rules (do not break)

1. **`generate.py` is standard-library only at runtime.** No `pip install` in
   the Action. Accessibility/asset tooling (pa11y, axe, html-validate,
   puppeteer, png-to-ico) is **dev-only** — see `package.json` / `tools/`.
   `i18n.py` is first-party data, not a third-party dependency.
2. **Never publish an empty or broken page.** If the data fetch fails,
   `generate.py` exits non-zero so the last good Pages deploy stays live. Keep
   that fail-safe.
3. **Site-level info only.** Show site name, address, and site phone. **Never**
   surface the personal contact first/last name or personal phone fields from
   the feed. The fetch does not even request those columns.
4. **No secrets in code.** The season endpoint lives in the repo **variable**
   `SERVICE_URL`, not hardcoded credentials.

## Data source — important specifics

- Org service directory:
  `https://services1.arcgis.com/RLQu0rK7h4kbsBq5/arcgis/rest/services`
- **Current endpoint (2026):** `Summer_Meals_Site_Finder_2026_(Testing)` —
  layer 0 `/query`. This is the only service with real, `Season=2026` Alaska
  data. ⚠️ **Open question:** its name still says "(Testing)" on USDA's side.
  Confirm with USDA-FNS / Alaska Child Nutrition Programs whether a renamed
  production endpoint will appear; if so, just update the `SERVICE_URL` repo
  variable (no code change).
- The schema **drifts between seasons**. The code is defensive about it:
  - It requests only fields the layer actually exposes (asking for a missing
    field makes ArcGIS return **zero** features).
  - Meal times come from `Foo_Time` **or** `Foo_Time2`; season dates from text
    (`StartDateText`/`EndDateText`) **or** epoch (`Start_date`/`End_date`).
  - `Days_of_operation` is free text **and** compact letter codes
    (`M,T,W,TH,F,SA`); `parse_days()` handles both. Anything ambiguous falls
    into the "Other sites (call for days)" bucket; raw text is always shown.
  - `Service_Model` is `CONGREGATE` / `NON-CONGREGATE PICK UP` (or legacy
    `Eat On-Site` / `Meals To Go`) → mapped to friendly labels.
  - City is hand-entered; known typos (e.g. `Anchroage`) stay in scope and are
    corrected for display (`CITY_FIXES`).
- Scope = the whole **Municipality of Anchorage** (`SCOPE_CITIES`), which
  includes Eagle River, Chugiak, Girdwood, etc. Set `SCOPE_CITIES = {"anchorage"}`
  for the city proper.

## How to run

```bash
python generate.py                 # live build into docs/   (needs network)
MOCK_DATA=mock.json python generate.py   # offline build from sample data
python -m unittest                 # run the test suite (stdlib unittest)
```

Environment variables (all optional): `SERVICE_URL`, `SITE_URL`, `OUT_DIR`,
`MOCK_DATA`. On Windows the interpreter is `python` (not `python3`).

## Tests

`test_generate.py` (stdlib `unittest`, no pytest) covers `parse_days`,
`format_days`, `parse_text_date`, `parse_epoch_date`, `model_info`, scope
filtering (incl. the `Anchroage` typo), status, and that PII fields never reach
the output. Importing `generate.py` does **not** hit the network.

## Internationalization

`i18n.py` holds the page-chrome translations (only headings/labels/footer —
listings stay as USDA provides). Non-English pages render a visible
**"machine-translated, awaiting human review"** banner. **Route translations
through the Municipality's language-access resources before launch** and only
then remove the banner (clear `review_note` / `needs_review`).

## Dev tooling / assets

- `npm install` then `npm run validate` / `npm run a11y` (serve first with
  `npm run serve`).
- `npm run make-assets` regenerates icons + the 1200×630 OG card from
  `docs/favicon.svg` via `tools/make-assets.mjs`. These are committed static
  files; the daily Action does not regenerate them.

## Accessibility bar

Built pages must report **zero** WCAG 2.1 AA violations (axe-core + pa11y) and
Lighthouse accessibility **100**, and pass `html-validate`. Re-check after any
template change.
