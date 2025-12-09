# Diccionario abreviación -> nombre completo

"""
Agrupamos los antiguos nombres de las franquicias con los nuevos.
"""
team_codes = {
    "ATL": "Atlanta Hawks",
    "BOS": "Boston Celtics",
    "BKN": "Brooklyn Nets",
    "NJN": "Brooklyn Nets",   # New Jersey Nets, como son misma franquicia
    "CHA": "Charlotte Hornets",
    #"CHA": "Charlotte Bobcats", Como es la misma franquicia 
    "CHI": "Chicago Bulls",
    "CLE": "Cleveland Cavaliers",
    "DAL": "Dallas Mavericks",
    "DEN": "Denver Nuggets",
    "DET": "Detroit Pistons",
    "GSW": "Golden State Warriors",
    "HOU": "Houston Rockets",
    "IND": "Indiana Pacers",
    "LAC": "Los Angeles Clippers",
    "LAL": "Los Angeles Lakers",
    "MEM": "Memphis Grizzlies",
    "MIA": "Miami Heat",
    "MIL": "Milwaukee Bucks",
    "MIN": "Minnesota Timberwolves",
    "NOP": "New Orleans Pelicans",
    "NOH": "New Orleans Pelicans",  # histórico
    "NOK": "New Orleans Pelicans", # New Orleans / Oklahoma City Hornets , donde Chris Paul empezó.
    "NYK": "New York Knicks",
    "OKC": "Oklahoma City Thunder",
    "SEA": "Oklahoma City Thunder",  # histórico
    "ORL": "Orlando Magic",
    "PHI": "Philadelphia 76ers",
    "PHX": "Phoenix Suns",
    "POR": "Portland Trail Blazers",
    "SAC": "Sacramento Kings",
    "SAS": "San Antonio Spurs",
    "TOR": "Toronto Raptors",
    "UTA": "Utah Jazz",
    "WAS": "Washington Wizards",
}


# Diccionario TEAM_ID -> nombre completo
team_ids = {
    1: "Atlanta Hawks",
    2: "Boston Celtics",
    3: "Brooklyn Nets",
    4: "Charlotte Hornets",
    5: "Oklahoma City Thunder",
    6: "New Orleans Pelicans",
    7: "Houston Rockets",
    8: "Portland Trail Blazers",
    9: "Memphis Grizzlies",
    10: "Indiana Pacers",
    11: "Philadelphia 76ers",
    12: "Toronto Raptors",
    13: "Utah Jazz",
    14: "Los Angeles Clippers",
    15: "Los Angeles Lakers",
    16: "Milwaukee Bucks",
    17: "Dallas Mavericks",
    18: "Denver Nuggets",
    19: "Golden State Warriors",
    20: "Miami Heat",
    21: "Minnesota Timberwolves",
    22: "Orlando Magic",
    23: "Phoenix Suns",
    24: "Sacramento Kings",
    25: "San Antonio Spurs",
    26: "Cleveland Cavaliers",
    27: "Detroit Pistons",
    28: "New York Knicks",
    29: "Washington Wizards",
    30: "Chicago Bulls"
}



#Mapeamos las antiguas franquicias con las nuevas, así perdemos fidelidad histórica pero iba a ser necesario 
#una relación para la red neuronal, y así es mucho más fácil de manejar.

nba_to_myid = {
    1610612737: 1,   # Atlanta Hawks
    1610612738: 2,   # Boston Celtics
    1610612751: 3,   # Brooklyn Nets
    1610612766: 4,   # Charlotte Hornets
    1610612760: 5,   # Oklahoma City Thunder
    1610612740: 6,   # New Orleans Pelicans
    1610612745: 7,   # Houston Rockets
    1610612757: 8,   # Portland Trail Blazers
    1610612763: 9,   # Memphis Grizzlies
    1610612754: 10,  # Indiana Pacers
    1610612755: 11,  # Philadelphia 76ers
    1610612761: 12,  # Toronto Raptors
    1610612762: 13,  # Utah Jazz
    1610612746: 14,  # Los Angeles Clippers
    1610612747: 15,  # Los Angeles Lakers
    1610612749: 16,  # Milwaukee Bucks
    1610612742: 17,  # Dallas Mavericks
    1610612743: 18,  # Denver Nuggets
    1610612744: 19,  # Golden State Warriors
    1610612748: 20,  # Miami Heat
    1610612750: 21,  # Minnesota Timberwolves
    1610612753: 22,  # Orlando Magic
    1610612756: 23,  # Phoenix Suns
    1610612758: 24,  # Sacramento Kings
    1610612759: 25,  # San Antonio Spurs
    1610612739: 26,  # Cleveland Cavaliers
    1610612765: 27,  # Detroit Pistons
    1610612752: 28,  # New York Knicks
    1610612764: 29,  # Washington Wizards
    1610612741: 30  # Chicago Bulls
}



#Diccionario de equipo a id de la api, muy útil para coger la información de los últimos partidos de un equipo
equipo_id = {
    "Atlanta Hawks" :   1610612737,   
    "Boston Celtics":   1610612738,   
    "Brooklyn Nets" :   1610612751,  
    "Charlotte Hornets" :    1610612766,
    "Oklahoma City Thunder" :   1610612760,
    "New Orleans Pelicans"  :   1610612740,
    "Houston Rockets"   :   1610612745,
    "Portland Trail Blazers":   1610612757,
    "Memphis Grizzlies" :   1610612763,
    "Indiana Pacers"    :   1610612754,
    "Philadelphia 76ers" :   1610612755,
    "Toronto Raptors"   :   1610612761,
    "Utah Jazz" :   1610612762,
    "Los Angeles Clippers"  :   1610612746,
    "Los Angeles Lakers"    :   1610612747,
    "Milwaukee Bucks"   :   1610612749,
    "Dallas Mavericks"  :   1610612742,
    "Denver Nuggets"    :   1610612743,
    "Golden State Warriors" :   1610612744,
    "Miami Heat"    :   1610612748,
    "Minnesota Timberwolves"    :   1610612750,
    "Orlando Magic" :   1610612753,
    "Phoenix Suns"  :   1610612756,
    "Sacramento Kings"  :   1610612758,
    "San Antonio Spurs" :   1610612759,
    "Cleveland Cavaliers"   :   1610612739,
    "Detroit Pistons"   :   1610612765,
    "New York Knicks"   :   1610612752,
    "Washington Wizards":   1610612764,
    "Chicago Bulls" :   1610612741
    
}


# Diccionario nombre -> índice (para redes neuronales)
team_index = {name: idx for idx, name in enumerate(sorted(set(team_codes.values())))}


def parse_matchup(matchup, team_codes ):
    # Ejemplo: "LAL vs BOS" o "LAL @ BOS"
    matchup = matchup.replace("vs.", "vs").strip()

    
    parts = matchup.split(" ")
    team1, symbol, team2 = parts[0], parts[1], parts[2]

    # Normalizar nombres con el diccionario
    team1 = team_codes.get(team1, team1)
    team2 = team_codes.get(team2, team2)

    if symbol == "vs":
        home, away = team1, team2
    elif symbol == "@":
        home, away = team2, team1
    else:
        raise ValueError(f"Formato de matchup desconocido: {matchup}")

        

    return home, away
