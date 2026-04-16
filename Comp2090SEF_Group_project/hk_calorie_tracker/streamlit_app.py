"""Streamlit frontend for HK Calorie Tracker.

This UI talks to the Flask API and does not access tracker internals directly.
"""

from __future__ import annotations

import datetime
import html as _html
import math
import os
import random
import re
from typing import Any, Callable

import altair as alt
import pandas as pd
import requests
import streamlit as st


DEFAULT_API_URL = "http://127.0.0.1:5050"

TIPS = [
    ("\U0001f966", "Eat at least 5 servings of fruits & veggies daily for optimal health."),
    ("\U0001f3c3", "30 minutes of moderate exercise burns ~200-300 calories."),
    ("\U0001f4a7", "Drinking water before meals can reduce calorie intake by 13%."),
    ("\U0001f634", "Poor sleep increases hunger hormones \u2014 aim for 7-9 hours."),
    ("\U0001f373", "High-protein breakfasts keep you fuller for longer."),
    ("\u23f0", "Eating dinner 2-3 hours before bed improves digestion."),
    ("\U0001f9d8", "Stress raises cortisol, which promotes fat storage. Try meditation."),
    ("\U0001f957", "Fill half your plate with vegetables at every meal."),
    ("\U0001f6b6", "Walking 10,000 steps = ~400-500 calories burned per day."),
    ("\U0001f375", "Green tea can boost metabolism by 3-4% through thermogenesis."),
]

EXERCISE_PRESETS = {
    "\U0001f3c3 Running (30 min)": 300,
    "\U0001f6b6 Walking (30 min)": 150,
    "\U0001f3ca Swimming (30 min)": 250,
    "\U0001f6b4 Cycling (30 min)": 280,
    "\U0001f9d8 Yoga (30 min)": 120,
    "\U0001f4aa Weight Training (30 min)": 200,
    "\U0001f938 HIIT (20 min)": 250,
    "\U0001f3c0 Basketball (30 min)": 260,
    "\u26bd Football (30 min)": 270,
    "\U0001f3be Tennis (30 min)": 230,
}


