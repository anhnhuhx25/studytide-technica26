import os
import random
from datetime import datetime, timedelta
import psycopg2
import streamlit as st
import pandas as pd

DB_URI = os.getenv(
    "TIGER_DATA_URI",
    "postgres://tsdbadmin:x5t0vtqjy76agj4h@uebghuiu6p.lgv3tuy49m.tsdb.cloud.timescale.com:32696/tsdb?sslmode=require"
)

st.set_page_config(page_title="StudyTide", layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Mono:ital,wght@0,400;0,700;1,400&family=Inter:wght@400;500;600&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    h1, h2, h3, h4, .mono-font, .card-title, .db-val, .rec-badge {
        font-family: 'Space Mono', monospace !important;
        letter-spacing: -0.5px;
    }

    .stApp {
        background-color: #0b0f17;
        color: #e2e8f0;
    }

    /* Recommendation Banner */
    .rec-box {
        background: #111827;
        border: 1px solid #1e293b;
        border-left: 4px solid #38bdf8;
        padding: 16px 20px;
        border-radius: 4px;
        margin-bottom: 24px;
    }
    .rec-title {
        font-size: 0.82rem;
        text-transform: uppercase;
        color: #38bdf8;
        font-weight: 700;
        margin-bottom: 6px;
    }
    .rec-targets {
        font-size: 1.15rem;
        font-weight: 700;
        color: #f8fafc;
        margin-bottom: 6px;
    }
    .rec-desc {
        font-size: 0.88rem;
        color: #94a3b8;
    }

    /* Space Cards */
    .space-card {
        background: #111827;
        border: 1px solid #1f293d;
        border-radius: 6px;
        padding: 20px;
        height: 100%;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }
    .space-card.highlight {
        border-color: #38bdf8;
        box-shadow: 0 0 0 1px #38bdf8;
    }
    .card-title {
        font-size: 1.05rem;
        font-weight: 700;
        color: #f8fafc;
        margin-bottom: 6px;
    }
    .card-body {
        font-size: 0.82rem;
        color: #94a3b8;
        line-height: 1.5;
        margin-bottom: 14px;
    }
    .db-row {
        display: flex;
        align-items: baseline;
        gap: 10px;
        margin-bottom: 12px;
    }
    .db-val {
        font-size: 1.8rem;
        font-weight: 700;
    }
    .status-badge {
        font-family: 'Space Mono', monospace;
        font-size: 0.72rem;
        padding: 2px 8px;
        border-radius: 3px;
        text-transform: uppercase;
        font-weight: 700;
    }
    .status-green { background: #064e3b; color: #34d399; border: 1px solid #059669; }
    .status-yellow { background: #713f12; color: #fde047; border: 1px solid #ca8a04; }
    .status-red { background: #450a0a; color: #f87171; border: 1px solid #dc2626; }

    .tag-list {
        display: flex;
        flex-wrap: wrap;
        gap: 6px;
        margin-top: auto;
    }
    .tag-item {
        font-family: 'Space Mono', monospace;
        font-size: 0.70rem;
        color: #cbd5e1;
        background: #1e293b;
        padding: 3px 6px;
        border-radius: 2px;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def get_db():
    conn = psycopg2.connect(DB_URI)
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS noise_telemetry (
                time TIMESTAMPTZ NOT NULL,
                location TEXT NOT NULL,
                decibels DOUBLE PRECISION NOT NULL
            );
        """)
        conn.commit()
    return conn

conn = get_db()

#4 spots on campus
SPACES = {
    "Leyburn Library - LL3": {
        "full_name": "Leyburn Library · Lower Level 3",
        "desc": "Underground quiet retreat. Floor-to-ceiling book stacks and solo carrels. Strictly silent.",
        "thresholds": {"quiet": 34.0, "moderate": 42.0},
        "target_db": (26, 33),
        "ideal_modes": ["deep_focus"],
        "tags": ["Quiet Stacks", "Solo Carrels", "Spotty WiFi", "Plentiful Outlets"]
    },
    "Telford Science Library": {
        "full_name": "Telford Science Library",
        "desc": "Science Center workstation zone. Dual-display PCs equipped with GIS, Stata, and compiler tools.",
        "thresholds": {"quiet": 44.0, "moderate": 54.0},
        "target_db": (38, 46),
        "ideal_modes": ["deep_focus", "listening_study"],
        "tags": ["Dual-Monitor PCs", "GIS / Stata", "Low Whispers", "Fast 5GHz WiFi"]
    },
    "Leyburn Library - Main": {
        "full_name": "Leyburn Library · Main Floor",
        "desc": "Central campus study hub. Collaborative tables, research desks, and direct access to library staff.",
        "thresholds": {"quiet": 56.0, "moderate": 68.0},
        "target_db": (54, 62),
        "ideal_modes": ["group_collab"],
        "tags": ["Open Discussion", "Desktop Labs", "Research Staff", "High Traffic"]
    },
    "Elrod Commons Cafe": {
        "full_name": "Elrod Commons · Cafe & Lounge",
        "desc": "Active campus lounge with background music, espresso bar, and high conversational flow.",
        "thresholds": {"quiet": 66.0, "moderate": 78.0},
        "target_db": (66, 75),
        "ideal_modes": ["group_collab"],
        "tags": ["Cafe Ambience", "Background Music", "Group Tables", "Casual Study"]
    }
}

# --- Sidebar: User Intent vs Admin Testing ---
st.sidebar.markdown("<h3 class='mono-font' style='color:#f8fafc; margin-bottom:4px;'>STUDYTIDE // HUB</h3>", unsafe_allow_html=True)
st.sidebar.caption("Client telemetry streaming to Tiger Data.")

st.sidebar.markdown("---")
st.sidebar.markdown("<p class='mono-font' style='font-size:0.85rem; color:#38bdf8;'>[1] STUDENT STUDY INTENT</p>", unsafe_allow_html=True)
user_intent = st.sidebar.radio(
    "How do you plan to study today?",
    options=[
        ("deep_focus", "Solo Deep Focus (Require Silence, <= 35 dB)"),
        ("listening_study", "Individual / Audio (Whispering allowed, <= 48 dB)"),
        ("group_collab", "Group Discussion (Normal speech, <= 75 dB)")
    ],
    format_func=lambda x: x[1]
)[0]

st.sidebar.markdown("---")
st.sidebar.markdown("<p class='mono-font' style='font-size:0.85rem; color:#94a3b8;'>[2] SENSOR TELEMETRY (DEMO)</p>", unsafe_allow_html=True)

if st.sidebar.button("⚡ Reset & Seed 4 Spaces (Clean)", use_container_width=True):
    with conn.cursor() as cur:
        cur.execute("TRUNCATE TABLE noise_telemetry;")
        now = datetime.utcnow()
        for loc_key, meta in SPACES.items():
            low, high = meta["target_db"]
            for m in range(90, 0, -2):
                timestamp = now - timedelta(minutes=m)
                val = round(random.uniform(low, high) + random.choice([-0.8, 0.0, 0.8]), 1)
                cur.execute(
                    "INSERT INTO noise_telemetry (time, location, decibels) VALUES (%s, %s, %s);",
                    (timestamp, loc_key, val)
                )
        conn.commit()
    st.sidebar.success("Database cleaned & seeded with exactly 4 spaces.")

target_loc = st.sidebar.selectbox("Test IoT Node", list(SPACES.keys()))
sim_mic = st.sidebar.slider("Simulate Live Sound (dB)", 20.0, 85.0, 32.0, 0.5)

if st.sidebar.button("Broadcast Sensor Ping", use_container_width=True):
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO noise_telemetry (time, location, decibels) VALUES (NOW(), %s, %s);",
            (target_loc, sim_mic)
        )
        conn.commit()
    st.sidebar.success(f"Streamed {sim_mic} dB to Tiger Data.")

# --- Main Dashboard Header ---
st.markdown("<h1 style='margin-bottom:2px;'>STUDYTIDE</h1>", unsafe_allow_html=True)
st.markdown("<p class='mono-font' style='color:#64748b; font-size:0.88rem; margin-bottom:20px;'>CAMPUS SOUNDSCAPE TELEMETRY // REAL-TIME INGESTION VIA TIGER DATA</p>", unsafe_allow_html=True)

latest_query = """
    SELECT DISTINCT ON (location) location, decibels, time 
    FROM noise_telemetry 
    WHERE location IN %s
    ORDER BY location, time DESC;
"""
active_keys = tuple(SPACES.keys())
latest_df = pd.read_sql_query(latest_query, conn, params=(active_keys,))

if not latest_df.empty:
    matched_spaces = []
    if user_intent == "deep_focus":
        matched_spaces = [k for k, v in SPACES.items() if "deep_focus" in v["ideal_modes"] and latest_df[latest_df['location'] == k]['decibels'].values[0] <= 36.0]
        if not matched_spaces:
            matched_spaces = ["Leyburn Library - LL3"]
        rec_desc = "Optimal low-decibel environments matching zero-interruption thresholds."
    elif user_intent == "listening_study":
        matched_spaces = ["Telford Science Library"]
        rec_desc = "Moderate acoustic levels with specialized workstation hardware and GIS resources."
    else:
        matched_spaces = ["Leyburn Library - Main", "Elrod Commons Cafe"]
        rec_desc = "Conversational volume permitted. High acoustic ceiling for discussions without disturbing silent zones."

    target_names = " // ".join([SPACES[k]["full_name"] for k in matched_spaces])

    st.markdown(f"""
    <div class="rec-box">
        <div class="rec-title">RECOMMENDED MATCH FOR YOUR STUDY INTENT</div>
        <div class="rec-targets">{target_names}</div>
        <div class="rec-desc">{rec_desc}</div>
    </div>
    """, unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    cols = [c1, c2, c3, c4]

    for idx, (loc_key, meta) in enumerate(SPACES.items()):
        match_row = latest_df[latest_df['location'] == loc_key]
        current_db = match_row.iloc[0]['decibels'] if not match_row.empty else 0.0

        t = meta["thresholds"]
        if current_db <= t["quiet"]:
            badge_class = "status-green"
            badge_label = "NOMINAL // QUIET"
            val_color = "#34d399"
        elif current_db <= t["moderate"]:
            badge_class = "status-yellow"
            badge_label = "MODERATE // BUSY"
            val_color = "#fde047"
        else:
            badge_class = "status-red"
            badge_label = "ELEVATED // LOUD"
            val_color = "#f87171"

        tags_markup = "".join([f'<span class="tag-item">{t}</span>' for t in meta["tags"]])
        is_highlight = "highlight" if loc_key in matched_spaces else ""

        with cols[idx]:
            st.markdown(f"""
            <div class="space-card {is_highlight}">
                <div>
                    <div class="card-title">{meta['full_name']}</div>
                    <div class="card-body">{meta['desc']}</div>
                </div>
                <div>
                    <div class="db-row">
                        <span class="db-val" style="color: {val_color};">{current_db:.1f} dB</span>
                        <span class="status-badge {badge_class}">{badge_label}</span>
                    </div>
                    <div class="tag-list">
                        {tags_markup}
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)

    st.markdown("<h4 class='mono-font' style='margin-bottom:2px;'>TELEMETRY TRENDS (90-MIN ROLLUP)</h4>", unsafe_allow_html=True)
    st.caption("Grouped by 2-minute time buckets directly on PostgreSQL via Tiger Data.")

    trend_query = """
        SELECT 
            date_trunc('minute', time) AS minute_bucket,
            location,
            AVG(decibels) AS avg_db
        FROM noise_telemetry
        WHERE time > NOW() - INTERVAL '90 minutes'
          AND location IN %s
        GROUP BY minute_bucket, location
        ORDER BY minute_bucket ASC;
    """
    trend_df = pd.read_sql_query(trend_query, conn, params=(active_keys,))

    if not trend_df.empty:
        chart_data = trend_df.pivot(index='minute_bucket', columns='location', values='avg_db')
        chart_data = chart_data.ffill()
        st.line_chart(chart_data, use_container_width=True)
else:
    st.info("Click '⚡ Reset & Seed 4 Spaces (Clean)' in the left sidebar to initialize the 4 spaces.")