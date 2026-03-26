import requests
from datetime import datetime


def fetch_json(url):
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    return r.json()


def get_today_schedule():
    today = datetime.today().strftime("%Y-%m-%d")
    url = (
        f"https://statsapi.mlb.com/api/v1/schedule"
        f"?sportId=1&date={today}&hydrate=team,linescore,probablePitcher"
    )
    data = fetch_json(url)
    dates = data.get("dates", [])
    if not dates:
        return []
    return dates[0].get("games", [])


def get_lineup(game_pk):
    url = f"https://statsapi.mlb.com/api/v1/game/{game_pk}/boxscore"
    data = fetch_json(url)

    lineups = {"home": [], "away": []}

    for side in ["home", "away"]:
        players = data.get("teams", {}).get(side, {}).get("players", {})

        confirmed = [
            {
                "player_id": p["person"]["id"],
                "name": p["person"]["fullName"],
                "order": p["battingOrder"],
                "team": data["teams"][side]["team"]["name"],
            }
            for p in players.values()
            if p.get("battingOrder")
        ]

        if confirmed:
            confirmed = sorted(confirmed, key=lambda x: int(x["order"]))
            lineups[side] = confirmed
        else:
            projected = [
                {
                    "player_id": p["person"]["id"],
                    "name": p["person"]["fullName"],
                    "order": None,
                    "team": data["teams"][side]["team"]["name"],
                }
                for p in players.values()
            ]
            lineups[side] = projected

    return lineups


def get_park_factor(team_id):
    try:
        url = f"https://statsapi.mlb.com/api/v1/teams/{team_id}"
        data = fetch_json(url)
        venue = data["teams"][0]["venue"]["id"]

        url = f"https://statsapi.mlb.com/api/v1/venues/{venue}"
        data = fetch_json(url)

        return data.get("venues", [{}])[0].get("fieldInfo", {}).get("capacity", 1)
    except Exception:
        return 1


def get_weather(game_pk):
    try:
        url = f"https://statsapi.mlb.com/api/v1.1/game/{game_pk}/feed/live"
        data = fetch_json(url)

        weather = data.get("gameData", {}).get("weather", {})
        return {
            "temp": weather.get("temp"),
            "wind": weather.get("wind"),
            "condition": weather.get("condition"),
        }
    except Exception:
        return {
            "temp": None,
            "wind": None,
            "condition": None,
        }


def get_today_games_and_lineups():
    games = get_today_schedule()
    output = []

    for g in games:
        game_pk = g["gamePk"]

        home_team = g["teams"]["home"]["team"]
        away_team = g["teams"]["away"]["team"]

        home_pitcher = g["teams"]["home"].get("probablePitcher")
        away_pitcher = g["teams"]["away"].get("probablePitcher")

        if not home_pitcher or not away_pitcher:
            continue

        lineups = get_lineup(game_pk)
        weather = get_weather(game_pk)
        park_factor = get_park_factor(home_team["id"])

        context = {
            "park_factor": park_factor,
            "weather_temp": weather["temp"],
            "weather_wind": weather["wind"],
            "weather_condition": weather["condition"],
        }

        for side, pitcher, home_flag in [
            ("away", home_pitcher, 0),
            ("home", away_pitcher, 1),
        ]:
            pitcher_id = pitcher["id"]
            pitcher_name = pitcher["fullName"]
            opponent = home_team["name"] if side == "away" else away_team["name"]

            for hitter in lineups[side]:
                output.append({
                    "gamePk": game_pk,
                    "hitter_id": hitter["player_id"],
                    "hitter_name": hitter["name"],
                    "team": hitter["team"],
                    "order": hitter["order"],
                    "pitcher_id": pitcher_id,
                    "pitcher_name": pitcher_name,
                    "opponent": opponent,
                    "home_flag": home_flag,
                    "context": context,
                })

    return output