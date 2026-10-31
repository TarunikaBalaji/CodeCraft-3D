import plotly.graph_objects as go


DISTRICTS = [
    {
        "name": "Starter District",
        "description": "Your first construction zone.",
        "required_xp": 0,
        "color": "#38D9C8",
        "position": (0, 0),
        "buildings": [(3, 3, 5), (8, 4, 8), (5, 9, 6)],
        "mission": "MISSION 001 — SAVE THE BLOCK",
    },
    {
        "name": "Neon Heights",
        "description": "Build a futuristic skyline.",
        "required_xp": 500,
        "color": "#917CFF",
        "position": (18, 0),
        "buildings": [(21, 3, 12), (26, 5, 9), (23, 10, 15)],
        "mission": "MISSION 002 — RISE ABOVE",
    },
    {
        "name": "Aqua Quarter",
        "description": "Design a sustainable waterfront.",
        "required_xp": 1200,
        "color": "#36BDF5",
        "position": (36, 0),
        "buildings": [(39, 3, 7), (44, 5, 11), (41, 10, 9)],
        "mission": "MISSION 003 — WATERFRONT RESCUE",
    },
    {
        "name": "Skyline Nexus",
        "description": "Master advanced urban design.",
        "required_xp": 2200,
        "color": "#F0B65C",
        "position": (18, 18),
        "buildings": [(21, 21, 14), (26, 23, 18), (23, 28, 12)],
        "mission": "MISSION 004 — SKYLINE PROTOCOL",
    },
    {
        "name": "Guardian Central",
        "description": "Protect the future of the city.",
        "required_xp": 3500,
        "color": "#F17BAF",
        "position": (36, 18),
        "buildings": [(39, 21, 20), (44, 23, 16), (41, 28, 24)],
        "mission": "MISSION 005 — CITY GUARDIAN",
    },
]


BACKGROUND = "#0B1224"
GROUND = "#111E36"
ROAD = "#263B5D"
TEXT = "#EAF0FF"


def add_building(fig, x, y, height, color, opacity=1.0):
    """Add a detailed cuboid building to the city."""

    dx = 3.0
    dy = 3.0

    vertices = [
        (x, y, 0),
        (x + dx, y, 0),
        (x + dx, y + dy, 0),
        (x, y + dy, 0),
        (x, y, height),
        (x + dx, y, height),
        (x + dx, y + dy, height),
        (x, y + dy, height),
    ]

    triangles = [
        (0, 1, 2), (0, 2, 3),
        (4, 5, 6), (4, 6, 7),
        (0, 1, 5), (0, 5, 4),
        (1, 2, 6), (1, 6, 5),
        (2, 3, 7), (2, 7, 6),
        (3, 0, 4), (3, 4, 7),
    ]

    fig.add_trace(
        go.Mesh3d(
            x=[v[0] for v in vertices],
            y=[v[1] for v in vertices],
            z=[v[2] for v in vertices],
            i=[t[0] for t in triangles],
            j=[t[1] for t in triangles],
            k=[t[2] for t in triangles],
            color=color,
            opacity=opacity,
            flatshading=True,
            hoverinfo="skip",
            showscale=False,
            lighting=dict(
                ambient=0.72,
                diffuse=0.85,
                specular=0.4,
                roughness=0.48,
            ),
            lightposition=dict(x=100, y=150, z=200),
        )
    )

    # Fine illuminated vertical edges.
    edge_pairs = [
        (0, 4),
        (1, 5),
        (2, 6),
        (3, 7),
    ]

    for start, end in edge_pairs:
        fig.add_trace(
            go.Scatter3d(
                x=[vertices[start][0], vertices[end][0]],
                y=[vertices[start][1], vertices[end][1]],
                z=[vertices[start][2], vertices[end][2]],
                mode="lines",
                line=dict(
                    color=color,
                    width=2,
                ),
                opacity=min(opacity + 0.1, 1.0),
                hoverinfo="skip",
                showlegend=False,
            )
        )


def add_district_platform(fig, district, selected, unlocked):
    """Draw a raised district platform and its perimeter."""

    x, y = district["position"]
    color = district["color"] if unlocked else "#46516A"

    # Platform floor.
    fig.add_trace(
        go.Mesh3d(
            x=[x, x + 15, x + 15, x],
            y=[y, y, y + 15, y + 15],
            z=[0.18, 0.18, 0.18, 0.18],
            i=[0, 0],
            j=[1, 2],
            k=[2, 3],
            color=color,
            opacity=0.12 if unlocked else 0.06,
            hoverinfo="skip",
            showscale=False,
        )
    )

    # District perimeter.
    perimeter_color = "#FFFFFF" if selected else color

    fig.add_trace(
        go.Scatter3d(
            x=[x, x + 15, x + 15, x, x],
            y=[y, y, y + 15, y + 15, y],
            z=[0.38] * 5,
            mode="lines",
            line=dict(
                color=perimeter_color,
                width=7 if selected else 3,
            ),
            hoverinfo="skip",
            showlegend=False,
        )
    )


