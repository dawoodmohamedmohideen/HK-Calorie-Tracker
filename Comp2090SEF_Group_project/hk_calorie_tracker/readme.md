# HK Calorie Tracker

HK Calorie Tracker is a Hong Kong-inspired calorie tracking app built with Python, Flask, and Streamlit. It combines a reusable object-oriented tracker core with a REST API and a polished Streamlit dashboard for food logging, exercise tracking, hydration monitoring, insights, and a local AI-style health coach.

## Key Features

- Multi-profile calorie tracking with profile switching
- Hong Kong food database plus custom food creation
- Meal logging with category tags and per-entry deletion
- Exercise logging with calories burned and duration
- Water intake tracking with adjustable daily goal
- Goal planning and BMI calculation tools
- Weekly calorie history and insight summaries
- Local AI health coach for meal ideas, recovery tips, and nutrition guidance
- Daily summary export as text
- Weekly history export as CSV
- Local SQLite persistence via `tracker_state.db`
- Automatic migration from legacy `tracker_state.json`
- Clean object-oriented design with ADT-backed collections

## Project Structure

Core modules:
- `food.py`: `HKFood` model and food entity logic
- `database.py`: `FoodDatabase` for food lookup and persistence
- `tracker.py`: `DailyLog` and calorie total calculations
- `user.py`: profile state, targets, and BMI calculations
- `collection_adt.py`: generic `ItemCollectionADT` used by tracker and database layers
- `main.py`: legacy CLI demo mode

Web app modules:
- `api_server.py`: Flask API service for tracker operations
- `streamlit_app.py`: Streamlit frontend UI that talks to the API
- `run_backend.py`: launcher for the backend service
- `run_frontend.py`: launcher for the Streamlit frontend

## Flask API Endpoints

- `GET /health`: service health check
- `GET /api/foods`: list all foods
- `POST /api/foods`: add a custom food
- `GET /api/log`: retrieve the current food log and totals
- `POST /api/log`: add a food entry to the log
- `DELETE /api/log`: reset the current day
- `DELETE /api/log/entry`: remove a single log entry
- `GET /api/user`: get the active profile
- `PUT /api/user`: update the active profile
- `GET /api/users`: list all user profiles
- `POST /api/users`: create a new profile
- `POST /api/users/select`: switch the active profile
- `DELETE /api/users`: delete a profile
- `POST /api/exercise`: log exercise
- `DELETE /api/exercise/entry`: delete an exercise entry
- `POST /api/water`: log water intake
- `PUT /api/water/goal`: update the daily water goal

## Requirements

- Python 3.10+ (recommended)
- `flask`
- `streamlit`
- `requests`
- `pandas`
- `altair`

Install dependencies using:

```bash
python -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
```

## Run the App

From the `hk_calorie_tracker` folder, start the backend and frontend in separate terminals:

```bash
python run_backend.py
python run_frontend.py
```

Alternative frontend launch:

```bash
python -m streamlit run streamlit_app.py
```

Default backend URL:
- `http://127.0.0.1:5050`

Override the backend port with:

```bash
set HK_TRACKER_API_PORT=5050
python run_backend.py
```

If the frontend runs in a different terminal, use the sidebar API URL field to point to the backend.

## Usage

- Create or select a user profile.
- Add custom foods and log meals from the dashboard.
- Track exercise and water intake each day.
- Review weekly trends, streaks, and calories history.
- Export a daily summary or weekly history CSV.
- Use the built-in AI-style guidance for nutrition and recovery suggestions.

## Persistence & Notes

- State is persisted locally in `tracker_state.db`.
- Legacy `tracker_state.json` state is migrated automatically on first startup.
- Profile, food log, water intake, exercise, and weekly data survive backend restarts.
- The frontend is built on Streamlit and communicates with the Flask API; it does not access tracker internals directly.

## Optional CLI Mode

A legacy CLI demo is available via:

```bash
python main.py
```

## Team

- Mohamed Mohideen Dawood (13776731)
- Wu Chun Yin (13879941)
- Pun Anjuli (13880208)
