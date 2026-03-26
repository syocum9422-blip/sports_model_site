import requests
from datetime import datetime

MLB_SCHEDULE_URL = "https://statsapi.mlb.com/api/v1/schedule?sportId=1"


def get_today_games():
    today = datetime.today().strftime("%Y-%m-%d")
    url = f"{MLB_SCHEDULE_URL}&date={today}"

    r = requests.get(url)
    data = r.json()

    games = []

    for date in data.get("dates", []):
        for game in date.get("games", []):
            games.append({
                "home_team": game["teams"]["home"]["team"]["name"],
                "away_team": game["teams"]["away"]["team"]["name"],
                "gamePk": game["gamePk"]
            })

    return games


def get_lineup_or_projection(gamePk):
    url = f"https://statsapi.mlb.com/api/v1.1/game/{gamePk}/feed/live"
    r = requests.get(url)
    data = r.json()

    lineups = []

    for side in ["home", "away"]:
        team = data.get("gameData", {}).get("teams", {}).get(side, {}).get("name", "")

        # 1️⃣ TRY CONFIRMED LINEUP
        players = data.get("liveData", {}).get("boxscore", {}).get("teams", {}).get(side, {}).get("players", {})

        confirmed = []
        for p in players.values():
            if p.get("battingOrder"):
                confirmed.append({
                    "team": team,
                    "hitter_name": p["person"]["fullName"],
                    "hitter_id": p["person"]["id"]
                })

        if confirmed:
            lineups.extend(confirmed)
            continue

        # 2️⃣ FALLBACK → PROBABLE LINEUP (projected-ish)
        probable = data.get("gameData", {}).get("probablePitchers", {})
        roster = data.get("gameData", {}).get("players", {})

        for p in roster.values():
            if p.get("primaryPosition", {}).get("type") == "infielder" or \
               p.get("primaryPosition", {}).get("type") == "outfielder":
                lineups.append({
                    "team": team,
                    "hitter_name": p.get("fullName"),
                    "hitter_id": p.get("id")
                })

    return lineups


def get_today_games_and_lineups():
    games = get_today_games()

    all_rows = []

    for g in games:
        lineup = get_lineup_or_projection(g["gamePk"])
        all_rows.extend(lineup)

    print(f"Collected {len(all_rows)} lineup rows (confirmed + projected fallback)")
    return all_rows


if __name__ == "__main__":
    rows = get_today_games_and_lineups()
    print(rows[:10])