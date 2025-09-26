from nba_api.stats.static import teams, players
from nba_api.stats.endpoints import playercareerstats
import pandas as pd


jugadores_Nikola = players.find_players_by_first_name('Nikola')

#jugador_x = playercareerstats.PlayerCareerStats(200377)

jd = pd.DataFrame(jugadores_Nikola)

#jugador_x.career_totals_regular_season.get_data_frame()



nikolas_activos = jd[jd['is_active'] == True]

print(nikolas_activos.iloc[:])