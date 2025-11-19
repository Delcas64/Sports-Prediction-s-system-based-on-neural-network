import pandas as pd
import os 


rutaActual = os.path.dirname(__file__)

rutaArchivos = os.path.join(rutaActual,'../data/data_api/Estadisticas_Temporada_Regular_Jugadores_Actuales')

rutaOeste = os.path.join(rutaArchivos,'estadisticas_jugadores_oeste.csv')
rutaEste = os.path.join(rutaArchivos,'estadisticas_jugadores_este.csv')


df_oeste = pd.read_csv(rutaOeste)
df_este = pd.read_csv(rutaEste)



df_oeste.drop(columns=['LEAGUE_ID','TEAM_ID'], inplace=True)
df_este.drop(columns=['TEAM_ID','LEAGUE_ID'], inplace=True)


columnas = ['PLAYER_ID','PLAYER','TEAM_NAME','GP','GS','MIN','FGM','FGA','FG_PCT','FG3M','FG3A','FG3_PCT','FTM','FTA','FT_PCT','OREB','DREB'
            ,'REB','AST','STL','BLK','TOV','PF','PTS']

df_oeste = df_oeste[columnas]
df_este = df_este[columnas]

df_oeste['CONFERENCE'] = 'Oeste'
df_este['CONFERENCE'] = 'Este' 

df_total = pd.concat([df_oeste,df_este],ignore_index=True)


rutaSalida = os.path.join(rutaArchivos,'../../data_limpia_usada_en_red_neuronal/estadisticas_historicas_jugadares_actuales.csv')

df_total.to_csv(rutaSalida,index=False)