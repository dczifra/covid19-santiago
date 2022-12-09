import os
import pandas as pd

import plotly.express as px
import plotly.graph_objects as go # or plotly.express as px

import dash
import json
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output

# === APP ===
mathjax = 'https://cdnjs.cloudflare.com/ajax/libs/mathjax/2.7.4/MathJax.js?config=TeX-MML-AM_CHTML'
external_scripts = [
    mathjax
]
app = dash.Dash(__name__, external_scripts=external_scripts)

# === Figures ===
def general_plot(df, title, value_names, xy_labels):
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
    df = pd.read_csv("log/ages.csv", index_col=0)
    return general_plot(
        df,
        title = r'Deathes in each age group',
        value_names = ["Ages", "Age groups"],
        xy_labels = ["Days", "Deaths"])

def loss_restrict(df, sim_name, th):
    df_dist = pd.read_csv(f"log/helper/{sim_name}_distribution.csv", index_col=0, dtype=str)
    params_best = [row[["R0", "R1", "R1_shift"]] for index,row in df_dist.iterrows() if float(row["loss"])<float(th)]

    df = df[["_".join([str(r) for r in row]) for row in params_best]+["Ground truth"]]
    return df

# Sims
@app.callback(
    Output('sims-fig', 'figure'),
    [Input('class-dropdown', 'value'), Input(component_id='loss_th', component_property='value')])
def sims_fig(sim_name, th):
    df = pd.read_csv(f"log/helper/{sim_name}_agg.csv", index_col=0)
    df = loss_restrict(df, sim_name, th)
    
    return general_plot(
        df,
        title = f'Simulations {th}',
        value_names = ["Dayly infection", "Simulations"],
        xy_labels = ["Days", "Infections"])

def param_loss(param, sim_name, th):
    df = pd.read_csv(f"log/helper/{sim_name}_distribution.csv", index_col=0)
    df = df[df["loss"]<float(th)]

    fig = px.scatter(df, 
        x=df[param], y=df["loss"],
        title=f"{param} - Loss function")
    return fig

def param_histogram(param, sim_name, th):
    df = pd.read_csv("log/helper/sim_second_06_distribution.csv", index_col=0)
    #df = loss_restrict(df, sim_name, th)
    df = df[df["loss"]<float(th)]

    fig = px.histogram(df, 
        x=df[param],
        title=f"Best {param} - distribution")

    return fig

def violin_plot(key, sim_name, th):
    df = pd.read_csv(f"log/helper/{sim_name}_distribution.csv", index_col=0)
    df = df[df["loss"]<float(th)]

    fig = go.Figure()

    for v in df[key].unique():
        #go.Violin
        fig.add_trace(go.Violin(x=df[key][df[key]==v].astype(str), box_visible=True, y=df['loss'][df[key]==v], points="all", name=v,
                                meanline_visible=True, opacity=0.6, x0=str(v),
                                ))
    

    fig.update_layout(
        updatemenus=[
            dict(
                type = "buttons",
                direction = "left",
                buttons=list([
                    dict(
                        args=["type", "box"],
                        label="Box",
                        method="restyle"
                    ),
                    dict(
                        args=[{"type":"violin", "box":True, "box_visible":True}],
                        #args=[{"type": "violin", "box_visible":False, "box":False, "opacity" : 1.0}],
                        label="Violin",
                        method="restyle"
                    )
                ]),
                pad={"r": 10, "t": 10},
                showactive=True,
                x=0.0,
                xanchor="left",
                y=1.1,
                yanchor="top"
            ),
        ]
    )
    fig.update_layout(
        title = {
            'text':f"Distribution of {key}",
            'y':0.9,
            'x':0.5,
            'xanchor':'center',
            'yanchor': 'top',
        },
        showlegend=False,
    )
    return fig

@app.callback(
    Output('R0-violin-fig', 'figure'),
    [Input('class-dropdown', 'value'), Input(component_id='dist_th', component_property='value')])
def violin_R0(sim_name, th):
    return violin_plot("R0", sim_name, th)

@app.callback(
    Output('R1-violin-fig', 'figure'),
    [Input('class-dropdown', 'value'), Input(component_id='dist_th', component_property='value')])
def violin_R1(sim_name, th):
    return violin_plot("R1", sim_name, th)

@app.callback(
    Output('R1_shift-violin-fig', 'figure'),
    [Input('class-dropdown', 'value'), Input(component_id='dist_th', component_property='value')])
