import dash
from dash import html, dcc, callback, Input, Output
import pandas as pd
from mylibrary import get_recent_incidents, load_config
import time

dash.register_page(__name__, path='/incident-history')

_layout_cache = None
_layout_cache_ts = 0
_layout_cache_ttl = 60

def create_incidents_table(incidents_data):
    if not incidents_data:
        return html.P("Keine Incidents in diesem Zeitraum.")

    table_rows = []
    for incident in incidents_data:
        status_class = 'incident-ongoing' if incident['status'] == 'ongoing' else 'incident-resolved'
        status_text = 'Noch gestört' if incident['status'] == 'ongoing' else 'Wieder aktiv'

        duration_hours = incident['duration_minutes'] / 60.0
        if duration_hours < 1:
            duration_text = f"{incident['duration_minutes']:.0f} Min"
        else:
            duration_text = f"{duration_hours:.1f} Std"

        start_time = pd.to_datetime(incident['incident_start']).tz_convert('Europe/Berlin').strftime('%d.%m.%Y %H:%M')
        end_time = ''
        if incident['incident_end']:
            end_time = pd.to_datetime(incident['incident_end']).tz_convert('Europe/Berlin').strftime('%d.%m.%Y %H:%M')
        else:
            end_time = 'Laufend'

        table_rows.append(html.Tr([
            html.Td([
                html.A(incident['ci'], href=f'/plot?ci={incident["ci"]}', className='ci-link'),
                html.Br(),
                html.Span(incident['name'], className='ci-name')
            ]),
            html.Td([
                html.Span(incident['organization'], className='org-name'),
                html.Br(),
                html.Span(incident['product'], className='product-name')
            ]),
            html.Td(start_time, className='timestamp'),
            html.Td(end_time, className='timestamp'),
            html.Td(duration_text, className='duration'),
            html.Td([
                html.Span(status_text, className=f'status-badge {status_class}')
            ])
        ]))

    return html.Div([
        html.Table([
            html.Thead([
                html.Tr([
                    html.Th("CI"),
                    html.Th("Organisation"),
                    html.Th("Beginn"),
                    html.Th("Ende"),
                    html.Th("Dauer"),
                    html.Th("Status")
                ])
            ]),
            html.Tbody(table_rows)
        ], className='incidents-table')
    ], className='incidents-table-container', style={'maxHeight': '600px', 'overflowY': 'auto'})


def serve_layout():
    global _layout_cache, _layout_cache_ts
    now_ts = time.time()
    if _layout_cache is not None and (now_ts - _layout_cache_ts) < _layout_cache_ttl:
        return _layout_cache

    config = load_config()
    core_config = config.get('core', {})
    stats_delta_hours = core_config.get('stats_delta_hours', 12)

    incidents_data = []
    try:
        incidents_data = get_recent_incidents(
            limit=100,
            only_enabled=True,
            only_ongoing=False,
            hours_back=stats_delta_hours
        )
    except Exception as e:
        print(f"Error loading incident history: {e}")
        incidents_data = []

    incidents_table = create_incidents_table(incidents_data)

    _layout_cache = html.Div([
        html.H2("Incident-Verlauf", className='page-title'),
        html.P(f"Incidents der letzten {stats_delta_hours} Stunden (inkl. behobene Störungen)"),
        html.Div([
            incidents_table
        ], className='incidents-section')
    ])
    _layout_cache_ts = time.time()
    return _layout_cache


layout = serve_layout
