
import time
import os
import tempfile
import streamlit as st

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from core.regulation_pipeline import run_regulation_pipeline
from core.meta_client import MetaAPIError
from core.mission_timing import get_mission_time_limit, is_timed_mode, format_clock

from visualization.scene_3d import build_3d_model
from visualization.city_world import build_city_world, DISTRICTS


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="CODECRAFT 3D",
    page_icon="🏙️",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# GAME CONFIGURATION
# ============================================================

COMPETITIVE_DURATION_SECONDS = 5 * 60

SITE_WIDTH = 40.0
SITE_DEPTH = 60.0

FRONT_SETBACK = 10.0
OTHER_SETBACK = 5.0
MAX_HEIGHT = 45.0
MAX_COVERAGE = 50.0

TOTAL_SITE_AREA = SITE_WIDTH * SITE_DEPTH

RANKS = [
    {"name": "Rookie Builder", "threshold": 0, "reward": "Starter District"},
    {"name": "Urban Explorer", "threshold": 500, "reward": "New Building Skin"},
    {"name": "City Planner", "threshold": 1200, "reward": "New District"},
    {"name": "Master Architect", "threshold": 2200, "reward": "Premium City Theme"},
    {"name": "City Guardian", "threshold": 3500, "reward": "Elite Missions"},
]


# ============================================================
# SESSION STATE
# ============================================================

DEFAULTS = {
    "quest_deadline": None,
    "quest_started_at": None,
    "quest_status": "ready",
    "quest_score": 0,

    "total_xp": 0,
    "total_stars": 0,
    "completed_missions": 0,

    "mission_history": [],
    "claimed_missions": [],

    "mission_attempt": 0,
    "difficulty": 1,

    "game_mode": "Campaign",
    "selected_district": "Starter District",

    "evidence_inspected": False,
    "design_optimized": False,

    "oracle_question": "",
    "oracle_answer": None,

    # Explicitly human-approved constraints for demo simulation only.
    "approved_demo_constraints": {},

    "last_reward": None,
    "last_level_up": None,
}

for key, value in DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = value


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def get_rank(xp):
    current = RANKS[0]

    for rank in RANKS:
        if xp >= rank["threshold"]:
            current = rank

    return current


def get_next_rank(xp):
    for rank in RANKS:
        if xp < rank["threshold"]:
            return rank

    return None


def get_rank_progress(xp):
    current = get_rank(xp)
    next_rank = get_next_rank(xp)

    if next_rank is None:
        return 1.0

    required = next_rank["threshold"] - current["threshold"]
    earned = xp - current["threshold"]

    return max(0.0, min(1.0, earned / required))


def get_selected_district():
    for district in DISTRICTS:
        if district["name"] == st.session_state.selected_district:
            return district

    return DISTRICTS[0]


def get_mission_id():
    return (
        f"{st.session_state.game_mode}:"
        f"{st.session_state.selected_district}:"
        f"{st.session_state.mission_attempt}"
    )


def calculate_mission_reward(
    legal,
    completed_in_time,
    evidence_inspected,
    design_optimized,
):
    if not legal:
        return {
            "completed": False,
            "xp": 0,
            "stars": 0,
        }

    xp = 200
    xp += 100

    if completed_in_time:
        xp += 100

    if evidence_inspected:
        xp += 50

    if design_optimized:
        xp += 50

    stars = 3 if completed_in_time else 2

    return {
        "completed": True,
        "xp": xp,
        "stars": stars,
    }


def update_difficulty():
    history = st.session_state.mission_history

    if len(history) < 3:
        return

    last_three = history[-3:]

    successes = sum(
        1 for item in last_three
        if item["completed"]
    )

    if successes >= 2:
        st.session_state.difficulty = min(
            5,
            st.session_state.difficulty + 1,
        )
    else:
        st.session_state.difficulty = max(
            1,
            st.session_state.difficulty - 1,
        )


def reset_quest():
    st.session_state.quest_deadline = None
    st.session_state.quest_started_at = None
    st.session_state.quest_status = "ready"
    st.session_state.quest_score = 0

    st.session_state.evidence_inspected = False
    st.session_state.design_optimized = False

    st.session_state.last_reward = None


def start_quest():
    reset_quest()

    st.session_state.mission_attempt += 1

    now = time.time()

    st.session_state.quest_started_at = now
    time_limit = get_mission_time_limit(st.session_state.game_mode)
    st.session_state.quest_deadline = now + time_limit if time_limit is not None else None
    st.session_state.quest_status = "active"


