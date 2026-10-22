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
from .kinematics import Kinematics, compute_kinematics

POS_COLS = [f'pose.pose.position.{axis}' for axis in 'xyz']
QUAT_COLS = [f'pose.pose.orientation.{axis}' for axis in 'xyzw']
STAMP_COLS = ['header.stamp.secs', 'header.stamp.nsecs']
REQUIRED_COLS = POS_COLS + QUAT_COLS + STAMP_COLS + ['header.frame_id']
LINEAR_COLS = [f'twist.twist.linear.{axis}' for axis in 'xyz']
ANGULAR_COLS = [f'twist.twist.angular.{axis}' for axis in 'xyz']


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
    child_frames: np.ndarray | None = None
    linear_velocity_m_s: np.ndarray | None = None
    angular_velocity_rad_s: np.ndarray | None = None
    kinematics: Kinematics | None = None
    confirmed_body_to_ned_frame_id: str | None = None


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
    if not np.equal(fields[STAMP_COLS].to_numpy(), np.column_stack([seconds, nanos])).all():
        raise ValueError(f'{key}: timestamps devem conter segundos/nanosegundos inteiros.')
    if ((nanos < 0) | (nanos >= 1_000_000_000)).any():
        raise ValueError(f'{key}: nanosegundos fora do intervalo.')
    times = seconds * 1_000_000_000 + nanos
    order = np.argsort(times, kind='stable')
    if np.any(np.diff(times[order]) <= 0):
        raise ValueError(f'{key}: timestamps repetidos; é necessário resolver duplicados.')
    coords = fields[POS_COLS].to_numpy()[order]
    if (np.abs(coords[:, 0]) > 90).any() or (np.abs(coords[:, 1]) > 180).any():
        raise ValueError(f'{key}: latitude/longitude fora do intervalo geográfico.')
    quat = fields[QUAT_COLS].to_numpy()[order]
    norms = np.linalg.norm(quat, axis=1)
    if np.any(~np.isfinite(norms) | (norms < 1e-10)):
        raise ValueError(f'{key}: quaterniões de norma zero ou inválida.')
    quat = quat / norms[:, None]
    ref = cfg['reference']
    ned = geodetic_to_ned(coords[:, 0], coords[:, 1], coords[:, 2],
                          ref['latitude_deg'], ref['longitude_deg'], ref['altitude_m'])
    label_info = cfg['robots'][key]
    frames = df['header.frame_id'].fillna('').astype(str).to_numpy()[order]
    child_frames = (df['child_frame_id'].fillna('').astype(str).to_numpy()[order]
                    if 'child_frame_id' in df else np.full(len(df), '', dtype=object))
    def optional_vector(columns):
        if not set(columns).issubset(df.columns):
            return np.full((len(df), 3), np.nan)
        vector = df[columns].apply(pd.to_numeric, errors='coerce').to_numpy(dtype=float)[order]
        vector[~np.isfinite(vector).all(axis=1)] = np.nan
        return vector
    linear = optional_vector(LINEAR_COLS)
    angular = optional_vector(ANGULAR_COLS)
    # A demo tem uma convenção conhecida por construção. Nos logs reais só uma
    # confirmação explícita na configuração autoriza conversões físicas.
    demo = cfg['data']['mode'] == 'demo'
    confirmed_frame = ('world_ned' if demo else
                       cfg.get('orientation', {}).get('confirmed_body_to_ned_frame_id'))
    settings = cfg.get('kinematics', {})
    velocity_frame = 'ned' if demo else settings.get('confirmed_velocity_frame', 'unknown')
    if velocity_frame not in ('unknown', 'body', 'ned'):
        raise ValueError('confirmed_velocity_frame deve ser unknown, body ou ned.')
    velocity_ned = np.full_like(linear, np.nan)
    if velocity_frame == 'ned':
        velocity_ned[:] = linear
    elif velocity_frame == 'body' and confirmed_frame:
        body_frame = settings.get('body_frame_id', 'body')
        usable = (frames == confirmed_frame) & (child_frames == body_frame) & np.isfinite(linear).all(axis=1)
        if usable.any():
            velocity_ned[usable] = Rotation.from_quat(quat[usable]).apply(linear[usable])
    kinematics = compute_kinematics(times[order], linear, velocity_ned,
                                    settings.get('max_gap_seconds', 2.0))
    return RobotTrace(key, label_info['label'], label_info['color'], times[order], ned,
                      quat, frames, coords[:, 0], coords[:, 1], coords[:, 2],
                      child_frames, linear, angular, kinematics, confirmed_frame)


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
                 'header.frame_id': ['world_ned'] * len(t_s),
                 'child_frame_id': ['body'] * len(t_s)}
        for name, vals in zip(POS_COLS, [lat, lon, alt]):
            frame[name] = vals
        for i, name in enumerate(QUAT_COLS):
            frame[name] = quat[:, i]
        # Velocidades sintéticas explicitamente na base NED fixa comum.
        ned = geodetic_to_ned(lat, lon, alt, base_lat, base_lon, base_alt)
        for i, name in enumerate(LINEAR_COLS):
            frame[name] = np.gradient(ned[:, i], t_s, edge_order=2)
        for i, name in enumerate(ANGULAR_COLS):
            frame[name] = np.gradient(np.unwrap(yaw), t_s) if i == 2 else np.zeros_like(t_s)
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
