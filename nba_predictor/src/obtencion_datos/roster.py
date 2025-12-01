from nba_api.stats.static import teams
from nba_api.stats.endpoints import CommonTeamRoster
from nba_api.stats.endpoints import PlayerCareerStats
from nba_api.stats.endpoints import PlayerGameLogs #Para coger los partidos de un jugador
from nba_api.stats.endpoints import PlayerGameLog #Menos problemas con la api, en principio
import pandas as pd
from datetime import datetime
import time
import os
from requests.exceptions import ReadTimeout, ConnectionError #Para el tema de la API y los fallos por espera


#Donde guardar los .csv

dir_actual = os.path.dirname(os.path.abspath(__file__)) #Cogemos la ruta del directorio actual

src_dir = os.path.dirname(dir_actual) #Ruta del src 

project_root = os.path.dirname(src_dir) #Pillamos la ruta de nba_predictor

ruta_objetivo = os.path.join(project_root,'data','data_NBA')

os.makedirs(ruta_objetivo, exist_ok=True) #Crear la carpeta si no existe

pd.set_option('display.max_columns',None) #Para ver todas las columnas y los ... entre medias


#HAY JUGADORES QUE DEVUELVEN resultSet, eso es que no tienen datos que coger. Ningún dataFrame devuelven.

#-----------------------------------------------------------------
# Coger los datos de los jugadores en cada partido y temporadas hasta la 2024-25. 
#-----------------------------------------------------------------



#Cogemos el roster actual
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



#La api tiene el Season_id = '2024-25', '2025-26' y así,
def last_season_complete():
    year = datetime.now().year
    month = datetime.now().month

    if month >= 7: # En julio ya se han acabado los playoffs, así que ya tenemos la última temporada completa
        start_year = year-1
        end_year = year
    else:
        start_year = year-2
        end_year = year -1
    
    return f'{start_year}-{str(end_year)[2:]}'



def obtener_roster():
    season = get_current_season()

    print(f"Obteniendo los jugadores de la temporada actual: {season}")

    #Cogemos todos los equipos, por sus id's 
    equipos = teams.get_teams()
    
    roster = [] #El roster completo de la temporada

    contador = 0 #Contador para esperar 10 segundos cada 10 equipos por el tema de la api
    #Recorremos todos los equipos 
    for equipo in equipos:
        id = equipo['id']
        nombre = equipo['full_name']

        if contador == 9:
            time.sleep(10) #Esperamos 10 segundos cada 10 equipos.
            contador = 0
        try:
            equipo_df = CommonTeamRoster(team_id=id,season=season).get_data_frames()[0] #Cogemos el roster del equipo

            equipo_df['TEAM_NAME'] = nombre
            equipo_df['ID'] = id

            roster.append(equipo_df)
            time.sleep(2) #Descansamos dos segundos entre equipos para el tema de la api.
        except Exception as e:
            print(f'Error desacargando el equipo: {nombre} -> {e}')
        

    df = pd.concat(roster, ignore_index=True)
    return df


#Cogemos solo las columnas que nos interesan para luego los datos de los jugadores
def limpiar_roster():
    roster = obtener_roster()

    features = ['TEAM_NAME', 'PLAYER', 'PLAYER_ID']

    roster = roster[features]

    #Renombramos el df
    roster = roster.rename(columns={ 
        'TEAM_NAME': 'TEAM',
        'PLAYER_ID': 'ID'
    })
   
    #Guardamos el roster en un csv propio
    csv_path = os.path.join(ruta_objetivo,'roster.csv')
    roster.to_csv(csv_path,index=False) #No necesitamso que nos ponga 1,2, como índice

    print(f'Se obtuvieron los datos del roster actual en la NBA. :)')
    return roster




#----------------------------------------------------------------------
#               ESTADISTICAS ROSTER ACTUAL
#----------------------------------------------------------------------