def record_failed_attempt():
    if st.session_state.quest_status != "active":
        return
    if not is_timed_mode(st.session_state.game_mode):
        return

    st.session_state.quest_status = "failed"

    st.session_state.mission_history.append({
        "completed": False,
        "xp": 0,
        "stars": 0,
        "district": st.session_state.selected_district,
        "mode": st.session_state.game_mode,
    })

    update_difficulty()


def complete_mission(is_legal):
    if st.session_state.quest_status != "active":
        return

    if not is_legal:
        return

    mission_id = get_mission_id()

    if mission_id in st.session_state.claimed_missions:
        return

    now = time.time()

    # Campaign is untimed: no speed bonus is awarded or withheld.
    # Competitive missions receive the speed bonus only when completed in time.
    completed_in_time = (
        is_timed_mode(st.session_state.game_mode)
        and st.session_state.quest_deadline is not None
        and now <= st.session_state.quest_deadline
    )

    reward = calculate_mission_reward(
        legal=is_legal,
        completed_in_time=completed_in_time,
        evidence_inspected=st.session_state.evidence_inspected,
        design_optimized=st.session_state.design_optimized,
    )

    previous_rank = get_rank(st.session_state.total_xp)

    st.session_state.total_xp += reward["xp"]
    st.session_state.total_stars += reward["stars"]
    st.session_state.completed_missions += 1

    st.session_state.quest_score = reward["xp"]
    st.session_state.quest_status = "won"

    st.session_state.claimed_missions.append(mission_id)

    st.session_state.mission_history.append({
        "completed": True,
        "xp": reward["xp"],
        "stars": reward["stars"],
        "district": st.session_state.selected_district,
        "mode": st.session_state.game_mode,
    })

    update_difficulty()

    new_rank = get_rank(st.session_state.total_xp)

    if new_rank["name"] != previous_rank["name"]:
        st.session_state.last_level_up = new_rank

    st.session_state.last_reward = reward


# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown(
    """
    <style>

    .stApp {
        background:
            radial-gradient(
                circle at 80% 10%,
                rgba(95, 79, 190, 0.20),
                transparent 30%
            ),
            linear-gradient(
                135deg,
                #080d1c 0%,
                #101a31 55%,
                #17142d 100%
            );
        color: #F3F5FF;
    }

    [data-testid="stSidebar"] {
        background: #0D1528;
        border-right: 1px solid rgba(140, 165, 255, 0.15);
    }

    .main-title {
        font-size: 46px;
        font-weight: 900;
        letter-spacing: 3px;
        color: #B8C8FF;
        margin-bottom: 0;
        text-shadow: 0 0 22px rgba(120, 145, 255, 0.35);
    }

    .subtitle {
        color: #AEBFE8;
        font-size: 15px;
        letter-spacing: 2px;
        margin-top: 5px;
    }

    .game-card {
        background: rgba(32, 46, 78, 0.68);
        border: 1px solid rgba(155, 180, 255, 0.20);
        padding: 18px;
        border-radius: 16px;
    }

    .small-label {
        color: #B7C6E5;
        font-size: 12px;
        letter-spacing: 1px;
    }

    div.stButton > button {
        border-radius: 10px;
        border: 1px solid rgba(160, 180, 255, 0.35);
        background: linear-gradient(100deg, #536FE2, #8766DB);
        color: white;
        font-weight: 700;
    }

    div.stButton > button:hover {
        border-color: #B9C9FF;
        color: white;
        box-shadow: 0 0 18px rgba(120, 140, 255, 0.30);
    }

    [data-testid="stMetricLabel"] {
        color: #AFC1E8 !important;
    }

    [data-testid="stMetricValue"] {
        color: #F4F6FF !important;
    }

    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] span {
        color: #D1DCF5 !important;
    }

    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3 {
        color: #C0D0FF !important;
    }


    /* Accessible, consistent controls: high contrast in every state. */
    div.stButton > button {
        min-height: 46px;
        padding: 0.62rem 1rem;
        border-radius: 11px;
        font-size: 0.96rem;
        font-weight: 800 !important;
        letter-spacing: 0.01em;
        color: #FFFFFF !important;
        background: linear-gradient(100deg, #405FCB, #7052C7) !important;
        border: 1px solid #AFC2FF !important;
        opacity: 1 !important;
        white-space: normal !important;
        line-height: 1.25 !important;
        box-shadow: 0 2px 10px rgba(0,0,0,0.22);
    }
    div.stButton > button p, div.stButton > button span {
        color: #FFFFFF !important;
        font-weight: 800 !important;
    }
    div.stButton > button:hover:not(:disabled) {
        background: linear-gradient(100deg, #5878EA, #896BE0) !important;
        border-color: #FFFFFF !important;
        transform: translateY(-1px);
        box-shadow: 0 0 0 2px rgba(190,205,255,0.22), 0 8px 18px rgba(0,0,0,0.24);
    }
    div.stButton > button:focus-visible {
        outline: 3px solid #F5D76E !important;
        outline-offset: 3px !important;
    }
    div.stButton > button:disabled {
        color: #E5EAF7 !important;
        background: #35415C !important;
        border: 1px solid #7F8EAD !important;
        opacity: 1 !important;
        cursor: not-allowed !important;
        filter: none !important;
    }
    div.stButton > button:disabled p, div.stButton > button:disabled span {
        color: #E5EAF7 !important;
        opacity: 1 !important;
    }
    [data-testid="stFileUploader"] button {
        color: #18233D !important;
        background: #F2F5FF !important;
        border: 1px solid #AAB8D8 !important;
        font-weight: 800 !important;
    }
    [data-testid="stFileUploader"] button p, [data-testid="stFileUploader"] button span {
        color: #18233D !important;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# HEADER
# ============================================================

header_left, header_right = st.columns([3, 1])

with header_left:
    st.markdown(
        '<div class="main-title">CODECRAFT 3D</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="subtitle">'
        'DECODE. DESIGN. DEFY THE IMPOSSIBLE.'
        '</div>',
        unsafe_allow_html=True,
    )

with header_right:
    st.markdown(
        """
        <div style="text-align:right; padding-top:15px;">
            <span style="color:#9eafff; font-size:13px;">
                CITY RESCUE PROTOCOL
            </span>
            <br>
            <span style="color:#66e6c2; font-weight:800;">
                ● SYSTEM ONLINE
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.caption(
    "A futuristic city-building adventure powered by "
    "geometry validation and regulation intelligence."
)


