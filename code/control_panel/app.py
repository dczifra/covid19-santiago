import os
import pandas as pd

import plotly.express as px
import plotly.graph_objects as go # or plotly.express as px

import dash
import json
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output

act_sim_folder = "sim_3"

# === APP ===
mathjax = 'https://cdnjs.cloudflare.com/ajax/libs/mathjax/2.7.4/MathJax.js?config=TeX-MML-AM_CHTML'
external_scripts = [
    mathjax
]
app = dash.Dash(__name__, external_scripts=external_scripts)

# === Figures ===
def general_plot(filename, title, value_names, xy_labels):
    df = pd.read_csv(filename, index_col=0)
    fig = px.line(df, 
        x=df.index, y=df.columns,
        labels={"value": value_names[0], "variable": value_names[1]},
        title=title)
    fig.update_layout(
        title_x = 0.5,
        title_y = 0.85,
        xaxis_title=xy_labels[0],
        yaxis_title=xy_labels[1],
        font=dict(
            family="Courier New, monospace",
            size=16,
            color="black",
        ),
    )
    return fig


def plot_map():
    with open("log/counties.geojson") as file:
        line = file.read()
        counties = json.loads(line)
    
    df = pd.read_csv("log/county_.csv")
    fig = px.choropleth_mapbox(df.where(df["days"]==150),
                            geojson=counties,
                            featureidkey="properties.megye",
                            locations='megye',
                            color='inf',
                            color_continuous_scale="Viridis",
                            mapbox_style="carto-positron",
                            zoom=8, center = {"lat": 47.49801, "lon": 19.03991},
                            opacity=0.5,
                            labels={'inf':'Infections'}
                            )
    fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
    return fig

def plot_map2():
    df = pd.read_csv("log/county_.csv")
    fig=px.choropleth(df,
                geojson="log/counties.geojson",
                featureidkey='properties.megye',
                locations='megye',        #column in dataframe
                animation_frame='days',       #dataframe
                color='inf',  #dataframe
                color_continuous_scale='Inferno',
                title='Infeections per day',
                height=700
                )
    fig.update_geos(fitbounds="locations", visible=False)
    return fig

# Age
def ages_fig():
    return general_plot(
        filename = "log/ages.csv",
        title = r'Deathes in each age group',
        value_names = ["Ages", "Age groups"],
        xy_labels = ["Days", "Deaths"])

# Sims
#@app.callback(
#    Output('sims-fig', 'figure'),
#    [Input('update-button', 'n_clicks')])
@app.callback(
    Output('sims-fig', 'figure'),
    [Input('class-dropdown', 'value')])
def sims_fig(value):
    return general_plot(
        filename = f"log/helper/{value}_agg.csv",
        title = r'Simulations',
        value_names = ["Dayly infection", "Simulations"],
        xy_labels = ["Days", "Infections"])

# County
def countys_fig():
    return general_plot(
        filename = "log/county.csv",
        title = r'Deathes in each county',
        value_names = ["Conty", "County"],
        xy_labels = ["Days", "Deaths"])

def get_folders():
    folders = []
    for folder in os.listdir("log"):
        if(folder[:4] == "sim_"):
            folders.append(folder)
    return folders

# === Helper functions ===
def create_dropdown_options(series):
    options = [{'label': i, 'value': i} for i in series]
    return options

def create_dropdown_value(series):
    value = series
    return value

def create_slider_marks(values):
    marks = {i: {'label': str(i)} for i in values}
    return marks

# === Layout ===
app.layout = html.Div(children=[
    # Left: control panel
    html.Div(children = [
        html.H1(children='Metapop Simulations'),
        html.P('Rényi Network Epidemic Research Group'),
        html.Img(src="assets/covid19.png"),
        html.Label("Simulations", className='dropdown-labels'),
        dcc.Dropdown(multi=False, className='dropdown', id='class-dropdown',
                     options=create_dropdown_options(get_folders()),
                     value=act_sim_folder),
        html.Div(id='drop-info'),
        html.Button("Update", id="update-button"),
        html.Div(children=[
            html.H2('Parameters', className='dropdown-labels'),
            
            
            html.Label("R0", className='dropdown-labels'),
            dcc.Input(id="R0", type="number", value=2.6, style={"text-align":"right", 'width': '9vh', 'height': '13px', "float":"right"}),
            html.Br(),
            
            html.Label("Second wave start", className='dropdown-labels'),
            dcc.Input(id="second_wave", type="number", value=100, style={"text-align":"right", 'width': '9vh', 'height': '13px', "float":"right"}),
            html.Br(),

            html.Label("Second wave ratio", className='dropdown-labels'),
            dcc.Input(id="second_ratio", type="number", value=3.0, style={"text-align":"right", 'width': '9vh', 'height': '13px', "float":"right"}),
            html.Br(),
            
            html.Label("Seasonality", className='dropdown-labels'),
            dcc.Input(id="sesonality", type="number", value=0.25, style={"text-align":"right", 'width': '9vh', 'height': '13px', "float":"right"}),
            html.Br(),
            
            html.Label("Number of age groups", className='dropdown-labels'),
            dcc.Input(id="age_groups", type="number", value=8, style={"text-align":"right", 'width': '9vh', 'height': '13px', "float":"right"}),
            html.Br(),

        ], style={'width': '100%', 'height': '400px'})

    ], id='left-container'),
    # Right: plots
    html.Div(children=[
        html.Div(children=[
            dcc.Graph(figure=plot_map(), style={'width': '100%'}),
            #dcc.Graph(figure=plot_map(), style={'width': '100%', 'height': '500px', 'display': 'inline-block'}),
            
            dcc.Graph(figure=ages_fig(), style={'width': '50%', 'height': '500px', 'display': 'inline-block'}),
            dcc.Graph(figure=countys_fig(), style={'width': '50%', 'height': '500px', 'display': 'inline-block'}),
            #dcc.Graph(id='sims-fig', figure=sims_fig("sims_3"), style={'width': '50%', 'height': '500px'}),
            dcc.Graph(id="sims-fig"),
            #html.Div(id="sims-fig",children=sims_fig())
        ], id="visualization")
    ], id="right-container")
], id='container')
app.run_server(debug=True, use_reloader=True)  # Turn off reloader if inside Jupyter