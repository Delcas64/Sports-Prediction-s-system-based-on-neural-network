import pandas as pd
from nba_api.stats.endpoints import playercareerstats
import os
import time


rutaActual = os.path.dirname(__file__)
rutaArchivo = os.path.join(rutaActual,'../../prueba_roster.csv') 

df_jugadores_roster = pd.read_csv(rutaArchivo)


conferencia_este = ('Boston Celtics','Brooklyn Nets','New York Knicks','Philadelphia 76ers','Toronto Raptors',
                    'Chicago Bulls','Cleveland Cavaliers','Detroit Pistons','Indiana Pacers','Milwaukee Bucks',
                    'Atlanta Hawks','Charlotte Hornets','Miami Heat','Orlando Magic','Washington Wizards')


condicion_este = df_jugadores_roster['TEAM_NAME'].isin(conferencia_este)

df_este = df_jugadores_roster[condicion_este]

lista_df = []


#Usamos el _ para indicar que hay una variable, el indice de la tupla que devuelve el iterrows(), pero que no es importante
for _,jugador in df_este.iterrows():
    player_id = jugador['PLAYER_ID']
    nombre = jugador['PLAYER']
    equipo = jugador['TEAM_NAME']
    try:
        datos = playercareerstats.PlayerCareerStats(player_id=player_id, per_mode36='PerGame') #Per game ya te da el promedio por partido , y con carrertotalsregularseason pues conseguimos el promedio de todas las temporadas
        df_datos = datos.career_totals_regular_season.get_data_frame()
        
        df_datos['PLAYER'] = nombre
        df_datos['TEAM_NAME'] = equipo
        lista_df.append(df_datos)
        print(f'Obteniendo datos del jugador: {nombre}') 
        time.sleep(1)
    except Exception as e:
        print(f'No se pudo obtener los datos del jugador -> {nombre}: {e}')


if lista_df:
    df_datos_historicos = pd.concat(lista_df,ignore_index=True)
    df_datos_historicos.to_csv('nba_predictor/data/data_api/Estadisticas_Temporada_Regular_Jugadores_Actuales/estadisticas_jugadores_este.csv')
else:
    df_datos_historicos= pd.DataFrame()