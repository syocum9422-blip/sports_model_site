from pathlib import Path
import pandas as pd
from get_today_games_and_lineups import get_today_games_and_lineups

OUTPUT_FILE = Path("data/mlb/lineups_with_ids.csv")


def export_lineups():
    rows = get_today_games_and_lineups()

    needed = ["team", "hitter_name", "hitter_id"]

    if not rows:
        OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
        pd.DataFrame(columns=needed).to_csv(OUTPUT_FILE, index=False)
        print("No lineup rows returned for today. Saved empty lineup bridge file.")
        return

    df = pd.DataFrame(rows)

    for col in needed:
        if col not in df.columns:
            OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
            pd.DataFrame(columns=needed).to_csv(OUTPUT_FILE, index=False)
            print(f"Missing required lineup column: {col}. Saved empty lineup bridge file.")
            return

    bridge_df = df[needed].copy()
    bridge_df = bridge_df.drop_duplicates().sort_values(
        by=["team", "hitter_name"]
    ).reset_index(drop=True)

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    bridge_df.to_csv(OUTPUT_FILE, index=False)

    print(f"Saved {len(bridge_df)} rows to {OUTPUT_FILE}")
    print(bridge_df.head(20).to_string(index=False))


if __name__ == "__main__":
    export_lineups()