# The Sports Dashboard I Built for Myself (and Why I Stopped Automating It)

*One HTML file on GitHub Pages that shows my teams' schedules and news in one place. I tried to make it update itself. Here's what happened, and why I update it by hand now.*

---

When I was younger I was a sports nut. I'd finish work and watch Dodgers games and Lakers games. At one point I got really into soccer after working on a soccer fan project in grad school. I became a Real Madrid fan and played league soccer in NYC for several years. I also went to NYCFC games, since the club started the same year I moved to NYC, so it's near and dear to my heart.

These days I'm busier, but I still want to follow my teams: Lakers, Dodgers, Real Madrid, NYCFC, Angel City FC, UCLA, USC, and UC Davis. Every week I was opening different tabs, apps, and bookmarks just to figure out what was on tonight. I rarely have time to watch a full game, so I want the headlines too.

So I built a dashboard.

## What I Built

It's a single `index.html` file hosted for free on GitHub Pages, at a URL I can bookmark: **[bessiec.github.io/sportsfan-dashboard](https://bessiec.github.io/sportsfan-dashboard)**.

It has two tabs:

- **Schedule**: upcoming games grouped by day, with Home/Away tags. Pro and college teams have their own sections, and off-season teams are faded so they're there but out of the way.
- **News**: the latest few headlines for each team, mostly from fan blogs like Silver Screen & Roll, True Blue LA, and Managing Madrid. Click a headline to open the article.

A row of team filters lets me focus on one team at a time.

There's no framework, no build step, and no backend. It's plain HTML, CSS, and JavaScript, and it works fine on my phone.

## The Automation Attempt

The first version updated itself. I wrote two small Python scripts:

- `update_dashboard.py` pulled each team's schedule from ESPN's public JSON API.
- `news_fetcher.py` pulled headlines from each team's RSS feed.

A GitHub Action ran them every Monday morning and committed the refreshed `index.html` back to the repo, and GitHub Pages redeployed it. It cost nothing, and for a while it worked well.

## Then ESPN Said No

Eventually ESPN started returning **403 Forbidden** to requests coming from GitHub Actions. Nothing in my code had changed. Some teams still came through and others didn't, and I couldn't count on any given Monday's data being complete. Around the same time, a few of the RSS feeds started failing or throttling too.

That's not a bug I could fix. It's a decision ESPN made about who gets to use their API, and they made it on purpose.

## Why I Didn't Spoof My Way Around It

The obvious fix was to add `Referer` and `Origin` headers so my requests looked like they came from espn.com. That would probably have worked for a while.

I decided not to. It would misrepresent where the requests were coming from, and it would get around a block that someone deliberately put in place. ESPN doesn't owe me a free API. If they don't want automated traffic from cloud servers, that's their call. A dashboard for my own use isn't a good reason to be sneaky about it.

## The Options I Weighed

Once spoofing was off the table, I looked at three options:

1. **TheSportsDB (free tier).** It's a community-run sports database with a real, documented API. But the free tier is limited, and its coverage of college teams and some leagues was spotty for my mix of teams.
2. **MySportsFeeds (about $10/month).** It's a proper paid API with clear terms. But $120 a year is a lot for a page only I look at, and I'd still need separate sources for soccer and news.
3. **Manual refresh with Claude.** Once a week, I ask Claude for an updated `index.html` with the coming week's games and recent headlines, then commit it myself.

## Why Manual Won

For a personal tool, manual came out ahead on almost everything:

- **It costs nothing**, and it doesn't depend on any API's rules or rate limits.
- **It takes about five minutes a week.** I was already checking in on my teams on Sundays anyway.
- **It's easier to trust.** I look at the page before it goes live, so I catch anything odd, like a postponed game or a wrong time.
- **There's nothing to maintain.** No broken Action to debug on a Monday morning, and no feed URLs quietly dying.

The automation was fun to build. But it solved a problem I didn't really have. Spending five minutes once a week was never what bothered me. Juggling eight tabs was.

## What the Weekly Workflow Looks Like

Every Sunday:

1. I ask Claude for a refreshed `index.html` with the coming week's schedule and the latest news for my teams.
2. I download the file and drop it into my local copy of the repo.
3. I open it in my browser to check it looks right.
4. I commit and push:

   ```bash
   git add index.html
   git commit -m "Weekly update"
   git push
   ```

5. About 30 seconds later, GitHub Pages has the new version live.

That's all.

## Build Your Own

The repo is at **[github.com/bessiec/sportsfan-dashboard](https://github.com/bessiec/sportsfan-dashboard)**. To make your own:

1. Fork the repo.
2. In `index.html`, change the team list, filter buttons, and badge colors to match your teams. The README walks through each spot.
3. Turn on GitHub Pages: **Settings → Pages → Deploy from branch → main → / (root) → Save**.
4. Each week, update the schedule and news sections of `index.html` (by hand, or by asking Claude) and push.

The old Python scripts are still in the repo as a record of the automation attempt. They don't run on their own anymore.

## What I'd Add Next

- **PWA support**, so I can add it to my phone's home screen and it opens like an app.
- **Team logos** in place of the text badges.
- **Dark mode**, for checking scores late at night.

None of these are urgent. The dashboard already does what I needed: one place to check on my teams.

---

*Built with help from Claude. Hosted for free on GitHub Pages.*
