"""
update_dashboard.py
-------------------
Fetches the next 7 days of games for each of my teams from ESPN's public API,
then rewrites the SCHEDULE block in index.html with the fresh data.

Run manually:   python update_dashboard.py
Run in CI:      called by .github/workflows/update.yml every Monday at 9am UTC

WHY THIS DESIGN:
- No API keys: ESPN's site.api.espn.com endpoints are public and don't require auth
- No dependencies beyond `requests`: keeps the GitHub Action fast and reliable
- Idempotent: running it twice in a row produces the same output
- Fails loudly: if a single team's API call fails, we log it and continue with the others
  rather than producing a half-broken file
"""

import json
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests


# ─── Team configuration ──────────────────────────────────────────────────────
# Each team's ESPN sport/league path + team ID.
# Find these by visiting espn.com/[sport]/team/_/id/[id] and watching the network tab.
# I keep the human display data here so the dashboard JSON stays self-contained.

TEAMS = {
    "lakers": {
        "label": "LAL",
        "badge": "badge-lakers",
        "sport": "basketball",
        "league": "nba",
        "espn_id": "13",
        "pro": True,
    },
    "dodgers": {
        "label": "LAD",
        "badge": "badge-dodgers",
        "sport": "baseball",
        "league": "mlb",
        "espn_id": "19",
        "pro": True,
    },
    "madrid": {
        "label": "RMA",
        "badge": "badge-madrid",
        "sport": "soccer",
        "league": "esp.1",  # La Liga
        "espn_id": "86",
        "pro": True,
    },
    "nycfc": {
        "label": "NYC",
        "badge": "badge-nycfc",
        "sport": "soccer",
        "league": "usa.1",  # MLS
        "espn_id": "17606",
        "pro": True,
    },
    "acfc": {
        "label": "ACFC",
        "badge": "badge-acfc",
        "sport": "soccer",
        "league": "usa.nwsl",
        "espn_id": "21422",
        "pro": True,
    },
    # College teams: ESPN has these too, but their schedules end after the season.
    # In the off-season they return empty arrays, which the dashboard handles
    # by falling back to the "Offseason" card defined in COLLEGE_FALLBACKS below.
    "ucla": {
        "label": "UCLA",
        "badge": "badge-ucla",
        "sport": "basketball",  # Will be active during Nov-Mar
        "league": "mens-college-basketball",
        "espn_id": "26",
        "college": True,
    },
    "usc": {
        "label": "USC",
        "badge": "badge-usc",
        "sport": "basketball",
        "league": "mens-college-basketball",
        "espn_id": "30",
        "college": True,
    },
    "ucdavis": {
        "label": "UCD",
        "badge": "badge-ucdavis",
        "sport": "basketball",
        "league": "mens-college-basketball",
        "espn_id": "302",
        "college": True,
    },
}

# Static fallback cards for teams in the off-season.
# These appear faded ("dim") in the dashboard when ESPN returns no upcoming games.
COLLEGE_FALLBACKS = [
    {
        "team": "ucla",
        "title": "UCLA — Off-season",
        "meta": "Football / Basketball / Soccer — seasons resume Aug–Sep",
        "note": "",
        "day": "Off-season",
        "time": "—",
        "tv": "",
        "home": False,
        "dim": True,
    },
    {
        "team": "usc",
        "title": "USC — Off-season",
        "meta": "All sports — seasons resume Aug–Sep",
        "note": "",
        "day": "Off-season",
        "time": "—",
        "tv": "",
        "home": False,
        "dim": True,
    },
    {
        "team": "ucdavis",
        "title": "UC Davis — Off-season",
        "meta": "Big West sports — seasons resume Aug–Sep",
        "note": "",
        "day": "Off-season",
        "time": "—",
        "tv": "",
        "home": False,
        "dim": True,
    },
]


# ─── ESPN API ────────────────────────────────────────────────────────────────

ESPN_BASE = "https://site.api.espn.com/apis/site/v2/sports"

# Some CDN edges return 403 for bare `python-requests/x.y.z` User-Agent strings.
# A normal browser UA avoids that. We're a polite weekly script — no abuse risk.
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
    ),
    "Accept": "application/json",
}


