import re
from pathlib import Path

import pandas as pd
import requests

OUTPUT_FILE = Path("/Users/steveyocum/Desktop/sports_model_site/data/mlb/lines_today.csv")
DEBUG_FILE = Path("/Users/steveyocum/Desktop/sports_model_site/data/mlb/lines_debug.csv")

API_URL = "https://api.underdogfantasy.com/beta/v5/over_under_lines"

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json",
}

def normalize_text(value):
    value = str(value).strip().lower()
    value = re.sub(r"[^a-z0-9_\s\+]", "", value)
    value = re.sub(r"\s+", " ", value)
    return value

def map_stat(raw_stat):
    raw = normalize_text(raw_stat)

    if raw in {"hits", "season_batter_hits"}:
        return "HIT"

    if raw in {"strikeouts", "pitcher_strikeouts", "pitching_strikeouts"}:
        return "K"

    return None

def main():
    response = requests.get(API_URL, headers=HEADERS, timeout=30)
    response.raise_for_status()
    data = response.json()

    players_df = pd.DataFrame(data.get("players", []))
    appearances_df = pd.DataFrame(data.get("appearances", []))
    lines_df = pd.DataFrame(data.get("over_under_lines", []))

    if players_df.empty or appearances_df.empty or lines_df.empty:
        raise ValueError("Missing players, appearances, or over_under_lines in line source response.")

    players_df = players_df.rename(columns={"id": "player_uuid"})
    appearances_df = appearances_df.rename(columns={"id": "appearance_id"})
    appearances_df = appearances_df.rename(columns={"player_id": "player_uuid"})

    players_keep = players_df[
        [
            "player_uuid",
            "first_name",
            "last_name",
            "team_id",
            "position_name",
            "position_display_name",
        ]
    ].copy()

    appearances_keep = appearances_df[
        [
            "appearance_id",
            "player_uuid",
            "team_id",
        ]
    ].copy()

    merged_players = appearances_keep.merge(
        players_keep,
        on=["player_uuid", "team_id"],
        how="left",
    )

    merged_players["PLAYER_NAME"] = (
        merged_players["first_name"].fillna("").astype(str).str.strip()
        + " "
        + merged_players["last_name"].fillna("").astype(str).str.strip()
    ).str.strip()

    rows = []
    debug_rows = []

    for _, row in lines_df.iterrows():
        over_under = row.get("over_under", {})
        if not isinstance(over_under, dict):
            continue

        appearance_stat = over_under.get("appearance_stat", {})
        if not isinstance(appearance_stat, dict):
            continue

        appearance_id = appearance_stat.get("appearance_id")
        raw_stat = appearance_stat.get("stat")

        if appearance_id is None or raw_stat is None:
            continue

        mapped_stat = map_stat(raw_stat)

        line_value = row.get("stat_value")
        try:
            line_value = float(line_value) if line_value is not None else None
        except Exception:
            line_value = None

        player_match = merged_players[merged_players["appearance_id"] == appearance_id]
        if player_match.empty:
            continue

        player = player_match.iloc[0]
        player_name = player["PLAYER_NAME"]
        team_id = player["team_id"]
        position_name = str(player.get("position_name", "") or "")
        position_display_name = str(player.get("position_display_name", "") or "")

        if line_value is None and mapped_stat == "HIT":
            line_value = 0.5

        debug_rows.append(
            {
                "PLAYER_NAME": player_name,
                "TEAM_ID": team_id,
                "POSITION_NAME": position_name,
                "POSITION_DISPLAY_NAME": position_display_name,
                "RAW_STAT": raw_stat,
                "MAPPED_STAT": mapped_stat,
                "LINE": line_value,
            }
        )

        if mapped_stat is None or line_value is None:
            continue

        if mapped_stat == "HIT":
            rows.append(
                {
                    "PLAYER_NAME": player_name,
                    "TEAM_ID": team_id,
                    "STAT": "HIT",
                    "LINE": float(line_value),
                    "PLAYER_TYPE": "HITTER",
                }
            )
        elif mapped_stat == "K":
            rows.append(
                {
                    "PLAYER_NAME": player_name,
                    "TEAM_ID": team_id,
                    "STAT": "K",
                    "LINE": float(line_value),
                    "PLAYER_TYPE": "PITCHER",
                }
            )

    final_df = pd.DataFrame(rows).drop_duplicates().reset_index(drop=True)
    debug_df = pd.DataFrame(debug_rows).drop_duplicates().reset_index(drop=True)

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    final_df.to_csv(OUTPUT_FILE, index=False)
    debug_df.to_csv(DEBUG_FILE, index=False)

    print(f"Saved lines to: {OUTPUT_FILE}")
    print(final_df.head(50).to_string(index=False))
    print(f"\nSaved debug file to: {DEBUG_FILE}")

if __name__ == "__main__":
    main()
