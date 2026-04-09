class Food:
    """Base class for food items."""

    def __init__(self, name, calories):
        self.name = name
        self.calories = calories

    def get_info(self):
        return f"{self.name} - {self.calories} kcal"


class HKFood(Food):
    """Inheritance: extends Food. Polymorphism: overrides get_info()."""

    def __init__(self, name, calories, category):
        super().__init__(name, calories)
        self.category = category

    def get_info(self):  # Polymorphism
        return f"{self.name} ({self.category}) - {self.calories} kcal"