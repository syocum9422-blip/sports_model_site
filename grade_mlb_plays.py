from pathlib import Path
import math
import requests
import pandas as pd

TRACKED_FILE = Path("/Users/steveyocum/Desktop/sports_model_site/data/mlb/tracked_plays.csv")

SCHEDULE_URL = "https://statsapi.mlb.com/api/v1/schedule"
BOXSCORE_URL = "https://statsapi.mlb.com/api/v1/game/{gamePk}/boxscore"

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json",
}

FINAL_STATES = {
    "Final",
    "Completed Early",
    "Game Over",
}

def fetch_json(url, params=None):
    response = requests.get(url, headers=HEADERS, params=params, timeout=30)
    response.raise_for_status()
    return response.json()

def normalize_name(name):
    return " ".join(str(name).strip().lower().split())

def is_final_game(game):
    status = game.get("status", {})
    detailed = status.get("detailedState", "")
    abstract = status.get("abstractGameState", "")
    coded = status.get("codedGameState", "")

    if detailed in FINAL_STATES:
        return True
    if abstract.lower() == "final":
        return True
    if coded == "F":
        return True

    return False

def get_final_game_ids_for_date(track_date):
    data = fetch_json(
        SCHEDULE_URL,
        params={
            "sportId": 1,
            "date": track_date,
        },
    )

    game_ids = []
    for date_block in data.get("dates", []):
        for game in date_block.get("games", []):
            if is_final_game(game):
                game_ids.append(game["gamePk"])

    return game_ids

def get_player_stat_maps(game_pk):
    data = fetch_json(BOXSCORE_URL.format(gamePk=game_pk))

    hitter_hits = {}
    pitcher_ks = {}

    for side in ["home", "away"]:
        team = data.get("teams", {}).get(side, {})
        players = team.get("players", {})

        for _, player in players.items():
            person = player.get("person", {})
            full_name = person.get("fullName", "")
            key = normalize_name(full_name)

            batting = player.get("stats", {}).get("batting", {})
            pitching = player.get("stats", {}).get("pitching", {})

            if key:
                hits = batting.get("hits")
                if hits is not None:
                    hitter_hits[key] = hits

                strikeouts = pitching.get("strikeOuts")
                if strikeouts is not None:
                    pitcher_ks[key] = strikeouts

    return hitter_hits, pitcher_ks

def grade_pick(pick, actual, line):
    if actual > line:
        outcome = "OVER"
    elif actual < line:
        outcome = "UNDER"
    else:
        outcome = "PUSH"

    if outcome == "PUSH":
        return "PUSH"

    return "WIN" if pick == outcome else "LOSS"

def main():
    if not TRACKED_FILE.exists():
        raise FileNotFoundError(f"Missing tracked plays file: {TRACKED_FILE}")

    df = pd.read_csv(TRACKED_FILE)

    if df.empty:
        print("Tracked plays file is empty.")
        return

    if "RESULT" not in df.columns:
        df["RESULT"] = ""
    if "ACTUAL" not in df.columns:
        df["ACTUAL"] = ""

    # Only work on ungraded rows
    ungraded_mask = df["RESULT"].fillna("").astype(str).str.strip() == ""
    ungraded_df = df[ungraded_mask].copy()

    if ungraded_df.empty:
        print("No ungraded plays found.")
        return

    updated_count = 0

    for track_date in sorted(ungraded_df["TRACK_DATE"].dropna().astype(str).unique()):
        game_ids = get_final_game_ids_for_date(track_date)

        if not game_ids:
            print(f"No final MLB games found yet for {track_date}.")
            continue

        all_hitter_hits = {}
        all_pitcher_ks = {}

        for game_pk in game_ids:
            hitter_hits, pitcher_ks = get_player_stat_maps(game_pk)
            all_hitter_hits.update(hitter_hits)
            all_pitcher_ks.update(pitcher_ks)

        date_mask = (df["TRACK_DATE"].astype(str) == track_date) & (
            df["RESULT"].fillna("").astype(str).str.strip() == ""
        )

        for idx in df[date_mask].index:
            player_name = df.at[idx, "PLAYER_NAME"]
            stat = str(df.at[idx, "STAT"]).strip().upper()
            pick = str(df.at[idx, "PICK"]).strip().upper()
            line = float(df.at[idx, "LINE"])

            player_key = normalize_name(player_name)

            actual = None

            if stat == "HIT":
                actual = all_hitter_hits.get(player_key)
            elif stat == "K":
                actual = all_pitcher_ks.get(player_key)

            if actual is None:
                continue

            result = grade_pick(pick, float(actual), line)

            df.at[idx, "ACTUAL"] = actual
            df.at[idx, "RESULT"] = result
            updated_count += 1

    df.to_csv(TRACKED_FILE, index=False)

    print(f"Updated {updated_count} plays in: {TRACKED_FILE}")

    if updated_count:
        graded_preview = df[df["RESULT"].fillna("").astype(str).str.strip() != ""].tail(20)
        print(graded_preview.to_string(index=False))
    else:
        print("No plays were graded yet. Games may not be final or player stats were not found.")

if __name__ == "__main__":
    main()
