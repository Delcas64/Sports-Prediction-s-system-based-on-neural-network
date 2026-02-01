#Construir las features de los equipos para las redes#
import os
import pandas as pd
import numpy as np


import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset

import joblib  # para guardar el scaler

from app.ml.teams import team_codes, team_ids, nba_to_myid, equipo_id, team_index, parse_matchup
from app.ml.stats_ultimos_partidos import ultimos_partidos

import xgboost as xgb



#Si se puede ejcutar la red con CUDA, para acelerar el entrenamiento mediante la gráfica
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")



# ====== CARGA GLOBAL ======

ruta_archivo = os.path.dirname(os.path.abspath(__file__))
BASE_PATH = os.path.join(ruta_archivo,"../data/")
# Función para cargar archivos de forma segura
def load_data(filename):
    path = os.path.join(BASE_PATH, filename)
    if os.path.exists(path):
        return pd.read_csv(path)
    else:
        print(f"No se encontró el archivo: {filename}")
        return None






ruta_archivo = os.path.dirname(os.path.abspath(__file__))

SCALER = os.path.join(ruta_archivo,"../models/scaler_temporadas.pkl")

#-------------LSTM-----------------------


def estimate_possessions(df, prefix):
    return (
        df[f"FGA_{prefix}"]
        - df[f"OREB_{prefix}"]
        + df[f"TOV_{prefix}"]
        + 0.44 * df[f"FTA_{prefix}"]
    )


def build_sequence(df, team_id, columnas, seq_len):

  df_team = df[
      (df['TEAM_ID_HOME'] == team_id) |
      (df['TEAM_ID_AWAY'] == team_id)
  ].sort_values('GAME_DATE')

  feats = df_team[columnas].values.astype(np.float32)

  if len(feats) >= seq_len:
      return feats[-seq_len:]
  else:
      pad = np.zeros((seq_len - len(feats), feats.shape[1]), dtype=np.float32)
      return np.vstack([pad, feats])

