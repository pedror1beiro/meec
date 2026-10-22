from pathlib import Path
import pytest
from tomsa.data import load_config, load_mission

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope='session')
def real_mission_and_config():
    cfg = load_config(ROOT / 'config.yaml')
    cfg['data']['mode'] = 'zip'
    path = Path(cfg['data']['zip_path'])
    if not (path if path.is_absolute() else ROOT / path).is_file():
        pytest.skip('ZIP restrito ausente; testes de dados reais são opcionais.')
    return load_mission(cfg, ROOT), cfg


@pytest.fixture(scope='session')
def demo_mission_and_config():
    cfg = load_config(ROOT / 'config.yaml')
    cfg['data']['mode'] = 'demo'
    return load_mission(cfg, ROOT), cfg
