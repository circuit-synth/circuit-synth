#!/usr/bin/env python3
"""
Claude API Usage Dashboard - Interactive Plotly Dash dashboard

Features:
- Real-time token usage monitoring
- Cost tracking and projections
- Worker performance metrics
- Historical trends
- Interactive filtering and exploration

Usage:
    python dashboard/api_dashboard.py

Then open: http://localhost:8050
"""

import sys
import json
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict

import dash
from dash import dcc, html, Input, Output, State
import plotly.graph_objs as go
import plotly.express as px
import pandas as pd

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))
from adws.adw_modules.api_logger import ClaudeAPILogger

# Initialize
REPO_ROOT = Path(__file__).parent.parent
LOG_DIR = REPO_ROOT / 'logs' / 'api'
logger = ClaudeAPILogger(LOG_DIR)

# Create Dash app
app = dash.Dash(__name__, update_title='Updating...')
app.title = 'Claude API Dashboard'


def load_logs(days: int = 7) -> pd.DataFrame:
    """Load logs from last N days into DataFrame"""
    rows = []

    for i in range(days):
        date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
        log_file = LOG_DIR / f"api-calls-{date}.jsonl"

        if not log_file.exists():
            continue

        with open(log_file, 'r') as f:
            for line in f:
                try:
                    call = json.loads(line)
                    rows.append(call)
                except json.JSONDecodeError:
                    continue

    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows)

    # Convert timestamp to datetime
    if 'timestamp' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['date'] = df['timestamp'].dt.date
        df['hour'] = df['timestamp'].dt.hour

    # Fill missing values
    for col in ['tokens_total', 'tokens_input', 'tokens_output', 'estimated_cost_usd']:
        if col in df.columns:
            df[col] = df[col].fillna(0)

    return df


def create_summary_cards(df: pd.DataFrame):
    """Create summary stat cards"""
    if df.empty:
        return html.Div("No data available", className="text-muted")

    total_calls = len(df)
    successful_calls = df['success'].sum() if 'success' in df.columns else 0
    total_tokens = df['tokens_total'].sum() if 'tokens_total' in df.columns else 0
    total_cost = df['estimated_cost_usd'].sum() if 'estimated_cost_usd' in df.columns else 0

    return html.Div([
        html.Div([
            html.Div([
                html.H3(f"{total_calls:,}", className="mb-0"),
                html.P("Total API Calls", className="text-muted mb-0")
            ], className="card-body", style={'textAlign': 'center'})
        ], className="card", style={'display': 'inline-block', 'width': '23%', 'margin': '1%'}),

        html.Div([
            html.Div([
                html.H3(f"{successful_calls:,}", className="mb-0 text-success"),
                html.P("Successful", className="text-muted mb-0")
            ], className="card-body", style={'textAlign': 'center'})
        ], className="card", style={'display': 'inline-block', 'width': '23%', 'margin': '1%'}),

        html.Div([
            html.Div([
                html.H3(f"{total_tokens:,}", className="mb-0"),
                html.P("Total Tokens", className="text-muted mb-0")
            ], className="card-body", style={'textAlign': 'center'})
        ], className="card", style={'display': 'inline-block', 'width': '23%', 'margin': '1%'}),

        html.Div([
            html.Div([
                html.H3(f"${total_cost:.2f}", className="mb-0 text-danger"),
                html.P("Estimated Cost", className="text-muted mb-0")
            ], className="card-body", style={'textAlign': 'center'})
        ], className="card", style={'display': 'inline-block', 'width': '23%', 'margin': '1%'}),
    ])


def create_tokens_timeline(df: pd.DataFrame):
    """Create tokens over time graph"""
    if df.empty or 'timestamp' not in df.columns:
        return go.Figure()

    # Group by hour
    hourly = df.groupby([df['timestamp'].dt.floor('H')]).agg({
        'tokens_input': 'sum',
        'tokens_output': 'sum',
        'tokens_total': 'sum'
    }).reset_index()

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=hourly['timestamp'],
        y=hourly['tokens_input'],
        name='Input Tokens',
        mode='lines+markers',
        line=dict(color='#1f77b4'),
        stackgroup='one'
    ))

    fig.add_trace(go.Scatter(
        x=hourly['timestamp'],
        y=hourly['tokens_output'],
        name='Output Tokens',
        mode='lines+markers',
        line=dict(color='#ff7f0e'),
        stackgroup='one'
    ))

    fig.update_layout(
        title='Token Usage Over Time',
        xaxis_title='Time',
        yaxis_title='Tokens',
        hovermode='x unified',
        template='plotly_white'
    )

    return fig


def create_cost_timeline(df: pd.DataFrame):
    """Create cost over time graph"""
    if df.empty or 'timestamp' not in df.columns:
        return go.Figure()

    # Group by date
    daily = df.groupby('date').agg({
        'estimated_cost_usd': 'sum'
    }).reset_index()

    daily['cumulative_cost'] = daily['estimated_cost_usd'].cumsum()

    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=daily['date'],
        y=daily['estimated_cost_usd'],
        name='Daily Cost',
        marker_color='#d62728'
    ))

    fig.add_trace(go.Scatter(
        x=daily['date'],
        y=daily['cumulative_cost'],
        name='Cumulative Cost',
        mode='lines+markers',
        line=dict(color='#2ca02c', width=3),
        yaxis='y2'
    ))

    fig.update_layout(
        title='Cost Tracking',
        xaxis_title='Date',
        yaxis_title='Daily Cost (USD)',
        yaxis2=dict(
            title='Cumulative Cost (USD)',
            overlaying='y',
            side='right'
        ),
        hovermode='x unified',
        template='plotly_white'
    )

    return fig


