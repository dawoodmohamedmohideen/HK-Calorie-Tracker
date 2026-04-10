from __future__ import annotations

from collection_adt import ItemCollectionADT
from food import Food


class DailyLog:
    """Tracks one day's food entries using the shared ADT.

    Like ``FoodDatabase``, this class makes the ADT usage explicit by storing
    entries inside ``ItemCollectionADT`` rather than a plain list.
    """

    def __init__(self):
        self.log: ItemCollectionADT[Food] = ItemCollectionADT()

    def add_entry(self, food: Food):
        self.log.add(food)

    def total_calories(self):
        return sum(food.calories for food in self.log)

    def show_log(self):
        for food in self.log:
            print(food.get_info())