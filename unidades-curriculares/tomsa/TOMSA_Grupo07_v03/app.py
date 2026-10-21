"""TOMSA 2026 · Grupo 07 · Reprodução de logs reais em Dash.

Executar: python app.py
"""
from __future__ import annotations
import argparse
import math
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
import pandas as pd
from dash import Dash, Input, Output, State, ctx, dcc, html
from tomsa.data import load_config, load_mission
from tomsa.figures import global_figure, global_figure_3d, local_figure
from tomsa.replay import (mission_state, orientation_is_usable, relative_aer,
                          local_snapshot_rows, next_step)

parser = argparse.ArgumentParser()
parser.add_argument('--config', type=Path, default=Path(__file__).resolve().parent / 'config.yaml')
arguments, _ = parser.parse_known_args()
CFG_PATH = arguments.config.resolve()
CFG = load_config(CFG_PATH)
MISSION = load_mission(CFG, CFG_PATH.parent)
STEP = float(CFG['replay']['step_seconds'])
TOLERANCE = float(CFG['replay']['tolerance_seconds'])
if STEP <= 0 or TOLERANCE < 0:
    raise ValueError('step_seconds deve ser positivo e tolerance_seconds não negativo.')
TOTAL_STEPS = max(1, math.ceil(MISSION.duration_s / STEP))


def time_at(step_index):
    return min(MISSION.end_ns, MISSION.start_ns + int(round(int(step_index) * STEP * 1e9)))


