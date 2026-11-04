"""Carregamento de uma missão repartida por ZIPs, com dados sintéticos."""
from pathlib import Path
from zipfile import ZipFile
import numpy as np
import pytest
from tomsa.data import load_config, load_mission, _demo_frames


@pytest.fixture
def split_mission(tmp_path):
    cfg = load_config(Path(__file__).resolve().parents[1] / 'config.yaml')
    cfg['data']['files']['robot8'] = 'robot8_s1.csv'
    cfg['robots']['robot8'] = {'label': 'Robô 8', 'color': '#7455b8'}
    cfg['data']['mode'] = 'demo'
    frames = _demo_frames(cfg)
    with ZipFile(tmp_path / 'base.zip', 'w') as base, ZipFile(tmp_path / 'extra.zip', 'w') as extra:
        for key, frame in frames.items():
            target = extra if key == 'robot8' else base
            target.writestr('logs/' + cfg['data']['files'][key], frame.iloc[:4].to_csv(index=False))
    cfg['data'].update(mode='zip', zip_path='base.zip', extra_zip_paths=['extra.zip'])
    return cfg, tmp_path


def test_four_robot_mission_from_two_relative_archive_paths(split_mission):
    cfg, folder = split_mission
    mission = load_mission(cfg, folder)
    assert set(mission.traces) == {'robot1', 'robot4', 'robot7', 'robot8'}
    assert mission.duration_s == pytest.approx(1.5)
    assert mission.traces['robot8'].label == 'Robô 8'
    assert all(len(trace.times_ns) == 4 for trace in mission.traces.values())
    assert np.isfinite(mission.traces['robot8'].positions_ned).all()


def test_duplicate_csv_across_archives_is_ambiguous(split_mission):
    cfg, folder = split_mission
    with ZipFile(folder / 'base.zip') as base:
        duplicate = base.read('logs/robot1_s1.csv')
    with ZipFile(folder / 'extra.zip', 'a') as extra:
        extra.writestr('other/robot1_s1.csv', duplicate)
    with pytest.raises(ValueError, match='robot1_s1.csv.*encontrados 2'):
        load_mission(cfg, folder)


def test_missing_extra_archive_is_reported(split_mission):
    cfg, folder = split_mission
    cfg['data']['extra_zip_paths'] = ['absent.zip']
    with pytest.raises(FileNotFoundError, match='absent.zip'):
        load_mission(cfg, folder)


def test_missing_robot_csv_is_reported(split_mission):
    cfg, folder = split_mission
    cfg['data']['files']['robot8'] = 'absent.csv'
    with pytest.raises(ValueError, match='absent.csv.*encontrados 0'):
        load_mission(cfg, folder)


def test_extra_archive_paths_requires_a_list(split_mission):
    cfg, folder = split_mission
    cfg['data']['extra_zip_paths'] = 'extra.zip'
    with pytest.raises(ValueError, match='extra_zip_paths.*lista'):
        load_mission(cfg, folder)
