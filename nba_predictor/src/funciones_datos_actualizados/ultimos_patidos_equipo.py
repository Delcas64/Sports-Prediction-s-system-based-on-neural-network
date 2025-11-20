from pathlib import Path

# Obtener la ruta del archivo actual
current_file = Path(__file__)
# Obtener la ruta del directorio padre
parent_dir = current_file.parent.parent

# Añadir la ruta del padre a sys.path (necesario para poder importar)
import sys
sys.path.append(str(parent_dir))
from teams import equipo_id


#Este archivo sirve para ayudar a predecir a la red neuronal ya guardada. Primero se entrena la red neuronal con todos los datos hasta
#la temporada 2025-26. Y luego para predecir, se cogen los últimos 10 partidos, sus estadísitcas y las estadísticas de los jugadores.





from nba_api.stats.endpoints.teamgamelogs import TeamGameLogs #Coge los partidos de un equipo, más robusto que teamgamelog. 
from nba_api.stats.endpoints import boxscoretraditionalv3 #Para las estadisticas del partido 
from datetime import datetime
import pandas as pd

#Para no depender de poner season = 2024-25 o la que toque, y tener que cambiarla cada año.
def get_current_season():
    year = datetime.now().year
    month = datetime.now().month

    if month >= 10:  # Octubre -> empieza temporada nueva
        start_year = year
        end_year = year + 1
    else:           # Antes de octubre sigue temporada del año anterior
        start_year = year - 1
        end_year = year

    return f"{start_year}-{str(end_year)[2:]}"



def ultimos_partidos(equipo,numeroPartidos = 10): #Asumimos que se pasa el equipo como "Atlanta Hawks", en String
    
    team_id = equipo_id[equipo]
    #Coger los últimos 10 partidos más actuales
    season = get_current_season()
    #Regular Season, ya que no se puede coger los últimos 5 así como así
    partidos_equipo = TeamGameLogs(season_nullable = season, team_id_nullable=team_id ).get_data_frames()[0] #Esto coge todos los partidos del equipo.

    #Pasamos las fechas a datetime, para el tema del uso de las fechas.
    partidos_equipo['GAME_DATE'] = pd.to_datetime(partidos_equipo['GAME_DATE'])

    df_partidos = partidos_equipo.sort_values('GAME_DATE',ascending = False) #Así devuelve los partidos ordenados por las últimos fechas
    #Coger los últimos numeroPartidos
    df_final = df_partidos.head(numeroPartidos)

    #Ya tenemos los últios partidos, ahora pillar las estadísticas de estos
    print(df_final.columns)

    df_estadisticas = pd.DataFrame()

    for _,partido in df_final.iterrows():
        game_id = partido['GAME_ID']
        
        box = boxscoretraditionalv3.BoxScoreTraditionalV3(game_id = game_id)
        equipos_stats = box.get_data_frames()[0] #Devuelve estadísticas de jugadores y de los equipos todo junto.
        
        #El isna(), cogemos las filas que no son de jugador, es decir, las que tienen como Player_ID, NA,
        #Ya que BoxScoreTradtionalV3 devuelve un dataframe con todo mezclado del partido,
        team_stats = equipos_stats[(equipos_stats["TEAM_ID"] == team_id) & (equipos_stats['PLAYER_ID'].isna())] 
        rival_stats = equipos_stats[(equipos_stats["TEAM_ID"] != team_id) & (equipos_stats['PLAYER_ID'].isna())]
        
        #Concatenaciones
        stats_totales = pd.concat([team_stats,rival_stats], ignore_index=True)
        df_estadisticas = pd.concat([df_estadisticas,stats_totales],ignore_index=True)
    
    return df_estadisticas



print(ultimos_partidos("Chicago Bulls"))



