from copy import deepcopy
import numpy as np
import pytest
from scipy.spatial.transform import Rotation
from tomsa.coordinates import geographic_heading, ecef_to_ned_rotation
from tomsa.data import _demo_frames, _to_trace, LINEAR_COLS, ANGULAR_COLS, QUAT_COLS
from tomsa.geography import map_frame_data
from tomsa.replay import mission_state, local_snapshot_rows


@pytest.mark.parametrize('yaw,heading', [(0, 0), (90, 90), (180, 180), (-90, 270)])
def test_heading_cardinals_and_normalization(yaw, heading):
    q = Rotation.from_euler('z', yaw, degrees=True).as_quat() * 4
    assert geographic_heading(q, 41., -8., 41., -8.) == pytest.approx(heading, abs=1e-10)
    assert geographic_heading(-q, 41., -8., 41., -8.) == pytest.approx(heading, abs=1e-10)


def test_vertical_body_axis_has_no_heading_and_zero_quaternion_rejected():
    q = Rotation.from_euler('y', 90, degrees=True).as_quat()
    assert geographic_heading(q, 41., -8., 41., -8.) is None
    with pytest.raises(ValueError):
        geographic_heading([0, 0, 0, 0], 41., -8., 41., -8.)


def test_heading_transports_fixed_ned_to_robot_tangent_plane():
    # Build an orientation whose forward direction is local east far from origin.
    east_ecef = ecef_to_ned_rotation(50., 10.).T @ [0., 1., 0.]
    forward_fixed = ecef_to_ned_rotation(41., -8.) @ east_ecef
    rotation, _ = Rotation.align_vectors([forward_fixed], [[1., 0., 0.]])
    assert geographic_heading(rotation.as_quat(), 50., 10., 41., -8.) == pytest.approx(90.)


def test_demo_has_confirmed_map_heading_and_explicit_local_export(demo_mission_and_config):
    mission, cfg = demo_mission_and_config
    state = mission_state(mission, mission.start_ns, .3)
    assert all(s.body_to_ned_confirmed for s in state.values())
    assert all(r['heading_deg'] is not None for r in map_frame_data(mission, state, 'robot1', cfg)['robots'])
    rows = local_snapshot_rows(mission, mission.start_ns, 'robot1', .3, None)
    assert {r['coordinate_frame'] for r in rows} == {'robot_body_confirmed'}


def test_unconfirmed_real_conventions_do_not_create_map_heading(demo_mission_and_config):
    mission, cfg = demo_mission_and_config
    state = mission_state(mission, mission.start_ns, .3)
    for snap in state.values():
        snap.body_to_ned_confirmed = False
    assert all(r['heading_deg'] is None for r in map_frame_data(mission, state, 'robot1', cfg)['robots'])


def test_rotating_body_velocity_must_be_transformed_before_differentiation(demo_mission_and_config):
    _, cfg = demo_mission_and_config
    cfg = deepcopy(cfg)
    frame = _demo_frames(cfg)['robot1'].iloc[:8].copy()
    yaw = np.linspace(0, 90, len(frame))
    quats = Rotation.from_euler('z', yaw[:, None], degrees=True).as_quat()
    frame[QUAT_COLS] = quats * 2
    frame[LINEAR_COLS] = Rotation.from_quat(quats).inv().apply(np.tile([1., 0., 0.], (len(frame), 1)))
    cfg['data']['mode'] = 'zip'
    unknown = _to_trace('robot1', frame, cfg)
    assert np.isnan(unknown.kinematics.acceleration_magnitude_m_s2).all()
    cfg['kinematics']['confirmed_velocity_frame'] = 'body'
    # A selected hypothesis must never enable physical acceleration.
    assert np.isnan(_to_trace('robot1', frame, cfg).kinematics.acceleration_magnitude_m_s2).all()
    cfg['orientation']['confirmed_body_to_ned_frame_id'] = 'world_ned'
    trace = _to_trace('robot1', frame, cfg)
    np.testing.assert_allclose(trace.kinematics.acceleration_magnitude_m_s2, 0., atol=1e-12)
    np.testing.assert_allclose(np.linalg.norm(trace.quaternions_xyzw, axis=1), 1.)
    frame['header.frame_id'] = 'WGS84'
    assert np.isnan(_to_trace('robot1', frame, cfg).kinematics.acceleration_magnitude_m_s2).all()
    frame['header.frame_id'] = 'world_ned'
    frame['child_frame_id'] = 'another_body'
    assert np.isnan(_to_trace('robot1', frame, cfg).kinematics.acceleration_magnitude_m_s2).all()


def test_optional_velocities_do_not_discard_valid_positions(demo_mission_and_config):
    _, cfg = demo_mission_and_config
    frame = _demo_frames(cfg)['robot1'].iloc[:8].copy()
    frame.loc[frame.index[2], LINEAR_COLS[0]] = np.inf
    trace = _to_trace('robot1', frame, cfg)
    assert len(trace.times_ns) == 8
    assert np.isnan(trace.kinematics.speed_m_s[2])
    frame = frame.drop(columns=LINEAR_COLS + ANGULAR_COLS + ['child_frame_id'])
    trace = _to_trace('robot1', frame, cfg)
    assert len(trace.times_ns) == 8
    assert np.isnan(trace.kinematics.speed_m_s).all()


def test_unsorted_velocity_rows_stay_aligned_with_poses(demo_mission_and_config):
    _, cfg = demo_mission_and_config
    frame = _demo_frames(cfg)['robot1'].iloc[:8].copy()
    expected = _to_trace('robot1', frame, cfg)
    shuffled = _to_trace('robot1', frame.iloc[::-1], cfg)
    np.testing.assert_allclose(shuffled.linear_velocity_m_s, expected.linear_velocity_m_s)
    np.testing.assert_allclose(shuffled.kinematics.speed_rate_m_s2, expected.kinematics.speed_rate_m_s2)


def test_real_kinematics_do_not_claim_confirmed_frames(real_mission_and_config):
    mission, cfg = real_mission_and_config
    state = mission_state(mission, mission.start_ns, .3)
    for trace in mission.traces.values():
        assert set(trace.child_frames) == {'body'}
        assert np.isfinite(trace.kinematics.speed_m_s).all()
        assert np.isfinite(trace.kinematics.speed_rate_m_s2).all()
        assert np.isnan(trace.kinematics.acceleration_magnitude_m_s2).all()
    assert all(robot['heading_deg'] is None for robot in map_frame_data(mission, state, 'robot1', cfg)['robots'])
