import pandas as pd
from get_matchups import get_todays_matchups
from get_pitcher_stats import get_pitcher_stats
from get_opponent_stats import get_opponent_stats


def get_park_factor(team_name):
    park_factors = {
        "COL": 1.15,
        "BOS": 1.05,
        "LAD": 1.02,
        "NYY": 1.03
    }
    return park_factors.get(str(team_name).upper(), 1.00)


def build_features_today():
    matchups = get_todays_matchups()

    if isinstance(matchups, list):
        matchups = pd.DataFrame(matchups)

    if matchups is None or len(matchups) == 0:
        print("No matchups found for today.")
        return pd.DataFrame()

    required_cols = ["pitcher_name", "pitcher_id", "opponent", "home_flag"]
    for col in required_cols:
        if col not in matchups.columns:
            print(f"Missing required column in matchups: {col}")
            return pd.DataFrame()

    pitcher_matchups = (
        matchups[["pitcher_name", "pitcher_id", "opponent", "home_flag"]]
        .drop_duplicates()
        .reset_index(drop=True)
    )

    rows = []

    for _, m in pitcher_matchups.iterrows():
        pitcher_name = m["pitcher_name"]
        pitcher_id = m["pitcher_id"]
        opponent = m["opponent"]
        home_flag = m["home_flag"]

        print(f"Processing {pitcher_name} vs {opponent}...")

        pstats = get_pitcher_stats(pitcher_name, pitcher_id)
        if not pstats:
            print(f"Skipping {pitcher_name} (missing stats)")
            continue

        ostats = get_opponent_stats(opponent, "R")
        if ostats is None:
            ostats = {}

        row = {
            "pitcher_name": pitcher_name,
            "pitcher_id": pitcher_id,
            "opponent": opponent,
            "home_flag": home_flag,
            "park_k_factor": get_park_factor(opponent),
            **pstats,
            **ostats
        }

        rows.append(row)

    df = pd.DataFrame(rows)

    if not df.empty:
        print("\n=== PITCHER FEATURE TABLE ===\n")
        cols_to_show = [
            c for c in [
                "pitcher_name",
                "opponent",
                "season_k_pct",
                "season_bb_pct",
                "season_ip_per_start",
                "k_pct_last_30d",
                "swstr_pct_last_30d",
                "csw_pct_last_30d",
                "ip_last_3_starts_avg",
                "pitches_last_3_starts_avg",
                "opp_vs_hand_k_pct",
                "opp_vs_hand_contact_pct",
                "opp_vs_hand_swstr_pct",
                "park_k_factor",
                "days_rest",
                "home_flag",
            ] if c in df.columns
        ]
        print(df[cols_to_show])

    return df


if __name__ == "__main__":
    df = build_features_today()
    print(df.head())