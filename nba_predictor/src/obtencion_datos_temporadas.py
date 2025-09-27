from nba_api.stats.static import teams
from nba_api.stats.endpoints import leaguegamelog 
import pandas as pd
import numpy as np
import matplotlib.pyplot as plot
from pathlib import Path


data_dir = Path('../data/data_api')


# Asegurarse de que el directorio existe (crear padres también)
try:
    data_dir.mkdir(parents=True, exist_ok=True)
    print(f"Directorio creado/verificado: {data_dir.absolute()}")
except Exception as e:
    print(f"Error creando directorio: {e}")
    # Fallback: usar directorio actual
    data_dir = Path('./data_api/')
    data_dir.mkdir(parents=True, exist_ok=True)
    print(f"Usando directorio alternativo: {data_dir.absolute()}")


# Listado de las temporadas que te interesan
seasons = [f"{year}-{str(year+1)[-2:]}" for year in range(2003, 2025)] # Esto generaría algo como ['2003-04', '2004-05', etc.]

all_games = pd.DataFrame() # DataFrame vacío para ir agregando los datos

for season in seasons:
    try:
        print(f"Obteniendo datos para la temporada: {season}")
        # Hacemos la llamada a la API
        file_path = data_dir / f'{season}.csv'
        log = leaguegamelog.LeagueGameLog(season=season, season_type_all_star="Regular Season")
        games_df = log.get_data_frames()[0]
        # Concatenamos los datos al DataFrame principal
        games_df.to_csv(f'../data/data_api/{season}.csv',index= False)
        all_games = pd.concat([all_games, games_df], ignore_index=True)
        
        #Pausa para no saturar la API
        import time
        time.sleep(1)
    except Exception as e:
        print(f"Error al obtener datos para la temporada {season}: {e}")

# Aquí 'all_games' contendrá la información de todos los partidos
# de la temporada regular desde 2003 hasta la actualidad.
print("\nDatos totales obtenidos:")
print(all_games.info())


#Mirar porque ya tengo los csv guardados

all_games = all_games.drop('TEAM_NAME', axis=1) #axis 1 para columnas

print(all_games.info())