def construirDf(df_temporadas):
    df_temporadas['GAME_ID'] = df_temporadas['GAME_ID_HOME']

    featuresInnecesariasTemporadas = [
        'GAME_DATE_HOME','SEASON_HOME','GAME_TYPE_HOME',
        'HOME_TEAM_HOME','AWAY_TEAM_HOME','GAME_DATE_AWAY',
        'HOME_TEAM_AWAY','GAME_TYPE_AWAY','AWAY_TEAM_AWAY',
        'TEAM_ABBREVIATION_HOME', 'TEAM_ABBREVIATION_AWAY',
        'MATCHUP_HOME', 'MATCHUP_AWAY',
        'SEASON_ID_HOME', 'SEASON_ID_AWAY','SEASON_AWAY',
        'VIDEO_AVAILABLE_HOME', 'VIDEO_AVAILABLE_AWAY',
        'GAME_ID_HOME', 'GAME_ID_AWAY',
        'TEAM_NAME_HOME','TEAM_NAME_AWAY', 'MIN_HOME','MIN_AWAY',
        'HOME_TEAM','AWAY_TEAM'
    ]

    df_temporadas = df_temporadas.drop(columns=featuresInnecesariasTemporadas)

    df_temporadas["WL_HOME"] = (df_temporadas["WL_HOME"] == "W").astype(int) # 1 = W, 0 = L
    df_temporadas["WL_AWAY"] = (df_temporadas["WL_AWAY"] == "W").astype(int) # 1 = W, 0 = L


    #La idea es, ¿ganará HOME? La probabilidad de que pase es lo que devolverá la red.
    df_temporadas["TARGET"] = df_temporadas["WL_HOME"] # 1 = gana HOME, 0 = pierde HOME



    #Convertimos fecha
    df_temporadas["GAME_DATE"] = pd.to_datetime(df_temporadas["GAME_DATE"])

    # Ordenar por fecha
    df_temporadas = df_temporadas.sort_values("GAME_DATE").reset_index(drop=True)

    #No tiene más importancia un partido de temporada regular que uno
    #de playoffs para el modelo
    df_temporadas = df_temporadas.drop(columns="GAME_TYPE")

    df_temporadas["FGM_DIFF"] = df_temporadas["FGM_HOME"] - df_temporadas["FGM_AWAY"]
    df_temporadas["FG3M_DIFF"] = df_temporadas["FG3M_HOME"] - df_temporadas["FG3M_AWAY"]
    df_temporadas["FTM_DIFF"] = df_temporadas["FTM_HOME"] - df_temporadas["FTM_AWAY"]
    df_temporadas["REB_DIFF"] = df_temporadas["REB_HOME"] - df_temporadas["REB_AWAY"]
    df_temporadas["AST_DIFF"] = df_temporadas["AST_HOME"] - df_temporadas["AST_AWAY"]
    df_temporadas["TOV_DIFF"] = df_temporadas["TOV_HOME"] - df_temporadas["TOV_AWAY"]
    df_temporadas["STL_DIFF"] = df_temporadas["STL_HOME"] - df_temporadas["STL_AWAY"]

    df_temporadas["POSS_HOME"] = estimate_possessions(df_temporadas, "HOME")
    df_temporadas["POSS_AWAY"] = estimate_possessions(df_temporadas, "AWAY")

    # --------- OFFENSIVE / DEFENSIVE RATING ---------
    df_temporadas["ORTG_HOME"] = 100 * df_temporadas["PTS_HOME"] / df_temporadas["POSS_HOME"]
    df_temporadas["ORTG_AWAY"] = 100 * df_temporadas["PTS_AWAY"] / df_temporadas["POSS_AWAY"]

    df_temporadas["DRTG_HOME"] = 100 * df_temporadas["PTS_AWAY"] / df_temporadas["POSS_HOME"]
    df_temporadas["DRTG_AWAY"] = 100 * df_temporadas["PTS_HOME"] / df_temporadas["POSS_AWAY"]

    # --------- NET RATING ---------
    df_temporadas["NETRTG_HOME"] = df_temporadas["ORTG_HOME"] - df_temporadas["DRTG_HOME"]
    df_temporadas["NETRTG_AWAY"] = df_temporadas["ORTG_AWAY"] - df_temporadas["DRTG_AWAY"]

    # Reemplazar infinitos debido a divisiones por cero.
    df_temporadas = df_temporadas.replace([np.inf, -np.inf], 0)

    # Racha últimos 10 partidos como LOCAL, si ha ganado 7, se guarda el valor 7.
    df_temporadas["STREAK_HOME"] = (
        df_temporadas
        .groupby("TEAM_ID_HOME")["WL_HOME"]
        .rolling(10) #sliding window, 10 como local
        .sum()
        .reset_index(0,drop=True)
    )

    # Racha últimos 10 partidos como VISITANTE
    df_temporadas["STREAK_AWAY"] = (
        df_temporadas
        .groupby("TEAM_ID_AWAY")["WL_AWAY"]
        .rolling(10)
        .sum()
        .reset_index(0,drop=True)
    )

    #Rellenamos los NaN de las rachas
    df_temporadas[["STREAK_HOME","STREAK_AWAY"]] = \
        df_temporadas[["STREAK_HOME","STREAK_AWAY"]].fillna(0)
    
    return df_temporadas

def ultimos_partidos(df, team_id, n=10):
    """Devuelve los últimos N partidos del equipo desde temporadas.csv"""

    df_team = df[
        (df["TEAM_ID_HOME"] == team_id) | (df["TEAM_ID_AWAY"] == team_id) 
    ].sort_values("GAME_DATE")

    return df_team.tail(n).copy()


def ultimos_partidos_local(df, team_id, n=10):
    """Devuelve los últimos N partidos del equipo desde temporadas.csv"""

    df_team = df[
        (df["TEAM_ID_HOME"] == team_id) 
    ].sort_values("GAME_DATE")

    return df_team.tail(n).copy()

