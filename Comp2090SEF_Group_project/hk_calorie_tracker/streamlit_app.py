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
                --bg: #0f0f0f;
                --panel: #1a1a1a;
                --ink: #ffffff;
                --accent: #ff6b35;
                --accent-2: #00d4aa;
                --muted: #888888;
                --border: #333333;
                --shadow: rgba(0,0,0,0.3);
            }

            .stApp {
                background:
                    radial-gradient(circle at 10% 20%, rgba(255,107,53,0.15), transparent 28%),
                    radial-gradient(circle at 92% 8%, rgba(0,212,170,0.1), transparent 24%),
                    linear-gradient(145deg, #0f0f0f 0%, #1a1a1a 55%, #141414 100%);
                color: var(--ink);
                font-family: 'Space Grotesk', sans-serif;
            }

            h1, h2, h3 {
                font-family: 'Fraunces', serif;
                letter-spacing: 0.2px;
                color: var(--ink);
            }

            .hero {
                background: linear-gradient(120deg, rgba(26,26,26,0.95), rgba(20,20,20,0.95));
                border: 1px solid var(--border);
                border-radius: 22px;
                padding: 1.2rem 1.4rem;
                box-shadow: 0 12px 30px var(--shadow);
                margin-bottom: 0.8rem;
                animation: floatIn 0.6s ease-out;
            }

            .stat-card {
                background: var(--panel);
                border: 1px solid var(--border);
                border-radius: 16px;
                padding: 0.8rem 1rem;
                box-shadow: 0 8px 20px var(--shadow);
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
                background: linear-gradient(180deg, #1a1a1a 0%, #141414 100%);
                border-right: 1px solid var(--border);
            }

            /* Dark theme for Streamlit components */
            .stTextInput, .stNumberInput, .stSelectbox, .stTextArea, .stSlider {
                background-color: var(--panel) !important;
                color: var(--ink) !important;
                border: 1px solid var(--border) !important;
            }

            .stTextInput input, .stNumberInput input, .stSelectbox select, .stTextArea textarea {
                background-color: var(--panel) !important;
                color: var(--ink) !important;
                border: none !important;
            }

            .stButton button {
                background: linear-gradient(135deg, var(--accent), var(--accent-2)) !important;
                color: white !important;
                border: none !important;
                transition: all 0.3s ease !important;
            }

            .stButton button:hover {
                transform: translateY(-2px) !important;
                box-shadow: 0 8px 20px rgba(255,107,53,0.3) !important;
            }

            .stSuccess, .stInfo, .stWarning, .stError {
                background-color: var(--panel) !important;
                color: var(--ink) !important;
                border: 1px solid var(--border) !important;
            }

            .stDataFrame {
                background-color: var(--panel) !important;
                color: var(--ink) !important;
                border: 1px solid var(--border) !important;
            }

            .stDataFrame th, .stDataFrame td {
                background-color: var(--panel) !important;
                color: var(--ink) !important;
                border-color: var(--border) !important;
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


def render_stat_card(label: str, value: str, icon: str = "") -> None:
    icon_html = f'<div style="font-size: 1.5rem; margin-bottom: 0.5rem;">{icon}</div>' if icon else ""
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
    st.markdown(
        """
        <div style="display: flex; justify-content: center; align-items: center; min-height: 80vh;">
            <div style="text-align: center; max-width: 400px;">
                <h1 style="color: #00d4aa; margin-bottom: 2rem;">🍜 HK Calorie Tracker</h1>
                <p style="color: #cccccc; margin-bottom: 2rem; font-size: 1.1rem;">Select your profile to continue tracking your calories</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Center the login form
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("### Login to Your Profile")

        api_base_url = st.text_input("API URL (optional)", value=DEFAULT_API_URL, key="login_api_url")

        try:
            users = load_users(api_base_url)
        except requests.RequestException:
            st.error("Could not connect to API. Please check the URL and ensure the backend is running.")
            return

        if not users:
            st.warning("No user profiles found. Create your first profile below.")
        else:
            user_names = [user["name"] for user in users]

            selected_user = st.selectbox("Select your profile", user_names, key="login_user_select")

            if st.button("Login", type="primary", use_container_width=True):
                try:
                    # Switch to selected user
                    api_call("POST", "/api/users/select", api_base_url, {"name": selected_user})
                    st.session_state["logged_in_user"] = selected_user
                    st.session_state["api_base_url"] = api_base_url
                    st.success(f"Welcome back, {selected_user}!")
                    st.rerun()
                except requests.RequestException as err:
                    st.error(f"Could not login: {err}")

        st.markdown("---")
        st.markdown("### Create New Profile")

        new_name = st.text_input("Name", key="login_new_name")
        new_age = st.number_input("Age", min_value=1, step=1, key="login_new_age")
        new_weight = st.number_input("Weight (kg)", min_value=1.0, step=0.5, key="login_new_weight")
        new_height = st.number_input("Height (cm)", min_value=1.0, step=0.5, key="login_new_height")
        new_goal = st.selectbox("Goal", options=["Maintain", "Lose", "Gain"], key="login_new_goal")

        if st.button("Create Profile", type="primary", use_container_width=True):
            if not new_name.strip():
                st.error("Name is required.")
            elif users and new_name.strip().lower() in {user["name"].lower() for user in users}:
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
                    st.success(f"Profile '{new_name}' created! You can now login.")
                    st.rerun()
                except requests.RequestException as err:
                    st.error(f"Could not create profile: {err}")


def show_main_dashboard() -> None:
    api_base_url = st.session_state.get("api_base_url", DEFAULT_API_URL)
    logged_in_user = st.session_state["logged_in_user"]

    with st.sidebar:
        st.markdown(f"## Welcome, {logged_in_user}")
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

    st.markdown(
        """
        <section class="hero">
            <div style="display:flex; justify-content: space-between; align-items: center; gap: 1rem; flex-wrap: wrap;">
                <div>
                    <h1>HK Calorie Tracker</h1>
                    <p>Track meals, manage foods, and stay within your daily calorie goal with a clean fitness-style dashboard.</p>
                </div>
                <div style="text-align:right; min-width: 180px;">
                    <p style="margin:0; color:#00d4aa; font-weight:700; letter-spacing:0.16em; text-transform:uppercase;">Health Mode</p>
                    <p style="margin:0.35rem 0 0; color:#cccccc;">Balanced meals, energy, and progress in one place.</p>
                </div>
            </div>
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

    calorie_status = log_data.get("total_calories", 0)
    goal_value = get_goal_value(user)
    bmi_value = calculate_bmi(user)
    bmi_label = bmi_category(float(bmi_value)) if bmi_value != "N/A" else ""

    col_a, col_b, col_c, col_d = st.columns([1, 1, 1, 1], gap="large")
    with col_a:
        render_stat_card("Foods in database", str(len(foods)), "🥢")
    with col_b:
        render_stat_card("Today's entries", str(log_data.get("entry_count", 0)), "📝")
    with col_c:
        render_stat_card("Total calories", str(calorie_status), "🔥")
    with col_d:
        render_stat_card("Daily goal", f"{goal_value} kcal", "🎯")

    if calorie_status > goal_value:
        st.error("You have exceeded today's calorie goal. Try lighter meals or reset the day.")
    elif calorie_status > 0 and calorie_status <= goal_value:
        st.success("You are within today's calorie goal. Keep it up!")
    elif calorie_status == 0:
        st.info("Start logging food to track your daily intake.")

    st.markdown("<div class='theme-divider'></div>", unsafe_allow_html=True)

    st.subheader("BMI Calculator")
    bmi_col1, bmi_col2, bmi_col3 = st.columns([1, 1, 1], gap="large")
    with bmi_col1:
        calc_height = st.number_input("Height (cm)", min_value=1.0, step=0.5, value=175.0, key="bmi_height")
    with bmi_col2:
        calc_weight = st.number_input("Weight (kg)", min_value=1.0, step=0.5, value=70.0, key="bmi_weight")
    with bmi_col3:
        st.write("")
        st.write("")
        if st.button("Calculate BMI"):
            try:
                height_m = calc_height / 100
                bmi_result = calc_weight / (height_m * height_m)
                bmi_cat = bmi_category(bmi_result)
                st.metric("Your BMI", f"{bmi_result:.1f}", bmi_cat)
            except ZeroDivisionError:
                st.error("Height must be greater than 0")

    st.markdown("<div class='theme-divider'></div>", unsafe_allow_html=True)

    st.subheader("Set Calorie Goals")
    goal_col1, goal_col2, goal_col3 = st.columns([1, 1, 1], gap="large")
    with goal_col1:
        current_target = int(user.get("daily_calorie_target", goal_value))
        new_target = st.number_input("Daily calorie target (kcal)", min_value=800, max_value=10000, step=50, value=current_target, key="goal_target")
    with goal_col2:
        st.write("")
        st.write("")
        if st.button("Save calorie goal"):
            try:
                api_call("PUT", "/api/user", api_base_url, {
                    "name": user.get("name", ""),
                    "age": int(user.get("age", 20)),
                    "weight": float(user.get("weight", 70)),
                    "height": float(user.get("height", 175)),
                    "goal": user.get("goal", "Maintain"),
                    "daily_calorie_target": int(new_target),
                })
                st.success(f"Daily calorie goal set to {new_target} kcal")
                st.rerun()
            except requests.RequestException as err:
                st.error(f"Could not save goal: {err}")
    with goal_col3:
        st.metric("Current Goal", f"{current_target} kcal")

    st.markdown("<div class='theme-divider'></div>", unsafe_allow_html=True)

    st.subheader("Weekly Calorie History")
    history = user.get("weekly_history", [])
    if history and len(history) > 0:
        hist_col1, hist_col2 = st.columns([0.6, 0.4], gap="large")
        with hist_col1:
            st.bar_chart(history)
        with hist_col2:
            history_rows = [{"Day": f"Day {i + 1}", "Calories": value} for i, value in enumerate(history)]
            st.table(history_rows)
    else:
        st.info("No weekly history yet. Log food and reset the day to build history.")

    st.markdown("<div class='theme-divider'></div>", unsafe_allow_html=True)

    left, right = st.columns([0.6, 0.4], gap="large")

    with left:
        st.subheader("Food Database")
        with st.form("food_form"):
            food_name = st.text_input("Food name", placeholder="e.g. Char Siu Rice")
            food_calories = st.number_input("Calories", min_value=1, step=10, value=300)
            food_category = st.selectbox("Category", options=["Food", "Drink", "Snack", "Dessert", "General"], index=0)
            submitted = st.form_submit_button("Add Food")

            if submitted:
                try:
                    api_call(
                        "POST",
                        "/api/foods",
                        api_base_url,
                        {"name": food_name, "calories": int(food_calories), "category": food_category},
                    )
                    st.success("Food added to database")
                    st.rerun()
                except requests.RequestException as err:
                    st.error(f"Could not add food: {err}")

        if foods:
            st.dataframe(foods, use_container_width=True, hide_index=True)

    with right:
        st.subheader("Log Food")
        with st.form("log_form"):
            selected_food = st.selectbox("Select food", [f["name"] for f in foods], key="log_food_select")
            quantity = st.number_input("Quantity", min_value=1, step=1, value=1, key="log_quantity")
            log_button = st.form_submit_button("Log Food")

            if log_button and foods:
                food_data = next((f for f in foods if f["name"] == selected_food), None)
                if food_data:
                    try:
                        api_call(
                            "POST",
                            "/api/log",
                            api_base_url,
                            {"food_name": selected_food, "quantity": int(quantity)},
                        )
                        st.success(f"Logged {quantity}x {selected_food}")
                        st.rerun()
                    except requests.RequestException as err:
                        st.error(f"Could not log food: {err}")

        if log_data.get("entries"):
            st.subheader("Today's Entries")
            for entry in log_data["entries"]:
                col1, col2, col3 = st.columns([2, 1, 1])
                with col1:
                    st.write(entry["food_name"])
                with col2:
                    st.write(f"{entry['quantity']}x")
                with col3:
                    st.write(f"{entry['total_calories']} kcal")

        if st.button("Reset Day"):
            try:
                api_call("POST", "/api/reset", api_base_url)
                st.success("Day reset successfully")
                st.rerun()
            except requests.RequestException as err:
                st.error(f"Could not reset day: {err}")


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
