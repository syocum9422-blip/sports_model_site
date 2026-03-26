import pandas as pd

from get_matchups import get_todays_matchups
from get_pitcher_stats import get_pitcher_stats
from get_hitter_stats import get_hitter_stats


def build_hitter_features_today():
    matchups = get_todays_matchups()

    if isinstance(matchups, list):
        matchups = pd.DataFrame(matchups)

    if matchups is None or matchups.empty:
        print("No hitter rows found for today.")
        return pd.DataFrame()

    print("\n=== HITTER MATCHUPS USED BY MODEL ===\n")
    cols_to_show = [c for c in ["hitter_name", "hitter_id", "pitcher_name", "pitcher_id"] if c in matchups.columns]
    if cols_to_show:
        print(matchups[cols_to_show].head(50).to_string(index=False))
    else:
        print(matchups.head(50).to_string(index=False))

    all_rows = []

    for _, row in matchups.iterrows():
        hitter_name = row["hitter_name"]
        hitter_id = row["hitter_id"]
        pitcher_name = row["pitcher_name"]
        pitcher_id = row["pitcher_id"]

        hitter_df = get_hitter_stats(hitter_name, hitter_id)
        if hitter_df.empty:
            continue

        hitter_stats = hitter_df.iloc[0].to_dict()

        pitcher_stats = get_pitcher_stats(pitcher_name, pitcher_id)
        if pitcher_stats is None:
            pitcher_stats = {}

        combined = {
            "hitter_name": hitter_name,
            "hitter_id": hitter_id,
            "pitcher_name": pitcher_name,
            "pitcher_id": pitcher_id,
            **hitter_stats,
            **pitcher_stats,
        }

        all_rows.append(combined)

    out = pd.DataFrame(all_rows)

    print(f"\nBuilt hitter feature rows: {len(out)}")
    return out


if __name__ == "__main__":
    df = build_hitter_features_today()
    print(df.head())