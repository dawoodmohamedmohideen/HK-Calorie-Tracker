# This file defines the User class.
# The User object stores basic user information and tracks daily calories.

class User:
    
    # Constructor: initializes user attributes
    def __init__(self, name, age, weight, height, goal):
        self.name = name              # User name
        self.age = age                # User age
        self.weight = weight          # User weight (kg)
        self.height = height          # User height (cm)
        self.goal = goal              # Fitness goal (e.g., maintain / lose / gain)
        self.daily_calories = 0       # Total calories consumed today

    # Method to add calories when the user eats food
    def add_calories(self, calories):
        self.daily_calories += calories

    # Method to reset daily calories (for a new day)
    def reset_daily_calories(self):
        self.daily_calories = 0

    # Method to get the total calories consumed today
    def get_daily_calories(self):
        return self.daily_calories