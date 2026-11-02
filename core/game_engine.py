from dataclasses import dataclass
from typing import List, Optional, Dict, Any


# --------------------------------------------------
# PLAYER RANKS
# --------------------------------------------------

@dataclass(frozen=True)
class PlayerRank:
    name: str
    xp_required: int
    reward: str


RANKS = [
    PlayerRank("Rookie Builder", 0, "Starter District"),
    PlayerRank("Urban Explorer", 500, "New Building Skin"),
    PlayerRank("City Planner", 1200, "New District"),
    PlayerRank("Master Architect", 2200, "Premium City Theme"),
    PlayerRank("City Guardian", 3500, "Elite Missions"),
]


# --------------------------------------------------
# MISSION RESULT
# --------------------------------------------------

@dataclass
class MissionResult:
    xp: int
    stars: int
    completed: bool
    rewards: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "xp": self.xp,
            "stars": self.stars,
            "completed": self.completed,
            "rewards": list(self.rewards),
        }


# --------------------------------------------------
# PLAYER PROGRESSION
# --------------------------------------------------

def _validate_xp(total_xp: int) -> None:
    if isinstance(total_xp, bool) or not isinstance(total_xp, int):
        raise TypeError("XP must be an integer.")

    if total_xp < 0:
        raise ValueError("XP cannot be negative.")


def get_player_rank(total_xp: int) -> PlayerRank:
    """Return the highest rank unlocked by the player's XP."""

    _validate_xp(total_xp)

    current_rank = RANKS[0]

    for rank in RANKS:
        if total_xp >= rank.xp_required:
            current_rank = rank
        else:
            break

    return current_rank


def get_next_rank(total_xp: int) -> Optional[PlayerRank]:
    """Return the next rank, or None if all ranks are unlocked."""

    current_rank = get_player_rank(total_xp)
    current_index = RANKS.index(current_rank)

    if current_index == len(RANKS) - 1:
        return None

    return RANKS[current_index + 1]


def get_unlocked_rewards(total_xp: int) -> List[str]:
    """Return rewards unlocked at the player's current XP."""

    _validate_xp(total_xp)

    return [
        rank.reward
        for rank in RANKS
        if total_xp >= rank.xp_required
    ]


def get_progress_summary(total_xp: int) -> Dict[str, Any]:
    """Calculate rank progress and XP required for the next rank."""

    _validate_xp(total_xp)

    current_rank = get_player_rank(total_xp)
    next_rank = get_next_rank(total_xp)

    if next_rank is None:
        return {
            "rank": current_rank.name,
            "next_rank": None,
            "xp_to_next_rank": 0,
            "progress": 1.0,
            "total_xp": total_xp,
        }

    xp_in_rank = total_xp - current_rank.xp_required
    xp_needed = next_rank.xp_required - current_rank.xp_required

    return {
        "rank": current_rank.name,
        "next_rank": next_rank.name,
        "xp_to_next_rank": next_rank.xp_required - total_xp,
        "progress": xp_in_rank / xp_needed,
        "total_xp": total_xp,
    }


# --------------------------------------------------
# MISSION REWARDS
# --------------------------------------------------

def calculate_mission_rewards(
    legal: bool,
    within_time: bool,
    all_violations_resolved: bool,
    evidence_inspected: bool,
    design_optimized: bool,
) -> MissionResult:
    """
    Calculate XP and stars for a mission.

    XP:
        Legal design:              200
        Completed within time:     100
        All violations resolved:   100
        Evidence inspected:         50
        Design optimized:           50

    Maximum: 500 XP

    Stars:
        1 star: Mission attempted.
        2 stars: Legal design with all violations resolved.
        3 stars: Above conditions plus completion within time.
    """

    conditions = [
        legal,
        within_time,
        all_violations_resolved,
        evidence_inspected,
        design_optimized,
    ]

    if not all(isinstance(value, bool) for value in conditions):
        raise TypeError("Mission conditions must be boolean values.")

    xp = 0

    if legal:
        xp += 200

    if within_time:
        xp += 100

    if all_violations_resolved:
        xp += 100

    if evidence_inspected:
        xp += 50

    if design_optimized:
        xp += 50

    completed = legal and all_violations_resolved

    stars = 1

    if legal and all_violations_resolved:
        stars = 2

    if completed and within_time:
        stars = 3

    rewards = []

    if completed:
        rewards.append("Mission Completed")

    if stars == 3:
        rewards.append("Perfect Mission")

    if evidence_inspected:
        rewards.append("Evidence Explorer")

    if design_optimized:
        rewards.append("Design Optimizer")

    return MissionResult(
        xp=xp,
        stars=stars,
        completed=completed,
        rewards=rewards,
    )


# --------------------------------------------------
# ADAPTIVE DIFFICULTY
# --------------------------------------------------

def get_adaptive_difficulty(
    current_difficulty: int,
    recent_results: List[bool],
) -> int:
    """
    Adjust difficulty after at least three missions.

    2 or more successes out of the latest 3:
        Increase difficulty by one.

    1 or fewer successes:
        Decrease difficulty by one.

    Difficulty is always between 1 and 5.

    This changes challenge parameters only.
    It must never modify building regulations.
    """

    if (
        isinstance(current_difficulty, bool)
        or not isinstance(current_difficulty, int)
    ):
        raise TypeError("Difficulty must be an integer.")

    if not 1 <= current_difficulty <= 5:
        raise ValueError("Difficulty must be between 1 and 5.")

    if not isinstance(recent_results, list):
        raise TypeError("Recent results must be a list.")

    if not all(isinstance(result, bool) for result in recent_results):
        raise TypeError("Mission results must contain boolean values.")

    if len(recent_results) < 3:
        return current_difficulty

    latest_three = recent_results[-3:]
    successes = sum(latest_three)

    if successes >= 2:
        return min(5, current_difficulty + 1)

    return max(1, current_difficulty - 1)