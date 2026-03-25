import os
from datetime import datetime

import pandas as pd
import streamlit as st

st.set_page_config(page_title="EdgeRank AI", layout="wide")

HITTERS_FILE = "data/mlb/official_plays.csv"
PITCHERS_FILE = "data/mlb/official_pitcher_plays.csv"

col1, col2 = st.columns([1, 4])

with col1:
    if os.path.exists("logo.png"):
        st.image("logo.png", width=120)

with col2:
    st.title("EdgeRank AI")
    st.subheader("MLB Official Plays")

st.caption(f"Updated: {datetime.now().strftime('%Y-%m-%d %I:%M %p')}")

# ----------------------------
# Load files
# ----------------------------
hitters_df = pd.DataFrame()
pitchers_df = pd.DataFrame()

if os.path.exists(HITTERS_FILE):
    hitters_df = pd.read_csv(HITTERS_FILE)

if os.path.exists(PITCHERS_FILE):
    pitchers_df = pd.read_csv(PITCHERS_FILE)

# ----------------------------
# Top stats
# ----------------------------
total_hitter_plays = len(hitters_df)
total_pitcher_plays = len(pitchers_df)
total_plays = total_hitter_plays + total_pitcher_plays

all_confidences = []

if not hitters_df.empty and "CONFIDENCE" in hitters_df.columns:
    all_confidences.extend(hitters_df["CONFIDENCE"].tolist())

if not pitchers_df.empty and "CONFIDENCE" in pitchers_df.columns:
    all_confidences.extend(pitchers_df["CONFIDENCE"].tolist())

avg_conf = round(sum(all_confidences) / len(all_confidences), 1) if all_confidences else 0

all_edges = []

if not hitters_df.empty and "EDGE" in hitters_df.columns:
    all_edges.extend(hitters_df["EDGE"].abs().tolist())

if not pitchers_df.empty and "EDGE" in pitchers_df.columns:
    all_edges.extend(pitchers_df["EDGE"].abs().tolist())

best_edge = round(max(all_edges), 2) if all_edges else 0

c1, c2, c3 = st.columns(3)
c1.metric("Total Plays", total_plays)
c2.metric("Average Confidence", f"{avg_conf}%")
c3.metric("Best Edge", best_edge)

# ----------------------------
# Hitter section
# ----------------------------
st.markdown("## Hitter Plays")

if hitters_df.empty:
    st.info("No hitter plays found.")
else:
    hitters_df = hitters_df.sort_values(
        by=["CONFIDENCE", "EDGE"],
        ascending=[False, False]
    ).reset_index(drop=True)

    for _, row in hitters_df.iterrows():
        with st.container(border=True):
            st.markdown(f"### {row['PLAYER_NAME']} — {row['PICK']} {row['LINE']} {row['STAT']}")
            cols = st.columns(4)
            cols[0].write(f"Projection: **{row['PROJECTION']}**")
            cols[1].write(f"Edge: **{row['EDGE']}**")
            cols[2].write(f"Confidence: **{row['CONFIDENCE']}%**")
            if "TEAM" in hitters_df.columns:
                cols[3].write(f"Team: **{row['TEAM']}**")

# ----------------------------
# Pitcher section
# ----------------------------
st.markdown("## Pitcher Strikeout Plays")

if pitchers_df.empty:
    st.info("No pitcher strikeout plays found.")
else:
    pitchers_df = pitchers_df.sort_values(
        by=["CONFIDENCE", "EDGE"],
        ascending=[False, False]
    ).reset_index(drop=True)

    for _, row in pitchers_df.iterrows():
        with st.container(border=True):
            st.markdown(f"### {row['PLAYER_NAME']} — {row['PICK']} {row['LINE']} {row['STAT']}")
            cols = st.columns(4)
            cols[0].write(f"Projection: **{row['PROJECTION']}**")
            cols[1].write(f"Edge: **{row['EDGE']}**")
            cols[2].write(f"Confidence: **{row['CONFIDENCE']}%**")
            if "OPPONENT" in pitchers_df.columns:
                cols[3].write(f"Opponent: **{row['OPPONENT']}**")

# ----------------------------
# Full tables
# ----------------------------
st.markdown("## Hitter Table")
if hitters_df.empty:
    st.write("No hitter table data.")
else:
    st.dataframe(hitters_df, use_container_width=True)

st.markdown("## Pitcher Table")
if pitchers_df.empty:
    st.write("No pitcher table data.")
else:
    st.dataframe(pitchers_df, use_container_width=True)
