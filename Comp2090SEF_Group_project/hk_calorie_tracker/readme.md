# HK Calorie Tracker

HK Calorie Tracker is a Hong Kong-focused calorie tracking app built with Python, Flask, and Streamlit. It keeps the original object-oriented project structure, adds a web API, and provides a richer dashboard for food logging, exercise tracking, hydration, insights, and a local AI health coach.

## What It Includes

- Multi-profile calorie tracking
- Hong Kong food database with custom food creation
- Food diary with meal labels and per-entry delete actions
- Exercise logging with calorie burn tracking
- Water intake tracking with configurable daily goal
- Goal and BMI tools
- Weekly insights and recommendations
- Local AI health coach for calories, protein, recovery, meal ideas, and summaries
- Daily summary export as a text file
- Weekly history export as CSV
- Automatic local SQLite persistence across backend restarts
- Object-oriented design with encapsulation, inheritance, and polymorphism across the core tracker models
- ADT-backed food and log collections through `ItemCollectionADT` for safer reusable item storage
- Refactored backend request handling and frontend API actions to reduce duplication and improve maintainability
- Python launch scripts that correctly forward extra command-line arguments such as custom ports

## Project Structure

Core modules:
- `food.py`: food entity model with inheritance and polymorphism through `HKFood(Food)`
- `database.py`: food database and lookup logic using the ADT-backed `food_list`
- `tracker.py`: daily food logging and calorie totals using the ADT-backed `log`
- `user.py`: user profile, targets, and tracking state with encapsulated calorie tracking fields
- `main.py`: original CLI entry point
- `collection_adt.py`: reusable `ItemCollectionADT` used by the tracker and database layers

Web app modules:
- `api_server.py`: Flask API for the tracker with shared request and response helpers to reduce repeated endpoint logic
- `streamlit_app.py`: Streamlit dashboard UI with shared API action handling for success, error, and rerun flow
- `run_backend.py`: Python launcher for the backend service
- `run_frontend.py`: Python launcher for the Streamlit frontend

## Flask API Endpoints

- `GET /health`: service health check
- `GET /api/foods`: list all foods
- `POST /api/foods`: add a custom food
- `GET /api/log`: get current food log and totals
- `POST /api/log`: log a food entry
- `DELETE /api/log`: reset the current day
- `DELETE /api/log/entry`: remove one logged food entry
- `GET /api/user`: get active user profile
- `PUT /api/user`: update active user profile
- `GET /api/users`: list all profiles
- `POST /api/users`: create a profile
- `POST /api/users/select`: switch active profile
- `DELETE /api/users`: delete a profile
- `POST /api/exercise`: log exercise
- `DELETE /api/exercise/entry`: delete exercise entry
- `POST /api/water`: log water intake
- `PUT /api/water/goal`: update water goal

## Setup

1. Open a terminal in this folder.
2. Create a virtual environment.
3. Install dependencies with Python.

```bash
python -m venv .venv
python -m pip install -r requirements.txt
```

## Run The App

Start the backend and frontend in separate terminals from this folder.

```bash
python run_backend.py
python run_frontend.py
```

Default URLs:
- Backend: `http://127.0.0.1:5050`
- Frontend: Streamlit will show the port in the terminal when it starts

## Using The App

- Sign in or create a profile from the login screen
- Use the sidebar to switch, create, edit, or delete profiles
- Add custom foods from the sidebar `Add Food` section
- Log meals, exercise, and water from the dashboard tabs
- Use the quick-log food search to find foods faster before adding them
- Review weekly trends and recommendations in `Insights`
- Use `AI Chat` for local health and fitness guidance
- Use `Download Daily Summary` to export the current day as a text file
- Use `Download Weekly History CSV` in `Insights` to export recent calorie history

## Notes

- App state is saved locally in `tracker_state.db`, so profiles, logs, water, exercise, and custom foods survive backend restarts
- If an older `tracker_state.json` exists, the backend can migrate that legacy state into SQLite automatically
- The frontend connects to `http://127.0.0.1:5050` by default, but the API URL can be changed from the sidebar
- The backend port can be overridden with `HK_TRACKER_API_PORT`
- The AI coach currently runs in local mode and does not require a third-party API key
- During debugging, the main flows were rechecked after the refactor and ADT changes, including profile creation, food logging, water tracking, exercise logging, and cleanup
- The project launch flow is now Python-only through `run_backend.py` and `run_frontend.py`

## Team

- Mohamed Mohideen Dawood (13776731)
- Wu Chun Yin (13879841)
- Pun Anjuli (13880208)
