import os
import logging
import base64
import urllib.request
import streamlit as st
import fastf1
from datetime import date, timedelta
from src.predictor import run
from src.data_loader import load_actual_results, CACHE_DIR
from src.visualize import team_color

fastf1.Cache.enable_cache(str(CACHE_DIR))
logging.getLogger("fastf1._api").setLevel(logging.ERROR)

LOGOS_DIR = os.path.join(str(CACHE_DIR), "logos")
os.makedirs(LOGOS_DIR, exist_ok=True)

st.set_page_config(
    page_title="F1 Race Predictor",
    page_icon="🏎",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Global CSS ─────────────────────────────────────────────────────────────────
st.html("""
<link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;600;700;800;900&family=Rajdhani:wght@300;400;500;600;700&family=Barlow+Condensed:wght@400;500;600;700;800;900&family=Barlow:wght@300;400;500;600;700&display=swap" rel="stylesheet">
<style>

/* ═══ ANIMATIONS ═══ */
@keyframes fadeInUp {
  from { opacity: 0; transform: translateY(18px); }
  to   { opacity: 1; transform: translateY(0); }
}
@keyframes gradientShift {
  0%   { background-position: 0% 50%; }
  50%  { background-position: 100% 50%; }
  100% { background-position: 0% 50%; }
}

/* ═══ BASE — carbon-fibre background with corner glows ═══ */
html, body, [data-testid="stAppViewContainer"] {
  background-color: #090912 !important;
  background-image:
    radial-gradient(ellipse at 0% 0%,   rgba(232,0,45,0.07) 0%, transparent 55%),
    radial-gradient(ellipse at 100% 100%, rgba(232,0,45,0.05) 0%, transparent 55%),
    repeating-linear-gradient(
      45deg,
      rgba(255,255,255,0.0)  0px, rgba(255,255,255,0.0)  2px,
      rgba(255,255,255,0.013) 2px, rgba(255,255,255,0.013) 3px
    ),
    repeating-linear-gradient(
      -45deg,
      rgba(255,255,255,0.0)  0px, rgba(255,255,255,0.0)  2px,
      rgba(255,255,255,0.013) 2px, rgba(255,255,255,0.013) 3px
    ) !important;
  background-size: 100% 100%, 100% 100%, 6px 6px, 6px 6px !important;
  color: #FFFFFF !important;
  font-family: 'Barlow', Arial, sans-serif !important;
}

/* ═══ SIDEBAR ═══ */
[data-testid="stSidebar"] {
  background: linear-gradient(180deg, #0E0E1E 0%, #090912 100%) !important;
  border-right: 1px solid rgba(232,0,45,0.2) !important;
  box-shadow: 4px 0 24px rgba(232,0,45,0.04) !important;
}
[data-testid="stSidebar"] * { color: #FFFFFF !important; }
[data-testid="stSidebar"] .stButton > button {
  background: linear-gradient(135deg, #E8002D 0%, #C8001F 100%) !important;
  color: #fff !important; border: none !important;
  font: 700 0.78rem 'Rajdhani', Arial, sans-serif !important;
  letter-spacing: 0.1em !important; text-transform: uppercase !important;
  border-radius: 6px !important;
  box-shadow: 0 4px 14px rgba(232,0,45,0.3) !important;
}

/* ═══ PRIMARY BUTTON ═══ */
.stButton > button[kind="primary"] {
  background: linear-gradient(135deg, #E8002D 0%, #C8001F 100%) !important;
  color: #fff !important; border: none !important;
  font: 700 0.88rem 'Rajdhani', Arial, sans-serif !important;
  letter-spacing: 0.12em !important; text-transform: uppercase !important;
  padding: 0.65rem 2rem !important; border-radius: 6px !important;
  box-shadow: 0 4px 16px rgba(232,0,45,0.35) !important;
  transition: all 0.2s ease !important;
}
.stButton > button[kind="primary"]:hover {
  transform: translateY(-2px) scale(1.02) !important;
  box-shadow: 0 8px 24px rgba(232,0,45,0.5) !important;
}

/* ═══ SELECTBOX ═══ */
[data-testid="stSelectbox"] label {
  font: 600 0.65rem 'Rajdhani', Arial, sans-serif !important;
  letter-spacing: 0.18em !important; text-transform: uppercase !important;
  color: #B3B3C2 !important;
}

/* ═══ HERO ═══ */
.hero-wrap {
  padding: 60px 0 44px;
  animation: fadeInUp 0.8s ease both;
}
.hero-eyebrow {
  font: 600 0.62rem 'Rajdhani', Arial, sans-serif;
  letter-spacing: 0.32em; text-transform: uppercase;
  color: #E8002D; margin-bottom: 18px; display: block;
}
.hero-title {
  font: 900 5.6rem/0.88 'Orbitron', 'Barlow Condensed', Arial, sans-serif;
  text-transform: uppercase; letter-spacing: 0.02em;
  background: linear-gradient(125deg, #FFFFFF 0%, #FFFFFF 35%, #E8002D 65%, #FF4D6D 100%);
  background-size: 200% 200%;
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  animation: gradientShift 5s ease infinite;
  margin: 0 0 16px;
}
.hero-tagline {
  font: 400 0.9rem 'Rajdhani', Arial, sans-serif;
  letter-spacing: 0.14em; text-transform: uppercase;
  color: #B3B3C2; margin-top: 18px; line-height: 1.6; max-width: 520px;
}

/* ═══ TIMELINE ═══ */
.timeline-outer {
  position: relative; margin: 28px 0 36px;
  animation: fadeInUp 0.6s ease 0.15s both;
}
.timeline-line {
  position: absolute; top: 34px; left: 8%; right: 8%; height: 1px;
  background: linear-gradient(90deg, transparent, rgba(232,0,45,0.35), rgba(232,0,45,0.35), transparent);
}
.timeline-wrap { display: flex; align-items: flex-start; }
.timeline-step {
  display: flex; flex-direction: column; align-items: center;
  flex: 1; position: relative; z-index: 1; padding: 0 6px; text-align: center;
}
.tl-num {
  font: 900 0.55rem 'Orbitron', Arial, sans-serif;
  color: #E8002D; letter-spacing: 0.06em; margin-bottom: 5px;
}
.tl-dot {
  width: 34px; height: 34px; border-radius: 50%;
  background: rgba(13,13,30,0.95);
  border: 1px solid rgba(232,0,45,0.35);
  display: flex; align-items: center; justify-content: center;
  font-size: 0.95rem; margin-bottom: 8px;
  box-shadow: 0 0 12px rgba(232,0,45,0.12);
}
.tl-label {
  font: 600 0.62rem 'Rajdhani', Arial, sans-serif;
  letter-spacing: 0.08em; text-transform: uppercase;
  color: #B3B3C2; line-height: 1.35;
}

/* ═══ GLASS CARD ═══ */
.glass-card {
  background: rgba(19,19,43,0.7);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border: 1px solid rgba(255,255,255,0.07);
  border-top: 1px solid rgba(255,255,255,0.12);
  border-radius: 12px; padding: 22px 24px;
  box-shadow: 0 8px 32px rgba(0,0,0,0.3), 0 0 0 1px rgba(232,0,45,0.05);
  transition: box-shadow 0.3s ease, transform 0.25s ease;
  animation: fadeInUp 0.6s ease both;
  margin-bottom: 18px;
}
.glass-card:hover {
  box-shadow: 0 12px 40px rgba(0,0,0,0.4), 0 0 0 1px rgba(232,0,45,0.14);
  transform: translateY(-2px);
}

/* ═══ SELECTOR CARD ═══ */
.selector-wrap {
  background: rgba(19,19,43,0.72);
  backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px);
  border: 1px solid rgba(255,255,255,0.07);
  border-top: 3px solid #E8002D;
  border-radius: 10px; padding: 24px 24px 20px; margin-bottom: 28px;
  box-shadow: 0 0 40px rgba(232,0,45,0.06);
  animation: fadeInUp 0.5s ease 0.1s both;
}

/* ═══ INFO CARDS ═══ */
.info-card {
  background: rgba(19,19,43,0.65);
  border: 1px solid rgba(255,255,255,0.06);
  border-left: 3px solid #E8002D; border-radius: 10px;
  padding: 20px; height: 100%;
  transition: box-shadow 0.3s ease;
  animation: fadeInUp 0.6s ease 0.2s both;
}
.info-card:hover { box-shadow: 0 0 20px rgba(232,0,45,0.1); }
.info-card h4 {
  margin: 0 0 10px;
  font: 700 0.72rem 'Rajdhani', Arial, sans-serif;
  letter-spacing: 0.18em; text-transform: uppercase; color: #E8002D;
}
.info-card p {
  margin: 0; font: 400 0.85rem 'Barlow', Arial, sans-serif;
  color: #B3B3C2; line-height: 1.65;
}

/* ═══ RACE HEADER ═══ */
.race-header {
  position: relative; padding: 36px 0 28px;
  margin-bottom: 28px; overflow: hidden;
  animation: fadeInUp 0.6s ease both;
}
.race-header::after {
  content: ''; position: absolute; bottom: 0; left: 0;
  width: 100%; height: 1px;
  background: linear-gradient(90deg, #E8002D 0%, rgba(232,0,45,0.15) 50%, transparent 100%);
}
.race-eyebrow {
  font: 600 0.6rem 'Rajdhani', Arial, sans-serif;
  letter-spacing: 0.3em; text-transform: uppercase;
  color: #E8002D; margin-bottom: 10px; display: block;
}
.race-name {
  font: 900 4rem/0.9 'Orbitron', 'Barlow Condensed', Arial, sans-serif;
  text-transform: uppercase; letter-spacing: 0.02em;
  color: #FFFFFF; margin: 0; word-break: break-word;
  text-shadow: 0 0 60px rgba(232,0,45,0.12);
}
.race-name em { color: #E8002D; font-style: normal; }

/* ═══ SECTION HEADER ═══ */
.sec-header {
  position: relative;
  font: 700 0.65rem 'Rajdhani', Arial, sans-serif;
  letter-spacing: 0.24em; text-transform: uppercase; color: #B3B3C2;
  border-bottom: 1px solid rgba(255,255,255,0.06);
  padding-bottom: 9px; margin-bottom: 4px;
}
.sec-header::after {
  content: ''; position: absolute; bottom: -1px; left: 0;
  width: 36px; height: 2px; background: #E8002D;
}

/* ═══ CIRCUIT CONTEXT CARD ═══ */
.circuit-card {
  display: flex; align-items: stretch;
  background: rgba(0,207,255,0.04);
  border: 1px solid rgba(0,207,255,0.12);
  border-radius: 10px; margin-bottom: 18px;
  overflow: hidden;
  animation: fadeInUp 0.5s ease 0.15s both;
}
.circuit-info {
  display: flex; align-items: flex-start; gap: 16px;
  padding: 16px 20px; flex: 1; min-width: 0;
}
.circuit-flag { flex-shrink: 0; display: flex; align-items: center; padding-top: 2px; }
.circuit-details { flex: 1; min-width: 0; }
.circuit-name {
  font: 700 0.92rem 'Rajdhani', Arial, sans-serif;
  color: #FFFFFF; letter-spacing: 0.06em; text-transform: uppercase; margin: 0 0 4px;
}
.circuit-blurb {
  font: 400 0.8rem 'Barlow', Arial, sans-serif;
  color: #B3B3C2; line-height: 1.55; margin: 0;
}
.ov-badge {
  font: 700 0.52rem 'Rajdhani', Arial, sans-serif;
  letter-spacing: 0.16em; text-transform: uppercase;
  padding: 3px 10px; border-radius: 4px; white-space: nowrap;
  flex-shrink: 0; align-self: flex-start; margin-top: 2px;
}
.ov-very-high { background: rgba(0,230,118,0.14); color: #00E676; border: 1px solid rgba(0,230,118,0.25); }
.ov-high      { background: rgba(0,207,255,0.12); color: #00CFFF; border: 1px solid rgba(0,207,255,0.22); }
.ov-medium    { background: rgba(255,213,79,0.12); color: #FFD54F; border: 1px solid rgba(255,213,79,0.22); }
.ov-low       { background: rgba(255,109,0,0.12); color: #FF8C42; border: 1px solid rgba(255,109,0,0.22); }
.ov-very-low  { background: rgba(232,0,45,0.12); color: #E8002D;  border: 1px solid rgba(232,0,45,0.22); }
.circuit-track {
  width: 300px; flex-shrink: 0;
  background: rgba(0,0,0,0.22);
  border-left: 1px solid rgba(0,207,255,0.1);
  display: flex; align-items: center; justify-content: center;
  padding: 12px 10px;
}
.circuit-track img {
  max-width: 100%; max-height: 200px;
  object-fit: contain; display: block;
  filter: drop-shadow(0 0 8px rgba(232,0,45,0.2));
}



/* ═══ PODIUM ═══ */
.podium-wrap {
  background: rgba(19,19,43,0.68);
  backdrop-filter: blur(10px); -webkit-backdrop-filter: blur(10px);
  border: 1px solid rgba(255,255,255,0.07); border-radius: 12px;
  padding: 22px 22px 0; margin-bottom: 24px;
  height: 100%; box-sizing: border-box;
  animation: fadeInUp 0.6s ease 0.2s both;
}
[data-testid="stHorizontalBlock"]:has(.podium-wrap) {
  align-items: stretch !important;
}
[data-testid="stHorizontalBlock"]:has(.podium-wrap) > [data-testid="stColumn"] {
  display: flex !important; flex-direction: column !important;
}
[data-testid="stHorizontalBlock"]:has(.podium-wrap) > [data-testid="stColumn"] > div {
  flex: 1 !important; display: flex !important; flex-direction: column !important;
}
[data-testid="stHorizontalBlock"]:has(.podium-wrap) > [data-testid="stColumn"] > div > div {
  flex: 1 !important;
}
.podium-label {
  font: 700 0.6rem 'Rajdhani', Arial, sans-serif;
  letter-spacing: 0.28em; text-transform: uppercase; color: #B3B3C2;
  border-bottom: 1px solid rgba(255,255,255,0.06); padding-bottom: 10px; margin-bottom: 20px;
}
.podium-grid { display: flex; align-items: flex-end; justify-content: center; gap: 4px; }
.pod-card { display: flex; flex-direction: column; align-items: center; flex: 1; max-width: 260px; }
.pod-info { text-align: center; margin-bottom: 10px; }
.pod-winner-badge {
  font: 700 0.52rem 'Rajdhani', Arial, sans-serif;
  letter-spacing: 0.2em; text-transform: uppercase;
  color: #E8C948; background: rgba(232,201,72,0.1);
  border: 1px solid rgba(232,201,72,0.25);
  padding: 3px 12px; border-radius: 4px; margin-bottom: 8px; display: inline-block;
  box-shadow: 0 0 14px rgba(232,201,72,0.18);
}
.pod-name { font: 700 0.98rem 'Barlow', Arial, sans-serif; color: #FFFFFF; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 230px; }
.pod-name-1 { font-size: 1.2rem; font-weight: 800; }
.pod-team { font: 500 0.64rem 'Rajdhani', Arial, sans-serif; text-transform: uppercase; letter-spacing: 0.1em; margin-top: 3px; }
.pod-block { width: 100%; display: flex; align-items: center; justify-content: center; border-radius: 4px 4px 0 0; margin-top: 10px; }
.pod-block-1 { height: 112px; background: linear-gradient(180deg, rgba(232,201,72,0.1) 0%, rgba(19,19,43,0.5) 100%); }
.pod-block-2 { height: 76px; background: rgba(19,19,43,0.5); }
.pod-block-3 { height: 56px; background: rgba(19,19,43,0.5); }
.pod-num { font: 900 3.2rem 'Orbitron', Arial, sans-serif; }
.pod-num-1 { color: #E8C948; font-size: 3.8rem; text-shadow: 0 0 24px rgba(232,201,72,0.4); }
.pod-num-2 { color: #9CA3AF; }
.pod-num-3 { color: #B87333; }

/* ═══ RESULTS TABLE — light/white theme ═══ */
.f1-table-wrap {
  background: #FFFFFF;
  border: 1px solid #E0E0EC;
  border-radius: 10px; overflow: hidden; margin-top: 2px;
  max-width: 560px;
  box-shadow: 0 4px 24px rgba(0,0,0,0.13);
  animation: fadeInUp 0.5s ease 0.2s both;
}
.f1-table { width: 100%; border-collapse: collapse; font-family: 'Barlow', Arial, sans-serif; }
.f1-table thead tr { border-bottom: 2px solid #E8002D; }
.f1-table thead th {
  font: 700 0.58rem 'Rajdhani', Arial, sans-serif;
  letter-spacing: 0.18em; text-transform: uppercase; color: #6B6B85;
  padding: 9px 12px; text-align: left; white-space: nowrap;
  background: #F5F5FA;
}
.f1-table thead th.right { text-align: right; }
.f1-table tbody tr { border-bottom: 1px solid #EFEFEF; transition: background 0.15s ease; background: #FFFFFF; }
.f1-table tbody tr:last-child { border-bottom: none; }
.f1-table tbody tr:hover { background: #FFF5F5; }
.f1-table td { padding: 10px 12px; vertical-align: middle; }
.td-pos { font: 900 0.85rem 'Orbitron', Arial, sans-serif; color: #111118; width: 36px; min-width: 36px; }
.td-pos.p1 { color: #C9A800; }
.td-pos.p2 { color: #7A8390; }
.td-pos.p3 { color: #9A6520; }
.td-driver-name { font: 600 0.88rem 'Barlow', Arial, sans-serif; color: #111118; white-space: nowrap; }
.td-team-cell { display: flex; align-items: center; }
.td-team-name { font: 400 0.78rem 'Barlow', Arial, sans-serif; color: #666680; white-space: nowrap; }
.td-stat { font: 500 0.82rem 'Barlow', Arial, sans-serif; color: #444458; text-align: right; white-space: nowrap; }
.td-delta { text-align: right; white-space: nowrap; }
.delta-up   { font: 700 0.8rem 'Barlow', Arial, sans-serif; color: #1A7A40; }
.delta-down { font: 700 0.8rem 'Barlow', Arial, sans-serif; color: #C80000; }
.delta-none { font: 500 0.8rem 'Barlow', Arial, sans-serif; color: #AAAABC; }
.err-badge { display: inline-block; font: 700 0.68rem 'Barlow', Arial, sans-serif; padding: 2px 9px; border-radius: 99px; }
.err-good { background: rgba(0,160,84,0.1);  color: #00873D; border: 1px solid rgba(0,160,84,0.2); }
.err-ok   { background: rgba(180,130,0,0.1); color: #9A7000; border: 1px solid rgba(180,130,0,0.2); }
.err-bad  { background: rgba(200,0,0,0.1);   color: #C80000; border: 1px solid rgba(200,0,0,0.2); }

/* ═══ TABS ═══ */
[data-testid="stTabs"] { gap: 0; }
[data-testid="stTab"] {
  font: 700 0.82rem 'Rajdhani', Arial, sans-serif !important;
  letter-spacing: 0.14em !important; text-transform: uppercase !important;
  color: #B3B3C2 !important; border-bottom: 2px solid transparent !important;
  padding: 10px 24px !important; background: transparent !important;
  transition: color 0.2s ease !important;
}
[data-testid="stTab"][aria-selected="true"] {
  color: #FFFFFF !important; border-bottom: 2px solid #E8002D !important;
}
[data-testid="stTabPanel"] { padding-top: 8px !important; }

/* ═══ STATUS BADGE ═══ */
.status-badge {
  display: inline-block;
  font: 700 0.62rem 'Rajdhani', Arial, sans-serif;
  letter-spacing: 0.12em; padding: 5px 14px; border-radius: 6px;
  text-transform: uppercase; margin-bottom: 14px;
}
.status-past    { background: rgba(0,230,118,0.1);  color: #00E676; border: 1px solid rgba(0,230,118,0.2); }
.status-quali   { background: rgba(255,213,79,0.1); color: #FFD54F; border: 1px solid rgba(255,213,79,0.2); }
.status-raceday { background: rgba(0,207,255,0.1);  color: #00CFFF; border: 1px solid rgba(0,207,255,0.2); }
.status-pending { background: rgba(232,0,45,0.1);   color: #E8002D; border: 1px solid rgba(232,0,45,0.2); }

/* ═══ MISC ═══ */
.f1-divider { border: none; border-top: 1px solid rgba(255,255,255,0.05); margin: 32px 0; }
.f1-caption {
  font: 400 0.6rem 'Barlow', Arial, sans-serif;
  letter-spacing: 0.08em; color: #55556A; margin-top: 14px; text-align: center;
}

/* ═══ HIDE SIDEBAR PANEL ON LANDING (keep toggle visible) ═══ */
[data-testid="stSidebar"] { display: none !important; }
</style>
""")

# ── Circuit context data ───────────────────────────────────────────────────────
_WP = "https://commons.wikimedia.org/wiki/Special:FilePath/"

# Official F1 CDN circuit map images — detailed track illustrations
_F1_CDN_TRACK = "https://media.formula1.com/image/upload/f_auto/q_auto/v1740000001/common/f1/{year}/track/{year}track{slug}detailed.webp"
_F1_TRACK_SLUG: dict[str, str] = {
    "Australia":     "melbourne",
    "China":         "shanghai",
    "Japan":         "suzuka",
    "Bahrain":       "sakhir",
    "Saudi Arabia":  "jeddah",
    "Miami":         "miami",
    "Canada":        "montreal",
    "Monaco":        "montecarlo",
    "Spain":         "catalunya",
    "Austria":       "spielberg",
    "Britain":       "silverstone",
    "Belgium":       "spafrancorchamps",
    "Hungary":       "hungaroring",
    "Netherlands":   "zandvoort",
    "Italy":         "monza",
    "Azerbaijan":    "baku",
    "Singapore":     "singapore",
    "United States": "austin",
    "Mexico City":   "mexicocity",
    "Brazil":        "interlagos",
    "Las Vegas":     "lasvegas",
    "Qatar":         "lusail",
    "Abu Dhabi":     "yasmarina",
    "Madrid":        "madrid",
}

CIRCUIT_INFO: dict[str, dict] = {
    "Australia":     {"cc": "au", "circuit": "Albert Park, Melbourne",        "ov": "MEDIUM",    "ov_cls": "ov-medium",    "blurb": "A street-park circuit built around a lake in Melbourne. One long DRS straight helps overtaking, but grid position still plays a major role. Expect a mix of strategic races and on-track battles.",                                                                                                                          "track_img": _WP + "Australia_circuit.svg?width=400"},
    "China":         {"cc": "cn", "circuit": "Shanghai International Circuit", "ov": "HIGH",      "ov_cls": "ov-high",      "blurb": "Two long DRS zones make passing relatively easy here. Cars with strong raw speed can work their way through the field even from mid-grid. Qualifying matters less than at most tracks.",                                                                                                                            "track_img": _WP + "Shanghai_international_circuit.svg?width=400"},
    "Japan":         {"cc": "jp", "circuit": "Suzuka Circuit",                "ov": "LOW",       "ov_cls": "ov-low",       "blurb": "A technical figure-8 layout famous for its fast, flowing corners. Overtaking spots are very limited, so getting a clean qualifying lap is essential. The race order usually mirrors the grid.",                                                                                                                       "track_img": _WP + "Suzuka_circuit_map.svg?width=400"},
    "Bahrain":       {"cc": "bh", "circuit": "Bahrain International Circuit",  "ov": "HIGH",      "ov_cls": "ov-high",      "blurb": "Three DRS zones and several long braking zones make Bahrain one of the most overtaking-friendly tracks on the calendar. Big gaps between grid position and final result are common here.",                                                                                                                         "track_img": _WP + "Bahrain_International_Circuit--2004.svg?width=400"},
    "Saudi Arabia":  {"cc": "sa", "circuit": "Jeddah Corniche Circuit",       "ov": "MEDIUM",    "ov_cls": "ov-medium",    "blurb": "An ultra-fast street circuit where safety cars appear regularly. When the safety car comes out it can completely reset the race order, so strategy and timing often matter more than outright qualifying pace.",                                                                                                       "track_img": _WP + "Jeddah_Street_Circuit.svg?width=400"},
    "Miami":         {"cc": "us", "circuit": "Miami International Autodrome",  "ov": "MEDIUM",    "ov_cls": "ov-medium",    "blurb": "A purpose-built street-style circuit with DRS-assisted passing opportunities on the main straight. Consistent tyre management over long stints tends to decide the outcome more than one-lap qualifying pace.",                                                                                                      "track_img": _WP + "Miami_International_Autodrome_track_map.svg?width=400"},
    "Canada":        {"cc": "ca", "circuit": "Circuit Gilles Villeneuve",     "ov": "HIGH",      "ov_cls": "ov-high",      "blurb": "A wall-lined circuit with a long straight leading into a tight hairpin at the end. One of F1's classic overtaking venues where bold late-braking moves and aggressive driving are regularly rewarded.",                                                                                                             "track_img": _WP + "Circuit_Gilles_Villeneuve.svg?width=400"},
    "Monaco":        {"cc": "mc", "circuit": "Circuit de Monaco",             "ov": "VERY LOW",  "ov_cls": "ov-very-low",  "blurb": "The most famous race in the world, held through the narrow streets of Monte Carlo. Overtaking is virtually impossible once the race begins, which means qualifying position is almost everything. It is essentially a time trial dressed up as a race.",                                                            "track_img": _WP + "Monte_Carlo_Formula_1_track_map.svg?width=400"},
    "Spain":         {"cc": "es", "circuit": "Circuit de Barcelona-Catalunya", "ov": "LOW",       "ov_cls": "ov-low",       "blurb": "A smooth, well-understood circuit used regularly for pre-season testing. Overtaking is difficult unless there is a significant pace gap between two cars. The grid order at the start tends to be closely reflected in the final result.",                                                                          "track_img": _WP + "Circuit_de_barcelona_catalunya.svg?width=400"},
    "Austria":       {"cc": "at", "circuit": "Red Bull Ring",                 "ov": "HIGH",      "ov_cls": "ov-high",      "blurb": "Short and fast with a DRS opportunity on the main straight. Tyre wear creates strategic variety and cars with strong race pace can recover positions quickly from lower grid slots during the race.",                                                                                                                "track_img": _WP + "Red_Bull_Ring.svg?width=400"},
    "Britain":       {"cc": "gb", "circuit": "Silverstone Circuit",           "ov": "HIGH",      "ov_cls": "ov-high",      "blurb": "High-speed corners combined with strong DRS zones make Silverstone an exciting race. Tyre wear is a significant variable and well-timed pit stop strategy can dramatically change where drivers finish.",                                                                                                         "track_img": _WP + "Silverstone_circuit_2011.svg?width=400"},
    "Belgium":       {"cc": "be", "circuit": "Circuit de Spa-Francorchamps",  "ov": "HIGH",      "ov_cls": "ov-high",      "blurb": "Spa's Kemmel Straight is one of the longest in F1, making raw engine power the dominant factor here. Cars with strong straight-line speed can make big gains, so grid position matters less than at most tracks.",                                                                                                 "track_img": _WP + "Spa-Francorchamps_of_Belgium.svg?width=400"},
    "Hungary":       {"cc": "hu", "circuit": "Hungaroring",                   "ov": "LOW",       "ov_cls": "ov-low",       "blurb": "Tight and twisty, the Hungaroring is often compared to Monaco without the barriers. Passing is very difficult unless there is a meaningful pace difference between two cars. Track position is extremely hard to recover once lost.",                                                                               "track_img": _WP + "Hungaroring.svg?width=400"},
    "Netherlands":   {"cc": "nl", "circuit": "Circuit Zandvoort",             "ov": "LOW",       "ov_cls": "ov-low",       "blurb": "Banked corners and a narrow layout leave very few genuine overtaking opportunities. A strong qualifying lap is essential at Zandvoort because once the race starts, changing position on track is extremely difficult.",                                                                                            "track_img": _WP + "Zandvoort_track_map.svg?width=400"},
    "Italy":         {"cc": "it", "circuit": "Autodromo Nazionale Monza",     "ov": "VERY HIGH", "ov_cls": "ov-very-high", "blurb": "Known as the Temple of Speed. Three DRS zones and the longest straights in F1 create massive slipstream battles throughout the race. Overtaking is very common here and starting position matters less than almost anywhere else on the calendar.",                                                                "track_img": _WP + "Monza_track_map.svg?width=400"},
    "Madrid":        {"cc": "es", "circuit": "Madrid Street Circuit",         "ov": "MEDIUM",    "ov_cls": "ov-medium",    "blurb": "New to the F1 calendar in 2026. The Madrid street layout features fast sections through the city combined with strategic overtaking zones. As a brand new venue, expect plenty of unpredictability and close racing throughout the weekend.",                                                                        "track_img": ""},
    "Azerbaijan":    {"cc": "az", "circuit": "Baku City Circuit",             "ov": "HIGH",      "ov_cls": "ov-high",      "blurb": "Baku's main straight is the longest in F1 at just over 2km. Safety cars appear regularly on these tight city streets, but the enormous DRS zone creates spectacular late-braking overtakes on every lap.",                                                                                                          "track_img": _WP + "Baku_Formula_1_track_map.svg?width=400"},
    "Singapore":     {"cc": "sg", "circuit": "Marina Bay Street Circuit",     "ov": "VERY LOW",  "ov_cls": "ov-very-low",  "blurb": "A night race through the tight streets of Marina Bay. Safety cars are almost guaranteed to appear and they often reshape the entire result more than raw race pace does. Strategy under safety car conditions is everything here.",                                                                                 "track_img": _WP + "Singapore_circuit_map.svg?width=400"},
    "United States": {"cc": "us", "circuit": "Circuit of the Americas",       "ov": "MEDIUM",    "ov_cls": "ov-medium",    "blurb": "Wide runoffs and a long back straight give cars room to race. Turn 1 at the top of the hill is a classic overtaking spot. Both qualifying position and tyre strategy play an important role in deciding the final order.",                                                                                        "track_img": _WP + "Americas_Formula_1_track_map.svg?width=400"},
    "Mexico City":   {"cc": "mx", "circuit": "Autodromo Hermanos Rodriguez",  "ov": "MEDIUM",    "ov_cls": "ov-medium",    "blurb": "High altitude significantly reduces aerodynamic downforce, so engines run near peak power throughout the lap. The pace advantage earned in qualifying tends to carry directly into the race without much opportunity for recovery.",                                                                                   "track_img": _WP + "Autodromo_Hermanos_Rodriguez_circuit_map.svg?width=400"},
    "Brazil":        {"cc": "br", "circuit": "Interlagos",                    "ov": "HIGH",      "ov_cls": "ov-high",      "blurb": "Interlagos is famous for producing chaotic and unpredictable races. The Brazilian weather can change rapidly and when rain or safety cars appear, the entire running order can be flipped on its head within a single lap.",                                                                                       "track_img": _WP + "Interlagos_circuit.svg?width=400"},
    "Las Vegas":     {"cc": "us", "circuit": "Las Vegas Strip Circuit",       "ov": "HIGH",      "ov_cls": "ov-high",      "blurb": "A Saturday night race held along the famous Las Vegas Strip. The enormously long straight creates massive slipstream battles between cars and produces exciting position changes that keep the race interesting from start to finish.",                                                                               "track_img": _WP + "Las_Vegas_Strip_Circuit_track_map.svg?width=400"},
    "Qatar":         {"cc": "qa", "circuit": "Lusail International Circuit",  "ov": "MEDIUM",    "ov_cls": "ov-medium",    "blurb": "A high-speed flowing circuit where tyre degradation is extremely severe. Managing tyre life becomes the priority for every team, and pit stop strategy often matters more than outright car pace or qualifying position.",                                                                                          "track_img": _WP + "Losail_International_Circuit_track_map.svg?width=400"},
    "Abu Dhabi":     {"cc": "ae", "circuit": "Yas Marina Circuit",            "ov": "MEDIUM",    "ov_cls": "ov-medium",    "blurb": "The season finale at Yas Marina. The updated post-2021 layout opened up more overtaking opportunities and the race tends to feature a combination of genuine wheel-to-wheel battles and strategic pit stop plays to close out the championship.",                                                                   "track_img": _WP + "Yas_Marina_circuit_2021.svg?width=400"},
}

# ── Race Calendar ──────────────────────────────────────────────────────────────
RACE_CALENDAR: dict[int, dict[str, date]] = {
    2024: {
        "Bahrain": date(2024,3,2), "Saudi Arabia": date(2024,3,9),
        "Australia": date(2024,3,24), "Japan": date(2024,4,7),
        "China": date(2024,4,21), "Miami": date(2024,5,5),
        "Emilia Romagna": date(2024,5,19), "Monaco": date(2024,5,26),
        "Canada": date(2024,6,9), "Spain": date(2024,6,23),
        "Austria": date(2024,6,30), "Britain": date(2024,7,7),
        "Hungary": date(2024,7,21), "Belgium": date(2024,7,28),
        "Netherlands": date(2024,8,25), "Italy": date(2024,9,1),
        "Azerbaijan": date(2024,9,15), "Singapore": date(2024,9,22),
        "United States": date(2024,10,20), "Mexico City": date(2024,10,27),
        "Brazil": date(2024,11,3), "Las Vegas": date(2024,11,23),
        "Qatar": date(2024,12,1), "Abu Dhabi": date(2024,12,8),
    },
    2025: {
        "Australia": date(2025,3,16), "China": date(2025,3,23),
        "Japan": date(2025,4,6), "Bahrain": date(2025,4,13),
        "Saudi Arabia": date(2025,4,20), "Miami": date(2025,5,4),
        "Emilia Romagna": date(2025,5,18), "Monaco": date(2025,5,25),
        "Spain": date(2025,6,1), "Canada": date(2025,6,15),
        "Austria": date(2025,6,29), "Britain": date(2025,7,6),
        "Belgium": date(2025,7,27), "Hungary": date(2025,8,3),
        "Netherlands": date(2025,8,31), "Italy": date(2025,9,7),
        "Azerbaijan": date(2025,9,21), "Singapore": date(2025,10,5),
        "United States": date(2025,10,19), "Mexico City": date(2025,10,26),
        "Brazil": date(2025,11,9), "Las Vegas": date(2025,11,22),
        "Qatar": date(2025,11,30), "Abu Dhabi": date(2025,12,7),
    },
    2026: {
        "Australia": date(2026,3,8), "China": date(2026,3,15),
        "Japan": date(2026,3,29), "Bahrain": date(2026,4,12),
        "Saudi Arabia": date(2026,4,19), "Miami": date(2026,5,3),
        "Canada": date(2026,5,24), "Monaco": date(2026,6,7),
        "Spain": date(2026,6,14), "Austria": date(2026,6,28),
        "Britain": date(2026,7,5), "Belgium": date(2026,7,19),
        "Hungary": date(2026,7,26), "Netherlands": date(2026,8,23),
        "Italy": date(2026,9,6), "Madrid": date(2026,9,13),
        "Azerbaijan": date(2026,9,26), "Singapore": date(2026,10,11),
        "United States": date(2026,10,25), "Mexico City": date(2026,11,1),
        "Brazil": date(2026,11,8), "Las Vegas": date(2026,11,21),
        "Qatar": date(2026,11,29), "Abu Dhabi": date(2026,12,6),
    },
}


def get_available_races(year: int) -> list[str]:
    today = date.today()
    cal = RACE_CALENDAR.get(year, {})
    return [r for r, d in cal.items() if today >= d - timedelta(days=3)]


def get_race_status(year: int, race: str) -> str:
    today = date.today()
    race_date = RACE_CALENDAR.get(year, {}).get(race)
    if race_date is None:
        return "past"
    if today > race_date:           return "past"
    if today == race_date:          return "race_day"
    if today >= race_date - timedelta(days=1): return "qualifying_done"
    if today >= race_date - timedelta(days=3): return "qualifying_pending"
    return "future"


# ── Session state ──────────────────────────────────────────────────────────────
_defaults = {
    "results": None, "stats": {}, "actual_df": None,
    "last_race": None, "last_year": None, "error": None,
    "sel_year": 2026, "sel_race": None,
    "train_years": [2024, 2025], "force_refresh": False,
    "collapse_sidebar": False,
}
for _k, _v in _defaults.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v


# ── HTML renderers ─────────────────────────────────────────────────────────────

def _pc(pos: int) -> str:
    return {1: "p1", 2: "p2", 3: "p3"}.get(pos, "")


def _pos_color(pos: int) -> str:
    return {1: "#E8C948", 2: "#9CA3AF", 3: "#B87333"}.get(pos, "#FFFFFF")




def render_circuit_card(race: str, map_b64: str = "") -> str:
    info = CIRCUIT_INFO.get(race)
    if not info:
        return ""
    cc   = info["cc"]
    flag = (f'<img src="https://flagcdn.com/w40/{cc}.png"'
            f' srcset="https://flagcdn.com/w80/{cc}.png 2x"'
            f' width="40" height="27"'
            f' style="border-radius:3px;display:block;object-fit:cover"'
            f' alt="{cc.upper()} flag">')
    # Prefer FastF1 telemetry map; fall back to official F1 CDN detailed illustration
    if map_b64:
        img_src  = f"data:image/png;base64,{map_b64}"
        img_type = "png"
    else:
        slug = _F1_TRACK_SLUG.get(race, "")
        img_src  = _F1_CDN_TRACK.format(year=2026, slug=slug) if slug else ""
        img_type = "webp"
    track_section = (
        f'<div class="circuit-track">'
        f'<img src="{img_src}" alt="{race} circuit map"'
        f' onerror="this.parentElement.style.display=\'none\'">'
        f'</div>'
    ) if img_src else ""
    return (
        f'<div class="circuit-card">'
        f'<div class="circuit-info">'
        f'<div class="circuit-flag">{flag}</div>'
        f'<div class="circuit-details">'
        f'<div class="circuit-name">{info["circuit"]}</div>'
        f'<div class="circuit-blurb">{info["blurb"]}</div>'
        f'</div>'
        f'<div class="ov-badge {info["ov_cls"]}">{info["ov"]}<br>OVERTAKING</div>'
        f'</div>'
        f'{track_section}'
        f'</div>'
    )






def render_timeline() -> str:
    steps = [
        ("01", "📅", "Select Grand Prix"),
        ("02", "⏱", "Qualifying Data Loaded"),
        ("03", "🤖", "Model Runs"),
        ("04", "🏎", "Predicted Order"),
        ("05", "🏁", "Compare Results"),
    ]
    step_html = "".join(
        f'<div class="timeline-step">'
        f'<div class="tl-num">{n}</div>'
        f'<div class="tl-dot">{ic}</div>'
        f'<div class="tl-label">{lb}</div>'
        f'</div>'
        for n, ic, lb in steps
    )
    return (
        f'<div class="timeline-outer">'
        f'<div class="timeline-line"></div>'
        f'<div class="timeline-wrap">{step_html}</div>'
        f'</div>'
    )




# F1 official Cloudinary CDN — confirmed working URLs (tested 2026-07-23)
def _f1_logo(year: str, slug: str) -> str:
    return (f"https://media.formula1.com/image/upload/f_auto/q_auto/v1"
            f"/common/f1/{year}/{slug}/{year}{slug}logo.webp")

TEAM_LOGOS: dict[str, str] = {
    "mercedes":      _f1_logo("2026", "mercedes"),
    "red bull":      _f1_logo("2026", "redbullracing"),
    "ferrari":       _f1_logo("2026", "ferrari"),
    "mclaren":       _f1_logo("2026", "mclaren"),
    "aston martin":  _f1_logo("2026", "astonmartin"),
    "alpine":        _f1_logo("2026", "alpine"),
    "williams":      _f1_logo("2026", "williams"),
    "haas":          _f1_logo("2026", "haasf1team"),
    "kick sauber":   _f1_logo("2025", "kicksauber"),
    "sauber":        _f1_logo("2025", "kicksauber"),
    "audi":          _f1_logo("2026", "audi"),
    "racing bulls":  _f1_logo("2026", "racingbulls"),
    "rb":            _f1_logo("2026", "racingbulls"),
    "alphatauri":    _f1_logo("2026", "racingbulls"),
    "visa cash app": _f1_logo("2026", "racingbulls"),
    "cadillac":      _f1_logo("2026", "cadillac"),
}

_LOGO_KEY: dict[str, str] = {
    "mercedes": "mercedes",    "red bull": "redbullracing",  "ferrari": "ferrari",
    "mclaren": "mclaren",      "aston martin": "astonmartin", "alpine": "alpine",
    "williams": "williams",    "haas": "haasf1team",          "kick sauber": "kicksauber",
    "sauber": "kicksauber",    "audi": "audi",
    "racing bulls": "racingbulls", "rb": "racingbulls",
    "alphatauri": "racingbulls",   "visa cash app": "racingbulls",
    "cadillac": "cadillac",
}


@st.cache_data(show_spinner=False)
def _fetch_logo_b64(disk_key: str, url: str) -> str:
    """Download logo from F1 CDN once, save to data/logos/, return inline base64 on all future calls."""
    cached_path = os.path.join(LOGOS_DIR, f"{disk_key}.webp")
    if os.path.exists(cached_path) and os.path.getsize(cached_path) > 100:
        with open(cached_path, "rb") as f:
            return "data:image/webp;base64," + base64.b64encode(f.read()).decode()
    try:
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "image/webp,image/*,*/*",
                "Referer": "https://www.formula1.com/",
            },
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = resp.read()
        if len(data) < 100:
            return ""
        with open(cached_path, "wb") as f:
            f.write(data)
        return "data:image/webp;base64," + base64.b64encode(data).decode()
    except Exception:
        return ""


