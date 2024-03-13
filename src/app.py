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
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
import pymongo                                                  
from bson.objectid import ObjectId
from dotenv import load_dotenv
import os
import schedule
import time
from datetime import datetime
dbc_css = "https://cdn.jsdelivr.net/gh/AnnMarieW/dash-bootstrap-templates/dbc.min.css"


# +
# file_path = '/Users/ryan/DashApps/nba_prop/'
# all_players_df = pd.read_csv(f'{file_path}player_gamelogs_2023.csv', index_col=None)
# game_df = pd.read_csv(f'{file_path}team_gamelogs_2023.csv', index_col=None)

# +
def fetch_data_from_database():
    # connecting to mongodb
    load_dotenv()
    uri = os.getenv('URI')
    client = pymongo.MongoClient(uri)
    db = client['nba_stats']
    
    # creating pandas df for players stats
    player_stats = db['player_gamelogs']
    player_cursor = player_stats.find()
    all_players_df = pd.DataFrame(list(player_cursor))
    all_players_df = all_players_df.drop(columns='_id')
    
    
    # creating pandas df for team gamelogs
    team_gamelogs = db['team_gamelogs']
    team_cursor = team_gamelogs.find()
    game_df = pd.DataFrame(list(team_cursor))
    game_df = game_df.drop(columns='_id')
    print("Database update successful at:", datetime.now())

    return all_players_df, game_df

all_players_df, game_df = fetch_data_from_database()


# +
default_table_style = {
    'overflowX': 'auto',
    'border': '1px solid #dee2e6',
    'borderCollapse': 'collapse',
    'width': '100%',
    'marginBottom': '0'
}

default_header_style = {
    'backgroundColor': '#f8f9fa',
    'fontWeight': 'bold',
    'border': '1px solid #dee2e6',
    'textAlign': 'center'
}

default_cell_style = {
    'textAlign': 'left',
    'padding': '8px',
    'border': '1px solid #dee2e6'
}

default_conditional_style = [
    {
        'if': {'row_index': 'odd'},
        'backgroundColor': 'rgba(248, 248, 248, 0.8)'
    },
    {
        'if': {'row_index': 'even'},
        'backgroundColor': 'rgba(255, 255, 255, 0.8)'
    }
]

default_styles = {
    'style_table': default_table_style,
    'style_header': default_header_style,
    'style_cell': default_cell_style,
    'style_data_conditional': default_conditional_style
}
# -




# +


app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP, dbc_css])
server = app.server

