# This file manages the daily food log of the user.

class DailyLog:

    # Constructor: initializes an empty log list
    def __init__(self):
        self.log = []

    # Method to add a food item to the daily log
    def add_entry(self, food):
        self.log.append(food)

    # Method to calculate the total calories consumed
    def total_calories(self):
        return sum(food.calories for food in self.log)

    # Method to display the foods eaten today
    def show_log(self):
        for food in self.log:
            print(food.get_info())