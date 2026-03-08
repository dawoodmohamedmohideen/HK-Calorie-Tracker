# This file implements the Heap Sort algorithm.
# Heap Sort uses a heap data structure to sort elements efficiently.

# Function to heapify a subtree
def heapify(arr, n, i):

    largest = i       # Assume root is largest
    left = 2 * i + 1  # Left child
    right = 2 * i + 2 # Right child

    # Check if left child exists and is greater
    if left < n and arr[left] > arr[largest]:
        largest = left

    # Check if right child exists and is greater
    if right < n and arr[right] > arr[largest]:
        largest = right

    # If largest is not root, swap and continue heapifying
    if largest != i:
        arr[i], arr[largest] = arr[largest], arr[i]
        heapify(arr, n, largest)


# Main Heap Sort function
def heap_sort(arr):

    n = len(arr)

    # Build a max heap
    for i in range(n // 2 - 1, -1, -1):
        heapify(arr, n, i)

    # Extract elements one by one
    for i in range(n - 1, 0, -1):

        arr[i], arr[0] = arr[0], arr[i]  # Move current root to end
        heapify(arr, i, 0)               # Heapify the reduced heap

    return arr


# Example test
if __name__ == "__main__":

    numbers = [12, 11, 13, 5, 6, 7]

    print("Original list:", numbers)

    sorted_numbers = heap_sort(numbers)

    print("Sorted list:", sorted_numbers)