def _team_cell(team: str) -> str:
    """Team cell: thin color bar + constructor logo + full team name."""
    key      = team.lower()
    logo_url = next((v for k, v in TEAM_LOGOS.items() if k in key), "")
    disk_key = next((v for k, v in _LOGO_KEY.items() if k in key), key.replace(" ", "_"))
    color    = team_color(team)
    bar      = (f'<div style="width:3px;border-radius:2px;align-self:stretch;'
                f'background:{color};flex-shrink:0;margin-right:10px"></div>')
    if logo_url:
        src = _fetch_logo_b64(disk_key, logo_url)
        if src:
            logo = (f'<img src="{src}" alt="{team}" '
                    f'style="height:18px;width:auto;max-width:40px;object-fit:contain;'
                    f'display:block;margin-right:9px;flex-shrink:0">')
        else:
            logo = ""
    else:
        logo = ""
    name = f'<span class="td-team-name">{team}</span>'
    return f'<div class="td-team-cell">{bar}{logo}{name}</div>'


def render_predicted_table(results_df) -> str:
    rows = []
    for _, row in results_df.sort_values("predicted_rank").iterrows():
        pred  = int(row["predicted_rank"])
        grid  = int(row["grid_position"])
        delta = grid - pred
        if delta > 0:
            delta_html = f'<span class="delta-up">&#9650;&nbsp;{delta}</span>'
        elif delta < 0:
            delta_html = f'<span class="delta-down">&#9660;&nbsp;{abs(delta)}</span>'
        else:
            delta_html = '<span class="delta-none">&#8212;</span>'
        rows.append(
            f'<tr>'
            f'<td class="td-pos {_pc(pred)}">{pred}</td>'
            f'<td><div class="td-driver-name">{row["driver"]}</div></td>'
            f'<td><div class="td-team-cell">{_team_cell(row["team"])}</div></td>'
            f'<td class="td-stat">P{grid}</td>'
            f'<td class="td-delta">{delta_html}</td>'
            f'</tr>'
        )
    return (
        '<div class="f1-table-wrap"><table class="f1-table">'
        '<thead><tr><th>POS.</th><th>DRIVER</th><th>TEAM</th>'
        '<th class="right">GRID</th><th class="right">CHANGE</th>'
        '</tr></thead>'
        f'<tbody>{"".join(rows)}</tbody></table></div>'
    )


