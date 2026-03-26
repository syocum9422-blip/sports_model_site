import pandas as pd
from pybaseball import pitching_stats

LAST_COMPLETED_YEAR = 2025


def _normalize_name(name: str) -> str:
    return " ".join(str(name).lower().strip().split())


def _safe_get(row, key, default=0):
    try:
        val = row.get(key, default)
        if pd.isna(val):
            return default
        return float(val)
    except:
        return default


def get_pitcher_stats(pitcher_name, pitcher_id):
    try:
        df = pitching_stats(LAST_COMPLETED_YEAR)

        if "Name" not in df.columns:
            return {}

        df["name_clean"] = df["Name"].apply(_normalize_name)
        pitcher_name_clean = _normalize_name(pitcher_name)

        row_df = df[df["name_clean"] == pitcher_name_clean]

        if row_df.empty:
            print(f"No pitcher stats found for: {pitcher_name}")
            return {}

        row = row_df.iloc[0]

    except Exception as e:
        print(f"Pitcher load error: {e}")
        return {}

    # pybaseball pitching_stats already returns decimal values for these
    k_pct = _safe_get(row, "K%", 0)
    bb_pct = _safe_get(row, "BB%", 0)
    ip = _safe_get(row, "IP", 0)
    gs = _safe_get(row, "GS", 1)

    ip_per_start = ip / gs if gs > 0 else 5.5

    swstr = _safe_get(row, "SwStr%", 0)
    csw = swstr * 1.5  # simple proxy

    return {
        "season_k_pct": k_pct,
        "season_bb_pct": bb_pct,
        "season_ip_per_start": ip_per_start,
        "k_pct_last_30d": k_pct,
        "swstr_pct_last_30d": swstr,
        "csw_pct_last_30d": csw,
        "ip_last_3_starts_avg": ip_per_start,
        "pitches_last_3_starts_avg": ip_per_start * 15,
        "days_rest": 5
    }