def ultimos_partidos_visitante(df, team_id, n=10):
    """Devuelve los últimos N partidos del equipo desde temporadas.csv"""

    df_team = df[
        (df["TEAM_ID_AWAY"] == team_id) 
    ].sort_values("GAME_DATE")

    return df_team.tail(n).copy()




#Por tema de rapidez, que no calcule los 10 últimos
def predecir_partido(home_name, away_name, model, seq_len=10):
    """
    Predice probabilidad de victoria del equipo HOME.
    Versión simple: usa ultimos_partidos() directamente.
    """

    home_id = nba_to_myid[equipo_id[home_name]]
    away_id = nba_to_myid[equipo_id[away_name]]

    # Cargar scaler
    scaler = joblib.load(SCALER)

    df_temporadas = load_data('temporadas.csv')

    df_temporadas = construirDf(df_temporadas)

    
    df_home = ultimos_partidos(df_temporadas, home_id, n=seq_len)
    df_away = ultimos_partidos(df_temporadas, away_id, n=seq_len)


    # --- HOME ---
    #df_home, _ = ultimos_partidos(home_name)   # usa NOMBRE, no ID

    # --- AWAY ---
    #df_away, _ = ultimos_partidos(away_name)


    """
    # 2. Combinar para calcular diffs igual que antes
    df = pd.concat([df_home, df_away], ignore_index=True)

    


    df = df_home.sort_values("GAME_DATE").copy()

    es_local = df["HOME"] == home_name


    #Mirar el tema de _TEAM y _RIVAL y _HOME y _AWAY

    # ---- DIFFS ----
    for stat in ["FGM", "FG3M", "FTM", "REB", "AST", "TOV", "STL"]:
        df[f"{stat}_DIFF"] = np.where(
            es_local,
            df[f"{stat}_TEAM"] - df[f"{stat}_RIVAL"],
            df[f"{stat}_RIVAL"] - df[f"{stat}_TEAM"]
        )



    df['TEAM_ID_HOME'] = df['HOME'].apply(lambda x: nba_to_myid[equipo_id[x]])
    df['TEAM_ID_AWAY'] = df['AWAY'].apply(lambda x: nba_to_myid[equipo_id[x]])

    # ---- NET RATING ----
    df["POSS_TEAM"] = estimate_possessions(df, "TEAM")
    df["POSS_RIVAL"] = estimate_possessions(df, "RIVAL")

    df["ORTG_TEAM"] = 100 * df["PTS_TEAM"] / df["POSS_TEAM"]
    df["ORTG_RIVAL"] = 100 * df["PTS_RIVAL"] / df["POSS_RIVAL"]
    df["DRTG_TEAM"] = 100 * df["PTS_RIVAL"] / df["POSS_TEAM"]
    df["DRTG_RIVAL"] = 100 * df["PTS_TEAM"] / df["POSS_RIVAL"]

    df["NETRTG_HOME"] = np.where(
        es_local,
        df["ORTG_TEAM"] - df["DRTG_TEAM"],
        df["ORTG_RIVAL"] - df["DRTG_RIVAL"]
    )
    df["NETRTG_AWAY"] = -df["NETRTG_HOME"]

    # ---- STREAK ----
    gano = np.where(
        es_local,
        df["PTS_TEAM"] > df["PTS_RIVAL"],   # ganó siendo local
        df["PTS_RIVAL"] > df["PTS_TEAM"]    # ganó siendo visitante
    ).astype(int)

    streak_home = gano[es_local][-10:].sum()
    streak_away = gano[~es_local][-10:].sum()


    df['STREAK_HOME'] = streak_home
    df['STREAK_AWAY'] = streak_away


    #---AHORA PARA EL EQUIPO VISITANTE--------------------------------


    df2 = df_away.sort_values("GAME_DATE").copy()

    es_local2 = df2["HOME"] == away_name


    # ---- DIFFS ----
    for stat in ["FGM", "FG3M", "FTM", "REB", "AST", "TOV", "STL"]:
        df2[f"{stat}_DIFF"] = np.where(
            es_local2,
            df2[f"{stat}_TEAM"] - df2[f"{stat}_RIVAL"],
            df2[f"{stat}_RIVAL"] - df2[f"{stat}_TEAM"]
        )


    df2['TEAM_ID_HOME'] = df2['HOME'].apply(lambda x: nba_to_myid[equipo_id[x]])
    df2['TEAM_ID_AWAY'] = df2['AWAY'].apply(lambda x: nba_to_myid[equipo_id[x]])

    # ---- NET RATING ----
    df2["POSS_TEAM"] = estimate_possessions(df2, "TEAM")
    df2["POSS_RIVAL"] = estimate_possessions(df2, "RIVAL")

    df2["ORTG_TEAM"] = 100 * df2["PTS_TEAM"] / df2["POSS_TEAM"]
    df2["ORTG_RIVAL"] = 100 * df2["PTS_RIVAL"] / df2["POSS_RIVAL"]
    df2["DRTG_TEAM"] = 100 * df2["PTS_RIVAL"] / df2["POSS_TEAM"]
    df2["DRTG_RIVAL"] = 100 * df2["PTS_TEAM"] / df2["POSS_RIVAL"]

    df2["NETRTG_HOME"] = np.where(
        es_local2,
        df2["ORTG_TEAM"] - df2["DRTG_TEAM"],
        df2["ORTG_RIVAL"] - df2["DRTG_RIVAL"]
    )
    df2["NETRTG_AWAY"] = -df2["NETRTG_HOME"]

    # ---- STREAK ----
    gano2 = np.where(
        es_local2,
        df2["PTS_TEAM"] > df2["PTS_RIVAL"],   # ganó siendo local
        df2["PTS_RIVAL"] > df2["PTS_TEAM"]    # ganó siendo visitante
    ).astype(int)

    streak_home2 = gano2[es_local2][-10:].sum()
    streak_away2 = gano2[~es_local2][-10:].sum()


    df2['STREAK_HOME'] = streak_home2
    df2['STREAK_AWAY'] = streak_away2

    """
    columnasUtiles = ['FGM_DIFF', 'FG3M_DIFF', 'FTM_DIFF', 'REB_DIFF', 'AST_DIFF', 
                      'TOV_DIFF', 'STL_DIFF', 'STREAK_HOME', 'STREAK_AWAY', 'NETRTG_HOME', 'NETRTG_AWAY']
     




    #df_total = pd.concat([df, df2], ignore_index=True)
    df_total = pd.concat([df_home, df_away], ignore_index=True)
    df_total["GAME_DATE"] = pd.to_datetime(df_total["GAME_DATE"])


    # Secuencias EXACTAS al entrenamiento
    seq_home = build_sequence(df_total, home_id, columnasUtiles, seq_len)
    seq_away = build_sequence(df_total, away_id, columnasUtiles, seq_len)


    X = np.concatenate([seq_home, seq_away], axis=0)  # (20, n_features)

    # Escalado
    X = scaler.transform(X)
    X = torch.tensor(X, dtype=torch.float32).unsqueeze(0).to(device)

    #model.eval()

    with torch.no_grad():
      logits = model(X)
      prob_home = torch.sigmoid(logits).item()



    #print(f"\nPredicción: {home_name} vs {away_name}")
    #print("--------------------------------------------")
    #print(f"Prob HOME: {prob_home:.3f}")
    #print(f"Prob AWAY: {1 - prob_home:.3f}")
    return {
    'home_win_prob': round(prob_home, 2),
    'away_win_prob': round((1 -prob_home), 2),
    'home_team': home_name,
    'away_team': away_name
    }

    #return f"Es un {prob_home*100:.2f}% probable que {home_name} gane a {away_name}."

    

   


