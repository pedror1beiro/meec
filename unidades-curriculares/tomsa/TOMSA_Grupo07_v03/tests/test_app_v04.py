"""Smoke test real dos callbacks/HTTP Dash com missão sintética e sem rede."""
import importlib.util
import io
from pathlib import Path
import sys
import numpy as np
import pandas as pd
import pytest
import yaml
from dash import Patch


@pytest.fixture(scope='module')
def dashboard():
    root = Path(__file__).resolve().parents[1]
    old = sys.argv
    try:
        sys.argv = ['app.py', '--demo']
        spec = importlib.util.spec_from_file_location('tomsa_dashboard_test', root / 'app.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    finally:
        sys.argv = old


def test_dash_routes_and_map_configuration(dashboard):
    client = dashboard.app.server.test_client()
    assert client.get('/').status_code == 200
    layout = client.get('/_dash-layout')
    assert layout.status_code == 200
    assert b'map-mission' in layout.data and b'speed-view' in layout.data
    assert client.get('/_dash-dependencies').status_code == 200
    assert client.get('/assets/geography.js').status_code == 200
    assert client.get('/assets/ocean.js').status_code == 200


def test_frame_callback_syncs_map_cursor_and_missing_samples(dashboard):
    for key in dashboard.MISSION.traces:
        for dimension in ('2d', '3d'):
            output = dashboard.render_frame(10, key, 450, dimension)
            assert len(output) == 9
            assert output[5]['selected'] == key
            assert len(output[5]['robots']) == 3
            assert isinstance(output[6], Patch) and isinstance(output[7], Patch)
            operations = output[6].to_plotly_json()['operations']
            assert all(op['params']['value'] == 5. for op in operations)
            assert len(output[8]) == 3
    state = dashboard.mission_state(dashboard.MISSION, dashboard.MISSION.start_ns - 10**10, .3)
    assert all(s is None for s in state.values())


def test_dash_frame_callback_http_serialization(dashboard):
    callback_key = next(key for key in dashboard.app.callback_map if 'global-view.figure' in key)
    outputs = dashboard.app.callback_map[callback_key]['output']
    response = dashboard.app.server.test_client().post('/_dash-update-component', json={
        'output': callback_key,
        'outputs': [{'id': o.component_id, 'property': o.component_property} for o in outputs],
        'inputs': [{'id': key, 'property': 'value', 'value': value} for key, value in [
            ('time-slider', 8), ('robot-choice', 'robot7'), ('radius-slider', 450), ('global-dimension', '2d')]],
        'state': [], 'changedPropIds': ['time-slider.value']})
    assert response.status_code == 200, response.data
    data = response.get_json()['response']
    assert len(data['map-frame']['data']['robots']) == 3
    assert data['speed-view']['figure']['__dash_patch_update']


def test_frame_callback_displays_unavailable_samples(dashboard, monkeypatch):
    monkeypatch.setattr(dashboard, 'mission_state', lambda *args: dict.fromkeys(dashboard.MISSION.traces))
    output = dashboard.render_frame(0, 'robot1', 450, '2d')
    assert output[5]['robots'] == []
    assert all('indisponível' in str(readout) for readout in output[8])


def test_static_kinematics_charts_have_consistent_colors_and_no_metric_axis_lock(dashboard):
    for kind in ('speed', 'acceleration'):
        fig = dashboard.kinematics_figure(dashboard.MISSION, kind, dashboard.CFG)
        assert fig.layout.yaxis.scaleanchor is None
        assert len(fig.layout.shapes) == 1
        assert set(trace.line.color for trace in fig.data) == set(trace.color for trace in dashboard.MISSION.traces.values())
        assert len(fig.to_json()) > 1000


def test_existing_exports_include_truthful_frames_and_effective_yaml(dashboard):
    log = dashboard.export_ned_log(1)
    frame = pd.read_csv(io.StringIO(log['content']))
    assert {'north_m', 'east_m', 'down_m', 'speed_m_s', 'speed_rate_m_s2'} <= set(frame.columns)
    assert np.isfinite(frame['speed_m_s']).all()
    local = pd.read_csv(io.StringIO(dashboard.export_local_snapshot(1, 8, 'robot1')['content']))
    assert set(local['coordinate_frame']) == {'robot_body_confirmed'}
    effective = yaml.safe_load(dashboard.export_config(1)['content'])
    assert effective['data']['mode'] == 'demo'
    assert effective == dashboard.CFG


def test_replay_play_pause_and_finish(dashboard, monkeypatch):
    class Trigger:
        triggered_id = 'play-pause'
    monkeypatch.setattr(dashboard, 'ctx', Trigger)
    assert dashboard.control_replay(1, 0, 0, True) == (0, False, '⏸ Pause')
    assert dashboard.control_replay(2, 0, 10, False) == (10, True, '▶ Play')
    assert dashboard.control_replay(3, 0, dashboard.TOTAL_STEPS, True)[0] == 0
    Trigger.triggered_id = 'replay-timer'
    assert dashboard.control_replay(3, 1, dashboard.TOTAL_STEPS-1, False) == (dashboard.TOTAL_STEPS, True, '▶ Play')
