"""Reprodução por amostra temporal mais próxima (sem interpolação)."""
from __future__ import annotations
from dataclasses import dataclass
from itertools import combinations
import numpy as np
from scipy.spatial.transform import Rotation
from .coordinates import world_to_robot, ned_to_aer


@dataclass
class Snapshot:
    index: int
    time_ns: int
    position_ned: np.ndarray
    quaternion_xyzw: np.ndarray
    frame_id: str
    body_to_ned_confirmed: bool = False


def nearest_sample(trace, time_ns, tolerance_s):
    times = trace.times_ns
    i = int(np.searchsorted(times, time_ns))
    candidates = [j for j in (i - 1, i) if 0 <= j < len(times)]
    if not candidates:
        return None
    best = min(candidates, key=lambda j: abs(int(times[j]) - int(time_ns)))
    if abs(int(times[best]) - int(time_ns)) > tolerance_s * 1e9:
        return None
    return Snapshot(best, int(times[best]), trace.positions_ned[best],
                    trace.quaternions_xyzw[best], str(trace.frames[best]),
                    bool(trace.confirmed_body_to_ned_frame_id and
                         trace.frames[best] == trace.confirmed_body_to_ned_frame_id))


def mission_state(mission, time_ns, tolerance_s):
    return {key: nearest_sample(trace, time_ns, tolerance_s)
            for key, trace in mission.traces.items()}


def orientation_is_usable(snapshot, assumed_frame_id):
    """Aceita orientação confirmada ou a hipótese explicitamente configurada.

    Esta seleção, por si só, não confirma fisicamente uma convenção.
    """
    return snapshot is not None and (snapshot.body_to_ned_confirmed or
                                     bool(assumed_frame_id and snapshot.frame_id == assumed_frame_id))


def local_positions(state, origin_key, assumed_frame_id):
    """Corpo selecionado se assumido; senão NED transladado sem rotação.

    Retorna (posições, usa_rotacao) para diferenciar os referenciais na UI.
    """
    origin = state.get(origin_key)
    if origin is None:
        raise ValueError('Sem pose do robô central.')
    rotated = orientation_is_usable(origin, assumed_frame_id)
    points = {}
    for key, s in state.items():
        if s is None:
            continue
        if rotated:
            points[key] = world_to_robot(s.position_ned, origin.position_ned,
                                         origin.quaternion_xyzw)
        else:
            points[key] = s.position_ned - origin.position_ned
    return points, rotated


def relative_aer(state, origin_key):
    """Observações AER geográficas desde o robô central; independentes da orientação."""
    central = state.get(origin_key)
    if central is None:
        return []
    rows = []
    for key, s in state.items():
        if key == origin_key or s is None:
            continue
        delta = s.position_ned - central.position_ned
        az, el, rng = ned_to_aer(delta)
        rows.append({'robot': key, 'azimuth_deg': float(az),
                     'elevation_deg': float(el), 'range_m': float(rng),
                     'north_m': float(delta[0]), 'east_m': float(delta[1]),
                     'down_m': float(delta[2])})
    return rows


def frame_diagnostics(state, origin_key, assumed_frame_id):
    """Invariantes do MESMO conjunto de amostras, sem filtrar por proximidade.

    T_ned_local = [R,t; 0,1], p_local = R.T (p_ned-t). Uma rotação
    matematicamente válida não confirma a interpretação física do quaternion.
    Todos os erros são calculados antes do arredondamento de apresentação.
    """
    origin = state.get(origin_key)
    if origin is None:
        return None
    positions, rotated = local_positions(state, origin_key, assumed_frame_id)
    rotation = (Rotation.from_quat(origin.quaternion_xyzw).as_matrix()
                if rotated else np.eye(3))
    keys = list(positions)
    world = np.array([state[key].position_ned for key in keys])
    local = np.array([positions[key] for key in keys])
    transform = np.eye(4)
    transform[:3, :3], transform[:3, 3] = rotation, origin.position_ned
    inverse = np.eye(4)
    inverse[:3, :3] = rotation.T
    inverse[:3, 3] = -rotation.T @ origin.position_ned
    pairs = []
    for i, j in combinations(range(len(keys)), 2):
        d_world = float(np.linalg.norm(world[i] - world[j]))
        d_local = float(np.linalg.norm(local[i] - local[j]))
        pairs.append({'robots': (keys[i], keys[j]), 'ned_m': d_world,
                      'local_m': d_local, 'error_m': abs(d_world-d_local)})
    restored = local @ rotation.T + origin.position_ned
    roundtrip_error = float(np.max(np.linalg.norm(restored-world, axis=1)))
    orthogonality_error = float(np.linalg.norm(rotation.T @ rotation-np.eye(3), ord='fro'))
    determinant = float(np.linalg.det(rotation))
    distances_match = all(np.isclose(p['ned_m'], p['local_m'], atol=1e-8, rtol=1e-12) for p in pairs)
    checks_pass = (orthogonality_error < 1e-12 and abs(determinant-1) < 1e-12
                   and np.allclose(restored, world, atol=1e-8, rtol=1e-12) and distances_match)
    frame = ('robot_body_confirmed' if origin.body_to_ned_confirmed else
             'robot_body_assumed') if rotated else 'ned_translated'
    return {'keys': keys, 'world': world, 'local': local, 'transform': transform,
            'inverse': inverse, 'pairs': pairs, 'frame': frame,
            'orthogonality_error': orthogonality_error, 'determinant': determinant,
            'roundtrip_error_m': roundtrip_error, 'checks_pass': bool(checks_pass)}


def next_step(current_step, total_steps):
    """Avança um passo; no último passo, pára em vez de repetir a missão."""
    if total_steps < 0:
        raise ValueError('Número total de passos inválido.')
    next_index = min(int(current_step or 0) + 1, total_steps)
    return next_index, next_index >= total_steps


def local_snapshot_rows(mission, time_ns, central_key, tolerance_s, assumed_frame_id):
    """Tabela exportável das posições relativas no instante selecionado.

    Usa R(q)^T somente se o frame corresponder à HIPÓTESE configurada.
    A coordenada [0,0,0] do robô central permanece explícita.
    """
    state = mission_state(mission, time_ns, tolerance_s)
    center = state.get(central_key)
    if center is None:
        return []
    positions, rotated = local_positions(state, central_key, assumed_frame_id)
    reference_name = ('robot_body_confirmed' if center.body_to_ned_confirmed else
                      'robot_body_assumed') if rotated else 'ned_translated'
    rows = []
    for key, position in positions.items():
        snap = state[key]
        rows.append({
            'timestamp_selected_ns': int(time_ns),
            'timestamp_sample_ns': int(snap.time_ns),
            'reference_robot': central_key,
            'robot': key,
            'coordinate_frame': reference_name,
            'local_x_m': float(position[0]),
            'local_y_m': float(position[1]),
            'local_z_m': float(position[2]),
        })
    return rows
