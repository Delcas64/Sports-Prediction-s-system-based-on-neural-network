from pathlib import Path

# Obtener la ruta del archivo actual
current_file = Path(__file__)
# Obtener la ruta del directorio padre
parent_dir = current_file.parent.parent

# Añadir la ruta del padre a sys.path (necesario para poder importar)
import sys
sys.path.append(str(parent_dir))
from teams import equipo_id, parse_matchup,team_codes


#Este archivo sirve para ayudar a predecir a la red neuronal ya guardada. Primero se entrena la red neuronal con todos los datos hasta
#la temporada 2025-26. Y luego para predecir, se cogen los últimos 10 partidos, sus estadísitcas y las estadísticas de los jugadores.



from nba_api.stats.endpoints.teamgamelogs import TeamGameLogs #Coge los partidos de un equipo, más robusto que teamgamelog. 
#from nba_api.stats.endpoints import boxscoretraditionalv3 #Para las estadisticas del partido 
#from nba_api.stats.endpoints import gamesummaryv2 #Para las estadisticas del juego con un game_id, home_team, away, arena y demás.
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


#Coger los últimos 10 partidos de un equipo y sus estadisticas
def ultimos_partidos(equipo,numeroPartidos = 10): #Asumimos que se pasa el equipo como "Atlanta Hawks", en String
    
    team_id = equipo_id[equipo]
    
    season = get_current_season()
    #Con TeamGameLogs cogemos los últimos, ya sean temporada regular, playoff, pretemporada o in-season
    partidos_equipo = TeamGameLogs(season_nullable = season, team_id_nullable=team_id ).get_data_frames()[0] #Esto coge todos los partidos del equipo dado.

    #Pasamos las fechas a datetime, para poder utilizarlas con mayor facilidad.
    partidos_equipo['GAME_DATE'] = pd.to_datetime(partidos_equipo['GAME_DATE'])

    df_partidos = partidos_equipo.sort_values('GAME_DATE',ascending = False) #Así devuelve los partidos ordenados por las últimos fechas
    #Coger los últimos numeroPartidos
    df_equipo = df_partidos.head(numeroPartidos)

    #Ya tenemos los últios partidos, ahora pillar las estadísticas de estos
    #print(df_equipo.columns)


    #Aquí ya tenemos las estadisticas que buscamos, quizá con MATCHUP SACAR AL RIVAL?? 
    """
    SEASON_YEAR', 'TEAM_ID', 'TEAM_ABBREVIATION', 'TEAM_NAME', 'GAME_ID',
       'GAME_DATE', 'MATCHUP', 'WL', 'MIN', 'FGM', 'FGA', 'FG_PCT', 'FG3M',
       'FG3A', 'FG3_PCT', 'FTM', 'FTA', 'FT_PCT', 'OREB', 'DREB', 'REB', 'AST',
       'TOV', 'STL', 'BLK', 'BLKA', 'PF', 'PFD', 'PTS', 'PLUS_MINUS',
       'GP_RANK', 'W_RANK', 'L_RANK', 'W_PCT_RANK', 'MIN_RANK', 'FGM_RANK',
       'FGA_RANK', 'FG_PCT_RANK', 'FG3M_RANK', 'FG3A_RANK', 'FG3_PCT_RANK',
       'FTM_RANK', 'FTA_RANK', 'FT_PCT_RANK', 'OREB_RANK', 'DREB_RANK',
       'REB_RANK', 'AST_RANK', 'TOV_RANK', 'STL_RANK', 'BLK_RANK', 'BLKA_RANK',
       'PF_RANK', 'PFD_RANK', 'PTS_RANK', 'PLUS_MINUS_RANK', 'AVAILABLE_FLAG'
    """
    #BLKA -> TAPONES RECIBIDOS, PF-> FALTAS COMETIDAS, PFD-> FALTAS  RECIBIDAS, PTS-> PUNTOS TOTALES ANOTADOS POR EL EQUIPO
    #RANK, LOS RANKING DENTRO DE LA LIGA. ES DECIR, EL 9º QUE MÁS PUNTOS METE, PTS_RANK. 1 EL MEJRO EQUIPO, 30 EL PEOR
   
    #Limpiamos las estadisticas que nos interesan

    features = ['GAME_DATE','GAME_ID','MATCHUP','WL','FGM', 'FGA', 'FG_PCT', 'FG3M',
       'FG3A', 'FG3_PCT', 'FTM', 'FTA', 'FT_PCT', 'OREB', 'DREB', 'REB', 'AST',
       'TOV', 'STL', 'BLK', 'BLKA', 'PF', 'PFD', 'PTS', 'PLUS_MINUS','W_RANK', 'L_RANK', 'W_PCT_RANK','FGM_RANK',
       'FGA_RANK', 'FG_PCT_RANK', 'FG3M_RANK', 'FG3A_RANK', 'FG3_PCT_RANK',
       'FTM_RANK', 'FTA_RANK', 'FT_PCT_RANK', 'OREB_RANK', 'DREB_RANK',
       'REB_RANK', 'AST_RANK', 'TOV_RANK', 'STL_RANK', 'BLK_RANK', 'BLKA_RANK',
       'PF_RANK', 'PFD_RANK', 'PTS_RANK', 'PLUS_MINUS_RANK']
    


    #Creamos el resultado en un DataFrame para luego pasarlo a numpy array. Lo que usan las redes neuronales

    res = [] 

    for _,partido in df_equipo.iterrows(): #Devuelve una Serie, no un DataFrame

        matchup = partido['MATCHUP']

        home,away = parse_matchup(matchup,team_codes)
        
        rival = away if home == equipo else home
        
        #Pillamos datos del rival 
        rival_id = equipo_id[rival]

        rival_equipo = TeamGameLogs(season_nullable=season, team_id_nullable=rival_id).get_data_frames()[0]
        
        #El partido que nos interesa
        stats_rival = rival_equipo[rival_equipo["GAME_ID"] == partido["GAME_ID"]]

        #Pasar de Series a DataFrame y con las columnas que queremos
        stats_rival = stats_rival[features].iloc[0]
        #Verificamos que haya datos del rival.
        if stats_rival.empty:
            continue #Mirar a guardar solo los datos del equipo actual 
            #raise ValueError(f"No se encontró el partido {partido['GAME_ID']} para el rival {rival}")

        stats_rival = stats_rival.add_suffix("_RIVAL")
        stats_rival = pd.DataFrame([stats_rival])

        #Lo mismo pero con el equipo a evaluar
        stats_equipo = partido[features]
        stats_equipo = stats_equipo.add_suffix("_TEAM")
        stats_equipo = pd.DataFrame([stats_equipo])

        #Ya vienen como datetimes las GAME_DATE

        stats_partido_totales = pd.concat([stats_rival,stats_equipo], axis=1)#Las juntamos en la misma fila

        res.append(stats_partido_totales)
  
    df_res = pd.concat(res,ignore_index=True)
    return df_res



print(ultimos_partidos("Chicago Bulls"))