# ------------XGBOOST-----------------------


def limpiarDf(df_temporadas, df_jugadores):
    df_temporadas['GAME_ID'] = df_temporadas['GAME_ID_HOME']

    featuresInnecesariasTemporadas = [
        'GAME_DATE_HOME','SEASON_HOME','GAME_TYPE_HOME',
        'HOME_TEAM_HOME','AWAY_TEAM_HOME','GAME_DATE_AWAY',
        'HOME_TEAM_AWAY','GAME_TYPE_AWAY','AWAY_TEAM_AWAY',
        'TEAM_ABBREVIATION_HOME', 'TEAM_ABBREVIATION_AWAY',
        'MATCHUP_HOME', 'MATCHUP_AWAY',
        'SEASON_ID_HOME', 'SEASON_ID_AWAY','SEASON_AWAY',
        'VIDEO_AVAILABLE_HOME', 'VIDEO_AVAILABLE_AWAY',
        'GAME_ID_HOME', 'GAME_ID_AWAY',
        'TEAM_NAME_HOME','TEAM_NAME_AWAY', 'MIN_HOME','MIN_AWAY',
        'HOME_TEAM','AWAY_TEAM'
        ]

    #Nos quedamos solo con los ID's de los equipos. TEAM_HOME_ID y TEAM_AWAY_ID. Los míos. No los de la NBA

    df_temporadas = df_temporadas.drop(columns=featuresInnecesariasTemporadas)


    #Seguimos con jugadores.csv
    #Nos quedamos con MATCHUP, necesario para luego
    featuresInnecesariasJugadores = [
        'WL','SEASON_YEAR','PLAYER_NAME',
        'NICKNAME','TEAM_ABBREVIATION','TEAM_NAME','NBA_FANTASY_PTS', 'DD2',
        'TD3', 'WNBA_FANTASY_PTS', 'GP_RANK', 'W_RANK', 'L_RANK', 'W_PCT_RANK',
        'MIN_RANK', 'FGM_RANK', 'FGA_RANK', 'FG_PCT_RANK', 'FG3M_RANK',
        'FG3A_RANK', 'FG3_PCT_RANK', 'FTM_RANK', 'FTA_RANK', 'FT_PCT_RANK',
        'OREB_RANK', 'DREB_RANK', 'REB_RANK', 'AST_RANK', 'TOV_RANK',
        'STL_RANK', 'BLK_RANK', 'BLKA_RANK', 'PF_RANK', 'PFD_RANK', 'PTS_RANK',
        'PLUS_MINUS_RANK', 'NBA_FANTASY_PTS_RANK', 'DD2_RANK', 'TD3_RANK',
        'WNBA_FANTASY_PTS_RANK', 'AVAILABLE_FLAG', 'MIN_SEC', 'TEAM_COUNT',
        'SEASON'
        ]

    df_jugadores = df_jugadores.drop(columns=featuresInnecesariasJugadores)

    df_temporadas["WL_HOME"] = (df_temporadas["WL_HOME"] == "W").astype(int) # 1 = W, 0 = L
    df_temporadas["WL_AWAY"] = (df_temporadas["WL_AWAY"] == "W").astype(int) # 1 = W, 0 = L


    #La idea es, ¿ganará HOME? Probabilidad de que pase es lo que devolverá la red.
    df_temporadas["TARGET"] = df_temporadas["WL_HOME"] # 1 = gana HOME, 0 = pierde HOME



    #Convertimos fecha
    df_temporadas["GAME_DATE"] = pd.to_datetime(df_temporadas["GAME_DATE"])
    df_jugadores["GAME_DATE"] = pd.to_datetime(df_jugadores["GAME_DATE"])
    # Ordenar por fecha
    df_temporadas = df_temporadas.sort_values("GAME_DATE").reset_index(drop=True)

    #No tiene más importancia un partido de temporada regular que uno
    #de playoffs para el modelo
    df_temporadas = df_temporadas.drop(columns="GAME_TYPE")

    df_temporadas["POSS_HOME"] = estimate_possessions(df_temporadas, "HOME")
    df_temporadas["POSS_AWAY"] = estimate_possessions(df_temporadas, "AWAY")

    # --------- OFFENSIVE / DEFENSIVE RATING ---------
    df_temporadas["ORTG_HOME"] = 100 * df_temporadas["PTS_HOME"] / df_temporadas["POSS_HOME"]
    df_temporadas["ORTG_AWAY"] = 100 * df_temporadas["PTS_AWAY"] / df_temporadas["POSS_AWAY"]

    df_temporadas["DRTG_HOME"] = 100 * df_temporadas["PTS_AWAY"] / df_temporadas["POSS_HOME"]
    df_temporadas["DRTG_AWAY"] = 100 * df_temporadas["PTS_HOME"] / df_temporadas["POSS_AWAY"]

    # --------- NET RATING ---------
    df_temporadas["NETRTG_HOME"] = df_temporadas["ORTG_HOME"] - df_temporadas["DRTG_HOME"]
    df_temporadas["NETRTG_AWAY"] = df_temporadas["ORTG_AWAY"] - df_temporadas["DRTG_AWAY"]

    # Reemplazar infinitos debido a divisiones por cero.
    df_temporadas = df_temporadas.replace([np.inf, -np.inf], 0)

    return df_temporadas, df_jugadores


