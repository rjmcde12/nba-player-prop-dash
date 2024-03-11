mongoimport --uri mongodb+srv://rjmcde12:nbaPROPdb18@nba-stats.7yfcx7v.mongodb.net/nba-stats --collection player_stats --type CSV --file player_gamelogs_2023_update.csv --headerline

mongoimport --uri mongodb+srv://rjmcde12:nbaPROPdb18@nba-stats.7yfcx7v.mongodb.net/nba-stats --collection team_gamelogs --type CSV --file team_gamelogs_2023_update.csv --headerline