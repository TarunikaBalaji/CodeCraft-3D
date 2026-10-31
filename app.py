
import time
import streamlit as st

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

QUEST_DURATION = 60

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
    st.session_state.quest_deadline = now + QUEST_DURATION
    st.session_state.quest_status = "active"


def record_failed_attempt():
    if st.session_state.quest_status != "active":
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

    completed_in_time = (
        now <= st.session_state.quest_deadline
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

with mode1:
    if st.button("🌆 CAMPAIGN MODE", width="stretch"):
        st.session_state.game_mode = "Campaign"
        st.rerun()

with mode2:
    if st.button("⚡ COMPETITIVE CHALLENGES", width="stretch"):
        st.session_state.game_mode = "Competitive"
        st.rerun()

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

fig, result = build_3d_model(
    site_width=SITE_WIDTH,
    site_depth=SITE_DEPTH,
    front_setback=FRONT_SETBACK,
    rear_setback=OTHER_SETBACK,
    left_setback=OTHER_SETBACK,
    right_setback=OTHER_SETBACK,
    max_height=MAX_HEIGHT,
    max_coverage_percent=MAX_COVERAGE,
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
    st.metric("MISSION TIME", f"{QUEST_DURATION} SECONDS")
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
st.subheader("⏱️ 60-SECOND BUILDING CHALLENGE")

timer_col, start_col, reset_col = st.columns([2, 1, 1])

with timer_col:

    if st.session_state.quest_status == "active":
        st.info("Mission active. Resolve all violations!")

    elif st.session_state.quest_status == "won":
        st.success("Mission successfully completed.")

    elif st.session_state.quest_status == "failed":
        st.error("Mission time expired.")

    else:
        st.info("Prepare your design, then start the mission.")

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

    deadline = st.session_state.quest_deadline

    remaining = max(
        0,
        int(deadline - time.time()) + 1,
    )

    if remaining <= 0:

        record_failed_attempt()

        st.error("TIME'S UP! Mission failed.")

        st.rerun(scope="app")

    else:

        st.progress(remaining / QUEST_DURATION)

        st.metric(
            "TIME REMAINING",
            f"{remaining} seconds",
        )


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
        "MISSION FAILED — The countdown expired. "
        "Reset or start another attempt."
    )


# ============================================================
# LIVE BUILDING ANALYTICS
# ============================================================

st.divider()
st.subheader("📊 LIVE BUILDING ANALYTICS")

metric1, metric2, metric3, metric4 = st.columns(4)

metric1.metric(
    "BUILDING STATUS",
    "LEGAL" if result.is_valid else "ILLEGAL",
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
        st.success("All geometry checks passed.")
    else:
        st.error("Building violations detected.")

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
