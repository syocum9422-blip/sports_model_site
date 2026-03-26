from pathlib import Path
import pandas as pd

PROJECTIONS_FILE = Path("data/mlb/pitcher_predictions_today.csv")
LINES_FILE = Path("data/mlb/lines_today.csv")
OUTPUT_FILE = Path("data/mlb/official_pitcher_plays.csv")
FULL_OUTPUT_FILE = Path("data/mlb/full_pitcher_projections.csv")

MIN_CONFIDENCE = 5
MAX_PLAYS = 15


def empty_pitcher_df():
    return pd.DataFrame(columns=[
        "PLAYER_NAME",
        "STAT",
        "LINE",
        "PROJECTION",
        "EDGE",
        "CONFIDENCE",
        "PICK",
        "OPPONENT",
    ])


def build_pitcher_plays():
    if not PROJECTIONS_FILE.exists():
        raise FileNotFoundError(f"Missing projections file: {PROJECTIONS_FILE}")
    if not LINES_FILE.exists():
        raise FileNotFoundError(f"Missing lines file: {LINES_FILE}")

    proj_df = pd.read_csv(PROJECTIONS_FILE)
    lines_df = pd.read_csv(LINES_FILE)

    lines_df = lines_df[
        (lines_df["STAT"] == "K") &
        (lines_df["PLAYER_TYPE"] == "PITCHER")
    ].copy()

    if lines_df.empty:
        OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
        FULL_OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

        empty_df = empty_pitcher_df()
        empty_df.to_csv(OUTPUT_FILE, index=False)
        empty_df.to_csv(FULL_OUTPUT_FILE, index=False)

        print("No pitcher strikeout lines found for this run.")
        return

    merged = lines_df.merge(
        proj_df,
        left_on="PLAYER_NAME",
        right_on="pitcher_name",
        how="inner"
    )

    full_rows = []
    play_rows = []

    for _, row in merged.iterrows():
        projection = round(float(row["predicted_strikeouts"]), 2)
        line = float(row["LINE"])
        edge = round(projection - line, 2)

        if edge > 0:
            pick = "OVER"
        elif edge < 0:
            pick = "UNDER"
        else:
            pick = "PUSH"

        confidence = round(abs(edge) * 10)

        out_row = {
            "PLAYER_NAME": row["PLAYER_NAME"],
            "STAT": "K",
            "LINE": line,
            "PROJECTION": projection,
            "EDGE": edge,
            "CONFIDENCE": confidence,
            "PICK": pick,
            "OPPONENT": row.get("opponent", ""),
        }

        full_rows.append(out_row)

        if confidence >= MIN_CONFIDENCE and pick != "PUSH":
            play_rows.append(out_row)

    full_df = pd.DataFrame(full_rows)
    plays_df = pd.DataFrame(play_rows)

    FULL_OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    if full_df.empty:
        full_df = empty_pitcher_df()
    else:
        full_df = full_df.sort_values(
            by=["CONFIDENCE", "EDGE"],
            ascending=[False, False]
        ).reset_index(drop=True)

    full_df.to_csv(FULL_OUTPUT_FILE, index=False)

    if plays_df.empty:
        plays_df = empty_pitcher_df()
    else:
        plays_df = plays_df.sort_values(
            by=["CONFIDENCE", "EDGE"],
            ascending=[False, False]
        ).head(MAX_PLAYS).reset_index(drop=True)

    plays_df.to_csv(OUTPUT_FILE, index=False)

    print(f"Saved full pitcher projections to: {FULL_OUTPUT_FILE}")
    print(f"Saved pitcher plays to: {OUTPUT_FILE}")

    if full_df.empty:
        print("No pitcher projections were created.")
    else:
        print(full_df.head(20).to_string(index=False))

    if plays_df.empty:
        print("No official pitcher plays were created for this run.")
    else:
        print("\nOfficial pitcher plays:")
        print(plays_df.to_string(index=False))


if __name__ == "__main__":
    build_pitcher_plays()