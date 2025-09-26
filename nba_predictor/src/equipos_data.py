from nba_api.stats.static import teams
from nba_api.stats.endpoints import leaguegamelog 
import pandas as pd
import numpy as np
import matplotlib.pyplot as plot


dt = teams.get_teams()
equipos = np.array(dt)

#for i in equipos:
#    print(i)
    
    
celtics = teams.find_teams_by_full_name("Boston Celtics")


narrray = np.array(celtics)



# Listado de las temporadas que te interesan
seasons = [f"{year}-{str(year+1)[-2:]}" for year in range(2003, 2025)] # Esto generaría algo como ['2003-04', '2004-05', etc.]

all_games = pd.DataFrame() # DataFrame vacío para ir agregando los datos

for season in seasons:
    try:
        print(f"Obteniendo datos para la temporada: {season}")
        # Hacemos la llamada a la API
        log = leaguegamelog.LeagueGameLog(season=season, season_type_all_star="Regular Season")
        games_df = log.get_data_frames()[0]
        # Concatenamos los datos al DataFrame principal
        games_df.to_csv(f'../data/data_api/{season}.csv',index= False)
        all_games = pd.concat([all_games, games_df], ignore_index=True)
    except Exception as e:
        print(f"Error al obtener datos para la temporada {season}: {e}")

# Aquí 'all_games' contendrá la información de todos los partidos
# de la temporada regular desde 2003 hasta la actualidad.
print("\nDatos totales obtenidos:")
print(all_games.info())

temporada_2003 = all_games.iloc[1]
for i in temporada_2003.items():
    print(i)