def fetch_team_schedule(team_key, team_config):
    """
    Hits the ESPN schedule endpoint for one team and returns a normalized list
    of games. Returns [] on any failure — we'd rather miss a team than crash.
    """
    sport = team_config["sport"]
    league = team_config["league"]
    espn_id = team_config["espn_id"]

    url = f"{ESPN_BASE}/{sport}/{league}/teams/{espn_id}/schedule"

    try:
        response = requests.get(url, timeout=10, headers=HEADERS)
        response.raise_for_status()
        data = response.json()
    except (requests.RequestException, ValueError) as e:
        print(f"  ⚠ Failed to fetch {team_key}: {e}", file=sys.stderr)
        return []

    events = data.get("events", [])
    games = []
    now = datetime.now(timezone.utc)
    horizon = now + timedelta(days=10)

    for event in events:
        try:
            game = parse_espn_event(event, team_key, team_config, now, horizon)
            if game:
                games.append(game)
        except (KeyError, IndexError, ValueError) as e:
            print(f"  ⚠ Skipped malformed event for {team_key}: {e}", file=sys.stderr)
            continue

    return games


def parse_espn_event(event, team_key, team_config, now, horizon):
    """
    Convert an ESPN event JSON blob into our dashboard's game format.
    Returns None for games outside our display window.
    """
    # ESPN gives times as ISO 8601 with a Z suffix
    start_str = event["date"]
    start = datetime.fromisoformat(start_str.replace("Z", "+00:00"))

    # Only include games from yesterday (so we can show "Today" recaps) through 7 days out
    if start < now - timedelta(days=1) or start > horizon:
        return None

    competitions = event.get("competitions", [])
    if not competitions:
        return None
    competition = competitions[0]
    competitors = competition.get("competitors", [])
    if len(competitors) != 2:
        return None

    # Find ourselves vs the opponent
    home_competitor = next((c for c in competitors if c.get("homeAway") == "home"), None)
    away_competitor = next((c for c in competitors if c.get("homeAway") == "away"), None)
    if not home_competitor or not away_competitor:
        return None

    my_id = team_config["espn_id"]
    is_home = home_competitor["id"] == my_id
    opponent = (away_competitor if is_home else home_competitor)["team"]["displayName"]

    # Title: "Lakers vs Warriors" when home, "Lakers at Warriors" when away
    my_team_name = (home_competitor if is_home else away_competitor)["team"]["shortDisplayName"]
    title = f"{my_team_name} {'vs' if is_home else 'at'} {opponent}"

    # Venue and league name for the meta line
    venue = competition.get("venue", {}).get("fullName", "")
    league_name = league_display_name(team_config["league"])
    meta_parts = [league_name, "Home" if is_home else "Away"]
    if venue:
        meta_parts.append(venue)
    meta = " · ".join(meta_parts)

    # TV broadcast — ESPN provides this on most games
    broadcasts = competition.get("broadcasts", [])
    tv = broadcasts[0]["names"][0] if broadcasts and broadcasts[0].get("names") else ""

    # Day label + time, in user's local time (PT for me)
    start_pt = start.astimezone(timezone(timedelta(hours=-7)))  # PDT; adjust seasonally
    today_pt = datetime.now(timezone(timedelta(hours=-7))).date()
    days_until = (start_pt.date() - today_pt).days

    if days_until == 0:
        day = f"Today — {start_pt.strftime('%a %b %-d')}"
    elif days_until == 1:
        day = f"Tomorrow — {start_pt.strftime('%a %b %-d')}"
    else:
        day = start_pt.strftime("%a %b %-d")

    time_str = start_pt.strftime("%-I:%M %p PT")

    # Score note for completed games
    note = ""
    status = event.get("status", {}).get("type", {}).get("state", "")
    if status == "post":
        my_score = (home_competitor if is_home else away_competitor)["score"]
        opp_score = (away_competitor if is_home else home_competitor)["score"]
        result = "W" if int(my_score) > int(opp_score) else "L"
        note = f"Final: {result} {my_score}-{opp_score}"
        time_str = "Final"

    return {
        "team": team_key,
        "title": title,
        "meta": meta,
        "note": note,
        "day": day,
        "time": time_str,
        "tv": tv,
        "home": is_home,
    }


