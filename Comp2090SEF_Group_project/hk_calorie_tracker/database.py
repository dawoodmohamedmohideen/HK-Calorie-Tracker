from collection_adt import ItemCollectionADT
from food import HKFood


class FoodDatabase:
    def __init__(self):
        self.food_list = ItemCollectionADT()

    def add_food(self, name, calories, category="General"):
        food = HKFood(name, calories, category)
        self.food_list.add(food)

    def show_foods(self):
        for food in self.food_list:
            print(food.get_info())

    def get_food(self, name):
        for food in self.food_list:
            if food.name.lower() == name.lower():
                return food
        return None