def render_actual_comparison(results_df, actual_df) -> str:
    merged = results_df.merge(actual_df, on="driver", how="inner")
    rows = []
    for _, row in merged.sort_values("actual_position").iterrows():
        actual  = int(row["actual_position"])
        pred    = int(row["predicted_rank"])
        error   = abs(pred - actual)
        err_cls = "err-good" if error <= 2 else ("err-ok" if error <= 4 else "err-bad")
        rows.append(
            f'<tr>'
            f'<td class="td-pos {_pc(actual)}">{actual}</td>'
            f'<td><div class="td-driver-name">{row["driver"]}</div></td>'
            f'<td><div class="td-team-cell">{_team_cell(row["team"])}</div></td>'
            f'<td class="td-stat">P{pred}</td>'
            f'<td class="td-delta"><span class="err-badge {err_cls}">&#177;&thinsp;{error}</span></td>'
            f'</tr>'
        )
    return (
        '<div class="f1-table-wrap"><table class="f1-table">'
        '<thead><tr><th>POS.</th><th>DRIVER</th><th>TEAM</th>'
        '<th class="right">PREDICTED</th><th class="right">ERROR</th>'
        '</tr></thead>'
        f'<tbody>{"".join(rows)}</tbody></table></div>'
    )


def _pod_card(driver: str, team: str, rank: int, badge_text: str = "") -> str:
    color = team_color(team)
    if rank == 1:
        block_cls, num_cls, name_cls = "pod-block-1", "pod-num pod-num-1", "pod-name pod-name-1"
    elif rank == 2:
        block_cls, num_cls, name_cls = "pod-block-2", "pod-num pod-num-2", "pod-name"
    else:
        block_cls, num_cls, name_cls = "pod-block-3", "pod-num pod-num-3", "pod-name"
    vis = "visible" if badge_text else "hidden"
    badge = f'<div class="pod-winner-badge" style="visibility:{vis}">{badge_text or "&nbsp;"}</div>'
    key      = team.lower()
    logo_url = next((v for k, v in TEAM_LOGOS.items() if k in key), "")
    disk_key = next((v for k, v in _LOGO_KEY.items() if k in key), key.replace(" ", "_"))
    logo_img = ""
    if logo_url:
        src = _fetch_logo_b64(disk_key, logo_url)
        if src:
            f = "filter:brightness(0) invert(1);" if "mercedes" in key else ""
            logo_img = (f'<img src="{src}" alt="{team}" '
                        f'style="height:16px;width:auto;max-width:50px;object-fit:contain;'
                        f'display:inline-block;vertical-align:middle;margin-right:6px;{f}">')
    team_line = (f'<div class="pod-team" style="display:flex;align-items:center;'
                 f'justify-content:center;margin-top:3px;">'
                 f'{logo_img}<span style="color:{color}">{team}</span></div>')
    return (
        f'<div class="pod-card">'
        f'<div class="pod-info">{badge}'
        f'<div class="{name_cls}">{driver}</div>'
        f'{team_line}'
        f'</div>'
        f'<div class="pod-block {block_cls}" style="border-top:3px solid {color}">'
        f'<span class="{num_cls}">{rank}</span>'
        f'</div></div>'
    )


