from user import User
from database import FoodDatabase
from tracker import DailyLog
from file_manager import save_data, load_data

def main():
    user = User("Dawood", 20, 70, 175, "Maintain")
    db = FoodDatabase()
    db.add_food("Char Siu Rice", 600, "Rice")
    db.add_food("Milk Tea", 250, "Drink")
    db.add_food("Dim Sum", 400, "Snack")
    log = DailyLog()
    load_data(user)

    while True:
        print("\n=== HK Calorie Tracker ===")
        print("1. Show Food List\n2. Add Food\n3. Show Log")
        print("4. Total Calories\n5. BMI\n6. Save & Exit")
        choice = input("Choose: ")

        if choice == "1":
            db.show_foods()
        elif choice == "2":
            food = db.get_food(input("Enter food: "))
            if food:
                log.add_entry(food)
                user.add_calories(food.calories)
                print("Added!")
            else:
                print("Food not found")
        elif choice == "3":
            log.show_log()
        elif choice == "4":
            total = log.total_calories()
            goal = user.get_daily_calorie_target()
            print(f"Total: {total}\nGoal: {goal}")
            print("You exceeded your goal!" if total > goal else "Within goal")
        elif choice == "5":
            print("BMI:", round(user.calculate_bmi(), 2))
        elif choice == "6":
            save_data(user)
            print("Data saved. Exiting...")
            break

if __name__ == "__main__":
    main()