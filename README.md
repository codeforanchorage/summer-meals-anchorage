# Free Summer Meals in Anchorage

A tiny, fast, accessible web page that lists USDA Summer Food Service Program
sites in the Municipality of Anchorage — what's **open today** at the top, and
the **full week** below. Built to be shared by text message with a large
audience.

It rebuilds itself every morning from the public USDA-FNS Summer Meals Site
Finder data feed. No servers, no database — just a static page on GitHub Pages.

## How it works

```
GitHub Action (daily)  ->  generate.py queries the USDA feature service
                       ->  filters to Anchorage + currently-open sites
                       ->  writes docs/index.html + docs/sites.txt
                       ->  deploys docs/ to GitHub Pages
```

Because the page is pre-rendered static HTML on a CDN, a burst of traffic from
an SMS blast to tens of thousands of people is a non-issue, and it loads fast on
a weak mobile connection even if the USDA service is slow that minute.

## Setup (about 5 minutes)

1. Create a new GitHub repo and add these files.
2. In **Settings → Pages**, set **Source = GitHub Actions**.
3. Go to the **Actions** tab, enable workflows, and run **Build summer meals
   page** once (the "Run workflow" button). After it finishes, your page is live
   at the URL shown in the workflow's `deploy` step.
4. It will then rebuild automatically every morning.

### Confirm the data endpoint first

The feed is versioned by season. This repo defaults to:

```
https://services1.arcgis.com/RLQu0rK7h4kbsBq5/arcgis/rest/services/Summer_Meal_Site_Finder_2026_WFL1/FeatureServer/0/query
```

Confirm the current-season name by opening the org's service directory and
looking for the newest `Summer_Meal_Site_Finder_<year>_WFL1`:

```
https://services1.arcgis.com/RLQu0rK7h4kbsBq5/arcgis/rest/services
```

If it differs, either edit `SERVICE_URL` at the top of `generate.py` or — better —
set a repo **variable** named `SERVICE_URL` (Settings → Secrets and variables →
Actions → Variables) so you can update it each year without touching code.

## Customizing

Everything tunable lives at the top of `generate.py`:

- **`SCOPE_CITIES`** — defaults to the whole Municipality of Anchorage (includes
  Eagle River, Chugiak, Girdwood, etc.). For the city proper only, set this to
  `{"anchorage"}`.
- **`SERVICE_URL`** — the season's query endpoint.
- **`STATE_AGENCY` / `OFFICIAL_FINDER` / `HUNGER_HOTLINE`** — footer links.

## Test it offline

No network needed — render from the included sample data:

```bash
MOCK_DATA=mock.json python3 generate.py
open docs/index.html
```

## Custom domain for the SMS link

A branded link (e.g. `meals.codeforanchorage.org`) is friendlier in a text and
far less likely to be caught by carrier spam filters than a generic shortener —
and you can repoint it later without re-texting anyone. Add a `CNAME` file in
`docs/` containing your domain and set the DNS record per GitHub's custom-domain
docs.

## Notes / caveats

- **PII:** the source data carries individual contact names and personal phone
  numbers. This page intentionally shows only the **site** name, address, and
  site phone.
- **Accuracy:** data is submitted by the state and updated by USDA on Fridays;
  sites only appear once they've opened for the season. The page always links to
  the official finder and the Alaska Child Nutrition Programs office for
  corrections.
- **Day parsing:** `Days_of_operation` is free text. The parser handles common
  formats (e.g. "Mon-Fri", "Monday through Friday", "Daily", "Tue, Thu"). Sites
  whose days can't be parsed confidently are shown in an "Other sites (call for
  days)" section rather than guessed into a weekday — and the raw text is always
  displayed.
- This is a community-built page, not an official USDA website.

## Files

| File | Purpose |
|------|---------|
| `generate.py` | Fetches, filters, and renders the page |
| `.github/workflows/update.yml` | Daily rebuild + deploy |
| `docs/index.html` | Generated page (Pages serves this folder) |
| `docs/sites.txt` | Generated plain-text version |
| `docs/data.json` | Generated cleaned data |
| `mock.json` | Sample data for offline testing |
