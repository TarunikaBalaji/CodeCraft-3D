
from typing import Any

import plotly.graph_objects as go

from core.geometry import (
    Site,
    Setbacks,
    Building,
    GeometryResult,
    calculate_geometry,
)


# ---------------------------------------------------------
# CODECRAFT 3D VISUAL THEME
# ---------------------------------------------------------

BACKGROUND = "#0B1224"
PLOT_BACKGROUND = "#0E1930"
GRID_COLOR = "#263957"
TEXT_COLOR = "#EAF0FF"
MUTED_COLOR = "#AAB8D4"

SITE_COLOR = "#8CA5C9"
ENVELOPE_COLOR = "#38BDF8"
LEGAL_COLOR = "#20D6B2"
VIOLATION_COLOR = "#FF4057"
HEIGHT_COLOR = "#FFC857"


def _add_box(
    fig: go.Figure,
    x0: float,
    x1: float,
    y0: float,
    y1: float,
    z0: float,
    z1: float,
    color: str,
    opacity: float,
    name: str,
    show_legend: bool = True,
) -> None:
    """Add a cuboid to the interactive 3D scene."""

    vertices = [
        (x0, y0, z0),
        (x1, y0, z0),
        (x1, y1, z0),
        (x0, y1, z0),
        (x0, y0, z1),
        (x1, y0, z1),
        (x1, y1, z1),
        (x0, y1, z1),
    ]

    x, y, z = zip(*vertices)

    i = [0, 0, 4, 4, 0, 0, 1, 1, 2, 2, 3, 3]
    j = [1, 2, 5, 6, 1, 5, 2, 6, 3, 7, 0, 4]
    k = [2, 3, 6, 7, 5, 4, 6, 5, 7, 6, 4, 7]

    fig.add_trace(
        go.Mesh3d(
            x=x,
            y=y,
            z=z,
            i=i,
            j=j,
            k=k,
            color=color,
            opacity=opacity,
            name=name,
            showlegend=show_legend,
            flatshading=True,
            showscale=False,
            lighting=dict(
                ambient=0.72,
                diffuse=0.82,
                specular=0.35,
                roughness=0.5,
            ),
            lightposition=dict(
                x=100,
                y=150,
                z=200,
            ),
            hovertemplate=(
                f"<b>{name}</b><br>"
                "X: %{x:.1f}<br>"
                "Y: %{y:.1f}<br>"
                "Height: %{z:.1f}"
                "<extra></extra>"
            ),
        )
    )


def _add_site_outline(
    fig: go.Figure,
    width: float,
    depth: float,
) -> None:
    """Draw a clearly visible site boundary."""

    x = [0, width, width, 0, 0]
    y = [0, 0, depth, depth, 0]
    z = [0.12, 0.12, 0.12, 0.12, 0.12]

    fig.add_trace(
        go.Scatter3d(
            x=x,
            y=y,
            z=z,
            mode="lines",
            name="Site boundary",
            line=dict(
                color=SITE_COLOR,
                width=6,
            ),
            hovertemplate="Site boundary<extra></extra>",
        )
    )


def _add_ground_plane(
    fig: go.Figure,
    width: float,
    depth: float,
) -> None:
    """Add a subtle ground plane beneath the building."""

    fig.add_trace(
        go.Mesh3d(
            x=[0, width, width, 0],
            y=[0, 0, depth, depth],
            z=[0, 0, 0, 0],
            i=[0, 0],
            j=[1, 2],
            k=[2, 3],
            color="#172945",
            opacity=0.65,
            name="Site ground",
            showlegend=False,
            hoverinfo="skip",
            showscale=False,
        )
    )


