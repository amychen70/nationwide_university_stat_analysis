import json
import numpy as np
import pandas as pd
import dash
from dash import dcc, html, Input, Output, State
import plotly.express as px
import plotly.graph_objects as go

# Load data from JSON files
with open('data/tuition_US.json', 'r') as f:
    tuition_data = json.load(f)
with open('data/edu_score_US.json', 'r') as f:
    edu_scores = json.load(f)

# Find common universities in both datasets
common_unis = set(tuition_data.keys()).intersection(edu_scores.keys())
data = []
for uni in common_unis:
    data.append({
        'University': uni,
        'Tuition': tuition_data[uni],
        'Score': edu_scores[uni]
    })

df = pd.DataFrame(data)

# Optionally, compute a regression line for display.
# Here we simply create a scatter plot.
scatter_fig = px.scatter(
    df, x="Tuition", y="Score", hover_name="University",
    title="Tuition vs Educational Score"
)

# Create the Dash app layout
app = dash.Dash(__name__)

app.layout = html.Div([
    html.Div([
        dcc.Input(
            id='university-search',
            type='text',
            placeholder='Search for a university...',
            style={'width': '48%', 'margin-bottom': '10px'}
        ),
        dcc.Graph(id='scatter-plot', figure=scatter_fig)
    ], style={'width': '48%', 'display': 'inline-block', 'vertical-align': 'top'}),

    html.Div([
        dcc.Graph(id='radar-chart'),
        html.Div(id='university-info')
    ], style={'width': '48%', 'display': 'inline-block', 'vertical-align': 'top'})
])




@app.callback(
    [Output('scatter-plot', 'figure'),
     Output('radar-chart', 'figure'),
     Output('university-info', 'children')],
    [Input('scatter-plot', 'clickData'),
     Input('university-search', 'n_submit')],
    [State('university-search', 'value')]
)

def update_plots(clickData, n_submit, search_value):
    # Create a copy of the base figure
    updated_fig = scatter_fig

    # Initialize variables
    radar_fig = go.Figure()
    info_text = "Select or search for a university to see details"
    selected_uni = None

    # Determine which input triggered the callback
    ctx = dash.callback_context
    if not ctx.triggered:
        trigger_id = None
    else:
        trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]

    # Handle click events
    if trigger_id == 'scatter-plot' and clickData:
        selected_uni = clickData['points'][0]['hovertext']

    # Handle search events
    elif trigger_id == 'university-search' and search_value:
        # Find closest matching university name
        matches = [uni for uni in df['University'] if search_value.lower() in uni.lower()]
        if matches:
            selected_uni = matches[0]  # Take the first match

    # If we have a selected university, update visualizations
    if selected_uni:
        # Highlight the selected university on scatter plot
        selected_data = df[df['University'] == selected_uni]
        if not selected_data.empty:
            updated_fig.add_trace(
                go.Scatter(
                    x=selected_data['Tuition'],
                    y=selected_data['Score'],
                    mode='markers',
                    marker=dict(color='gold', size=12, line=dict(color='black', width=2)),
                    name='Selected University',
                    hoverinfo='text',
                    hovertext=selected_uni
                )
            )

            # Create radar chart
            try:
                with open('data/uni_ratings_US.json', 'r') as f:
                    uni_ratings = json.load(f)

                metrics = ["Academic", "Social", "Facilities", "Career", "Diversity"]
                rating_strings = uni_ratings.get(selected_uni, ["NA", "NA", "NA", "NA", "NA"])

                scores = []
                for rating in rating_strings:
                    try:
                        score = int(rating.split('/')[0])
                    except Exception:
                        score = 0
                    scores.append(score)

                radar_fig = go.Figure()
                radar_fig.add_trace(go.Scatterpolar(
                    r=scores,
                    theta=metrics,
                    fill='toself',
                    name=selected_uni
                ))
                radar_fig.update_layout(
                    polar=dict(
                        radialaxis=dict(visible=True, range=[0, 10])
                    ),
                    showlegend=False,
                    title=f"{selected_uni} Ratings"
                )

                info_text = html.Div([
                    html.H4(selected_uni),
                    html.P(f"Tuition: ${selected_data['Tuition'].values[0]:,}"),
                    html.P(f"Education Score: {selected_data['Score'].values[0]:.1f}"),
                    html.Ul([html.Li(f"{metric}: {score}/10") for metric, score in zip(metrics, scores)])
                ])
            except FileNotFoundError:
                info_text = html.Div([
                    html.H4(selected_uni),
                    html.P(f"Tuition: ${selected_data['Tuition'].values[0]:,}"),
                    html.P(f"Education Score: {selected_data['Score'].values[0]:.1f}"),
                    html.P("Rating data not available")
                ])

    return updated_fig, radar_fig, info_text



if __name__ == '__main__':
    app.run(debug=True)
