from __future__ import annotations

import os
from threading import Lock
from typing import Dict, List

from flask import Flask, jsonify, request

from database import FoodDatabase
from tracker import DailyLog
from user import User


class CalorieTrackerService:
    def __init__(self) -> None:
        self._lock = Lock()
        self.users = [User("Dawood", 20, 70, 175, "Maintain", daily_calorie_target=2000)]
        self.current_user_index = 0
        self.db = FoodDatabase()
        self.logs = [DailyLog()]
        self.weekly_history = [[0]]
        # Water tracking: glasses per user per day
        self.water_intake: List[int] = [0]
        self.water_goal: List[int] = [8]  # default 8 glasses
        # Meal categories for log entries
        self.meal_labels: List[List[str]] = [[]]  # parallel to log entries
        # Streak tracking: consecutive days logged
        self.streaks: List[int] = [0]
        # Exercise tracking: list of {name, calories_burned, duration_min} per user
        self.exercises: List[List[Dict]] = [[]]
        self._seed_foods()

    def current_user(self) -> User:
        return self.users[self.current_user_index]

    def current_log(self) -> DailyLog:
        return self.logs[self.current_user_index]

    def _user_payload(self, user: User, index: int | None = None) -> Dict[str, int | str]:
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

    def _food_payload(self, food) -> Dict[str, int | str]:
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

    def add_user(self, name: str, age: int, weight: float, height: float, goal: str, daily_calorie_target: int = 2000) -> None:
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
            self.current_user_index = len(self.users) - 1

    def select_user(self, name: str) -> None:
        with self._lock:
            for index, user in enumerate(self.users):
                if user.name.lower() == name.lower():
                    self.current_user_index = index
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
                    return
            raise ValueError("User not found")

    def list_foods(self) -> List[Dict[str, int | str]]:
        return [self._food_payload(food) for food in self.db.food_list]

    def add_food(self, name: str, calories: int, category: str = "General") -> None:
        with self._lock:
            self.db.add_food(name, calories, category)

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
            return self._food_payload(food)

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
            return self.water_intake[self.current_user_index]

    def set_water_goal(self, goal: int) -> None:
        with self._lock:
            self.water_goal[self.current_user_index] = max(1, goal)

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

    def get_user(self) -> Dict[str, int | str]:
        return self._user_payload(self.current_user())

    def update_user(self, payload: Dict[str, object]) -> Dict[str, int | str]:
        with self._lock:
            user = self.current_user()
            user.name = str(payload.get("name", user.name)).strip() or user.name
            user.age = int(payload.get("age", user.age))
            user.weight = float(payload.get("weight", user.weight))
            user.height = float(payload.get("height", user.height))
            user.goal = str(payload.get("goal", user.goal)).strip() or user.goal
            daily_target = payload.get("daily_calorie_target", user.get_daily_calorie_target())
            user.set_daily_calorie_target(int(daily_target))
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
    category = str(payload.get("category", "General")).strip() or "General"

    if not name:
        return jsonify({"error": "Field 'name' is required"}), 400

    try:
        calories_int = int(calories)
        if calories_int <= 0:
            raise ValueError
    except (TypeError, ValueError):
        return jsonify({"error": "Field 'calories' must be a positive integer"}), 400

    service.add_food(name, calories_int, category)
    return jsonify({"message": "Food added", "food": {"name": name, "calories": calories_int, "category": category}}), 201


@app.post("/api/log")
def add_log_entry() -> tuple:
    payload = request.get_json(silent=True) or {}
    food_name = str(payload.get("food_name", "")).strip()

    if not food_name:
        return jsonify({"error": "Field 'food_name' is required"}), 400

    quantity = payload.get("quantity", 1)
    try:
        quantity = max(1, int(quantity))
    except (TypeError, ValueError):
        quantity = 1

    meal = str(payload.get("meal", "General")).strip() or "General"

    try:
        entry = service.log_food(food_name, quantity, meal)
    except ValueError as err:
        return jsonify({"error": str(err)}), 404

    return jsonify({"message": "Food logged", "entry": entry, "daily_calories": service.get_user()["daily_calories"]}), 201


