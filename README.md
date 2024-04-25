# nba-player-prop-dash

https://nba-player-prop-dash.onrender.com/
(site may take a minute or so to load. the server spins down after a period of inactivity)

Webpage built via Dash that allows the user to select a player and a statistic (or combo of statistics) and a projected line to determine how they have performed over various lengths of time.

The data is pulled from the nba_api and is updated daily. Historical data since 2016 (as far back as data on the API goes) has also been collected and in the future will be used to incorporate into the analysis. Currently only regular season stats are included. Working through issues with a difference in how playoff stats are presented in the API.

Explantion of statistic:

Hits: Count of how often over the corresponding time span the player hit the prop bet.
Note:Only wins are included in the count. Pushes are marked as a loss.

Hits: Takes # Hit and converts it to a percentage.

Fair Odds: Translates the corresponding % Hit to American odds. If you believe a particular stat to be an accurate estimationof the odds for the prop winning, this would be the break even point for the bet. If you can find odds at a sportsbook with a better payout, it would be a positive Expected Value bet.

Last 5/10: Results from previous 5/10 games played by the player.

Rolling 5/10: This looks at the % Hit for every unique 5/10 consecutive game stretch and then takes the average of those.

Season: Results of all games played by the player this season. Total games in parentheses.

B2B: Results from the second game of back-backs this season. Only counts as a back-to-back if the player appeared in both games. Total B2B games in parentheses