def league_display_name(league_code):
    """Map ESPN's league codes to human-readable names for the meta line."""
    return {
        "nba": "NBA",
        "mlb": "MLB",
        "esp.1": "La Liga",
        "usa.1": "MLS",
        "usa.nwsl": "NWSL",
        "mens-college-basketball": "NCAA M Basketball",
        "womens-college-basketball": "NCAA W Basketball",
    }.get(league_code, league_code)


# ─── File rewriting ──────────────────────────────────────────────────────────

# Markers in index.html tell us where each auto-generated block lives.
# Everything between them gets replaced; everything outside is preserved.
SCHEDULE_START = "// ─── BEGIN AUTO-GENERATED SCHEDULE ───"
SCHEDULE_END   = "// ─── END AUTO-GENERATED SCHEDULE ───"
NEWS_START     = "// ─── BEGIN AUTO-GENERATED NEWS ───"
NEWS_END       = "// ─── END AUTO-GENERATED NEWS ───"


def build_schedule_block(games):
    """Turn the games list into the JavaScript that goes into index.html."""
    js_array = json.dumps(games, indent=2, ensure_ascii=False)
    timestamp = datetime.now().strftime('%b %d, %Y at %I:%M %p UTC')
    return (
        f"{SCHEDULE_START}\n"
        f"const SCHEDULE = {js_array};\n"
        f"const LAST_UPDATED = '{timestamp}';\n"
        f"{SCHEDULE_END}"
    )


def build_news_block(news_dict):
    """Turn the news dict into the JavaScript that goes into index.html."""
    js_obj = json.dumps(news_dict, indent=2, ensure_ascii=False)
    return f"{NEWS_START}\nconst NEWS = {js_obj};\n{NEWS_END}"


def replace_block(content, start_marker, end_marker, new_block):
    """Replace one marked block in the file content; raises if marker missing."""
    pattern = re.compile(
        re.escape(start_marker) + r".*?" + re.escape(end_marker),
        re.DOTALL,
    )
    if not pattern.search(content):
        raise RuntimeError(
            f"Markers not found: {start_marker} ... {end_marker}\n"
            f"Add the marker comments around the relevant constant in index.html."
        )
    return pattern.sub(new_block, content)


def rewrite_index_html(games, news_dict, index_path):
    """Replace BOTH auto-generated sections of index.html with fresh data."""
    content = index_path.read_text()
    new_content = replace_block(content, SCHEDULE_START, SCHEDULE_END, build_schedule_block(games))
    new_content = replace_block(new_content, NEWS_START, NEWS_END, build_news_block(news_dict))

    if new_content == content:
        print("  → No changes detected (file already up to date)")
        return False

    index_path.write_text(new_content)
    return True


# ─── Main ────────────────────────────────────────────────────────────────────


def main():
    index_path = Path(__file__).parent / "index.html"
    if not index_path.exists():
        print(f"❌ index.html not found at {index_path}", file=sys.stderr)
        sys.exit(1)

    # ─── Schedule (from ESPN) ─────────────────────────────────────────
    print("=== Fetching schedules ===")
    all_games = []
    for team_key, team_config in TEAMS.items():
        print(f"→ Fetching {team_key}...")
        games = fetch_team_schedule(team_key, team_config)
        if games:
            print(f"  ✓ {len(games)} games")
            all_games.extend(games)
        elif team_config.get("college"):
            print(f"  · No active games — will use off-season fallback")

    # For college teams with no live games, add the fallback cards
    college_with_games = {g["team"] for g in all_games if TEAMS[g["team"]].get("college")}
    for fallback in COLLEGE_FALLBACKS:
        if fallback["team"] not in college_with_games:
            all_games.append(fallback)

    print(f"\n✓ Total: {len(all_games)} game entries")

    # ─── News (from RSS feeds) ────────────────────────────────────────
    print("\n=== Fetching news ===")
    from news_fetcher import fetch_all_news
    news_dict = fetch_all_news()
    print(f"\n✓ News fetched for {len(news_dict)} teams")

    # ─── Rewrite the file ─────────────────────────────────────────────
    print("\n=== Updating index.html ===")
    changed = rewrite_index_html(all_games, news_dict, index_path)
    if changed:
        print("✓ index.html updated")
    sys.exit(0)


if __name__ == "__main__":
    main()
