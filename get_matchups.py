import pandas as pd
from get_today_games_and_lineups import get_today_games_and_lineups

REQUIRED_COLS = [
    "hitter_name",
    "hitter_id",
    "pitcher_name",
    "pitcher_id",
    "opponent",
    "home_flag",
]

def get_todays_matchups(test_date=None):
    try:
        rows = get_today_games_and_lineups()
    except Exception as e:
        print(f"Live matchup load failed: {e}")
        return pd.DataFrame(columns=REQUIRED_COLS)

    if not rows:
        print("No live matchup rows returned for today.")
        return pd.DataFrame(columns=REQUIRED_COLS)

    df = pd.DataFrame(rows)

    print("\n=== RAW MATCHUP COLUMNS ===\n")
    print(list(df.columns))

    for col in REQUIRED_COLS:
        if col not in df.columns:
            print(f"Missing required matchup column: {col}")
            return pd.DataFrame(columns=REQUIRED_COLS)

    df = df[REQUIRED_COLS].drop_duplicates().reset_index(drop=True)

    print("\n=== LIVE MATCHUPS ===\n")
    print(df.head(50).to_string(index=False))
    print(f"\nTotal matchup rows: {len(df)}")

    return df

if __name__ == "__main__":
    df = get_todays_matchups()
    print(df.head())