app.layout = html.Div(className='dbc', children=[
    dbc.Container(children = [ #can add style={} here
            dbc.Row([
            dbc.Col(html.H1('Player Prop Overview', style={'textAlign':'center', 'margin-bottom':'30px'}), width=12)
        ], justify='center'),
        dbc.Stack([
                html.Div('Player', style={'textAlign':'left'}),
                dcc.Dropdown(
                    options = all_players_df['full_name'].unique(),
                    value = 'Derrick White',
                    id = 'player-selection',
                    style={'width':'250px'}
                ),
                html.Div('Prop', style={'textAlign':'left'}),
                dcc.Dropdown(
                    id='prop-selection', multi=True,
                    options = [{'value':'PTS', 'label':'PTS'},{'value':'AST', 'label':'AST'},{'label':'REB', 'value':'REB'},
                               {'label':'BLK', 'value':'BLK'}, {'label':'STL', 'value':'STL'}, {'value':'3PT', 'label':'3PT'}],
                    value = ['BLK','STL'],
                    style={'width':'400px'}
                ),
                html.Div('Total for the prop:'),
                dbc.Input(id='prop-line', type='number', min=0, step=0.5, value=1.5, style={'width':'100px'}),
                dbc.RadioItems(
                    options=[{'label':'Over', 'value':'Over'},{'label':'Under', 'value':'Under'}],
                    value='Over', id='prop-side', style={'width':'auto', 'align':'left'}
                )
                ], gap=2, style={'size':'auto'}),
        html.Div(''),
        html.Div(
            dbc.Button(
                'Generate Data', id='generate-table', class_name='me-1', n_clicks=0, style={'margin-bottom':'5px', 'margin-top':'10px'})
        ),
        html.Div(id='b2b-warning'),
        html.Hr(), 
        html.Div(children = [
            dbc.Row([
                dbc.Col([
                    html.H3(children = [
                        ('Past Prop Results'),
                            dbc.Button('?',id='open', class_name={'color':'ms-auto'}, n_clicks=0),
                            dbc.Modal(
                                [
                                    dbc.ModalHeader(dbc.ModalTitle('Data Explained')),
                                    dbc.ModalBody([
                                        html.P([
                                            html.Strong('# Hits:'),
                                            ' Count of how often over the corresponding time span the player hit the prop bet.'
                                        ]) ,
                                        html.P([
                                            html.Strong('Note:'),
                                            'Only wins are included in the count. Pushes are marked as a loss.'
                                        ]),
                                        html.P([
                                            html.Strong('Hits:'),
                                            ' Takes # Hit and converts it to a percentage.'
                                        ]),
                                        html.P([
                                            html.Strong('Fair Odds:'),
                                            ' Translates the corresponding % Hit to American odds. If you believe a particular stat to be an accurate estimation' 
                                            'of the odds for the prop winning, this would be the break even point for the bet. If you can find odds at a sportsbook'
                                            ' with a better payout, it would be a positive Expected Value bet.'
                                        ]),
                                        html.P([
                                            html.Strong('Last 5/10:'),
                                            ' Results from previous 5/10 games played by the player.'
                                        ]),
                                        html.P([
                                            html.Strong('Rolling 5/10:'),
                                            ' This looks at the % Hit for every unique 5/10 consecutive game stretch and then takes the average of those.'
                                        ]),
                                        html.P([
                                            html.Strong('Season:'),
                                            ' Results of all games played by the player this season. Total games in parentheses.'
                                        ]),
                                        html.P([
                                            html.Strong('B2B:'),
                                            ' Results from the second game of back-backs this season. Only counts as a back-to-back if the player'
                                            ' appeared in both games. Total B2B games in parentheses'
                                        ])
                                    ]),
                                    dbc.ModalFooter(
                                        dbc.Button(
                                            'Close', id='close', class_name='ms-auto', n_clicks=0
                                        )
                                    )
                                ],id='modal', centered=True, is_open=False 
                            )], style={'display': 'flex', 'flex':'1'}),
                    html.Div(id='stat-overview-table')
                ], class_name='col col-auto'
                       ),
                dbc.Col([  
                    html.H3('Player Averages'),
                    html.Div(id='averages-table')
                ],class_name='col col-auto'
                       ),
            ], style={'justify':'center'})
        ]
                ), 
        html.Hr(),
        html.H3('Player Gamelogs',style={'margin-bottom':'5px', 'margin-top':'10px'}),
        html.H5(id = 'next-opp-header'),
        html.Div(id='next-opp-gamelogs', style={'size':'auto','overflow':'auto'}),
        html.H5('Recent Games'),
        html.Div(
            [
                dbc.Tabs(
                    [
                        dbc.Tab(label='Last 5', tab_id='last_5'),
                        dbc.Tab(label='Last 10', tab_id='last_10'),
                        dbc.Tab(label='Season', tab_id='season'),
                        dbc.Tab(label='B2B', tab_id='b2b')
                    ],
                    id='tab-chosen',
                    active_tab='last_5'
                ),
        html.Div(id='player-stats-table-2', style={'size':'auto','overflow':'auto'})
            ]
        ),
        dcc.Graph(id='prop-graph')
    ])
])

@app.callback(
    Output('modal','is_open'),
    [Input('open', 'n_clicks'), Input('close','n_clicks')],
    State('modal','is_open'),
)

def table_explainer(n1, n2, is_open):
    if n1 or n2:
        return not is_open
    else:
        return is_open