def render_podium(results_df, label: str = "PREDICTED PODIUM") -> str:
    top3 = results_df[results_df["predicted_rank"] <= 3].sort_values("predicted_rank")
    if len(top3) < 3:
        return ""
    p1, p2, p3 = (top3[top3["predicted_rank"] == i].iloc[0] for i in (1, 2, 3))
    cards = (
        _pod_card(p2["driver"], p2["team"], 2) +
        _pod_card(p1["driver"], p1["team"], 1, badge_text="PREDICTED WINNER") +
        _pod_card(p3["driver"], p3["team"], 3)
    )
    return (
        f'<div class="podium-wrap"><div class="podium-label">{label}</div>'
        f'<div class="podium-grid">{cards}</div></div>'
    )


def render_actual_podium(actual_df, results_df) -> str:
    merged = actual_df.merge(results_df[["driver", "team"]], on="driver", how="left")
    top3 = merged[merged["actual_position"] <= 3].sort_values("actual_position")
    if len(top3) < 3:
        return ""
    p1, p2, p3 = (top3[top3["actual_position"] == i].iloc[0] for i in (1, 2, 3))
    cards = (
        _pod_card(p2["driver"], p2.get("team", ""), 2) +
        _pod_card(p1["driver"], p1.get("team", ""), 1, badge_text="RACE WINNER") +
        _pod_card(p3["driver"], p3.get("team", ""), 3)
    )
    return (
        f'<div class="podium-wrap"><div class="podium-label">ACTUAL PODIUM</div>'
        f'<div class="podium-grid">{cards}</div></div>'
    )


