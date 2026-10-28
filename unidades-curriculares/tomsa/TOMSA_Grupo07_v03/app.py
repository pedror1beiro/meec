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
import yaml
from dash import Dash, ClientsideFunction, Input, Output, Patch, State, ctx, dcc, html
from tomsa.data import load_config, load_mission
from tomsa.figures import (global_figure, global_figure_3d, local_figure,
                           kinematics_figure, frame_comparison_figure)
from tomsa.geography import map_mission_data, map_frame_data
from tomsa.replay import (mission_state, orientation_is_usable, relative_aer,
                          local_snapshot_rows, next_step, frame_diagnostics)

parser = argparse.ArgumentParser()
parser.add_argument('--config', type=Path, default=Path(__file__).resolve().parent / 'config.yaml')
parser.add_argument('--demo', action='store_true', help='Usar dados sintéticos sem alterar o YAML.')
arguments, _ = parser.parse_known_args()
CFG_PATH = arguments.config.resolve()
CFG = load_config(CFG_PATH)
if arguments.demo:
    CFG['data']['mode'] = 'demo'
MISSION = load_mission(CFG, CFG_PATH.parent)
STEP = float(CFG['replay']['step_seconds'])
TOLERANCE = float(CFG['replay']['tolerance_seconds'])
if STEP <= 0 or TOLERANCE < 0:
    raise ValueError('step_seconds deve ser positivo e tolerance_seconds não negativo.')
TOTAL_STEPS = max(1, math.ceil(MISSION.duration_s / STEP))
VELOCITY_FRAME = ('ned' if CFG['data']['mode'] == 'demo' else
                  CFG.get('kinematics', {}).get('confirmed_velocity_frame', 'unknown'))
VELOCITY_FRAME_LABEL = {'unknown': 'não confirmada', 'ned': 'NED fixo confirmado',
                         'body': 'corpo confirmado'}[VELOCITY_FRAME]


def time_at(step_index):
    return min(MISSION.end_ns, MISSION.start_ns + int(round(int(step_index) * STEP * 1e9)))