# ============================================================
# PLAYER COMMAND CENTER
# ============================================================

player_xp = st.session_state.total_xp
player_rank = get_rank(player_xp)
next_rank = get_next_rank(player_xp)

st.divider()
st.subheader("👤 PLAYER COMMAND CENTER")

hud1, hud2, hud3, hud4 = st.columns(4)

hud1.metric("PLAYER RANK", player_rank["name"])
hud2.metric("TOTAL XP", f"{player_xp:,}")
hud3.metric("MISSIONS COMPLETED", st.session_state.completed_missions)
hud4.metric("TOTAL STARS", st.session_state.total_stars)

if next_rank:
    st.progress(get_rank_progress(player_xp))

    st.caption(
        f"Next rank: {next_rank['name']} · "
        f"{next_rank['threshold'] - player_xp} XP remaining"
    )
else:
    st.success("Maximum player rank achieved: City Guardian.")

st.caption(f"Current reward: {player_rank['reward']}")

if st.session_state.last_level_up:
    st.success(
        f"🎉 RANK UNLOCKED: "
        f"{st.session_state.last_level_up['name']}!"
    )


# ============================================================
# GAME MODE
# ============================================================

st.divider()
st.subheader("🎮 SELECT GAME MODE")

mode1, mode2 = st.columns(2)

mode_locked = st.session_state.quest_status == "active"

with mode1:
    if st.button(
        "🌆 CAMPAIGN MODE · SELECTED" if st.session_state.game_mode == "Campaign" else "🌆 CAMPAIGN MODE",
        width="stretch",
        type="primary" if st.session_state.game_mode == "Campaign" else "secondary",
        disabled=mode_locked,
        key="select_campaign_mode",
    ):
        st.session_state.game_mode = "Campaign"
        st.rerun()

with mode2:
    if st.button(
        "⚡ COMPETITIVE CHALLENGES · SELECTED" if st.session_state.game_mode == "Competitive" else "⚡ COMPETITIVE CHALLENGES",
        width="stretch",
        type="primary" if st.session_state.game_mode == "Competitive" else "secondary",
        disabled=mode_locked,
        key="select_competitive_mode",
    ):
        st.session_state.game_mode = "Competitive"
        st.rerun()

