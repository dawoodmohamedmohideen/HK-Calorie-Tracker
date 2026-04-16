from __future__ import annotations

import json
import os
from pathlib import Path
import sqlite3
from threading import Lock
from typing import Any, Dict, List

from flask import Flask, jsonify, request

from database import FoodDatabase
from food import HKFood
from tracker import DailyLog
from user import User


class CalorieTrackerService:
    """Application service that coordinates the app's OOP models.

    It composes ``User``, ``FoodDatabase``, ``DailyLog``, and ``HKFood``
    objects and exposes higher-level operations for the Flask API layer.
    """

    def __init__(self) -> None:
        self._lock = Lock()
        self._state_file = Path(__file__).with_name("tracker_state.db")
        self._legacy_state_file = Path(__file__).with_name("tracker_state.json")
        self.users: List[User] = []
        self.current_user_index = 0
        self.db = FoodDatabase()
        self.logs: List[DailyLog] = []
        self.weekly_history: List[List[int]] = []
        self.water_intake: List[int] = []
        self.water_goal: List[int] = []
        self.meal_labels: List[List[str]] = []
        self.streaks: List[int] = []
        self.exercises: List[List[Dict]] = []

        self._initialize_db()
        if not self._load_state():
            if self._load_legacy_state():
                self._save_state()
            else:
                self._load_default_state()
                self._save_state()

    def _initialize_db(self) -> None:
        with sqlite3.connect(self._state_file) as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS app_meta (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS users (
                    user_index INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    age INTEGER NOT NULL,
                    weight REAL NOT NULL,
                    height REAL NOT NULL,
                    goal TEXT NOT NULL,
                    daily_calorie_target INTEGER NOT NULL,
                    daily_calories INTEGER NOT NULL
                );
                CREATE TABLE IF NOT EXISTS foods (
                    position INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    calories INTEGER NOT NULL,
                    category TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS logs (
                    user_index INTEGER NOT NULL,
                    position INTEGER NOT NULL,
                    food_name TEXT NOT NULL,
                    calories INTEGER NOT NULL,
                    category TEXT NOT NULL,
                    PRIMARY KEY (user_index, position)
                );
                CREATE TABLE IF NOT EXISTS weekly_history (
                    user_index INTEGER NOT NULL,
                    position INTEGER NOT NULL,
                    calories INTEGER NOT NULL,
                    PRIMARY KEY (user_index, position)
                );
                CREATE TABLE IF NOT EXISTS water (
                    user_index INTEGER PRIMARY KEY,
                    intake INTEGER NOT NULL,
                    goal INTEGER NOT NULL
                );
                CREATE TABLE IF NOT EXISTS meal_labels (
                    user_index INTEGER NOT NULL,
                    position INTEGER NOT NULL,
                    meal TEXT NOT NULL,
                    PRIMARY KEY (user_index, position)
                );
                CREATE TABLE IF NOT EXISTS streaks (
                    user_index INTEGER PRIMARY KEY,
                    streak INTEGER NOT NULL
                );
                CREATE TABLE IF NOT EXISTS exercises (
                    user_index INTEGER NOT NULL,
                    position INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    calories_burned INTEGER NOT NULL,
                    duration_min INTEGER NOT NULL,
                    PRIMARY KEY (user_index, position)
                );
                """
            )

    def _load_default_state(self) -> None:
        self.users = [User("Dawood", 20, 70, 175, "Maintain", daily_calorie_target=2000)]
        self.current_user_index = 0
        self.db = FoodDatabase()
        self.logs = [DailyLog()]
        self.weekly_history = [[0]]
        self.water_intake = [0]
        self.water_goal = [8]
        self.meal_labels = [[]]
        self.streaks = [0]
        self.exercises = [[]]
        self._seed_foods()

    def _save_state(self) -> None:
        with sqlite3.connect(self._state_file) as conn:
            conn.executescript(
                """
                DELETE FROM app_meta;
                DELETE FROM users;
                DELETE FROM foods;
                DELETE FROM logs;
                DELETE FROM weekly_history;
                DELETE FROM water;
                DELETE FROM meal_labels;
                DELETE FROM streaks;
                DELETE FROM exercises;
                """
            )
            conn.execute(
                "INSERT INTO app_meta (key, value) VALUES (?, ?)",
                ("current_user_index", str(self.current_user_index)),
            )

            for user_index, user in enumerate(self.users):
                conn.execute(
                    """
                    INSERT INTO users (user_index, name, age, weight, height, goal, daily_calorie_target, daily_calories)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        user_index,
                        user.name,
                        int(user.age),
                        float(user.weight),
                        float(user.height),
                        user.goal,
                        int(user.get_daily_calorie_target()),
                        int(user.get_daily_calories()),
                    ),
                )

            for position, food in enumerate(self.db.food_list):
                conn.execute(
                    "INSERT INTO foods (position, name, calories, category) VALUES (?, ?, ?, ?)",
                    (position, food.name, int(food.calories), str(getattr(food, "category", "General"))),
                )

            for user_index, daily_log in enumerate(self.logs):
                for position, food in enumerate(daily_log.log):
                    conn.execute(
                        "INSERT INTO logs (user_index, position, food_name, calories, category) VALUES (?, ?, ?, ?, ?)",
                        (user_index, position, food.name, int(food.calories), str(getattr(food, "category", "General"))),
                    )

            for user_index, history in enumerate(self.weekly_history):
                for position, calories in enumerate(history):
                    conn.execute(
                        "INSERT INTO weekly_history (user_index, position, calories) VALUES (?, ?, ?)",
                        (user_index, position, int(calories)),
                    )

            for user_index, intake in enumerate(self.water_intake):
                conn.execute(
                    "INSERT INTO water (user_index, intake, goal) VALUES (?, ?, ?)",
                    (user_index, int(intake), int(self.water_goal[user_index])),
                )

            for user_index, labels in enumerate(self.meal_labels):
                for position, meal in enumerate(labels):
                    conn.execute(
                        "INSERT INTO meal_labels (user_index, position, meal) VALUES (?, ?, ?)",
                        (user_index, position, str(meal)),
                    )

            for user_index, streak in enumerate(self.streaks):
                conn.execute(
                    "INSERT INTO streaks (user_index, streak) VALUES (?, ?)",
                    (user_index, int(streak)),
                )

            for user_index, exercise_list in enumerate(self.exercises):
                for position, exercise in enumerate(exercise_list):
                    conn.execute(
                        """
                        INSERT INTO exercises (user_index, position, name, calories_burned, duration_min)
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        (
                            user_index,
                            position,
                            str(exercise.get("name", "Exercise")),
                            int(exercise.get("calories_burned", 0)),
                            int(exercise.get("duration_min", 0)),
                        ),
                    )

    def _load_state(self) -> bool:
        if not self._state_file.exists() or self._state_file.stat().st_size == 0:
            return False

        try:
            with sqlite3.connect(self._state_file) as conn:
                conn.row_factory = sqlite3.Row
                user_rows = conn.execute("SELECT * FROM users ORDER BY user_index").fetchall()
                if not user_rows:
                    return False

                self.db = FoodDatabase()
                food_rows = conn.execute("SELECT name, calories, category FROM foods ORDER BY position").fetchall()
                for food_row in food_rows:
                    self.db.add_food(food_row["name"], int(food_row["calories"]), food_row["category"])

                self.users = []
                for row in user_rows:
                    user = User(
                        row["name"],
                        int(row["age"]),
                        float(row["weight"]),
                        float(row["height"]),
                        row["goal"],
                        int(row["daily_calorie_target"]),
                    )
                    user.add_calories(int(row["daily_calories"]))
                    self.users.append(user)

                user_count = len(self.users)
                self.logs = [DailyLog() for _ in range(user_count)]
                for row in conn.execute("SELECT * FROM logs ORDER BY user_index, position"):
                    self.logs[int(row["user_index"])].add_entry(
                        HKFood(row["food_name"], int(row["calories"]), row["category"])
                    )

                self.weekly_history = [[] for _ in range(user_count)]
                for row in conn.execute("SELECT * FROM weekly_history ORDER BY user_index, position"):
                    self.weekly_history[int(row["user_index"])].append(int(row["calories"]))

                self.water_intake = [0 for _ in range(user_count)]
                self.water_goal = [8 for _ in range(user_count)]
                for row in conn.execute("SELECT * FROM water ORDER BY user_index"):
                    index = int(row["user_index"])
                    self.water_intake[index] = int(row["intake"])
                    self.water_goal[index] = int(row["goal"])

                self.meal_labels = [[] for _ in range(user_count)]
                for row in conn.execute("SELECT * FROM meal_labels ORDER BY user_index, position"):
                    self.meal_labels[int(row["user_index"])].append(row["meal"])

                self.streaks = [0 for _ in range(user_count)]
                for row in conn.execute("SELECT * FROM streaks ORDER BY user_index"):
                    self.streaks[int(row["user_index"])] = int(row["streak"])

                self.exercises = [[] for _ in range(user_count)]
                for row in conn.execute("SELECT * FROM exercises ORDER BY user_index, position"):
                    self.exercises[int(row["user_index"])].append(
                        {
                            "name": row["name"],
                            "calories_burned": int(row["calories_burned"]),
                            "duration_min": int(row["duration_min"]),
                        }
                    )

                for history in self.weekly_history:
                    if not history:
                        history.append(0)

                meta_row = conn.execute(
                    "SELECT value FROM app_meta WHERE key = ?",
                    ("current_user_index",),
                ).fetchone()
                loaded_index = int(meta_row["value"]) if meta_row else 0
                self.current_user_index = min(max(0, loaded_index), user_count - 1)
            return True
        except (OSError, ValueError, TypeError, sqlite3.Error):
            return False

    def _load_legacy_state(self) -> bool:
        if not self._legacy_state_file.exists():
            return False

        try:
            payload = json.loads(self._legacy_state_file.read_text(encoding="utf-8"))
            users_payload = payload.get("users", [])
            if not users_payload:
                return False

            self.db = FoodDatabase()
            for food_payload in payload.get("foods", []):
                self.db.add_food(
                    str(food_payload.get("name", "")).strip(),
                    int(food_payload.get("calories", 0)),
                    str(food_payload.get("category", "General")).strip() or "General",
                )

            self.users = []
            for user_payload in users_payload:
                user = User(
                    str(user_payload.get("name", "User")).strip() or "User",
                    int(user_payload.get("age", 20)),
                    float(user_payload.get("weight", 70)),
                    float(user_payload.get("height", 175)),
                    str(user_payload.get("goal", "Maintain")).strip() or "Maintain",
                    int(user_payload.get("daily_calorie_target", 2000)),
                )
                user.add_calories(int(user_payload.get("daily_calories", 0)))
                self.users.append(user)

            self.logs = []
            for log_payload in payload.get("logs", []):
                daily_log = DailyLog()
                for food_payload in log_payload:
                    daily_log.add_entry(
                        HKFood(
                            str(food_payload.get("name", "Unknown")),
                            int(food_payload.get("calories", 0)),
                            str(food_payload.get("category", "General")),
                        )
                    )
                self.logs.append(daily_log)

            user_count = len(self.users)
            self.weekly_history = [list(map(int, history)) for history in payload.get("weekly_history", [])[:user_count]]
            self.water_intake = [int(value) for value in payload.get("water_intake", [])[:user_count]]
            self.water_goal = [int(value) for value in payload.get("water_goal", [])[:user_count]]
            self.meal_labels = [list(map(str, labels)) for labels in payload.get("meal_labels", [])[:user_count]]
            self.streaks = [int(value) for value in payload.get("streaks", [])[:user_count]]
            self.exercises = [
                [
                    {
                        "name": str(exercise.get("name", "Exercise")),
                        "calories_burned": int(exercise.get("calories_burned", 0)),
                        "duration_min": int(exercise.get("duration_min", 0)),
                    }
                    for exercise in exercise_list
                ]
                for exercise_list in payload.get("exercises", [])[:user_count]
            ]

            while len(self.logs) < user_count:
                self.logs.append(DailyLog())
            while len(self.weekly_history) < user_count:
                self.weekly_history.append([0])
            while len(self.water_intake) < user_count:
                self.water_intake.append(0)
            while len(self.water_goal) < user_count:
                self.water_goal.append(8)
            while len(self.meal_labels) < user_count:
                self.meal_labels.append([])
            while len(self.streaks) < user_count:
                self.streaks.append(0)
            while len(self.exercises) < user_count:
                self.exercises.append([])

            loaded_index = int(payload.get("current_user_index", 0))
            self.current_user_index = min(max(0, loaded_index), user_count - 1)
            return True
        except (OSError, ValueError, TypeError, json.JSONDecodeError, KeyError):
            return False

    def current_user(self) -> User:
        return self.users[self.current_user_index]

    def current_log(self) -> DailyLog:
        return self.logs[self.current_user_index]

    def _user_payload(self, user: User, index: int | None = None) -> Dict[str, Any]:
        if index is None:
            index = self.current_user_index
        return {
            "name": user.name,
            "age": user.age,
            "weight": user.weight,
            "height": user.height,
            "goal": user.goal,
            "daily_calories": user.get_daily_calories(),
            "daily_calorie_target": user.get_daily_calorie_target(),
            "weekly_history": self.weekly_history[index] if 0 <= index < len(self.weekly_history) else [],
            "water_intake": self.water_intake[index] if 0 <= index < len(self.water_intake) else 0,
            "water_goal": self.water_goal[index] if 0 <= index < len(self.water_goal) else 8,
            "streak": self.streaks[index] if 0 <= index < len(self.streaks) else 0,
            "exercises": self.exercises[index] if 0 <= index < len(self.exercises) else [],
            "exercise_burned": sum(e.get("calories_burned", 0) for e in (self.exercises[index] if 0 <= index < len(self.exercises) else [])),
        }

    def _food_payload(self, food: Any) -> Dict[str, Any]:
        return {
            "name": food.name,
            "calories": food.calories,
            "category": getattr(food, "category", "General"),
        }

    def user_exists(self, name: str) -> bool:
        return any(user.name.lower() == name.lower() for user in self.users)

    def _seed_foods(self) -> None:
        self.db.add_food("Rice Noodle Roll (Cheung Fun) / 腸粉", 220, "Food")
        self.db.add_food("Curry Fish Balls (6 pieces) / 咖哩魚蛋", 117, "Snack")
        self.db.add_food("Egg Waffle (Gai Daan Jai) / 雞蛋仔", 420, "Snack")
        self.db.add_food("Fish Siu Mai (6 pieces) / 魚肉燒賣", 312, "Snack")
        self.db.add_food("Hong Kong Style Milk Tea / 絲襪奶茶", 150, "Drink")
        self.db.add_food("Pineapple Bun (Bo Lo Bao) / 菠蘿包", 340, "Food")
        self.db.add_food("Egg Tart (Dan Tat) / 蛋撻", 220, "Dessert")
        self.db.add_food("Shrimp Dumpling (Har Gow - 1 piece) / 蝦餃", 50, "Food")
        self.db.add_food("Pork Dumpling (Siu Mai - 1 piece) / 燒賣 (點心)", 62, "Food")
        self.db.add_food("BBQ Pork Bun (Char Siu Bao) / 叉燒包", 155, "Food")
        self.db.add_food("Roast Goose (per serving) / 燒鵝", 450, "Food")
        self.db.add_food("BBQ Pork (Char Siu) / 叉燒", 380, "Food")
        self.db.add_food("Wonton Noodle Soup / 雲吞麵", 550, "Food")
        self.db.add_food("Beef Brisket Noodle Soup / 牛腩麵", 650, "Food")
        self.db.add_food("Fried Two (Rice Roll with Dough Stick) / 炸兩", 450, "Food")
        self.db.add_food("Steamed Spare Ribs (in Black Bean Sauce) / 豉汁蒸排骨", 260, "Food")
        self.db.add_food("Steamed Beef Tripe / 柱侯金錢肚", 223, "Food")
        self.db.add_food("Steamed Chicken Feet / 豉汁蒸鳳爪", 200, "Food")
        self.db.add_food("Curry Squid / 咖喱蒸土魷", 192, "Food")
        self.db.add_food("Fried Spring Roll (1 piece) / 炸春卷", 150, "Snack")
        self.db.add_food("Claypot Rice / 煲仔飯", 900, "Food")
        self.db.add_food("Fried Rice with Salted Fish / 鹹魚雞粒炒飯", 800, "Food")
        self.db.add_food("Baked Pork Chop Rice / 焗豬扒飯", 900, "Food")
        self.db.add_food("Macaroni in Soup with Ham / 火腿通粉", 350, "Food")
        self.db.add_food("French Toast (Hong Kong Style) / 西多士", 450, "Food")
        self.db.add_food("Satay Beef Instant Noodles / 沙爹牛肉麵", 580, "Food")
        self.db.add_food("Lemon Tea (Iced) / 凍檸茶", 120, "Drink")
        self.db.add_food("Yin Yang Coffee & Tea / 鴛鴦", 160, "Drink")
        self.db.add_food("Sago Cream with Mango / 楊枝甘露", 300, "Dessert")
        self.db.add_food("Tofu Fa (Sweet Tofu Pudding) / 豆腐花", 150, "Dessert")
        self.db.add_food("Mango Pancake / 芒果班戟", 250, "Dessert")
        self.db.add_food("Durian Dessert / 榴槤甜品", 350, "Dessert")
        self.db.add_food("Stinky Tofu (2 pieces) / 臭豆腐", 225, "Snack")
        self.db.add_food("Put Chai Ko (Red Bean Pudding) / 砵仔糕", 260, "Snack")
        self.db.add_food("Three Treasures (Stuffed Veggies) / 煎釀三寶", 176, "Snack")
        self.db.add_food("Takoyaki (Octopus Balls - 8 pcs) / 章魚小丸子", 630, "Snack")
        self.db.add_food("Waffle (Gai Daan Jai Grid Cake) / 格仔餅", 504, "Snack")
        self.db.add_food("Offal (Cow内脏) / 牛雜", 300, "Snack")
        self.db.add_food("Fake Shark Fin Soup (Bowl) / 碗仔翅", 112, "Snack")
        self.db.add_food("Fish & Lettuce Soup / 生菜魚肉", 120, "Snack")
        self.db.add_food("Chive & Pig Blood Soup / 韭菜豬紅", 150, "Snack")
        self.db.add_food("Chestnuts (Fried - 100g) / 炒栗子", 210, "Snack")
        self.db.add_food("Sesame Balls (Jian Dui - 2 pieces) / 煎堆", 300, "Dessert")
        self.db.add_food("Steamed Milk Pudding / 雙皮奶", 220, "Dessert")
        self.db.add_food("Sugarcane Juice / 竹蔗水", 130, "Drink")
        self.db.add_food("Red Bean Ice / 紅豆冰", 280, "Drink")
        self.db.add_food("Salted Lemon 7-Up/Soda / 鹹檸七", 110, "Drink")
        self.db.add_food("Fried Squid Tentacles (1 serving) / 炸魷魚鬚", 400, "Snack")
        self.db.add_food("Steamed Glutinous Rice (Lo Mai Gai) / 糯米雞", 600, "Food")
        self.db.add_food("Shrimp & Pork Shumai / 鮮蝦豬肉燒賣", 60, "Food")

    def list_users(self) -> List[Dict[str, int | str]]:
        return [self._user_payload(user, index=index) for index, user in enumerate(self.users)]

    def add_user(self, name: str, age: int, weight: float, height: float, goal: str, daily_calorie_target: int = 2000) -> Dict[str, int | str]:
        with self._lock:
            if self.user_exists(name):
                raise ValueError("User already exists")
            new_user = User(name, age, weight, height, goal, daily_calorie_target)
            self.users.append(new_user)
            self.logs.append(DailyLog())
            self.weekly_history.append([0])
            self.water_intake.append(0)
            self.water_goal.append(8)
            self.meal_labels.append([])
            self.streaks.append(0)
            self.exercises.append([])
            self._save_state()
            return self._user_payload(new_user, index=len(self.users) - 1)

    def select_user(self, name: str) -> None:
        with self._lock:
            for index, user in enumerate(self.users):
                if user.name.lower() == name.lower():
                    self.current_user_index = index
                    self._save_state()
                    return
            raise ValueError("User not found")

    def delete_user(self, name: str) -> None:
        with self._lock:
            if len(self.users) <= 1:
                raise ValueError("Cannot delete the last user")
            for index, user in enumerate(self.users):
                if user.name.lower() == name.lower():
                    if index == self.current_user_index:
                        self.current_user_index = 0 if index != 0 else 1
                    del self.users[index]
                    del self.logs[index]
                    del self.weekly_history[index]
                    del self.water_intake[index]
                    del self.water_goal[index]
                    del self.meal_labels[index]
                    del self.streaks[index]
                    del self.exercises[index]
                    # Adjust current index after deletion
                    if self.current_user_index > index:
                        self.current_user_index -= 1
                    if self.current_user_index >= len(self.users):
                        self.current_user_index = len(self.users) - 1
                    self._save_state()
                    return
            raise ValueError("User not found")

    def list_foods(self) -> List[Dict[str, int | str]]:
        return [self._food_payload(food) for food in self.db.food_list]

    def add_food(self, name: str, calories: int, category: str = "General") -> None:
        with self._lock:
            self.db.add_food(name, calories, category)
            self._save_state()

    def log_food(self, food_name: str, quantity: int = 1, meal: str = "General") -> Dict[str, int | str]:
        with self._lock:
            food = self.db.get_food(food_name)
            if not food:
                raise ValueError("Food not found in database")
            for _ in range(quantity):
                self.current_log().add_entry(food)
                self.current_user().add_calories(food.calories)
                self.meal_labels[self.current_user_index].append(meal)
            self.weekly_history[self.current_user_index][-1] = self.current_log().total_calories()
            # Update streak: if first log of the day, increment streak
            if len(self.current_log().log) == quantity:
                self.streaks[self.current_user_index] += 1
            self._save_state()
            return self._food_payload(food)

    def remove_log_entry(self, food_name: str) -> bool:
        with self._lock:
            log_list = self.current_log().log
            meal_labels = self.meal_labels[self.current_user_index]
            for index, food in enumerate(log_list):
                if food.name == food_name:
                    self.current_user().add_calories(-food.calories)
                    log_list.pop(index)
                    if index < len(meal_labels):
                        meal_labels.pop(index)
                    self.weekly_history[self.current_user_index][-1] = self.current_log().total_calories()
                    self._save_state()
                    return True
            return False

    def get_log(self) -> Dict[str, object]:
        # Group entries by food name + meal for cleaner display
        from collections import Counter, defaultdict
        meal_labels = self.meal_labels[self.current_user_index]
        counts: Counter = Counter()
        cals: Dict[str, int] = {}
        meals: Dict[str, str] = {}
        for i, food in enumerate(self.current_log().log):
            meal = meal_labels[i] if i < len(meal_labels) else "General"
            counts[food.name] += 1
            cals[food.name] = food.calories
            meals[food.name] = meal
        entries = [
            {"food_name": name, "quantity": qty, "total_calories": qty * cals[name], "meal": meals[name]}
            for name, qty in counts.items()
        ]
        # Compute per-meal breakdown
        meal_totals: Dict[str, int] = defaultdict(int)
        for entry in entries:
            meal_totals[entry["meal"]] += entry["total_calories"]
        return {
            "entries": entries,
            "total_calories": self.current_log().total_calories(),
            "entry_count": len(self.current_log().log),
            "meal_totals": dict(meal_totals),
        }

    def add_water(self, glasses: int = 1) -> int:
        with self._lock:
            self.water_intake[self.current_user_index] += glasses
            self._save_state()
            return self.water_intake[self.current_user_index]

    def set_water_goal(self, goal: int) -> None:
        with self._lock:
            self.water_goal[self.current_user_index] = max(1, goal)
            self._save_state()

    def reset_day(self) -> None:
        with self._lock:
            total = self.current_log().total_calories()
            history = self.weekly_history[self.current_user_index]
            if history:
                history[-1] = total
            history.append(0)
            if len(history) > 7:
                history.pop(0)
            self.current_log().log.clear()
            self.current_user().reset_daily_calories()
            self.water_intake[self.current_user_index] = 0
            self.meal_labels[self.current_user_index] = []
            self.exercises[self.current_user_index] = []
            self._save_state()

    def get_user(self) -> Dict[str, Any]:
        return self._user_payload(self.current_user())

    def update_user(self, payload: Dict[str, object]) -> Dict[str, Any]:
        with self._lock:
            user = self.current_user()
            user.name = str(payload.get("name", user.name)).strip() or user.name
            age_val = payload.get("age", user.age)
            if age_val is not None:
                try:
                    user.age = int(str(age_val))
                except (ValueError, TypeError):
                    pass
            weight_val = payload.get("weight", user.weight)
            if weight_val is not None:
                try:
                    user.weight = float(str(weight_val))
                except (ValueError, TypeError):
                    pass
            height_val = payload.get("height", user.height)
            if height_val is not None:
                try:
                    user.height = float(str(height_val))
                except (ValueError, TypeError):
                    pass
            user.goal = str(payload.get("goal", user.goal)).strip() or user.goal
            daily_target = payload.get("daily_calorie_target", user.get_daily_calorie_target())
            if daily_target is not None:
                try:
                    user.set_daily_calorie_target(int(str(daily_target)))
                except (ValueError, TypeError):
                    pass
            self._save_state()
            return self.get_user()

    def add_exercise(self, name: str, calories_burned: int, duration: int) -> List[Dict[str, Any]]:
        with self._lock:
            self.exercises[self.current_user_index].append(
                {"name": name, "calories_burned": calories_burned, "duration_min": duration}
            )
            self._save_state()
            return self.exercises[self.current_user_index]

    def delete_exercise(self, index: int) -> Dict[str, Any] | None:
        with self._lock:
            ex_list = self.exercises[self.current_user_index]
            if 0 <= index < len(ex_list):
                removed = ex_list.pop(index)
                self._save_state()
                return removed
            return None


app = Flask(__name__)
service = CalorieTrackerService()


def request_payload() -> dict:
    return request.get_json(silent=True) or {}


def respond(payload: dict, status: int = 200) -> tuple:
    return jsonify(payload), status


def fail(message: str, status: int = 400) -> tuple:
    return respond({"error": message}, status)


def text_field(payload: dict, field: str, default: str = "") -> str:
    return str(payload.get(field, default)).strip() or default


def require_text(payload: dict, field: str) -> str:
    value = text_field(payload, field)
    if not value:
        raise ValueError(f"Field '{field}' is required")
    return value


@app.get("/health")
def health() -> tuple:
    return respond({"status": "ok"})


@app.get("/api/foods")
def get_foods() -> tuple:
    return respond({"foods": service.list_foods()})


@app.post("/api/foods")
def create_food() -> tuple:
    payload = request_payload()
    name = text_field(payload, "name")
    calories = payload.get("calories")
    category = text_field(payload, "category", "General")

    if not name:
        return fail("Field 'name' is required")

    try:
        calories_int = int(calories or 0)
        if calories_int <= 0:
            raise ValueError
    except (TypeError, ValueError):
        return fail("Field 'calories' must be a positive integer")

    service.add_food(name, calories_int, category)
    return respond({"message": "Food added", "food": {"name": name, "calories": calories_int, "category": category}}, 201)


@app.post("/api/log")
def add_log_entry() -> tuple:
    payload = request_payload()
    try:
        food_name = require_text(payload, "food_name")
    except ValueError as err:
        return fail(str(err))

    quantity = payload.get("quantity", 1)
    try:
        quantity = max(1, int(quantity))
    except (TypeError, ValueError):
        quantity = 1

    meal = str(payload.get("meal", "General")).strip() or "General"

    try:
        entry = service.log_food(food_name, quantity, meal)
    except ValueError as err:
        return fail(str(err), 404)

    return respond({"message": "Food logged", "entry": entry, "daily_calories": service.get_user()["daily_calories"]}, 201)


@app.get("/api/log")
def get_log() -> tuple:
    return respond(service.get_log())


@app.delete("/api/log")
def reset_log() -> tuple:
    service.reset_day()
    return respond({"message": "Daily log reset"})


@app.delete("/api/log/entry")
def delete_log_entry() -> tuple:
    payload = request_payload()
    try:
        food_name = require_text(payload, "food_name")
    except ValueError as err:
        return fail(str(err))
    if service.remove_log_entry(food_name):
        return respond({"message": f"Removed one '{food_name}'"})
    return fail(f"'{food_name}' not found in log", 404)


@app.delete("/api/exercise/entry")
def delete_exercise_entry() -> tuple:
    payload = request_payload()
    index = payload.get("index")
    if index is None:
        return fail("Field 'index' is required")
    try:
        index = int(index)
    except (TypeError, ValueError):
        return fail("'index' must be an integer")
    removed = service.delete_exercise(index)
    if removed is not None:
        return respond({"message": f"Removed '{removed['name']}'"})
    return fail("Index out of range", 404)


@app.get("/api/users")
def get_users() -> tuple:
    return respond({"users": service.list_users()})


@app.post("/api/users")
def create_user() -> tuple:
    payload = request_payload()
    name = text_field(payload, "name")
    age = payload.get("age")
    weight = payload.get("weight")
    height = payload.get("height")
    goal = text_field(payload, "goal", "Maintain")
    daily_target = payload.get("daily_calorie_target", 2000)

    if not name:
        return fail("Field 'name' is required")

    try:
        age_int = int(age or 0)
        weight_float = float(weight or 0)
        height_float = float(height or 0)
        daily_target_int = int(daily_target or 2000)
    except (TypeError, ValueError):
        return fail("Age, weight, height, and daily_calorie_target must be numbers")

    try:
        created_user = service.add_user(name, age_int, weight_float, height_float, goal, daily_target_int)
    except ValueError as err:
        return fail(str(err), 409)

    return respond({"message": "User created", "user": created_user}, 201)


@app.post("/api/users/select")
def select_user() -> tuple:
    payload = request_payload()
    try:
        name = require_text(payload, "name")
    except ValueError as err:
        return fail(str(err))

    try:
        service.select_user(name)
    except ValueError as err:
        return fail(str(err), 404)

    return respond({"message": "User selected", "user": service.get_user()})


@app.delete("/api/users")
def delete_user_endpoint() -> tuple:
    payload = request_payload()
    try:
        name = require_text(payload, "name")
    except ValueError as err:
        return fail(str(err))

    try:
        service.delete_user(name)
    except ValueError as err:
        status = 400 if "last user" in str(err) else 404
        return fail(str(err), status)

    return respond({"message": "User deleted"})


@app.get("/api/user")
def get_user() -> tuple:
    return respond({"user": service.get_user()})


@app.put("/api/user")
def update_user() -> tuple:
    payload = request_payload()

    try:
        user = service.update_user(payload)
    except (TypeError, ValueError):
        return fail("Invalid user payload")

    return respond({"message": "User updated", "user": user})


@app.post("/api/water")
def add_water() -> tuple:
    payload = request_payload()
    glasses = payload.get("glasses", 1)
    try:
        glasses = max(1, int(glasses))
    except (TypeError, ValueError):
        glasses = 1
    total = service.add_water(glasses)
    return respond({"message": f"Added {glasses} glass(es)", "water_intake": total})


@app.put("/api/water/goal")
def set_water_goal() -> tuple:
    payload = request_payload()
    goal = payload.get("goal", 8)
    try:
        goal = max(1, int(goal))
    except (TypeError, ValueError):
        goal = 8
    service.set_water_goal(goal)
    return respond({"message": "Water goal updated", "water_goal": goal})


@app.post("/api/exercise")
def add_exercise() -> tuple:
    payload = request_payload()
    try:
        name = require_text(payload, "name")
    except ValueError as err:
        return fail(str(err))
    try:
        calories_burned = max(0, int(payload.get("calories_burned", 0)))
        duration = max(1, int(payload.get("duration_min", 30)))
    except (TypeError, ValueError):
        return fail("calories_burned and duration_min must be integers")
    exercises = service.add_exercise(name, calories_burned, duration)
    return respond({"message": "Exercise logged", "exercises": exercises}, 201)


@app.get("/api/exercise")
def get_exercises() -> tuple:
    exercises = service.exercises[service.current_user_index]
    total_burned = sum(e.get("calories_burned", 0) for e in exercises)
    return respond({"exercises": exercises, "total_burned": total_burned})


if __name__ == "__main__":
    port = int(os.environ.get("HK_TRACKER_API_PORT", "5050"))
    app.run(host="0.0.0.0", port=port, debug=True)
