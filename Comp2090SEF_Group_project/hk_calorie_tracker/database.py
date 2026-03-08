# This file manages the food database used by the calorie tracker.

from food import Food

class FoodDatabase:

    # Constructor: creates an empty list to store food objects
    def __init__(self):
        self.food_list = []

    # Method to add a new food item to the database
    def add_food(self, name, calories):
        food = Food(name, calories)   # Create a Food object
        self.food_list.append(food)   # Store it in the list

    # Method to display all foods in the database
    def show_foods(self):
        for food in self.food_list:
            print(food.get_info())

    # Method to search for a food by name
    def get_food(self, name):
        for food in self.food_list:
            if food.name.lower() == name.lower():
                return food
        return None