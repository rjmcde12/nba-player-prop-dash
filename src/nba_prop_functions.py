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
import nba_api
import nba_api_functions as nba
from nba_api.stats.static import players
from nba_api.stats.static import teams
from nba_api.stats.endpoints import commonteamroster as rosters
from nba_api.stats.endpoints import playergamelog
from nba_api.stats.endpoints import playbyplayv2 as pbp
from nba_api.stats.endpoints import commonallplayers
from nba_api.stats.endpoints import teamgamelog
from nba_api.stats.endpoints import winprobabilitypbp as winprob
from nba_api.stats.endpoints import BoxScoreAdvancedV3 as box
import time
pd.options.mode.copy_on_write = True


def player_gamelog_id(df, player_id):
    player_df = df[df['Player_ID'] == player_id]
    return player_df


def player_gamelog_name(df, full_name):
    player_df = df[df['full_name'] == full_name]
    return player_df


def player_last_x_gamelogs(player_df, games=112):
    player_df = player_df.copy()
    player_df.sort_values(by='team_game_no', ascending=False, inplace=True)
    player_df = player_df.reset_index(drop=True)
    last_x = player_df.iloc[:games]
    return last_x


def player_last_x_avg(player_df, games=None):
    last_x = player_last_x_gamelogs(player_df, games)
    avg_x = last_x[['MIN','PTS','REB','AST','STL','BLK']].mean().reset_index()
    if games is not None:
        avg_x.columns = ['Stat',('Last ' + str(games) + ' Avg')]
    else:
        avg_x.columns = ['Stat','Season Avg']
    avg_x = avg_x.copy()
    avg_x.set_index('Stat', inplace=True)
    avg_x = avg_x.T
    return avg_x


def player_gamelogs_dfs(player_df):
    last_5 = player_last_x_gamelogs(player_df, 5)
    last_10 = player_last_x_gamelogs(player_df, 10)
    season = player_df.sort_values(by='team_game_no', ascending=False)
    return last_5, last_10, season


def stat_overview(player_df):
    avg_5 = player_last_x_avg(player_df, 5)
    avg_10 = player_last_x_avg(player_df, 10)
    avg_season = player_last_x_avg(player_df)
    averages = pd.concat([avg_5, avg_10, avg_season])
    averages = averages.map(lambda x: round(x, 1))
    display(averages)
    display(player_last_x_gamelogs(player_df, 5))
    return avg_5, avg_10, avg_season, averages


# +
def percent_to_decimal(percent_odds):
    if percent_odds == 0:
        return np.nan
    elif percent_odds > 0 and percent_odds <= 1:
        return 1 / percent_odds
    elif percent_odds > 1:
        return 100 / percent_odds
    else:
        return 0

def decimal_to_american(decimal_odds):
    if decimal_odds == 0:
        return 0
    elif decimal_odds > 2:
        return round((100) * (decimal_odds - 1))
    else:
        return round(-100 / (decimal_odds - 1))

def decimal_to_american_str(decimal_odds):
    if np.isnan(decimal_odds):
        return 'NL'
    elif decimal_odds == 0:
        return 'NL'
    elif decimal_odds == 1:
        return 'NL'
    elif decimal_odds > 2:
        return '+' + str(round((100) * (decimal_odds - 1)))
    else:
        return str(round(-100 / (decimal_odds - 1)))

def percent_to_american_str(percent_odds):
    decimal_odds = percent_to_decimal(percent_odds)
    return decimal_to_american_str(decimal_odds)


# -

def create_combo_cols(prop, player_df):
    prop_list = prop.split('+')
    num_props = len(prop_list)

    
    if num_props == 2:
        player_df.loc[:, prop] = player_df[prop_list[0]] + player_df[prop_list[1]]
    elif num_props == 3:
        player_df.loc[:, prop] = player_df[prop_list[0]] + player_df[prop_list[1]] + player_df[prop_list[2]]
    elif num_props == 4:
        player_df.loc[:, prop] = player_df[prop_list[0]] + player_df[prop_list[1]] + player_df[prop_list[2]] + player_df[prop_list[3]]
    if num_props == 5:
        player_df.loc[:, prop] = player_df[prop_list[0]] + player_df[prop_list[1]] + player_df[prop_list[2]] + player_df[prop_list[3]] + player_df[prop_list[4]]

    player_df.insert(11, prop, player_df.pop(prop))

    return player_df


