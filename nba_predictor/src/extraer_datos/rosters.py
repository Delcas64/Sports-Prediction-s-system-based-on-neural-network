from nba_api.stats.static import teams
from nba_api.stats.endpoints import commonteamroster
import pandas as pd
import time


#Desactualizados. :((((
equipos = teams.get_teams()

player_team_map = []


for equipo in equipos:
    team_id = equipo['id']
    nombre = equipo['full_name']
    print(f"Descargando roster de {nombre}...")

    try:
        roster = commonteamroster.CommonTeamRoster(team_id=team_id)
        df_roster = roster.get_data_frames()[0]
        df_roster['TEAM_ID'] = team_id
        df_roster['TEAM_NAME'] = nombre
        player_team_map.append(df_roster[['PLAYER_ID', 'PLAYER','TEAM_NAME','TEAM_ID']])
        print(f"  -> {len(df_roster)} jugadores añadidos.")
        time.sleep(1)
    except Exception as e:
        print(f'Error con el equipo{nombre}:{e}')



# Al final:
print(f"\nEquipos procesados con éxito: {len(player_team_map)}")

if player_team_map:
    df_jugadores_por_equipos = pd.concat(player_team_map, ignore_index=True)
    df_jugadores_por_equipos.to_csv('prueba_roster.csv', index=False)
else:
    print(" No se añadió ningún equipo a player_team_map")