import pytest
from core.mission_timing import (
    COMPETITIVE_TIME_LIMIT_SECONDS,
    format_clock,
    get_mission_time_limit,
    is_timed_mode,
)

def test_campaign_is_untimed():
    assert get_mission_time_limit("Campaign") is None
    assert not is_timed_mode("Campaign")

def test_competitive_has_five_minute_limit():
    assert get_mission_time_limit("Competitive") == 300
    assert is_timed_mode("Competitive")

def test_mode_matching_is_case_insensitive():
    assert get_mission_time_limit("competitive") == 300

def test_unknown_mode_defaults_to_untimed():
    assert get_mission_time_limit("Practice") is None

def test_format_clock():
    assert format_clock(300) == "05:00"
    assert format_clock(65) == "01:05"
    assert format_clock(-2) == "00:00"
