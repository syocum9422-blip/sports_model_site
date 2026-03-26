from pathlib import Path
import pandas as pd
from get_today_games_and_lineups import get_today_games_and_lineups

OUTPUT_FILE = Path("data/mlb/lineups_with_ids.csv")


def export_lineups():
    rows = get_today_games_and_lineups()

    if not rows:
        raise ValueError("No lineup rows returned for today.")

    df = pd.DataFrame(rows)

    needed = ["team", "hitter_name", "hitter_id"]
    for col in needed:
        if col not in df.columns:
            raise ValueError(f"Missing required lineup column: {col}")

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