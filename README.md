# 🏟️ Fan Dashboard

A personal sports dashboard you can host for free on GitHub Pages. Tracks your teams' schedules and news headlines in one place, filterable by team, with separate Schedule and News tabs. **I update it by hand once a week.**

**[→ See it live](https://bessiec.github.io/sportsfan-dashboard)**

---

## Features

- **Schedule tab**: upcoming games grouped by day, with Home/Away tags
- **News tab**: latest headlines per team
- **Team filters**: click any team to focus the view
- **Pro + College sections**: separate sections, with off-season teams faded
- **Mobile-friendly**: works well on phone browsers
- **One static file**: no servers, no API keys, no cost

---

## What's in the repo

```
sportsfan-dashboard/
├── index.html                  # the dashboard (HTML/CSS/JS + this week's data)
├── BLOG-POST.md                # write-up of how this came together
├── update_dashboard.py         # retired: old ESPN schedule fetcher (see History)
├── news_fetcher.py             # retired: old RSS news fetcher (see History)
└── test_update_dashboard.py    # retired: tests for the old fetcher
```

---

## Setup

### 1. Fork or copy this repo

Click **Fork** in GitHub, or create a new repo and upload `index.html`.

### 2. Customize your teams in `index.html`

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

### 3. Enable GitHub Pages

**Settings → Pages → Source → Deploy from branch → main → / (root) → Save**

Your dashboard goes live at:
```
https://YOUR-USERNAME.github.io/REPO-NAME
```

---

## Weekly updates

The schedule and news live in two blocks inside `index.html`, between these markers:

```
// ─── BEGIN AUTO-GENERATED SCHEDULE ───   …   // ─── END AUTO-GENERATED SCHEDULE ───
// ─── BEGIN AUTO-GENERATED NEWS ───       …   // ─── END AUTO-GENERATED NEWS ───
```

(The names are left over from the automation days.) Everything outside those blocks, like team colors, layout, and the page title, stays the same week to week.

My routine each Sunday:

1. Ask Claude for a refreshed `index.html` with the coming week's games and recent headlines.
2. Download it into my local copy of the repo and open it in a browser to check it.
3. Commit and push:
   ```bash
   git add index.html
   git commit -m "Weekly update"
   git push
   ```
4. GitHub Pages redeploys in about 30 seconds.

You can also edit `index.html` directly in GitHub's web editor.

---

## History

This dashboard used to update itself. A weekly GitHub Action ran `update_dashboard.py` (schedules from ESPN's public API) and `news_fetcher.py` (headlines from RSS feeds), then committed the new `index.html`.

Then ESPN started returning 403 Forbidden to requests from GitHub Actions IPs, the schedule data became unreliable, and several RSS feeds began failing or throttling. Instead of working around ESPN's block, I removed the workflow and switched to manual weekly updates. The scripts and tests are still in the repo as a record of that attempt. They don't run automatically anymore. [BLOG-POST.md](BLOG-POST.md) has the full story.

---

## License

MIT. Use it, fork it, share it. If you build something cool, share the link!
