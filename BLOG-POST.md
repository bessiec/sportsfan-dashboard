# I Built a Sports Dashboard That Updates Itself — Free, on GitHub Pages

*A personal fan dashboard that uses GitHub Actions to refresh both its schedule and news every Monday. Zero cost, zero API keys, no servers.*

---

When I was younger I used to be a sports nut. I'd finish work and watch Dodgers games and Lakers games. At one point I got super into soccer after working on a soccer fan project in grad school and became a Real Madrid fan and played league soccer in NYC for several years. I also went to NYCFC games since the club started the first year I moved to NYC so it's near and dear to my heart.

I got too busy and still want to follow my teams I'm a fan of for one reason or another: Lakers, Dodgers, Real Madrid, NYCFC, Angel City FC, UCLA, USC, UC Davis. Every week I was opening different tabs, different apps, and various browser bookmarks just to figure out what was on tonight. Because I don't often have enough time to tune into a full game, I want to get the headlines too. 

So I built a dashboard. It lives at a URL I can bookmark. It shows all my teams' schedules and news in one place. And — this is the good part — **it updates itself**.

Here's how, and how you can build your own.

## What It Does

The dashboard has two tabs: **Schedule** and **News**.

The schedule shows upcoming games grouped by day, with Home/Away tags. Pro teams and college teams live in separate sections. Off-season teams show up faded so you know they exist but aren't cluttering the view.

The news tab shows the latest 2–3 headlines per team, pulled directly from each team's best fan blog (Silver Screen & Roll for Lakers, True Blue LA for Dodgers, Managing Madrid for Real Madrid, etc.). Click any headline to open the article in a new tab.

A row of team filters lets you focus on just one team when you want to.

The whole thing refreshes itself every Monday morning while I'm asleep.

## The Stack

The whole thing is one HTML file plus two small Python scripts. No React. No build step. No framework. No backend.

- **Frontend**: plain HTML/CSS/JS
- **Hosting**: GitHub Pages (free)
- **Auto-updates**: GitHub Actions running Python scripts (free)
- **Schedule data**: ESPN's public API (no key required)
- **News data**: RSS feeds from team fan blogs (also free, no key required)

Total monthly cost: $0. Total weekly maintenance: 0 minutes.

## How the Automation Works

This is the part I'm proud of, because it took a static GitHub Pages site and made it self-updating without introducing a server, a database, or a paid service.

**The trick** is that GitHub Actions can do two things people don't usually think to combine:
1. Run code on a schedule
2. Commit changes back to your own repo

Put those together and you get a poor man's CMS. Every Monday at 9 AM UTC, GitHub spins up a tiny Linux container, runs my Python scripts, and commits the result.

### Step 1: Schedule from ESPN

ESPN has an undocumented public API at `site.api.espn.com` that returns clean JSON for any team. No authentication. No rate limit at this volume. It's been stable for years.

```python
for team_key, team_config in TEAMS.items():
    url = f"{ESPN_BASE}/{team_config['sport']}/{team_config['league']}/teams/{team_config['espn_id']}/schedule"
    response = requests.get(url, timeout=10, headers=HEADERS)
    # ... parse the events into our dashboard's game format
```

For each team, the script fetches the next 7 days of games and turns each one into a card on the dashboard.

### Step 2: News from RSS

This was the harder part to get right, and the answer is humbler than you'd expect: **RSS still exists**, and almost every team fan blog on the internet exposes a feed.

SB Nation network sites (Silver Screen & Roll, True Blue LA, Managing Madrid, Hudson River Blue, Bruins Nation) all use `/rss/index.xml`. WordPress sites (Angels on Parade) use `/feed/`. Both are easy to consume with Python's `feedparser`:

```python
for team_key, (source_name, feed_url) in NEWS_FEEDS.items():
    feed = feedparser.parse(feed_url, agent=USER_AGENT)
    items = []
    for entry in feed.entries[:3]:
        items.append({
            "title": entry.get("title", "").strip(),
            "url": entry.get("link", "").strip(),
            "date": format_entry_date(entry),
        })
```