#Cogemos todos los datos de los jugadores de cada equipo y los guardamos.
#No nos importan las conferencias. Solo nos importa el historial de los partidos y de los jugadores para la red neuronal
#Es posible que influya algo la conferencia. Pero suponemos que es poco y que es más importante el tema de los back-to-back y local o visitante

#No separamos temporadas por playofffs y temporada regular. Consideramos la temporda completa. 
def datos_roster():
    #Cogemos el roster ya limpio
    roster = limpiar_roster()

    #Estadisticas históricas y de la última temporada
    playersHistorical = []
    playersLastSeason = [] 
    
    #Estadísticas de playoffs

    playerPlayoffsHistorical = []
    playerPlayoffsSeason = []


    equipoActual = None

    #Cogemos las estadísticas de cada jugador del roster
    for _,player in roster.iterrows():


        #Datos de los jugadores que ya tenemos

        id = player['ID']
        nombre = player['PLAYER']
        equipo = player['TEAM']

        
        if equipoActual and equipoActual != equipo: 
            time.sleep(10) #Cuando cambiamos de equipo esperamos 10 segundos, pero no con el primer equipo de ahi el if equipoActual
         
        print(f'Sacando datos de {nombre} ({equipo})')

        try:

            #-----------------------------------
            #       TEMPORADA REGULAR
            #-----------------------------------


            df = PlayerCareerStats(player_id=id, per_mode36='PerGame') # Te da las estadísticas por partido, en forma de objeto, ya luego cojo el dataframe especifico
            
            historico = df.career_totals_regular_season.get_data_frame()



            if historico is None or historico.empty:
                print(f'{nombre} no tiene datos de carrera (rookie o sin minutos).') 
                
                #Asumimos que si no ha jugado en temporada regular tampoco en playoffs. Habrá excepciones, pero serán muy pocas y casi insignificantes
                continue #Tampoco tendrá datos de la última temporada
            else:
                historico = historico.copy()
                historico['JUGADOR'] = nombre
                historico['EQUIPO'] = equipo
                historico['ID'] = id
                playersHistorical.append(historico)

            #última temporada
            temporadas_df = df.season_totals_regular_season.get_data_frame()

            if temporadas_df is None or temporadas_df.empty:
                print(f'{nombre} no tiene estadísticas de la última temporada regular.')
            else:
                
                #Filtramos para coger la última temporada completa, a fecha de hoy 24/11/2025 -> 2024-25
                temporadas_df = temporadas_df[temporadas_df['GP'] > 0] #Temporadas en que haya jugado

                season_id = last_season_complete() #id de la temporada

                #Última temporada completa.
                #SEASON_ID =  2003-04, 2024-25
                temporadas_df = temporadas_df[temporadas_df['SEASON_ID']  == season_id] 

                if not temporadas_df.empty: #Si hay al menos una temporada, pues lo cogemos. Los rookies no tendrán última temporada
                    
                    last = temporadas_df.copy() #Cogemos la última temporada, es decir, la 2024-25. Y hacemos copy para evitar problemas
                    last['JUGADOR'] = nombre
                    last['EQUIPO'] = equipo
                    last['ID'] = id
                    playersLastSeason.append(last)
            

            #Esperamos un poco para no abrumar a la api

            time.sleep(0.5) #Medio segundo entre temporada regular y playoffs

            #---------------------------------------
            #       PLAYOFFS
            #---------------------------------------


            #Post season == Playoff

            historico_playoff = df.career_totals_post_season.get_data_frame()

            if historico_playoff is None or historico_playoff.empty:
                print(f'{nombre} no tiene datos de carrera en playoffs.')
                continue #Tampoco tendrá datos de la última temporada de playoffs.
            else:
                historico_playoff = historico_playoff.copy()
                historico_playoff['JUGADOR'] = nombre
                historico_playoff['EQUIPO'] = equipo
                historico_playoff['ID'] = id
                playerPlayoffsHistorical.append(historico_playoff)


            season_playoff = df.season_totals_post_season.get_data_frame()

            if season_playoff is None or season_playoff.empty:
                print(f'{nombre} no tiene estadísticas de la última temporada en playoffs.')
            else:
                 #Filtramos para coger la última temporada completa, a fecha de hoy 24/11/2025 -> 2024-25

                season_playoff = season_playoff[season_playoff['GP'] > 0] #Temporadas en que haya jugado algún partido en playoffs

                season_id = last_season_complete() #id de la temporada

                #Última temporada completa.
                season_playoff = season_playoff[season_playoff['SEASON_ID']  == season_id] 

                if not season_playoff.empty: #Si hay al menos una temporada, pues lo cogemos. Los rookies no tendrán última temporada
                    
                    last_playoff = season_playoff.copy() #Cogemos la última temporada, es decir, la 2024-25. Y hacemos copy para evitar problemas
                    last_playoff['JUGADOR'] = nombre
                    last_playoff['EQUIPO'] = equipo
                    last_playoff['ID'] = id
                    playerPlayoffsSeason.append(last_playoff)




        except Exception as e:
            print(f'Error descargando al jugador {nombre} -> {e}')

        equipoActual = equipo
        time.sleep(1) #1 segundo por jugador


    #Para evitar el warning por si estuviesen vacias estas listas. Ya que hay jugadores que no tienen datos, rookies.    
    historico_df = pd.concat(playersHistorical, ignore_index=True) if playersHistorical else pd.DataFrame() 
    ultima_df = pd.concat(playersLastSeason,ignore_index=True) if playersLastSeason else pd.DataFrame()

    #Playoff 
    historico_pf_df = pd.concat(playerPlayoffsHistorical,ignore_index=True) if playerPlayoffsHistorical else pd.DataFrame()
    ultima_pf_df = pd.concat(playerPlayoffsSeason,ignore_index=True) if playerPlayoffsSeason else pd.DataFrame()


    return historico_df,ultima_df,historico_pf_df,ultima_pf_df



