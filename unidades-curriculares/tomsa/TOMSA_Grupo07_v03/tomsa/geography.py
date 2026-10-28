"""Dados geográficos para MapLibre: trajetórias uma vez, poses por frame."""
from __future__ import annotations
from .coordinates import geographic_heading

DEFAULT_MAP = {
    'base_tiles_url': 'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
    'base_attribution': '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap contributors</a>',
    'seamark_tiles_url': 'https://t1.openseamap.org/seamark/{z}/{x}/{y}.png',
    'seamark_attribution': '© <a href="https://www.openseamap.org">OpenSeaMap contributors</a>',
    'ocean_surface': True,
    'ocean_tiles_url': 'https://tiles.openfreemap.org/planet/latest',
}


def map_mission_data(mission, cfg):
    features = []
    timeline_s = {}
    west, south, east, north = 180., 90., -180., -90.
    for key, trace in mission.traces.items():
        # GeoJSON usa [longitude, latitude], sem converter ou estimar posições.
        coordinates = [[float(lon), float(lat)]
                       for lon, lat in zip(trace.longitude, trace.latitude)]
        west = min(west, float(trace.longitude.min()))
        east = max(east, float(trace.longitude.max()))
        south = min(south, float(trace.latitude.min()))
        north = max(north, float(trace.latitude.max()))
        features.append({'type': 'Feature', 'properties': {
            'robot': key, 'label': trace.label, 'color': trace.color},
            'geometry': {'type': 'LineString', 'coordinates': coordinates}})
        # JS não representa épocas em ns com exatidão: subtrair primeiro em int64.
        timeline_s[key] = ((trace.times_ns-mission.start_ns) / 1e9).tolist()
    return {'trajectories': {'type': 'FeatureCollection', 'features': features},
            'timeline_s': timeline_s,
            'bounds': [[west, south], [east, north]],
            'settings': {**DEFAULT_MAP, **cfg.get('map', {}),
                         'trail_max_gap_seconds': cfg.get('kinematics', {}).get('max_gap_seconds', 2.0)}}


def map_frame_data(mission, state, central_key, cfg=None, radius_m=None):
    """Payload pequeno; uma ausência temporal remove o marcador, sem o congelar."""
    robots = []
    for key, snap in state.items():
        if snap is None:
            continue
        trace = mission.traces[key]
        lon, lat = float(trace.longitude[snap.index]), float(trace.latitude[snap.index])
        heading = None
        if snap.body_to_ned_confirmed and cfg is not None:
            ref = cfg['reference']
            heading = geographic_heading(snap.quaternion_xyzw, lat, lon,
                                         ref['latitude_deg'], ref['longitude_deg'])
        robots.append({'robot': key, 'longitude': lon, 'latitude': lat,
                       'sample_index': int(snap.index), 'heading_deg': heading})
    return {'selected': central_key, 'robots': robots, 'radius_m': radius_m}
