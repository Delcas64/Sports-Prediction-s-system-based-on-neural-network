from pathlib import Path

# Obtener la ruta del archivo actual
current_file = Path(__file__)
# Obtener la ruta del directorio padre
parent_dir = current_file.parent.parent

# Añadir la ruta del padre a sys.path (necesario para poder importar)
import sys
sys.path.append(str(parent_dir))
from teams import equipo_id

from nba_api.stats.endpoints.leaguegamelog import LeagueGameLog #Para coger los partidos tanto de temporada regular como de playoffs, teamgamelog solo de temporada regular
from nba_api.stats.endpoints import boxscoretraditionalv2 #Para las estadisticas del partido 
from datetime import datetime
import pandas as pd

#Para no depender de poner season = 2024-25
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
    fechaActual =  datetime.now()
    #Coger los últimos 10 partidos más actuales
    season = get_current_season()
    #Regular Season, ya que no se puede coger los últimos 5 así como así
    partidos_id_regular = LeagueGameLog(season = season, season_type='Regular Season' ).get_data_frames()[0]

    df_reg_equipo = partidos_id_regular[partidos_id_regular["TEAM_ID"] == team_id]
    #Playoffs
    partidos_id_playoffs = LeagueGameLog(season=season, season_type='Playoffs').get_data_frames()[0]

    df_playoffs_equipo = partidos_id_playoffs[partidos_id_playoffs["TEAM_ID"] == team_id]

    df_partidos = pd.concat([df_reg_equipo, df_playoffs_equipo]) #Tenemos todos los partidos del equipo X

    #Coger los últimos numeroPartidos

    df_partidos["GAME_DATE"] = pd.to_datetime(df["GAME_DATE"]) #Pasamoe la fecha a datetime
    df = df_partidos.sort_values("GAME_DATE",ascending = False) #Así devuelve los partidos ordenados por las últimos fechas

    df_final = df.head(numeroPartidos)

    #Ya tenemos los últios partidos, ahora pillar las estadísticas de estos

    partidos = df_final.values

    df_estadisticas = pd.DataFrame()

    for partido in partidos:
        box = boxscoretraditionalv2.BoxScoreTraditionalV2(game_id = partido["GAME_ID"])
        estadisticas = box.get_data_frames[1]
        estadisticas_rival = box.get_data_frames[3]
        stats_totales = pd.concat([estadisticas,estadisticas_rival])
        df_estadisticas = df_estadisticas.append(stats_totales, ignore_index=True)
    
    return df_estadisticas


print(ultimos_partidos("Chicago Bulls"))



