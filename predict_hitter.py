from pathlib import Path
import joblib
import pandas as pd

from build_hitter_features_today import build_hitter_features_today

BASE_DIR = Path(__file__).resolve().parent
MODEL_DIR = BASE_DIR / "mlb" / "models"
OUTPUT_DIR = BASE_DIR / "mlb" / "outputs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

FALLBACK_FEATURE_COLS = [
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


def ensure_features(df, cols):
    for col in cols:
        if col not in df.columns:
            df[col] = 0
    return df


def load_model(path):
    if path.exists():
        return joblib.load(path)
    return None


def get_model_features(model):
    if model is not None and hasattr(model, "feature_names_in_"):
        return list(model.feature_names_in_)
    return FALLBACK_FEATURE_COLS


def predict_one(model, df):
    if model is None:
        return pd.Series([0.0] * len(df), index=df.index)

    feature_cols = get_model_features(model)
    df =