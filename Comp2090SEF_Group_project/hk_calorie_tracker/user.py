class User:
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

    def get_calories(self):
        return self.__daily_calories

    def get_daily_calories(self):
        return self.get_calories()

    def reset_calories(self):
        self.__daily_calories = 0

    def reset_daily_calories(self):
        self.reset_calories()

    def calculate_bmi(self):
        height_m = self.height / 100
        return self.weight / (height_m ** 2)

    def calorie_goal(self):
        return self.daily_calorie_target

    def set_daily_calorie_target(self, target: int):
        self.daily_calorie_target = target

    def get_daily_calorie_target(self):
        return self.daily_calorie_target