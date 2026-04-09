"""Streamlit frontend for HK Calorie Tracker.

This UI talks to the Flask API and does not access tracker internals directly.
"""

from __future__ import annotations

import datetime
import os
import requests
import streamlit as st


DEFAULT_API_URL = "http://127.0.0.1:5050"


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
                --muted: #6b6b80;
                --border: rgba(255,255,255,0.08);
                --border-hover: rgba(255,255,255,0.15);
                --shadow: rgba(0,0,0,0.4);
                --glass: rgba(255,255,255,0.03);
                --radius: 16px;
                --radius-sm: 10px;
                --radius-lg: 24px;
            }

            /* ── Global ── */
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

            h1, h2, h3 {
                font-family: 'Playfair Display', Georgia, serif;
                color: var(--ink);
                letter-spacing: -0.01em;
            }

            h1 { font-weight: 700; }
            h2 { font-weight: 600; font-size: 1.5rem; }
            h3 { font-weight: 500; }

            p, span, label, div {
                letter-spacing: 0.01em;
            }

            /* ── Glassmorphism Hero ── */
            .hero {
                background: linear-gradient(135deg, rgba(255,255,255,0.05) 0%, rgba(255,255,255,0.02) 100%);
                backdrop-filter: blur(20px);
                -webkit-backdrop-filter: blur(20px);
                border: 1px solid var(--border);
                border-radius: var(--radius-lg);
                padding: 2rem 2.2rem;
                box-shadow:
                    0 20px 60px rgba(0,0,0,0.3),
                    inset 0 1px 0 rgba(255,255,255,0.06);
                margin-bottom: 1.5rem;
                position: relative;
                overflow: hidden;
            }

            .hero::before {
                content: '';
                position: absolute;
                top: 0; right: 0;
                width: 200px; height: 200px;
                background: radial-gradient(circle, var(--accent-glow), transparent 70%);
                opacity: 0.4;
                border-radius: 50%;
                transform: translate(30%, -30%);
            }

            /* ── Stat Cards ── */
            .stat-card {
                background: linear-gradient(145deg, rgba(255,255,255,0.06) 0%, rgba(255,255,255,0.02) 100%);
                backdrop-filter: blur(12px);
                -webkit-backdrop-filter: blur(12px);
                border: 1px solid var(--border);
                border-radius: var(--radius);
                padding: 1.2rem 1.4rem;
                box-shadow: 0 8px 32px rgba(0,0,0,0.2);
                transition: all 0.3s cubic-bezier(0.4,0,0.2,1);
                position: relative;
                overflow: hidden;
            }

            .stat-card:hover {
                border-color: var(--border-hover);
                transform: translateY(-2px);
                box-shadow: 0 12px 40px rgba(0,0,0,0.3);
            }

            .stat-card .stat-icon {
                font-size: 1.6rem;
                margin-bottom: 0.6rem;
                display: inline-block;
            }

            .stat-card .stat-label {
                color: var(--muted);
                font-size: 0.78rem;
                font-weight: 500;
                letter-spacing: 0.06em;
                text-transform: uppercase;
                margin-bottom: 0.3rem;
            }

            .stat-card .stat-value {
                font-family: 'Inter', sans-serif;
                font-size: 1.6rem;
                font-weight: 800;
                color: var(--ink);
                letter-spacing: -0.02em;
            }

            /* ── Progress Ring ── */
            .progress-container {
                background: linear-gradient(145deg, rgba(255,255,255,0.06), rgba(255,255,255,0.02));
                backdrop-filter: blur(12px);
                border: 1px solid var(--border);
                border-radius: var(--radius);
                padding: 1.5rem;
                text-align: center;
            }

            .progress-bar-track {
                width: 100%;
                height: 10px;
                background: rgba(255,255,255,0.06);
                border-radius: 5px;
                overflow: hidden;
                margin: 0.8rem 0;
            }

            .progress-bar-fill {
                height: 100%;
                border-radius: 5px;
                transition: width 0.6s cubic-bezier(0.4,0,0.2,1);
            }

            /* ── Section Divider ── */
            .theme-divider {
                height: 1px;
                background: linear-gradient(90deg, transparent, var(--border), transparent);
                margin: 1.8rem 0;
            }

            /* ── Sidebar ── */
            [data-testid="stSidebar"] {
                background: linear-gradient(180deg, #111118 0%, #0d0d14 100%);
                border-right: 1px solid var(--border);
            }

            [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
            [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h2,
            [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h3,
            [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h4,
            [data-testid="stSidebar"] label,
            [data-testid="stSidebar"] .stMarkdown,
            [data-testid="stSidebar"] span,
            [data-testid="stSidebar"] div {
                color: #e0e0e8 !important;
            }

            [data-testid="stSidebar"] button {
                color: #ffffff !important;
            }

            [data-testid="stSidebar"] [data-testid="stSelectbox"] span,
            [data-testid="stSidebar"] [data-testid="stSelectbox"] input,
            [data-testid="stSidebar"] [data-testid="stSelectbox"] div[data-baseweb="select"] span {
                color: #ffffff !important;
            }

            [data-testid="stSidebar"] [data-testid="stTextInput"] input {
                color: #ffffff !important;
            }

            /* ── Sidebar profile badge ── */
            .sidebar-badge {
                background: linear-gradient(135deg, rgba(255,107,53,0.12), rgba(0,212,170,0.08));
                border: 1px solid rgba(255,107,53,0.2);
                border-radius: var(--radius-sm);
                padding: 0.8rem 1rem;
                margin-bottom: 1rem;
            }

            .sidebar-badge .badge-name {
                font-family: 'Playfair Display', serif;
                font-size: 1.2rem;
                font-weight: 700;
                color: var(--ink);
            }

            .sidebar-badge .badge-sub {
                color: var(--muted);
                font-size: 0.75rem;
                text-transform: uppercase;
                letter-spacing: 0.1em;
                margin-top: 0.15rem;
            }

            /* ── Entry rows ── */
            .entry-row {
                display: flex;
                align-items: center;
                justify-content: space-between;
                background: rgba(255,255,255,0.03);
                border: 1px solid var(--border);
                border-radius: var(--radius-sm);
                padding: 0.65rem 1rem;
                margin-bottom: 0.45rem;
                transition: background 0.2s;
            }

            .entry-row:hover {
                background: rgba(255,255,255,0.06);
            }

            .entry-name { color: var(--ink); font-weight: 500; flex: 2; }
            .entry-qty { color: var(--accent); font-weight: 600; flex: 0.5; text-align: center; }
            .entry-cal { color: var(--accent-2); font-weight: 700; flex: 1; text-align: right; }

            /* ── Login card ── */
            .login-card {
                background: linear-gradient(145deg, rgba(255,255,255,0.06), rgba(255,255,255,0.02));
                backdrop-filter: blur(20px);
                border: 1px solid var(--border);
                border-radius: var(--radius-lg);
                padding: 2.5rem 2rem;
                box-shadow: 0 24px 80px rgba(0,0,0,0.4);
                max-width: 480px;
                margin: 0 auto;
            }

            .login-header {
                text-align: center;
                margin-bottom: 2rem;
            }

            .login-header h1 {
                font-size: 2.2rem;
                margin-bottom: 0.5rem;
                background: linear-gradient(135deg, var(--accent), var(--accent-2));
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
            }

            .login-header p {
                color: var(--muted);
                font-size: 0.95rem;
            }

            /* ── Login page layout ── */
            .login-page {
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                padding: 1rem;
            }

            .login-logo {
                width: 56px;
                height: 56px;
                background: linear-gradient(135deg, var(--accent), var(--accent-2));
                border-radius: 16px;
                display: inline-flex;
                align-items: center;
                justify-content: center;
                font-size: 1.8rem;
                margin: 0 auto 0.6rem;
                box-shadow: 0 8px 28px var(--accent-glow);
            }

            .login-title {
                font-family: 'Playfair Display', serif;
                font-size: 1.8rem;
                font-weight: 700;
                color: var(--ink);
                margin: 0 0 0.15rem;
                text-align: center;
            }

            .login-subtitle {
                color: var(--muted);
                font-size: 0.82rem;
                text-align: center;
                margin: 0 0 0.8rem;
            }

            .login-divider {
                display: flex;
                align-items: center;
                gap: 1rem;
                margin: 1.5rem 0;
                color: var(--muted);
                font-size: 0.78rem;
                text-transform: uppercase;
                letter-spacing: 0.1em;
            }

            .login-divider::before,
            .login-divider::after {
                content: '';
                flex: 1;
                height: 1px;
                background: var(--border);
            }

            .login-features {
                display: flex;
                justify-content: center;
                gap: 1.2rem;
                margin-top: 0.8rem;
                flex-wrap: wrap;
            }

            .login-feature {
                display: flex;
                align-items: center;
                gap: 0.5rem;
                color: var(--ink-secondary);
                font-size: 0.82rem;
            }

            .login-feature-icon {
                width: 30px;
                height: 30px;
                background: rgba(255,255,255,0.05);
                border: 1px solid var(--border);
                border-radius: 8px;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 0.9rem;
            }

            /* ── Buttons ── */
            .stButton > button {
                background: linear-gradient(135deg, var(--accent) 0%, #e85d2c 100%) !important;
                color: #fff !important;
                border: none !important;
                border-radius: var(--radius-sm) !important;
                font-weight: 600 !important;
                font-size: 0.9rem !important;
                letter-spacing: 0.02em !important;
                padding: 0.55rem 1.2rem !important;
                transition: all 0.25s cubic-bezier(0.4,0,0.2,1) !important;
                box-shadow: 0 4px 15px var(--accent-glow) !important;
            }

            .stButton > button:hover {
                transform: translateY(-1px) !important;
                box-shadow: 0 8px 25px var(--accent-glow) !important;
                filter: brightness(1.1) !important;
            }

            .stButton > button:active {
                transform: translateY(0) !important;
            }

            /* ── Form submit buttons ── */
            .stFormSubmitButton > button {
                background: linear-gradient(135deg, var(--accent-2) 0%, #00b894 100%) !important;
                box-shadow: 0 4px 15px var(--accent-2-glow) !important;
            }

            .stFormSubmitButton > button:hover {
                box-shadow: 0 8px 25px var(--accent-2-glow) !important;
            }

            /* ── Inputs ── */
            [data-testid="stTextInput"] input,
            [data-testid="stNumberInput"] input {
                background: rgba(255,255,255,0.04) !important;
                border: 1px solid var(--border) !important;
                border-radius: var(--radius-sm) !important;
                color: var(--ink) !important;
                transition: border-color 0.2s !important;
            }

            [data-testid="stTextInput"] input:focus,
            [data-testid="stNumberInput"] input:focus {
                border-color: var(--accent) !important;
                box-shadow: 0 0 0 2px var(--accent-glow) !important;
            }

            /* ── Selectbox ── */
            [data-testid="stSelectbox"] > div > div {
                background: rgba(255,255,255,0.04) !important;
                border: 1px solid var(--border) !important;
                border-radius: var(--radius-sm) !important;
                cursor: pointer !important;
                color: #ffffff !important;
            }

            [data-testid="stSelectbox"] input {
                caret-color: transparent !important;
                cursor: pointer !important;
                color: #ffffff !important;
            }

            [data-testid="stSelectbox"] span,
            [data-testid="stSelectbox"] div[data-baseweb="select"] span {
                color: #ffffff !important;
            }

            /* Selectbox dropdown options */
            [data-baseweb="menu"] li,
            [data-baseweb="menu"] [role="option"] {
                color: #ffffff !important;
            }

            /* ── Tabs ── */
            .stTabs [data-baseweb="tab-list"] {
                gap: 0.5rem;
            }

            .stTabs [data-baseweb="tab"] {
                background: transparent;
                border-radius: var(--radius-sm);
                padding: 0.5rem 1.2rem;
                color: var(--muted);
                font-weight: 500;
            }

            .stTabs [aria-selected="true"] {
                background: rgba(255,107,53,0.12) !important;
                color: var(--accent) !important;
            }

            /* ── Expander ── */
            .streamlit-expanderHeader {
                background: rgba(255,255,255,0.03) !important;
                border-radius: var(--radius-sm) !important;
                border: 1px solid var(--border) !important;
            }

            /* ── Metric ── */
            [data-testid="stMetric"] {
                background: var(--panel);
                border: 1px solid var(--border);
                border-radius: var(--radius-sm);
                padding: 0.8rem;
            }

            [data-testid="stMetricValue"] {
                color: var(--accent-2) !important;
                font-weight: 800 !important;
            }

            /* ── DataFrame ── */
            [data-testid="stDataFrame"] {
                border: 1px solid var(--border) !important;
                border-radius: var(--radius-sm) !important;
                overflow: hidden !important;
            }

            /* ── Animations ── */
            @keyframes fadeUp {
                from { opacity: 0; transform: translateY(12px); }
                to { opacity: 1; transform: translateY(0); }
            }

            .hero, .stat-card, .progress-container, .entry-row, .login-card {
                animation: fadeUp 0.5s cubic-bezier(0.4,0,0.2,1) both;
            }

            .stat-card:nth-child(2) { animation-delay: 0.05s; }
            .stat-card:nth-child(3) { animation-delay: 0.1s; }
            .stat-card:nth-child(4) { animation-delay: 0.15s; }

            /* ── Calorie ring ── */
            .calorie-ring-wrap {
                display: flex;
                align-items: center;
                gap: 2rem;
                background: linear-gradient(145deg, rgba(255,255,255,0.06), rgba(255,255,255,0.02));
                backdrop-filter: blur(12px);
                border: 1px solid var(--border);
                border-radius: var(--radius-lg);
                padding: 1.8rem 2rem;
                margin-bottom: 1rem;
            }

            .calorie-ring {
                position: relative;
                width: 140px;
                height: 140px;
                flex-shrink: 0;
            }

            .calorie-ring svg { transform: rotate(-90deg); }

            .calorie-ring-label {
                position: absolute;
                inset: 0;
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
            }

            .calorie-ring-label .ring-value {
                font-size: 1.6rem;
                font-weight: 800;
                color: var(--ink);
                line-height: 1;
            }

            .calorie-ring-label .ring-unit {
                font-size: 0.7rem;
                color: var(--muted);
                text-transform: uppercase;
                letter-spacing: 0.08em;
                margin-top: 0.2rem;
            }

            .calorie-ring-details { flex: 1; }

            .calorie-ring-details .ring-row {
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 0.45rem 0;
                border-bottom: 1px solid var(--border);
            }

            .calorie-ring-details .ring-row:last-child { border-bottom: none; }

            .ring-row-label {
                display: flex;
                align-items: center;
                gap: 0.5rem;
                color: var(--ink-secondary);
                font-size: 0.85rem;
            }

            .ring-row-label .dot {
                width: 8px; height: 8px;
                border-radius: 50%;
                display: inline-block;
            }

            .ring-row-value {
                font-weight: 700;
                color: var(--ink);
                font-size: 0.95rem;
            }

            /* ── Water visual ── */
            .water-visual {
                display: flex;
                gap: 0.35rem;
                flex-wrap: wrap;
                margin: 0.6rem 0;
            }

            .water-glass {
                font-size: 1.4rem;
                opacity: 0.25;
                transition: all 0.3s;
            }

            .water-glass.filled {
                opacity: 1;
                filter: drop-shadow(0 0 4px rgba(59,130,246,0.4));
            }

            /* ── Section header ── */
            .section-head {
                display: flex;
                align-items: center;
                gap: 0.6rem;
                margin: 0.5rem 0 1rem;
            }

            .section-head .sh-icon {
                width: 36px; height: 36px;
                border-radius: 10px;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 1.1rem;
            }

            .section-head .sh-text {
                font-family: 'Playfair Display', serif;
                font-size: 1.25rem;
                font-weight: 600;
                color: var(--ink);
            }

            /* ── Quick-log chips ── */
            .quick-log-row {
                display: flex;
                gap: 0.45rem;
                flex-wrap: wrap;
                margin-bottom: 0.8rem;
            }

            .ql-chip {
                background: rgba(255,255,255,0.04);
                border: 1px solid var(--border);
                border-radius: 20px;
                padding: 0.3rem 0.8rem;
                font-size: 0.78rem;
                color: var(--ink-secondary);
                cursor: default;
                transition: all 0.2s;
            }

            .ql-chip:hover {
                background: rgba(255,107,53,0.1);
                border-color: var(--accent);
                color: var(--accent);
            }

            /* ── Nutrient mini-bar ── */
            .nutrient-bar-wrap {
                display: flex;
                gap: 1rem;
                margin-top: 0.4rem;
            }

            .nutrient-item {
                flex: 1;
                text-align: center;
            }

            .nutrient-item .ni-label {
                font-size: 0.68rem;
                color: var(--muted);
                text-transform: uppercase;
                letter-spacing: 0.08em;
                margin-bottom: 0.25rem;
            }

            .nutrient-item .ni-bar {
                height: 5px;
                border-radius: 3px;
                background: rgba(255,255,255,0.06);
                overflow: hidden;
            }

            .nutrient-item .ni-fill {
                height: 100%;
                border-radius: 3px;
            }

            .nutrient-item .ni-value {
                font-size: 0.75rem;
                font-weight: 600;
                color: var(--ink);
                margin-top: 0.2rem;
            }

            /* ── Responsive ── */
            @media (max-width: 768px) {
                .hero { padding: 1.2rem; border-radius: var(--radius); }
                .stat-card { padding: 0.8rem; }
                .login-card { padding: 1.5rem 1.2rem; }
                .calorie-ring-wrap { flex-direction: column; text-align: center; }
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


def render_stat_card(label: str, value: str, icon: str = "") -> None:
    icon_html = f'<div class="stat-icon">{icon}</div>' if icon else ""
    st.markdown(
        f"""
        <div class="stat-card">
            {icon_html}
            <div class="stat-label">{label}</div>
            <div class="stat-value">{value}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_progress_bar(current: int, goal: int) -> None:
    pct = min(100, int((current / goal) * 100)) if goal > 0 else 0
    remaining = max(0, goal - current)
    if pct >= 100:
        color = "#e74c3c"
        status = "⚠️ Over goal"
    elif pct >= 75:
        color = "#f39c12"
        status = "Almost there"
    else:
        color = "#00d4aa"
        status = f"{remaining} kcal left"

    st.markdown(
        f"""
        <div class="progress-container">
            <div style="display:flex; justify-content:space-between; align-items:baseline; margin-bottom:0.3rem;">
                <span style="color:#a0a0b0; font-size:0.78rem; text-transform:uppercase; letter-spacing:0.06em; font-weight:500;">Daily Progress</span>
                <span style="color:{color}; font-weight:700; font-size:1.1rem;">{pct}%</span>
            </div>
            <div class="progress-bar-track">
                <div class="progress-bar-fill" style="width:{pct}%; background:linear-gradient(90deg, {color}, {color}dd);"></div>
            </div>
            <div style="display:flex; justify-content:space-between; margin-top:0.4rem;">
                <span style="color:#6b6b80; font-size:0.78rem;">{current} / {goal} kcal</span>
                <span style="color:{color}; font-size:0.78rem; font-weight:500;">{status}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_calorie_ring(eaten: int, goal: int, remaining: int, burned: int = 0) -> None:
    """SVG donut ring like MyFitnessPal's home screen."""
    pct = min(100, int((eaten / goal) * 100)) if goal > 0 else 0
    stroke_color = "#00d4aa" if pct < 75 else ("#f39c12" if pct < 100 else "#e74c3c")
    circumference = 2 * 3.14159 * 56
    offset = circumference * (1 - pct / 100)
    st.markdown(
        f"""
        <div class="calorie-ring-wrap">
            <div class="calorie-ring">
                <svg viewBox="0 0 128 128" width="140" height="140">
                    <circle cx="64" cy="64" r="56" fill="none" stroke="rgba(255,255,255,0.06)" stroke-width="10"/>
                    <circle cx="64" cy="64" r="56" fill="none" stroke="{stroke_color}" stroke-width="10"
                        stroke-dasharray="{circumference}" stroke-dashoffset="{offset}"
                        stroke-linecap="round" style="transition: stroke-dashoffset 0.8s cubic-bezier(.4,0,.2,1);"/>
                </svg>
                <div class="calorie-ring-label">
                    <span class="ring-value">{remaining}</span>
                    <span class="ring-unit">remaining</span>
                </div>
            </div>
            <div class="calorie-ring-details">
                <div class="ring-row">
                    <span class="ring-row-label"><span class="dot" style="background:#6c5ce7;"></span>Base Goal</span>
                    <span class="ring-row-value">{goal}</span>
                </div>
                <div class="ring-row">
                    <span class="ring-row-label"><span class="dot" style="background:{stroke_color};"></span>Food</span>
                    <span class="ring-row-value">{eaten}</span>
                </div>
                <div class="ring-row">
                    <span class="ring-row-label"><span class="dot" style="background:#3b82f6;"></span>Exercise</span>
                    <span class="ring-row-value">{burned}</span>
                </div>
                <div class="ring-row" style="border-bottom:none; padding-top:0.6rem;">
                    <span class="ring-row-label" style="font-weight:600; color:var(--ink);">Remaining</span>
                    <span class="ring-row-value" style="color:{stroke_color}; font-size:1.1rem;">{remaining}</span>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_water_visual(intake: int, goal: int) -> None:
    """Visual water glasses display."""
    glasses_html = ""
    for i in range(goal):
        filled = "filled" if i < intake else ""
        glasses_html += f'<span class="water-glass {filled}">💧</span>'
    pct = min(100, int((intake / goal) * 100)) if goal > 0 else 0
    st.markdown(
        f"""
        <div class="progress-container">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.5rem;">
                <span style="color:var(--ink); font-weight:600; font-size:0.95rem;">💧 Water Intake</span>
                <span style="color:#3b82f6; font-weight:700; font-size:1.1rem;">{intake}/{goal}</span>
            </div>
            <div class="water-visual">{glasses_html}</div>
            <div class="progress-bar-track" style="margin-top:0.6rem;">
                <div class="progress-bar-fill" style="width:{pct}%; background:linear-gradient(90deg, #3b82f6, #60a5fa);"></div>
            </div>
            <div style="text-align:right; margin-top:0.3rem;">
                <span style="color:#6b6b80; font-size:0.75rem;">{pct}% of daily goal</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_section_header(icon: str, text: str, bg_color: str = "rgba(255,107,53,0.12)") -> None:
    st.markdown(
        f"""
        <div class="section-head">
            <div class="sh-icon" style="background:{bg_color};">{icon}</div>
            <div class="sh-text">{text}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def load_dashboard_data(api_base_url: str) -> tuple[list[dict], dict, dict]:
    foods = api_call("GET", "/api/foods", api_base_url).get("foods", [])
    log_data = api_call("GET", "/api/log", api_base_url)
    user = api_call("GET", "/api/user", api_base_url).get("user", {})
    return foods, log_data, user


def get_goal_value(user: dict) -> int:
    """Calculate daily calorie goal based on user profile."""
    if "daily_calorie_target" in user:
        return int(user["daily_calorie_target"])

    # BMR calculation using Mifflin-St Jeor Equation
    age = user.get("age", 25)
    weight = user.get("weight", 70)  # kg
    height = user.get("height", 175)  # cm
    goal = user.get("goal", "Maintain")

    # BMR for men (assuming male for simplicity)
    bmr = 10 * weight + 6.25 * height - 5 * age + 5

    if goal == "Lose":
        return int(bmr * 0.8)  # 20% deficit
    elif goal == "Gain":
        return int(bmr * 1.2)  # 20% surplus
    else:  # Maintain
        return int(bmr)


def calculate_bmi(user: dict) -> str:
    """Calculate BMI from user data."""
    try:
        height_m = user.get("height", 175) / 100
        weight = user.get("weight", 70)
        if height_m > 0:
            bmi = weight / (height_m * height_m)
            return f"{bmi:.1f}"
        return "N/A"
    except (TypeError, ZeroDivisionError):
        return "N/A"


def bmi_category(bmi: float) -> str:
    """Get BMI category."""
    if bmi < 18.5:
        return "Underweight"
    elif bmi < 25:
        return "Normal"
    elif bmi < 30:
        return "Overweight"
    else:
        return "Obese"


def load_users(api_base_url: str) -> list[dict]:
    return api_call("GET", "/api/users", api_base_url).get("users", [])


def get_current_user_name(api_base_url: str) -> str:
    try:
        user = api_call("GET", "/api/user", api_base_url).get("user", {})
        return user.get("name", "Dawood")
    except requests.RequestException:
        return "Dawood"


def show_login_screen() -> None:
    # Hide sidebar on login
    st.markdown("<style>[data-testid='stSidebar']{display:none;}</style>", unsafe_allow_html=True)

    # ── Compact centered login ──
    _, center, _ = st.columns([1, 2.4, 1])
    with center:
        st.markdown(
            """
            <div style="text-align:center; padding-top:2rem;">
                <div class="login-logo">🍜</div>
                <div class="login-title" style="font-size:1.8rem; margin-bottom:0.2rem;">HK Calorie Tracker</div>
                <div class="login-subtitle" style="margin-bottom:1.2rem;">Your personal Hong Kong nutrition companion</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        api_base_url = DEFAULT_API_URL

        try:
            users = load_users(api_base_url)
        except requests.RequestException:
            st.error("Cannot connect to API — make sure Flask backend is running on port 5050.")
            with st.expander("⚙️ Custom API URL"):
                api_base_url = st.text_input("API URL", value=DEFAULT_API_URL, key="login_api_url")
            return

        # ── Sign-in / Create Account tabs ──
        sign_in, sign_up = st.tabs(["🔓 Sign In", "✨ Create Account"])

        with sign_in:
            if not users:
                st.markdown(
                    """
                    <div style="text-align:center; padding:1.5rem 0; color:var(--muted);">
                        <div style="font-size:2.5rem; margin-bottom:0.5rem;">👋</div>
                        <p style="font-size:1rem; margin:0;">No profiles yet</p>
                        <p style="font-size:0.85rem; color:var(--muted);">Head to <b>Create Account</b> to get started</p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            else:
                user_names = [u["name"] for u in users]
                selected_user = st.selectbox(
                    "Profile",
                    user_names,
                    key="login_user_select",
                    label_visibility="collapsed",
                    format_func=lambda n: f"👤  {n}",
                )
                st.markdown("<div style='height:0.3rem'></div>", unsafe_allow_html=True)
                if st.button("Sign In →", type="primary", use_container_width=True):
                    try:
                        api_call("POST", "/api/users/select", api_base_url, {"name": selected_user})
                        st.session_state["logged_in_user"] = selected_user
                        st.session_state["api_base_url"] = api_base_url
                        st.rerun()
                    except requests.RequestException as err:
                        st.error(f"Login failed: {err}")

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

            if st.button("Create Account →", type="primary", use_container_width=True):
                if not new_name.strip():
                    st.error("Name is required.")
                elif users and new_name.strip().lower() in {u["name"].lower() for u in users}:
                    st.warning("This name already exists.")
                else:
                    try:
                        api_call(
                            "POST", "/api/users", api_base_url,
                            {"name": new_name.strip(), "age": int(new_age), "weight": float(new_weight),
                             "height": float(new_height), "goal": new_goal},
                        )
                        st.success(f"Welcome, {new_name.strip()}! Switch to Sign In.")
                        st.rerun()
                    except requests.RequestException as err:
                        st.error(f"Could not create profile: {err}")

        # ── Feature pills ──
        st.markdown(
            """
            <div class="login-features" style="margin-top:1.2rem;">
                <div class="login-feature"><div class="login-feature-icon">🔥</div>Calories</div>
                <div class="login-feature"><div class="login-feature-icon">💧</div>Water</div>
                <div class="login-feature"><div class="login-feature-icon">📊</div>History</div>
                <div class="login-feature"><div class="login-feature-icon">🍜</div>HK Foods</div>
            </div>
            <p style="text-align:center; color:#4a4a5a; font-size:0.72rem; margin-top:1rem; letter-spacing:0.04em;">
                Track meals · Set goals · Stay healthy
            </p>
            """,
            unsafe_allow_html=True,
        )


def show_main_dashboard() -> None:
    api_base_url = st.session_state.get("api_base_url", DEFAULT_API_URL)
    logged_in_user = st.session_state["logged_in_user"]

    with st.sidebar:
        st.markdown(
            f"""
            <div class="sidebar-badge">
                <div class="badge-icon">🍜</div>
                <div class="badge-title">{logged_in_user}</div>
                <div class="badge-sub">Active Profile</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown("---")

        st.markdown("## Connection")
        api_base_url_input = st.text_input("Flask API URL", value=api_base_url, key="dashboard_api_url")
        if api_base_url_input != api_base_url:
            st.session_state["api_base_url"] = api_base_url_input
            api_base_url = api_base_url_input

        if st.button("Check API Health"):
            try:
                health = api_call("GET", "/health", api_base_url)
                st.success(f"API reachable: {health.get('status', 'unknown')}")
            except requests.RequestException as err:
                st.error(f"API not reachable: {err}")

        st.markdown("---")

        if st.button("Logout", type="secondary"):
            if "logged_in_user" in st.session_state:
                del st.session_state["logged_in_user"]
            if "api_base_url" in st.session_state:
                del st.session_state["api_base_url"]
            st.success("Logged out successfully!")
            st.rerun()

        st.markdown("---")

        try:
            users = load_users(api_base_url)
        except requests.RequestException:
            users = []

        if users:
            user_names = [user["name"] for user in users]
            current_name = st.session_state.get("logged_in_user", get_current_user_name(api_base_url))
            if current_name in user_names:
                selected_index = user_names.index(current_name)
            else:
                selected_index = 0

            selected_profile = st.selectbox("Switch profile", user_names, index=selected_index, key="switch_profile")
            if st.button("Switch profile"):
                try:
                    api_call("POST", "/api/users/select", api_base_url, {"name": selected_profile})
                    st.session_state["logged_in_user"] = selected_profile
                    st.success(f"Switched to profile: {selected_profile}")
                    st.rerun()
                except requests.RequestException as err:
                    st.error(f"Could not switch profile: {err}")
        else:
            st.info("No profiles found. Create a new profile below.")

        with st.expander("Create a new profile"):
            new_name = st.text_input("Name", key="new_name")
            new_age = st.number_input("Age", min_value=1, step=1, key="new_age")
            new_weight = st.number_input("Weight (kg)", min_value=1.0, step=0.5, key="new_weight")
            new_height = st.number_input("Height (cm)", min_value=1.0, step=0.5, key="new_height")
            new_goal = st.selectbox("Goal", options=["Maintain", "Lose", "Gain"], key="new_goal")

            if st.button("Create profile"):
                if not new_name.strip():
                    st.error("Name is required.")
                elif new_name.strip().lower() in {user["name"].lower() for user in users}:
                    st.warning("A profile with this name already exists.")
                else:
                    try:
                        api_call(
                            "POST",
                            "/api/users",
                            api_base_url,
                            {
                                "name": new_name,
                                "age": int(new_age),
                                "weight": float(new_weight),
                                "height": float(new_height),
                                "goal": new_goal,
                            },
                        )
                        st.success("Profile created.")
                        st.rerun()
                    except requests.RequestException as err:
                        st.error(f"Could not create profile: {err}")

        if len(users) > 1:
            with st.expander("Delete a profile"):
                delete_name = st.selectbox("Select profile to delete", [u["name"] for u in users], key="delete_name")
                confirm_delete = st.checkbox("I confirm I want to delete this profile", key="confirm_delete")
                if st.button("Delete profile"):
                    if not confirm_delete:
                        st.error("Please confirm deletion.")
                    else:
                        try:
                            api_call("DELETE", "/api/users", api_base_url, {"name": delete_name})
                            st.success(f"Profile '{delete_name}' deleted.")
                            if st.session_state.get("logged_in_user") == delete_name:
                                del st.session_state["logged_in_user"]
                                st.rerun()
                            st.rerun()
                        except requests.RequestException as err:
                            st.error(f"Could not delete profile: {err}")

        st.markdown("---")
        st.markdown("#### Controls")
        st.caption("Run Flask first, then this Streamlit app.")
        st.markdown("---")
        st.markdown("#### About")
        st.write("Build your Hong Kong calorie tracker with a modern UI for meals, metrics, and progress.")

    # ── Load data from backend ──
    try:
        foods, log_data, user = load_dashboard_data(api_base_url)
    except requests.RequestException as err:
        st.error("Could not load data from backend. Start Flask API and check the URL in the sidebar.")
        st.exception(err)
        return

    calorie_status = log_data.get("total_calories", 0)
    goal_value = get_goal_value(user)
    water_intake = user.get("water_intake", 0)
    water_goal = user.get("water_goal", 8)
    streak = user.get("streak", 0)

    st.markdown(
        f"""
        <section class="hero">
            <div style="display:flex; justify-content: space-between; align-items: center; gap: 1rem; flex-wrap: wrap;">
                <div>
                    <h1 style="margin:0 0 0.3rem;">Good {'morning' if datetime.datetime.now().hour < 12 else 'afternoon' if datetime.datetime.now().hour < 18 else 'evening'}, {logged_in_user} 👋</h1>
                    <p style="margin:0; color:var(--ink-secondary);">Here's your nutrition overview for today.</p>
                </div>
                <div style="text-align:right; min-width: 160px;">
                    <p style="margin:0; color:var(--accent-2); font-weight:700; letter-spacing:0.12em; text-transform:uppercase; font-size:0.8rem;">🔥 {streak} Day Streak</p>
                    <p style="margin:0.3rem 0 0; color:var(--muted); font-size:0.82rem;">{datetime.date.today().strftime('%B %d, %Y')}</p>
                </div>
            </div>
        </section>
        """,
        unsafe_allow_html=True,
    )

    # ── Calorie Ring + Quick Stats ──
    ring_left, ring_right = st.columns([0.55, 0.45], gap="large")
    with ring_left:
        render_calorie_ring(calorie_status, goal_value, max(0, goal_value - calorie_status))
    with ring_right:
        mini_a, mini_b = st.columns(2, gap="medium")
        with mini_a:
            render_stat_card("Eaten", f"{calorie_status} kcal", "🔥")
        with mini_b:
            render_stat_card("Remaining", f"{max(0, goal_value - calorie_status)} kcal", "🎯")
        mini_c, mini_d = st.columns(2, gap="medium")
        with mini_c:
            render_stat_card("Water", f"{water_intake}/{water_goal}", "💧")
        with mini_d:
            render_stat_card("Entries", str(log_data.get("entry_count", 0)), "📝")

    render_progress_bar(calorie_status, goal_value)

    if calorie_status > goal_value:
        st.error("⚠️ You've exceeded your daily calorie goal!")
    elif calorie_status > 0:
        st.success("✅ You're within your calorie budget. Keep going!")

    st.markdown("<div class='theme-divider'></div>", unsafe_allow_html=True)

    # ── Tabbed Interface ──
    tab_diary, tab_water, tab_foods, tab_goals, tab_history = st.tabs(
        ["📋 Food Diary", "💧 Water", "🥢 Foods", "🎯 Goals & BMI", "📊 History"]
    )

    # ── TAB: Food Diary ──
    with tab_diary:
        render_section_header("📋", "Food Diary", "rgba(0,212,170,0.12)")

        # Meal breakdown cards
        meal_totals = log_data.get("meal_totals", {})
        if meal_totals:
            meal_icons = {"Breakfast": "🍳", "Lunch": "🍜", "Dinner": "🍕", "Snack": "🍪", "General": "🍽️"}
            meal_cols = st.columns(len(meal_totals), gap="medium")
            for i, (meal_name, meal_cal) in enumerate(meal_totals.items()):
                with meal_cols[i]:
                    icon = meal_icons.get(meal_name, "🍽️")
                    render_stat_card(meal_name, f"{meal_cal} kcal", icon)
            st.markdown("<div class='theme-divider'></div>", unsafe_allow_html=True)

        diary_left, diary_right = st.columns([0.55, 0.45], gap="large")

        with diary_left:
            if log_data.get("entries"):
                for entry in log_data["entries"]:
                    meal_icon = {"Breakfast": "🍳", "Lunch": "🍜", "Dinner": "🍕", "Snack": "🍪"}.get(entry.get("meal", ""), "🍽️")
                    st.markdown(
                        f"""
                        <div class="entry-row">
                            <span style="flex:0.3; text-align:center;">{meal_icon}</span>
                            <span class="entry-name">{entry["food_name"]}</span>
                            <span class="entry-qty">{entry["quantity"]}x</span>
                            <span class="entry-cal">{entry["total_calories"]} kcal</span>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
            else:
                st.info("No food logged yet today. Use the form to start tracking!")

        with diary_right:
            st.markdown("**Quick Log**")
            with st.form("log_form"):
                selected_food = st.selectbox("Select food", [f["name"] for f in foods], key="log_food_select")
                q_col, m_col = st.columns(2)
                with q_col:
                    quantity = st.number_input("Qty", min_value=1, step=1, value=1, key="log_quantity")
                with m_col:
                    meal_type = st.selectbox("Meal", ["Breakfast", "Lunch", "Dinner", "Snack", "General"], key="log_meal_type")
                log_button = st.form_submit_button("Log Food", use_container_width=True)

                if log_button and foods:
                    food_data = next((f for f in foods if f["name"] == selected_food), None)
                    if food_data:
                        try:
                            api_call("POST", "/api/log", api_base_url,
                                     {"food_name": selected_food, "quantity": int(quantity), "meal": meal_type})
                            st.success(f"Logged {quantity}x {selected_food}")
                            st.rerun()
                        except requests.RequestException as err:
                            st.error(f"Could not log food: {err}")

            if st.button("🔄 Reset Day", use_container_width=True):
                try:
                    api_call("DELETE", "/api/log", api_base_url)
                    st.success("Day reset successfully")
                    st.rerun()
                except requests.RequestException as err:
                    st.error(f"Could not reset day: {err}")

    # ── TAB: Water ──
    with tab_water:
        render_section_header("💧", "Water Tracker", "rgba(59,130,246,0.12)")

        w_left, w_right = st.columns([0.6, 0.4], gap="large")
        with w_left:
            render_water_visual(water_intake, water_goal)
        with w_right:
            glasses_to_add = st.number_input("Glasses to add", min_value=1, max_value=10, step=1, value=1, key="water_add")
            if st.button("💧 Log Water", use_container_width=True):
                try:
                    api_call("POST", "/api/water", api_base_url, {"glasses": int(glasses_to_add)})
                    st.success(f"Added {glasses_to_add} glass(es)!")
                    st.rerun()
                except requests.RequestException as err:
                    st.error(f"Could not log water: {err}")
            st.markdown("---")
            new_water_goal = st.number_input("Daily goal (glasses)", min_value=1, max_value=20, step=1, value=water_goal, key="water_goal_input")
            if st.button("Set Water Goal", use_container_width=True):
                try:
                    api_call("PUT", "/api/water/goal", api_base_url, {"goal": int(new_water_goal)})
                    st.success(f"Goal set to {new_water_goal} glasses")
                    st.rerun()
                except requests.RequestException as err:
                    st.error(f"Could not set goal: {err}")

    # ── TAB: Foods ──
    with tab_foods:
        render_section_header("🥢", "Food Database", "rgba(108,92,231,0.12)")

        foods_left, foods_right = st.columns([0.5, 0.5], gap="large")
        with foods_left:
            st.markdown("**Add New Food**")
            with st.form("food_form"):
                food_name = st.text_input("Food name", placeholder="e.g. Char Siu Rice")
                fc1, fc2 = st.columns(2)
                with fc1:
                    food_calories = st.number_input("Calories", min_value=1, step=10, value=300)
                with fc2:
                    food_category = st.selectbox("Category", options=["Food", "Drink", "Snack", "Dessert", "General"])
                submitted = st.form_submit_button("Add Food", use_container_width=True)
                if submitted:
                    try:
                        api_call("POST", "/api/foods", api_base_url,
                                 {"name": food_name, "calories": int(food_calories), "category": food_category})
                        st.success("Food added!")
                        st.rerun()
                    except requests.RequestException as err:
                        st.error(f"Could not add food: {err}")

        with foods_right:
            st.markdown(f"**{len(foods)} foods in database**")
            if foods:
                # Quick category filter
                categories = sorted({f.get("category", "General") for f in foods})
                cat_filter = st.selectbox("Filter by category", ["All"] + categories, key="food_cat_filter")
                filtered = foods if cat_filter == "All" else [f for f in foods if f.get("category") == cat_filter]
                st.dataframe(filtered, use_container_width=True, hide_index=True, height=400)

    # ── TAB: Goals & BMI ──
    with tab_goals:
        render_section_header("🎯", "Goals & BMI", "rgba(255,107,53,0.12)")

        g_left, g_right = st.columns([0.5, 0.5], gap="large")
        with g_left:
            st.markdown("**Calorie Goal**")
            current_target = int(user.get("daily_calorie_target", goal_value))
            new_target = st.number_input("Daily calorie target (kcal)", min_value=800, max_value=10000, step=50, value=current_target, key="goal_target")
            if st.button("Save Calorie Goal", use_container_width=True):
                try:
                    api_call("PUT", "/api/user", api_base_url, {
                        "name": user.get("name", ""),
                        "age": int(user.get("age", 20)),
                        "weight": float(user.get("weight", 70)),
                        "height": float(user.get("height", 175)),
                        "goal": user.get("goal", "Maintain"),
                        "daily_calorie_target": int(new_target),
                    })
                    st.success(f"Goal set to {new_target} kcal")
                    st.rerun()
                except requests.RequestException as err:
                    st.error(f"Could not save goal: {err}")
            st.metric("Current Goal", f"{current_target} kcal")

        with g_right:
            st.markdown("**BMI Calculator**")
            calc_height = st.number_input("Height (cm)", min_value=1.0, step=0.5, value=float(user.get("height", 175)), key="bmi_height")
            calc_weight = st.number_input("Weight (kg)", min_value=1.0, step=0.5, value=float(user.get("weight", 70)), key="bmi_weight")
            if st.button("Calculate BMI", use_container_width=True):
                try:
                    height_m = calc_height / 100
                    bmi_result = calc_weight / (height_m * height_m)
                    bmi_cat = bmi_category(bmi_result)
                    st.metric("Your BMI", f"{bmi_result:.1f}", bmi_cat)
                except ZeroDivisionError:
                    st.error("Height must be greater than 0")

    # ── TAB: History ──
    with tab_history:
        render_section_header("📊", "Weekly History", "rgba(0,212,170,0.12)")

        history = user.get("weekly_history", [])
        if history and len(history) > 0:
            hist_left, hist_right = st.columns([0.6, 0.4], gap="large")
            with hist_left:
                st.bar_chart(history)
            with hist_right:
                history_rows = [{"Day": f"Day {i + 1}", "Calories": value} for i, value in enumerate(history)]
                st.table(history_rows)
                avg_cal = sum(history) / len(history) if history else 0
                st.metric("7-Day Average", f"{avg_cal:.0f} kcal")
        else:
            st.info("No weekly history yet. Log food and reset the day to build history.")


def main() -> None:
    st.set_page_config(page_title="HK Calorie Tracker", page_icon="🍜", layout="wide")
    inject_styles()

    # Check if user is logged in
    if "logged_in_user" not in st.session_state:
        show_login_screen()
        return

    # User is logged in, show main dashboard
    show_main_dashboard()


if __name__ == "__main__":
    if not st.runtime.exists() and os.environ.get("STREAMLIT_RUN_FROM_CLI") != "true":
        print("This is a Streamlit app. Run: streamlit run streamlit_app.py")
    else:
        main()
