import pandas as pd

# -----------------------------
# Helper: Get Fangraphs CSV
# -----------------------------
import ssl

def get_fangraphs_csv(url):
    try:
        ssl._create_default_https_context = ssl._create_unverified_context
        df = pd.read_csv(url)
        return df
    except:
        return pd.DataFrame()
# -----------------------------
# Opponent Stats vs Handedness
# -----------------------------
def get_opponent_stats(team_name, pitcher_throws):
    # pitcher_throws = "R" or "L"
    hand = "vsR" if pitcher_throws == "R" else "vsL"

    # Fangraphs team splits
    url = f"https://www.fangraphs.com/api/teams/stats?team={team_name}&split={hand}&stats=bat&csv=1"
    df = get_fangraphs_csv(url)

    if df.empty:
        return {
            "opp_vs_hand_k_pct": 0.22,
            "opp_vs_hand_contact_pct": 0.75,
            "opp_vs_hand_swstr_pct": 0.11
        }

    row = df.iloc[0]

    return {
        "opp_vs_hand_k_pct": row.get("K%", 22) / 100,
        "opp_vs_hand_contact_pct": row.get("Contact%", 75) / 100,
        "opp_vs_hand_swstr_pct": row.get("SwStr%", 11) / 100
    }

if __name__ == "__main__":
    print(get_opponent_stats("Yankees", "R"))