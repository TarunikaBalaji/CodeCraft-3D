
from visualization.scene_3d import build_3d_model


def test_3d_model_returns_plotly_figure_and_geometry_result():
    fig, result = build_3d_model()

    assert fig is not None
    assert len(fig.data) >= 4
    assert result.violations == ["HEIGHT_VIOLATION"]
    assert result.is_valid is False


def test_legal_building_uses_valid_geometry_result():
    fig, result = build_3d_model(
        building_width=20,
        building_depth=30,
        building_height=30,
        building_x=5,
        building_y=10,
    )

    assert result.is_valid is True
    assert result.violations == []
    assert len(fig.data) >= 4


def test_building_position_is_checked_by_geometry_engine():
    fig, result = build_3d_model(
        building_width=20,
        building_depth=30,
        building_height=30,
        building_x=1,
        building_y=1,
    )

    assert "SETBACK_VIOLATION" in result.violations
    assert result.is_valid is False


def test_3d_scene_contains_expected_visual_layers():
    fig, result = build_3d_model()

    trace_names = [trace.name for trace in fig.data]

    assert "Site boundary" in trace_names
    assert "Permitted envelope" in trace_names
    assert "Proposed building" in trace_names
    assert "Maximum height" in trace_names
