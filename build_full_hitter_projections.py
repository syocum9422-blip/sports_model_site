from pathlib import Path
import pandas as pd

SOURCE_FILE = Path("data/mlb/hitter_predictions_today.csv")
OUTPUT_FILE = Path("data/mlb/full_hitter_projections.csv")

def main():
    if not SOURCE_FILE.exists():
        raise FileNotFoundError(f"Missing source file: {SOURCE_FILE}")

    df = pd.read_csv(SOURCE_FILE).copy()

    if "hit_prob" in df.columns:
        df["HIT_PROJECTION"] = (pd.to_numeric(df["hit_prob"], errors="coerce") / 100).round(2)

    keep_cols = []
    for col in [
        "hitter_name",
        "hitter_id",
        "pitcher_name",
        "pitcher_id",
        "HIT_PROJECTION",
        "hit_prob",
        "tb2_prob",
        "hr_prob",
        "rbi_prob",
    ]:
        if col in df.columns:
            keep_cols.append(col)

    out = df[keep_cols].copy()

    rename_map = {
        "hitter_name": "PLAYER_NAME",
        "hitter_id": "PLAYER_ID",
        "pitcher_name": "OPPOSING_PITCHER",
        "pitcher_id": "PITCHER_ID",
        "hit_prob": "HIT_PROB_PCT",
        "tb2_prob": "TB2_PROB_PCT",
        "hr_prob": "HR_PROB_PCT",
        "rbi_prob": "RBI_PROB_PCT",
    }
    out = out.rename(columns=rename_map)

    if "HIT_PROB_PCT" in out.columns:
        out["HIT_PROB_PCT"] = pd.to_numeric(out["HIT_PROB_PCT"], errors="coerce").round(1)
    if "TB2_PROB_PCT" in out.columns:
        out["TB2_PROB_PCT"] = pd.to_numeric(out["TB2_PROB_PCT"], errors="coerce").round(1)
    if "HR_PROB_PCT" in out.columns:
        out["HR_PROB_PCT"] = pd.to_numeric(out["HR_PROB_PCT"], errors="coerce").round(1)
    if "RBI_PROB_PCT" in out.columns:
        out["RBI_PROB_PCT"] = pd.to_numeric(out["RBI_PROB_PCT"], errors="coerce").round(1)

    sort_cols = [c for c in ["HIT_PROJECTION", "HIT_PROB_PCT"] if c in out.columns]
    if sort_cols:
        out = out.sort_values(by=sort_cols, ascending=False).reset_index(drop=True)

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUTPUT_FILE, index=False)

    print(f"Saved full hitter projections to: {OUTPUT_FILE}")
    print(out.head(20).to_string(index=False))

if __name__ == "__main__":
    main()