#----------------------------------------------------------------------
#               ESTADISTICAS POR PARTIDO ROSTER ACTUAL
#----------------------------------------------------------------------

# Esperar entre llamadas bastante para evitar IP blocks

#Como a veces la API tiene que coger muchos datos, y tarda demasiado, debemos implementar retries y aumentar el Timeout     





#---------------------------TEMPORADA REGULAR--------------------------------------







#COGEMOS LAS TEMPORADAS QUE JUGÓ EL JUGADOR, CUIDADO CON LOS ROOKIES. NO TIENEN TEMPORADAS JUGADAS
def obtener_temporadas_regular_jugador(player_id,retries = 5, timeout=60, segundoIntento = False):


    for intento in range(1, retries + 1):
        try:
            stats = PlayerCareerStats(
                player_id=player_id,
                timeout=timeout
            )

            df = stats.season_totals_regular_season.get_data_frame()

            # Caso: rookie, two-way o sin datos -> devolver lista vacía
            if df.empty:
                print(f"[INFO] El jugador {player_id} no tiene temporadas jugadas.")
                return []

            temporadas = list(df['SEASON_ID'].unique())
            return temporadas

        except ReadTimeout:
            print(f"[Timeout] PlayerCareerStats({player_id}) "
                  f"Reintento {intento}/{retries}...")
            time.sleep(2 * intento)

        except ConnectionError:
            print(f"[Conexion] Error PlayerCareerStats({player_id}) "
                  f"Reintento {intento}/{retries}...")
            time.sleep(2 * intento)

        except Exception as e:
            print(f"[ERROR] PlayerCareerStats({player_id}) fallo inesperado: {e}")
            return []


    # ❗ Ha fallado los 5 reintentos
    if not segundoIntento:
        print(f"PlayerCarrerStats falló 5 veces seguidas para {player_id}. Esperando 20 minutos...\n")
        time.sleep((20 * 60)+10)
        print("Reintentando PlayerCarrerStats desde cero...\n")

        # Volvemos a intentar DESPUÉS DEL COOLDOWN
        return obtener_temporadas_regular_jugador(player_id, retries, timeout, segundoIntento=True)

    # ❗ Si llega aquí → falló también después del cooldown
    print(f"[ERROR] PlayerCarrerStats falló incluso después del cooldown para {player_id}.")
    return []

    


