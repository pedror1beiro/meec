"""Propriedades de SE(3) testadas com geometria conhecida e amostras reais."""
from copy import deepcopy
import numpy as np
import pytest
from scipy.spatial.transform import Rotation
from tomsa.figures import frame_comparison_figure
from tomsa.replay import Snapshot, frame_diagnostics, mission_state


def triangle(frame='world_ned', confirmed=False):
    origin = np.array([1000., -2000., -3.])
    quat = Rotation.from_euler('xyz', [33., 17., 61.], degrees=True).as_quat()
    return {key: Snapshot(i, i*20_000_000, origin+offset, quat.copy(), frame, confirmed)
            for i, (key, offset) in enumerate(zip(['robot1', 'robot4', 'robot7'],
                [np.zeros(3), [1., 2., 3.], [4., -1., 5.]]))}


def test_known_triangle_preserves_full_3d_distances_and_inverse():
    state = triangle()
    result = frame_diagnostics(state, 'robot1', 'world_ned')
    assert result['frame'] == 'robot_body_assumed'
    assert result['checks_pass']
    np.testing.assert_allclose(result['local'][0], 0., atol=1e-12)
    np.testing.assert_allclose(result['inverse'] @ result['transform'], np.eye(4), atol=1e-12)
    assert result['pairs'][0]['ned_m'] == pytest.approx(np.sqrt(14))
    assert result['pairs'][0]['local_m'] == pytest.approx(np.sqrt(14))
    assert result['orthogonality_error'] < 1e-12
    assert result['determinant'] == pytest.approx(1.)
    assert result['roundtrip_error_m'] < 1e-9
    # A projeção XY pode mudar de comprimento: não pode validar o invariante 3D.
    projected_world = np.linalg.norm((result['world'][1]-result['world'][0])[:2])
    projected_local = np.linalg.norm((result['local'][1]-result['local'][0])[:2])
    assert not np.isclose(projected_world, projected_local)


def test_unknown_frame_is_translation_and_checks_do_not_confirm_convention():
    result = frame_diagnostics(triangle('WGS84'), 'robot1', 'world_ned')
    assert result['checks_pass']
    assert result['frame'] == 'ned_translated'
    np.testing.assert_allclose(result['transform'][:3, :3], np.eye(3))
    np.testing.assert_allclose(result['local'], result['world']-result['world'][0])
    disabled = frame_diagnostics(triangle(), 'robot1', None)
    assert disabled['frame'] == 'ned_translated'


def test_confirmed_and_sign_scaled_quaternions_give_same_geometry():
    state = triangle(confirmed=True)
    baseline = frame_diagnostics(state, 'robot1', None)
    scaled = deepcopy(state)
    scaled['robot1'].quaternion_xyzw *= -4
    result = frame_diagnostics(scaled, 'robot1', None)
    assert result['frame'] == 'robot_body_confirmed'
    np.testing.assert_allclose(result['local'], baseline['local'], atol=1e-12)


def test_missing_center_peers_and_coincident_positions_are_explicit():
    state = triangle()
    state['robot1'] = None
    assert frame_diagnostics(state, 'robot1', 'world_ned') is None
    state = triangle()
    state['robot7'] = None
    assert len(frame_diagnostics(state, 'robot1', 'world_ned')['pairs']) == 1
    state['robot4'] = None
    assert frame_diagnostics(state, 'robot1', 'world_ned')['pairs'] == []
    state = triangle()
    state['robot4'].position_ned = state['robot1'].position_ned.copy()
    result = frame_diagnostics(state, 'robot1', 'world_ned')
    assert result['checks_pass'] and result['pairs'][0]['ned_m'] == 0


def test_comparison_figure_uses_the_exact_3d_samples(demo_mission_and_config):
    mission, cfg = demo_mission_and_config
    state = mission_state(mission, mission.start_ns, .3)
    result = frame_diagnostics(state, 'robot1', cfg['orientation']['assumed_body_to_ned_frame_id'])
    figure = frame_comparison_figure(mission, result, 'robot1')
    for scene, points in [('scene', result['world']), ('scene2', result['local'])]:
        markers = [trace for trace in figure.data if getattr(trace, 'mode', None) == 'markers' and trace.scene == scene]
        for marker, point in zip(markers, points):
            np.testing.assert_allclose([marker.x[0], marker.y[0], marker.z[0]], point)
    assert figure.layout.scene.xaxis.range[1]-figure.layout.scene.xaxis.range[0] == pytest.approx(
        figure.layout.scene2.xaxis.range[1]-figure.layout.scene2.xaxis.range[0])
    assert len(figure.to_json()) > 1000


def test_real_data_checks_preserve_the_original_orientation_limits(real_mission_and_config):
    mission, cfg = real_mission_and_config
    state = mission_state(mission, mission.start_ns+40_000_000_000, .3)
    for center in mission.traces:
        result = frame_diagnostics(state, center, cfg['orientation']['assumed_body_to_ned_frame_id'])
        assert result['checks_pass']
        assert result['frame'] == ('ned_translated' if center == 'robot7' else 'robot_body_assumed')
        assert len(result['pairs']) == 3