@app.get("/api/log")
def get_log() -> tuple:
    return jsonify(service.get_log()), 200


@app.delete("/api/log")
def reset_log() -> tuple:
    service.reset_day()
    return jsonify({"message": "Daily log reset"}), 200


@app.get("/api/users")
def get_users() -> tuple:
    return jsonify({"users": service.list_users()}), 200


@app.post("/api/users")
def create_user() -> tuple:
    payload = request.get_json(silent=True) or {}
    name = str(payload.get("name", "")).strip()
    age = payload.get("age")
    weight = payload.get("weight")
    height = payload.get("height")
    goal = str(payload.get("goal", "Maintain")).strip() or "Maintain"
    daily_target = payload.get("daily_calorie_target", 2000)

    if not name:
        return jsonify({"error": "Field 'name' is required"}), 400

    try:
        age_int = int(age)
        weight_float = float(weight)
        height_float = float(height)
        daily_target_int = int(daily_target)
    except (TypeError, ValueError):
        return jsonify({"error": "Age, weight, height, and daily_calorie_target must be numbers"}), 400

    try:
        service.add_user(name, age_int, weight_float, height_float, goal, daily_target_int)
    except ValueError as err:
        return jsonify({"error": str(err)}), 409

    return jsonify({"message": "User created", "user": service.get_user()}), 201


@app.post("/api/users/select")
def select_user() -> tuple:
    payload = request.get_json(silent=True) or {}
    name = str(payload.get("name", "")).strip()

    if not name:
        return jsonify({"error": "Field 'name' is required"}), 400

    try:
        service.select_user(name)
    except ValueError as err:
        return jsonify({"error": str(err)}), 404

    return jsonify({"message": "User selected", "user": service.get_user()}), 200


@app.delete("/api/users")
def delete_user_endpoint() -> tuple:
    payload = request.get_json(silent=True) or {}
    name = str(payload.get("name", "")).strip()

    if not name:
        return jsonify({"error": "Field 'name' is required"}), 400

    try:
        service.delete_user(name)
    except ValueError as err:
        status = 400 if "last user" in str(err) else 404
        return jsonify({"error": str(err)}), status

    return jsonify({"message": "User deleted"}), 200


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


@app.post("/api/water")
def add_water() -> tuple:
    payload = request.get_json(silent=True) or {}
    glasses = payload.get("glasses", 1)
    try:
        glasses = max(1, int(glasses))
    except (TypeError, ValueError):
        glasses = 1
    total = service.add_water(glasses)
    return jsonify({"message": f"Added {glasses} glass(es)", "water_intake": total}), 200


@app.put("/api/water/goal")
def set_water_goal() -> tuple:
    payload = request.get_json(silent=True) or {}
    goal = payload.get("goal", 8)
    try:
        goal = max(1, int(goal))
    except (TypeError, ValueError):
        goal = 8
    service.set_water_goal(goal)
    return jsonify({"message": "Water goal updated", "water_goal": goal}), 200


@app.post("/api/exercise")
def add_exercise() -> tuple:
    payload = request.get_json(silent=True) or {}
    name = str(payload.get("name", "")).strip()
    if not name:
        return jsonify({"error": "Field 'name' is required"}), 400
    try:
        calories_burned = max(0, int(payload.get("calories_burned", 0)))
        duration = max(1, int(payload.get("duration_min", 30)))
    except (TypeError, ValueError):
        return jsonify({"error": "calories_burned and duration_min must be integers"}), 400
    with service._lock:
        service.exercises[service.current_user_index].append(
            {"name": name, "calories_burned": calories_burned, "duration_min": duration}
        )
    return jsonify({"message": "Exercise logged", "exercises": service.exercises[service.current_user_index]}), 201


@app.get("/api/exercise")
def get_exercises() -> tuple:
    exercises = service.exercises[service.current_user_index]
    total_burned = sum(e.get("calories_burned", 0) for e in exercises)
    return jsonify({"exercises": exercises, "total_burned": total_burned}), 200


if __name__ == "__main__":
    port = int(os.environ.get("HK_TRACKER_API_PORT", "5050"))
    app.run(host="0.0.0.0", port=port, debug=True)