if mode_locked:
    st.caption("Finish or reset the current mission before changing game mode.")

st.caption(f"ACTIVE MODE: {st.session_state.game_mode.upper()}")

if st.session_state.game_mode == "Competitive":
    st.info(
        "Competitive mode currently records local challenge results. "
        "Online multiplayer and global leaderboards are not connected."
    )


# ============================================================
# CITY WORLD
# ============================================================

st.divider()
st.subheader("🌐 CITY WORLD")

st.write(
    "Explore the city, unlock districts and build its future."
)

city_fig = build_city_world(
    player_xp=st.session_state.total_xp,
    selected_district=st.session_state.selected_district,
)

st.plotly_chart(
    city_fig,
    width="stretch",
    key="city_world_map",
    config={
        "displayModeBar": False,
        "scrollZoom": False,
    },
)

st.markdown("### 🗺️ SELECT YOUR DISTRICT")

district_columns = st.columns(3)

for index, district in enumerate(DISTRICTS):

    unlocked = (
        st.session_state.total_xp >= district["required_xp"]
    )

    selected = (
        st.session_state.selected_district == district["name"]
    )

    with district_columns[index % 3]:

        if unlocked:

            label = (
                f"🟢 {district['name']} · SELECTED"
                if selected
                else f"🏙️ {district['name']}"
            )

            if st.button(
                label,
                key=f"district_{index}",
                width="stretch",
            ):
                st.session_state.selected_district = district["name"]
                st.rerun()

        else:
            st.button(
                f"🔒 {district['name']} · {district['required_xp']} XP",
                key=f"locked_district_{index}",
                disabled=True,
                width="stretch",
            )

selected_district = get_selected_district()

st.info(
    f"CURRENT DISTRICT: {selected_district['name']}"
)


# ============================================================
# SIDEBAR — BUILDING CONTROLS
# ============================================================

st.sidebar.title("🏙️ CITY GRID")
st.sidebar.caption("BUILDING DESIGN CONTROL")

st.sidebar.divider()
st.sidebar.subheader("Site parameters")

st.sidebar.write("Site: 40 × 60 ft")
st.sidebar.write("Front setback: 10 ft")
st.sidebar.write("Other setbacks: 5 ft")
st.sidebar.write("Illustrative maximum height: 45 ft")
st.sidebar.write("Illustrative maximum coverage: 50%")
if st.session_state.get("approved_demo_constraints"):
    st.sidebar.caption("Approved document candidates are active in the demo geometry.")

st.sidebar.divider()
st.sidebar.subheader("Design your building")

building_width = st.sidebar.slider(
    "Building width (ft)", 1, 40, 30
)

building_depth = st.sidebar.slider(
    "Building depth (ft)", 1, 60, 35
)

building_height = st.sidebar.slider(
    "Building height (ft)", 1, 80, 50
)

building_x = st.sidebar.slider(
    "Horizontal position (ft)", 0, 40, 5
)

building_y = st.sidebar.slider(
    "Depth position (ft)", 0, 60, 10
)

st.sidebar.divider()
st.sidebar.subheader("Mission difficulty")

st.sidebar.metric(
    "ADAPTIVE DIFFICULTY",
    f"LEVEL {st.session_state.difficulty}/5",
)

st.sidebar.caption(
    "Difficulty changes after every three attempts. "
    "Legal geometry constraints remain unchanged."
)


# ============================================================
# GEOMETRY ENGINE
# ============================================================

# The existing CITY GRID uses feet. Extracted metric constraints are converted
# only after an explicit human approval for this illustrative demo.
METRES_TO_FEET = 3.280839895
approved_demo = st.session_state.get("approved_demo_constraints", {})
active_front_setback = FRONT_SETBACK
active_rear_setback = OTHER_SETBACK
active_left_setback = OTHER_SETBACK
active_right_setback = OTHER_SETBACK
active_max_height = MAX_HEIGHT
active_max_coverage = MAX_COVERAGE