The interesting design decision: **failures are non-fatal**. If a team's feed returns 404 or malformed XML, the script logs a warning and continues. The dashboard simply shows no news for that team rather than crashing. That's the right tradeoff for a personal tool — partial freshness beats total brokenness.

### Step 3: Rewriting the HTML

The script has marker comments like `// ─── BEGIN AUTO-GENERATED SCHEDULE ───` so it knows exactly which sections to replace and leaves the rest untouched. The manual stuff (team colors, page title, layout) is safe.

```python
SCHEDULE_START = "// ─── BEGIN AUTO-GENERATED SCHEDULE ───"
SCHEDULE_END   = "// ─── END AUTO-GENERATED SCHEDULE ───"
NEWS_START     = "// ─── BEGIN AUTO-GENERATED NEWS ───"
NEWS_END       = "// ─── END AUTO-GENERATED NEWS ───"

def replace_block(content, start_marker, end_marker, new_block):
    pattern = re.compile(re.escape(start_marker) + r".*?" + re.escape(end_marker), re.DOTALL)
    return pattern.sub(new_block, content)
```

If anything actually changed, the Action commits the file:

```yaml
- name: Commit changes if any
  run: |
    git config user.name "dashboard-bot"
    git add index.html
    if git diff --staged --quiet; then
      echo "No changes — skipping commit"
    else
      git commit -m "Auto-update schedule and news ($(date -u +%Y-%m-%d))"
      git push
    fi
```

GitHub Pages picks up the new commit and redeploys within 30 seconds.

## Why This Is Better Than the Obvious Alternatives

**Why not a real backend?** Because I'd have to pay for a server, maintain it, monitor it, and rotate API keys. For a personal dashboard, that's wildly overbuilt.

**Why not fetch the data client-side in JavaScript?** I tried this. The ESPN API doesn't send CORS headers, so the browser blocks the request. I'd need a proxy server — back to having a backend.

**Why not a paid sports API?** SportsRadar, MySportsFeeds, and friends are great but cost $10–50/month. For a personal tool that's an order of magnitude too much.

**Why not a news API?** NewsAPI and Bing News exist but their free tiers are noisy (sports betting spam mixed in with real news) and rate-limited. RSS feeds from fan blogs give me higher-quality, team-specific content for free.

The GitHub Action approach is the right size for the job. GitHub gives you 2,000 free Action minutes per month, and my script uses about 1 minute per run × 4 runs per month = 4 minutes. I'd have to scale this to thousands of users before cost became an issue.

## Designing for Graceful Failure

This is the part of the project I'm most happy with from a software engineering perspective.

There are eight teams, each pulling from two sources (ESPN API + RSS feed). That's 16 network requests every Monday. Something will eventually break — a feed will return 404, a team will be missing from ESPN's data, a venue field will be malformed. The question is what happens then.

The wrong answer is "the whole script crashes and the dashboard freezes on stale data." The right answer is "log the failure clearly, skip the affected team, keep going for everyone else."

Every layer of the script catches its own errors:

- **Per-team fetch errors** → logged with ⚠, that team's section is empty for this run
- **Per-game parse errors** → logged, that game is skipped, others continue
- **Off-season detection** → if ESPN returns no games for a college team, fall back to a static "Off-season" card

The result: even if half the network calls fail, the dashboard still shows fresh data for whatever did succeed. And the Actions log shows me exactly which feeds need attention.

## Add a Test Suite

The parsing logic — taking ESPN's JSON or RSS's XML and turning it into the dashboard's format — is the most likely thing to break. So I wrote unit tests for it:

```python
def test_home_game_formats_as_vs():
    event = make_event(home_id="13", away_name="Boston Celtics", away_short="Celtics")
    result = parse_espn_event(event, "lakers", LAKERS_CONFIG, NOW, HORIZON)
    assert result["title"] == "Lakers vs Boston Celtics"
    assert result["home"] is True

def test_completed_game_includes_score():
    event = make_event(home_score="110", away_score="105", status_state="post")
    result = parse_espn_event(event, "lakers", LAKERS_CONFIG, NOW, HORIZON)
    assert "W 110-105" in result["note"]
```

The tests run automatically before any auto-update commits. If a future change to the parser breaks the schema, the Action fails before it can push broken HTML to my live site.

10 tests. 0.12 seconds. The right amount of testing for a project this size.

## How to Build Your Own

The repo is at **[github.com/YOUR-LINK]** with everything you need:

```
fan-dashboard/
├── index.html                       # the dashboard (with marker comments)
├── update_dashboard.py              # ESPN fetcher + file rewriter
├── news_fetcher.py                  # RSS feed fetcher
├── test_update_dashboard.py         # unit tests
├── README.md                        # quick start
└── .github/workflows/update.yml     # weekly automation
```

Setup takes about 15 minutes:

1. Fork the repo
2. Edit `update_dashboard.py` to use your teams' ESPN IDs (find them in the URL when you visit a team's ESPN page — e.g. `espn.com/nba/team/_/id/13/los-angeles-lakers` → ID `13`)
3. Edit `news_fetcher.py` to point at your favorite fan blogs' RSS feeds
4. Edit `index.html` to set your team colors
5. Enable GitHub Pages: **Settings → Pages → Deploy from branch → main → Save**
6. Enable Action write permissions: **Settings → Actions → Workflow permissions → Read and write**
7. Run the action manually once: **Actions tab → Update Dashboard → Run workflow**

Your dashboard lives at `https://your-username.github.io/your-repo-name`. The schedule and news both refresh automatically every Monday. You'll never have to think about it.

## Finding RSS Feeds for Your Teams

If you follow different teams, here's the trick for finding their fan blog RSS:

- **SB Nation sites** (most major team blogs): append `/rss/index.xml`
- **WordPress sites**: append `/feed/`
- **Substack newsletters**: append `/feed`
- **Custom sites**: view source, search for `application/rss+xml`

Add the URL to the `NEWS_FEEDS` dictionary in `news_fetcher.py`. The script handles the rest.

## Honest Caveats

A few things to know if you build this:

**ESPN's API could change.** It's not officially documented or guaranteed. In practice it's been stable for many years, but if ESPN restructures it, the script will break and you'll need to update it. For a swap-in alternative, [TheSportsDB](https://www.thesportsdb.com/) has a free tier that covers most leagues.

**RSS feeds can disappear.** A blog might redesign, kill their feed, or change URL patterns. The script handles failures gracefully — that team's news section just goes empty — but you'd want to glance at the Actions logs occasionally to spot persistent failures.

**Timezones are tricky.** My script hardcodes Pacific Time because that's where I live. Making it timezone-aware would take maybe 10 lines of Python.

**It's polite to be polite.** The script makes about 16 requests per run, once a week. That's fine. Don't crank the cron to "every minute" or you'll eventually get blocked by either ESPN's CDN or someone's WordPress server.

## What I'd Add Next

Things I've thought about but haven't built:

- **Fallback feeds** — for each team, try a secondary RSS source (e.g. their subreddit) if the primary fails
- **Last successful fetch timestamps** per team so I can see at a glance which news has gone stale
- **PWA support** so I can "Add to Home Screen" on mobile and it feels like a native app
- **Team logos** instead of text badges (ESPN's CDN hosts them at predictable URLs)
- **A configurator page** where someone can pick teams and download a customized repo without editing code

None of those are required to use the dashboard. They're just things that would be fun.

## Try It

If you build your own and share the link, I'd love to see it. The fork-and-customize loop should take under an hour. The result is something you'll actually use.

---

*Built with help from Claude (Anthropic) for the data parsing and schema design. Hosted free on GitHub Pages. Automated free with GitHub Actions. The whole project is in one repo.*
