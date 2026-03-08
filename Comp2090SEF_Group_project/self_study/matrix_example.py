# This file demonstrates a simple Matrix data structure.
# A matrix is a 2D array used to store data in rows and columns.

class Matrix:

    # Constructor: create a matrix with given rows and columns
    def __init__(self, rows, cols):
        self.rows = rows
        self.cols = cols
        
        # Create a matrix filled with zeros
        self.matrix = [[0 for _ in range(cols)] for _ in range(rows)]

    # Method to set a value in the matrix
    def set_value(self, row, col, value):
        self.matrix[row][col] = value

    # Method to display the matrix
    def display(self):
        for row in self.matrix:
            print(row)


# Example usage
if __name__ == "__main__":

    # Create a 2x2 matrix
    m = Matrix(2, 2)

    # Insert values
    m.set_value(0, 0, 5)
    m.set_value(0, 1, 10)
    m.set_value(1, 0, 15)
    m.set_value(1, 1, 20)

    print("Matrix Data:")
    m.display()