def create_model_breakdown(df: pd.DataFrame):
    """Create pie chart of usage by model"""
    if df.empty or 'model' not in df.columns:
        return go.Figure()

    model_stats = df.groupby('model').agg({
        'tokens_total': 'sum',
        'estimated_cost_usd': 'sum'
    }).reset_index()

    fig = go.Figure(data=[go.Pie(
        labels=model_stats['model'],
        values=model_stats['tokens_total'],
        hole=0.3,
        textinfo='label+percent',
        hovertemplate='<b>%{label}</b><br>Tokens: %{value:,}<br>Cost: $%{customdata:.2f}<extra></extra>',
        customdata=model_stats['estimated_cost_usd']
    )])

    fig.update_layout(
        title='Token Usage by Model',
        template='plotly_white'
    )

    return fig


def create_task_performance(df: pd.DataFrame):
    """Create task performance scatter plot"""
    if df.empty or 'task_id' not in df.columns:
        return go.Figure()

    # Filter to tasks with data
    task_df = df[df['task_id'].notna()].copy()

    if task_df.empty:
        return go.Figure()

    fig = px.scatter(
        task_df,
        x='duration_seconds',
        y='tokens_total',
        color='success',
        hover_data=['task_id', 'worker_id', 'estimated_cost_usd'],
        title='Task Performance: Duration vs Tokens',
        labels={
            'duration_seconds': 'Duration (seconds)',
            'tokens_total': 'Total Tokens',
            'success': 'Success'
        },
        color_discrete_map={True: 'green', False: 'red'}
    )

    fig.update_layout(template='plotly_white')

    return fig


def create_hourly_heatmap(df: pd.DataFrame):
    """Create heatmap of activity by hour/day"""
    if df.empty or 'date' not in df.columns:
        return go.Figure()

    # Group by date and hour
    heatmap_data = df.groupby(['date', 'hour']).size().reset_index(name='calls')

    # Pivot for heatmap
    pivot = heatmap_data.pivot(index='hour', columns='date', values='calls').fillna(0)

    fig = go.Figure(data=go.Heatmap(
        z=pivot.values,
        x=[str(d) for d in pivot.columns],
        y=pivot.index,
        colorscale='YlOrRd',
        hoverongaps=False
    ))

    fig.update_layout(
        title='API Call Activity Heatmap',
        xaxis_title='Date',
        yaxis_title='Hour of Day',
        template='plotly_white'
    )

    return fig


# Layout
app.layout = html.Div([
    html.H1('Claude API Usage Dashboard', style={'textAlign': 'center', 'marginTop': 20}),

    html.Div([
        html.Label('Time Range:'),
        dcc.Dropdown(
            id='time-range',
            options=[
                {'label': 'Last 24 Hours', 'value': 1},
                {'label': 'Last 7 Days', 'value': 7},
                {'label': 'Last 30 Days', 'value': 30},
            ],
            value=7,
            style={'width': '200px', 'display': 'inline-block', 'marginLeft': 10}
        ),
        html.Button('Refresh', id='refresh-btn', n_clicks=0,
                    style={'marginLeft': 20})
    ], style={'textAlign': 'center', 'margin': 20}),

    html.Div(id='summary-cards', style={'margin': 20}),

    html.Div([
        html.Div([
            dcc.Graph(id='tokens-timeline')
        ], style={'width': '100%'}),
    ], style={'margin': 20}),

    html.Div([
        html.Div([
            dcc.Graph(id='cost-timeline')
        ], style={'width': '60%', 'display': 'inline-block'}),

        html.Div([
            dcc.Graph(id='model-breakdown')
        ], style={'width': '38%', 'display': 'inline-block', 'marginLeft': '2%'}),
    ], style={'margin': 20}),

    html.Div([
        html.Div([
            dcc.Graph(id='task-performance')
        ], style={'width': '60%', 'display': 'inline-block'}),

        html.Div([
            dcc.Graph(id='hourly-heatmap')
        ], style={'width': '38%', 'display': 'inline-block', 'marginLeft': '2%'}),
    ], style={'margin': 20}),

    # Auto-refresh every 30 seconds
    dcc.Interval(
        id='interval-component',
        interval=30*1000,  # in milliseconds
        n_intervals=0
    )
], style={'fontFamily': 'Arial, sans-serif'})


# Callbacks
@app.callback(
    [Output('summary-cards', 'children'),
     Output('tokens-timeline', 'figure'),
     Output('cost-timeline', 'figure'),
     Output('model-breakdown', 'figure'),
     Output('task-performance', 'figure'),
     Output('hourly-heatmap', 'figure')],
    [Input('refresh-btn', 'n_clicks'),
     Input('interval-component', 'n_intervals'),
     Input('time-range', 'value')]
)
def update_dashboard(n_clicks, n_intervals, days):
    """Update all dashboard components"""
    df = load_logs(days=days)

    return (
        create_summary_cards(df),
        create_tokens_timeline(df),
        create_cost_timeline(df),
        create_model_breakdown(df),
        create_task_performance(df),
        create_hourly_heatmap(df)
    )


if __name__ == '__main__':
    print("\n" + "="*60)
    print("🚀 Claude API Usage Dashboard")
    print("="*60)
    print(f"📁 Log Directory: {LOG_DIR}")
    print(f"🌐 Dashboard URL: http://localhost:8050")
    print("="*60 + "\n")

    app.run_server(debug=True, host='0.0.0.0', port=8050)
