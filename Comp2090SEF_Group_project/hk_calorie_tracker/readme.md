# HK Calorie Tracker

HK Calorie Tracker is a modular Python project for recording daily calorie intake based on common Hong Kong food items.

This repository now supports:
- a CLI application (original flow),
- a Flask backend API,
- and a Streamlit frontend that sends requests to the Flask backend.

## Architecture

Core logic (existing modules):
- `food.py`: `Food` entity (name, calories)
- `database.py`: `FoodDatabase` for storing and searching foods
- `tracker.py`: `DailyLog` for consumed food entries and total calorie calculation
- `user.py`: `User` profile and daily calorie count
- `main.py`: CLI entrypoint and menu-driven flow

Web integration (added):
- `api_server.py`: Flask API wrapper around existing logic
- `streamlit_app.py`: Streamlit UI consuming Flask endpoints via HTTP

## Flask API Endpoints

- `GET /health` - service health check
- `GET /api/foods` - list foods in database
- `POST /api/foods` - add a food (`name`, `calories`)
- `POST /api/log` - add food to daily log (`food_name`)
- `GET /api/log` - get daily log entries and totals
- `DELETE /api/log` - reset current day log and calories
- `GET /api/user` - fetch current user profile
- `PUT /api/user` - update user profile fields

## Setup

1. Create and activate a Python virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

## Run

Open two terminals in this folder.

Terminal 1 (Flask backend):

```bash
./run_backend.sh
```

Terminal 2 (Streamlit frontend):

```bash
./run_frontend.sh
```

Or run manually:

```bash
python3 api_server.py
streamlit run streamlit_app.py
```

## Notes

- Data is stored in memory, so restarting Flask resets foods/logs to initial state.
- The frontend default backend URL is `http://127.0.0.1:5050` and can be changed from the sidebar.
- Backend port can be overridden with `HK_TRACKER_API_PORT`.

## Team

- Mohamed Mohideen Dawood (13776731)
- Wu Chun Yin (13879841)
- Pun Anjuli (13880208)