def team_stats_before_game(df, team_id, game_date, n_games=10):
    """
    Estadísticas históricas avanzadas de un equipo ANTES de game_date
    (sin data leakage).
    """

    # -------- HOME --------
    home = df[
        (df["TEAM_ID_HOME"] == team_id) &
        (df["GAME_DATE"] < game_date)
    ][[
        "GAME_DATE",
        "PTS_HOME", "REB_HOME", "AST_HOME",
        "FG_PCT_HOME", "FG3_PCT_HOME", "FT_PCT_HOME",
        "TOV_HOME", "STL_HOME",
        "POSS_HOME",
        "ORTG_HOME", "DRTG_HOME", "NETRTG_HOME",
        "WL_HOME"
    ]].rename(columns={
        "PTS_HOME": "PTS",
        "REB_HOME": "REB",
        "AST_HOME": "AST",
        "FG_PCT_HOME": "FG_PCT",
        "FG3_PCT_HOME": "FG3_PCT",
        "FT_PCT_HOME": "FT_PCT",
        "TOV_HOME": "TOV",
        "STL_HOME": "STL",
        "POSS_HOME": "PACE",
        "ORTG_HOME": "ORTG",
        "DRTG_HOME": "DRTG",
        "NETRTG_HOME": "NETRTG",
        "WL_HOME": "WL"
    })

    # -------- AWAY --------
    away = df[
        (df["TEAM_ID_AWAY"] == team_id) &
        (df["GAME_DATE"] < game_date)
    ][[
        "GAME_DATE",
        "PTS_AWAY", "REB_AWAY", "AST_AWAY",
        "FG_PCT_AWAY", "FG3_PCT_AWAY", "FT_PCT_AWAY",
        "TOV_AWAY", "STL_AWAY",
        "POSS_AWAY",
        "ORTG_AWAY", "DRTG_AWAY", "NETRTG_AWAY",
        "WL_AWAY"
    ]].rename(columns={
        "PTS_AWAY": "PTS",
        "REB_AWAY": "REB",
        "AST_AWAY": "AST",
        "FG_PCT_AWAY": "FG_PCT",
        "FG3_PCT_AWAY": "FG3_PCT",
        "FT_PCT_AWAY": "FT_PCT",
        "TOV_AWAY": "TOV",
        "STL_AWAY": "STL",
        "POSS_AWAY": "PACE",
        "ORTG_AWAY": "ORTG",
        "DRTG_AWAY": "DRTG",
        "NETRTG_AWAY": "NETRTG",
        "WL_AWAY": "WL"
    })

    past = (
        pd.concat([home, away])
        .sort_values("GAME_DATE")
        .tail(n_games)
    )

    if past.empty:
        return {k: 0 for k in [
            "PTS_mean", "REB_mean", "AST_mean",
            "FG_PCT_mean", "FG3_PCT_mean", "FT_PCT_mean",
            "TOV_mean", "STL_mean",
            "PACE_mean",
            "ORTG_mean", "DRTG_mean", "NETRTG_mean",
            "WINS"
        ]}

    return {
        "PTS_mean": past["PTS"].mean(),
        "REB_mean": past["REB"].mean(),
        "AST_mean": past["AST"].mean(),
        "FG_PCT_mean": past["FG_PCT"].mean(),
        "FG3_PCT_mean": past["FG3_PCT"].mean(),
        "FT_PCT_mean": past["FT_PCT"].mean(),
        "TOV_mean": past["TOV"].mean(),
        "STL_mean": past["STL"].mean(),
        "PACE_mean": past["PACE"].mean(),
        "ORTG_mean": past["ORTG"].mean(),
        "DRTG_mean": past["DRTG"].mean(),
        "NETRTG_mean": past["NETRTG"].mean(),
        "WINS": past["WL"].sum()
    }



