from pathlib import Path
import joblib
import pandas as pd

from build_hitter_features_today import build_hitter_features_today

BASE_DIR = Path(__file__).resolve().parent
MODEL_DIR = BASE_DIR / "mlb" / "models"
OUTPUT_DIR = BASE_DIR / "mlb" / "outputs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

FEATURE_COLS = [
    "season_avg",
    "season_obp",
    "season_slg",
    "season_ops",
    "xBA",
    "xSLG",
    "xwOBA",
    "xISO",
    "xOBP",
    "vs_lhp_avg",
    "vs_rhp_avg",
    "vs_lhp_ops",
    "vs_rhp_ops",
    "barrel_rate",
    "hard_hit_rate",
    "avg_ev",
    "max_ev",
    "sweet_spot_rate",
    "last_30_avg",
    "last_30_obp",
    "last_30_slg",
    "last_30_ops",
    "last_7_ops",
    "last_15_ops",
    "pitcher_k_pct",
    "pitcher_bb_pct",
    "pitcher_swstr",
    "pitcher_csw",
]


def ensure_features(df):
    for col in FEATURE_COLS:
        if col not in df.columns:
            df[col] = 0
    return df


def load_model(path):
    if path.exists():
        return joblib.load(path)
    return None


def predict_hitter():
    df = build_hitter_features_today()

    if df.empty:
        print("No hitter rows found for today.")
        return df

    # map live pitcher columns into training names
    if "season_k_pct" in df.columns:
        df["pitcher_k_pct"] = df["season_k_pct"]
    if "season_bb_pct" in df.columns:
        df["pitcher_bb_pct"] = df["season_bb_pct"]
    if "swstr_pct_last_30d" in df.columns:
        df["pitcher_swstr"] = df["swstr_pct_last_30d"]
    if "csw_pct_last_30d" in df.columns:
        df["pitcher_csw"] = df["csw_pct_last_30d"]

    df = ensure_features(df)
    X = df[FEATURE_COLS].apply(pd.to_numeric, errors="coerce").fillna(0)

    hit_model = load_model(MODEL_DIR / "hit_model.pkl")
    tb2_model = load_model(MODEL_DIR / "tb2_model.pkl")
    rbi_model = load_model(MODEL_DIR / "rbi_model.pkl")
    hr_model = load_model(MODEL_DIR / "hr_model.pkl")

    df["hit_prob"] = (hit_model.predict_proba(X)[:, 1] * 100).round(1) if hit_model is not None else 0.0
    df["tb2_prob"] = (tb2_model.predict_proba(X)[:, 1] * 100).round(1) if tb2_model is not None else 0.0
    df["rbi_prob"] = (rbi_model.predict_proba(X)[:, 1] * 100).round(1) if rbi_model is not None else 0.0
    df["hr_prob"] = (hr_model.predict_proba(X)[:, 1] * 100).round(1) if hr_model is not None else 0.0

    df = df.sort_values(["hr_prob", "tb2_prob", "hit_prob"], ascending=False)

    print("\n=== TODAY'S HITTER PROBABILITIES ===\n")
    print(df[[
        "hitter_name",
        "pitcher_name",
        "season_avg",
        "season_ops",
        "avg_ev",
        "last_30_ops",
        "pitcher_k_pct",
        "pitcher_swstr",
        "hit_prob",
        "tb2_prob",
        "rbi_prob",
        "hr_prob"
    ]])

    out_path = OUTPUT_DIR / "hitter_predictions_today.csv"
    df.to_csv(out_path, index=False)
    print(f"\nSaved: {out_path}")

    return df


if __name__ == "__main__":
    predict_hitter()