def inject_styles() -> None:
    st.markdown(
        """
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=Playfair+Display:wght@500;700&display=swap');

            :root {
                --bg: #0a0a0f;
                --panel: rgba(255,255,255,0.04);
                --panel-solid: #141419;
                --ink: #f0f0f5;
                --ink-secondary: #a0a0b0;
                --accent: #ff6b35;
                --accent-glow: rgba(255,107,53,0.25);
                --accent-2: #00d4aa;
                --accent-2-glow: rgba(0,212,170,0.2);
                --accent-3: #6c5ce7;
                --accent-3-glow: rgba(108,92,231,0.2);
                --blue: #3b82f6;
                --blue-glow: rgba(59,130,246,0.2);
                --muted: #6b6b80;
                --border: rgba(255,255,255,0.08);
                --border-hover: rgba(255,255,255,0.15);
                --radius: 16px;
                --radius-sm: 10px;
                --radius-lg: 24px;
            }

            .stApp {
                background:
                    radial-gradient(ellipse at 15% 10%, rgba(255,107,53,0.08), transparent 40%),
                    radial-gradient(ellipse at 85% 5%, rgba(0,212,170,0.06), transparent 35%),
                    radial-gradient(ellipse at 50% 90%, rgba(108,92,231,0.05), transparent 40%),
                    linear-gradient(160deg, #0a0a0f 0%, #101018 50%, #0d0d14 100%);
                color: var(--ink);
                font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
                -webkit-font-smoothing: antialiased;
            }

            h1, h2, h3 { font-family: 'Playfair Display', Georgia, serif; color: var(--ink); letter-spacing: -0.01em; }
            h1 { font-weight: 700; } h2 { font-weight: 600; font-size: 1.5rem; } h3 { font-weight: 500; }
            p, span, label, div { letter-spacing: 0.01em; }

            .hero {
                background: linear-gradient(135deg, rgba(255,255,255,0.05) 0%, rgba(255,255,255,0.02) 100%);
                backdrop-filter: blur(20px); border: 1px solid var(--border);
                border-radius: var(--radius-lg); padding: 1.8rem 2rem;
                box-shadow: 0 20px 60px rgba(0,0,0,0.3), inset 0 1px 0 rgba(255,255,255,0.06);
                margin-bottom: 1.2rem; position: relative; overflow: hidden;
            }
            .hero::before {
                content: ''; position: absolute; top: 0; right: 0;
                width: 200px; height: 200px;
                background: radial-gradient(circle, var(--accent-glow), transparent 70%);
                opacity: 0.4; border-radius: 50%; transform: translate(30%, -30%);
            }

            .stat-card {
                background: linear-gradient(145deg, rgba(255,255,255,0.06), rgba(255,255,255,0.02));
                backdrop-filter: blur(12px); border: 1px solid var(--border);
                border-radius: var(--radius); padding: 1.1rem 1.3rem;
                box-shadow: 0 8px 32px rgba(0,0,0,0.2);
                transition: all 0.3s cubic-bezier(0.4,0,0.2,1); overflow: hidden;
            }
            .stat-card:hover { border-color: var(--border-hover); transform: translateY(-2px); box-shadow: 0 12px 40px rgba(0,0,0,0.3); }
            .stat-card .stat-icon { font-size: 1.5rem; margin-bottom: 0.5rem; display: inline-block; }
            .stat-card .stat-label { color: var(--muted); font-size: 0.72rem; font-weight: 500; letter-spacing: 0.06em; text-transform: uppercase; margin-bottom: 0.2rem; }
            .stat-card .stat-value { font-family: 'Inter', sans-serif; font-size: 1.5rem; font-weight: 800; color: var(--ink); letter-spacing: -0.02em; }

            .status-panel {
                background: linear-gradient(145deg, rgba(255,255,255,0.05), rgba(255,255,255,0.02));
                border: 1px solid var(--border); border-radius: var(--radius);
                padding: 0.9rem; margin: 0.8rem 0 1rem;
            }
            .status-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 0.65rem; }
            .status-chip {
                background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.06);
                border-radius: 12px; padding: 0.7rem 0.8rem; min-height: 84px;
            }
            .status-top {
                display: flex; align-items: center; justify-content: space-between;
                gap: 0.5rem; margin-bottom: 0.35rem;
            }
            .status-name {
                color: var(--muted); font-size: 0.68rem; font-weight: 600;
                letter-spacing: 0.08em; text-transform: uppercase;
            }
            .status-value { color: var(--ink); font-size: 1rem; font-weight: 700; line-height: 1.2; }
            .status-detail { color: var(--ink-secondary); font-size: 0.74rem; line-height: 1.4; }

            .progress-container {
                background: linear-gradient(145deg, rgba(255,255,255,0.06), rgba(255,255,255,0.02));
                backdrop-filter: blur(12px); border: 1px solid var(--border);
                border-radius: var(--radius); padding: 1.2rem;
            }
            .progress-bar-track { width: 100%; height: 10px; background: rgba(255,255,255,0.06); border-radius: 5px; overflow: hidden; margin: 0.6rem 0; }
            .progress-bar-fill { height: 100%; border-radius: 5px; transition: width 0.6s cubic-bezier(0.4,0,0.2,1); }

            .theme-divider { height: 1px; background: linear-gradient(90deg, transparent, var(--border), transparent); margin: 1.5rem 0; }

            [data-testid="stSidebar"] { background: linear-gradient(180deg, #111118 0%, #0d0d14 100%); border-right: 1px solid var(--border); }
            [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
            [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h2,
            [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h3,
            [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h4,
            [data-testid="stSidebar"] label, [data-testid="stSidebar"] .stMarkdown,
            [data-testid="stSidebar"] span, [data-testid="stSidebar"] div { color: #e0e0e8 !important; }
            [data-testid="stSidebar"] button { color: #ffffff !important; }
            [data-testid="stSidebar"] [data-testid="stSelectbox"] span,
            [data-testid="stSidebar"] [data-testid="stSelectbox"] input,
            [data-testid="stSidebar"] [data-testid="stSelectbox"] div[data-baseweb="select"] span { color: #ffffff !important; }
            [data-testid="stSidebar"] [data-testid="stTextInput"] input { color: #ffffff !important; }

            .sidebar-badge {
                background: linear-gradient(135deg, rgba(255,107,53,0.12), rgba(0,212,170,0.08));
                border: 1px solid rgba(255,107,53,0.2); border-radius: var(--radius-sm);
                padding: 0.8rem 1rem; margin-bottom: 1rem;
            }
            .sidebar-badge .badge-name { font-family: 'Playfair Display', serif; font-size: 1.2rem; font-weight: 700; color: var(--ink); }
            .sidebar-badge .badge-sub { color: var(--muted); font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.1em; margin-top: 0.15rem; }

            .entry-row {
                display: flex; align-items: center; justify-content: space-between;
                background: rgba(255,255,255,0.03); border: 1px solid var(--border);
                border-radius: var(--radius-sm); padding: 0.6rem 1rem;
                margin-bottom: 0.4rem; transition: background 0.2s;
            }
            .entry-row:hover { background: rgba(255,255,255,0.06); }
            .entry-name { color: var(--ink); font-weight: 500; flex: 2; }
            .entry-qty { color: var(--accent); font-weight: 600; flex: 0.5; text-align: center; }
            .entry-cal { color: var(--accent-2); font-weight: 700; flex: 1; text-align: right; }

            .login-logo {
                width: 52px; height: 52px;
                background: linear-gradient(135deg, var(--accent), var(--accent-2));
                border-radius: 14px; display: inline-flex; align-items: center; justify-content: center;
                font-size: 1.6rem; margin: 0 auto 0.5rem;
                box-shadow: 0 8px 28px var(--accent-glow);
            }
            .login-title { font-family: 'Playfair Display', serif; font-size: 1.6rem; font-weight: 700; color: var(--ink); margin: 0 0 0.1rem; text-align: center; }
            .login-subtitle { color: var(--muted); font-size: 0.78rem; text-align: center; margin: 0 0 0.6rem; }
            .login-features { display: flex; justify-content: center; gap: 1rem; margin-top: 0.6rem; flex-wrap: wrap; }
            .login-feature { display: flex; align-items: center; gap: 0.4rem; color: var(--ink-secondary); font-size: 0.75rem; }
            .login-feature-icon {
                width: 26px; height: 26px; background: rgba(255,255,255,0.05);
                border: 1px solid var(--border); border-radius: 7px;
                display: flex; align-items: center; justify-content: center; font-size: 0.8rem;
            }

            .calorie-ring-wrap {
                display: flex; align-items: center; gap: 2rem;
                background: linear-gradient(145deg, rgba(255,255,255,0.06), rgba(255,255,255,0.02));
                backdrop-filter: blur(12px); border: 1px solid var(--border);
                border-radius: var(--radius-lg); padding: 1.5rem 1.8rem; margin-bottom: 1rem;
            }
            .calorie-ring { position: relative; width: 140px; height: 140px; flex-shrink: 0; }
            .calorie-ring svg { transform: rotate(-90deg); }
            .calorie-ring-label { position: absolute; inset: 0; display: flex; flex-direction: column; align-items: center; justify-content: center; }
            .calorie-ring-label .ring-value { font-size: 1.5rem; font-weight: 800; color: var(--ink); line-height: 1; }
            .calorie-ring-label .ring-unit { font-size: 0.65rem; color: var(--muted); text-transform: uppercase; letter-spacing: 0.08em; margin-top: 0.2rem; }
            .calorie-ring-details { flex: 1; }
            .calorie-ring-details .ring-row { display: flex; justify-content: space-between; align-items: center; padding: 0.4rem 0; border-bottom: 1px solid var(--border); }
            .calorie-ring-details .ring-row:last-child { border-bottom: none; }
            .ring-row-label { display: flex; align-items: center; gap: 0.5rem; color: var(--ink-secondary); font-size: 0.82rem; }
            .ring-row-label .dot { width: 8px; height: 8px; border-radius: 50%; display: inline-block; }
            .ring-row-value { font-weight: 700; color: var(--ink); font-size: 0.92rem; }

            .water-visual { display: flex; gap: 0.35rem; flex-wrap: wrap; margin: 0.6rem 0; }
            .water-glass { font-size: 1.4rem; opacity: 0.25; transition: all 0.3s; }
            .water-glass.filled { opacity: 1; filter: drop-shadow(0 0 4px rgba(59,130,246,0.4)); }

            .section-head { display: flex; align-items: center; gap: 0.6rem; margin: 0.3rem 0 0.8rem; }
            .section-head .sh-icon { width: 34px; height: 34px; border-radius: 10px; display: flex; align-items: center; justify-content: center; font-size: 1rem; }
            .section-head .sh-text { font-family: 'Playfair Display', serif; font-size: 1.2rem; font-weight: 600; color: var(--ink); }

            .motivation-banner {
                background: linear-gradient(135deg, rgba(108,92,231,0.1), rgba(0,212,170,0.06));
                border: 1px solid rgba(108,92,231,0.18); border-radius: var(--radius);
                padding: 0.9rem 1.2rem; display: flex; align-items: center; gap: 0.8rem; margin-bottom: 1rem;
            }
            .motivation-banner .mb-icon { font-size: 1.6rem; flex-shrink: 0; }
            .motivation-banner .mb-text { color: var(--ink-secondary); font-size: 0.82rem; line-height: 1.5; }
            .motivation-banner .mb-label { font-size: 0.65rem; color: var(--accent-3); text-transform: uppercase; letter-spacing: 0.1em; font-weight: 600; margin-bottom: 0.15rem; }

            .macro-wrap { display: flex; gap: 0.8rem; margin: 0.5rem 0 1rem; }
            .macro-item { flex: 1; background: rgba(255,255,255,0.03); border: 1px solid var(--border); border-radius: var(--radius-sm); padding: 0.7rem; text-align: center; }
            .macro-item .mi-label { font-size: 0.65rem; color: var(--muted); text-transform: uppercase; letter-spacing: 0.06em; }
            .macro-item .mi-value { font-size: 1.1rem; font-weight: 700; color: var(--ink); margin: 0.2rem 0; }
            .macro-item .mi-bar { height: 4px; border-radius: 2px; background: rgba(255,255,255,0.06); overflow: hidden; }
            .macro-item .mi-fill { height: 100%; border-radius: 2px; }

            .exercise-entry {
                display: flex; align-items: center; justify-content: space-between;
                background: rgba(255,255,255,0.03); border: 1px solid var(--border);
                border-radius: var(--radius-sm); padding: 0.55rem 1rem; margin-bottom: 0.35rem;
            }
            .exercise-entry .ex-name { color: var(--ink); font-weight: 500; flex: 2; }
            .exercise-entry .ex-dur { color: var(--accent-3); font-weight: 600; flex: 0.7; text-align: center; font-size: 0.85rem; }
            .exercise-entry .ex-cal { color: #e74c3c; font-weight: 700; flex: 1; text-align: right; }

            .insight-card {
                background: linear-gradient(145deg, rgba(255,255,255,0.05), rgba(255,255,255,0.02));
                border: 1px solid var(--border); border-radius: var(--radius); padding: 1rem 1.2rem;
            }
            .insight-card .ic-label { font-size: 0.7rem; color: var(--muted); text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 0.3rem; }
            .insight-card .ic-value { font-size: 1.3rem; font-weight: 800; color: var(--ink); }
            .insight-card .ic-sub { font-size: 0.75rem; color: var(--ink-secondary); margin-top: 0.2rem; }

            .stButton > button {
                background: linear-gradient(135deg, var(--accent) 0%, #e85d2c 100%) !important;
                color: #fff !important; border: none !important; border-radius: var(--radius-sm) !important;
                font-weight: 600 !important; font-size: 0.88rem !important;
                padding: 0.5rem 1.2rem !important;
                transition: all 0.25s cubic-bezier(0.4,0,0.2,1) !important;
                box-shadow: 0 4px 15px var(--accent-glow) !important;
            }
            .stButton > button:hover { transform: translateY(-1px) !important; box-shadow: 0 8px 25px var(--accent-glow) !important; filter: brightness(1.1) !important; }
            .stButton > button:active { transform: translateY(0) !important; }
            .stFormSubmitButton > button { background: linear-gradient(135deg, var(--accent-2) 0%, #00b894 100%) !important; box-shadow: 0 4px 15px var(--accent-2-glow) !important; }
            .stFormSubmitButton > button:hover { box-shadow: 0 8px 25px var(--accent-2-glow) !important; }

            [data-testid="stTextInput"] input, [data-testid="stNumberInput"] input {
                background: rgba(255,255,255,0.04) !important; border: 1px solid var(--border) !important;
                border-radius: var(--radius-sm) !important; color: var(--ink) !important;
            }
            [data-testid="stTextInput"] input:focus, [data-testid="stNumberInput"] input:focus {
                border-color: var(--accent) !important; box-shadow: 0 0 0 2px var(--accent-glow) !important;
            }

            [data-testid="stSelectbox"] > div > div {
                background: rgba(255,255,255,0.04) !important; border: 1px solid var(--border) !important;
                border-radius: var(--radius-sm) !important; cursor: pointer !important; color: #ffffff !important;
            }
            [data-testid="stSelectbox"] input { caret-color: transparent !important; cursor: pointer !important; color: #ffffff !important; }
            [data-testid="stSelectbox"] span, [data-testid="stSelectbox"] div[data-baseweb="select"] span { color: #ffffff !important; }
            [data-baseweb="menu"] li, [data-baseweb="menu"] [role="option"] { color: #ffffff !important; }

            .stTabs [data-baseweb="tab-list"] { gap: 0.4rem; }
            .stTabs [data-baseweb="tab"] { background: transparent; border-radius: var(--radius-sm); padding: 0.45rem 1rem; color: var(--muted); font-weight: 500; }
            .stTabs [aria-selected="true"] { background: rgba(255,107,53,0.12) !important; color: var(--accent) !important; }

            .streamlit-expanderHeader { background: rgba(255,255,255,0.03) !important; border-radius: var(--radius-sm) !important; border: 1px solid var(--border) !important; }
            [data-testid="stMetric"] { background: var(--panel); border: 1px solid var(--border); border-radius: var(--radius-sm); padding: 0.8rem; }
            [data-testid="stMetricValue"] { color: var(--accent-2) !important; font-weight: 800 !important; }
            [data-testid="stDataFrame"] { border: 1px solid var(--border) !important; border-radius: var(--radius-sm) !important; overflow: hidden !important; }

            @keyframes fadeUp { from { opacity: 0; transform: translateY(12px); } to { opacity: 1; transform: translateY(0); } }
            .hero, .stat-card, .progress-container, .entry-row, .motivation-banner { animation: fadeUp 0.5s cubic-bezier(0.4,0,0.2,1) both; }
            .stat-card:nth-child(2) { animation-delay: 0.05s; }
            .stat-card:nth-child(3) { animation-delay: 0.1s; }
            .stat-card:nth-child(4) { animation-delay: 0.15s; }

            .chat-container { max-height: 420px; overflow-y: auto; padding: 0.5rem; display: flex; flex-direction: column; gap: 0.6rem; }
            .chat-msg { padding: 0.7rem 1rem; border-radius: var(--radius-sm); max-width: 85%; animation: fadeUp 0.3s ease; line-height: 1.5; font-size: 0.88rem; }
            .chat-user { background: linear-gradient(135deg, rgba(255,107,53,0.15), rgba(255,107,53,0.08)); border: 1px solid rgba(255,107,53,0.2); align-self: flex-end; color: var(--ink); }
            .chat-bot { background: linear-gradient(135deg, rgba(0,212,170,0.1), rgba(108,92,231,0.08)); border: 1px solid rgba(0,212,170,0.15); align-self: flex-start; color: var(--ink-secondary); }
            .chat-bot strong { color: var(--ink); }
            .rec-card { background: linear-gradient(145deg, rgba(255,255,255,0.05), rgba(255,255,255,0.02)); border: 1px solid var(--border); border-radius: var(--radius); padding: 1rem 1.2rem; margin-bottom: 0.5rem; }
            .rec-card .rc-icon { font-size: 1.4rem; margin-bottom: 0.4rem; }
            .rec-card .rc-title { font-weight: 700; color: var(--ink); font-size: 0.9rem; margin-bottom: 0.3rem; }
            .rec-card .rc-text { color: var(--ink-secondary); font-size: 0.8rem; line-height: 1.5; }
            .rec-card .rc-tag { display: inline-block; font-size: 0.65rem; padding: 0.15rem 0.5rem; border-radius: 20px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.04em; margin-top: 0.4rem; }

            @media (max-width: 768px) {
                .hero { padding: 1.2rem; border-radius: var(--radius); }
                .stat-card { padding: 0.8rem; }
                .calorie-ring-wrap { flex-direction: column; text-align: center; }
                .macro-wrap { flex-direction: column; }
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def api_call(method: str, path: str, base_url: str, payload: dict | None = None) -> dict:
    url = f"{base_url.rstrip('/')}{path}"
    response = requests.request(method=method, url=url, json=payload, timeout=8)
    response.raise_for_status()
    return response.json()


def run_api_action(
    action: Callable[[], Any],
    *,
    success_message: str | None = None,
    error_prefix: str = "Error",
    on_success: Callable[[Any], None] | None = None,
    rerun: bool = True,
) -> Any | None:
    try:
        result = action()
    except requests.RequestException as err:
        st.error(f"{error_prefix}: {err}")
        return None

    if on_success is not None:
        on_success(result)
    if success_message:
        st.success(success_message)
    if rerun:
        st.rerun()
    return result


def render_stat_card(label: str, value: str, icon: str = "") -> None:
    icon_html = f'<div class="stat-icon">{icon}</div>' if icon else ""
    st.markdown(f'<div class="stat-card">{icon_html}<div class="stat-label">{label}</div><div class="stat-value">{value}</div></div>', unsafe_allow_html=True)


def render_progress_bar(current: int, goal: int) -> None:
    pct = min(100, int((current / goal) * 100)) if goal > 0 else 0
    remaining = max(0, goal - current)
    if pct >= 100:
        color, status = "#e74c3c", "Over goal"
    elif pct >= 75:
        color, status = "#f39c12", "Almost there"
    else:
        color, status = "#00d4aa", f"{remaining} kcal left"
    st.markdown(f"""<div class="progress-container">
        <div style="display:flex; justify-content:space-between; align-items:baseline; margin-bottom:0.2rem;">
            <span style="color:#a0a0b0; font-size:0.75rem; text-transform:uppercase; letter-spacing:0.06em; font-weight:500;">Daily Progress</span>
            <span style="color:{color}; font-weight:700; font-size:1.05rem;">{pct}%</span>
        </div>
        <div class="progress-bar-track"><div class="progress-bar-fill" style="width:{pct}%; background:linear-gradient(90deg, {color}, {color}dd);"></div></div>
        <div style="display:flex; justify-content:space-between; margin-top:0.3rem;">
            <span style="color:#6b6b80; font-size:0.75rem;">{current} / {goal} kcal</span>
            <span style="color:{color}; font-size:0.75rem; font-weight:500;">{status}</span>
        </div>
    </div>""", unsafe_allow_html=True)


def render_calorie_ring(eaten: int, goal: int, remaining: int, burned: int = 0) -> None:
    pct = min(100, int((eaten / goal) * 100)) if goal > 0 else 0
    stroke_color = "#00d4aa" if pct < 75 else ("#f39c12" if pct < 100 else "#e74c3c")
    circumference = 2 * math.pi * 56
    offset = circumference * (1 - pct / 100)
    st.markdown(f"""<div class="calorie-ring-wrap">
        <div class="calorie-ring">
            <svg viewBox="0 0 128 128" width="140" height="140">
                <circle cx="64" cy="64" r="56" fill="none" stroke="rgba(255,255,255,0.06)" stroke-width="10"/>
                <circle cx="64" cy="64" r="56" fill="none" stroke="{stroke_color}" stroke-width="10"
                    stroke-dasharray="{circumference}" stroke-dashoffset="{offset}"
                    stroke-linecap="round" style="transition: stroke-dashoffset 0.8s cubic-bezier(.4,0,.2,1);"/>
            </svg>
            <div class="calorie-ring-label"><span class="ring-value">{remaining}</span><span class="ring-unit">remaining</span></div>
        </div>
        <div class="calorie-ring-details">
            <div class="ring-row"><span class="ring-row-label"><span class="dot" style="background:#6c5ce7;"></span>Goal</span><span class="ring-row-value">{goal}</span></div>
            <div class="ring-row"><span class="ring-row-label"><span class="dot" style="background:{stroke_color};"></span>Food</span><span class="ring-row-value">{eaten}</span></div>
            <div class="ring-row"><span class="ring-row-label"><span class="dot" style="background:#e74c3c;"></span>Exercise</span><span class="ring-row-value">-{burned}</span></div>
            <div class="ring-row" style="border-bottom:none; padding-top:0.5rem;"><span class="ring-row-label" style="font-weight:600; color:var(--ink);">Net</span><span class="ring-row-value" style="color:{stroke_color}; font-size:1.05rem;">{remaining}</span></div>
        </div>
    </div>""", unsafe_allow_html=True)


def render_water_visual(intake: int, goal: int) -> None:
    glasses_html = "".join(f'<span class="water-glass {"filled" if i < intake else ""}">\U0001f4a7</span>' for i in range(goal))
    pct = min(100, int((intake / goal) * 100)) if goal > 0 else 0
    st.markdown(f"""<div class="progress-container">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.4rem;">
            <span style="color:var(--ink); font-weight:600; font-size:0.9rem;">\U0001f4a7 Water Intake</span>
            <span style="color:#3b82f6; font-weight:700; font-size:1.05rem;">{intake}/{goal}</span>
        </div>
        <div class="water-visual">{glasses_html}</div>
        <div class="progress-bar-track" style="margin-top:0.5rem;"><div class="progress-bar-fill" style="width:{pct}%; background:linear-gradient(90deg, #3b82f6, #60a5fa);"></div></div>
        <div style="text-align:right; margin-top:0.2rem;"><span style="color:#6b6b80; font-size:0.72rem;">{pct}% of daily goal</span></div>
    </div>""", unsafe_allow_html=True)


def render_section_header(icon: str, text: str, bg_color: str = "rgba(255,107,53,0.12)") -> None:
    st.markdown(f'<div class="section-head"><div class="sh-icon" style="background:{bg_color};">{icon}</div><div class="sh-text">{text}</div></div>', unsafe_allow_html=True)


def render_macro_bars(calories: int) -> None:
    protein_g = int(calories * 0.30 / 4)
    carbs_g = int(calories * 0.45 / 4)
    fat_g = int(calories * 0.25 / 9)
    protein_pct = min(100, int(protein_g / 150 * 100)) if calories > 0 else 0
    carbs_pct = min(100, int(carbs_g / 300 * 100)) if calories > 0 else 0
    fat_pct = min(100, int(fat_g / 70 * 100)) if calories > 0 else 0
    st.markdown(f"""<div class="macro-wrap">
        <div class="macro-item"><div class="mi-label">Protein</div><div class="mi-value">{protein_g}g</div><div class="mi-bar"><div class="mi-fill" style="width:{protein_pct}%; background:linear-gradient(90deg, #6c5ce7, #a29bfe);"></div></div></div>
        <div class="macro-item"><div class="mi-label">Carbs</div><div class="mi-value">{carbs_g}g</div><div class="mi-bar"><div class="mi-fill" style="width:{carbs_pct}%; background:linear-gradient(90deg, #00d4aa, #55efc4);"></div></div></div>
        <div class="macro-item"><div class="mi-label">Fat</div><div class="mi-value">{fat_g}g</div><div class="mi-bar"><div class="mi-fill" style="width:{fat_pct}%; background:linear-gradient(90deg, #ff6b35, #fdcb6e);"></div></div></div>
    </div>""", unsafe_allow_html=True)


def render_motivation_banner() -> None:
    day_index = datetime.date.today().toordinal() % len(TIPS)
    icon, text = TIPS[day_index]
    st.markdown(f"""<div class="motivation-banner">
        <div class="mb-icon">{icon}</div>
        <div><div class="mb-label">Daily Tip</div><div class="mb-text">{text}</div></div>
    </div>""", unsafe_allow_html=True)


def build_daily_summary_text(user: dict, log_data: dict, goal_value: int, water_intake: int, water_goal: int, exercise_burned: int, exercises: list[dict]) -> str:
    entries = log_data.get("entries", [])
    lines = [
        f"HK Calorie Tracker Daily Summary - {datetime.date.today().isoformat()}",
        "",
        f"Profile: {user.get('name', 'Unknown')}",
        f"Goal: {user.get('goal', 'Maintain')}",
        f"Calories: {log_data.get('total_calories', 0)} / {goal_value} kcal",
        f"Exercise burned: {exercise_burned} kcal",
        f"Water: {water_intake} / {water_goal} glasses",
        "",
        "Meals logged:",
    ]

    if entries:
        for entry in entries:
            lines.append(
                f"- {entry.get('meal', 'General')}: {entry.get('food_name', 'Unknown')} x{entry.get('quantity', 1)} ({entry.get('total_calories', 0)} kcal)"
            )
    else:
        lines.append("- No food logged today")

    lines.extend(["", "Exercises logged:"])
    if exercises:
        for exercise in exercises:
            lines.append(
                f"- {exercise.get('name', 'Exercise')} for {exercise.get('duration_min', 0)} min ({exercise.get('calories_burned', 0)} kcal)"
            )
    else:
        lines.append("- No exercise logged today")

    return "\n".join(lines)


def build_weekly_history_csv(history: list[int], goal_value: int) -> str:
    day_labels = [
        (datetime.date.today() - datetime.timedelta(days=len(history) - 1 - index)).isoformat()
        for index in range(len(history))
    ]
    history_df = pd.DataFrame({"date": day_labels, "calories": history})
    history_df["status"] = history_df["calories"].apply(
        lambda calories: "Over" if calories > goal_value else ("On Track" if calories > 0 else "Rest")
    )
    return history_df.to_csv(index=False)


def generate_recommendations(calorie_status: int, goal_value: int, water_intake: int, water_goal: int, exercise_burned: int, history: list[int], user: dict) -> list[dict]:
    recs = []
    goal = user.get("goal", "Maintain")
    pct = int(calorie_status / goal_value * 100) if goal_value > 0 else 0
    avg_cal = sum(history) / len(history) if history else 0

    # Calorie-based
    if pct == 0:
        recs.append({"icon": "\U0001f373", "title": "Time to eat!", "text": "You haven't logged any food yet today. Start with a healthy breakfast to fuel your morning.", "tag": "Nutrition", "color": "#ff6b35"})
    elif pct > 100:
        over = calorie_status - goal_value
        recs.append({"icon": "\u26a0\ufe0f", "title": f"Over by {over} kcal", "text": f"You've exceeded your goal. Try a 30-min walk (~150 kcal) or light jog (~300 kcal) to balance it out.", "tag": "Alert", "color": "#e74c3c"})
    elif pct > 85:
        recs.append({"icon": "\U0001f3af", "title": "Almost at your limit", "text": f"You're at {pct}% of your goal. Choose a light snack like fruits or veggies if you're still hungry.", "tag": "Nutrition", "color": "#f39c12"})
    elif 40 <= pct <= 60:
        recs.append({"icon": "\u2705", "title": "Great pacing!", "text": "You're right on track for the day. Keep maintaining this balance through your next meal.", "tag": "Positive", "color": "#00d4aa"})

    # Water
    water_pct = int(water_intake / water_goal * 100) if water_goal > 0 else 0
    if water_pct < 50:
        recs.append({"icon": "\U0001f4a7", "title": "Drink more water", "text": f"You're only at {water_intake}/{water_goal} glasses. Dehydration can be mistaken for hunger \u2014 grab a glass now!", "tag": "Hydration", "color": "#3b82f6"})
    elif water_pct >= 100:
        recs.append({"icon": "\U0001f4a7", "title": "Hydration goal met!", "text": "Excellent work staying hydrated today. Proper hydration boosts metabolism by up to 30%.", "tag": "Positive", "color": "#00d4aa"})

    # Exercise
    if exercise_burned == 0 and calorie_status > 0:
        recs.append({"icon": "\U0001f3c3", "title": "Add some movement", "text": "No exercise logged today. Even a 15-min walk after meals aids digestion and burns ~75 kcal.", "tag": "Exercise", "color": "#6c5ce7"})
    elif exercise_burned > 300:
        recs.append({"icon": "\U0001f4aa", "title": "Great workout!", "text": f"You've burned {exercise_burned} kcal through exercise. Make sure to refuel with protein-rich foods for recovery.", "tag": "Positive", "color": "#00d4aa"})

    # Goal-specific
    if goal == "Lose" and avg_cal > goal_value * 1.1 and len(history) >= 3:
        recs.append({"icon": "\U0001f4c9", "title": "Trending above target", "text": f"Your 7-day average ({avg_cal:.0f} kcal) exceeds your goal by {avg_cal - goal_value:.0f} kcal. Try meal prepping to stay consistent.", "tag": "Trend", "color": "#e74c3c"})
    elif goal == "Gain" and avg_cal < goal_value * 0.9 and len(history) >= 3:
        recs.append({"icon": "\U0001f4c8", "title": "Eat more to reach your goal", "text": f"Your average ({avg_cal:.0f} kcal) is below target. Add calorie-dense foods like nuts, avocado, or rice.", "tag": "Trend", "color": "#f39c12"})

    # Consistency
    if len(history) >= 5:
        on_target = sum(1 for h in history if 0 < h <= goal_value)
        if on_target / len(history) >= 0.7:
            recs.append({"icon": "\U0001f525", "title": "Consistency champion!", "text": f"You've been on target {on_target}/{len(history)} days this week. Keep this momentum going!", "tag": "Positive", "color": "#00d4aa"})

    if not recs:
        recs.append({"icon": "\U0001f31f", "title": "Looking good!", "text": "Keep tracking your meals and exercise. Consistency is the key to reaching your goals.", "tag": "General", "color": "#6c5ce7"})

    return recs


def get_chatbot_response(message: str, calorie_status: int, goal_value: int, water_intake: int, water_goal: int, exercise_burned: int, exercises: list, user: dict, foods: list[dict], log_entries: list[dict]) -> str:
    msg = message.lower().strip()
    name = user.get("name", "there")
    remaining = max(0, goal_value - calorie_status + exercise_burned)
    goal = user.get("goal", "Maintain")

    # Greetings
    if any(w in msg for w in ["hi", "hello", "hey", "sup"]):
        return f"Hey {name}! \U0001f44b I'm your nutrition assistant. Ask me about your calories, water, exercise, or food suggestions!"

    # Calorie queries
    if any(w in msg for w in ["calorie", "eaten", "consumed", "how much", "intake"]):
        if calorie_status == 0:
            return f"You haven't logged any food yet today. Your daily goal is **{goal_value} kcal**. Start tracking to stay on top of your nutrition!"
        return f"You've eaten **{calorie_status} kcal** out of your **{goal_value} kcal** goal. That's **{remaining} kcal** remaining (after accounting for {exercise_burned} kcal burned from exercise)."

    # Remaining
    if any(w in msg for w in ["remaining", "left", "budget"]):
        return f"You have **{remaining} kcal** remaining today. {'You\'re doing great \u2014 stay mindful with your next meal!' if remaining > 200 else 'You\'re close to your limit \u2014 opt for lighter options like salad or soup.'}"

    # Water
    if any(w in msg for w in ["water", "hydrat", "drink", "glass"]):
        return f"You've had **{water_intake}/{water_goal} glasses** of water today. {'Great hydration! \U0001f4a7' if water_intake >= water_goal else f'Try to drink {water_goal - water_intake} more glasses before the day ends.'}"

    # Exercise
    if any(w in msg for w in ["exercise", "workout", "burn", "active", "gym"]):
        if not exercises:
            return "No exercises logged today. Try adding a 30-min walk (150 kcal), jog (300 kcal), or yoga session (120 kcal) to boost your day!"
        ex_list = ", ".join(f"{e['name']} (-{e['calories_burned']} kcal)" for e in exercises)
        return f"Today's exercise: {ex_list}. Total burned: **{exercise_burned} kcal**. {'Amazing effort! \U0001f4aa' if exercise_burned > 200 else 'Every bit counts!'}"

    # Protein and macros
    if any(w in msg for w in ["protein", "macro", "macros", "carb", "fat intake"]):
        protein_target = max(60, int(user.get("weight", 70) * 1.6))
        return f"For general fitness, a solid protein target is around **{protein_target} g/day** based on your profile. Keep most meals balanced with protein, slow carbs, and healthy fats. Good options include eggs, chicken rice with extra lean meat, tofu, fish, Greek yogurt, oats, and fruit."

    # Recovery and sleep
    if any(w in msg for w in ["recovery", "recover", "sleep", "rest day", "sore"]):
        return "Recovery matters as much as training. Aim for **7-9 hours of sleep**, drink enough water, and include protein after exercise. If you're sore, go for light walking, mobility work, and avoid stacking intense sessions on consecutive days unless you're already adapted to it."

    # Weight loss / muscle gain guidance
    if any(w in msg for w in ["lose fat", "weight loss", "cut", "gain muscle", "bulk", "maintain muscle"]):
        if goal == "Lose":
            return "Because your goal is **Lose**, focus on a moderate calorie deficit, high-protein meals, daily steps, and strength training 2-4 times per week so you keep muscle while dropping fat."
        if goal == "Gain":
            return "Because your goal is **Gain**, aim for a small calorie surplus, regular strength training, and protein spread across the day. Consistency usually beats trying to force huge calorie jumps."
        return "For body recomposition, keep calories close to maintenance, prioritize protein, and train consistently. Small, repeatable habits work better than aggressive cuts or bulks."

    # Local meal ideas
    if any(w in msg for w in ["hong kong", "local food", "healthy meal", "healthy option", "restaurant"]):
        return "Good Hong Kong-friendly choices include steamed fish with rice, congee with lean meat, wonton soup, roast meat with extra greens and less sauce, or cha chaan teng breakfasts with eggs and less sugary drinks. The easiest upgrade is usually **more protein, more vegetables, and fewer liquid calories**."

    # Safety boundary for medical issues
    if any(w in msg for w in ["chest pain", "faint", "dizzy", "injury", "injured", "sick", "fever"]):
        return "That sounds more medical than fitness-related. I can give general wellness guidance, but symptoms like chest pain, fainting, severe dizziness, or injury should be checked by a qualified healthcare professional promptly."

    # Food suggestions
    if any(w in msg for w in ["suggest", "recommend", "what should i eat", "food idea", "meal idea", "hungry"]):
        if remaining < 200:
            return "You're close to your limit. Try: a small fruit (50-80 kcal), green tea (0 kcal), or a handful of cherry tomatoes (25 kcal)."
        low_cal = [f for f in foods if f["calories"] <= remaining // 2]
        if low_cal:
            picks = random.sample(low_cal, min(3, len(low_cal)))
            items = "\n".join(f"\u2022 **{p['name']}** \u2014 {p['calories']} kcal" for p in picks)
            return f"Here are some options that fit your budget ({remaining} kcal left):\n{items}"
        return f"You have {remaining} kcal left. Check the Food Database tab for options that fit your budget."

    # BMI
    if "bmi" in msg:
        h = user.get("height", 175)
        w = user.get("weight", 70)
        bmi = w / (h / 100) ** 2 if h > 0 else 0
        cat = "Underweight" if bmi < 18.5 else "Normal" if bmi < 25 else "Overweight" if bmi < 30 else "Obese"
        return f"Your BMI is **{bmi:.1f}** ({cat}). {'You\'re in a healthy range! \U0001f44d' if cat == 'Normal' else 'Talk to a healthcare professional for personalized advice.'}"

    # Goal
    if any(w in msg for w in ["goal", "target", "aim"]):
        return f"Your goal is to **{goal}** weight with a daily target of **{goal_value} kcal**. {'Focus on a calorie deficit through portion control.' if goal == 'Lose' else 'Focus on nutrient-dense, calorie-rich foods.' if goal == 'Gain' else 'Keep a balanced diet to maintain your weight.'}"

    # Today summary
    if any(w in msg for w in ["summary", "today", "overview", "status"]):
        entries_count = len(log_entries)
        return f"**Today's Summary:**\n\u2022 Food: {calorie_status}/{goal_value} kcal ({entries_count} items)\n\u2022 Exercise: -{exercise_burned} kcal\n\u2022 Net remaining: {remaining} kcal\n\u2022 Water: {water_intake}/{water_goal} glasses\n\n{'You\'re on track! \U0001f525' if calorie_status <= goal_value else 'You\'ve exceeded your goal \u2014 consider some exercise.'}"

    # Help
    if any(w in msg for w in ["help", "what can you", "commands", "options"]):
        return "I can help with:\n\u2022 **\"How many calories?\"** \u2014 check your intake\n\u2022 **\"What should I eat?\"** \u2014 meal suggestions\n\u2022 **\"Protein tips\"** \u2014 macros and protein guidance\n\u2022 **\"Workout recovery\"** \u2014 sleep and rest advice\n\u2022 **\"Water status\"** \u2014 hydration check\n\u2022 **\"Exercise\"** \u2014 today's activity\n\u2022 **\"Summary\"** \u2014 daily overview\n\u2022 **\"BMI\"** \u2014 calculate your BMI\n\u2022 **\"Goal\"** \u2014 your current target"

    # Fallback
    return f"I can help with calories, meals, protein, hydration, workouts, recovery, BMI, and daily summaries. Try **\"help\"**, **\"protein tips\"**, **\"healthy Hong Kong meal\"**, or **\"today's summary\"**."


def load_dashboard_data(api_base_url: str) -> tuple[list[dict], dict, dict]:
    foods = api_call("GET", "/api/foods", api_base_url).get("foods", [])
    log_data = api_call("GET", "/api/log", api_base_url)
    user = api_call("GET", "/api/user", api_base_url).get("user", {})
    return foods, log_data, user


def get_goal_value(user: dict) -> int:
    if "daily_calorie_target" in user:
        return int(user["daily_calorie_target"])
    age, weight, height = user.get("age", 25), user.get("weight", 70), user.get("height", 175)
    goal = user.get("goal", "Maintain")
    bmr = 10 * weight + 6.25 * height - 5 * age + 5
    if goal == "Lose":
        return int(bmr * 0.8)
    elif goal == "Gain":
        return int(bmr * 1.2)
    return int(bmr)


def bmi_category(bmi: float) -> str:
    if bmi < 18.5:
        return "Underweight"
    elif bmi < 25:
        return "Normal"
    elif bmi < 30:
        return "Overweight"
    return "Obese"


def load_users(api_base_url: str) -> list[dict]:
    return api_call("GET", "/api/users", api_base_url).get("users", [])


def get_current_user_name(api_base_url: str) -> str:
    try:
        return api_call("GET", "/api/user", api_base_url).get("user", {}).get("name", "Dawood")
    except requests.RequestException:
        return "Dawood"


def render_sidebar_status_panel(profile_name: str, profile_count: int, user_data: dict) -> None:
    height_cm = float(user_data.get("height", 0) or 0)
    weight_kg = float(user_data.get("weight", 0) or 0)
    bmi_value = weight_kg / (height_cm / 100) ** 2 if height_cm > 0 and weight_kg > 0 else 0
    target_value = int(user_data.get("daily_calorie_target", get_goal_value(user_data))) if user_data else 0
    status_items = [
        ("Profile", profile_name, f"{profile_count} saved profile{'s' if profile_count != 1 else ''}.", "👤"),
        ("Goal", str(user_data.get("goal", "Maintain")), "Current body-weight objective.", "🎯"),
        ("Target", f"{target_value} kcal", "Daily calorie target.", "🔥"),
        ("BMI", f"{bmi_value:.1f}" if bmi_value > 0 else "N/A", bmi_category(bmi_value) if bmi_value > 0 else "Add height and weight to calculate.", "📏"),
    ]
    chips_html = "".join(
        f'<div class="status-chip"><div class="status-top"><span class="status-name">{_html.escape(name)}</span><span>{icon}</span></div><div class="status-value">{_html.escape(value)}</div><div class="status-detail">{_html.escape(detail)}</div></div>'
        for name, value, detail, icon in status_items
    )
    st.markdown(f'<div class="status-panel"><div class="status-grid">{chips_html}</div></div>', unsafe_allow_html=True)


def show_login_screen() -> None:
    st.markdown("<style>[data-testid='stSidebar']{display:none;}</style>", unsafe_allow_html=True)
    _, center, _ = st.columns([1, 2.2, 1])
    with center:
        st.markdown("""<div style="text-align:center; padding-top:1.5rem;">
            <div class="login-logo">\U0001f35c</div>
            <div class="login-title">HK Calorie Tracker</div>
            <div class="login-subtitle">Your personal Hong Kong nutrition companion</div>
        </div>""", unsafe_allow_html=True)

        api_base_url = DEFAULT_API_URL
        try:
            users = load_users(api_base_url)
        except requests.RequestException:
            st.error("Cannot connect to API \u2014 make sure Flask backend is running on port 5050.")
            with st.expander("\u2699\ufe0f Custom API URL"):
                api_base_url = st.text_input("API URL", value=DEFAULT_API_URL, key="login_api_url")
            return

        sign_in, sign_up = st.tabs(["\U0001f513 Sign In", "\u2728 Create Account"])

        with sign_in:
            if not users:
                st.markdown('<div style="text-align:center; padding:1rem 0; color:var(--muted);"><div style="font-size:2rem; margin-bottom:0.3rem;">\U0001f44b</div><p style="font-size:0.9rem; margin:0;">No profiles yet</p><p style="font-size:0.8rem; color:var(--muted);">Head to <b>Create Account</b> to get started</p></div>', unsafe_allow_html=True)
            else:
                user_names = [u["name"] for u in users]
                selected_user = st.selectbox("Profile", user_names, key="login_user_select", label_visibility="collapsed", format_func=lambda n: f"\U0001f464  {n}")
                if st.button("Sign In \u2192", type="primary", width="stretch"):
                    def _set_user_and_api(_result: Any) -> None:
                        st.session_state.__setitem__("logged_in_user", selected_user)
                        st.session_state.__setitem__("api_base_url", api_base_url)
                    run_api_action(
                        lambda: api_call("POST", "/api/users/select", api_base_url, {"name": selected_user}),
                        error_prefix="Login failed",
                        on_success=_set_user_and_api,
                    )

        with sign_up:
            r1c1, r1c2 = st.columns(2, gap="medium")
            with r1c1:
                new_name = st.text_input("Name", placeholder="e.g. Dawood", key="login_new_name")
            with r1c2:
                new_goal = st.selectbox("Goal", ["Maintain", "Lose", "Gain"], key="login_new_goal")
            r2c1, r2c2, r2c3 = st.columns(3, gap="medium")
            with r2c1:
                new_age = st.number_input("Age", min_value=1, max_value=120, step=1, value=20, key="login_new_age")
            with r2c2:
                new_weight = st.number_input("Weight (kg)", min_value=20.0, max_value=300.0, step=0.5, value=70.0, key="login_new_weight")
            with r2c3:
                new_height = st.number_input("Height (cm)", min_value=50.0, max_value=250.0, step=0.5, value=175.0, key="login_new_height")
            if st.button("Create Account \u2192", type="primary", width="stretch"):
                if not new_name.strip():
                    st.error("Name is required.")
                elif users and new_name.strip().lower() in {u["name"].lower() for u in users}:
                    st.warning("This name already exists.")
                else:
                    created_name = new_name.strip()
                    def _create_and_select(_result: Any) -> None:
                        api_call("POST", "/api/users/select", api_base_url, {"name": created_name})
                    def _set_created_user(_result: Any) -> None:
                        st.session_state.__setitem__("logged_in_user", created_name)
                        st.session_state.__setitem__("api_base_url", api_base_url)
                    run_api_action(
                        lambda: api_call("POST", "/api/users", api_base_url, {"name": created_name, "age": int(new_age), "weight": float(new_weight), "height": float(new_height), "goal": new_goal}),
                        error_prefix="Could not create profile",
                        on_success=_set_created_user,
                    )

        st.markdown("""<div class="login-features" style="margin-top:0.8rem;">
            <div class="login-feature"><div class="login-feature-icon">\U0001f525</div>Calories</div>
            <div class="login-feature"><div class="login-feature-icon">\U0001f4a7</div>Water</div>
            <div class="login-feature"><div class="login-feature-icon">\U0001f3c3</div>Exercise</div>
            <div class="login-feature"><div class="login-feature-icon">\U0001f4ca</div>Insights</div>
            <div class="login-feature"><div class="login-feature-icon">\U0001f35c</div>HK Foods</div>
        </div>
        <p style="text-align:center; color:#4a4a5a; font-size:0.68rem; margin-top:0.8rem; letter-spacing:0.04em;">Track meals \u00b7 Log exercise \u00b7 Set goals \u00b7 Stay healthy</p>""", unsafe_allow_html=True)


def show_main_dashboard() -> None:
    api_base_url: str = st.session_state.get("api_base_url", DEFAULT_API_URL) or DEFAULT_API_URL
    logged_in_user = st.session_state["logged_in_user"]

    with st.sidebar:
        st.markdown(f'<div class="sidebar-badge"><div class="badge-name">\U0001f35c {logged_in_user}</div><div class="badge-sub">Active Profile</div></div>', unsafe_allow_html=True)
        st.markdown("---")
        st.markdown("## Connection")
        api_base_url_input = st.text_input("Flask API URL", value=api_base_url, key="dashboard_api_url")
        if api_base_url_input != api_base_url:
            st.session_state["api_base_url"] = api_base_url_input
            api_base_url = api_base_url_input
        if st.button("Refresh Status", width="stretch"):
            st.rerun()
        st.markdown("---")
        if st.button("\U0001f6aa Logout", type="secondary"):
            for key in ("logged_in_user", "api_base_url"):
                st.session_state.pop(key, None)
            st.rerun()
        st.markdown("---")

        try:
            users = load_users(api_base_url or DEFAULT_API_URL)
        except requests.RequestException:
            users = []

        current_user_data = {}

        if users:
            user_names = [u["name"] for u in users]
            current_name = st.session_state.get("logged_in_user", get_current_user_name(api_base_url or DEFAULT_API_URL))
            current_user_data = next((u for u in users if u["name"] == current_name), {})
            selected_index = user_names.index(current_name) if current_name in user_names else 0
            selected_profile = st.selectbox("Switch profile", user_names, index=selected_index, key="switch_profile")
            if st.button("Switch profile"):
                run_api_action(
                    lambda: api_call("POST", "/api/users/select", api_base_url or DEFAULT_API_URL, {"name": selected_profile}),
                    error_prefix="Could not switch",
                    on_success=lambda _result: st.session_state.__setitem__("logged_in_user", selected_profile),
                )

        with st.expander("\u2795 Create profile"):
            new_name = st.text_input("Name", key="new_name")
            new_age = st.number_input("Age", min_value=1, step=1, key="new_age")
            new_weight = st.number_input("Weight (kg)", min_value=1.0, step=0.5, key="new_weight")
            new_height = st.number_input("Height (cm)", min_value=1.0, step=0.5, key="new_height")
            new_goal = st.selectbox("Goal", ["Maintain", "Lose", "Gain"], key="new_goal")
            if st.button("Create profile"):
                if not new_name.strip():
                    st.error("Name is required.")
                elif new_name.strip().lower() in {u["name"].lower() for u in users}:
                    st.warning("Already exists.")
                else:
                    run_api_action(
                        lambda: api_call("POST", "/api/users", api_base_url or DEFAULT_API_URL, {"name": new_name, "age": int(new_age), "weight": float(new_weight), "height": float(new_height), "goal": new_goal}),
                        success_message="Profile created.",
                    )

        with st.expander("\u270f\ufe0f Edit Profile"):
            current_user_data = next((u for u in users if u["name"] == logged_in_user), current_user_data)
            edit_name: str = st.text_input("Name", value=current_user_data.get("name", ""), key="edit_name") or ""
            edit_age = st.number_input("Age", min_value=1, step=1, value=int(current_user_data.get("age", 25)), key="edit_age")
            edit_weight = st.number_input("Weight (kg)", min_value=1.0, step=0.5, value=float(current_user_data.get("weight", 70)), key="edit_weight")
            edit_height = st.number_input("Height (cm)", min_value=1.0, step=0.5, value=float(current_user_data.get("height", 175)), key="edit_height")
            edit_goal = st.selectbox("Goal", ["Maintain", "Lose", "Gain"], index=["Maintain", "Lose", "Gain"].index(current_user_data.get("goal", "Maintain")), key="edit_goal")
            edit_target = st.number_input("Daily Calorie Target", min_value=500, max_value=10000, step=50, value=int(current_user_data.get("daily_calorie_target", 2000)), key="edit_target")
            if st.button("Save Changes", type="primary"):
                if not edit_name.strip():
                    st.error("Name cannot be empty.")
                else:
                    run_api_action(
                        lambda: api_call("PUT", "/api/user", api_base_url or DEFAULT_API_URL, {
                            "name": edit_name.strip(),
                            "age": int(edit_age),
                            "weight": float(edit_weight),
                            "height": float(edit_height),
                            "goal": edit_goal,
                            "daily_calorie_target": int(edit_target),
                        }),
                        success_message="Profile updated!",
                        on_success=lambda _result: st.session_state.__setitem__("logged_in_user", edit_name.strip()),
                    )

        try:
            sidebar_foods = api_call("GET", "/api/foods", api_base_url or DEFAULT_API_URL).get("foods", [])
        except requests.RequestException:
            sidebar_foods = []

        st.markdown("## Profile Snapshot")
        render_sidebar_status_panel(logged_in_user, len(users), current_user_data)

        with st.expander("\U0001f962 Add Food"):
            st.markdown(f"**{len(sidebar_foods)} foods in database**")
            if sidebar_foods:
                categories = sorted({f.get("category", "General") for f in sidebar_foods})
                cat_filter = st.selectbox("Filter by category", ["All"] + categories, key="sidebar_food_cat_filter")
                filtered = sidebar_foods if cat_filter == "All" else [f for f in sidebar_foods if f.get("category") == cat_filter]
                st.dataframe(filtered, width="stretch", hide_index=True, height=260)

            with st.form("sidebar_food_form"):
                food_name = st.text_input("Food name", placeholder="e.g. Char Siu Rice")
                fc1, fc2 = st.columns(2)
                with fc1:
                    food_calories = st.number_input("Calories", min_value=1, step=10, value=300)
                with fc2:
                    food_category = st.selectbox("Category", ["Food", "Drink", "Snack", "Dessert", "General"])
                if st.form_submit_button("Add Food", width="stretch"):
                    run_api_action(
                        lambda: api_call("POST", "/api/foods", api_base_url or DEFAULT_API_URL, {"name": food_name, "calories": int(food_calories), "category": food_category}),
                        success_message="Food added!",
                    )

        if len(users) > 1:
            with st.expander("\U0001f5d1\ufe0f Delete profile"):
                delete_name = st.selectbox("Select profile", [u["name"] for u in users], key="delete_name")
                confirm = st.checkbox("Confirm deletion", key="confirm_delete")
                if st.button("Delete"):
                    if not confirm:
                        st.error("Please confirm.")
                    else:
                        run_api_action(
                            lambda: api_call("DELETE", "/api/users", api_base_url or DEFAULT_API_URL, {"name": delete_name}),
                            success_message=f"Deleted '{delete_name}'.",
                            on_success=lambda _result: st.session_state.pop("logged_in_user", None) if st.session_state.get("logged_in_user") == delete_name else None,
                        )

    # Load data
    try:
        foods, log_data, user = load_dashboard_data(api_base_url or DEFAULT_API_URL)
    except requests.RequestException as err:
        st.error("Could not load data. Start Flask API and check URL.")
        st.info("Launch the backend with 'python run_backend.py' and refresh once it is running.")
        st.exception(err)
        return

    calorie_status = log_data.get("total_calories", 0)
    goal_value = get_goal_value(user)
    water_intake = user.get("water_intake", 0)
    water_goal = user.get("water_goal", 8)
    streak = user.get("streak", 0)
    exercise_burned = user.get("exercise_burned", 0)
    exercises = user.get("exercises", [])

    hour = datetime.datetime.now().hour
    greeting = "morning" if hour < 12 else "afternoon" if hour < 18 else "evening"

    # Hero
    st.markdown(f"""<section class="hero">
        <div style="display:flex; justify-content:space-between; align-items:center; gap:1rem; flex-wrap:wrap;">
            <div>
                <h1 style="margin:0 0 0.2rem; font-size:1.6rem;">Good {greeting}, {logged_in_user} \U0001f44b</h1>
                <p style="margin:0; color:var(--ink-secondary); font-size:0.88rem;">Here's your nutrition overview for today.</p>
            </div>
            <div style="text-align:right; min-width:140px;">
                <p style="margin:0; color:var(--accent-2); font-weight:700; letter-spacing:0.1em; text-transform:uppercase; font-size:0.75rem;">\U0001f525 {streak} Day Streak</p>
                <p style="margin:0.2rem 0 0; color:var(--muted); font-size:0.78rem;">{datetime.date.today().strftime('%B %d, %Y')}</p>
            </div>
        </div>
    </section>""", unsafe_allow_html=True)

    render_motivation_banner()

    # Calorie Ring + Stats
    net_remaining = max(0, goal_value - calorie_status + exercise_burned)
    ring_left, ring_right = st.columns([0.55, 0.45], gap="large")
    with ring_left:
        render_calorie_ring(calorie_status, goal_value, net_remaining, exercise_burned)
    with ring_right:
        m_a, m_b = st.columns(2, gap="medium")
        with m_a:
            render_stat_card("Eaten", str(calorie_status), "\U0001f525")
        with m_b:
            render_stat_card("Remaining", str(net_remaining), "\U0001f3af")
        m_c, m_d = st.columns(2, gap="medium")
        with m_c:
            render_stat_card("Burned", str(exercise_burned), "\U0001f3c3")
        with m_d:
            render_stat_card("Water", f"{water_intake}/{water_goal}", "\U0001f4a7")

    render_macro_bars(calorie_status)
    render_progress_bar(calorie_status, goal_value)

    summary_text = build_daily_summary_text(user, log_data, goal_value, water_intake, water_goal, exercise_burned, exercises)
    st.download_button(
        "Download Daily Summary",
        data=summary_text,
        file_name=f"hk-calorie-summary-{datetime.date.today().isoformat()}.txt",
        mime="text/plain",
    )

    if calorie_status > goal_value:
        st.error("\u26a0\ufe0f You've exceeded your daily calorie goal!")
    elif calorie_status > 0:
        st.success("\u2705 You're within your calorie budget. Keep going!")

    st.markdown("<div class='theme-divider'></div>", unsafe_allow_html=True)

    # Tabs
    tab_diary, tab_exercise, tab_water, tab_goals, tab_history, tab_chat = st.tabs(
        ["\U0001f4cb Food Diary", "\U0001f3c3 Exercise", "\U0001f4a7 Water", "\U0001f3af Goals & BMI", "\U0001f4ca Insights", "\U0001f916 AI Chat"]
    )

    # Food Diary
    with tab_diary:
        render_section_header("\U0001f4cb", "Food Diary", "rgba(0,212,170,0.12)")
        meal_totals = log_data.get("meal_totals", {})
        if meal_totals:
            meal_icons = {"Breakfast": "\U0001f373", "Lunch": "\U0001f35c", "Dinner": "\U0001f355", "Snack": "\U0001f36a", "General": "\U0001f37d\ufe0f"}
            meal_cols = st.columns(len(meal_totals), gap="medium")
            for i, (meal_name, meal_cal) in enumerate(meal_totals.items()):
                with meal_cols[i]:
                    render_stat_card(meal_name, f"{meal_cal} kcal", meal_icons.get(meal_name, "\U0001f37d\ufe0f"))
            st.markdown("<div class='theme-divider'></div>", unsafe_allow_html=True)

        diary_left, diary_right = st.columns([0.55, 0.45], gap="large")
        with diary_left:
            if log_data.get("entries"):
                for entry in log_data["entries"]:
                    mi = {"Breakfast": "\U0001f373", "Lunch": "\U0001f35c", "Dinner": "\U0001f355", "Snack": "\U0001f36a"}.get(entry.get("meal", ""), "\U0001f37d\ufe0f")
                    ec_left, ec_right = st.columns([0.85, 0.15])
                    with ec_left:
                        st.markdown(f'<div class="entry-row"><span style="flex:0.3; text-align:center;">{mi}</span><span class="entry-name">{entry["food_name"]}</span><span class="entry-qty">{entry["quantity"]}x</span><span class="entry-cal">{entry["total_calories"]} kcal</span></div>', unsafe_allow_html=True)
                    with ec_right:
                        if st.button("\u2716", key=f"del_food_{entry['food_name']}", help=f"Remove {entry['food_name']}"):
                            run_api_action(
                                lambda: api_call("DELETE", "/api/log/entry", api_base_url or DEFAULT_API_URL, {"food_name": entry["food_name"]}),
                            )
            else:
                st.info("No food logged yet today. Use the form to start tracking!")

        with diary_right:
            st.markdown("**Quick Log**")
            food_search = st.text_input("Search foods", key="log_food_search", placeholder="Type a food name...")
            matching_foods = [
                food for food in foods
                if food_search.strip().lower() in food["name"].lower()
            ] if food_search.strip() else foods
            if food_search.strip() and not matching_foods:
                st.warning("No foods match that search.")
            with st.form("log_form"):
                food_options = [f["name"] for f in matching_foods] if matching_foods else [f["name"] for f in foods]
                selected_food = st.selectbox("Select food", food_options, key="log_food_select")
                q_col, m_col = st.columns(2)
                with q_col:
                    quantity = st.number_input("Qty", min_value=1, step=1, value=1, key="log_quantity")
                with m_col:
                    meal_type = st.selectbox("Meal", ["Breakfast", "Lunch", "Dinner", "Snack", "General"], key="log_meal_type")
                if st.form_submit_button("Log Food", width="stretch"):
                    if foods:
                        run_api_action(
                            lambda: api_call("POST", "/api/log", api_base_url or DEFAULT_API_URL, {"food_name": selected_food, "quantity": int(quantity), "meal": meal_type}),
                            success_message=f"Logged {quantity}x {selected_food}",
                            error_prefix="Could not log",
                        )
            if st.button("\U0001f504 Reset Day", width="stretch"):
                run_api_action(
                    lambda: api_call("DELETE", "/api/log", api_base_url or DEFAULT_API_URL),
                    success_message="Day reset!",
                )

    # Exercise
    with tab_exercise:
        render_section_header("\U0001f3c3", "Exercise Tracker", "rgba(108,92,231,0.12)")
        ex_left, ex_right = st.columns([0.55, 0.45], gap="large")
        with ex_left:
            total_duration = sum(e.get("duration_min", 0) for e in exercises)
            s_a, s_b, s_c = st.columns(3, gap="medium")
            with s_a:
                render_stat_card("Burned", f"{exercise_burned} kcal", "\U0001f525")
            with s_b:
                render_stat_card("Activities", str(len(exercises)), "\U0001f3cb\ufe0f")
            with s_c:
                render_stat_card("Duration", f"{total_duration} min", "\u23f1\ufe0f")
            if exercises:
                st.markdown("**Today's Activities**")
                for idx, ex in enumerate(exercises):
                    ex_left_col, ex_del_col = st.columns([0.85, 0.15])
                    with ex_left_col:
                        st.markdown(f'<div class="exercise-entry"><span class="ex-name">{ex["name"]}</span><span class="ex-dur">{ex.get("duration_min", 30)} min</span><span class="ex-cal">-{ex["calories_burned"]} kcal</span></div>', unsafe_allow_html=True)
                    with ex_del_col:
                        if st.button("\u2716", key=f"del_ex_{idx}", help=f"Remove {ex['name']}"):
                            run_api_action(
                                lambda: api_call("DELETE", "/api/exercise/entry", api_base_url or DEFAULT_API_URL, {"index": idx}),
                            )
            else:
                st.info("No exercises logged today. Add one to offset your calories!")
        with ex_right:
            st.markdown("**Log Exercise**")
            preset_names = list(EXERCISE_PRESETS.keys())
            preset = st.selectbox("Quick preset", ["Custom"] + preset_names, key="exercise_preset")
            with st.form("exercise_form"):
                if preset != "Custom":
                    ex_name = preset.split(" ", 1)[1].split(" (")[0]
                    ex_cal_default = EXERCISE_PRESETS[preset]
                else:
                    ex_name = ""
                    ex_cal_default = 200
                ex_name_input = st.text_input("Activity name", value=ex_name, key="ex_name")
                ec1, ec2 = st.columns(2)
                with ec1:
                    ex_cal = st.number_input("Calories burned", min_value=1, step=10, value=ex_cal_default, key="ex_cal")
                with ec2:
                    ex_dur = st.number_input("Duration (min)", min_value=1, step=5, value=30, key="ex_dur")
                if st.form_submit_button("Log Exercise", width="stretch"):
                    if ex_name_input.strip():
                        run_api_action(
                            lambda: api_call("POST", "/api/exercise", api_base_url or DEFAULT_API_URL, {"name": ex_name_input.strip(), "calories_burned": int(ex_cal), "duration_min": int(ex_dur)}),
                            success_message=f"Logged {ex_name_input.strip()} (-{ex_cal} kcal)",
                        )
                    else:
                        st.error("Activity name is required.")

    # Water
    with tab_water:
        render_section_header("\U0001f4a7", "Water Tracker", "rgba(59,130,246,0.12)")
        w_left, w_right = st.columns([0.6, 0.4], gap="large")
        with w_left:
            render_water_visual(water_intake, water_goal)
        with w_right:
            glasses_to_add = st.number_input("Glasses to add", min_value=1, max_value=10, step=1, value=1, key="water_add")
            if st.button("\U0001f4a7 Log Water", width="stretch"):
                run_api_action(
                    lambda: api_call("POST", "/api/water", api_base_url or DEFAULT_API_URL, {"glasses": int(glasses_to_add)}),
                    success_message=f"Added {glasses_to_add} glass(es)!",
                )
            st.markdown("---")
            new_water_goal = st.number_input("Daily goal (glasses)", min_value=1, max_value=20, step=1, value=water_goal, key="water_goal_input")
            if st.button("Set Water Goal", width="stretch"):
                run_api_action(
                    lambda: api_call("PUT", "/api/water/goal", api_base_url or DEFAULT_API_URL, {"goal": int(new_water_goal)}),
                    success_message=f"Goal \u2192 {new_water_goal} glasses",
                )

    # Goals & BMI
    with tab_goals:
        render_section_header("\U0001f3af", "Goals & BMI", "rgba(255,107,53,0.12)")
        g_left, g_right = st.columns([0.5, 0.5], gap="large")
        with g_left:
            st.markdown("**Calorie Goal**")
            current_target = int(user.get("daily_calorie_target", goal_value))
            new_target = st.number_input("Daily calorie target (kcal)", min_value=800, max_value=10000, step=50, value=current_target, key="goal_target")
            if st.button("Save Calorie Goal", width="stretch"):
                run_api_action(
                    lambda: api_call("PUT", "/api/user", api_base_url or DEFAULT_API_URL, {"name": user.get("name", ""), "age": int(user.get("age", 20)), "weight": float(user.get("weight", 70)), "height": float(user.get("height", 175)), "goal": user.get("goal", "Maintain"), "daily_calorie_target": int(new_target)}),
                    success_message=f"Goal \u2192 {new_target} kcal",
                )
            st.metric("Current Goal", f"{current_target} kcal")
        with g_right:
            st.markdown("**BMI Calculator**")
            calc_height = st.number_input("Height (cm)", min_value=1.0, step=0.5, value=float(user.get("height", 175)), key="bmi_height")
            calc_weight = st.number_input("Weight (kg)", min_value=1.0, step=0.5, value=float(user.get("weight", 70)), key="bmi_weight")
            if st.button("Calculate BMI", width="stretch"):
                try:
                    height_m = calc_height / 100
                    bmi_result = calc_weight / (height_m ** 2)
                    bmi_cat = bmi_category(bmi_result)
                    color = {"Underweight": "#3b82f6", "Normal": "#00d4aa", "Overweight": "#f39c12", "Obese": "#e74c3c"}.get(bmi_cat, "#a0a0b0")
                    st.markdown(f'<div class="insight-card"><div class="ic-label">Your BMI</div><div class="ic-value" style="color:{color};">{bmi_result:.1f}</div><div class="ic-sub">{bmi_cat}</div></div>', unsafe_allow_html=True)
                except ZeroDivisionError:
                    st.error("Height must be > 0")

    # Insights & History
    with tab_history:
        render_section_header("\U0001f4ca", "Insights & History", "rgba(0,212,170,0.12)")
        history = user.get("weekly_history", [])
        avg_cal = sum(history) / len(history) if history else 0
        max_cal = max(history) if history else 0
        min_cal = min(h for h in history if h > 0) if any(h > 0 for h in history) else 0
        total_days = len([h for h in history if h > 0])

        if history:
            st.download_button(
                "Download Weekly History CSV",
                data=build_weekly_history_csv(history, goal_value),
                file_name=f"hk-calorie-history-{datetime.date.today().isoformat()}.csv",
                mime="text/csv",
            )

        i_a, i_b, i_c, i_d = st.columns(4, gap="medium")
        with i_a:
            st.markdown(f'<div class="insight-card"><div class="ic-label">7-Day Average</div><div class="ic-value">{avg_cal:.0f}</div><div class="ic-sub">kcal / day</div></div>', unsafe_allow_html=True)
        with i_b:
            st.markdown(f'<div class="insight-card"><div class="ic-label">Peak Day</div><div class="ic-value">{max_cal}</div><div class="ic-sub">kcal</div></div>', unsafe_allow_html=True)
        with i_c:
            st.markdown(f'<div class="insight-card"><div class="ic-label">Lightest Day</div><div class="ic-value">{min_cal}</div><div class="ic-sub">kcal</div></div>', unsafe_allow_html=True)
        with i_d:
            st.markdown(f'<div class="insight-card"><div class="ic-label">Active Days</div><div class="ic-value">{total_days}/{len(history)}</div><div class="ic-sub">tracked</div></div>', unsafe_allow_html=True)

        st.markdown("<div class='theme-divider'></div>", unsafe_allow_html=True)

        if history:
            h_left, h_right = st.columns([0.6, 0.4], gap="large")
            with h_left:
                st.markdown("**Calorie Trend**")
                day_labels = [(datetime.date.today() - datetime.timedelta(days=len(history) - 1 - i)).strftime("%a %d") for i in range(len(history))]
                chart_df = pd.DataFrame({"Day": day_labels, "Calories": history, "order": list(range(len(history)))})
                chart_df["Status"] = chart_df["Calories"].apply(lambda c: "Over" if c > goal_value else ("On Track" if c > 0 else "Rest"))
                color_scale = alt.Scale(domain=["On Track", "Over", "Rest"], range=["#00d4aa", "#e74c3c", "#333333"])
                bars = alt.Chart(chart_df).mark_bar(
                    cornerRadiusTopLeft=6, cornerRadiusTopRight=6, size=24
                ).encode(
                    x=alt.X("Day:N", sort=alt.EncodingSortField(field="order"), axis=alt.Axis(labelAngle=-45, labelColor="#a0a0b0", title=None)),
                    y=alt.Y("Calories:Q", axis=alt.Axis(labelColor="#a0a0b0", title="kcal", gridColor="rgba(255,255,255,0.05)")),
                    color=alt.Color("Status:N", scale=color_scale, legend=None),
                    tooltip=["Day:N", "Calories:Q", "Status:N"]
                )
                goal_line = alt.Chart(pd.DataFrame({"goal": [goal_value]})).mark_rule(
                    strokeDash=[6, 4], color="#f39c12", strokeWidth=2
                ).encode(y="goal:Q")
                goal_text = alt.Chart(pd.DataFrame({"goal": [goal_value], "label": [f"Goal: {goal_value}"]})).mark_text(
                    align="right", dx=-4, dy=-8, color="#f39c12", fontSize=11, fontWeight="bold"
                ).encode(y="goal:Q", text="label:N")
                st.altair_chart((bars + goal_line + goal_text).properties(height=320).configure(background="transparent").configure_view(strokeWidth=0), width="stretch")
            with h_right:
                st.markdown("**Daily Breakdown**")
                rows = [{"Day": f"Day {i+1}", "Calories": v, "Status": "\u2705" if 0 < v <= goal_value else ("\u26a0\ufe0f" if v > goal_value else "\u2014")} for i, v in enumerate(history)]
                st.table(rows)

            on_target = sum(1 for h in history if 0 < h <= goal_value)
            consistency = int(on_target / len(history) * 100) if history else 0
            bar_color = "#00d4aa" if consistency >= 70 else "#f39c12" if consistency >= 40 else "#e74c3c"
            st.markdown(f"""<div class="progress-container">
                <div style="display:flex; justify-content:space-between; align-items:baseline;">
                    <span style="color:#a0a0b0; font-size:0.75rem; text-transform:uppercase; letter-spacing:0.06em;">Weekly Consistency</span>
                    <span style="color:{bar_color}; font-weight:700;">{consistency}%</span>
                </div>
                <div class="progress-bar-track"><div class="progress-bar-fill" style="width:{consistency}%; background:{bar_color};"></div></div>
                <div style="text-align:right; margin-top:0.2rem;"><span style="color:#6b6b80; font-size:0.72rem;">{on_target}/{len(history)} days on target</span></div>
            </div>""", unsafe_allow_html=True)
        else:
            st.info("No weekly history yet. Log food and reset the day to build history.")

        # Recommendations
        st.markdown("<div class='theme-divider'></div>", unsafe_allow_html=True)
        render_section_header("\U0001f4a1", "Personalized Recommendations", "rgba(255,107,53,0.12)")
        recs = generate_recommendations(calorie_status, goal_value, water_intake, water_goal, exercise_burned, history, user)
        rec_cols = st.columns(min(len(recs), 3), gap="medium")
        for i, rec in enumerate(recs):
            with rec_cols[i % min(len(recs), 3)]:
                st.markdown(f'<div class="rec-card"><div class="rc-icon">{rec["icon"]}</div><div class="rc-title">{rec["title"]}</div><div class="rc-text">{rec["text"]}</div><span class="rc-tag" style="background:{rec["color"]}22; color:{rec["color"]};">{rec["tag"]}</span></div>', unsafe_allow_html=True)

    # AI Chat
    with tab_chat:
        render_section_header("\U0001f916", "AI Health Coach", "rgba(0,212,170,0.12)")
        st.markdown('<div style="color:var(--ink-secondary); font-size:0.82rem; margin-bottom:1rem;">Local AI mode is active. Ask about calories, protein, hydration, workouts, recovery, healthy Hong Kong meals, BMI, or get a daily summary.</div>', unsafe_allow_html=True)

        if "chat_messages" not in st.session_state:
            st.session_state["chat_messages"] = [
                {"role": "bot", "text": f"Hey {logged_in_user}! \U0001f44b I'm your AI health coach. Ask me about meals, protein, hydration, exercise, recovery, or your progress for today."}
            ]

        # Display chat history
        chat_html = '<div class="chat-container">'
        for msg in st.session_state["chat_messages"]:
            cls = "chat-user" if msg["role"] == "user" else "chat-bot"
            prefix = "" if msg["role"] == "user" else "\U0001f916 "
            safe = _html.escape(msg["text"]).replace("\n", "<br>")
            safe = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", safe)
            chat_html += f'<div class="chat-msg {cls}">{prefix}{safe}</div>'
        chat_html += '</div>'
        st.markdown(chat_html, unsafe_allow_html=True)

        # Quick action buttons
        qc1, qc2, qc3, qc4 = st.columns(4, gap="small")
        quick_prompts = [
            (qc1, "\U0001f525 Calories", "How many calories have I eaten?"),
            (qc2, "\U0001f4aa Protein", "Protein tips"),
            (qc3, "\U0001f35c Meal idea", "Give me a healthy Hong Kong meal idea"),
            (qc4, "\U0001f4cb Summary", "Give me today's summary"),
        ]
        for col, label, prompt in quick_prompts:
            with col:
                if st.button(label, width="stretch", key=f"quick_{label}"):
                    st.session_state["chat_messages"].append({"role": "user", "text": prompt})
                    reply = get_chatbot_response(prompt, calorie_status, goal_value, water_intake, water_goal, exercise_burned, exercises, user, foods, log_data.get("entries", []))
                    st.session_state["chat_messages"].append({"role": "bot", "text": reply})
                    st.rerun()

        # Text input
        with st.form("chat_form", clear_on_submit=True):
            user_input = st.text_input("Type your message...", key="chat_input", label_visibility="collapsed", placeholder="Ask me anything about your nutrition...")
            if st.form_submit_button("Send \U0001f680", width="stretch"):
                if user_input.strip():
                    st.session_state["chat_messages"].append({"role": "user", "text": user_input.strip()})
                    reply = get_chatbot_response(user_input, calorie_status, goal_value, water_intake, water_goal, exercise_burned, exercises, user, foods, log_data.get("entries", []))
                    st.session_state["chat_messages"].append({"role": "bot", "text": reply})
                    st.rerun()

        if len(st.session_state["chat_messages"]) > 1:
            if st.button("\U0001f5d1\ufe0f Clear chat"):
                st.session_state["chat_messages"] = [
                    {"role": "bot", "text": f"Chat cleared! How can I help you, {logged_in_user}?"}
                ]
                st.rerun()


def main() -> None:
    st.set_page_config(page_title="HK Calorie Tracker", page_icon="\U0001f35c", layout="wide")
    inject_styles()
    if "logged_in_user" not in st.session_state:
        show_login_screen()
        return
    show_main_dashboard()


if __name__ == "__main__":
    # Check if running directly vs via Streamlit
    if os.environ.get("STREAMLIT_RUN_FROM_CLI") != "true":
        frontend_hint = "python run_frontend.py"
        backend_hint = "python run_backend.py"
        print(f"This is a Streamlit app. Start the backend with {backend_hint}, then run the frontend with {frontend_hint}.")
    else:
        main()