def build_city_world(
    player_xp=0,
    selected_district="Starter District",
):
    """Build the futuristic isometric city map."""

    fig = go.Figure()

    # ---------------------------------------------------------
    # 1. CITY GROUND
    # ---------------------------------------------------------

    fig.add_trace(
        go.Mesh3d(
            x=[0, 54, 54, 0],
            y=[0, 0, 36, 36],
            z=[0, 0, 0, 0],
            i=[0, 0],
            j=[1, 2],
            k=[2, 3],
            color=GROUND,
            opacity=1,
            hoverinfo="skip",
            showscale=False,
        )
    )

    # ---------------------------------------------------------
    # 2. ROAD NETWORK
    # ---------------------------------------------------------

    for x in [9, 27, 45]:
        fig.add_trace(
            go.Scatter3d(
                x=[x, x],
                y=[-1, 37],
                z=[0.25, 0.25],
                mode="lines",
                line=dict(
                    color=ROAD,
                    width=8,
                ),
                hoverinfo="skip",
                showlegend=False,
            )
        )

    for y in [9, 27]:
        fig.add_trace(
            go.Scatter3d(
                x=[-1, 55],
                y=[y, y],
                z=[0.25, 0.25],
                mode="lines",
                line=dict(
                    color=ROAD,
                    width=8,
                ),
                hoverinfo="skip",
                showlegend=False,
            )
        )

    # ---------------------------------------------------------
    # 3. DISTRICTS AND BUILDINGS
    # ---------------------------------------------------------

    for district in DISTRICTS:

        unlocked = player_xp >= district["required_xp"]
        selected = district["name"] == selected_district

        x, y = district["position"]

        color = district["color"] if unlocked else "#46516A"
        opacity = 1.0 if unlocked else 0.28

        add_district_platform(
            fig,
            district,
            selected,
            unlocked,
        )

        # Buildings.
        for bx, by, height in district["buildings"]:
            add_building(
                fig,
                bx,
                by,
                height,
                color,
                opacity,
            )

        # -----------------------------------------------------
        # 4. DISTRICT LABELS
        # Put labels above each district's tallest building.
        # This avoids putting every label at the same Z level.
        # -----------------------------------------------------

        tallest_building = max(
            building[2] for building in district["buildings"]
        )

        label_height = tallest_building + 5

        if unlocked:
            label = district["name"]
            label_color = TEXT
        else:
            label = f"LOCKED · {district['required_xp']} XP"
            label_color = "#A5B0C8"

        fig.add_trace(
            go.Scatter3d(
                x=[x + 7.5],
                y=[y + 7.5],
                z=[label_height],
                mode="text",
                text=[label],
                textposition="middle center",
                textfont=dict(
                    family="Arial",
                    size=12 if selected else 10,
                    color="#FFFFFF" if selected else label_color,
                ),
                hovertemplate=(
                    f"<b>{district['name']}</b><br>"
                    f"{district['description']}<br>"
                    f"Required XP: {district['required_xp']}"
                    "<extra></extra>"
                ),
                showlegend=False,
            )
        )

        # Selected district marker.
        if selected:
            fig.add_trace(
                go.Scatter3d(
                    x=[x + 7.5],
                    y=[y + 7.5],
                    z=[0.75],
                    mode="markers",
                    marker=dict(
                        size=10,
                        color="#FFFFFF",
                        symbol="diamond",
                        line=dict(
                            color=district["color"],
                            width=4,
                        ),
                    ),
                    hoverinfo="skip",
                    showlegend=False,
                )
            )

    # ---------------------------------------------------------
    # 5. SCENE AND CAMERA
    # ---------------------------------------------------------

    fig.update_layout(
        height=640,
        autosize=True,
        margin=dict(
            l=0,
            r=0,
            t=0,
            b=0,
        ),
        paper_bgcolor=BACKGROUND,
        plot_bgcolor=BACKGROUND,
        font=dict(
            color=TEXT,
            family="Arial",
        ),
        scene=dict(
            bgcolor=BACKGROUND,
            xaxis=dict(
                visible=False,
                range=[-2, 56],
                showbackground=False,
            ),
            yaxis=dict(
                visible=False,
                range=[-2, 38],
                showbackground=False,
            ),
            zaxis=dict(
                visible=False,
                range=[0, 32],
                showbackground=False,
            ),
            camera=dict(
                eye=dict(
                    x=1.25,
                    y=1.25,
                    z=0.88,
                ),
                center=dict(
                    x=0,
                    y=0,
                    z=-0.08,
                ),
                projection=dict(
                    type="perspective",
                ),
            ),
            aspectmode="manual",
            aspectratio=dict(
                x=1.35,
                y=1.0,
                z=0.62,
            ),
        ),
        showlegend=False,
    )

    return fig