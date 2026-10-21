"""Leitura de dados ROS-like a partir do ZIP ou geração de missão demo."""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from zipfile import ZipFile
import numpy as np
import pandas as pd
import yaml
from scipy.spatial.transform import Rotation
from .coordinates import geodetic_to_ned

POS_COLS = [f'pose.pose.position.{axis}' for axis in 'xyz']
QUAT_COLS = [f'pose.pose.orientation.{axis}' for axis in 'xyzw']
STAMP_COLS = ['header.stamp.secs', 'header.stamp.nsecs']
REQUIRED_COLS = POS_COLS + QUAT_COLS + STAMP_COLS + ['header.frame_id']


@dataclass
class RobotTrace:
    key: str
    label: str
    color: str
    times_ns: np.ndarray
    positions_ned: np.ndarray
    quaternions_xyzw: np.ndarray
    frames: np.ndarray
    latitude: np.ndarray
    longitude: np.ndarray
    altitude: np.ndarray


@dataclass
class Mission:
    traces: dict[str, RobotTrace]
    start_ns: int
    end_ns: int
    source: str

    @property
    def duration_s(self):
        return (self.end_ns - self.start_ns) / 1e9


def load_config(path):
    path = Path(path)
    with path.open(encoding='utf-8') as file:
        cfg = yaml.safe_load(file)
    if not isinstance(cfg, dict):
        raise ValueError('Ficheiro YAML de configuração inválido.')
    return cfg


def _to_trace(key, df, cfg):
    missing = sorted(set(REQUIRED_COLS) - set(df.columns))
    if missing:
        raise ValueError(f'{key}: faltam colunas obrigatórias: {missing}')
    fields = df[POS_COLS + QUAT_COLS + STAMP_COLS].apply(pd.to_numeric, errors='coerce')
    valid = np.isfinite(fields.to_numpy()).all(axis=1)
    if not valid.all():
        # Não inventar posições ou orientações para registos incompletos.
        df = df.loc[valid].reset_index(drop=True)
        fields = fields.loc[valid].reset_index(drop=True)
    if len(df) < 2:
        raise ValueError(f'{key}: registos válidos insuficientes.')
    seconds = fields[STAMP_COLS[0]].to_numpy(dtype=np.int64)
    nanos = fields[STAMP_COLS[1]].to_numpy(dtype=np.int64)
    if ((nanos < 0) | (nanos >= 1_000_000_000)).any():
        raise ValueError(f'{key}: nanosegundos fora do intervalo.')
    times = seconds * 1_000_000_000 + nanos
    order = np.argsort(times, kind='stable')
    if np.any(np.diff(times[order]) <= 0):
        raise ValueError(f'{key}: timestamps repetidos; é necessário resolver duplicados.')
    coords = fields[POS_COLS].to_numpy()[order]
    quat = fields[QUAT_COLS].to_numpy()[order]
    norms = np.linalg.norm(quat, axis=1)
    if np.any(norms < 1e-10):
        raise ValueError(f'{key}: quaterniões de norma zero.')
    quat = quat / norms[:, None]
    ref = cfg['reference']
    ned = geodetic_to_ned(coords[:, 0], coords[:, 1], coords[:, 2],
                          ref['latitude_deg'], ref['longitude_deg'], ref['altitude_m'])
    label_info = cfg['robots'][key]
    return RobotTrace(key, label_info['label'], label_info['color'], times[order], ned,
                      quat, df['header.frame_id'].fillna('').astype(str).to_numpy()[order],
                      coords[:, 0], coords[:, 1], coords[:, 2])


def _load_zip(cfg, config_dir):
    src = Path(cfg['data']['zip_path'])
    if not src.is_absolute():
        src = config_dir / src
    if not src.is_file():
        raise FileNotFoundError(f'ZIP não encontrado: {src}. Colocar o ficheiro e mudar data.mode para zip.')
    result = {}
    with ZipFile(src) as z:
        for key, filename in cfg['data']['files'].items():
            # ZIP pode conter um diretório raiz; encontrar pelo nome sem ambiguidade.
            matches = [entry for entry in z.namelist() if Path(entry).name == filename]
            if len(matches) != 1:
                raise ValueError(f'{filename}: esperava um único CSV no ZIP; encontrados {len(matches)}.')
            with z.open(matches[0]) as file:
                result[key] = pd.read_csv(file)
    return result


def _demo_frames(cfg):
    """Dados SINTÉTICOS em pequena área para exercício de matemática e interface.

    Não representam a missão real nem contêm dados fornecidos pelo docente.
    """
    base_ns = 1_760_000_000_000_000_000
    t_s = np.arange(0.0, 180.5, 0.5)
    base_lat = cfg['reference']['latitude_deg']
    base_lon = cfg['reference']['longitude_deg']
    base_alt = cfg['reference']['altitude_m']
    demo = {}
    for k, key in enumerate(cfg['data']['files']):
        # Desenhar trajetos suaves em componentes norte/este (m).
        phase = 2 * np.pi * k / 3
        north_m = 35 * np.cos(t_s / 35 + phase) + 0.22 * t_s + 7 * k
        east_m = 42 * np.sin(t_s / 35 + phase) + 12 * k
        # Aproximação local usada só para CRIAR a missão sintética.
        lat = base_lat + north_m / 111_050
        lon = base_lon + east_m / (111_050 * np.cos(np.deg2rad(base_lat)))
        alt = base_alt + 1.5 * np.sin(t_s / 40 + phase)
        north_v = np.gradient(north_m, t_s)
        east_v = np.gradient(east_m, t_s)
        # Yaw no NED é medido de Norte para Este.
        yaw = np.arctan2(east_v, north_v)
        quat = Rotation.from_euler('z', yaw.reshape(-1, 1)).as_quat()
        times_ns = base_ns + np.rint(t_s * 1e9).astype(np.int64)
        frame = {'header.stamp.secs': times_ns // 1_000_000_000,
                 'header.stamp.nsecs': times_ns % 1_000_000_000,
                 'header.frame_id': ['world_ned'] * len(t_s)}
        for name, vals in zip(POS_COLS, [lat, lon, alt]):
            frame[name] = vals
        for i, name in enumerate(QUAT_COLS):
            frame[name] = quat[:, i]
        demo[key] = pd.DataFrame(frame)
    return demo


def load_mission(cfg, config_dir='.'): 
    mode = cfg['data']['mode']
    if mode == 'demo':
        frames = _demo_frames(cfg)
        source = 'DEMONSTRAÇÃO — dados sintéticos, não são os logs reais'
    elif mode == 'zip':
        frames = _load_zip(cfg, Path(config_dir))
        source = 'DADOS REAIS — ZIP fornecido para a UC'
    else:
        raise ValueError("data.mode deve ser 'demo' ou 'zip'.")
    traces = {key: _to_trace(key, frame, cfg) for key, frame in frames.items()}
    start = max(int(trace.times_ns[0]) for trace in traces.values())
    end = min(int(trace.times_ns[-1]) for trace in traces.values())
    if end <= start:
        raise ValueError('Não existe intervalo temporal comum aos três robôs.')
    return Mission(traces, start, end, source)
