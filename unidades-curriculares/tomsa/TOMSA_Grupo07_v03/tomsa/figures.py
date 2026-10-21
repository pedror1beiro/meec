"""Vistas cartesianas interativas global NED e local body/NED relativo."""
from __future__ import annotations
import numpy as np
import plotly.graph_objects as go
from scipy.spatial.transform import Rotation
from .coordinates import world_to_robot
from .replay import orientation_is_usable

BACKGROUND = '#ffffff'
FG = '#17263c'
GRID = '#e5eaf1'


def _base_figure(title, xaxis, yaxis):
    """Tema claro para as duas vistas 2D: alto contraste e legenda abaixo."""
    fig = go.Figure()
    fig.update_layout(
        title=dict(text=title, x=0.04, y=0.97,
                   font=dict(size=16, color=FG)),
        template='plotly_white',
        paper_bgcolor=BACKGROUND,
        plot_bgcolor=BACKGROUND,
        font=dict(color=FG, family='Arial, sans-serif', size=12),
        margin=dict(l=76, r=24, t=88, b=105),
        showlegend=True,
        legend=dict(
            orientation='h', x=0, y=-0.26,
            yanchor='top', xanchor='left',
            font=dict(size=11, color=FG),
            bgcolor='rgba(255,255,255,0)',
        ),
        xaxis=dict(title=xaxis, showline=True, linecolor='#aab7ca',
                   zeroline=True, zerolinecolor='#aab7ca', gridcolor=GRID),
        yaxis=dict(title=yaxis, showline=True, linecolor='#aab7ca',
                   zeroline=True, zerolinecolor='#aab7ca', gridcolor=GRID,
                   scaleanchor='x', scaleratio=1),
        uirevision='keep',
    )
    return fig

def _history(trace, time_ns, max_points):
    end = int(np.searchsorted(trace.times_ns, time_ns, side='right'))
    if end <= 0:
        return np.empty((0, 3))
    step = max(1, int(np.ceil(end / max_points)))
    indices = np.arange(0, end, step)
    if indices[-1] != end - 1:
        indices = np.append(indices, end - 1)
    return trace.positions_ned[indices]


def _add_heading(fig, start_xy, direction_xy, color):
    direction_xy = np.asarray(direction_xy, dtype=float)
    norm = np.linalg.norm(direction_xy)
    if norm < 1e-8:
        return
    final = np.asarray(start_xy) + 8.0 * direction_xy / norm
    fig.add_annotation(x=float(final[0]), y=float(final[1]),
                       ax=float(start_xy[0]), ay=float(start_xy[1]),
                       xref='x', yref='y', axref='x', ayref='y',
                       arrowhead=3, arrowsize=1.2, arrowwidth=2.8,
                       arrowcolor=color, showarrow=True)


def global_figure(mission, state, time_ns, cfg):
    fig = _base_figure('Vista global · NED relativo à origem geográfica', 'Este (m)', 'Norte (m)')
    max_points = cfg['replay']['max_plot_points_per_robot']
    assumed_frame = cfg['orientation']['assumed_body_to_ned_frame_id']
    for key, trace in mission.traces.items():
        past = _history(trace, time_ns, max_points)
        if len(past):
            fig.add_trace(go.Scatter(x=past[:, 1], y=past[:, 0], mode='lines',
                         name=f'Trajetória · {trace.label}', line=dict(color=trace.color, width=2)))
        snap = state[key]
        if snap is None:
            continue
        p = snap.position_ned
        fig.add_trace(go.Scatter(x=[p[1]], y=[p[0]], mode='markers+text',
                      marker=dict(color=trace.color, size=12, line=dict(color='white', width=1)),
                      text=[trace.label], textposition='top center', showlegend=False,
                      hovertemplate=f'{trace.label}<br>Este: %{{x:.2f}} m<br>Norte: %{{y:.2f}} m<br>Down: {p[2]:.2f} m<extra></extra>'))
        if orientation_is_usable(snap, assumed_frame):
            fwd = Rotation.from_quat(snap.quaternion_xyzw).apply([1.0, 0.0, 0.0])
            _add_heading(fig, p[[1, 0]], fwd[[1, 0]], trace.color)
    return fig


