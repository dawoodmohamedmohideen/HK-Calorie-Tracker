from __future__ import annotations

from collection_adt import ItemCollectionADT
from food import HKFood


class FoodDatabase:
    """Stores food objects using an ADT-backed collection.

    This class shows object composition: it owns an ``ItemCollectionADT`` of
    ``HKFood`` objects instead of exposing a raw list directly.
    """

    def __init__(self):
        self.food_list: ItemCollectionADT[HKFood] = ItemCollectionADT()

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