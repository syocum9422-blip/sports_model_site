from pathlib import Path
import joblib
import pandas as pd
from build_features_today import build_features_today

BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / "strikeout_model.pkl"
OUTPUT_DIR = BASE_DIR / "mlb" / "outputs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def load_model():
    return joblib.load(MODEL_PATH)


def predict_today():
    model = load_model()
    df = build_features_today()

    if df.empty:
        print("No pitchers found for today.")
        return df

    feature_cols = [
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
        "home_flag"
    ]

    for col in feature_cols:
        if col not in df.columns:
            df[col] = 0

    X = df[feature_cols].fillna(0)

    print("\n=== MODEL INPUT FEATURES ===\n")
    print(X)

    df["predicted_strikeouts"] = model.predict(X)
    df = df.sort_values("predicted_strikeouts", ascending=False)

    print("\n=== TODAY'S STRIKEOUT PREDICTIONS ===\n")
    print(df[["pitcher_name", "opponent", "predicted_strikeouts"]])

    out_path = OUTPUT_DIR / "pitcher_predictions_today.csv"
    df.to_csv(out_path, index=False)
    print(f"\nSaved: {out_path}")

    return df


if __name__ == "__main__":
    predict_today()