def utc_timestamp(time_ns):
    return datetime.fromtimestamp(time_ns // 1_000_000_000, tz=timezone.utc).strftime('%d/%m/%Y %H:%M:%S')


app = Dash(__name__)
app.title = 'TOMSA · Grupo 07 · Missão Real · v0.3'
COLORS = {'text': '#e8edf4', 'muted': '#a7b4c4', 'bg': '#0b1220', 'panel': '#101827'}
PANEL = {'background': COLORS['panel'], 'padding': '16px', 'borderRadius': '12px'}

app.layout = html.Div([
    html.Div([
        html.H1('TOMSA · Multi-Robot Mission Replay', style={'marginBottom': '5px'}),
        html.Div('ISEP 2026 · Grupo 07 · Versão 0.3', style={'color': COLORS['muted']}),
        html.P(MISSION.source, style={'fontWeight': 'bold', 'color': '#8ee7bc'}),
        html.P(f'Intervalo comum: {utc_timestamp(MISSION.start_ns)} até '
               f'{utc_timestamp(MISSION.end_ns)} UTC · duração {MISSION.duration_s / 60:.1f} min',
               style={'color': COLORS['muted']}),
    ]),
    html.Div([
        html.Div([
            html.Label('Robô de referência'),
            dcc.Dropdown(id='robot-choice', clearable=False, value=next(iter(MISSION.traces)),
                         options=[{'label': trace.label, 'value': key}
                                  for key, trace in MISSION.traces.items()],
                         style={'color': '#1f2937'}),
        ], style={'flex': '1 1 220px'}),
        html.Div([
            html.Label('Raio de proximidade (m)'),
            dcc.Slider(id='radius-slider', min=50, max=600, step=50,
                       value=float(CFG['replay']['proximity_radius_m']),
                       marks={int(x): f'{int(x)}' for x in range(100, 601, 100)}),
        ], style={'flex': '1 1 230px'}),
        html.Div([
            html.Label('Reprodução'),
            html.Div([
                html.Button('▶ Play', id='play-pause', n_clicks=0,
                            style={'padding': '10px 20px', 'cursor': 'pointer'}),
                html.Span(id='clock-label', style={'marginLeft': '12px'}),
            ]),
        ], style={'flex': '2 1 320px'}),
    ], style={**PANEL, 'display': 'flex', 'flexWrap': 'wrap', 'gap': '18px', 'marginBottom': '12px'}),
    html.Div([
        dcc.Slider(id='time-slider', min=0, max=TOTAL_STEPS, value=0, step=1,
                   marks={int(i): f'{i*STEP/60:.0f} min' for i in
                          np.linspace(0, TOTAL_STEPS, min(7, TOTAL_STEPS + 1), dtype=int)},
                   updatemode='mouseup', tooltip={'placement': 'bottom', 'always_visible': False}),
        dcc.Interval(id='replay-timer', interval=max(200, int(STEP * 1000)),
                     n_intervals=0, disabled=True),
    ], style={**PANEL, 'marginBottom': '12px', 'padding': '20px 25px'}),
    html.Div([
        html.Label('Vista global:'),
        dcc.RadioItems(id='global-dimension',
                       options=[{'label': ' 2D', 'value': '2d'},
                                {'label': ' 3D', 'value': '3d'}],
                       value='2d', inline=True,
                       style={'display': 'inline-flex', 'gap': '18px', 'marginLeft': '12px'}),
    ], style={**PANEL, 'marginBottom': '12px'}),
    html.Div([
        html.Div(dcc.Graph(id='global-view', style={'height': '510px'}), style={'flex': '1 1 430px'}),
        html.Div(dcc.Graph(id='local-view', style={'height': '510px'}), style={'flex': '1 1 430px'}),
    ], style={'display': 'flex', 'gap': '12px', 'flexWrap': 'wrap'}),
    html.Details([
        html.Summary('Informação adicional · Azimute, Elevação e Distância (AER)',
                     style={'cursor': 'pointer'}),
        html.P('Azimute desde Norte no sentido horário; elevação positiva para cima; '
               'distância espacial 3D.', style={'color': COLORS['muted'], 'fontSize': '13px'}),
        html.Div(id='aer-table', style={'marginTop': '10px'}),
    ], style={**PANEL, 'marginTop': '12px'}),
    html.Div([
        html.Div(id='status-panel', style={'marginBottom': '10px', 'color': COLORS['muted']}),
        html.Button('Exportar NED (CSV)', id='download-log-button', n_clicks=0),
        html.Button('Exportar vista local (CSV)', id='download-local-button', n_clicks=0,
                    style={'marginLeft': '10px'}),
        html.Button('Exportar configuração (YAML)', id='download-yaml-button', n_clicks=0,
                    style={'marginLeft': '10px'}),
        dcc.Download(id='download-log'),
        dcc.Download(id='download-local'),
        dcc.Download(id='download-config'),
    ], style={**PANEL, 'marginTop': '12px'}),
    html.P('ATENÇÃO: a posição foi interpretada como latitude/longitude/altitude em todos os logs, '
           'conforme o README do conjunto de dados. Setas e coordenadas alinhadas com o corpo '
           'são HIPÓTESES apenas para world_ned: o sentido dos quaterniões não foi confirmado. '
           'Quando indisponível, a vista relativa mantém os eixos NED (sem rotação). '
           'A exportação local indica explicitamente o referencial aplicado. '
           'O datum vertical da altitude também permanece por confirmar.',
           style={'fontSize': '12px', 'color': '#f4ce83', 'marginTop': '14px'}),
], style={'background': COLORS['bg'], 'color': COLORS['text'], 'minHeight': '100vh',
          'padding': '24px', 'fontFamily': 'Arial, sans-serif'})


@app.callback(Output('time-slider', 'value'), Output('replay-timer', 'disabled'),
              Output('play-pause', 'children'),
              Input('play-pause', 'n_clicks'), Input('replay-timer', 'n_intervals'),
              State('time-slider', 'value'), State('replay-timer', 'disabled'),
              prevent_initial_call=True)
def control_replay(_clicks, _ticks, current, stopped):
    """A reprodução termina no fim; não recua automaticamente ao início."""
    if ctx.triggered_id == 'play-pause':
        if stopped:
            index = 0 if (current or 0) >= TOTAL_STEPS else (current or 0)
            return index, False, '⏸ Pause'
        return current or 0, True, '▶ Play'
    if stopped:
        return current or 0, True, '▶ Play'
    index, finished = next_step(current, TOTAL_STEPS)
    return index, finished, '▶ Play' if finished else '⏸ Pause'


def aer_table(rows):
    if not rows:
        return html.P('Sem outras amostras disponíveis com a tolerância temporal configurada.')
    headers = ['Robô', 'Azimute', 'Elevação', 'Distância 3D', 'Δ Norte', 'Δ Este', 'Δ Down']
    cells = []
    for row in rows:
        values = [MISSION.traces[row['robot']].label,
                  f"{row['azimuth_deg']:.1f}°", f"{row['elevation_deg']:.1f}°",
                  f"{row['range_m']:.1f} m", f"{row['north_m']:.1f} m",
                  f"{row['east_m']:.1f} m", f"{row['down_m']:.1f} m"]
        cells.append(html.Tr([html.Td(v, style={'padding': '8px 12px'}) for v in values]))
    return html.Div(html.Table([
        html.Thead(html.Tr([html.Th(t, style={'textAlign': 'left', 'padding': '8px 12px'})
                            for t in headers])), html.Tbody(cells)
    ], style={'width': '100%', 'borderCollapse': 'collapse'}), style={'overflowX': 'auto'})


@app.callback(Output('global-view', 'figure'), Output('local-view', 'figure'),
              Output('clock-label', 'children'), Output('status-panel', 'children'),
              Output('aer-table', 'children'),
              Input('time-slider', 'value'), Input('robot-choice', 'value'),
              Input('radius-slider', 'value'), Input('global-dimension', 'value'))
def render_frame(step_index, central_key, radius, dimension):
    time_ns = time_at(step_index or 0)
    state = mission_state(MISSION, time_ns, TOLERANCE)
    global_view = (global_figure_3d(MISSION, state, time_ns, CFG)
                   if dimension == '3d' else global_figure(MISSION, state, time_ns, CFG))
    local_view = local_figure(MISSION, state, time_ns, central_key, CFG, radius)
    elapsed = (time_ns - MISSION.start_ns) / 1e9
    label = f'{utc_timestamp(time_ns)} UTC · {elapsed:.1f}s / {MISSION.duration_s:.1f}s'
    statuses = []
    for key, snap in state.items():
        trace = MISSION.traces[key]
        if snap is None:
            statuses.append(f'{trace.label}: sem amostra ±{TOLERANCE:.2f}s')
        else:
            provisional = orientation_is_usable(snap, CFG['orientation']['assumed_body_to_ned_frame_id'])
            statuses.append(f'{trace.label}: {snap.frame_id}; orientação '
                            + ('assumida, não validada' if provisional else 'desconhecida'))
    return global_view, local_view, label, ' | '.join(statuses), aer_table(relative_aer(state, central_key))


@app.callback(Output('download-log', 'data'), Input('download-log-button', 'n_clicks'),
              prevent_initial_call=True)
def export_ned_log(n_clicks):
    records = []
    for key, trace in MISSION.traces.items():
        records.append(pd.DataFrame({
            'robot': key, 'frame_id_log': trace.frames,
            'timestamp_ns': trace.times_ns,
            'time_from_mission_start_s': (trace.times_ns - MISSION.start_ns) / 1e9,
            'latitude_deg': trace.latitude, 'longitude_deg': trace.longitude,
            'altitude_source_m': trace.altitude,
            'north_m': trace.positions_ned[:, 0],
            'east_m': trace.positions_ned[:, 1],
            'down_m': trace.positions_ned[:, 2],
        }))
    merged = pd.concat(records, ignore_index=True).sort_values('timestamp_ns')
    return dcc.send_data_frame(merged.to_csv, 'tomsa_log_ned.csv', index=False)


@app.callback(Output('download-local', 'data'), Input('download-local-button', 'n_clicks'),
              State('time-slider', 'value'), State('robot-choice', 'value'),
              prevent_initial_call=True)
def export_local_snapshot(_n, step_index, central_key):
    time_ns = time_at(step_index or 0)
    rows = local_snapshot_rows(
        MISSION, time_ns, central_key, TOLERANCE,
        CFG['orientation']['assumed_body_to_ned_frame_id'])
    cols = ['timestamp_selected_ns', 'timestamp_sample_ns', 'reference_robot',
            'robot', 'coordinate_frame', 'local_x_m', 'local_y_m', 'local_z_m']
    return dcc.send_data_frame(pd.DataFrame(rows, columns=cols).to_csv,
                               'tomsa_snapshot_local.csv', index=False)


@app.callback(Output('download-config', 'data'), Input('download-yaml-button', 'n_clicks'),
              prevent_initial_call=True)
def export_config(_n):
    return dcc.send_file(str(CFG_PATH))


if __name__ == '__main__':
    app.run(debug=False, host='127.0.0.1', port=8050)
