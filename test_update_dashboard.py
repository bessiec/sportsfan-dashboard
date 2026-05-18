"""
test_update_dashboard.py
------------------------
Unit tests for the parsing logic. Run with: python -m pytest test_update_dashboard.py

These tests cover the part of the script that's most likely to break:
the translation from ESPN's event JSON to our dashboard's game dict.
The HTTP calls themselves aren't tested — those are integration concerns
better verified by a manual workflow_dispatch run on GitHub Actions.
"""

from datetime import datetime, timedelta, timezone

from update_dashboard import (
    build_schedule_block,
    league_display_name,
    parse_espn_event,
)


# ─── Fixtures ────────────────────────────────────────────────────────────────

LAKERS_CONFIG = {
    "label": "LAL",
    "badge": "badge-lakers",
    "sport": "basketball",
    "league": "nba",
    "espn_id": "13",
    "pro": True,
}

NOW = datetime(2026, 5, 17, 18, 0, tzinfo=timezone.utc)
HORIZON = NOW + timedelta(days=7)


def make_event(
    *,
    date_iso="2026-05-19T02:30Z",
    venue="Crypto.com Arena",
    home_id="13",
    home_name="Los Angeles Lakers",
    home_short="Lakers",
    away_id="2",
    away_name="Boston Celtics",
    away_short="Celtics",
    home_score=None,
    away_score=None,
    status_state="pre",
    broadcast="ESPN",
):
    """Build a minimal ESPN event JSON for testing."""
    competitors = [
        {
            "id": home_id,
            "homeAway": "home",
            "team": {"displayName": home_name, "shortDisplayName": home_short},
        },
        {
            "id": away_id,
            "homeAway": "away",
            "team": {"displayName": away_name, "shortDisplayName": away_short},
        },
    ]
    if home_score is not None:
        competitors[0]["score"] = home_score
        competitors[1]["score"] = away_score

    return {
        "date": date_iso,
        "status": {"type": {"state": status_state}},
        "competitions": [{
            "venue": {"fullName": venue},
            "broadcasts": [{"names": [broadcast]}] if broadcast else [],
            "competitors": competitors,
        }],
    }


# ─── parse_espn_event ─────────────────────────────────────────────────────────

def test_home_game_formats_as_vs():
    event = make_event(home_id="13", away_name="Boston Celtics", away_short="Celtics")
    result = parse_espn_event(event, "lakers", LAKERS_CONFIG, NOW, HORIZON)
    assert result is not None
    assert result["title"] == "Lakers vs Boston Celtics"
    assert result["home"] is True


def test_away_game_formats_as_at():
    event = make_event(
        home_id="2", home_name="Boston Celtics", home_short="Celtics",
        away_id="13", away_name="Los Angeles Lakers", away_short="Lakers",
    )
    result = parse_espn_event(event, "lakers", LAKERS_CONFIG, NOW, HORIZON)
    assert result is not None
    assert result["title"] == "Lakers at Boston Celtics"
    assert result["home"] is False


def test_completed_game_includes_score():
    event = make_event(
        date_iso="2026-05-17T02:30Z",
        home_score="110", away_score="105",
        status_state="post",
    )
    result = parse_espn_event(event, "lakers", LAKERS_CONFIG, NOW, HORIZON)
    assert result is not None
    assert "Final" in result["time"]
    assert "W 110-105" in result["note"]


def test_game_outside_horizon_is_skipped():
    far_future = (NOW + timedelta(days=30)).isoformat().replace("+00:00", "Z")
    event = make_event(date_iso=far_future)
    result = parse_espn_event(event, "lakers", LAKERS_CONFIG, NOW, HORIZON)
    assert result is None


def test_meta_line_includes_league_and_venue():
    event = make_event(venue="Crypto.com Arena")
    result = parse_espn_event(event, "lakers", LAKERS_CONFIG, NOW, HORIZON)
    assert "NBA" in result["meta"]
    assert "Home" in result["meta"]
    assert "Crypto.com Arena" in result["meta"]


def test_missing_broadcast_doesnt_crash():
    event = make_event(broadcast=None)
    result = parse_espn_event(event, "lakers", LAKERS_CONFIG, NOW, HORIZON)
    assert result is not None
    assert result["tv"] == ""


# ─── league_display_name ──────────────────────────────────────────────────────

def test_known_leagues_get_friendly_names():
    assert league_display_name("nba") == "NBA"
    assert league_display_name("esp.1") == "La Liga"
    assert league_display_name("usa.nwsl") == "NWSL"


def test_unknown_league_falls_back_to_code():
    assert league_display_name("xyz.99") == "xyz.99"


# ─── build_schedule_block ─────────────────────────────────────────────────────

def test_schedule_block_contains_markers():
    block = build_schedule_block([])
    assert "BEGIN AUTO-GENERATED SCHEDULE" in block
    assert "END AUTO-GENERATED SCHEDULE" in block
    assert "const SCHEDULE = []" in block
    assert "const LAST_UPDATED" in block


def test_schedule_block_serializes_unicode():
    games = [{"team": "rma", "title": "Real Madrid vs Atlético", "meta": "La Liga · Home"}]
    block = build_schedule_block(games)
    assert "Atlético" in block
    assert "·" in block