def _status_badge(status: str) -> str:
    labels = {
        "past":               ("RACE COMPLETE",     "status-past"),
        "race_day":           ("RACE DAY",           "status-raceday"),
        "qualifying_done":    ("QUALIFYING DONE",    "status-quali"),
        "qualifying_pending": ("QUALIFYING PENDING", "status-pending"),
    }
    label, cls = labels.get(status, ("", ""))
    return f'<span class="status-badge {cls}">{label}</span>' if label else ""


# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## Settings")
    st.markdown("---")

    if st.session_state.results is not None:
        year_options = [2026]
        sb_year = st.selectbox(
            "Season", year_options,
            index=year_options.index(st.session_state.sel_year), key="sb_year",
        )
        sb_avail = get_available_races(sb_year)
        sb_race_idx = (
            sb_avail.index(st.session_state.sel_race)
            if st.session_state.sel_race in sb_avail
            else max(0, len(sb_avail) - 1)
        )
        sb_race = st.selectbox("Race", sb_avail, index=sb_race_idx, key="sb_race")
        sb_status = get_race_status(sb_year, sb_race)

        if sb_status == "qualifying_pending":
            st.warning("Qualifying hasn't happened yet — check back after Saturday.")
        else:
            if st.button("Run Prediction", type="primary", use_container_width=True, key="sb_run"):
                st.session_state.sel_year = sb_year
                st.session_state.sel_race = sb_race
                st.session_state.error = None
                with st.spinner(f"Running {sb_year} {sb_race} GP…"):
                    try:
                        results, stats = run(
                            race=sb_race, year=sb_year,
                            train_years=tuple(st.session_state.train_years),
                            force_refresh=st.session_state.force_refresh,
                        )
                        st.session_state.results   = results
                        st.session_state.stats     = stats
                        st.session_state.actual_df = load_actual_results(sb_year, sb_race)
                        st.session_state.last_race = sb_race
                        st.session_state.last_year = sb_year
                        st.session_state.collapse_sidebar = True
                    except Exception as e:
                        st.session_state.error = str(e)
                st.rerun()
        st.markdown("---")

    st.markdown("**Advanced**")
    train_years = st.multiselect(
        "Training seasons", options=[2024, 2025],
        default=st.session_state.train_years,
        help="Historical seasons used to learn circuit-specific patterns.",
        key="sb_train",
    )
    st.session_state.train_years = train_years

    force_refresh = st.checkbox(
        "Force data refresh", value=st.session_state.force_refresh,
        help="Re-download historical data from FastF1, ignoring the local cache.",
        key="sb_refresh",
    )
    st.session_state.force_refresh = force_refresh

    st.markdown("---")
    st.markdown(
        "<small style='color:#55556A'>Data via FastF1 · Pace-first ML blend</small>",
        unsafe_allow_html=True,
    )


