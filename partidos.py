import pandas as pd

games_df = pd.read_csv("nba_predictor/data/game.csv")

print(games_df.sort_values('pts_away'))




#Selección por columnas

#print(games_df["team_name_home"].to_string())



#Selección por filas, iloc y loc. 


#print(games_df.iloc[65600:]) #Del 100 para arriba

#Podemos hacer un df = pd.read_csv(".csv", index_col = "team_home")
