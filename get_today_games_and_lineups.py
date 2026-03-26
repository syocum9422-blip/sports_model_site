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


def get_projected_or_confirmed_hitters(game_pk):
    url = f"https://statsapi.mlb.com/api/v1.1/game/{game_pk}/feed/live"
    data = fetch_json(url)

    result = {"home": [], "away": []}

    for side in ["home", "away"]:
        team_name = data.get("gameData", {}).get("teams", {}).get(side, {}).get("name", "")
        players = data.get("liveData", {}).get("boxscore", {}).get("teams", {}).get(side, {}).get("players", {})

        confirmed = []
        projected = []

        for p in players.values():
            person = p.get("person", {})
            pid = person.get("id")
            pname = person.get("fullName")
            position_type = p.get("position", {}).get("type", "")

            if not pid or not pname:
                continue

            # confirmed lineup
            if p.get("battingOrder"):
                confirmed.append({
                    "player_id": pid,
                    "name": pname,
                    "team": team_name,
                    "order": p.get("battingOrder"),
                })
                continue

            # projected fallback: only non-pitchers
            if position_type != "Pitcher":
                projected.append({
                    "player_id": pid,
                    "name": pname,
                    "team": team_name,
                    "order": None,
                })

        if confirmed:
            confirmed = sorted(confirmed, key=lambda x: int(x["order"]))
            result[side] = confirmed
        else:
            result[side] = projected

    return result


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

        lineups = get_projected_or_confirmed_hitters(game_pk)

        for side, pitcher, home_flag in [
            ("away", home_pitcher, 0),
            ("home", away_pitcher, 1),
        ]:
            pitcher_id = pitcher["id"]
            pitcher_name = pitcher["fullName"]
            opponent = home_team["name"] if side == "away" else away_team["name"]

            for hitter in lineups.get(side, []):
                output.append({
                    "gamePk": game_pk,
                    "team": hitter["team"],
                    "hitter_name": hitter["name"],
                    "hitter_id": hitter["player_id"],
                    "pitcher_name": pitcher_name,
                    "pitcher_id": pitcher_id,
                    "opponent": opponent,
                    "home_flag": home_flag,
                    "order": hitter["order"],
                })

    print(f"Collected {len(output)} matchup rows for today.")
    return output


if __name__ == "__main__":
    rows = get_today_games_and_lineups()
    print(rows[:20])