for constraint_type, item in approved_demo.items():
    try:
        value = float(item["value"])
        unit = str(item.get("unit") or "").strip().lower()
    except (TypeError, ValueError, KeyError):
        continue

    if constraint_type in {"front_setback", "rear_setback", "left_setback", "right_setback", "max_height"}:
        if unit in {"m", "meter", "meters", "metre", "metres"}:
            value *= METRES_TO_FEET
        elif unit not in {"ft", "feet", "foot"}:
            continue

    if constraint_type == "front_setback":
        active_front_setback = value
    elif constraint_type == "rear_setback":
        active_rear_setback = value
    elif constraint_type == "left_setback":
        active_left_setback = value
    elif constraint_type == "right_setback":
        active_right_setback = value
    elif constraint_type == "max_height":
        active_max_height = value
    elif constraint_type == "max_site_coverage" and unit in {"%", "percent", "percentage"}:
        active_max_coverage = value

fig, result = build_3d_model(
    site_width=SITE_WIDTH,
    site_depth=SITE_DEPTH,
    front_setback=active_front_setback,
    rear_setback=active_rear_setback,
    left_setback=active_left_setback,
    right_setback=active_right_setback,
    max_height=active_max_height,
    max_coverage_percent=active_max_coverage,
    building_width=building_width,
    building_depth=building_depth,
    building_height=building_height,
    building_x=building_x,
    building_y=building_y,
)


# ============================================================
# 3D BUILDING VISUAL THEME
# ============================================================

fig.update_layout(
    paper_bgcolor="#0B1224",
    plot_bgcolor="#0B1224",
    font=dict(
        color="#E7EDFF",
        family="Arial",
    ),
    title_font=dict(color="#B8C8FF"),
    legend=dict(
        bgcolor="rgba(11,18,36,0.75)",
        font=dict(color="#E7EDFF"),
    ),
)

if hasattr(fig.layout, "scene") and fig.layout.scene is not None:
    fig.update_layout(
        scene=dict(
            bgcolor="#0B1224",
            xaxis=dict(
                backgroundcolor="#0B1224",
                gridcolor="#263552",
                zerolinecolor="#536C9C",
                color="#C4D2F2",
            ),
            yaxis=dict(
                backgroundcolor="#0B1224",
                gridcolor="#263552",
                zerolinecolor="#536C9C",
                color="#C4D2F2",
            ),
            zaxis=dict(
                backgroundcolor="#0B1224",
                gridcolor="#263552",
                zerolinecolor="#536C9C",
                color="#C4D2F2",
            ),
        )
    )


# ============================================================
# MISSION BRIEFING
# ============================================================

st.divider()
st.subheader(f"📜 {selected_district['mission']}")

briefing1, briefing2 = st.columns([2, 1])

