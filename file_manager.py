# file_manager.py
# Saves and loads user calorie data

import json


def save_data(user):

    data = {
        "calories": user.get_calories()
    }

    with open("data.json", "w") as file:
        json.dump(data, file)


def load_data(user):

    try:
        with open("data.json", "r") as file:
            data = json.load(file)
            user.add_calories(data["calories"])
    except:
        pass
