from nba_api.stats.endpoints import LeagueGameLog #Partido por partido, con stats completas de cada partido 
import pandas as pd
import time
from teams import parse_matchup,team_codes,team_ids,nba_to_myid,name_to_myid
import os

pd.set_option('display.max_columns',None)

#LeagueGameLog devuelve los partidos para el local y visitante en dos filas distintas


#Añadimos las columnas HOME_TEAM y AWAY_TEAM en el df. Recorremos cada fila y entonces metemos en cada fila el HOME_TEAM y el AWAY_TEAM
def agregar_home_away(df):
    df['HOME_TEAM'] = None
    df['AWAY_TEAM'] = None

    #En cada fila pues dependiendo de si ha sido local o visitante, se añade.
    for i,fila in df.iterrows():
        home,away = parse_matchup(fila['MATCHUP'], team_codes) #Esto nos devuelve los equipos que jugaron y quien fue el local y el visitante
        df.at[i, "HOME_TEAM"] = home
        df.at[i,  "AWAY_TEAM"] = away
    
    return df

#Mapeamos los ids a los nuestros, incluidos los históricos. Los de Seattle Supersonic y demás.
def map_team_ids(df):
    df['TEAM_ID'] = df['TEAM_ID'].map(nba_to_myid)  #Pasamos del id global al mio, el de los 30 equipos y demás
    #Rename quiza
    df['TEAM_NAME'] = df['TEAM_ID'].map(team_ids) #Para unificar todos los equipos, Seattle -> Oklahoma  y así. 

    return df

#Como un partido está dividido en dos filas, hay que unirlos. 
def juntar_filas(df):

    #print(df['TEAM_NAME'].iloc[0] == df['HOME_TEAM'].iloc[0]) Para verificar que fallaba por los strings

    #Local
    df_home = df[df['TEAM_NAME'] == df['HOME_TEAM']].copy()
    
    #Añadimos el prefijo home
    df_home = df_home.add_suffix('_HOME')
    

    #Visitante
    df_away = df[df['TEAM_NAME'] == df['AWAY_TEAM']].copy()
    df_away = df_away.add_suffix('_AWAY')

    #Unimos por GAME_ID
    df_final = pd.merge(
        df_home,
        df_away,
        left_on="GAME_ID_HOME",
        right_on="GAME_ID_AWAY",
        suffixes=("_HOME", "_AWAY")
    )


    #Unificamos datos duplicados
    df_final['GAME_DATE'] = df_final['GAME_DATE_HOME']
    df_final['HOME_TEAM'] = df_final['HOME_TEAM_HOME']
    df_final['AWAY_TEAM'] = df_final['AWAY_TEAM_HOME']
    df_final['GAME_TYPE'] = df_final['GAME_TYPE_HOME']


    #Ahora limpiamos el dataframe de columnas inútiles para la red
    featuresInnecesarias = [
        'GAME_DATE_HOME','SEASON_HOME','GAME_TYPE_HOME',
        'HOME_TEAM_HOME','AWAY_TEAM_HOME','GAME_DATE_AWAY',
        'HOME_TEAM_AWAY','GAME_TYPE_AWAY','AWAY_TEAM_AWAY',
        'TEAM_ABBREVIATION_HOME', 'TEAM_ABBREVIATION_AWAY',
        'MATCHUP_HOME', 'MATCHUP_AWAY',
        'SEASON_ID_HOME', 'SEASON_ID_AWAY','SEASON_AWAY'
        'VIDEO_AVAILABLE_HOME', 'VIDEO_AVAILABLE_AWAY',
        'GAME_ID_HOME', 'GAME_ID_AWAY',
        'TEAM_NAME_HOME','TEAM_NAME_AWAY',
        'TEAM_ID_HOME','TEAM_ID_AWAY'
    ]

    df_final = df_final.drop(columns = featuresInnecesarias)

    return df_final




def guardar_en_csv(df):

    #Cogemos la ruta del directorio actual
    dir_actual = os.path.dirname(os.path.abspath(__file__)) 
    #Ruta del src
    src_dir = os.path.dirname(dir_actual)  
    #Pillamos la ruta de nba_predictor
    project_root = os.path.dirname(src_dir) 
    #Donde queremos guardarlo
    ruta_objetivo = os.path.join(project_root,'data','data_NBA')
    #Crear la carpeta si no existe
    os.makedirs(ruta_objetivo, exist_ok=True) 

    temporadas_path = os.path.join(ruta_objetivo,'temporadas.csv')
    df.to_csv(temporadas_path,index=False)


def cargar_datos_temporadas():

    # Temporadas que me interesan. Desde la 2003-04 hasta la 2024-25
    seasons = [f"{year}-{str(year+1)[-2:]}" for year in range(2003, 2025)] # Esto generaría algo como ['2003-04', '2004-05', etc.]

    #Un mismo csv con todas las temporadas, uno para temporada regular y otro para playoffs.


    todosLosPartidos = []

    for season in seasons:
        print(f"Descargando datos temporada regular temporada: {season}")
        rSeason = LeagueGameLog(season=season, season_type_all_star='Regular Season')
        df_rSeason = rSeason.get_data_frames()[0]
        df_rSeason['SEASON'] = season
        df_rSeason['GAME_TYPE'] = 'Regular Season'
        todosLosPartidos.append(df_rSeason)


        time.sleep(1) #Descansamos un segundo entre temporada regular y playoffs


        print(f"Descargando datos playoffs de la temporada: {season}")
        pOffs = LeagueGameLog(season=season, season_type_all_star='Playoffs')
        df_Playoffs = pOffs.get_data_frames()[0]
        df_Playoffs['SEASON'] = season
        df_Playoffs['GAME_TYPE'] = 'Playoffs'
        todosLosPartidos.append(df_Playoffs)

        time.sleep(1) #Esperamos otro segundo entre temporadas, para dar descanso a la API


    df_final = pd.concat(todosLosPartidos, ignore_index=True)
    
    #Procesamos el dataframe
    df_final = map_team_ids(df_final)
    df_final = agregar_home_away(df_final)
    df_final = juntar_filas(df_final)
    
    guardar_en_csv(df_final)




cargar_datos_temporadas()