def build_3d_model(
    site_width: float = 40,
    site_depth: float = 60,
    front_setback: float = 10,
    rear_setback: float = 5,
    left_setback: float = 5,
    right_setback: float = 5,
    max_height: float = 45,
    max_coverage_percent: float = 50,
    building_width: float = 30,
    building_depth: float = 35,
    building_height: float = 50,
    building_x: float = 5,
    building_y: float = 10,
) -> tuple[go.Figure, GeometryResult]:
    """
    Build an interactive 3D site, permitted envelope,
    and proposed building.

    Geometry validation remains exclusively in
    core.geometry.calculate_geometry().
    """

    # 1. Create geometry inputs.
    site = Site(
        width=site_width,
        depth=site_depth,
    )

    setbacks = Setbacks(
        front=front_setback,
        rear=rear_setback,
        left=left_setback,
        right=right_setback,
    )

    building = Building(
        width=building_width,
        depth=building_depth,
        height=building_height,
        x=building_x,
        y=building_y,
    )

    # The deterministic geometry engine remains
    # the single source of truth for compliance.
    result = calculate_geometry(
        site=site,
        setbacks=setbacks,
        building=building,
        max_height=max_height,
        max_coverage_percent=max_coverage_percent,
    )

    fig = go.Figure()

    # 2. Ground and site boundary.
    _add_ground_plane(
        fig,
        width=site_width,
        depth=site_depth,
    )

    _add_site_outline(
        fig,
        width=site_width,
        depth=site_depth,
    )

    # 3. Permitted buildable envelope.
    _add_box(
        fig=fig,
        x0=left_setback,
        x1=site_width - right_setback,
        y0=front_setback,
        y1=site_depth - rear_setback,
        z0=0,
        z1=max_height,
        color=ENVELOPE_COLOR,
        opacity=0.12,
        name="Permitted envelope",
    )

    # 4. Proposed building.
    building_color = (
        LEGAL_COLOR
        if result.is_valid
        else VIOLATION_COLOR
    )

    building_status = (
        "COMPLIANT"
        if result.is_valid
        else "VIOLATION DETECTED"
    )

    _add_box(
        fig=fig,
        x0=building_x,
        x1=building_x + building_width,
        y0=building_y,
        y1=building_y + building_depth,
        z0=0,
        z1=building_height,
        color=building_color,
        opacity=0.88,
        name="Proposed building",
    )

    # 5. Maximum height reference.
    fig.add_trace(
        go.Scatter3d(
            x=[0, site_width],
            y=[0, 0],
            z=[max_height, max_height],
            mode="lines",
            name="Maximum height",
            line=dict(
                color=HEIGHT_COLOR,
                width=5,
                dash="dash",
            ),
            hovertemplate=(
                f"Maximum permitted height: {max_height}"
                "<extra></extra>"
            ),
        )
    )

    # 6. Scene styling.
    z_max = max(
        max_height,
        building_height,
        1,
    ) * 1.15

    fig.update_layout(
        title=dict(
            text=(
                f"<b>CODECRAFT 3D | {building_status}</b>"
                "<br>"
                "<sup>Deterministic building constraint simulation</sup>"
            ),
            x=0.5,
            xanchor="center",
            y=0.98,
            yanchor="top",
            font=dict(
                family="Arial",
                size=17,
                color=TEXT_COLOR,
            ),
        ),

        scene=dict(
            bgcolor=PLOT_BACKGROUND,

            xaxis=dict(
                title=dict(
                    text="Site width",
                    font=dict(color=TEXT_COLOR, size=12),
                ),
                range=[-3, site_width + 3],
                backgroundcolor=PLOT_BACKGROUND,
                gridcolor=GRID_COLOR,
                zerolinecolor=GRID_COLOR,
                linecolor=GRID_COLOR,
                tickfont=dict(color=MUTED_COLOR),
                showbackground=True,
                showspikes=False,
            ),

            yaxis=dict(
                title=dict(
                    text="Site depth",
                    font=dict(color=TEXT_COLOR, size=12),
                ),
                range=[-3, site_depth + 3],
                backgroundcolor=PLOT_BACKGROUND,
                gridcolor=GRID_COLOR,
                zerolinecolor=GRID_COLOR,
                linecolor=GRID_COLOR,
                tickfont=dict(color=MUTED_COLOR),
                showbackground=True,
                showspikes=False,
            ),

            zaxis=dict(
                title=dict(
                    text="Building height",
                    font=dict(color=TEXT_COLOR, size=12),
                ),
                range=[0, z_max],
                backgroundcolor=PLOT_BACKGROUND,
                gridcolor=GRID_COLOR,
                zerolinecolor=GRID_COLOR,
                linecolor=GRID_COLOR,
                tickfont=dict(color=MUTED_COLOR),
                showbackground=True,
                showspikes=False,
            ),

            # Slightly taller scene proportions.
            aspectmode="manual",
            aspectratio=dict(
                x=1.0,
                y=1.25,
                z=1.15,
            ),

            # Closer camera: building becomes the focal point.
            camera=dict(
                eye=dict(
                    x=1.05,
                    y=1.20,
                    z=0.90,
                ),
                center=dict(
                    x=0,
                    y=0,
                    z=0,
                ),
                up=dict(
                    x=0,
                    y=0,
                    z=1,
                ),
                projection=dict(
                    type="perspective",
                ),
            ),
        ),

        paper_bgcolor=BACKGROUND,
        plot_bgcolor=BACKGROUND,

        font=dict(
            color=TEXT_COLOR,
            family="Arial",
            size=12,
        ),

        legend=dict(
            orientation="h",
            yanchor="top",
            y=1.075,
            xanchor="center",
            x=0.5,
            font=dict(
                size=10,
                color=TEXT_COLOR,
            ),
            bgcolor="rgba(14,25,48,0.88)",
            bordercolor="#263957",
            borderwidth=1,
            tracegroupgap=8,
        ),

        margin=dict(
            l=5,
            r=5,
            t=125,
            b=5,
        ),

        height=570,
        autosize=True,

        hoverlabel=dict(
            bgcolor="#172945",
            bordercolor="#38BDF8",
            font=dict(
                color=TEXT_COLOR,
                size=12,
            ),
        ),
    )

    return fig, result