@app.callback(
    [
        Output('b2b-warning', 'children'),
        Output('stat-overview-table', 'children'),
        Output('averages-table', 'children'),
        Output('next-opp-header', 'children'),
        Output('next-opp-gamelogs', 'children'),
        Output('player-stats-table-2','children'),
        Output('prop-graph','figure')
    ],
    
    [
        Input('generate-table','n_clicks'),
        Input('tab-chosen', 'active_tab')
    ],
    [
        
        State('player-selection', 'value'),
        State('prop-selection', 'value'),
        State('prop-line', 'value'),
        State('prop-side', 'value')
    ]
)


def create_tables(n, selected_tab, player_selected, prop_selection, prop_line, prop_side):
    
    player_df = nbaprop.player_gamelog_name(all_players_df, player_selected)
    player_df = nbaprop.add_b2b_flag(player_df)
    player_df.insert(14, '3PT', player_df.pop('3PT'))
    avg_table = nbaprop.stat_overview(player_df)
    player_id = player_df.loc[0,'player_id']
    player_df = player_df.sort_values(by='team_game_no', ascending=False).reset_index(drop=True)
    next_opp = player_df.loc[0, 'next_game_opp']
    opp_df = nbaprop.player_gamelogs_opp(player_df, next_opp)
    combo_prop = '+'.join(prop_selection)
    
    
    if len(prop_selection) > 1:
        player_df = nbaprop.create_combo_cols(combo_prop, player_df)
        opp_df = nbaprop.create_combo_cols(combo_prop, opp_df)
    else:
        pass
        
    last_5, last_10, season, b2b = nbaprop.player_gamelogs_dfs(player_df)
    prop_results = nbaprop.past_prop_results(last_5, last_10, season, b2b, combo_prop, prop_line, prop_side)

    b2b_warning = nbaprop.coming_off_b2b(player_id, season)
    opp_df = nbaprop.create_final_table(opp_df)
    
    if b2b_warning == 'Yes':
        b2b_message = dbc.Alert(f'Heads up: {player_selected} is coming off a back-to-back.', color='danger', style={'width':'auto'})
    else:
        b2b_message = ''

    player_string = f'Below are the results for {player_selected} successfully hitting the {prop_side} on {combo_prop} with a line of {prop_line}.'
    opp_header = f'vs {next_opp}:'

    prop_results, avg_table = nbaprop.drop_b2b_row(prop_results, avg_table, b2b_warning)

    prop_results_table = dbc.Table.from_dataframe(prop_results, striped=True, bordered=True, hover=True, style={'width':'auto'})

    avg_table = dbc.Table.from_dataframe(avg_table, striped=True, bordered=True, hover=True, style={'width':'auto'})
    
    if len(opp_df) == 0:
        opp_table = (f'{player_selected} has not played against {next_opp} yet this season.')
    else:    
        opp_table = dbc.Table.from_dataframe(opp_df, striped=True, bordered=True, hover=True, style={'width':'auto'})

    if selected_tab == 'last_5':
        df = last_5
    elif selected_tab == 'last_10':
        df = last_10
    elif selected_tab == 'season':
        df = season
    elif selected_tab == 'b2b':
        df = b2b

    tab_log_df = nbaprop.create_final_table(df)
    
    games_in_graph = len(tab_log_df)
    x_tickvals = tab_log_df['Game #'].tolist()
    step = max(len(x_tickvals) // 10, 1)
    x_tickvals = x_tickvals[::step]
    fig = px.line(tab_log_df, x='Game #', y=combo_prop, title=f'Past Results for {combo_prop}', markers=True)
    fig.update_xaxes(tickvals=x_tickvals, ticktext=[str(val) for val in x_tickvals])
    fig.add_hline(y=prop_line, line_dash='dash', line_color='red', annotation_text=f'Line {prop_line}', annotation_position='left')

    

    gamelogs_tab = dash_table.DataTable(
        id='player-stats',
        columns = [{'name':col, 'id':col} for col in tab_log_df.columns],
        data = tab_log_df.to_dict('records'),
        page_size=10,
        **default_styles
    )

    return  b2b_message, prop_results_table, avg_table, opp_header, opp_table, gamelogs_tab, fig



if __name__ == '__main__':
    app.run_server(debug=True)
    # app.run_server(debug=True, port=8051)