#Asumo que no puede coger una temporada que no tiene ningún partido, por el tema de PlayerCareerStats y el unique


#OBTENEMOS LOS PARTIDOS DE UNA TEMPORADA DEL JUGADOR
def obtener_partido_temporada_regular(player_id, season,retries=5, sleep_time = 1, segundoIntento = False):
    

    for intento in range(1,retries+1):
        try:
            
            df_season = PlayerGameLog(
                player_id=player_id,
                season_type_all_star='Regular Season',
                season=season,
                timeout=30
            )
            
            
            return df_season.get_data_frames()[0]
        
        except ReadTimeout:
            print(f"Timeout en PlayerGameLog ({player_id}, {season}). "
                  f"Reintento {intento}/{retries}...")
            time.sleep(sleep_time * intento)

        except ConnectionError:
            print(f"Error de conexión ({player_id}, {season}). "
                  f"Reintentando {intento}/{retries}...")
            time.sleep(sleep_time * intento)

        except Exception as e:
            print(f"Error inesperado para player {player_id}, season {season}: {e}")
            return pd.DataFrame()


    # ❗ Ha fallado los 5 reintentos
    if not segundoIntento:
        print(f"PlayerGameLog falló 5 veces seguidas para ({player_id},{season}). "
              f"Esperando 20 minutos...\n")
        time.sleep((20 * 60)+10)
        print("Reintentando PlayerGameLog desde cero...\n")

        # Reintentamos DESPUÉS DEL COOLDOWN
        return obtener_partido_temporada_regular(player_id, season, retries, segundoIntento=True)

    print(f"[ERROR] PlayerGameLog falló incluso después del cooldown para {player_id} en {season}.")
    return pd.DataFrame()

#PROBAR MENOS tiempo de espera entre llamadas

#FUNCIÓN PARA COGER TODOS LOS PARTIDOS DE TODOS LAS TEMPORADAS QUE HA JUGADO UN JUGADOR
def obtener_todas_los_partidos_temporada_regular(player_id):
    
    temporadas = obtener_temporadas_regular_jugador(player_id)

    allMatches = []

    ultima_temporada = last_season_complete()

    for temporada in temporadas:

        if temporada > ultima_temporada:
            break #quiza continue mejor, ver.

        #print(f"Obteniendo datos del jugador {player_id} de la temporada {temporada}")

        df = obtener_partido_temporada_regular(player_id,temporada)

        if not df.empty:
            df['SEASON'] = temporada
            allMatches.append(df)
        
        time.sleep(2) #Esperamos 2 segundos entre temporadas
    
    if not allMatches:
        return pd.DataFrame()

    return pd.concat(allMatches,ignore_index=True)
              


#---------------------------PLAYOFFS--------------------------------------


