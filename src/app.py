# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py:light
#     text_representation:
#       extension: .py
#       format_name: light
#       format_version: '1.5'
#       jupytext_version: 1.16.1
#   kernelspec:
#     display_name: Python 3 (ipykernel)
#     language: python
#     name: python3
# ---

import pandas as pd
import numpy as np
import nba_api_functions as nba
import nba_prop_functions as nbaprop
from dash import Dash, dcc, html, Input, Output, State, Patch, MATCH, ALLSMALLER, callback, dash_table
import pandas as pd
import plotly.express as px


all_players_df = pd.read_csv('player_gamelogs_2023.csv', index_col=None)
game_df = pd.read_csv('team_gamelogs_2023.csv', index_col=None)

# +


app = Dash(__name__)
server = app.server

app.layout = html.Div([
    html.H1('Player Prop Overview'),
    html.Hr(),
    html.Div('Player'),
    dcc.Dropdown(
        options = all_players_df['full_name'].unique(),
        value = 'Derrick White',
        id = 'player-selection'
    ),
    html.Div('Prop'),
    dcc.Dropdown(
        id='prop-selection', multi=True,
        options = ['PTS','AST','REB','BLK','STL'],
        value = ['BLK','STL']
    ),
    html.Div('Over/Under for the prop:'),
    dcc.Input(id='prop-line', type='number', min=0, step=0.5, value=1.5),
    html.Div(''),
    html.Button('Generate Data', id='generate-table', n_clicks=0),
    html.Div(id='player-selected'),
    html.Hr(),
    html.Div(id='stat-overview-table'), 
    html.H2('Player Gamelogs'),
    dcc.RadioItems(options=[
        {'label':'Last 5 games', 'value':'last_5'},
        {'label':'Last 10 games', 'value':'last_10'},
        {'label':'Full Season', 'value':'season'}
    ], 
                   value='last_5', id='radio-items'),
    html.Div(id='player-stats-table')
])

@app.callback(
    [
        Output('player-selected', 'children'),
        Output('player-stats-table','children'),
        Output('stat-overview-table', 'children')
    ],
    [
        Input('generate-table','n_clicks'),
        Input('radio-items', 'value')
    ],
    [
        State('player-selection', 'value'),
        State('prop-selection', 'value'),
        State('prop-line', 'value')
    ]
)


def create_table(n, selected_df, player_selected, prop_selection, prop_line):
    player_df = nbaprop.player_gamelog_name(all_players_df, player_selected)
    combo_prop = '+'.join(prop_selection)
    if len(prop_selection) > 1:
        player_df = nbaprop.create_combo_cols(combo_prop, player_df)
    last_5, last_10, season = nbaprop.player_gamelogs_dfs(player_df)
    prop_results = nbaprop.past_prop_results(last_5, last_10, season, combo_prop, prop_line)
    if selected_df == 'last_5':
        df=last_5
    elif selected_df == 'last_10':
        df=last_10
    else:
        df=season
    player_string = f'Below are the results for {player_selected} successfully hitting the over on {combo_prop} with a line of {prop_line}.'

    df = nbaprop.create_final_table(df)
    gamelogs_table = dash_table.DataTable(
        id='player-stats',
        columns = [{'name':col, 'id':col} for col in df.columns],
        data = df.to_dict('records'),
        page_size=10)
    prop_results_table = dash_table.DataTable(
        id='created-stat-overview-table',
        columns = [{'name':col, 'id':col} for col in prop_results.columns],
        data = prop_results.to_dict('records'))

    return player_string, gamelogs_table, prop_results_table


if __name__ == '__main__':
    app.run_server(debug=True)
