class Food:
    """Base food model shared by all food entries in the tracker.

    This class is the parent in the inheritance relationship, while
    subclasses can specialize how a food item is represented.
    """

    def __init__(self, name: str, calories: int):
        self.name = name
        self.calories = calories

    def get_info(self) -> str:
        return f"{self.name} - {self.calories} kcal"


class HKFood(Food):
    """Specialized food model for Hong Kong foods.

    This makes the inheritance relationship explicit: HKFood reuses the base
    Food state and overrides ``get_info`` to provide polymorphic behavior.
    """

    def __init__(self, name: str, calories: int, category: str):
        super().__init__(name, calories)
        self.category = category

    def get_info(self) -> str:
        return f"{self.name} ({self.category}) - {self.calories} kcal"