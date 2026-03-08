# This file implements the Shell Sort algorithm.
# Shell Sort is an improved version of insertion sort.

def shell_sort(arr):

    n = len(arr)
    gap = n // 2  # Initial gap size

    # Continue reducing gap until it becomes 0
    while gap > 0:

        for i in range(gap, n):

            temp = arr[i]
            j = i

            # Shift earlier gap-sorted elements
            while j >= gap and arr[j - gap] > temp:
                arr[j] = arr[j - gap]
                j -= gap

            arr[j] = temp

        gap //= 2  # Reduce gap size

    return arr


# Example usage
if __name__ == "__main__":

    numbers = [23, 12, 1, 8, 34, 54, 2, 3]

    print("Original List:", numbers)

    sorted_numbers = shell_sort(numbers)

    print("Sorted List:", sorted_numbers)