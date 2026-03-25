from pathlib import Path
from datetime import datetime
import pandas as pd

HITTERS_FILE = Path("/Users/steveyocum/Desktop/sports_model_site/data/mlb/official_plays.csv")
PITCHERS_FILE = Path("/Users/steveyocum/Desktop/sports_model_site/data/mlb/official_pitcher_plays.csv")
TRACKED_FILE = Path("/Users/steveyocum/Desktop/sports_model_site/data/mlb/tracked_plays.csv")

def load_csv_if_exists(path):
    if path.exists():
        return pd.read_csv(path)
    return pd.DataFrame()

def main():
    today = datetime.now().strftime("%Y-%m-%d")

    hitters_df = load_csv_if_exists(HITTERS_FILE)
    pitchers_df = load_csv_if_exists(PITCHERS_FILE)

    plays = []

    if not hitters_df.empty:
        hitters_df = hitters_df.copy()
        hitters_df["SPORT"] = "MLB"
        hitters_df["MARKET_TYPE"] = "HITTER"
        plays.append(hitters_df)

    if not pitchers_df.empty:
        pitchers_df = pitchers_df.copy()
        pitchers_df["SPORT"] = "MLB"
        pitchers_df["MARKET_TYPE"] = "PITCHER"
        plays.append(pitchers_df)

    if not plays:
        raise ValueError("No hitter or pitcher plays found to track.")

    combined_df = pd.concat(plays, ignore_index=True)

    combined_df["TRACK_DATE"] = today
    combined_df["RESULT"] = ""
    combined_df["ACTUAL"] = ""

    required_cols = [
        "TRACK_DATE",
        "SPORT",
        "MARKET_TYPE",
        "PLAYER_NAME",
        "STAT",
        "LINE",
        "PROJECTION",
        "EDGE",
        "CONFIDENCE",
        "PICK",
        "RESULT",
        "ACTUAL",
    ]

    if "TEAM" in combined_df.columns:
        required_cols.append("TEAM")

    if "OPPONENT" in combined_df.columns:
        required_cols.append("OPPONENT")

    combined_df = combined_df[[col for col in required_cols if col in combined_df.columns]].copy()

    existing_df = load_csv_if_exists(TRACKED_FILE)

    if not existing_df.empty:
        key_cols = ["TRACK_DATE", "PLAYER_NAME", "STAT", "LINE", "PICK"]
        existing_keys = set(existing_df[key_cols].astype(str).agg("|".join, axis=1))
        combined_df["TRACK_KEY"] = combined_df[key_cols].astype(str).agg("|".join, axis=1)
        combined_df = combined_df[~combined_df["TRACK_KEY"].isin(existing_keys)].copy()
        combined_df = combined_df.drop(columns=["TRACK_KEY"])

    if existing_df.empty:
        final_df = combined_df
    else:
        final_df = pd.concat([existing_df, combined_df], ignore_index=True)

    TRACKED_FILE.parent.mkdir(parents=True, exist_ok=True)
    final_df.to_csv(TRACKED_FILE, index=False)

    print(f"Saved tracked plays to: {TRACKED_FILE}")
    print(f"Added {len(combined_df)} new plays.")
    print(final_df.tail(20).to_string(index=False))

if __name__ == "__main__":
    main()
