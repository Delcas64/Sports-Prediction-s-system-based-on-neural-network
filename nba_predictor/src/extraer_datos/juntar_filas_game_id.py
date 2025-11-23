"""
Archivo para juntar las filas de las estadísticas de 
los mismos game_id(partidos) del csv donde guardo todos los partidos desde el 2003 hasta el 2025
"""
import os
import pandas as pd
from nba_predictor.src.obtencion_datos.teams import team_ids

rutaActual = os.path.dirname(os.path.abspath(__file__)) #Ruta actual del archivo
rutaArchivo = os.path.join(rutaActual, "../../ejemplo.csv") 

df = pd.read_csv(rutaArchivo)


df['TEAM_NAME'] = df['ID_TEAM'].map(team_ids)


home_df = df[df["TEAM_NAME"] == df["HOME_TEAM"]].copy()
away_df = df[df["TEAM_NAME"] == df["AWAY_TEAM"]].copy()


# Renombrar columnas para distinguir local/visitante, añade ese sufijo a todos los labels de ese df
home_df = home_df.add_suffix("_home") 
away_df = away_df.add_suffix("_away") 


# El GAME_ID es la clave común
merged = pd.merge(
    home_df,
    away_df,
    left_on="GAME_ID_home",
    right_on="GAME_ID_away",
    suffixes=("_home", "_away")
)


# Ahora limpiamos columnas duplicadas
merged["GAME_ID"] = merged["GAME_ID_home"]
merged["GAME_DATE"] = merged["GAME_DATE_home"]
merged["SEASON"] = merged["SEASON_home"]
merged["HOME_TEAM"] = merged["HOME_TEAM_home"]
merged["AWAY_TEAM"] = merged["AWAY_TEAM_home"]


# Variable objetivo: quién ganó
merged["WINNER"] = merged.apply(lambda row: "HOME" if row["PTS_home"] > row["PTS_away"] else "AWAY", axis=1)

# Drop columnas redundantes
final = merged.drop(columns=["GAME_ID_home", "GAME_ID_away", "GAME_DATE_home", "GAME_DATE_away",
                             "SEASON_home", "SEASON_away", "HOME_TEAM_home", "AWAY_TEAM_home",
                             "HOME_TEAM_away", "AWAY_TEAM_away"])



final = final.drop(columns= ["TEAM_NAME_home", "TEAM_NAME_away", "HOME_TEAM", "AWAY_TEAM", "PLUS_MINUS_home", "PLUS_MINUS_away",
                             "WL_home", "WL_away", "REB_home", "REB_away"])

final.to_csv('./regular_season_limpio.csv', index=False)

