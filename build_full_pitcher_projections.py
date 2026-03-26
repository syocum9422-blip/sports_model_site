from pathlib import Path
import pandas as pd

SOURCE_FILE = Path("data/mlb/pitcher_predictions_today.csv")
OUTPUT_FILE = Path("data/mlb/full_pitcher_projections.csv")

def main():
    if not SOURCE_FILE.exists():
        raise FileNotFoundError(f"Missing source file: {SOURCE_FILE}")

    df = pd.read_csv(SOURCE_FILE).copy()

    keep_cols = []
    for col in [
        "pitcher_name",
        "pitcher_id",
        "opponent",
        "predicted_strikeouts",
        "season_k_pct",
        "k_pct_last_30d",
        "ip_last_3_starts_avg",
        "pitches_last_3_starts_avg",
        "days_rest",
    ]:
        if col in df.columns:
            keep_cols.append(col)

    out = df[keep_cols].copy()

    rename_map = {
        "pitcher_name": "PLAYER_NAME",
        "pitcher_id": "PLAYER_ID",
        "opponent": "OPPONENT",
        "predicted_strikeouts": "K_PROJECTION",
        "season_k_pct": "SEASON_K_PCT",
        "k_pct_last_30d": "LAST30_K_PCT",
        "ip_last_3_starts_avg": "IP_LAST3_AVG",
        "pitches_last_3_starts_avg": "PITCHES_LAST3_AVG",
        "days_rest": "DAYS_REST",
    }
    out = out.rename(columns=rename_map)

    for col in ["K_PROJECTION", "IP_LAST3_AVG", "PITCHES_LAST3_AVG"]:
        if col in out.columns:
            out[col] = pd.to_numeric(out[col], errors="coerce").round(2)

    for col in ["SEASON_K_PCT", "LAST30_K_PCT"]:
        if col in out.columns:
            out[col] = (pd.to_numeric(out[col], errors="coerce") * 100).round(1)

    if "K_PROJECTION" in out.columns:
        out = out.sort_values(by="K_PROJECTION", ascending=False).reset_index(drop=True)

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUTPUT_FILE, index=False)

    print(f"Saved full pitcher projections to: {OUTPUT_FILE}")
    print(out.head(20).to_string(index=False))

if __name__ == "__main__":
    main()