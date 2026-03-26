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
        f"?sportId=1&date={today}&hydrate=team,probablePitcher"
    )
    data = fetch_json(url)
    dates = data.get("dates", [])
    if not dates:
        return []
    return dates[0].get("games", [])


def get_confirmed_lineup(game_pk):
    url = f"https://statsapi.mlb.com/api/v1/game/{game_pk}/boxscore"
    data = fetch_json(url)

    lineups = {"home": [], "away": []}

    for side in ["home", "away"]:
        players = data.get("teams", {}).get(side, {}).get("players", {})

        confirmed = []
        for p in players.values():
            batting_order = p.get("battingOrder")
            if not batting_order:
                continue

            person = p.get("person", {})
            if not person.get("id") or not person.get("fullName"):
                continue

            confirmed.append({
                "player_id": person["id"],
                "name": person["fullName"],
                "order": batting_order,
                "team": data["teams"][side]["team"]["name"],
            })

        confirmed = sorted(confirmed, key=lambda x: int(x["order"]))
        lineups[side] = confirmed

    return lineups


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

        lineups = get_confirmed_lineup(game_pk)

        # only use confirmed lineup hitters
        for side, pitcher, home_flag in [
            ("away", home_pitcher, 0),
            ("home", away_pitcher, 1),
        ]:
            confirmed_hitters = lineups.get(side, [])
            if not confirmed_hitters:
                continue

            pitcher_id = pitcher["id"]
            pitcher_name = pitcher["fullName"]
            opponent = home_team["name"] if side == "away" else away_team["name"]

            for hitter in confirmed_hitters:
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
                })

    return output


if __name__ == "__main__":
    rows = get_today_games_and_lineups()
    print(rows[:20])