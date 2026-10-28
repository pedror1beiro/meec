"""Mapa validado com dados sintéticos públicos, sem exportar trajetórias reais."""
import json
import shutil
import subprocess
import pytest
from pathlib import Path

from tomsa.data import load_config, load_mission
from tomsa.geography import map_mission_data, map_frame_data
from tomsa.replay import mission_state


def test_map_uses_original_lon_lat_and_shared_replay_samples():
    cfg = load_config(Path(__file__).resolve().parents[1] / 'config.yaml')
    cfg['data']['mode'] = 'demo'
    mission = load_mission(cfg)
    data = map_mission_data(mission, cfg)
    state = mission_state(mission, mission.start_ns + 5_100_000_000, .3)
    frame = map_frame_data(mission, state, 'robot4')
    for feature in data['trajectories']['features']:
        trace = mission.traces[feature['properties']['robot']]
        assert feature['properties']['color'] == trace.color
        assert feature['geometry']['coordinates'] == list(map(list, zip(trace.longitude, trace.latitude)))
        assert data['timeline_s'][trace.key] == ((trace.times_ns-mission.start_ns) / 1e9).tolist()
    for robot in frame['robots']:
        trace, snap = mission.traces[robot['robot']], state[robot['robot']]
        assert robot['longitude'] == trace.longitude[snap.index]
        assert robot['latitude'] == trace.latitude[snap.index]
        assert robot['sample_index'] == snap.index
    assert frame['selected'] == 'robot4'
    assert len(json.dumps(frame, allow_nan=False)) < 700
    assert 'trajectories' not in frame
    assert map_frame_data(mission, dict.fromkeys(state), 'robot1')['robots'] == []
    json.dumps(data, allow_nan=False)


def test_map_ring_uses_the_selected_radius_and_not_an_orientation_assumption(demo_mission_and_config):
    mission, cfg = demo_mission_and_config
    state = mission_state(mission, mission.start_ns, .3)
    data = map_frame_data(mission, state, 'robot7', cfg, 350)
    assert data['radius_m'] == 350
    assert data['selected'] == 'robot7'


def test_map_javascript_lifecycle():
    node = shutil.which('node')
    if not node:
        pytest.skip('Node ausente; executar node --test tests/test_geography.js para validar o ciclo JS.')
    result = subprocess.run([node, '--test', str(Path(__file__).with_suffix('.js')),
                             str(Path(__file__).with_name('test_ocean.js'))],
                            capture_output=True, text=True, encoding='utf-8', timeout=30)
    assert result.returncode == 0, result.stdout + result.stderr
