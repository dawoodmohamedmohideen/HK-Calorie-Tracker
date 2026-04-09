class DailyLog:
    def __init__(self):
        self.log = []

    def add_entry(self, food):
        self.log.append(food)

    def total_calories(self):
        return sum(food.calories for food in self.log)

    def show_log(self):
        for food in self.log:
            print(food.get_info())