# ── Error banner ───────────────────────────────────────────────────────────────
if st.session_state.error:
    st.error(f"Prediction failed: {st.session_state.error}")


# ── Results view ───────────────────────────────────────────────────────────────
if st.session_state.results is not None:
    results    = st.session_state.results
    stats      = st.session_state.stats
    actual_df  = st.session_state.actual_df
    race_name  = st.session_state.last_race
    race_year  = st.session_state.last_year
    has_actual = actual_df is not None and not actual_df.empty

    # Race header
    st.html(
        f'<div class="race-header">'
        f'<span class="race-eyebrow">Formula 1 &middot; {race_year} World Championship &middot; Race Prediction</span>'
        f'<div class="race-name">{race_name} <em>Grand Prix</em></div>'
        f'</div>'
    )

    circuit_html = render_circuit_card(race_name)
    if circuit_html:
        st.html(circuit_html)

    # Podium
    if has_actual:
        pod_l, pod_r = st.columns(2)
        with pod_l:
            st.html(render_podium(results))
        with pod_r:
            st.html(render_actual_podium(actual_df, results))
    else:
        st.html(render_podium(results))

    # Tabs
    tab_labels = ["Predicted", "Actual Results"] if has_actual else ["Predicted"]
    tabs = st.tabs(tab_labels)

    with tabs[0]:
        st.html('<div class="sec-header">Predicted Race Order</div>')
        st.html(render_predicted_table(results))

    if has_actual:
        with tabs[1]:
            st.html('<div class="sec-header">Actual Result &middot; Prediction Error</div>')
            st.html(render_actual_comparison(results, actual_df))

    # Caption
    n_races  = stats.get("n_races")
    spearman = stats.get("model_spearman_fin")
    dir_acc  = stats.get("directional_acc")
    if n_races:
        parts = [f"Backtest: {n_races} races"]
        if spearman: parts.append(f"Spearman ρ {spearman:.3f}")
        if dir_acc:  parts.append(f"Directional acc. {dir_acc:.0%} (movers ≥3 places)")
        st.html(f'<div class="f1-caption">{" · ".join(parts)}</div>')

    # Restore sidebar
    st.html("""<style>
    [data-testid="stSidebar"] { display: flex !important; }
    [data-testid="stSidebarCollapseButton"] { display: flex !important; }
    </style>""")

    if st.session_state.collapse_sidebar:
        st.html("""<script>
        (function() {
            var attempts = 0;
            function tryCollapse() {
                var doc = window.parent.document;
                // Check sidebar is actually open before clicking
                var sidebar = doc.querySelector('[data-testid="stSidebar"]');
                if (sidebar) {
                    var isOpen = sidebar.getAttribute('aria-expanded') !== 'false'
                                 && getComputedStyle(sidebar).display !== 'none'
                                 && sidebar.getBoundingClientRect().width > 50;
                    if (!isOpen) return true;  // already closed
                }
                // Try both known selector variants
                var btn = doc.querySelector('[data-testid="stSidebarCollapseButton"]')
                       || doc.querySelector('[data-testid="collapsedControl"]');
                if (btn) { btn.click(); return true; }
                if (++attempts < 8) setTimeout(tryCollapse, 300);
            }
            setTimeout(tryCollapse, 100);
        })();
        </script>""")
        st.session_state.collapse_sidebar = False


