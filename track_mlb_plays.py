from pathlib import Path
import pandas as pd

HITTER_FILE = Path("data/mlb/official_plays.csv")
PITCHER_FILE = Path("data/mlb/official_pitcher_plays.csv")
TRACKED_FILE = Path("data/mlb/tracked_plays.csv")


def load_csv(path):
    if path.exists():
        try:
            return pd.read_csv(path)
        except Exception:
            return pd.DataFrame()
    return pd.DataFrame()


def main():
    hitter_df = load_csv(HITTER_FILE)
    pitcher_df = load_csv(PITCHER_FILE)

    frames = []

    if not hitter_df.empty:
        hitter_df = hitter_df.copy()
        hitter_df["SPORT"] = "MLB"
        hitter_df["MARKET_TYPE"] = "HITTER"
        frames.append(hitter_df)

    if not pitcher_df.empty:
        pitcher_df = pitcher_df.copy()
        pitcher_df["SPORT"] = "MLB"
        pitcher_df["MARKET_TYPE"] = "PITCHER"
        frames.append(pitcher_df)

    TRACKED_FILE.parent.mkdir(parents=True, exist_ok=True)

    if not frames:
        empty_cols = [
            "DATE",
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
            "TEAM",
            "OPPONENT",
        ]
        pd.DataFrame(columns=empty_cols).to_csv(TRACKED_FILE, index=False)
        print("No hitter or pitcher plays found to track. Saved empty tracked_plays.csv")
        return

    combined = pd.concat(frames, ignore_index=True)

    if "RESULT" not in combined.columns:
        combined["RESULT"] = ""
    if "ACTUAL" not in combined.columns:
        combined["ACTUAL"] = ""

    if "DATE" not in combined.columns:
        combined["DATE"] = pd.Timestamp.today().strftime("%Y-%m-%d")

    combined.to_csv(TRACKED_FILE, index=False)
    print(f"Saved tracked plays to: {TRACKED_FILE}")
    print(combined.head(20).to_string(index=False))


if __name__ == "__main__":
    main()