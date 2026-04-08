"""Streamlit frontend for HK Calorie Tracker.

This UI talks to the Flask API and does not access tracker internals directly.
"""

from __future__ import annotations

import os
import requests
import streamlit as st


DEFAULT_API_URL = "http://127.0.0.1:5050"


def inject_styles() -> None:
    st.markdown(
        """
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;700&family=Fraunces:opsz,wght@9..144,500;9..144,700&display=swap');

            :root {
                --bg: #f4f1e9;
                --panel: #fff8ee;
                --ink: #1f1b16;
                --accent: #cf5c36;
                --accent-2: #2f6f66;
                --muted: #76685b;
            }

            .stApp {
                background:
                    radial-gradient(circle at 10% 20%, rgba(207,92,54,0.18), transparent 28%),
                    radial-gradient(circle at 92% 8%, rgba(47,111,102,0.2), transparent 24%),
                    linear-gradient(145deg, #f4f1e9 0%, #ede6d8 55%, #e8ddca 100%);
                color: var(--ink);
                font-family: 'Space Grotesk', sans-serif;
            }

            h1, h2, h3 {
                font-family: 'Fraunces', serif;
                letter-spacing: 0.2px;
                color: var(--ink);
            }

            .hero {
                background: linear-gradient(120deg, rgba(255,248,238,0.95), rgba(255,241,220,0.95));
                border: 1px solid rgba(31,27,22,0.1);
                border-radius: 22px;
                padding: 1.2rem 1.4rem;
                box-shadow: 0 12px 30px rgba(31,27,22,0.08);
                margin-bottom: 0.8rem;
                animation: floatIn 0.6s ease-out;
            }

            .stat-card {
                background: var(--panel);
                border: 1px solid rgba(31,27,22,0.1);
                border-radius: 16px;
                padding: 0.8rem 1rem;
                box-shadow: 0 8px 20px rgba(31,27,22,0.06);
                margin-bottom: 0.6rem;
                animation: rise 0.5s ease-out;
            }

            .stat-label {
                color: var(--muted);
                font-size: 0.86rem;
                letter-spacing: 0.2px;
            }

            .stat-value {
                font-size: 1.35rem;
                font-weight: 700;
                color: var(--accent-2);
            }

            [data-testid="stSidebar"] {
                background: linear-gradient(180deg, #fff7eb 0%, #f3ebde 100%);
                border-right: 1px solid rgba(31,27,22,0.08);
            }

            @keyframes floatIn {
                from { opacity: 0; transform: translateY(8px); }
                to { opacity: 1; transform: translateY(0); }
            }

            @keyframes rise {
                from { opacity: 0; transform: translateY(6px); }
                to { opacity: 1; transform: translateY(0); }
            }

            @media (max-width: 900px) {
                .hero {
                    padding: 1rem;
                }
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


def render_stat_card(label: str, value: str) -> None:
    st.markdown(
        f"""
        <div class="stat-card">
            <div class="stat-label">{label}</div>
            <div class="stat-value">{value}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def load_dashboard_data(api_base_url: str) -> tuple[list[dict], dict, dict]:
    foods = api_call("GET", "/api/foods", api_base_url).get("foods", [])
    log_data = api_call("GET", "/api/log", api_base_url)
    user = api_call("GET", "/api/user", api_base_url).get("user", {})
    return foods, log_data, user


def main() -> None:
    st.set_page_config(page_title="HK Calorie Tracker", page_icon="🍜", layout="wide")
    inject_styles()

    with st.sidebar:
        st.header("Connection")
        api_base_url = st.text_input("Flask API URL", value=DEFAULT_API_URL)

        if st.button("Check API Health"):
            try:
                health = api_call("GET", "/health", api_base_url)
                st.success(f"API reachable: {health.get('status', 'unknown')}")
            except requests.RequestException as err:
                st.error(f"API not reachable: {err}")

        st.markdown("---")
        st.caption("Run Flask first, then this Streamlit app.")

    st.markdown(
        """
        <section class="hero">
            <h1>HK Calorie Tracker</h1>
            <p>Track your day with a clean workflow: manage foods, log meals, and monitor totals in real time.</p>
        </section>
        """,
        unsafe_allow_html=True,
    )

    try:
        foods, log_data, user = load_dashboard_data(api_base_url)
    except requests.RequestException as err:
        st.error("Could not load data from backend. Start Flask API and check the URL in the sidebar.")
        st.exception(err)
        return

    col_a, col_b, col_c = st.columns(3)
    with col_a:
        render_stat_card("Foods in Database", str(len(foods)))
    with col_b:
        render_stat_card("Today's Entries", str(log_data.get("entry_count", 0)))
    with col_c:
        render_stat_card("Total Calories", str(log_data.get("total_calories", 0)))

    st.subheader("User Profile")
    with st.form("user_form"):
        c1, c2, c3, c4, c5 = st.columns(5)
        name = c1.text_input("Name", value=str(user.get("name", "")))
        age = c2.number_input("Age", min_value=1, step=1, value=int(user.get("age", 20)))
        weight = c3.number_input("Weight (kg)", min_value=1.0, step=0.5, value=float(user.get("weight", 70)))
        height = c4.number_input("Height (cm)", min_value=1.0, step=0.5, value=float(user.get("height", 175)))
        goal = c5.selectbox("Goal", options=["Maintain", "Lose", "Gain"], index=["Maintain", "Lose", "Gain"].index(str(user.get("goal", "Maintain"))) if str(user.get("goal", "Maintain")) in ["Maintain", "Lose", "Gain"] else 0)

        if st.form_submit_button("Update Profile", use_container_width=True):
            try:
                api_call(
                    "PUT",
                    "/api/user",
                    api_base_url,
                    {
                        "name": name,
                        "age": int(age),
                        "weight": float(weight),
                        "height": float(height),
                        "goal": goal,
                    },
                )
                st.success("Profile updated")
                st.rerun()
            except requests.RequestException as err:
                st.error(f"Could not update profile: {err}")

    left, right = st.columns([1, 1], gap="large")

    with left:
        st.subheader("Food Database")
        with st.form("food_form"):
            food_name = st.text_input("Food name", placeholder="e.g. Pineapple Bun")
            food_calories = st.number_input("Calories", min_value=1, step=10, value=300)
            submitted = st.form_submit_button("Add Food", use_container_width=True)

            if submitted:
                try:
                    api_call(
                        "POST",
                        "/api/foods",
                        api_base_url,
                        {"name": food_name, "calories": int(food_calories)},
                    )
                    st.success("Food added to database")
                    st.rerun()
                except requests.RequestException as err:
                    st.error(f"Could not add food: {err}")

        st.dataframe(foods, use_container_width=True, hide_index=True)

    with right:
        st.subheader("Daily Log")
        food_options = [item["name"] for item in foods] if foods else []

        with st.form("log_form"):
            selected = st.selectbox("Choose food to log", options=food_options, disabled=not food_options)
            log_submit = st.form_submit_button("Log Food", use_container_width=True)

            if log_submit and selected:
                try:
                    api_call("POST", "/api/log", api_base_url, {"food_name": selected})
                    st.success(f"Logged: {selected}")
                    st.rerun()
                except requests.RequestException as err:
                    st.error(f"Could not log food: {err}")

        entries = log_data.get("entries", [])
        st.dataframe(entries, use_container_width=True, hide_index=True)

        if st.button("Reset Day", type="secondary", use_container_width=True):
            try:
                api_call("DELETE", "/api/log", api_base_url)
                st.success("Daily log reset")
                st.rerun()
            except requests.RequestException as err:
                st.error(f"Could not reset log: {err}")


if __name__ == "__main__":
    if not st.runtime.exists() and os.environ.get("STREAMLIT_RUN_FROM_CLI") != "true":
        print("This is a Streamlit app. Run: streamlit run streamlit_app.py")
    else:
        main()
