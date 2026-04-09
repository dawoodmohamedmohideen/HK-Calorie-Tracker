class Food:
    def __init__(self, name, calories):
        self.name = name
        self.calories = calories

    def get_info(self):
        return f"{self.name} - {self.calories} kcal"


class HKFood(Food):
    def __init__(self, name, calories, category):
        super().__init__(name, calories)
        self.category = category

    def get_info(self):
        return f"{self.name} ({self.category}) - {self.calories} kcal"