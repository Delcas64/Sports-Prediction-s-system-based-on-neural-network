import  nba_api.stats.static.players as jugadores
from nba_api.stats.endpoints import playergamelog
import pandas as pd

import time

df_jugadores  = pd.DataFrame(jugadores.get_active_players())


df_partidos_jugadores_activos = pd.DataFrame()

for idx, jugador in df_jugadores.iterrows():
    player_id = jugador['id']
    nombre =   jugador['full_name']

    try:
        gamelog = playergamelog.PlayerGameLog(player_id=player_id, season='2024-25')

        df_gamelog = gamelog.get_data_frames()[0]
        df_gamelog['player_name'] = nombre

        df_partidos_jugadores_activos= pd.concat([df_partidos_jugadores_activos,df_gamelog], ignore_index=True)


        print(f'Descargado el jugador: {nombre}')
        time.sleep(1)

    except Exception as e:
        print(f'Error al descargar el jugador: {nombre} - {e}')



df_partidos_jugadores_activos.to_csv('./stats_jugadores_2024.csv', index=False)


"""
for season in range(2003, 2025):
    season_str = f"{season}-{str(season+1)[2:]}"
    gamelog = playergamelog.PlayerGameLog(player_id=player_id, season=season_str)
"""