def player_stats_before_game(df_players, team_id, game_date, n_games=5):
    """
    Calcula estadísticas históricas de los jugadores de un equipo
    ANTES de game_date, sin leakage.
    """

    past = df_players[
        (df_players["TEAM_ID"] == team_id) &
        (df_players["GAME_DATE"] < game_date)
    ].sort_values("GAME_DATE")

    if past.empty:
        return {
            "PTS_mean": 0,
            "REB_mean": 0,
            "AST_mean": 0,
            "FG_PCT_mean": 0,
            "FG3_PCT_mean": 0,
            "FT_PCT_mean": 0,
            "MIN_mean": 0
        }

    # Últimos n partidos por jugador
    past_last = (
        past
        .groupby("PLAYER_ID", group_keys=False)
        .tail(n_games)
    )

    return {
        "PTS_mean": past_last["PTS"].mean(),
        "REB_mean": past_last["REB"].mean(),
        "AST_mean": past_last["AST"].mean(),
        "FG_PCT_mean": past_last["FG_PCT"].mean(),
        "FG3_PCT_mean": past_last["FG3_PCT"].mean(),
        "FT_PCT_mean": past_last["FT_PCT"].mean(),
        "MIN_mean": past_last["MIN"].mean()
    }






XGB_FEATURE_COLS = [
    'TEAM_REB_DIFF', 'TEAM_AST_DIFF', 'TEAM_FG_PCT_DIFF',
    'TEAM_FG3_PCT_DIFF', 'TEAM_FT_PCT_DIFF', 'TEAM_TOV_DIFF',
    'TEAM_STL_DIFF', 'TEAM_PACE_DIFF', 'TEAM_ORTG_DIFF', 'TEAM_DRTG_DIFF',
    'TEAM_NETRTG_DIFF', 'TEAM_STREAK_DIFF', 'PLY_PTS_DIFF', 'PLY_REB_DIFF',
    'PLY_AST_DIFF', 'PLY_FG_PCT_DIFF', 'PLY_FG3_PCT_DIFF',
    'PLY_FT_PCT_DIFF', 'PLY_MIN_DIFF'
]

