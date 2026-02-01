import requests
from datetime import datetime, timedelta


def get_upcoming_matches(limit=10, max_days_ahead=5):
    # Usar ESPN API para próximos partidos (más fiable)
    url = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard"
    
    
    for offset in range(max_days_ahead):

        # Día que vamos a consultar (hoy + offset)
        date = (datetime.utcnow() + timedelta(days=offset)).strftime("%Y%m%d")
        url = f"{url}?dates={date}"
        print(f"Consultando ESPN para fecha: {date}")

        response = requests.get(url)
        data = response.json()
        
        matches = []
        for event in data.get("events", []):
            # Solo partidos upcoming o hoy
            status = event["status"]["type"]["state"] #shortDetail
            print(f'El status es: {status}')
            if status == 'pre':
                matches.append({
                    "id": event["id"],
                    "date": event["date"][:10],
                    "home": event["competitions"][0]["competitors"][0]["team"]["displayName"],
                    "away": event["competitions"][0]["competitors"][1]["team"]["displayName"]
                })
                if len(matches) >= limit:
                    break
        

        
         # Si hemos encontrado partidos futuros en este día → devolvemos
        if matches:
            return matches

    print("STATUS ESPN:", response.status_code)
    print("RAW keys:", list(data.keys()))
    print("EVENTS LEN:", len(data.get("events", [])))
    print("MATCHES:", matches)
   
    # Si en varios días no encontramos partidos futuros → fallback
    return [{
        "id": 1,
        "date": "2026-01-18",
        "home": "Los Angeles Lakers",
        "away": "Golden State Warriors"
    }]

