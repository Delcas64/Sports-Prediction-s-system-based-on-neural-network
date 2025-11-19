from nba_api.stats.endpoints import commonplayerinfo    
from nba_api.stats.static import teams
from nba_api.stats.endpoints import commonteamroster
import pandas as pd


equipos = teams.get_teams()

nombre = "boston celtics"
team = next((t for t in equipos if t['full_name'].lower() == nombre.lower()), None)

id = team['id']
roster = commonteamroster.CommonTeamRoster(team_id=id)
df_roster = roster.get_data_frames()[0]

with pd.option_context('display.max_columns',None,'display.width',0):
    print(df_roster.to_string(index=False))


# ---------- 3) Buscar el jugador dentro del roster ----------
#nombre_jugador = "Jrue Holiday"  # ojo: Jrue no está en POR hoy; es solo ejemplo

# Búsqueda tolerante (sin mayúsculas/minúsculas y con espacios limpios)
#mask = df_roster['PLAYER'].str.casefold().str.strip() == nombre_jugador.casefold().strip()

"""
for _, jugador in df_roster.iterrows():
    if jugador['PLAYER'] == 'Jrue Holiday':
        idHoliday = jugador['PLAYER_ID']


stats = commonplayerinfo.CommonPlayerInfo(player_id=idHoliday)
df_stats = stats.get_data_frames()[0]

# Ver toda la fila/tabla resultante
with pd.option_context('display.max_columns', None, 'display.width', 0):
    print(df_stats.to_string(index=False))

    
"""