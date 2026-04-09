import json

def save_data(user):
    with open("data.json", "w") as f:
        json.dump({"calories": user.get_daily_calories()}, f)

def load_data(user):
    try:
        with open("data.json", "r") as f:
            user.add_calories(json.load(f)["calories"])
    except (FileNotFoundError, KeyError, json.JSONDecodeError):
        pass
