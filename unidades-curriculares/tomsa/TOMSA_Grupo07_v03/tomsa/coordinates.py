"""Transformações geodésicas WGS84 → ECEF → NED → referencial do robô.

Convenção NED: x=Norte, y=Este, z=Baixo. Os quaterniões seguem (x,y,z,w).
A orientação só pode ser aplicada quando o frame e o sentido da rotação
estiverem confirmados; o nome do frame, por si só, não prova a convenção.
"""
from __future__ import annotations
import numpy as np
from scipy.spatial.transform import Rotation

WGS84_A = 6378137.0
WGS84_F = 1.0 / 298.257223563
WGS84_E2 = WGS84_F * (2.0 - WGS84_F)


def geodetic_to_ecef(lat_deg, lon_deg, altitude_m):
    """De latitude/longitude em graus e altura elipsoidal em m para ECEF em m.

    Aceita escalares ou arrays compatíveis (broadcasting).
    """
    lat = np.deg2rad(np.asarray(lat_deg, dtype=float))
    lon = np.deg2rad(np.asarray(lon_deg, dtype=float))
    alt = np.asarray(altitude_m, dtype=float)
    s_lat, c_lat = np.sin(lat), np.cos(lat)
    radius = WGS84_A / np.sqrt(1.0 - WGS84_E2 * s_lat**2)
    x = (radius + alt) * c_lat * np.cos(lon)
    y = (radius + alt) * c_lat * np.sin(lon)
    z = (radius * (1.0 - WGS84_E2) + alt) * s_lat
    return np.stack(np.broadcast_arrays(x, y, z), axis=-1)


def ecef_to_ned(ecef, reference_lat_deg, reference_lon_deg, reference_alt_m):
    """ECEF (m) → NED (m) relativamente à origem geodésica fixa."""
    p = np.asarray(ecef, dtype=float)
    ref = geodetic_to_ecef(reference_lat_deg, reference_lon_deg, reference_alt_m)
    return (p - ref) @ ecef_to_ned_rotation(reference_lat_deg, reference_lon_deg).T


def ecef_to_ned_rotation(latitude_deg, longitude_deg):
    """Matriz ortonormal de mudança de base ECEF -> NED tangente local."""
    lat, lon = np.deg2rad([latitude_deg, longitude_deg])
    sl, cl = np.sin(lat), np.cos(lat)
    so, co = np.sin(lon), np.cos(lon)
    return np.array([
        [-sl * co, -sl * so, cl],
        [-so, co, 0.0],
        [-cl * co, -cl * so, -sl],
    ])


def geographic_heading(quaternion_xyzw, latitude_deg, longitude_deg, ref_lat_deg, ref_lon_deg):
    """Rumo horário desde Norte verdadeiro, para corpo -> NED FIXO confirmado.

    Transporta o eixo X do corpo através de ECEF para o NED tangente no robô;
    um eixo vertical não define rumo. Não é course-over-ground nem yaw ENU.
    """
    q = np.asarray(quaternion_xyzw, dtype=float)
    norm = np.linalg.norm(q)
    if not np.isfinite(norm) or norm < 1e-12:
        raise ValueError('Quaternion inválido.')
    forward_ned = Rotation.from_quat(q / norm).apply([1., 0., 0.])
    forward_ecef = ecef_to_ned_rotation(ref_lat_deg, ref_lon_deg).T @ forward_ned
    forward_local = ecef_to_ned_rotation(latitude_deg, longitude_deg) @ forward_ecef
    if np.hypot(*forward_local[:2]) < 1e-8:
        return None
    return float(np.degrees(np.arctan2(forward_local[1], forward_local[0])) % 360)


def geodetic_to_ned(lat_deg, lon_deg, altitude_m, ref_lat_deg, ref_lon_deg, ref_alt_m):
    return ecef_to_ned(
        geodetic_to_ecef(lat_deg, lon_deg, altitude_m),
        ref_lat_deg, ref_lon_deg, ref_alt_m,
    )


def world_to_robot(points_ned, robot_position_ned, robot_quat_xyzw):
    """Expressa ponto(s) NED no corpo do robô: p_body = R⁻¹ (p_ned-p0).

    Premissa: quaternion representa a rotação corpo → NED.
    """
    delta = np.asarray(points_ned, dtype=float) - np.asarray(robot_position_ned, dtype=float)
    q = np.asarray(robot_quat_xyzw, dtype=float)
    norm = np.linalg.norm(q)
    if not np.isfinite(norm) or norm < 1e-12:
        raise ValueError('Quaternion inválido.')
    rotation = Rotation.from_quat(q / norm)
    return rotation.inv().apply(delta)


def robot_to_world(points_body, robot_position_ned, robot_quat_xyzw):
    """Inversa de world_to_robot, com a mesma hipótese corpo -> NED."""
    q = np.asarray(robot_quat_xyzw, dtype=float)
    norm = np.linalg.norm(q)
    if not np.isfinite(norm) or norm < 1e-12:
        raise ValueError('Quaternion inválido.')
    return Rotation.from_quat(q / norm).apply(
        np.asarray(points_body, dtype=float)
    ) + np.asarray(robot_position_ned, dtype=float)


def ned_to_aer(delta_ned):
    """NED relativo (m) -> azimute (deg, desde Norte, sentido horário),
    elevação (deg, positiva para cima), distância 3D (m).

    Na origem (distância zero), azimute e elevação são indefinidos (nan).
    """
    delta = np.asarray(delta_ned, dtype=float)
    north, east, down = np.moveaxis(delta, -1, 0)
    horizontal = np.hypot(north, east)
    distance = np.hypot(horizontal, down)
    azimuth = np.mod(np.degrees(np.arctan2(east, north)), 360.0)
    elevation = np.degrees(np.arctan2(-down, horizontal))
    azimuth = np.where(distance > 1e-9, azimuth, np.nan)
    elevation = np.where(distance > 1e-9, elevation, np.nan)
    return azimuth, elevation, distance