def obtener_temporadas_playoffs_jugador(player_id,retries = 5, timeout=60, segundoIntento = False):


    for intento in range(1, retries + 1):
        try:
            stats = PlayerCareerStats(
                player_id=player_id,
                timeout=timeout
            )

            df = stats.season_totals_post_season.get_data_frame()

            # Caso: rookie, o jugador que no ha llegado nunca a playoffs -> devolver lista vacía
            if df.empty:
                print(f"[INFO] El jugador {player_id} no tiene temporadas en playoffs jugadas.")
                return []

            temporadas = list(df['SEASON_ID'].unique())
            return temporadas

        except ReadTimeout:
            print(f"[Timeout] PlayerCareerStats, post-season, ({player_id})  "
                  f"Reintento {intento}/{retries}...")
            time.sleep(2 * intento)

        except ConnectionError:
            print(f"[Conexion] Error PlayerCareerStats,post-season, ({player_id}) "
                  f"Reintento {intento}/{retries}...")
            time.sleep(2 * intento)

        except Exception as e:
            print(f"[ERROR] PlayerCareerStats, post-season, ({player_id}) fallo inesperado: {e}")
            return []


    # ❗ Ha fallado los 5 reintentos
    if not segundoIntento:
        print(f"PlayerCarrerStats, post-season,  falló 5 veces seguidas para {player_id}. Esperando 20 minutos...\n")
        time.sleep((20 * 60)+10)
        print("Reintentando, post-season,  PlayerCarrerStats desde cero...\n")

        # Volvemos a intentar DESPUÉS DEL COOLDOWN
        return obtener_temporadas_playoffs_jugador(player_id, retries, timeout, segundoIntento=True)

    # ❗ Si llega aquí → falló también después del cooldown
    print(f"[ERROR] PlayerCarrerStats, post-season,  falló incluso después del cooldown para {player_id}.")
    return []


def obtener_partido_playoffs(player_id, season,retries=5, sleep_time = 1, segundoIntento = False):
    
    for intento in range(1,retries+1):
        try:
            
            df_season = PlayerGameLog(
                player_id=player_id,
                season_type_all_star='Playoffs',
                season=season,
                timeout=30
            )
            
            
            return df_season.get_data_frames()[0]
        
        except ReadTimeout:
            print(f"Timeout en PlayerGameLog, playoffs, ({player_id}, {season}). "
                  f"Reintento {intento}/{retries}...")
            time.sleep(sleep_time * intento)

        except ConnectionError:
            print(f"Error de conexión, playoffs, ({player_id}, {season}). "
                  f"Reintentando {intento}/{retries}...")
            time.sleep(sleep_time * intento)

        except Exception as e:
            print(f"Error inesperado para player, playoffs, {player_id}, season {season}: {e}")
            return pd.DataFrame()


    # ❗ Ha fallado los 5 reintentos
    if not segundoIntento:
        print(f"PlayerGameLog, playoffs, falló 5 veces seguidas para ({player_id},{season}). "
              f"Esperando 20 minutos...\n")
        time.sleep((20 * 60)+10)
        print("Reintentando PlayerGameLog, playoffs, desde cero...\n")

        # Reintentamos DESPUÉS DEL COOLDOWN
        return obtener_partido_temporada_regular(player_id, season, retries, segundoIntento=True)

    print(f"[ERROR] PlayerGameLog, playoffs, falló incluso después del cooldown para {player_id} en {season}.")
    return pd.DataFrame()

def obtener_todos_los_partidos_playoffs(player_id ):

    temporadas_playoffs = obtener_temporadas_playoffs_jugador(player_id)

    allMatches = []

    ultima_temporada = last_season_complete()

    for temporada in temporadas_playoffs:

        if temporada > ultima_temporada:
            break #quiza continue mejor, ver.

        df = obtener_partido_playoffs(player_id,temporada)

        if not df.empty:
            df['SEASON'] = temporada
            allMatches.append(df)
        
        time.sleep(2) #Esperamos 2 segundos entre temporadas
    
    if not allMatches:
        return pd.DataFrame()

    return pd.concat(allMatches,ignore_index=True)








