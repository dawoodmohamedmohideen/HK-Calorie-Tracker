# This is the main program that runs the HK Calorie Tracker application.

from user import User
from database import FoodDatabase
from tracker import DailyLog


def main():

    # Create a sample user
    user = User("Dawood", 20, 70, 175, "Maintain")

    # Create food database
    db = FoodDatabase()

    # Add some Hong Kong food examples
    db.add_food("Char Siu Rice", 600)
    db.add_food("Milk Tea", 250)
    db.add_food("Dim Sum", 400)

    # Create a daily log object
    log = DailyLog()

    # Main program loop (menu system)
    while True:

        print("\n=== HK Calorie Tracker ===")
        print("1. Show Food List")
        print("2. Add Food to Daily Log")
        print("3. Show Daily Log")
        print("4. Show Total Calories")
        print("5. Exit")

        # Ask user to choose an option
        choice = input("Choose: ")

        # Option 1: Show available foods
        if choice == "1":
            db.show_foods()

        # Option 2: Add food to today's log
        elif choice == "2":
            name = input("Enter food name: ")

            food = db.get_food(name)

            if food:
                log.add_entry(food)              # Add food to log
                user.add_calories(food.calories) # Update user calorie count
                print("Food added!")
            else:
                print("Food not found.")

        # Option 3: Show foods eaten today
        elif choice == "3":
            log.show_log()

        # Option 4: Show total calories consumed today
        elif choice == "4":
            print("Total calories:", log.total_calories())

        # Option 5: Exit program
        elif choice == "5":
            print("Exiting program...")
            break


# Run the application
if __name__ == "__main__":
    main()