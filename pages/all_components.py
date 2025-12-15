import dash
from dash import html, dcc, callback, Input, Output, State, ALL
import json
import time
from mylibrary import get_all_cis_with_downtimes

dash.register_page(__name__, path='/all-components')

_layout_cache = None
_layout_cache_ts = 0
_layout_cache_ttl = 60


def _format_minutes_to_human(minutes: float) -> str:
    try:
        m = float(minutes or 0.0)
        if m < 60:
            return f"{m:.0f} Min"
        h = m / 60.0
        if h < 24:
            return f"{h:.1f} Std"
        d = h / 24.0
        return f"{d:.1f} Tg"
    except Exception:
        return "0 Min"


def serve_layout():
    global _layout_cache, _layout_cache_ts
    now_ts = time.time()
    if _layout_cache is not None and (now_ts - _layout_cache_ts) < _layout_cache_ttl:
        return _layout_cache

    _layout_cache = html.Div([
        html.H2("Alle TI-Komponenten", className='page-title'),
        html.P("Übersicht aller Configuration Items mit Statusdaten und Ausfallzeiten."),
        html.Div([
            dcc.Input(
                id='components-filter',
                type='text',
                placeholder='CIs filtern (CI, Organisation, Produkt oder Name)',
                style={
                    'width': '100%',
                    'boxSizing': 'border-box',
                    'marginBottom': '16px',
                    'padding': '10px 14px',
                    'borderRadius': '8px',
                    'backgroundColor': '#ffffff',
                    'color': '#1e293b',
                    'border': '1px solid #cbd5e1',
                    'fontSize': '14px'
                },
                className='incidents-filter-input'
            ),
            dcc.Store(id='components-sort-state', data={'by': 'ci', 'asc': True}),
            html.Div(
                id='components-table-container',
                className='incidents-table-container',
                style={'maxHeight': '600px', 'overflowY': 'auto'}
            )
        ], className='incidents-section')
    ])
    _layout_cache_ts = time.time()
    return _layout_cache


layout = serve_layout


@callback(
    Output('components-table-container', 'children'),
    [Input('components-filter', 'value'),
     Input('components-sort-state', 'data')],
    prevent_initial_call=False
)
def render_components_table(filter_text, sort_state):
    try:
        df = get_all_cis_with_downtimes()
        if df is None or df.empty:
            return html.Div('Keine CIs verfügbar.')

        df = df.copy()
        df['ci'] = df['ci'].astype(str)

        by = (sort_state or {}).get('by', 'ci')
        asc = bool((sort_state or {}).get('asc', True))

        if by in ['ci', 'organization', 'product', 'name']:
            df = df.sort_values(
                [by, 'ci'] if by != 'ci' else ['ci'],
                ascending=[asc, True] if by != 'ci' else asc
            )
        elif by == 'downtime_7d_min':
            df = df.sort_values(['downtime_7d_min', 'ci'], ascending=[asc, True])
        elif by == 'downtime_30d_min':
            df = df.sort_values(['downtime_30d_min', 'ci'], ascending=[asc, True])
        elif by == 'current_availability':
            df = df.sort_values(['current_availability', 'ci'], ascending=[asc, True])
        else:
            df = df.sort_values('ci')

        if filter_text:
            f = str(filter_text).strip().lower()

            def match_row(r):
                try:
                    return (
                        f in str(r.get('ci', '')).lower()
                        or f in str(r.get('organization', '')).lower()
                        or f in str(r.get('product', '')).lower()
                        or f in str(r.get('name', '')).lower()
                    )
                except Exception:
                    return False

            mask = df.apply(match_row, axis=1)
            df = df[mask]

        rows = []
        for _, row in df.iterrows():
            status = int(row.get('current_availability') or 0)
            status_class = 'available' if status == 1 else 'unavailable'
            status_text = 'Verfügbar' if status == 1 else 'Gestört'

            rows.append(
                html.Tr([
                    html.Td([
                        html.A(
                            str(row.get('ci', '')),
                            href=f"/plot?ci={str(row.get('ci', ''))}",
                            className='ci-link'
                        ),
                        html.Br(),
                        html.Span(str(row.get('name', '')), className='ci-name')
                    ]),
                    html.Td([
                        html.Span(str(row.get('organization', '')), className='org-name'),
                        html.Br(),
                        html.Span(str(row.get('product', '')), className='product-name')
                    ]),
                    html.Td(_format_minutes_to_human(row.get('downtime_7d_min')), className='duration'),
                    html.Td(_format_minutes_to_human(row.get('downtime_30d_min')), className='duration'),
                    html.Td(
                        html.Span(status_text, className=f'status-badge {status_class}')
                    )
                ])
            )

        def sort_header(label, col_key, current, min_width=None):
            is_active = (current.get('by') == col_key)
            asc_active = is_active and current.get('asc', True)
            desc_active = is_active and not current.get('asc', True)
            arrow_style_base = {
                'border': 'none',
                'background': 'transparent',
                'cursor': 'pointer',
                'padding': '0 4px',
                'fontSize': '10px',
                'lineHeight': '1'
            }
            asc_style = {**arrow_style_base, 'color': '#0d9488' if asc_active else 'inherit'}
            desc_style = {**arrow_style_base, 'color': '#0d9488' if desc_active else 'inherit'}
            th_style = {
                'whiteSpace': 'nowrap',
                'verticalAlign': 'middle',
                'paddingRight': '8px',
                'paddingLeft': '8px',
                'minWidth': min_width or 'auto'
            }
            return html.Th([
                html.Span(label),
                html.Span([
                    html.Button(
                        '▲',
                        id={'type': 'comp-sort', 'col': col_key, 'dir': 'asc'},
                        n_clicks=0,
                        style=asc_style,
                        className='table-sort-btn'
                    ),
                    html.Button(
                        '▼',
                        id={'type': 'comp-sort', 'col': col_key, 'dir': 'desc'},
                        n_clicks=0,
                        style=desc_style,
                        className='table-sort-btn'
                    )
                ], style={'float': 'right', 'display': 'inline-flex', 'gap': '2px'})
            ], style=th_style)

        header = html.Thead([
            html.Tr([
                sort_header('CI', 'ci', sort_state or {}, min_width='140px'),
                sort_header('Organisation · Produkt', 'organization', sort_state or {}, min_width='280px'),
                sort_header('Down 7 Tage', 'downtime_7d_min', sort_state or {}, min_width='120px'),
                sort_header('Down 30 Tage', 'downtime_30d_min', sort_state or {}, min_width='120px'),
                sort_header('Status', 'current_availability', sort_state or {}, min_width='120px')
            ])
        ])

        table = html.Table([header, html.Tbody(rows)], className='incidents-table')
        return table

    except Exception as e:
        return html.Div(f'Fehler beim Laden: {str(e)}', style={'color': 'red'})


@callback(
    Output('components-sort-state', 'data'),
    Input({'type': 'comp-sort', 'col': ALL, 'dir': ALL}, 'n_clicks'),
    State('components-sort-state', 'data'),
    prevent_initial_call=True
)
def toggle_components_sort(_clicks, state):
    ctx = dash.callback_context
    state = state or {'by': 'ci', 'asc': True}
    if not ctx.triggered:
        return state
    trig = ctx.triggered[0]['prop_id'].split('.')[0]
    try:
        obj = json.loads(trig)
        col = obj.get('col')
        direction = obj.get('dir')
    except Exception:
        return state
    if not col or direction not in ('asc', 'desc'):
        return state
    return {'by': col, 'asc': direction == 'asc'}
