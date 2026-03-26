import pandas as pd
from pybaseball import batting_stats, statcast_batter_exitvelo_barrels

CURRENT_YEAR = 2025

_SEASON_CACHE = None
_POWER_CACHE = None


def _safe_get(row, key, default=0):
    try:
        val = row.get(key, default)
        if pd.isna(val):
            return default
        return val
    except Exception:
        return default


def _normalize_name(name: str) -> str:
    if not isinstance(name, str):
        return ""
    return " ".join(name.lower().strip().split())


def _load_season_stats():
    global _SEASON_CACHE
    if _SEASON_CACHE is None:
        try:
            df = batting_stats(CURRENT_YEAR)
            if "Name" in df.columns:
                df["name_clean"] = df["Name"].astype(str).apply(_normalize_name)
            else:
                df = pd.DataFrame()
        except Exception:
            df = pd.DataFrame()
        _SEASON_CACHE = df
    return _SEASON_CACHE


def _load_power_stats():
    global _POWER_CACHE
    if _POWER_CACHE is None:
        try:
            power = statcast_batter_exitvelo_barrels(CURRENT_YEAR)
            if "player_name" in power.columns:
                power["name_clean"] = power["player_name"].astype(str).apply(_normalize_name)
            elif "last_name, first_name" in power.columns:
                def convert_name(n):
                    parts = str(n).split(",")
                    if len(parts) == 2:
                        return _normalize_name(parts[1] + " " + parts[0])
                    return _normalize_name(str(n))
                power["name_clean"] = power["last_name, first_name"].apply(convert_name)
            else:
                power = pd.DataFrame()
        except Exception:
            power = pd.DataFrame()
        _POWER_CACHE = power
    return _POWER_CACHE


def get_hitter_stats(hitter_name: str, hitter_id: int):
    hitter_name_clean = _normalize_name(hitter_name)

    season = _load_season_stats()
    power = _load_power_stats()

    season_row_df = pd.DataFrame()
    if not season.empty and "name_clean" in season.columns:
        season_row_df = season[season["name_clean"] == hitter_name_clean]

    if season_row_df.empty:
        print(f"No season stats found for hitter: {hitter_name}")
        return pd.DataFrame([{
            "hitter_name": hitter_name,
            "hitter_id": hitter_id,
            "season_avg": 0,
            "season_obp": 0,
            "season_slg": 0,
            "season_ops": 0,
            "xBA": 0,
            "xSLG": 0,
            "xwOBA": 0,
            "xISO": 0,
            "xOBP": 0,
            "oswing_percent": 0,
            "zswing_percent": 0,
            "contact_percent": 0,
            "whiff_percent": 0,
            "chase_percent": 0,
            "vs_lhp_avg": 0,
            "vs_rhp_avg": 0,
            "vs_lhp_ops": 0,
            "vs_rhp_ops": 0,
            "barrel_rate": 0,
            "hard_hit_rate": 0,
            "avg_ev": 0,
            "max_ev": 0,
            "sweet_spot_rate": 0,
            "last_30_avg": 0,
            "last_30_obp": 0,
            "last_30_slg": 0,
            "last_30_ops": 0,
            "last_7_ops": 0,
            "last_15_ops": 0,
        }])

    season_row = season_row_df.iloc[0]

    xBA = _safe_get(season_row, "xBA", 0)
    xSLG = _safe_get(season_row, "xSLG", 0)
    xwOBA = _safe_get(season_row, "xwOBA", 0)
    xOBP = _safe_get(season_row, "xOBP", 0)
    xISO = (xSLG - xBA) if xSLG and xBA else 0

    power_row_df = pd.DataFrame()
    if not power.empty and "name_clean" in power.columns:
        power_row_df = power[power["name_clean"] == hitter_name_clean]

    if not power_row_df.empty:
        power_row = power_row_df.iloc[0]
        barrel_rate = _safe_get(power_row, "brl_percent", 0)
        hard_hit_rate = _safe_get(power_row, "hard_hit_percent", 0)
        avg_ev = _safe_get(power_row, "avg_hit_speed", 0)
        max_ev = _safe_get(power_row, "max_hit_speed", 0)
        sweet_spot_rate = _safe_get(power_row, "sweet_spot_percent", 0)
    else:
        barrel_rate = 0
        hard_hit_rate = 0
        avg_ev = 0
        max_ev = 0
        sweet_spot_rate = 0

    season_avg = _safe_get(season_row, "AVG", 0)
    season_obp = _safe_get(season_row, "OBP", 0)
    season_slg = _safe_get(season_row, "SLG", 0)
    season_ops = _safe_get(season_row, "OPS", 0)

    # Fast fallback recent form: use season stats instead of per-player Statcast pulls
    last_30_avg = season_avg
    last_30_obp = season_obp
    last_30_slg = season_slg
    last_30_ops = season_ops
    last_7_ops = season_ops
    last_15_ops = season_ops

    return pd.DataFrame([{
        "hitter_name": hitter_name,
        "hitter_id": hitter_id,
        "season_avg": season_avg,
        "season_obp": season_obp,
        "season_slg": season_slg,
        "season_ops": season_ops,
        "xBA": xBA,
        "xSLG": xSLG,
        "xwOBA": xwOBA,
        "xISO": xISO,
        "xOBP": xOBP,
        "oswing_percent": 0,
        "zswing_percent": 0,
        "contact_percent": 0,
        "whiff_percent": 0,
        "chase_percent": 0,
        "vs_lhp_avg": season_avg,
        "vs_rhp_avg": season_avg,
        "vs_lhp_ops": season_ops,
        "vs_rhp_ops": season_ops,
        "barrel_rate": barrel_rate,
        "hard_hit_rate": hard_hit_rate,
        "avg_ev": avg_ev,
        "max_ev": max_ev,
        "sweet_spot_rate": sweet_spot_rate,
        "last_30_avg": last_30_avg,
        "last_30_obp": last_30_obp,
        "last_30_slg": last_30_slg,
        "last_30_ops": last_30_ops,
        "last_7_ops": last_7_ops,
        "last_15_ops": last_15_ops,
    }])