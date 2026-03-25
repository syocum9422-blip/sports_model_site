import re
from pathlib import Path

import pandas as pd

PROJECTIONS_FILE = Path("data/mlb/hitter_predictions_today.csv")
LINES_FILE = Path("data/mlb/lines_today.csv")
LINEUPS_FILE = Path("data/mlb/lineups_with_ids.csv")
OUTPUT_FILE = Path("data/mlb/official_plays.csv")

MIN_CONFIDENCE = 5
MAX_PLAYS = 15

def clean_name(name):
    name = str(name).lower().strip()
    name = re.sub(r"[^a-z0-9\s]", "", name)
    name = re.sub(r"\s+", " ", name)
    return name

def convert_hit_probability_to_projection(prob_value):
    return round(float(prob_value) / 100.0, 2)

def build_official_plays():
    if not PROJECTIONS_FILE.exists():
        raise FileNotFoundError(f"Missing projections file: {PROJECTIONS_FILE}")
    if not LINES_FILE.exists():
        raise FileNotFoundError(f"Missing lines file: {LINES_FILE}")
    if not LINEUPS_FILE.exists():
        raise FileNotFoundError(f"Missing lineup bridge file: {LINEUPS_FILE}")

    proj_df = pd.read_csv(PROJECTIONS_FILE)
    lines_df = pd.read_csv(LINES_FILE)
    lineup_df = pd.read_csv(LINEUPS_FILE)

    lines_df = lines_df[
        (lines_df["STAT"] == "HIT") &
        (lines_df["PLAYER_TYPE"] == "HITTER")
    ].copy()

    lines_df["PLAYER_KEY"] = lines_df["PLAYER_NAME"].apply(clean_name)
    lineup_df["PLAYER_KEY"] = lineup_df["hitter_name"].apply(clean_name)

    lineup_df = lineup_df.dropna(subset=["hitter_id"]).copy()
    lineup_df["hitter_id"] = pd.to_numeric(lineup_df["hitter_id"], errors="coerce")
    proj_df["hitter_id"] = pd.to_numeric(proj_df["hitter_id"], errors="coerce")

    bridged_df = lines_df.merge(
        lineup_df[["PLAYER_KEY", "team", "hitter_name", "hitter_id"]],
        on="PLAYER_KEY",
        how="inner"
    )

    merged = bridged_df.merge(
        proj_df,
        on="hitter_id",
        how="inner",
        suffixes=("", "_model")
    )

    plays = []

    for _, row in merged.iterrows():
        projection = convert_hit_probability_to_projection(row["hit_prob"])
        line = float(row["LINE"])

        if line > 3:
            continue

        edge = round(projection - line, 2)

        if edge > 0:
            pick = "OVER"
        elif edge < 0:
            pick = "UNDER"
        else:
            pick = "PUSH"

        confidence = round(abs(edge) * 100)

        plays.append({
            "PLAYER_NAME": row["PLAYER_NAME"],
            "TEAM": row["team"],
            "HITTER_ID": int(row["hitter_id"]),
            "STAT": "HIT",
            "LINE": line,
            "PROJECTION": projection,
            "EDGE": edge,
            "CONFIDENCE": confidence,
            "PICK": pick,
        })

    plays_df = pd.DataFrame(plays)

    if plays_df.empty:
        raise ValueError("No HIT plays were created.")

    plays_df = plays_df[
        (plays_df["CONFIDENCE"] >= MIN_CONFIDENCE) &
        (plays_df["PICK"] != "PUSH")
    ]

    plays_df = plays_df.sort_values(
        by=["CONFIDENCE", "EDGE"],
        ascending=[False, False]
    ).head(MAX_PLAYS).reset_index(drop=True)

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    plays_df.to_csv(OUTPUT_FILE, index=False)

    print(f"Saved official HIT plays to: {OUTPUT_FILE}")
    print(plays_df.to_string(index=False))

if __name__ == "__main__":
    build_official_plays()
