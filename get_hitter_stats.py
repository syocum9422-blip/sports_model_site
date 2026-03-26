from datetime import date, timedelta
import pandas as pd
from pybaseball import (
    batting_stats,
    statcast_batter,
    statcast_batter_exitvelo_barrels
)

# Use last completed season until current season has real data
CURRENT_YEAR = 2025


def _safe_mean(series):
    if series is None or len(series) == 0:
        return 0
    try:
        val = series.mean()
        if pd.isna(val):
            return 0
        return float(val)
    except Exception:
        return 0


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


def get_hitter_stats(hitter_name: str, hitter_id: int):
    """
    Builds a hitter feature row using the last completed MLB season.
    Uses NAME matching for batting_stats/power tables.
    Uses hitter_id only for statcast_batter recent lookup.
    """

    today = date.today()
    hitter_name_clean = _normalize_name(hitter_name)

    # -------------------------
    # 1. SEASON STATS
    # -------------------------
    try:
        season = batting_stats(CURRENT_YEAR)
        if "Name" in season.columns:
            season["name_clean"] = season["Name"].astype(str).apply(_normalize_name)
            season_row_df = season[season["name_clean"] == hitter_name_clean]
        else:
            season_row_df = pd.DataFrame()
    except Exception:
        season_row_df = pd.DataFrame()

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

    # -------------------------
    # 2. EXPECTED STATS
    # -------------------------
    xBA = _safe_get(season_row, "xBA", 0)
    xSLG = _safe_get(season_row, "xSLG", 0)
    xwOBA = _safe_get(season_row, "xwOBA", 0)
    xOBP = _safe_get(season_row, "xOBP", 0)
    xISO = (xSLG - xBA) if xSLG and xBA else 0

    # -------------------------
    # 3. Plate discipline placeholders
    # -------------------------
    oswing = 0
    zswing = 0
    contact = 0
    whiff = 0
    chase = 0

    # -------------------------
    # 4. Splits fallback
    # -------------------------
    vs_lhp_avg = _safe_get(season_row, "AVG", 0)
    vs_rhp_avg = _safe_get(season_row, "AVG", 0)
    vs_lhp_ops = _safe_get(season_row, "OPS", 0)
    vs_rhp_ops = _safe_get(season_row, "OPS", 0)

    # -------------------------
    # 5. Power indicators
    # -------------------------
    try:
        power = statcast_batter_exitvelo_barrels(CURRENT_YEAR)
        power_row_df = pd.DataFrame()

        if "player_name" in power.columns:
            power["name_clean"] = power["player_name"].astype(str).apply(_normalize_name)
            power_row_df = power[power["name_clean"] == hitter_name_clean]
        elif "last_name, first_name" in power.columns:
            def convert_name(n):
                parts = str(n).split(",")
                if len(parts) == 2:
                    return _normalize_name(parts[1] + " " + parts[0])
                return _normalize_name(str(n))

            power["name_clean"] = power["last_name, first_name"].apply(convert_name)
            power_row_df = power[power["name_clean"] == hitter_name_clean]

    except Exception:
        power_row_df = pd.DataFrame()

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

    # -------------------------
    # 6. Recent Statcast
    # Use a fixed recent window from last completed season
    # -------------------------
    try:
        recent = statcast_batter("2025-08-01", "2025-09-30", hitter_id)
    except Exception:
        recent = pd.DataFrame()

    if not recent.empty:
        est_ba = recent["estimated_ba_using_speedangle"] if "estimated_ba_using_speedangle" in recent.columns else pd.Series(dtype=float)
        est_slg = recent["estimated_slg_using_speedangle"] if "estimated_slg_using_speedangle" in recent.columns else pd.Series(dtype=float)

        last_30_avg = _safe_mean(est_ba)
        last_30_slg = _safe_mean(est_slg)
        last_30_ops = last_30_avg + last_30_slg
        last_30_obp = last_30_avg * 1.25

        last_7_ops = last_30_ops
        last_15_ops = last_30_ops
    else:
        last_30_avg = 0
        last_30_obp = 0
        last_30_slg = 0
        last_30_ops = 0
        last_7_ops = 0
        last_15_ops = 0

    return pd.DataFrame([{
        "hitter_name": hitter_name,
        "hitter_id": hitter_id,
        "season_avg": _safe_get(season_row, "AVG", 0),
        "season_obp": _safe_get(season_row, "OBP", 0),
        "season_slg": _safe_get(season_row, "SLG", 0),
        "season_ops": _safe_get(season_row, "OPS", 0),
        "xBA": xBA,
        "xSLG": xSLG,
        "xwOBA": xwOBA,
        "xISO": xISO,
        "xOBP": xOBP,
        "oswing_percent": oswing,
        "zswing_percent": zswing,
        "contact_percent": contact,
        "whiff_percent": whiff,
        "chase_percent": chase,
        "vs_lhp_avg": vs_lhp_avg,
        "vs_rhp_avg": vs_rhp_avg,
        "vs_lhp_ops": vs_lhp_ops,
        "vs_rhp_ops": vs_rhp_ops,
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