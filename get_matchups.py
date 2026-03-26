import pandas as pd
from get_today_games_and_lineups import get_today_games_and_lineups


def get_todays_matchups(test_date=None):
    rows = get_today_games_and_lineups()

    required_cols = [
        "hitter_name",
        "hitter_id",
        "pitcher_name",
        "pitcher_id",
        "opponent",
        "home_flag",
    ]

    if not rows:
        print("No live matchup rows returned for today.")
        return pd.DataFrame(columns=required_cols)

    df = pd.DataFrame(rows)

    for col in required_cols:
        if col not in df.columns:
            print(f"Missing required matchup column: {col}")
            return pd.DataFrame(columns=required_cols)

    df = df[required_cols].drop_duplicates().reset_index(drop=True)

    print("\n=== LIVE MATCHUPS ===\n")
    print(df.head(20).to_string(index=False))

    return df


if __name__ == "__main__":
    df = get_todays_matchups()
    print(df.head())
