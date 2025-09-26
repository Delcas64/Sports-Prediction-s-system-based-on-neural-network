import pandas as pd
import os

rutaActual = os.path.dirname(os.path.abspath(__file__))

rutaArchivo = os.path.join(rutaActual, '../data/common_player_info.csv')

jugadores = pd.read_csv(rutaArchivo)


jugadores_Activos = jugadores.loc[jugadores['to_year'] > 2009, ['first_name', 'last_name'] ]


print(jugadores_Activos)