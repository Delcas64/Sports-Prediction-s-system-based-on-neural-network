from nba_api.stats.endpoints import leaguegamelog
import os
import pandas as pd

rutaActual = os.path.dirname(os.path.abspath(__file__))
rutaArchivo = os.path.join(rutaActual, '../data/data_api/Playoffs-2003-2025')




seasons = [f"{year}-{str(year+1)[-2:]}" for year in range(2003, 2025)]


games_playoffs = pd.DataFrame() #DataFrame para ir agregando los datos


for season in seasons:
    try:
        print(f'Obteniendo datos de los playoffs de la temporada: {season}')
        nombreArchivo = rutaArchivo+ f'/{season}.csv'
        log = leaguegamelog.LeagueGameLog(season=season, season_type_all_star="Playoffs")
        playoffs_df = log.get_data_frames()[0]
        # Concatenamos los datos al DataFrame principal
        playoffs_df.to_csv(nombreArchivo,index= False)
        games_playoffs = pd.concat([games_playoffs, playoffs_df], ignore_index=True)
        import time
        time.sleep(1)
    except Exception as e:
        print(f'Error al obtener los datos de la temporada {season} : {e}')


print(games_playoffs.tail())