#Siempre es mejor que sea secuencial para la LSTM, por eso cogemos los datos de los partidos jugados, no el global de las estadísticas
def datos_partido_por_jugador():
    roster = limpiar_roster()

    equipoActual = None

    datos_jugadores = []

    #jugadores = 0

    for _,player in roster.iterrows():

        
        #Datos de los jugadores que ya tenemos

        id = player['ID']
        nombre = player['PLAYER']
        equipo = player['TEAM']


        if equipoActual and equipoActual != equipo: 
            print(F'Cambiando de equipo')
            time.sleep(15) #Cuando cambiamos de equipo esperamos 15 segundos, pero no con el primer equipo de ahi el if equipoActual

        
        equipoActual = equipo


        print(f"Descargando partidos de {nombre} ({equipo})...")

        df = obtener_todas_los_partidos_temporada_regular(id)

        
        if df.empty:
            print(f"No se obtuvieron datos del jugador {nombre}")
            continue
        
        df_playoffs = obtener_todos_los_partidos_playoffs(id)

        if not df_playoffs.empty:
            df_total = pd.concat([df,df_playoffs], ignore_index=True)
            datos_jugadores.append(df)
        else:
            datos_jugadores.append(df)
        
        
        
        time.sleep(5) # 5 segundos entre jugadores


    df_jugadores = pd.concat(datos_jugadores, ignore_index=True)
    
    #Limpiamos las estadisticas inútiles

    #columnasInnecesarias = ['SEASON_YEAR','NICKNAME','TEAM_ABBREVIATION','MATCHUP','WL',  
    #                        'NBA_FANTASY_PTS','DD2','TD3','WNBA_FANTASY_PTS','GP_RANK','W_RANK',
    #                        'L_RANK','W_PCT_RANK','MIN_RANK','FGM_RANK','FGA_RANK','FG_PCT_RANK','FG3M_RANK',
    #                        'FG3A_RANK','FG3_PCT_RANK','FTM_RANK','FTA_RANK','FT_PCT_RANK','OREB_RANK',
    #                        'DREB_RANK','REB_RANK','AST_RANK','TOV_RANK','STL_RANK','BLK_RANK','BLKA_RANK'
    #                        'PF_RANK','PFD_RANK','PTS_RANK','PLUS_MINUS_RANK','NBA_FANTASY_PTS_RANK',
    #                        'DD2_RANK','TD3_RANK','WNBA_FANTASY_PTS_RANK','AVAILABLE_FLAG','MIN_SEC',
    #                        'TEAM_COUNT'] 
    columnasInnecesarias = ['MATCHUP','WL','VIDEO_AVAILABLE','SEASON_ID']
    
    df_jugadores = df_jugadores.drop(columns=columnasInnecesarias)

    df_jugadores['GAME_DATE'] = pd.to_datetime(df_jugadores['GAME_DATE']).dt.date #Para quitar la hora
    
    print(df_jugadores.head(5))

    path = os.path.join(ruta_objetivo,'jugadores.csv')
    df_jugadores.to_csv(path, index=False)
    
    return df_jugadores






def limpiar_roster_y_guardar_en_csv():
    historico,ultima, historico_pf, ultima_pf = datos_roster()

    #GS -> Games Started, útil.
    features = ['JUGADOR','EQUIPO','GP','GS','MIN','FGM','FGA','FG_PCT','FG3M','FG3A',
                'FG3_PCT','FTM','FTA','FT_PCT','OREB','DREB','REB','AST','STL','BLK','TOV','PF','PTS',
                'ID']

    historico = historico[features]
    ultima = ultima[features]
    historico_pf = historico_pf[features]
    ultima_pf = ultima_pf[features]

    #Guardamos en csv's

    historico_path = os.path.join(ruta_objetivo,'jugadores_datos_historicos_temporada_regular.csv')
    ultima_path = os.path.join(ruta_objetivo,'jugadores_datos_ultima_temporada_regular.csv')

    historico_pf_path = os.path.join(ruta_objetivo,'jugadores_datos_historicos_playoffs.csv')
    ultima_pf_path = os.path.join(ruta_objetivo,'jugadores_datos_ultima_temporada_playoffs.csv')

    historico.to_csv(historico_path,index=False)
    ultima.to_csv(ultima_path,index=False)
    historico_pf.to_csv(historico_pf_path,index=False)
    ultima_pf.to_csv(ultima_pf_path,index=False)




#limpiar_roster_y_guardar_en_csv()
inicio = time.time()
datos_partido_por_jugador()
fin = time.time()
print(f"El programa ha tardado {fin-inicio} segundos")