with briefing1:
    st.markdown(
        f"""
        <div class="game-card">
            <h3 style="color:#B9CAFF;">
                THE CITY NEEDS YOU.
            </h3>
            <p style="color:#D1DCF5;">
                {selected_district['description']}
                Investigate the challenge rules, redesign the
                building and restore the district.
            </p>
            <p style="color:#8FA9E8;">
                OBJECTIVE: Resolve every geometry violation.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

with briefing2:
    if is_timed_mode(st.session_state.game_mode):
        st.metric("TIME LIMIT", "05:00")
        st.caption("Competitive missions are strict timed challenges.")
    else:
        st.metric("MISSION TIME", "UNTIMED")
        st.caption("Explore, design and experiment at your own pace.")
    st.metric("MAXIMUM REWARD", "500 XP")


# ============================================================
# OPTIONAL OBJECTIVES
# ============================================================

st.subheader("🔍 OPTIONAL MISSION OBJECTIVES")

objective1, objective2 = st.columns(2)

with objective1:
    st.checkbox(
        "I inspected the available evidence",
        key="evidence_inspected",
        disabled=st.session_state.quest_status != "active",
    )

with objective2:
    st.checkbox(
        "I optimized my building design",
        key="design_optimized",
        disabled=st.session_state.quest_status != "active",
    )

st.caption(
    "These are player-confirmed demo objectives, not yet "
    "independently verified evidence actions."
)


# ============================================================
# QUEST TIMER CONTROLS
# ============================================================

st.divider()
st.subheader("⏱️ MISSION CONTROL")

timer_col, start_col, reset_col = st.columns([2, 1, 1])

with timer_col:

    if st.session_state.quest_status == "active":
        st.info("Mission active. Resolve all violations!")

    elif st.session_state.quest_status == "won":
        st.success("Mission successfully completed.")

    elif st.session_state.quest_status == "failed":
        st.error("Mission time expired.")

    else:
        st.info("Campaign: take your time. Competitive: complete the challenge within 5 minutes. Start when you are ready.")

with start_col:

    if st.button(
        "▶ Start Quest",
        width="stretch",
        disabled=st.session_state.quest_status == "active",
    ):
        start_quest()
        st.rerun()

with reset_col:

    if st.button("↻ Reset", width="stretch"):
        reset_quest()
        st.rerun()


# ============================================================
# TIMER
# ============================================================

@st.fragment(run_every="1s")
def render_timer():
    if st.session_state.quest_status != "active":
        return

    if not is_timed_mode(st.session_state.game_mode):
        elapsed = max(0, int(time.time() - st.session_state.quest_started_at))
        st.success("Campaign mission active · No countdown. Build at your own pace.")
        st.metric("TIME ELAPSED", format_clock(elapsed))
        return

    deadline = st.session_state.quest_deadline
    remaining = max(0, int(deadline - time.time()) + 1) if deadline else 0

    if remaining <= 0:
        record_failed_attempt()
        st.error("TIME'S UP! Competitive attempt recorded as failed. You can retry.")
        st.rerun(scope="app")
        return

    st.progress(remaining / COMPETITIVE_DURATION_SECONDS)
    st.metric("COMPETITIVE TIME REMAINING", format_clock(remaining))


render_timer()


# ============================================================
# MISSION COMPLETION
# ============================================================

if (
    st.session_state.quest_status == "active"
    and result.is_valid
):

    st.success(
        "All geometry checks passed. "
        "You can complete this mission."
    )

    if st.button(
        "🏆 COMPLETE MISSION",
        key="complete_mission",
        width="stretch",
    ):

        complete_mission(result.is_valid)

        st.balloons()
        st.rerun()


# ============================================================
# MISSION RESULTS
# ============================================================

if st.session_state.quest_status == "won":

    st.divider()
    st.subheader("🏆 MISSION VICTORY")

    reward = st.session_state.last_reward

    if reward:

        result1, result2, result3 = st.columns(3)

        result1.metric("XP EARNED", f"+{reward['xp']}")
        result2.metric("STARS EARNED", "⭐" * reward["stars"])
        result3.metric("TOTAL XP", f"{st.session_state.total_xp:,}")

        st.success(
            f"{selected_district['name']} mission completed!"
        )

elif st.session_state.quest_status == "failed":

    st.error(
        "COMPETITIVE ATTEMPT EXPIRED — Reset and try again."
    )


# ============================================================
# LIVE BUILDING ANALYTICS
# ============================================================

st.divider()
st.subheader("📊 LIVE BUILDING ANALYTICS")

metric1, metric2, metric3, metric4 = st.columns(4)

metric1.metric(
    "BUILDING STATUS",
    "WITHIN DEMO RULES" if result.is_valid else "DEMO RULES FAILED",
)

metric2.metric(
    "VIOLATIONS",
    len(result.violations),
)

metric3.metric(
    "QUEST SCORE",
    st.session_state.quest_score,
)

metric4.metric(
    "DIFFICULTY",
    f"{st.session_state.difficulty}/5",
)


# ============================================================
# 3D BUILDING GRID
# ============================================================

st.divider()
st.subheader("🌐 YOUR 3D BUILDING DESIGN")

left, right = st.columns([3, 1])

with left:

    st.plotly_chart(
        fig,
        width="stretch",
        key="city_grid",
    )

with right:

    st.subheader("MISSION STATUS")

    if result.is_valid:
        st.success("All illustrative geometry checks passed.")
    else:
        st.error("Illustrative geometry violations detected.")

    if result.violations:

        st.write("**Detected violations:**")

        for violation in result.violations:
            st.write(f"🔴 {violation}")

    st.caption(
        "Red/green validation comes from the deterministic "
        "geometry engine."
    )


# ============================================================
# REGULATION ORACLE — SIMULATED DEMO
# ============================================================

st.divider()
st.subheader("🔮 REGULATION ORACLE")

st.warning(
    "DEMO MODE — Responses below are illustrative, "
    "not live AI findings or verified legal citations."
)

question = st.text_input(
    "Ask the Oracle",
    placeholder="Example: What is the maximum building height?",
    key="oracle_question",
)

if st.button("🔍 Investigate", key="oracle_button"):

    normalized = question.lower().strip()

    if "height" in normalized:

        answer = (
            f"Illustrative challenge rule: maximum height is "
            f"{MAX_HEIGHT:.0f} ft. Current building height is "
            f"{building_height} ft."
        )

    elif "setback" in normalized:

        answer = (
            f"Illustrative challenge rule: front setback is "
            f"{FRONT_SETBACK:.0f} ft. Building front position is "
            f"{building_y} ft."
        )

    elif "coverage" in normalized:

        footprint = building_width * building_depth

        coverage = footprint / TOTAL_SITE_AREA * 100

        answer = (
            f"Illustrative challenge rule: maximum coverage is "
            f"{MAX_COVERAGE:.0f}%. Your proposed footprint is "
            f"{footprint:.1f} sq ft, representing "
            f"{coverage:.2f}% of the site."
        )

    else:

        answer = (
            "The simulated Oracle could not identify a matching "
            "challenge rule. Try height, setback or coverage."
        )

    st.session_state.oracle_answer = answer

if st.session_state.oracle_answer:
    st.info(st.session_state.oracle_answer)


# ============================================================
# REGULATION INTELLIGENCE — MUSE SPARK + EVIDENCE CHECKS
# ============================================================

st.divider()
st.subheader("📄 REGULATION INTELLIGENCE ENGINE")
st.caption(
    "Upload a text-based regulation PDF. Muse Spark extracts candidate rules; "
    "CODECRAFT checks source traceability before anything can be considered for review."
)

if "regulation_analysis" not in st.session_state:
    st.session_state.regulation_analysis = None

api_key_configured = bool(os.getenv("MODEL_API_KEY"))
if not api_key_configured:
    st.warning(
        "Meta API is not configured yet. Add MODEL_API_KEY to a local .env file "
        "in the project root, then restart Streamlit. Do not paste the key into this app or chat."
    )

uploaded_regulation = st.file_uploader(
    "Upload a building regulation PDF",
    type=["pdf"],
    key="regulation_pdf_upload",
    help="Text-based PDFs are supported in this first version. Scanned/image-only PDFs need OCR."
)

run_extraction = st.button(
    "🧠 Analyse with Muse Spark",
    key="run_regulation_analysis",
    disabled=(uploaded_regulation is None or not api_key_configured),
    width="stretch",
)

if run_extraction and uploaded_regulation is not None:
    if uploaded_regulation.size > 10 * 1024 * 1024:
        st.error("Please use a PDF smaller than 10 MB for this prototype.")
    else:
        temp_path = None
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
                temp_file.write(uploaded_regulation.getvalue())
                temp_path = temp_file.name
            with st.spinner("Extracting pages and asking Muse Spark to identify candidate constraints..."):
                # A newly analysed document invalidates approvals from the previous upload.
                st.session_state.approved_demo_constraints = {}
                for state_key in list(st.session_state.keys()):
                    if state_key.startswith("approve_demo_constraint_"):
                        del st.session_state[state_key]
                st.session_state.regulation_analysis = run_regulation_pipeline(temp_path)
                st.session_state.regulation_analysis["document"]["file_name"] = uploaded_regulation.name
            st.success("Analysis completed. Review each candidate below; none is automatically treated as legally verified.")
        except (MetaAPIError, ValueError) as exc:
            st.error(f"Regulation analysis could not be completed: {exc}")
        except Exception as exc:
            st.error(f"Unexpected analysis error: {exc}")
        finally:
            if temp_path and os.path.exists(temp_path):
                os.remove(temp_path)

analysis = st.session_state.regulation_analysis
if analysis:
    doc = analysis["document"]
    st.write(
        f"**Document:** {doc['file_name']} · **Pages:** {doc['page_count']} · "
        f"**Provider:** {analysis['provider']} · **Model:** {analysis['model']}"
    )
    st.warning(
        "DEMO SAFETY: Evidence checks confirm source traceability only. They do not "
        "confirm legal applicability or certify compliance. Approving a candidate "
        "below applies it only to this prototype's illustrative 3D simulation."
    )
    st.info(analysis["disclaimer"])

    candidates = analysis.get("constraints", [])
    eligible_candidate_indexes = []
    if not candidates:
        st.warning("No supported numeric constraints were extracted from this document.")
    for idx, candidate in enumerate(candidates, start=1):
        checks = candidate.get("evidence_check", {})
        with st.expander(
            f"Candidate {idx}: {candidate.get('constraint_type', 'unknown')} — "
            f"{candidate.get('status', 'unresolved').upper()}",
            expanded=True,
        ):
            st.write(
                f"**Value:** {candidate.get('value')} {candidate.get('unit') or ''} · "
                f"**Page:** {candidate.get('page_number')} · "
                f"**Clause:** {candidate.get('clause_reference') or 'Not supplied'}"
            )
            st.write("**Source excerpt:**")
            st.code(candidate.get("source_excerpt", "No excerpt returned"), language="text")
            if checks.get("passed"):
                st.success("Basic source traceability checks passed. Human review is still required.")
            else:
                st.error("Evidence checks failed: " + ", ".join(checks.get("issues", [])))

            constraint_type = candidate.get("constraint_type")
            unit = str(candidate.get("unit") or "").strip().lower()
            try:
                numeric_value = float(candidate.get("value"))
            except (TypeError, ValueError):
                numeric_value = None

            supported_units = {
                "front_setback": {"m", "meter", "meters", "metre", "metres", "ft", "feet", "foot"},
                "rear_setback": {"m", "meter", "meters", "metre", "metres", "ft", "feet", "foot"},
                "left_setback": {"m", "meter", "meters", "metre", "metres", "ft", "feet", "foot"},
                "right_setback": {"m", "meter", "meters", "metre", "metres", "ft", "feet", "foot"},
                "max_height": {"m", "meter", "meters", "metre", "metres", "ft", "feet", "foot"},
                "max_site_coverage": {"%", "percent", "percentage"},
            }
            eligible = (
                checks.get("passed") is True
                and constraint_type in supported_units
                and unit in supported_units.get(constraint_type, set())
                and numeric_value is not None
                and numeric_value > 0
            )
            if eligible:
                eligible_candidate_indexes.append(idx)
                st.checkbox(
                    "I reviewed this source and approve it for the demo 3D simulation",
                    key=f"approve_demo_constraint_{idx}",
                )
            else:
                st.caption(
                    "Not eligible for demo application: evidence must pass and the "
                    "constraint type/unit must be supported. Human review is still required."
                )
            st.caption("No candidate is applied unless you explicitly approve it below.")

    if eligible_candidate_indexes:
        if st.button("Apply selected approvals to demo geometry", key="apply_approved_demo_constraints", width="stretch"):
            newly_approved = {}
            for idx in eligible_candidate_indexes:
                candidate = candidates[idx - 1]
                if st.session_state.get(f"approve_demo_constraint_{idx}", False):
                    newly_approved[candidate["constraint_type"]] = {
                        "value": candidate["value"],
                        "unit": candidate.get("unit"),
                        "page_number": candidate.get("page_number"),
                        "source_excerpt": candidate.get("source_excerpt"),
                        "document_id": candidate.get("document_id"),
                    }
            if newly_approved:
                st.session_state.approved_demo_constraints.update(newly_approved)
                st.success("Approved constraints saved for the demo simulation. The 3D model will refresh now.")
                st.rerun()
            else:
                st.warning("Select at least one eligible candidate before applying approvals.")

    if st.session_state.get("approved_demo_constraints"):
        st.write("**Currently applied to demo geometry:**")
        for approved_type, approved_item in st.session_state.approved_demo_constraints.items():
            st.write(f"- {approved_type}: {approved_item['value']} {approved_item.get('unit') or ''}")
        if st.button("Restore illustrative default geometry rules", key="reset_demo_geometry_rules"):
            st.session_state.approved_demo_constraints = {}
            st.rerun()

    if analysis.get("ambiguities"):
        st.subheader("Ambiguities requiring review")
        for ambiguity in analysis["ambiguities"]:
            st.warning(str(ambiguity))

    with st.expander("View complete extraction result (JSON)"):
        st.json(analysis)


# ============================================================
# MISSION HISTORY
# ============================================================

st.divider()
st.subheader("📜 MISSION HISTORY")

if st.session_state.mission_history:

    for index, mission in enumerate(
        reversed(st.session_state.mission_history),
        start=1,
    ):

        status = (
            "COMPLETED"
            if mission["completed"]
            else "FAILED"
        )

        st.write(
            f"{index}. {mission['district']} · "
            f"{mission['mode']} · {status} · "
            f"{mission['xp']} XP · "
            f"{mission['stars']} Stars"
        )

else:

    st.caption("Your city-building journey starts here.")


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "CODECRAFT 3D | Prototype challenge environment | "
    "Illustrative values only — not legal certification."
)
