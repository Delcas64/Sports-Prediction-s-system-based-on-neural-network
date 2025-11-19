import pandas as pd
import os 
import re
from teams import team_codes, parse_matchup, nba_to_myid


ruta_actual = os.path.dirname(os.path.abspath(__file__))
ruta_archivo = os.path.join(ruta_actual, '../data/data_api/Temporada-Regular-2003-2025')


#Para cambiar el ID de las season a 2003-2004...
season_map = {f"2{year}": f"{year}-{year+1}" for year in range(2003, 2025)}

# Listado de las temporadas que te interesan
seasons = [f"{year}-{str(year+1)[-2:]}" for year in range(2003, 2025)] # Esto generaría algo como ['2003-04', '2004-05', etc.]

temporadas = []

#Tenemos las temporadas en dataframes
#Falta limpiar los team_name, team_abbrevation, season_id, y los team_id con los nuevos

#No está bien lo de los ID's, además mirar el orden de las columnas.

for season in seasons:
    temporada_x = pd.read_csv(ruta_archivo+f'/{season}.csv')
    
    temporada_x.drop(columns=['VIDEO_AVAILABLE','MIN'], inplace=True) #Quitamos si hay video disponible y los minutos jugados, siempre hay 240, 48 x 5
    temporada_x[['HOME_TEAM', 'AWAY_TEAM']] = temporada_x['MATCHUP'].apply(
    lambda x: pd.Series(parse_matchup(x, team_codes)))
    temporada_x['SEASON'] = temporada_x['SEASON_ID'].astype(str).map(season_map)
    temporada_x['ID_TEAM'] = temporada_x['TEAM_ID'].map(nba_to_myid)
    temporada_x.drop(columns=['SEASON_ID','TEAM_ABBREVIATION','TEAM_NAME', 'TEAM_ID', 'MATCHUP'], inplace=True)
    temporadas.append(temporada_x)



df_all = pd.concat(temporadas, ignore_index=True)
columnas = [
    'ID_TEAM','GAME_ID','GAME_DATE','SEASON','HOME_TEAM','AWAY_TEAM','WL',
    'FGM','FGA','FG_PCT','FG3M','FG3A','FG3_PCT',
    'FTM','FTA','FT_PCT','OREB','DREB','REB','AST','STL','BLK','TOV','PF','PTS','PLUS_MINUS'
]

df_all = df_all[columnas]

df_all.to_csv('ejemplo.csv', index=False)




#Está bien el .csv, cuidado que por cada partido hay dos filas, una del equipo local y otra del visitante. Ambas con 
#las estadísticas correspondientes a cada equipo, se distingue por el ID_TEAM