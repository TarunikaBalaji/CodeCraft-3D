from __future__ import annotations

CAMPAIGN_TIME_LIMIT_SECONDS = None
COMPETITIVE_TIME_LIMIT_SECONDS = 5 * 60

def is_timed_mode(game_mode: str) -> bool:
    return game_mode.strip().lower() == "competitive"

def get_mission_time_limit(game_mode: str) -> int | None:
    """Campaign has no deadline; Competitive has a strict five-minute limit."""
    return COMPETITIVE_TIME_LIMIT_SECONDS if is_timed_mode(game_mode) else CAMPAIGN_TIME_LIMIT_SECONDS

def format_clock(seconds: int) -> str:
    seconds = max(0, int(seconds))
    minutes, remainder = divmod(seconds, 60)
    return f"{minutes:02d}:{remainder:02d}"
