import pytest

from core.game_engine import (
    RANKS,
    calculate_mission_rewards,
    get_adaptive_difficulty,
    get_next_rank,
    get_player_rank,
    get_progress_summary,
    get_unlocked_rewards,
)


def test_new_player_starts_as_rookie():
    assert get_player_rank(0).name == "Rookie Builder"


def test_player_levels_up_at_500_xp():
    assert get_player_rank(500).name == "Urban Explorer"


def test_next_rank_is_returned():
    assert get_next_rank(200).name == "Urban Explorer"


def test_final_rank_has_no_next_rank():
    assert get_next_rank(3500) is None


def test_perfect_mission_awards_500_xp_and_three_stars():
    result = calculate_mission_rewards(
        legal=True,
        within_time=True,
        all_violations_resolved=True,
        evidence_inspected=True,
        design_optimized=True,
    )

    assert result.xp == 500
    assert result.stars == 3
    assert result.completed is True


def test_illegal_design_does_not_complete_mission():
    result = calculate_mission_rewards(
        legal=False,
        within_time=True,
        all_violations_resolved=False,
        evidence_inspected=True,
        design_optimized=False,
    )

    assert result.completed is False
    assert result.stars == 1


def test_legal_mission_without_time_bonus_gets_two_stars():
    result = calculate_mission_rewards(
        legal=True,
        within_time=False,
        all_violations_resolved=True,
        evidence_inspected=True,
        design_optimized=True,
    )

    assert result.stars == 2


def test_three_successes_increase_difficulty():
    assert get_adaptive_difficulty(
        2, [True, True, True]
    ) == 3


def test_two_successes_increase_difficulty():
    assert get_adaptive_difficulty(
        2, [True, False, True]
    ) == 3


def test_repeated_failures_reduce_difficulty():
    assert get_adaptive_difficulty(
        3, [False, False, True]
    ) == 2


def test_difficulty_never_exceeds_five():
    assert get_adaptive_difficulty(
        5, [True, True, True]
    ) == 5


def test_difficulty_never_falls_below_one():
    assert get_adaptive_difficulty(
        1, [False, False, False]
    ) == 1


def test_adaptive_difficulty_waits_for_three_missions():
    assert get_adaptive_difficulty(
        2, [True, True]
    ) == 2


def test_progress_summary():
    summary = get_progress_summary(250)

    assert summary["rank"] == "Rookie Builder"
    assert summary["next_rank"] == "Urban Explorer"
    assert summary["xp_to_next_rank"] == 250
    assert summary["progress"] == 0.5


def test_all_rewards_unlock_at_final_rank():
    assert get_unlocked_rewards(3500) == [
        rank.reward for rank in RANKS
    ]


def test_negative_xp_is_rejected():
    with pytest.raises(ValueError):
        get_player_rank(-1)


def test_invalid_difficulty_is_rejected():
    with pytest.raises(ValueError):
        get_adaptive_difficulty(6, [True, True, True])