def local_figure(mission, state, time_ns, central_key, cfg, radius_override=None):
    radius = float(cfg['replay']['proximity_radius_m'] if radius_override is None else radius_override)
    central = state.get(central_key)
    assumed_frame = cfg['orientation']['assumed_body_to_ned_frame_id']
    rotated = orientation_is_usable(central, assumed_frame)
    label = mission.traces[central_key].label
    if rotated:
        fig = _base_figure(f'Local · corpo do {label} (hipótese não validada)',
                           'Eixo Y do robô (m; hipótese)', 'Eixo X do robô (m; hipótese)')
    else:
        fig = _base_figure(f'Relativo · NED centrado no {label} (sem rotação)',
                           'Este relativo (m)', 'Norte relativo (m)')
    if central is None:
        fig.add_annotation(text='Sem amostra temporal do robô selecionado',
                           xref='paper', yref='paper', x=.5, y=.5, showarrow=False)
        return fig
    max_points = cfg['replay']['max_plot_points_per_robot']
    for key, trace in mission.traces.items():
        snap = state[key]
        if snap is None:
            continue
        dist = float(np.linalg.norm(snap.position_ned - central.position_ned))
        if key != central_key and dist > radius:
            continue
        past = _history(trace, time_ns, max_points)
        if len(past):
            transformed = (world_to_robot(past, central.position_ned, central.quaternion_xyzw)
                           if rotated else past - central.position_ned)
            fig.add_trace(go.Scatter(x=transformed[:, 1], y=transformed[:, 0], mode='lines',
                            name=f'Trajetória · {trace.label}', line=dict(color=trace.color, width=2)))
        p = (world_to_robot(snap.position_ned, central.position_ned, central.quaternion_xyzw)
             if rotated else snap.position_ned - central.position_ned)
        fig.add_trace(go.Scatter(x=[p[1]], y=[p[0]], mode='markers+text',
                        name=trace.label, showlegend=False,
                        marker=dict(color=trace.color, size=12,
                                                       line=dict(color='white', width=1)),
                        text=[trace.label], textposition='top center',
                        hovertemplate=f'{trace.label}<br>X horizontal: %{{x:.2f}} m<br>Y vertical: %{{y:.2f}} m<extra></extra>'))
        if rotated and orientation_is_usable(snap, assumed_frame):
            heading_world = Rotation.from_quat(snap.quaternion_xyzw).apply([1.0, 0.0, 0.0])
            tip = world_to_robot(snap.position_ned + heading_world,
                                 central.position_ned, central.quaternion_xyzw)
            _add_heading(fig, p[[1, 0]], (tip - p)[[1, 0]], trace.color)
    if not rotated:
        fig.add_annotation(text='Orientação desconhecida: apenas translação NED',
                           xref='paper', yref='paper', x=0.5, y=.01, showarrow=False,
                           font=dict(color='#9a5a12', size=11), bgcolor='#fff4de')
    return fig


def global_figure_3d(mission, state, time_ns, cfg):
    """Vista global 3D NED: coordenadas x=Este, y=Norte, z=Baixo (m).

    Usa os mesmos dados que a vista 2D, sem alterar a origem ou as unidades.
    """
    fig = go.Figure()
    max_points = cfg['replay']['max_plot_points_per_robot']
    assumed_frame = cfg['orientation']['assumed_body_to_ned_frame_id']
    for key, trace in mission.traces.items():
        past = _history(trace, time_ns, max_points)
        if len(past):
            fig.add_trace(go.Scatter3d(
                x=past[:, 1], y=past[:, 0], z=past[:, 2],
                mode='lines', name=f'Trajetória · {trace.label}',
                line=dict(color=trace.color, width=4)))
        snap = state[key]
        if snap is None:
            continue
        p = snap.position_ned
        fig.add_trace(go.Scatter3d(
            x=[p[1]], y=[p[0]], z=[p[2]],
            mode='markers+text', name=trace.label, showlegend=False,
            text=[trace.label], textposition='top center',
            marker=dict(color=trace.color, size=6),
            hovertemplate=(f'{trace.label}<br>Este: %{{x:.2f}} m'
                           '<br>Norte: %{y:.2f} m<br>Baixo: %{z:.2f} m<extra></extra>')))
        if orientation_is_usable(snap, assumed_frame):
            # Vetor do eixo X do corpo, apenas sob a hipótese corpo -> NED.
            q = snap.quaternion_xyzw
            forward = Rotation.from_quat(q).apply([1.0, 0.0, 0.0])
            tip = p + 8.0 * forward
            fig.add_trace(go.Scatter3d(
                x=[p[1], tip[1]], y=[p[0], tip[0]], z=[p[2], tip[2]],
                mode='lines', line=dict(color=trace.color, width=6),
                showlegend=False, hoverinfo='skip'))
    fig.update_layout(
        title=dict(text='Vista global · 3D NED (orientações provisórias)',
                   x=0.04, y=0.97, font=dict(size=16, color=FG)),
        template='plotly_white', paper_bgcolor=BACKGROUND, plot_bgcolor=BACKGROUND,
        font=dict(color=FG, family='Arial, sans-serif', size=12),
        margin=dict(l=18, r=18, t=85, b=100),
        legend=dict(
            orientation='h', x=0, y=-0.20, yanchor='top',
            font=dict(size=11, color=FG),
            bgcolor='rgba(255,255,255,0)',
        ),
        scene=dict(
            xaxis=dict(title='Este (m)', backgroundcolor=BACKGROUND,
                       gridcolor=GRID, zerolinecolor='#aab7ca', color=FG),
            yaxis=dict(title='Norte (m)', backgroundcolor=BACKGROUND,
                       gridcolor=GRID, zerolinecolor='#aab7ca', color=FG),
            zaxis=dict(title='Baixo (m)', backgroundcolor=BACKGROUND,
                       gridcolor=GRID, zerolinecolor='#aab7ca', color=FG),
            aspectmode='data',
            camera=dict(eye=dict(x=1.35, y=1.35, z=1.1)),
        ),
        uirevision='keep-3d',
    )
    return fig
