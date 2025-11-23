from nba_api.stats.static import teams
from nba_api.stats.endpoints import CommonTeamRoster
from nba_api.stats.endpoints import PlayerCareerStats
import pandas as pd
from datetime import datetime
import time
import os

pd.set_option('display.max_columns',None) #Para ver todas las columnas y los ... entre medias

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


def obtener_roster():
    season = get_current_season()

    print(f"Obteniendo los datos de la temporada actual: {season}")

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
   

    return roster


#Cogemos todos los datos de los jugadores de cada equipo y los guardamos.
# No nos importan las conferencias. Solo nos importa el historial de los partidos y de los jugadores para la red neuronal
# Es posible que influya algo la conferencia. Pero suponemos que es poco y que es más importante el tema de los back-to-back y local o visitante

#Regular season todo
def datos_roster():
    #Cogemos el roster ya limpio
    roster = limpiar_roster()

    #Estadisticas históricas y de la última temporada
    playersHistorical = []
    playersLastSeason = [] 
    

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
            df = PlayerCareerStats(player_id=id, per_mode36='PerGame') # Te da el promedio por partido, en forma de objeto, ya luego cojo el dataframe especifico
            
            historico = df.career_totals_regular_season.get_data_frame()

            if historico is None or historico.empty:
                print(f'{nombre} no tiene datos de carrera (rookie o sin minutos).')
            else:
                historico_fila = historico_df.iloc[0].copy
                historico_fila['JUGADOR'] = nombre
                historico_fila['EQUIPO'] = equipo
                historico_fila['ID'] = id
                playersHistorical.append(historico_fila)

            #última temporada
            temporadas_df = df.season_totals_regular_season.get_data_frame()

            if temporadas_df is None or temporadas_df.empty:
                print(f'{nombre} no tiene temporadas jugadas todavía.')
            else:
                if len(temporadas_df) > 0: #Si hay al menos una temporada, pues lo cogemos. Los rookies no tendrán última temporada
                    last = temporadas_df.iloc[-1].copy() #Para evitar problemas
                    last['JUGADOR'] = nombre
                    last['EQUIPO'] = equipo
                    last['ID'] = id
                    playersLastSeason.append(last)

        except Exception as e:
            print(f'Error descargando al jugador {nombre} -> {e}')

        equipoActual = equipo
        time.sleep(0.6) #0.6 segundos por jugado


    #Para evitar el warning por si estuviesen vacias estas listas. Ya que hay jugadores que no tienen datos, rookies.    
    historico_df = pd.concat(playersHistorical, ignore_index=True) if playersHistorical else pd.DataFrame() 
    ultima_df = pd.concat(playersLastSeason,ignore_index=True) if playersLastSeason else pd.DataFrame()


    return historico_df,ultima_df




historico, ultima = datos_roster()
print(historico.head(5))
print(ultima.head(5))


def limpiar_roster_y_guardar_en_csv():
    historico,ultima = datos_roster()




