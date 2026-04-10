class User:
    """User profile model.

    The private ``__daily_calories`` field highlights encapsulation: outside
    code should interact with the value through this class's methods instead of
    mutating it directly.
    """

    def __init__(self, name, age, weight, height, goal, daily_calorie_target: int = 2000):
        self.name = name
        self.age = age
        self.weight = weight
        self.height = height
        self.goal = goal
        self.daily_calorie_target = daily_calorie_target
        self.__daily_calories = 0

    def add_calories(self, calories):
        self.__daily_calories += calories

    def get_daily_calories(self):
        return self.__daily_calories

    def reset_daily_calories(self):
        self.__daily_calories = 0

    def calculate_bmi(self):
        if self.height <= 0:
            return 0.0
        return self.weight / (self.height / 100) ** 2

    def get_daily_calorie_target(self):
        return self.daily_calorie_target

    def set_daily_calorie_target(self, target: int):
        self.daily_calorie_target = target