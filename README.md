# 🏟️ Fan Dashboard

A personal sports dashboard you can host for free on GitHub Pages. Tracks your teams' schedules and news headlines in one place — filterable by team, tabbed between schedule and news. **Both auto-update weekly via GitHub Actions.**

**[→ See a live example](https://your-username.github.io/fan-dashboard)**

---

## Features

- **Schedule tab** — upcoming games grouped by day, with Home/Away tags
- **News tab** — latest headlines per team, pulled from each team's fan blog RSS feed
- **Team filters** — click any team to focus the view
- **Pro + College sections** — separate sections with off-season teams faded
- **Auto-updates weekly** — GitHub Action refreshes both schedule and news every Monday at 9 AM UTC
- **Mobile-friendly** — works well on phone browsers
- **Zero servers, zero API keys, zero cost**

---

## What's in the repo

```
fan-dashboard/
├── index.html                       # the dashboard (HTML/CSS/JS)
├── update_dashboard.py              # fetches schedules from ESPN, rewrites index.html
├── news_fetcher.py                  # fetches news from RSS feeds
├── test_update_dashboard.py         # unit tests for the parser
└── .github/workflows/update.yml     # the weekly automation
```

---

## Quickstart (15 minutes)

### 1. Fork or copy this repo

Click **Fork** in GitHub, or create a new repo and upload all the files above.

### 2. Customize your teams

Three places to edit:

**A) `index.html` — team filter buttons and colors:**

In the `<style>` block, add CSS for each team:
```css
.badge-lakers { background: #5B2582; color: #F0B429; }
```

In the `TEAMS` object near the top of the `<script>`:
```js
const TEAMS = {
  lakers: { label:'LAL', badge:'badge-lakers', pro: true },
  // 'college: true' instead of 'pro: true' for college teams
};
```

In the filter buttons:
```html
<button class="filter-btn" data-t="lakers">Lakers</button>
```

**B) `update_dashboard.py` — ESPN team IDs:**

```python
TEAMS = {
    "lakers": {
        "label": "LAL", "badge": "badge-lakers",
        "sport": "basketball", "league": "nba",
        "espn_id": "13",        # ← find in ESPN URL: espn.com/nba/team/_/id/13/...
        "pro": True,
    },
}
```

**C) `news_fetcher.py` — RSS feed URLs:**

```python
NEWS_FEEDS = {
    "lakers":  ("Silver Screen & Roll", "https://www.silverscreenandroll.com/rss/index.xml"),
}
```

### 3. Enable GitHub Pages

**Settings → Pages → Source → Deploy from branch → main → / (root) → Save**

Your dashboard goes live at:
```
https://YOUR-USERNAME.github.io/REPO-NAME
```

### 4. Enable Action write permissions

**Settings → Actions → General → Workflow permissions → Read and write permissions → Save**

This lets the Action commit fresh data back to your repo.

### 5. Test the automation

**Actions tab → Update Dashboard → Run workflow → Run workflow**

Wait 30 seconds. You should see a green checkmark and a new commit titled "Auto-update schedule and news". Your live URL now shows the fresh data.

---

## How it works

When the Action runs (every Monday at 9 AM UTC, or any time you trigger it manually):

1. **Checkout** — pulls your repo
2. **Fetch schedules** — for each team, hits `site.api.espn.com/.../teams/{id}/schedule` and parses the next 7 days of games
3. **Fetch news** — for each team, parses the RSS feed of its fan blog and grabs the latest 3 headlines
4. **Rewrite** — replaces the content between marker comments in `index.html`. Manual sections (team colors, page title) are preserved
5. **Commit** — if anything changed, commits with a timestamp and pushes
6. **Deploy** — GitHub Pages auto-redeploys within ~30 seconds

---

## Finding RSS feeds for your teams

- **SB Nation sites** (most fan blogs): append `/rss/index.xml`
- **WordPress sites**: append `/feed/`
- **Substack newsletters**: append `/feed`
- **Custom sites**: view source, search for `application/rss+xml`

If a feed fails, the script logs a warning and that team's news section just goes empty for the week. No crashes.

---

## Updating manually

You can also edit `index.html` directly in GitHub's web editor anytime. The auto-update only overwrites the sections between the `BEGIN AUTO-GENERATED` markers — everything else stays.

---

## Running locally

```bash
# Install dependencies
pip3 install requests feedparser

# Run the update script
python3 update_dashboard.py

# Open the result in your browser
open index.html

# Run the tests
pip3 install pytest
python3 -m pytest test_update_dashboard.py -v
```

---

## Honest caveats

- **ESPN's API is undocumented.** Stable for years but not guaranteed. If it breaks, [TheSportsDB](https://www.thesportsdb.com/) is a free alternative.
- **RSS feeds can disappear.** A blog might redesign or kill their feed. Check the Actions logs occasionally for ⚠ warnings.
- **Timezone is hardcoded to PT** in the script. Easy to make configurable.
- **It's polite to ESPN and fan blogs.** ~16 requests per week is fine. Don't crank the cron schedule.

---

## License

MIT — use it, fork it, share it. If you build something cool, share the link!
