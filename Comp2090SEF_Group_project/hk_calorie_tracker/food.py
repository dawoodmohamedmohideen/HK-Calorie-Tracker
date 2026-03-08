# This file defines the Food class.
# Each Food object represents one type of food and its calorie value.

class Food:

    # Constructor: initializes food name and calorie value
    def __init__(self, name, calories):
        self.name = name            # Name of the food
        self.calories = calories    # Calories for the food

    # Method to display food information
    def get_info(self):
        return f"{self.name} - {self.calories} kcal"