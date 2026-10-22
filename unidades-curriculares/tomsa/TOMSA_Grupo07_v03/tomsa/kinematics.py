"""Cinemática calculada uma vez, usando timestamps em ns e intervalos reais."""
from __future__ import annotations
from dataclasses import dataclass
import numpy as np


@dataclass
class Kinematics:
    speed_m_s: np.ndarray
    speed_rate_m_s2: np.ndarray
    acceleration_ned_m_s2: np.ndarray
    acceleration_magnitude_m_s2: np.ndarray


def differentiate(times_ns, values, max_gap_s=2.0):
    """Gradiente de 3 pontos, não uniforme; extremos unilaterais.

    Cada segmento finito/estritamente crescente é independente. Não derivar
    através de NaN, dt<=0 ou lacunas >max_gap_s; um ponto isolado fica NaN.
    Com dois pontos usa-se a secante. Sem suavização ou interpolação.
    """
    times = np.asarray(times_ns, dtype=np.int64)
    values = np.asarray(values, dtype=float)
    if len(times) != len(values) or values.ndim not in (1, 2):
        raise ValueError('Tempos e valores incompatíveis.')
    if not np.isfinite(max_gap_s) or max_gap_s <= 0:
        raise ValueError('max_gap_seconds deve ser positivo e finito.')
    result = np.full_like(values, np.nan)
    valid = np.isfinite(values).all(axis=1) if values.ndim == 2 else np.isfinite(values)
    start = None
    for i in range(len(times) + 1):
        connected = (i < len(times) and valid[i] and
                     (start is None or 0 < int(times[i]) - int(times[i - 1]) <= max_gap_s * 1e9))
        if start is not None and not connected:
            if i - start >= 2:
                # Subtrair em inteiros ANTES de converter para segundos.
                seconds = (times[start:i] - times[start]).astype(float) / 1e9
                result[start:i] = np.gradient(values[start:i], seconds, axis=0,
                                              edge_order=2 if i - start >= 3 else 1)
            start = None
        if i < len(times) and valid[i] and start is None:
            start = i
    return result


def compute_kinematics(times_ns, linear_velocity_m_s, velocity_ned_m_s=None, max_gap_s=2.0):
    """A norma é invariante a rotações; dv/dt exige uma base fixa confirmada.

    Diferenciar componentes num corpo em rotação não dá aceleração inercial.
    Por isso o argumento NED é opcional, sem estimativa alternativa inventada.
    """
    velocity = np.asarray(linear_velocity_m_s, dtype=float)
    if velocity.shape != (len(times_ns), 3):
        raise ValueError('Velocidade deve ter forma (n, 3).')
    speed = np.linalg.norm(velocity, axis=1)
    speed_rate = differentiate(times_ns, speed, max_gap_s)
    acceleration = (np.full_like(velocity, np.nan) if velocity_ned_m_s is None else
                    differentiate(times_ns, velocity_ned_m_s, max_gap_s))
    return Kinematics(speed, speed_rate, acceleration, np.linalg.norm(acceleration, axis=1))
