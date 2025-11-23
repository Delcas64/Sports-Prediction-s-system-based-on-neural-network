import pandas as pd
import os 
from nba_predictor.src.obtencion_datos.teams import parse_matchup, team_codes

rutaActual = os.path.dirname(__file__)
rutaArchivo = os.path.join(rutaActual,'../../stats_jugadores_2024.csv')


df = pd.read_csv(rutaArchivo)

temporada = '2024-2025'


df[['HOME_TEAM', 'AWAY_TEAM']] = df['MATCHUP'].apply(lambda x: pd.Series(parse_matchup(x,team_codes)))
df['SEASON'] = df['SEASON_ID']
df['SEASON'] = temporada

df.drop(columns=['VIDEO_AVAILABLE', 'SEASON_ID', 'MATCHUP','REB'], inplace=True)
columnas= ['player_name','Player_ID','SEASON','GAME_DATE','HOME_TEAM','AWAY_TEAM','Game_ID','MIN','FGM','FGA','FG_PCT','FG3M','FG3A','FG3_PCT','FTM','FTA',
             'FT_PCT','OREB','DREB','AST','STL','BLK','TOV','PF','PTS','PLUS_MINUS','WL']

df = df[columnas]

df.to_csv('stats_jugadores_limpias.csv',index=False)