def violin_R1(sim_name, th):
    return violin_plot("R1_shift", sim_name, th)

# === Histogram ===
@app.callback(
    Output('R0-hist-fig', 'figure'),
    [Input('class-dropdown', 'value'), Input(component_id='loss_th', component_property='value')])
def hist_R0(sim_name, th):
    return param_histogram("R0", sim_name, th)

@app.callback(
    Output('R1-hist-fig', 'figure'),
    [Input('class-dropdown', 'value'), Input(component_id='loss_th', component_property='value')])
def hist_R1(sim_name, th):
    return param_histogram("R1", sim_name, th)


@app.callback(
    Output('EqualRatio-hist-fig', 'figure'),
    [Input('class-dropdown', 'value'), Input(component_id='loss_th', component_property='value')])
def hist_equalRatio(sim_name, th):
    return param_histogram("equal_ratio", sim_name, th)

@app.callback(
    Output('R1Shift-hist-fig', 'figure'),
    [Input('class-dropdown', 'value'), Input(component_id='loss_th', component_property='value')])
def hist_R1Shift(sim_name, th):
    return param_histogram("R1_shift", sim_name, th)

# County
def countys_fig():
    df = pd.read_csv("log/county.csv", index_col=0)
    return general_plot(
        df,
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
        html.P('Rényi Network Epidemic Research Group',  style={"text-align":"center"}),
        html.Img(src="assets/covid19.png"),
        html.Label("Simulations", className='dropdown-labels'),
        dcc.Dropdown(multi=False, className='dropdown', id='class-dropdown',
                     options=create_dropdown_options(get_folders()),
                     value=get_folders()[0]),
        html.Div(id='drop-info'),
        html.Button("Update", id="update-button"),
        html.Div(children=[
            html.H2('Parameters', className='dropdown-labels'),
            
            html.Div([
                html.Label("Distribution threshold", className='dropdown-labels'),
                dcc.Input(id='dist_th', value='5000', type='number', style={"text-align":"right", 'width': '9vh', 'height': '13px', "float":"right"})
            ]),
            html.Br(),

            html.Div([
                html.Label("Loss threshold", className='dropdown-labels'),
                dcc.Input(id='loss_th', value='600', type='number', style={"text-align":"right", 'width': '9vh', 'height': '13px', "float":"right"})
            ]),
            html.Br(),

        ], style={'width': '100%', 'height': '400px'})

    ], id='left-container'),
    # Right: plots
    html.Div(children=[
        html.Div(children=[
            #dcc.Graph(figure=plot_map(), style={'width': '100%'}),
            #dcc.Graph(figure=plot_map(), style={'width': '100%', 'height': '500px', 'display': 'inline-block'}),
            
            #dcc.Graph(figure=ages_fig(), style={'width': '50%', 'height': '500px', 'display': 'inline-block'}),
            #dcc.Graph(figure=countys_fig(), style={'width': '50%', 'height': '500px', 'display': 'inline-block'}),
            
            # === Timeline ===
            dcc.Graph(id="sims-fig"),

            # === Distributions ===
            # TODO: histogram
            dcc.Graph(id="R0-violin-fig", style={'width': '33%', 'height': '500px', 'display': 'inline-block'}),
            dcc.Graph(id="R1-violin-fig", style={'width': '33%', 'height': '500px', 'display': 'inline-block'}),
            dcc.Graph(id="R1_shift-violin-fig", style={'width': '33%', 'height': '500px', 'display': 'inline-block'}),

            dcc.Graph(id="R0-hist-fig", style={'width': '50%', 'height': '500px', 'display': 'inline-block'}),
            dcc.Graph(id="R1-hist-fig",style={'width': '50%', 'height': '500px', 'display': 'inline-block'}),

            dcc.Graph(id="R1Shift-hist-fig", style={'width': '50%', 'height': '500px', 'display': 'inline-block'}),
            dcc.Graph(id="EqualRatio-hist-fig",style={'width': '50%', 'height': '500px', 'display': 'inline-block'})
        ], id="visualization")
    ], id="right-container")
], id='container')
app.run_server(debug=True, use_reloader=True)  # Turn off reloader if inside Jupyter


# TODO:
#   * more thorough simulations
#   * sliding map with update_layout/trace
#   * left panel values bigger steps
#   * outlook:
#      -> Ground truth BOLD
#      -> green left panel