def build_features_xgb(df_temporadas,df_jugadores, homename, awayname, ngames_team: int = 10, ngames_player: int = 5):
    #Construye el vector de features para XGBoost dado el nombre de los equipos
    homeid = nba_to_myid[equipo_id[homename]]
    awayid = nba_to_myid[equipo_id[awayname]]

    # Usamos la misma lógica que en el bucle de construcción de dfXGB,
    # pero solo para "hoy" (o la fecha del partido a predecir).
    gamedate = pd.Timestamp.today()

    hometeam = team_stats_before_game(df_temporadas, homeid, gamedate, n_games=ngames_team)
    awayteam = team_stats_before_game(df_temporadas, awayid, gamedate, n_games=ngames_team)
    homeplayers = player_stats_before_game(df_jugadores, homeid, gamedate, n_games=ngames_player)
    awayplayers = player_stats_before_game(df_jugadores, awayid, gamedate, n_games=ngames_player)

    row = {
        "GAME_DATE": gamedate,

        # ---- EQUIPO (AVANZADO) ----
        #"TEAM_PTS_DIFF": home_team["PTS_mean"] - away_team["PTS_mean"],
        "TEAM_REB_DIFF": hometeam["REB_mean"] - awayteam["REB_mean"],
        "TEAM_AST_DIFF": hometeam["AST_mean"] - awayteam["AST_mean"],

        "TEAM_FG_PCT_DIFF": hometeam["FG_PCT_mean"] - awayteam["FG_PCT_mean"],
        "TEAM_FG3_PCT_DIFF": hometeam["FG3_PCT_mean"] - awayteam["FG3_PCT_mean"],
        "TEAM_FT_PCT_DIFF": hometeam["FT_PCT_mean"] - awayteam["FT_PCT_mean"],

        "TEAM_TOV_DIFF": hometeam["TOV_mean"] - awayteam["TOV_mean"],
        "TEAM_STL_DIFF": hometeam["STL_mean"] - awayteam["STL_mean"],

        "TEAM_PACE_DIFF": hometeam["PACE_mean"] - awayteam["PACE_mean"],

        "TEAM_ORTG_DIFF": hometeam["ORTG_mean"] - awayteam["ORTG_mean"],
        "TEAM_DRTG_DIFF": hometeam["DRTG_mean"] - awayteam["DRTG_mean"],
        "TEAM_NETRTG_DIFF": hometeam["NETRTG_mean"] - awayteam["NETRTG_mean"],

        "TEAM_STREAK_DIFF": hometeam["WINS"] - awayteam["WINS"],

        # ---- JUGADORES ----
        "PLY_PTS_DIFF": homeplayers["PTS_mean"] - awayplayers["PTS_mean"],
        "PLY_REB_DIFF": homeplayers["REB_mean"] - awayplayers["REB_mean"],
        "PLY_AST_DIFF": homeplayers["AST_mean"] - awayplayers["AST_mean"],
        "PLY_FG_PCT_DIFF": homeplayers["FG_PCT_mean"] - awayplayers["FG_PCT_mean"],
        "PLY_FG3_PCT_DIFF": homeplayers["FG3_PCT_mean"] - awayplayers["FG3_PCT_mean"],
        "PLY_FT_PCT_DIFF": homeplayers["FT_PCT_mean"] - awayplayers["FT_PCT_mean"],
        "PLY_MIN_DIFF": homeplayers["MIN_mean"] - awayplayers["MIN_mean"],

        # TARGET
        "TARGET": df_temporadas["TARGET"]
    }

    
    # Vector EXACTO en orden correcto (NO necesita dfXGB)
    X = np.array([[row[col] for col in XGB_FEATURE_COLS]], dtype=np.float32)
    return X




def predecir_partido_xgb(homename: str, awayname: str, model) -> float:
    #Devuelve probabilidad de victoria del HOME usando XGBoost.
    df_jugadores = load_data("jugadores.csv")
    df_temporadas = load_data("temporadas.csv")
    df_temporadas, df_jugadores = limpiarDf(df_temporadas, df_jugadores)
    X = build_features_xgb(df_temporadas,df_jugadores,homename, awayname)
    dX = xgb.DMatrix(X)

   
    prob_home = float(model.predict(dX)[0])


    return {
    'home_win_prob': round(prob_home, 2),
    'away_win_prob': round((1 -prob_home), 2),
    'home_team': homename,
    'away_team': awayname
    }
    
    


