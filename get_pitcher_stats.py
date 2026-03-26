import pandas as pd

LAST_COMPLETED_YEAR = 2025

_PITCHING_CACHE = None


def _normalize_name(name: str) -> str:
    return " ".join(str(name).lower().strip().split())


def _safe_get(row, key, default=0):
    try:
        val = row.get(key, default)
        if pd.isna(val):
            return default
        return float(val)
    except Exception:
        return default


def _load_pitching_cache():
    global _PITCHING_CACHE
    if _PITCHING_CACHE is not None:
        return _PITCHING_CACHE

    try:
        from pybaseball import pitching_stats
        df = pitching_stats(LAST_COMPLETED_YEAR)
        if "Name" in df.columns:
            df["name_clean"] = df["Name"].apply(_normalize_name)
        else:
            df = pd.DataFrame()
    except Exception as e:
        print(f"Pitcher load error: {e}")
        df = pd.DataFrame()

    _PITCHING_CACHE = df
    return _PITCHING_CACHE


def get_pitcher_stats(pitcher_name, pitcher_id):
    df = _load_pitching_cache()

    if df.empty or "name_clean" not in df.columns:
        return {
            "season_k_pct": 0.23,
            "season_bb_pct": 0.08,
            "season_ip_per_start": 5.5,
            "k_pct_last_30d": 0.23,
            "swstr_pct_last_30d": 0.11,
            "csw_pct_last_30d": 0.16,
            "ip_last_3_starts_avg": 5.5,
            "pitches_last_3_starts_avg": 85,
            "days_rest": 5,
        }

    pitcher_name_clean = _normalize_name(pitcher_name)
    row_df = df[df["name_clean"] == pitcher_name_clean]

    if row_df.empty:
        print(f"No pitcher stats found for: {pitcher_name}")
        return {
            "season_k_pct": 0.23,
            "season_bb_pct": 0.08,
            "season_ip_per_start": 5.5,
            "k_pct_last_30d": 0.23,
            "swstr_pct_last_30d": 0.11,
            "csw_pct_last_30d": 0.16,
            "ip_last_3_starts_avg": 5.5,
            "pitches_last_3_starts_avg": 85,
            "days_rest": 5,
        }

    row = row_df.iloc[0]

    k_pct = _safe_get(row, "K%", 0.23)
    bb_pct = _safe_get(row, "BB%", 0.08)
    ip = _safe_get(row, "IP", 170)
    gs = _safe_get(row, "GS", 30)

    ip_per_start = ip / gs if gs > 0 else 5.5
    swstr = _safe_get(row, "SwStr%", 0.11)
    csw = swstr * 1.5 if swstr else 0.16

    return {
        "season_k_pct": k_pct,
        "season_bb_pct": bb_pct,
        "season_ip_per_start": ip_per_start,
        "k_pct_last_30d": k_pct,
        "swstr_pct_last_30d": swstr,
        "csw_pct_last_30d": csw,
        "ip_last_3_starts_avg": ip_per_start,
        "pitches_last_3_starts_avg": ip_per_start * 15,
        "days_rest": 5,
    }