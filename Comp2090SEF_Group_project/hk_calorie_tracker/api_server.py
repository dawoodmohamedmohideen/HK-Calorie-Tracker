"""Flask API server for the HK Calorie Tracker.

This module wraps the existing OOP classes (User, FoodDatabase, DailyLog)
behind JSON endpoints so a web UI can consume the same core logic.
"""

from __future__ import annotations

import os
from threading import Lock
from typing import Dict, List

from flask import Flask, jsonify, request

from database import FoodDatabase
from tracker import DailyLog
from user import User


class CalorieTrackerService:
    """Encapsulates shared tracker state and operations.

    A lock is used to avoid race conditions when running Flask with threading.
    """

    def __init__(self) -> None:
        self._lock = Lock()
        self.user = User("Dawood", 20, 70, 175, "Maintain")
        self.db = FoodDatabase()
        self.log = DailyLog()
        self._seed_foods()

    def _seed_foods(self) -> None:
        self.db.add_food("Char Siu Rice", 600)
        self.db.add_food("Milk Tea", 250)
        self.db.add_food("Dim Sum", 400)

    def list_foods(self) -> List[Dict[str, int | str]]:
        return [
            {"name": food.name, "calories": food.calories}
            for food in self.db.food_list
        ]

    def add_food(self, name: str, calories: int) -> None:
        with self._lock:
            self.db.add_food(name, calories)

    def log_food(self, food_name: str) -> Dict[str, int | str]:
        with self._lock:
            food = self.db.get_food(food_name)
            if not food:
                raise ValueError("Food not found in database")

            self.log.add_entry(food)
            self.user.add_calories(food.calories)
            return {"name": food.name, "calories": food.calories}

    def get_log(self) -> Dict[str, object]:
        entries = [
            {"name": food.name, "calories": food.calories}
            for food in self.log.log
        ]
        return {
            "entries": entries,
            "total_calories": self.log.total_calories(),
            "entry_count": len(entries),
        }

    def reset_day(self) -> None:
        with self._lock:
            self.log.log.clear()
            self.user.reset_daily_calories()

    def get_user(self) -> Dict[str, int | str]:
        return {
            "name": self.user.name,
            "age": self.user.age,
            "weight": self.user.weight,
            "height": self.user.height,
            "goal": self.user.goal,
            "daily_calories": self.user.get_daily_calories(),
        }

    def update_user(self, payload: Dict[str, object]) -> Dict[str, int | str]:
        with self._lock:
            self.user.name = str(payload.get("name", self.user.name)).strip() or self.user.name
            self.user.age = int(payload.get("age", self.user.age))
            self.user.weight = float(payload.get("weight", self.user.weight))
            self.user.height = float(payload.get("height", self.user.height))
            self.user.goal = str(payload.get("goal", self.user.goal)).strip() or self.user.goal
            return self.get_user()


app = Flask(__name__)
service = CalorieTrackerService()


@app.get("/health")
def health() -> tuple:
    return jsonify({"status": "ok"}), 200


@app.get("/api/foods")
def get_foods() -> tuple:
    return jsonify({"foods": service.list_foods()}), 200


@app.post("/api/foods")
def create_food() -> tuple:
    payload = request.get_json(silent=True) or {}
    name = str(payload.get("name", "")).strip()
    calories = payload.get("calories")

    if not name:
        return jsonify({"error": "Field 'name' is required"}), 400

    try:
        calories_int = int(calories)
        if calories_int <= 0:
            raise ValueError
    except (TypeError, ValueError):
        return jsonify({"error": "Field 'calories' must be a positive integer"}), 400

    service.add_food(name, calories_int)
    return jsonify({"message": "Food added", "food": {"name": name, "calories": calories_int}}), 201


@app.post("/api/log")
def add_log_entry() -> tuple:
    payload = request.get_json(silent=True) or {}
    food_name = str(payload.get("food_name", "")).strip()

    if not food_name:
        return jsonify({"error": "Field 'food_name' is required"}), 400

    try:
        entry = service.log_food(food_name)
    except ValueError as err:
        return jsonify({"error": str(err)}), 404

    return jsonify({"message": "Food logged", "entry": entry, "daily_calories": service.user.get_daily_calories()}), 201


@app.get("/api/log")
def get_log() -> tuple:
    return jsonify(service.get_log()), 200


@app.delete("/api/log")
def reset_log() -> tuple:
    service.reset_day()
    return jsonify({"message": "Daily log reset"}), 200


@app.get("/api/user")
def get_user() -> tuple:
    return jsonify({"user": service.get_user()}), 200


@app.put("/api/user")
def update_user() -> tuple:
    payload = request.get_json(silent=True) or {}

    try:
        user = service.update_user(payload)
    except (TypeError, ValueError):
        return jsonify({"error": "Invalid user payload"}), 400

    return jsonify({"message": "User updated", "user": user}), 200


if __name__ == "__main__":
    port = int(os.environ.get("HK_TRACKER_API_PORT", "5050"))
    app.run(host="0.0.0.0", port=port, debug=True)