def utc_timestamp(time_ns):
    return datetime.fromtimestamp(time_ns // 1_000_000_000, tz=timezone.utc).strftime('%d/%m/%Y %H:%M:%S')


def kinematics_cursor(elapsed_s):
    patch = Patch()
    patch['layout']['shapes'][0]['x0'] = elapsed_s
    patch['layout']['shapes'][0]['x1'] = elapsed_s
    return patch


MAPLIBRE_VERSION = '5.6.1'
MAPLIBRE_CDN = f'https://unpkg.com/maplibre-gl@{MAPLIBRE_VERSION}/dist/maplibre-gl'
app = Dash(__name__, external_scripts=[f'{MAPLIBRE_CDN}.js'],
           external_stylesheets=[f'{MAPLIBRE_CDN}.css'])
app.title = 'TOMSA · Grupo 07 · Mission Replay'

app.layout = html.Div([
    dcc.Store(id='map-mission', data=map_mission_data(MISSION, CFG)),
    dcc.Store(id='map-frame'),
    html.Header([
        html.Div('ISEP · MEEC / Sistemas Autónomos', className='eyebrow'),
        html.H1('Multi-Robot Mission Replay'),
        html.P('TOMSA · Grupo 07 · v0.4 · Trajetórias, referenciais e cinemática',
               className='subtitle'),
        html.Div([
            html.Span(MISSION.source, className='source-label'),
            html.Span(
                f'Intervalo comum · {utc_timestamp(MISSION.start_ns)}–'
                f'{utc_timestamp(MISSION.end_ns)} UTC · {MISSION.duration_s / 60:.1f} min',
                className='mission-range',
            ),
        ], className='hero-meta'),
    ], className='hero'),

    html.Section([
        html.Div([
            html.Label('Robô de referência', htmlFor='robot-choice'),
            dcc.Dropdown(
                id='robot-choice', clearable=False, value=next(iter(MISSION.traces)),
                options=[{'label': trace.label, 'value': key}
                         for key, trace in MISSION.traces.items()],
            ),
        ], className='control-group'),
        html.Div([
            html.Label('Raio de proximidade', htmlFor='radius-slider'),
            dcc.Slider(
                id='radius-slider', min=50, max=600, step=50,
                value=float(CFG['replay']['proximity_radius_m']),
                marks={int(x): f'{int(x)}' for x in range(100, 601, 100)},
            ),
            html.P('Metros · filtra os outros robôs na vista local',
                   className='helper-text'),
        ], className='control-group'),
        html.Div([
            html.Label('Reprodução'),
            html.Div([
                html.Button('▶ Play', id='play-pause', n_clicks=0,
                            className='button button-primary'),
                html.Span(id='clock-label', className='clock-readout'),
            ], className='playback-controls'),
        ], className='control-group'),
    ], className='card toolbar'),

    html.Section([
        html.Div([
            html.H2('Linha temporal', className='section-title'),
            html.Span('Arrasta para escolher um instante da missão',
                      className='helper-text'),
        ], className='section-heading'),
        dcc.Slider(
            id='time-slider', min=0, max=TOTAL_STEPS, value=0, step=1,
            marks={int(i): f'{i*STEP/60:.0f} min' for i in
                   np.linspace(0, TOTAL_STEPS, min(7, TOTAL_STEPS + 1), dtype=int)},
            updatemode='mouseup',
            tooltip={'placement': 'bottom', 'always_visible': False},
        ),
        dcc.Interval(
            id='replay-timer', interval=max(200, int(STEP * 1000)),
            n_intervals=0, disabled=True,
        ),
    ], className='card timeline-card'),

    html.Section([
        html.Div([
            html.H2('Mapa geográfico · WGS84', className='section-title'),
            html.Div([
                dcc.RadioItems(id='map-dimension', value='2d', inline=True,
                               options=[{'label': '2D', 'value': '2d'},
                                        {'label': '3D · oceano', 'value': '3d'}]),
                dcc.Checklist(id='map-seamarks', value=['show'],
                              options=[{'label': 'OpenSeaMap', 'value': 'show'}], inline=True),
                html.Button('Enquadrar missão', id='map-reset', n_clicks=0, className='button'),
            ], className='map-controls'),
        ], className='section-heading'),
        html.P('Latitude/longitude originais · 3D com ondas e iluminação ilustrativas, sem batimetria ou alturas de onda medidas',
               className='helper-text'),
        html.Div([
            html.Label('Percurso', htmlFor='map-trails'),
            dcc.Dropdown(id='map-trails', clearable=False, value='60', options=[
                {'label': 'Rasto · últimos 60 s', 'value': '60'},
                {'label': 'Rasto · últimos 30 s', 'value': '30'},
                {'label': 'Trajetórias completas', 'value': 'full'},
                {'label': 'Sem trajetórias', 'value': 'none'}]),
            dcc.Checklist(id='map-effects', value=['icons', 'ring'], inline=True, options=[
                {'label': 'Ícones de robô', 'value': 'icons'},
                {'label': 'Anel de proximidade', 'value': 'ring'}]),
        ], className='map-display-options'),
        html.P('Rasto até à amostra visível · ícones ilustrativos; rumo só com convenção confirmada. '
               'Anel horizontal aproximado; o filtro local usa distância 3D.', className='helper-text'),
        html.Div(id='geographical-map', role='region', **{'aria-label': 'Mapa das trajetórias dos robôs'}),
        html.P(id='map-status', role='status', className='helper-text'),
        html.Div([html.Span([html.Span(className='legend-dot', style={'background': trace.color}),
                            trace.label]) for trace in MISSION.traces.values()], className='map-legend'),
    ], className='card map-card'),

    html.Section([
        html.Span('Dimensão da vista global', className='section-title'),
        dcc.RadioItems(
            id='global-dimension',
            options=[{'label': '2D', 'value': '2d'},
                     {'label': '3D', 'value': '3d'}],
            value='2d', inline=True,
        ),
    ], className='card view-options'),

    html.Main([
        html.Div([
            dcc.Graph(
                id='global-view',
                config={'displaylogo': False, 'responsive': True},
                style={'height': '560px', 'width': '100%'},
            ),
        ], className='graph-card'),
        html.Div([
            dcc.Graph(
                id='local-view',
                config={'displaylogo': False, 'responsive': True},
                style={'height': '560px', 'width': '100%'},
            ),
        ], className='graph-card'),
    ], className='graph-grid'),

    html.Details([
        html.Summary('Mostrar a matemática · o que muda quando trocamos de referencial?',
                     id='math-toggle', n_clicks=0),
        html.P('As coordenadas mudam; uma transformação rígida preserva as distâncias 3D. '
               'Os pontos são as mesmas amostras do replay, sem interpolação.', className='helper-text'),
        html.Div(id='math-content'),
    ], id='math-panel', open=False, className='card details-card math-panel'),

    html.Section([
        html.H2('Velocidade e aceleração', className='section-title'),
        html.P('Rapidez = ‖v‖. Linha contínua: d‖v‖/dt, assinada (pode ser negativa). '
               'Linha pontilhada: ‖dv NED/dt‖, apenas com referencial fixo confirmado.',
               className='helper-text'),
        html.Div(id='kinematics-readouts', className='kinematics-readouts'),
        html.P('Logs reais: unidades SI usuais (m/s, rad/s), descritas como “normalmente” no README; '
               f'base das velocidades: {VELOCITY_FRAME_LABEL}. Sem filtros ou suavização.',
               className='helper-text') if CFG['data']['mode'] != 'demo' else
        html.P('Demo sintética: velocidades na base NED fixa e orientações corpo→NED conhecidas por construção.',
               className='helper-text'),
    ], className='card'),
    html.Div([
        html.Div(dcc.Graph(id='speed-view', figure=kinematics_figure(MISSION, 'speed', CFG),
                           config={'displaylogo': False, 'responsive': True},
                           style={'height': '390px'}), className='graph-card'),
        html.Div(dcc.Graph(id='acceleration-view', figure=kinematics_figure(MISSION, 'acceleration', CFG),
                           config={'displaylogo': False, 'responsive': True},
                           style={'height': '390px'}), className='graph-card'),
    ], className='graph-grid'),

    html.Details([
        html.Summary('Medições adicionais · Azimute, Elevação e Distância (AER)'),
        html.P(
            'Azimute desde Norte no sentido horário; elevação positiva para cima; '
            'distância espacial 3D.', className='helper-text',
        ),
        html.Div(id='aer-table', className='table-wrap'),
    ], className='card details-card'),

    html.Section([
        html.H2('Exportações', className='section-title'),
        html.Div(id='status-panel', className='status-panel'),
        html.Div([
            html.Button('Exportar NED (CSV)', id='download-log-button', n_clicks=0,
                        className='button button-secondary'),
            html.Button('Exportar vista local (CSV)', id='download-local-button',
                        n_clicks=0, className='button button-secondary'),
            html.Button('Exportar configuração (YAML)', id='download-yaml-button',
                        n_clicks=0, className='button button-secondary'),
        ], className='export-buttons'),
        dcc.Download(id='download-log'),
        dcc.Download(id='download-local'),
        dcc.Download(id='download-config'),
    ], className='card export-card'),

    html.P(
        'Nota técnica: as posições são latitude/longitude/altitude nos três logs, '
        'segundo o README. O nome world_ned, por si só, não confirma corpo→NED; '
        'setas provisórias estão identificadas. WGS84 não determina eixos de orientação. No mapa, setas só '
        'com corpo→NED confirmado. O datum vertical da altitude carece de confirmação.',
        className='technical-note',
    ),
], className='app-shell')

app.clientside_callback(
    ClientsideFunction(namespace='tomsaMap', function_name='render'),
    Output('map-status', 'children'), Input('map-mission', 'data'),
    Input('map-frame', 'data'), Input('map-dimension', 'value'),
    Input('map-seamarks', 'value'), Input('map-reset', 'n_clicks'),
    Input('map-trails', 'value'), Input('map-effects', 'value'))

# Native <details> toggles its DOM attribute, but does not notify Dash props.
# Keep Dash's open state in sync so expensive diagnostics are built only on demand.
app.clientside_callback(
    'function(clicks) { return (clicks || 0) % 2 === 1; }',
    Output('math-panel', 'open'), Input('math-toggle', 'n_clicks'))


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


def mathematics_panel(state, time_ns, central_key):
    diagnostics = frame_diagnostics(state, central_key, CFG['orientation']['assumed_body_to_ned_frame_id'])
    if diagnostics is None:
        return html.P('Sem amostra do robô de referência dentro da tolerância temporal.', className='technical-note')
    frame_label = {'robot_body_confirmed': 'Corpo → NED confirmado',
                   'robot_body_assumed': 'Corpo → NED: hipótese não validada',
                   'ned_translated': 'NED transladado: sem rotação do corpo'}[diagnostics['frame']]
    def matrix_table(values):
        return html.Table(html.Tbody([html.Tr([html.Td(f'{v:.6f}') for v in row]) for row in values]),
                          className='matrix-table')
    def table(headers, rows):
        return html.Div(html.Table([html.Thead(html.Tr([html.Th(h) for h in headers])),
                                    html.Tbody([html.Tr([html.Td(cell) for cell in row]) for row in rows])]),
                        className='table-wrap')
    position_rows = []
    for key, world, local in zip(diagnostics['keys'], diagnostics['world'], diagnostics['local']):
        position_rows.append([MISSION.traces[key].label,
            f'{(state[key].time_ns-time_ns)/1e6:+.3f} ms',
            ', '.join(f'{v:.3f}' for v in world), ', '.join(f'{v:.3f}' for v in local)])
    pair_rows = [[' ↔ '.join(MISSION.traces[k].label for k in pair['robots']),
                  f'{pair["ned_m"]:.6f}', f'{pair["local_m"]:.6f}', f'{pair["error_m"]:.3e}']
                 for pair in diagnostics['pairs']]
    return html.Div([
        html.P(frame_label, className='math-frame-label'),
        html.P('Uma verificação numérica bem-sucedida não confirma a convenção física dos quaterniões. '
               'O NED mantém a hipótese documentada sobre o datum vertical.', className='helper-text'),
        html.Div([
            html.Div([html.Strong('T NED ← local'), matrix_table(diagnostics['transform'])]),
            html.Div([html.Strong('T local ← NED = T⁻¹'), matrix_table(diagnostics['inverse'])]),
        ], className='math-matrices'),
        dcc.Markdown(r'$$p_{local}=R^T(p_{NED}-t),\qquad '
                     r'T_{NED\leftarrow local}=\begin{bmatrix}R&t\\0&1\end{bmatrix}$$', mathjax=True),
        html.Div([
            html.Span(f'‖RᵀR − I‖F = {diagnostics["orthogonality_error"]:.3e}'),
            html.Span(f'det(R) = {diagnostics["determinant"]:.12f}'),
            html.Span(f'Erro máximo ida/volta = {diagnostics["roundtrip_error_m"]:.3e} m'),
        ], className='math-checks'),
        html.P('Invariantes numéricos respeitados' if diagnostics['checks_pass'] else 'Verificação numérica fora da tolerância',
               className='math-check-result'),
        html.P('Matrizes e coordenadas arredondadas só na apresentação. Verificação com precisão completa: '
               'distâncias/ida-volta atol = 10⁻⁸ m, rtol = 10⁻¹²; ortogonalidade/determinante 10⁻¹².',
               className='helper-text'),
        dcc.Graph(id='math-comparison', figure=frame_comparison_figure(MISSION, diagnostics, central_key),
                  config={'displaylogo': False, 'responsive': True}, style={'height': '440px'}),
        html.P('Mesma escala métrica nos dois painéis. A projeção no ecrã pode alterar a forma aparente. '
               'São mostradas todas as amostras disponíveis, independentemente do raio de proximidade.', className='helper-text'),
        table(['Par', 'Distância NED (m)', 'Distância local (m)', '|Δd| (m)'], pair_rows)
            if pair_rows else html.P('É necessária outra amostra para comparar distâncias.'),
        table(['Robô', 'Δt amostra − instante', 'NED (N, E, D) · m', 'Local (x, y, z) · m'], position_rows),
        html.P(f'Alinhamento por amostra mais próxima, ±{TOLERANCE:.3f} s: os timestamps podem diferir.',
               className='helper-text'),
    ])


@app.callback(Output('global-view', 'figure'), Output('local-view', 'figure'),
              Output('clock-label', 'children'), Output('status-panel', 'children'),
              Output('aer-table', 'children'),
              Output('map-frame', 'data'),
              Output('speed-view', 'figure'), Output('acceleration-view', 'figure'),
              Output('kinematics-readouts', 'children'),
              Output('math-content', 'children'),
              Input('time-slider', 'value'), Input('robot-choice', 'value'),
              Input('radius-slider', 'value'), Input('global-dimension', 'value'),
              Input('math-panel', 'open'))
def render_frame(step_index, central_key, radius, dimension, math_open=False):
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
            orientation = ('confirmada' if snap.body_to_ned_confirmed else
                           'assumida, não validada' if provisional else 'desconhecida')
            statuses.append(f'{trace.label}: {snap.frame_id}; orientação {orientation}')
    readouts = []
    for key, trace in MISSION.traces.items():
        snap = state[key]
        def value(array, unit):
            return f'{array[snap.index]:.3f} {unit}' if snap is not None and np.isfinite(array[snap.index]) else 'indisponível'
        readouts.append(html.Div([
            html.Strong([html.Span(className='legend-dot', style={'background': trace.color}), trace.label]),
            html.Span(value(trace.kinematics.speed_m_s, 'm/s'), className='speed-value'),
            html.Span('d‖v‖/dt: ' + value(trace.kinematics.speed_rate_m_s2, 'm/s²')),
            html.Span('‖a NED‖: ' + value(trace.kinematics.acceleration_magnitude_m_s2, 'm/s²')),
        ], className='kinematics-readout'))
    return (global_view, local_view, label, ' | '.join(statuses),
            aer_table(relative_aer(state, central_key)), map_frame_data(MISSION, state, central_key, CFG, radius),
            kinematics_cursor(elapsed), kinematics_cursor(elapsed), readouts,
            mathematics_panel(state, time_ns, central_key) if math_open else None)


@app.callback(Output('download-log', 'data'), Input('download-log-button', 'n_clicks'),
              prevent_initial_call=True)
def export_ned_log(n_clicks):
    records = []
    for key, trace in MISSION.traces.items():
        records.append(pd.DataFrame({
            'robot': key, 'frame_id_log': trace.frames,
            'child_frame_id_log': trace.child_frames,
            'timestamp_ns': trace.times_ns,
            'time_from_mission_start_s': (trace.times_ns - MISSION.start_ns) / 1e9,
            'latitude_deg': trace.latitude, 'longitude_deg': trace.longitude,
            'altitude_source_m': trace.altitude,
            'north_m': trace.positions_ned[:, 0],
            'east_m': trace.positions_ned[:, 1],
            'down_m': trace.positions_ned[:, 2],
            'speed_m_s': trace.kinematics.speed_m_s,
            'speed_rate_m_s2': trace.kinematics.speed_rate_m_s2,
            'acceleration_ned_magnitude_m_s2': trace.kinematics.acceleration_magnitude_m_s2,
            'velocity_frame_confirmed': VELOCITY_FRAME,
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
    return dcc.send_string(yaml.safe_dump(CFG, allow_unicode=True, sort_keys=False), 'tomsa_config.yaml')


if __name__ == '__main__':
    app.run(debug=False, host='127.0.0.1', port=8050)
