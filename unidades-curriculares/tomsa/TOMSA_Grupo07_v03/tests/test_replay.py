from pathlib import Path
import numpy as np
import pytest
from tomsa.data import RobotTrace, load_config, load_mission
from tomsa.replay import nearest_sample, mission_state, local_positions, relative_aer

HERE = Path(__file__).resolve().parents[1]


@pytest.fixture(scope='module')
def mission(real_mission_and_config):
    return real_mission_and_config[0]


def test_nearest_timestamp_and_gap():
    trace = RobotTrace('r','R','#fff',np.array([0, 500_000_000, 1_000_000_000], dtype=np.int64),
                       np.zeros((3,3)), np.tile([0,0,0,1], (3,1)),
                       np.array(['world_ned']*3), np.zeros(3), np.zeros(3), np.zeros(3))
    assert nearest_sample(trace, 580_000_000, .3).index == 1
    assert nearest_sample(trace, 580_000_000, .05) is None
    assert nearest_sample(trace, -1_000_000_000, .3) is None


def test_real_mission_row_counts_and_time_overlap(mission):
    assert {k: len(t.times_ns) for k, t in mission.traces.items()} == {
        'robot1': 9537, 'robot4': 5615, 'robot7': 15000}
    assert abs(mission.duration_s - 2396.191938162) < 1e-7


def test_local_center_is_zero(mission):
    state = mission_state(mission, mission.start_ns + 40_000_000_000, .3)
    assert all(snap is not None for snap in state.values())
    local, rotated = local_positions(state, 'robot1', 'world_ned')
    assert rotated
    np.testing.assert_allclose(local['robot1'], [0, 0, 0], atol=1e-9)


def test_unknown_orientation_falls_back_to_translated_ned(mission):
    state = mission_state(mission, mission.start_ns + 40_000_000_000, .3)
    local, rotated = local_positions(state, 'robot7', 'world_ned')
    assert not rotated
    np.testing.assert_allclose(local['robot7'], [0, 0, 0], atol=1e-9)
    np.testing.assert_allclose(local['robot1'],
                               state['robot1'].position_ned - state['robot7'].position_ned)


def test_aer_independent_of_unknown_orientation(mission):
    state = mission_state(mission, mission.start_ns + 40_000_000_000, .3)
    rows = relative_aer(state, 'robot7')
    assert len(rows) == 2
    assert all(x['range_m'] > 0 and np.isfinite(x['azimuth_deg']) for x in rows)
