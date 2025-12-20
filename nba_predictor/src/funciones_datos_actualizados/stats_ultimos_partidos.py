from nba_predictor.src.obtencion_datos.teams import equipo_id, parse_matchup,team_codes


#Este archivo sirve para ayudar a predecir a la red neuronal ya guardada. Primero se entrena la red neuronal con todos los datos hasta
#la temporada 2025-26. Y luego para predecir, se cogen los últimos 10 partidos, sus estadísitcas y las estadísticas de los jugadores.

#HAY NaN por el tema de que TeamGameLogs, tarda en acutalizarse, y si pones partidos de Regular Season, si se jugo un In-Season Tournament,
# no cuenta como eso.
#Probamos con BoxScoreTraditionalV3. Más útil y fiable. Lo usa la API interna de la NBA.

from nba_api.stats.endpoints import boxscoretraditionalv3 #Lo único que no da rankings, pero no pasa nada.
from nba_api.stats.endpoints.teamgamelogs import TeamGameLogs #Coge los partidos de un equipo, más robusto que leaguegamelog. 
from datetime import datetime
import pandas as pd
import time

pd.set_option('display.max_columns',None)

#Para no depender de poner season = 2024-25 o la que toque, y tener que cambiarla cada año. La misma que en rosters.py
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




def get_boxscore_stats_equipo(game_id, team_id):
    #Devuelve las estadísticas de un equipo en un partido usando BoxScoreTraditionalV3

    #Devuelve tres dataframes, 0 = PlayerStats, 1 = TeamStarterBenchStats, 2 = TeamStats
    box = boxscoretraditionalv3.BoxScoreTraditionalV3(game_id=game_id).get_data_frames()[2]
    fila = box[box["teamId"] == team_id].iloc[0]

    # features que sí existen en BoxScoreTraditionalV3, tenemos que hacer un diccionario, en la api de boxScore son ls features en minúsculas
    features = {

        "FGM": "fieldGoalsMade",
        "FGA": "fieldGoalsAttempted",
        "FG_PCT": "fieldGoalsPercentage",
        "FG3M": "threePointersMade",
        "FG3A": "threePointersAttempted",
        "FG3_PCT": "threePointersPercentage",
        "FTM": "freeThrowsMade",
        "FTA": "freeThrowsAttempted",
        "FT_PCT": "freeThrowsPercentage",
        "OREB": "reboundsOffensive",
        "DREB": "reboundsDefensive",
        "REB": "reboundsTotal",
        "AST": "assists",
        "STL": "steals",
        "BLK": "blocks",
        "TOV": "turnovers",
        "PF": "foulsPersonal",
        "PTS": "points",
        "PLUS_MINUS": "plusMinusPoints"
    }

    # 1. Crear un diccionario vacío donde iremos guardando las estadísticas
    data = {}

    # 2. Rellenar el diccionario recorriendo el mapeo (out → src) #src son las de la api de boxScore. "free...",....
    for out, source in features.items():
        data[out] = fila[source]

    # 3. Convertir el diccionario en un DataFrame de una sola fila
    df = pd.DataFrame([data])

    return df

#Fallaba aqui por el tema de los tiempos de espera de la api.
#Ver con cuidado lo que devuelve

def get_boxcore_stats_jugadores(game_id):
    
    try:
        df_jugadroes = boxscoretraditionalv3.BoxScoreTraditionalV3(game_id).get_data_frames()[0]
        
    except Exception as e:
        print(f"Error al obtener BoxScoreTraditionalV3 para {game_id}: {e}")
        return pd.DataFrame()

    if df_jugadroes.empty:
        print(f"BoxScoreTraditionalV3 vacío para game_id={game_id}")
        return pd.DataFrame()
    
    #Devuelve tres dataframes, 0 = PlayerStats, 1 = TeamStarterBenchStats, 2 = TeamStats
    #box = boxscoretraditionalv3.BoxScoreTraditionalV3(game_id=game_id).get_data_frames()[0]
    #fila = box[box["teamId"] == team_id].iloc[0]

    player_features = {
        "PLAYER_ID": "personId",
        "TEAM_ID": "teamId", #Creo que inútil, pero ya veremos.
        "FIRST": "firstName",
        "LAST": "familyName",
        "MIN": "minutes",
        "FGM": "fieldGoalsMade",
        "FGA": "fieldGoalsAttempted",
        "FG_PCT": "fieldGoalsPercentage",
        "FG3M": "threePointersMade",
        "FG3A": "threePointersAttempted",
        "FG3_PCT": "threePointersPercentage",
        "FTM": "freeThrowsMade",
        "FTA": "freeThrowsAttempted",
        "FT_PCT": "freeThrowsPercentage",
        "OREB": "reboundsOffensive",
        "DREB": "reboundsDefensive",
        "REB": "reboundsTotal",
        "AST": "assists",
        "STL": "steals",
        "BLK": "blocks",
        "TOV": "turnovers",
        "PF": "foulsPersonal",
        "PTS": "points",
        "PLUS_MINUS": "plusMinusPoints"
    }

    # 1. Crear un diccionario vacío donde iremos guardando las estadísticas
    data = {}

    # 2. Rellenar el diccionario recorriendo el mapeo (out → src) #src son las de la api de boxScore. "free...",....
    for out, source in player_features.items():
        data[out] = df_jugadroes[source]

    # 3. Convertir el diccionario en un DataFrame de una sola fila
    df = pd.DataFrame([data])

    return df

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
        
        game_id = partido['GAME_ID']
        #Para el modelo, mejor rival y team
        matchup = partido['MATCHUP']

        home,away = parse_matchup(matchup,team_codes)

        rival = away if home == equipo else home    
        
        #Pillamos datos del rival 
        rival_id = equipo_id[rival]
        

        stats_equipo = get_boxscore_stats_equipo(game_id,team_id)
        stats_equipo = stats_equipo.add_suffix("_TEAM")
        #rival_equipo = TeamGameLogs(season_nullable=season, team_id_nullable=rival_id).get_data_frames()[0]
        

        #Esperamos 0.6 segunditos entre equipos
        time.sleep(0.6)
        stats_rival = get_boxscore_stats_equipo(game_id, rival_id)
        stats_rival = stats_rival.add_suffix("_RIVAL")

        #Cogemos los jugadores

        df_jugadores = get_boxcore_stats_jugadores(game_id)
        df_jugadores['GAME_ID'] = game_id 

        #Ya vienen como datetimes las GAME_DATE

        time.sleep(0.6)
        stats_partido_totales = pd.concat([stats_equipo,stats_rival], axis=1)#Las juntamos en la misma fila

        #Limpiamos algunas columnas comunes y otras innecesarios
        stats_partido_totales['GAME_DATE'] = pd.to_datetime(partido['GAME_DATE'])
        #columnasInnecesarias = ['GAME_DATE_TEAM', 'GAME_DATE_RIVAL', 'GAME_ID_TEAM','GAME_ID_RIVAL','MATCHUP_TEAM','MATCHUP_RIVAL']
        stats_partido_totales['HOME'] = home
        stats_partido_totales['AWAY'] = away
        stats_partido_totales['GAME_ID'] = game_id
        
        #Quitamos esas columnas
        #stats_partido_totales = stats_partido_totales.drop(columns=columnasInnecesarias)


        res.append(stats_partido_totales)
  
    df_res = pd.concat(res,ignore_index=True)
    return df_res,df_jugadores


df_res, df_jugadores = ultimos_partidos('Chicago Bulls')
print(df_res.columns)
print(df_jugadores.columns)
print(df_res.head(1))
print(df_jugadores.head(1))