# ── Landing page ───────────────────────────────────────────────────────────────
else:
    # Hero
    st.html(
        '<div class="hero-wrap">'
        '<span class="hero-eyebrow">🏁 2026 Formula 1 Season</span>'
        '<div class="hero-title">🏎 F1 Race<br>Predictor</div>'
        '<p class="hero-tagline">AI-powered race predictions from qualifying performance &amp; real race pace data</p>'
        '</div>'
    )

    # Timeline
    st.html(render_timeline())

    # Race selector
    st.markdown('<div class="selector-wrap">', unsafe_allow_html=True)
    year_options = [2026]
    col_year, col_race, col_btn = st.columns([1, 2, 1])

    with col_year:
        sel_year = st.selectbox(
            "Season", year_options,
            index=year_options.index(st.session_state.sel_year), key="lp_year",
        )
        st.session_state.sel_year = sel_year

    available = get_available_races(sel_year)
    if not available:
        available = ["No races available yet"]

    with col_race:
        race_idx = (
            available.index(st.session_state.sel_race)
            if st.session_state.sel_race in available
            else max(0, len(available) - 1)
        )
        sel_race = st.selectbox("Race", available, index=race_idx, key="lp_race")
        st.session_state.sel_race = sel_race

    status = get_race_status(sel_year, sel_race) if sel_race != "No races available yet" else "future"

    with col_btn:
        st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
        run_disabled = status == "qualifying_pending"
        run_btn = st.button(
            "Generate Prediction", type="primary",
            use_container_width=True, disabled=run_disabled, key="lp_run",
        )
    st.markdown("</div>", unsafe_allow_html=True)

    # Status badge + message
    badge = _status_badge(status)
    if badge:
        st.html(badge)

    if status == "qualifying_pending":
        st.warning(
            "Qualifying for this race hasn't happened yet. "
            "The model needs qualifying results to set grid positions — "
            "come back after Saturday qualifying is complete."
        )
    elif status == "race_day":
        st.info("Race day! Qualifying results are in — prediction is based on today's grid.")
    elif status == "qualifying_done":
        st.info("Qualifying complete — race hasn't started yet. Prediction based on qualifying.")

    # Run handler
    if run_btn and not run_disabled:
        if not st.session_state.train_years:
            st.error("Select at least one training season in the sidebar.")
        else:
            st.session_state.error = None
            with st.spinner(f"Running prediction for {sel_year} {sel_race} GP…"):
                try:
                    results, stats = run(
                        race=sel_race, year=sel_year,
                        train_years=tuple(st.session_state.train_years),
                        force_refresh=st.session_state.force_refresh,
                    )
                    st.session_state.results   = results
                    st.session_state.stats     = stats
                    st.session_state.actual_df = load_actual_results(sel_year, sel_race)
                    st.session_state.last_race = sel_race
                    st.session_state.last_year = sel_year
                    st.session_state.collapse_sidebar = True
                except Exception as e:
                    st.session_state.error = str(e)
            st.rerun()

    # How it works cards
    st.html('<hr class="f1-divider">')
    st.html('<div class="sec-header" style="margin-bottom:16px">How It Works</div>')

    info_c1, info_c2 = st.columns(2)
    with info_c1:
        st.html(
            '<div class="info-card">'
            '<h4>Stage 1 — Circuit Baseline</h4>'
            '<p>Trained on 2024–2025 race history. Learns how qualifying positions translate to '
            'race finishes at each specific circuit — including track-specific overtaking tendencies. '
            'Monaco behaves very differently to Bahrain.</p>'
            '</div>'
        )
    with info_c2:
        st.html(
            '<div class="info-card">'
            '<h4>Stage 2 — In-Season Race Pace</h4>'
            '<p>Uses actual green-flag lap times from the last 4 rounds, fuel-corrected and '
            'safety-car filtered. This is real race pace — no sandbagging. '
            'Blended with grid position to produce the final prediction.</p>'
            '</div>'
        )

    st.html(
        '<div class="f1-caption" style="margin-top:20px">'
        'Prediction = pace rank (primary) + grid position (anchor) &middot; '
        'Blend weight tuned to maximise Spearman rank correlation across backtests'
        '</div>'
    )
