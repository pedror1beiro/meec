from pathlib import Path
import pytest
from tomsa.data import load_config, load_mission
from tomsa.replay import mission_state
from tomsa.figures import global_figure, local_figure

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope='module')
def mission_and_config():
    cfg=load_config(ROOT/'config.yaml')
    return load_mission(cfg,ROOT), cfg


def test_global_and_local_figures_are_serializable(mission_and_config):
    mission, cfg=mission_and_config
    timestamp=mission.start_ns + 900_000_000_000
    state=mission_state(mission,timestamp,cfg['replay']['tolerance_seconds'])
    for figure in [global_figure(mission,state,timestamp,cfg),
                   local_figure(mission,state,timestamp,'robot1',cfg,450),
                   local_figure(mission,state,timestamp,'robot7',cfg,450)]:
        assert figure.data
        assert len(figure.to_json()) > 100


def test_unknown_quaternion_does_not_fake_local_body_axes(mission_and_config):
    mission,cfg=mission_and_config
    timestamp=mission.start_ns + 900_000_000_000
    state=mission_state(mission,timestamp,cfg['replay']['tolerance_seconds'])
    fig=local_figure(mission,state,timestamp,'robot7',cfg,450)
    assert 'sem rotação' in fig.layout.title.text
    assert 'Este relativo' in fig.layout.xaxis.title.text
