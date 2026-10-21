"""Reprodução por amostra temporal mais próxima (sem interpolação)."""
from __future__ import annotations
from dataclasses import dataclass
import numpy as np
from .coordinates import world_to_robot, ned_to_aer


@dataclass
class Snapshot:
    index: int
    time_ns: int
    position_ned: np.ndarray
    quaternion_xyzw: np.ndarray
    frame_id: str


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
                    trace.quaternions_xyzw[best], str(trace.frames[best]))


def mission_state(mission, time_ns, tolerance_s):
    return {key: nearest_sample(trace, time_ns, tolerance_s)
            for key, trace in mission.traces.items()}


def orientation_is_usable(snapshot, assumed_frame_id):
    """Apenas seleção de uma HIPÓTESE de orientação, não validação física."""
    return snapshot is not None and snapshot.frame_id == assumed_frame_id


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
    reference_name = 'robot_body_assumed' if rotated else 'ned_translated'
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
