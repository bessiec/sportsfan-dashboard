"""
news_fetcher.py
---------------
Fetches the latest headlines from each team's fan blog RSS feed.
Returns a dict keyed by team that the main script merges into index.html.

DESIGN NOTES:
- Each team gets its own RSS feed URL (configurable below)
- We only fetch the 3 most recent entries per team
- Date parsing is best-effort — RSS dates are notoriously inconsistent across publishers
- A failed feed produces an empty list for that team, NOT a crash
- We log every failure so you can see in the Action logs which feeds are broken
"""

import sys
from datetime import datetime

import feedparser


# Each team maps to: (display source name, RSS feed URL)
# To find a site's RSS feed: append /rss/index.xml (SB Nation), /feed/ (WordPress),
# or look for <link rel="alternate" type="application/rss+xml"> in the page source.
NEWS_FEEDS = {
    "lakers":   ("Silver Screen & Roll",  "https://www.silverscreenandroll.com/rss/index.xml"),
    "dodgers":  ("True Blue LA",          "https://www.truebluela.com/rss/index.xml"),
    "madrid":   ("Managing Madrid",       "https://www.managingmadrid.com/rss/index.xml"),
    "nycfc":    ("NYCFC Official",        "https://www.nycfc.com/rss.xml"),
    "acfc":     ("Angels on Parade",      "https://angelsonparade.com/feed"),  # no trailing slash
    "ucla":     ("UCLA Bruins",           "https://uclabruins.com/services/rss.aspx?rss=1"),
    "usc":      ("USC Trojans",           "https://usctrojans.com/services/rss.aspx?rss=1"),
    "ucdavis":  ("UC Davis Aggies",       "https://ucdavisaggies.com/services/rss.aspx?rss=1"),
}

# Same browser-style UA we use for ESPN — some sites block bare python-requests/feedparser UAs
USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
)


def fetch_team_news(team_key, source_name, feed_url, max_items=3):
    """
    Returns a dict like { 'src': 'Silver Screen & Roll', 'items': [...] }
    or None if the feed couldn't be fetched.

    Each item: { 'title': str, 'url': str, 'date': str }
    """
    try:
        feed = feedparser.parse(feed_url, agent=USER_AGENT)
    except Exception as e:
        print(f"  ⚠ {team_key} feed crashed: {e}", file=sys.stderr)
        return None

    # feedparser sets `bozo=1` on malformed feeds but often still returns usable entries
    if not feed.entries:
        status = getattr(feed, "status", "?")
        print(f"  ⚠ {team_key} feed returned no entries (HTTP {status})", file=sys.stderr)
        return None

    items = []
    for entry in feed.entries[:max_items]:
        title = entry.get("title", "").strip()
        url = entry.get("link", "").strip()
        if not title or not url:
            continue
        items.append({
            "title": title,
            "url": url,
            "date": format_entry_date(entry),
        })

    if not items:
        return None

    return {"src": source_name, "items": items}


def format_entry_date(entry):
    """
    Pull a human-readable date out of an RSS entry.
    Returns 'Mar 28' style. Falls back to '' if no parseable date.
    """
    # feedparser normalizes dates to a struct_time tuple
    parsed = entry.get("published_parsed") or entry.get("updated_parsed")
    if not parsed:
        return ""
    try:
        dt = datetime(*parsed[:6])
        return dt.strftime("%b %-d")
    except (ValueError, TypeError):
        return ""


def fetch_all_news():
    """
    Fetch news for every team. Returns a dict { team_key: {src, items} }.
    Teams whose feeds failed are simply omitted.
    """
    result = {}
    for team_key, (source_name, feed_url) in NEWS_FEEDS.items():
        print(f"→ Fetching news for {team_key}...")
        news = fetch_team_news(team_key, source_name, feed_url)
        if news:
            print(f"  ✓ {len(news['items'])} headlines")
            result[team_key] = news
    return result


if __name__ == "__main__":
    # Allow running this file directly for testing the feeds
    import json
    print(json.dumps(fetch_all_news(), indent=2, ensure_ascii=False))
