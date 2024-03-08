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
# player_df = nbaprop.player_gamelog_name(all_players_df, 'Jayson Tatum')
# season = player_df.sort_values(by='team_game_no', ascending = False)
# season

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
    html.H4(id='b2b-warning', style={'background-color':'yellow'}),
    html.Hr(),
    html.Div(id='stat-overview-table'), 
    html.H2('Player Gamelogs'),
    html.H3(id = 'next-opp-header'),
    html.Div(id='next-opp-gamelogs'),
    html.H3('Recent Games'),
    dcc.RadioItems(options=[
        {'label':'Last 5 games', 'value':'last_5'},
        {'label':'Last 10 games', 'value':'last_10'},
        {'label':'Full Season', 'value':'season'},
        {'label':'Back to Backs', 'value':'b2b'}
    ], 
                   value='last_5', id='radio-items'),
    html.Div(id='player-stats-table'),
    dcc.Graph(id='prop-graph')
])

@app.callback(
    [
        Output('player-selected', 'children'),
        Output('b2b-warning', 'children'),
        Output('stat-overview-table', 'children'),
        Output('next-opp-header', 'children'),
        Output('next-opp-gamelogs', 'children'),
        Output('player-stats-table','children'),
        Output('prop-graph','figure'),
        
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
    player_df = nbaprop.add_b2b_flag(player_df)
    player_id = player_df.loc[0,'Player_ID']
    next_opp = nbaprop.player_next_opp(player_id)
    opp_df = nbaprop.player_gamelogs_opp(player_df, next_opp)
    combo_prop = '+'.join(prop_selection)
    next_opp = nbaprop.player_next_opp(player_id)
    
    if len(prop_selection) > 1:
        player_df = nbaprop.create_combo_cols(combo_prop, player_df)
        opp_df = nbaprop.create_combo_cols(combo_prop, opp_df)
    else:
        pass
        
    last_5, last_10, season, b2b = nbaprop.player_gamelogs_dfs(player_df)
    prop_results = nbaprop.past_prop_results(last_5, last_10, season, b2b, combo_prop, prop_line)
    
    if selected_df == 'last_5':
        df = last_5
    elif selected_df == 'last_10':
        df = last_10
    elif selected_df == 'b2b':
        df = b2b
    else:
        df = season
    
    b2b_warning = nbaprop.coming_off_b2b(player_id, df)
    df = nbaprop.create_final_table(df)
    opp_df = nbaprop.create_final_table(opp_df)
    
    if b2b_warning == 'Yes':
        b2b_message = f'Heads up, {player_selected} is coming off a back-to-back.'
    else:
        b2b_message = ''

    player_string = f'Below are the results for {player_selected} successfully hitting the over on {combo_prop} with a line of {prop_line}.'
    opp_header = f'vs {next_opp}:'

    if len(opp_df) == 0:
        opp_table = (f'{player_selected} has not played against {next_opp} yet this season.')
    else:    
        opp_table = dash_table.DataTable(
            id='next-opp-gamelogs-table',
            columns = [{'name':col, 'id':col} for col in opp_df.columns],
            data = opp_df.to_dict('records'))
    
    prop_results_table = dash_table.DataTable(
        id='created-stat-overview-table',
        columns = [{'name':col, 'id':col} for col in prop_results.columns],
        data = prop_results.to_dict('records'))
    
    gamelogs_table = dash_table.DataTable(
        id='player-stats',
        columns = [{'name':col, 'id':col} for col in df.columns],
        data = df.to_dict('records'),
        page_size=10)

    games_in_graph = len(df)
    x_values = list(range(1, games_in_graph + 1))
    fig = px.line(df, x=x_values, y=combo_prop, title=f'Past Results for {combo_prop}', markers=True)
    fig.add_hline(y=prop_line, line_dash='dash', line_color='red')
    

    return player_string, b2b_message, prop_results_table, opp_header, opp_table, gamelogs_table, fig


if __name__ == '__main__':
    app.run_server(debug=True)
