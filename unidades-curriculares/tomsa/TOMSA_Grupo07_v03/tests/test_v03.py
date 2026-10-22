"""Verificações adicionadas na versão 0.3 — sem dependência do Dash."""
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import yaml

from tomsa.coordinates import geodetic_to_ecef, geodetic_to_ned, world_to_robot, robot_to_world
from tomsa.data import load_config, load_mission
from tomsa.figures import global_figure, global_figure_3d, local_figure
from tomsa.replay import local_snapshot_rows, mission_state, next_step

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope='module')
def real_mission(real_mission_and_config):
    return real_mission_and_config


def test_ecef_reference_invariant():
    """Para uma origem qualquer, NED da própria origem é [0,0,0]."""
    orig = (41.45201666666667, -8.81322222222222, 55.44791126176966)
    assert np.isfinite(geodetic_to_ecef(*orig)).all()
    np.testing.assert_allclose(geodetic_to_ned(*orig, *orig), [0, 0, 0], atol=1e-8)


def test_ned_distance_approximately_matches_local_earth_arc():
    orig = (41.45201666666667, -8.81322222222222, 55.44791126176966)
    # Apenas uma verificação de ordem de grandeza: 0.001° latitude ~ 111m.
    result = geodetic_to_ned(orig[0] + .001, orig[1], orig[2], *orig)
    assert 110 < result[0] < 112
    assert abs(result[1]) < 1e-4


def test_body_round_trip_random_multiple_points():
    from scipy.spatial.transform import Rotation
    rng = np.random.default_rng(2026)
    origin = rng.normal(size=3)
    points = rng.normal(size=(24, 3))
    for ang in ([0, 0, 0], [0, 0, 90], [30, -20, 120]):
        quat = Rotation.from_euler('xyz', ang, degrees=True).as_quat()
        restored = robot_to_world(world_to_robot(points, origin, quat), origin, quat)
        np.testing.assert_allclose(restored, points, atol=1e-12)


def test_replay_last_step_stops():
    assert next_step(1, 8) == (2, False)
    assert next_step(7, 8) == (8, True)
    assert next_step(8, 8) == (8, True)
    with pytest.raises(ValueError):
        next_step(0, -1)


def test_3d_global_uses_same_ned_as_2d(real_mission):
    mission, cfg = real_mission
    t = mission.start_ns + 40_000_000_000
    state = mission_state(mission, t, cfg['replay']['tolerance_seconds'])
    f2 = global_figure(mission, state, t, cfg)
    f3 = global_figure_3d(mission, state, t, cfg)
    assert any(trace.type == 'scatter3d' for trace in f3.data)
    for key, trace in mission.traces.items():
        s = state[key]
        np.testing.assert_allclose(s.position_ned,
                                   [float(s.position_ned[i]) for i in range(3)], atol=0)
        points3d = [tr for tr in f3.data if tr.mode == 'markers+text' and tr.text[0] == trace.label]
        assert len(points3d) == 1
        np.testing.assert_allclose(
            [points3d[0].y[0], points3d[0].x[0], points3d[0].z[0]],
            s.position_ned, atol=1e-12)
    assert f2.layout.yaxis.title.text == 'Norte (m)'
    assert f3.layout.scene.zaxis.title.text == 'Baixo (m)'
    assert len(f3.to_json()) > 1000


def test_export_local_origin_is_zero_and_frame_is_explicit(real_mission):
    mission, cfg = real_mission
    t = mission.start_ns + 40_000_000_000
    frame = cfg['orientation']['assumed_body_to_ned_frame_id']
    for origin in mission.traces:
        rows = local_snapshot_rows(mission, t, origin, 0.3, frame)
        assert len(rows) == 3
        center = next(row for row in rows if row['robot'] == origin)
        assert center['reference_robot'] == origin
        np.testing.assert_allclose([center[f'local_{axis}_m'] for axis in 'xyz'],
                                   [0, 0, 0], atol=1e-10)
        assert set(row['coordinate_frame'] for row in rows) == (
            {'ned_translated'} if origin == 'robot7' else {'robot_body_assumed'})
    assert local_snapshot_rows(mission, t - 60_000_000_000,
                               'robot1', .3, frame) == []


def test_export_local_matches_plot(real_mission):
    mission, cfg = real_mission
    t = mission.start_ns + 40_000_000_000
    state = mission_state(mission, t, 0.3)
    for central_key in ['robot1', 'robot7']:
        rows = local_snapshot_rows(mission, t, central_key, 0.3,
                                   cfg['orientation']['assumed_body_to_ned_frame_id'])
        f = local_figure(mission, state, t, central_key, cfg, 600)
        for row in rows:
            marker = next(tr for tr in f.data
                          if tr.mode == 'markers+text' and tr.name == mission.traces[row['robot']].label)
            np.testing.assert_allclose([marker.y[0], marker.x[0]],
                                       [row['local_x_m'], row['local_y_m']], atol=1e-9)


def test_local_csv_round_trip(real_mission, tmp_path):
    mission, cfg = real_mission
    rows = local_snapshot_rows(mission, mission.start_ns + 40_000_000_000,
                               'robot7', .3,
                               cfg['orientation']['assumed_body_to_ned_frame_id'])
    path = tmp_path / 'tomsa_snapshot_local.csv'
    pd.DataFrame(rows).to_csv(path, index=False)
    df = pd.read_csv(path)
    assert len(df) == 3
    assert set(df['coordinate_frame']) == {'ned_translated'}
    assert set(df['reference_robot']) == {'robot7'}


def test_yaml_can_be_read_back():
    cfg = load_config(ROOT / 'config.yaml')
    # Serializar e ler de volta valida estrutura + tipagem dos parâmetros.
    assert yaml.safe_load(yaml.safe_dump(cfg, sort_keys=True)) == cfg