def past_prop_results(last_5, last_10, season, prop, line):
    hit_last_5 = (last_5[prop] > line).sum()
    hit_last_10 = (last_10[prop] > line).sum()
    hit_season = (season[prop] > line).sum()
    total_games = len(season['matchup'])

    if total_games != 0:
        hit_pct_5 = (hit_last_5 / 5) * 100
        hit_pct_10 = (hit_last_10 / 10) * 100
        hit_pct_season = round((hit_season / total_games) * 100, 1)
    
        player_rolling = season.copy()
        
        player_rolling['covered'] = player_rolling[prop].apply(lambda x: 1 if x > line else 0)
        
        player_rolling['rolling_5'] = player_rolling['covered'].transform(lambda x: x.rolling(window=5, min_periods=0).sum()).fillna(0) 
        player_rolling['rolling_5_pct'] = player_rolling['rolling_5'] / 5
        player_rolling['rolling_10'] = player_rolling['covered'].transform(lambda x: x.rolling(window=10, min_periods=0).sum()).fillna(0) 
        player_rolling['rolling_10_pct'] = player_rolling['rolling_10'] / 10
        
        hit_pct_roll_5 = round(player_rolling['rolling_5_pct'].mean(), 1) * 100
        hit_pct_roll_10 = round(player_rolling['rolling_10_pct'].mean(), 1) * 100
        
        data = {
            'Stat':['Last 5', 'Last 5 Rolling Avg', 'Last 10', 'Last 10 Rolling Avg', 'Season'],
            '# Hits':[hit_last_5, '-', hit_last_10, '-', hit_season],
            '% Hit':[hit_pct_5, hit_pct_roll_5, hit_pct_10, hit_pct_roll_10, hit_pct_season]
        }

        df_results = pd.DataFrame(data)
        
        df_results['Fair Odds'] = df_results['% Hit'].apply(lambda x: percent_to_american_str(x))

    else:
        data = {
            'Stat':['Last 5', 'Last 5 Rolling Avg', 'Last 10', 'Last 10 Rolling Avg', 'Season'],
            '# Hits':[0, 0, 0, 0, 0],
            '% Hit':[0, 0, 0, 0, 0]
        }
        
        df_results = pd.DataFrame(data)
        df_results['Fair Odds'] = 'NL'
        
    # df_results.set_index('Stat', inplace=True)
    
        
    return df_results


def player_prop_overview(df):
    print('First Name:')
    first_name = input()
    print('Last Name:')
    last_name = input()
    print('Prop: (if combo prop separate with +)')
    prop = input()
    print('Line:')
    line = float(input())
    player_id = nba.get_player_id(first_name, last_name)
    player_df = nbaprop.player_gamelog(df, player_id)
    prop_list = prop.split('+')
    if len(prop_list) > 1:
        player_df = nbaprop.create_combo_cols(prop, player_df)
    else:
        pass
    last_5, last_10, season = nbaprop.player_gamelogs_dfs(player_df)
    prop_results = nbaprop.past_prop_results(last_5, last_10, season, prop, line)
    print(f'{first_name} {last_name} season results for over {str(line)} {prop}')
    display(prop_results)
    nbaprop.stat_overview(player_df)


def player_stats_dash(df, player_name):
    first_name, last_name = player_name.split()
    player_id = nba.get_player_id(first_name, last_name)
    player_df = nbaprop.player_gamelog(df, player_id)
    last_5, last_10, season = nbaprop.player_gamelogs_dfs(player_df)
    return last_5, last_10, season


def create_final_table(df):
    df = df.rename(columns={
        'game_date':'Game Date', 'team_short':'Team', 'matchup':'Matchup', 'outcome':'Outcome', 'team_game_no':'Game #'
    })
    
    df['Game #'] = df['Game #'].astype(int)
    df.drop(columns='full_name', inplace=True)

    return df
