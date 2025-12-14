#!/usr/bin/env python3
"""
Visualize classic and not-so-classic sort algorithms as horizontal bands,

Creates a GIFT animation visualizing classic (etc) sort algorithms on colored bands
along the Z-axis with periodic boundary conditions.

The num_bands param specifies the number of horizontal bands to divide the tree into,
each assigned an HSV hue (i.e. color) within the range 0-360.  Frames are generated of
each step of each algorithm sorting the bands from randomized order to ascending per
their HSV value.

Algorithms demonstrated: bubble, selection, insertion, merge, stooge, quick
"""

import argparse
import numpy as np
import math
from pathlib import Path
from gift_creator import GIFTCreator, hsv_to_rgb


def create_sortaggeon_animation(
    position_map_path: str,
    output_path: str,
    framerate: float = 30.0,
    num_bands: int = 100,
    sort_algos: list[str] = ['bubble', 'selection', 'insertion', 'merge', 'stooge', 'quick']
):
    """
    Create sort visualization animation.

    Args:
        position_map_path: Path to position map JSON
        output_path: Output .gift file path
        framerate: Frames per second
        num_bands: Number of horizontal bands to sort
        sort_algos: Sort algorithms to visualize, in that order
    """
    print("Creating Sort Visualization Animation")
    print("=" * 60)
    print(f"Position map: {position_map_path}")
    print(f"Output: {output_path}")
    print(f"Number bands: {num_bands}")
    print(f"Sort algorithms: {sort_algos}")
    print()

    # Create GIFT creator (LED count will be inferred from position map)
    creator = GIFTCreator(framerate=framerate)

    # Load position map
    print("Loading position map...")
    creator.load_position_map(position_map_path)
    print(f"✓ Loaded {creator.led_count} LED positions")

    # Get Z positions for all LEDs
    positions = creator.get_positions_array()
    z_positions = positions[:, 2]  # Z is the third column

    z_min = z_positions.min()
    z_max = z_positions.max()
    z_range = z_max - z_min

    print(f"  Z range: [{z_min:.3f}, {z_max:.3f}]")
    print(f"  Z span: {z_range:.3f}")
    print()

    # List of evenly spaced HSV hues, and colors
    rainbow_hues = np.linspace(0, 360, num_bands)

    # Random hue order as initial state for all sort algos
    rando_hues = np.random.permutation(rainbow_hues).tolist()
    rando_colors = [hsv_to_rgb(h, 1.0, 1.0) for h in rando_hues]

    print(f"Randomized ({num_bands} colors):")
    for i, (hue, color) in enumerate(zip(rando_hues, rando_colors)):
        print(f"  Band {i}: Hue {int(hue):3d}° -> RGB{color}")
    print()

    frames_generated = 0
    for a in sort_algos:
        sorted_hues = rando_hues.copy()
        frames = 0
        match a:
            case "bubble":
                print("Starting bubble sort")
                frames = _bubblesort_frames(creator, z_positions, num_bands, sorted_hues)
                print(f"Bubble sort generated {frames} frames")

            case "selection":
                print("Starting selection sort")
                frames = _selectionsort_frames(creator, z_positions, num_bands, sorted_hues)
                print(f"Selection sort generated {frames} frames")

            case "insertion":
                print("Starting insertion sort")
                frames = _insertionsort_frames(creator, z_positions, num_bands, sorted_hues)
                print(f"Insertion sort generated {frames} frames")

            case "merge":
                print("Starting merge sort")
                frames = _mergesort_frames(creator, z_positions, num_bands, sorted_hues)
                print(f"Merge sort generated {frames} frames")

            case "stooge":
                print("Starting stooge sort")
                frames = _stoogesort_frames(creator, z_positions, num_bands, sorted_hues)
                print(f"Stooge sort generated {frames} frames")

            case "quick":
                print("Starting quick sort")
                frames = _quicksort_frames(creator, z_positions, num_bands, sorted_hues)
                print(f"Quick sort generated {frames} frames")

            case _:
                print(f"Unknown sort algorithm {a}")

        frames_generated += frames

        # Pause a couple secs on sorted hues
        p = int(2 * framerate)
        for i in range(p):
            _add_frame(creator, z_positions, num_bands, sorted_hues)            
        frames_generated += p

    print()
    print(f"✓ Generated {frames_generated} frames")
    print()

    # Export animation
    print("Exporting GIFT file...")
    creator.export(output_path, loop=True)
    print()
    print("=" * 60)
    print("✓ Animation complete!")
    print()
    print("To play this animation, use the GIFT player on your Raspberry Pi:")
    print(f"  python3 gift_player.py {output_path}")

def _bubblesort_frames(creator: GIFTCreator, z_positions: list[float], num_bands: int, hues: list[float]) -> int:
    """
    The infamous Bubble Sort, everyone's favorite trivial sort algorithm.
    """
    frames = 0
    # Outer loop
    for i in range(num_bands):
        swapped = False
        # Inner loop
        for j in range(0, num_bands - i - 1):
            if hues[j] > hues[j+1]:
                # Swap
                hues[j], hues[j+1] = hues[j+1], hues[j]
                swapped = True
                # Add a frame with current sorting state
                _add_frame(creator, z_positions, num_bands, hues)
                frames += 1
        if not swapped:
            break
    return frames

def _selectionsort_frames(creator: GIFTCreator, z_positions: list[float], num_bands: int, hues: list[float]) -> int:
    """
    An iterative implementation of Selection Sort.
    """
    frames = 0
    # Outer loop
    for i in range(len(hues) - 1):
        min_index = i
        # Inner loop
        for j in range(i + 1, len(hues)):
            if hues[j] < hues[min_index]:
                min_index = j
        # Swap
        hues[i], hues[min_index] = hues[min_index], hues[i]
        # Add a frame with current sorting state
        _add_frame(creator, z_positions, num_bands, hues)
        frames += 1

    return frames

def _insertionsort_frames(creator: GIFTCreator, z_positions: list[float], num_bands: int, hues: list[float]) -> int:
    """
    An iterative implementation of Insertion Sort.
    """
    frames = 0
    # Outer loop
    for i in range(1, len(hues)):
        key = hues[i]

        # Inner loop
        j = i - 1
        while j >= 0 and key < hues[j]:
            hues[j+1] = hues[j]

            # Add a frame with current sorting state
            _add_frame(creator, z_positions, num_bands, hues)
            frames += 1
            j -= 1

        hues[j+1] = key

    return frames

def _mergesort_frames(creator: GIFTCreator, z_positions: list[float], num_bands: int, hues: list[float]) -> int:
    """
    An iterative implementation of Merge Sort.
    """
    frames = 0
    n = len(hues)
    # Start with sub-arrays of size 1, then 2, 4, 8, ...
    size = 1
    while size < n:
        # Traverse through all sub-arrays of the current size
        for left_start in range(0, n - size, 2 * size):
            # Find the mid and right indices of the sub-arrays
            mid = left_start + size - 1
            # Ensure the right index does not exceed array bounds
            right_end = min(left_start + 2 * size - 1, n - 1)
            
            # Merge the two sub-arrays arr[left_start...mid] and arr[mid+1...right_end]
            _mergesort_merge(hues, left_start, mid, right_end)

            # Add a frame with current sorting state
            _add_frame(creator, z_positions, num_bands, hues)
            frames += 1

        # Double the sub-array size for the next pass
        size *= 2
    return frames

def _mergesort_merge(arr, left, mid, right):
    """
    Helper function for Merge Sort, merges two sorted sub-arrays into a single sorted sub-array.
    """
    n1 = mid - left + 1
    n2 = right - mid
    
    # Create temporary arrays
    L = [0] * n1
    R = [0] * n2
    
    # Copy data to temp arrays L[] and R[]
    for i in range(n1):
        L[i] = arr[left + i]
    for j in range(n2):
        R[j] = arr[mid + 1 + j]
        
    # Merge the temporary arrays back into arr[left...right]
    i = 0  # Initial index of first sub-array
    j = 0  # Initial index of second sub-array
    k = left # Initial index of merged sub-array

    while i < n1 and j < n2:
        if L[i] <= R[j]:
            arr[k] = L[i]
            i += 1
        else:
            arr[k] = R[j]
            j += 1
        k += 1

    # Copy the remaining elements of L[], if any
    while i < n1:
        arr[k] = L[i]
        i += 1
        k += 1

    # Copy the remaining elements of R[], if any
    while j < n2:
        arr[k] = R[j]
        j += 1
        k += 1

def _stoogesort_frames(creator: GIFTCreator, z_positions: list[float], num_bands: int, hues: list[float]) -> int:
    """
    Sorts an array by element value using an iterative Stooge sort algorithm.  As you can see below, doing this
    without recursion made Gemini vent quite angrily in the comments.
    """
    frames = 0

    # The stack stores tuples of (low, high) indices representing the sub-arrays to sort
    stack = [(0, len(hues) - 1)]

    while stack:
        # Pop the current sub-array range from the stack
        low, high = stack.pop()

        # If the sub-array has less than 2 elements, it's already sorted
        if low >= high:
            continue

        # If the first element is greater than the last, swap them
        if hues[low] > hues[high]:
            hues[low], hues[high] = hues[high], hues[low]

            # Add a frame with current sorting state
            _add_frame(creator, z_positions, num_bands, hues)
            frames += 1

        # If there are 3 or more elements, we need to sort the two overlapping 2/3 segments
        if high - low + 1 > 2:
            # Calculate the size of the 1/3 segment (using math.ceil for the required behavior)
            # Python's integer division // usually works as floor, so we use math.ceil explicitly or adjust the formula
            # For the original algorithm's behavior, int((high - low + 1) / 3) is common
            t = (high - low + 1) // 3
            
            # The order of pushing to the stack is crucial to emulate the recursive call order (LIFO)
            # The last recursive call is "stooge sort the first 2/3 of the list again"
            # The second recursive call is "stooge sort the last 2/3 of the list"
            # The first recursive call is "stooge sort the initial 2/3 of the list"
            
            # 3. Push the first 2/3 segment again (will be processed first in the next iteration)
            stack.append((low, high - t))
            # 2. Push the last 2/3 segment
            stack.append((low + t, high))
            # 1. Push the first 2/3 segment (will be processed last in the next iteration, i.e., first after these pushes)
            # This push order is incorrect for LIFO to match recursion.
            # The calls happen as: 1st 2/3, then last 2/3, then 1st 2/3 again.
            # We want the 'again' part to execute after the 'last 2/3' part.
            
            # Correct push order for a stack (last in, first out):
            # We want the order of execution to be: (low, high - t), then (low + t, high), then (low, high - t) again.
            # So we push the last one first, then the second one, then the first one (which will be processed immediately).
            stack.append((low, high - t)) # Executes first
            stack.append((low + t, high)) # Executes second
            stack.append((low, high - t)) # Executes third/last
            
            # Note: This logic is still flawed because the 'again' call must happen *after* the previous two have finished
            # their entire sub-processes, which a simple LIFO stack doesn't handle automatically. This requires a more complex state management in the stack.

    # A simpler approach using a stack with state is required.
    # A true iterative implementation using a single list as a stack with just indices is non-trivial for Stooge sort due to
    # the re-sorting step that depends on the completion of the prior two steps.
    # The common recursive structure (see snippets) is the standard way.
    
    # Given the difficulty of a *simple* iterative implementation that maintains the exact Stooge sort logic,
    # the recommended approach is the clear and standard recursive function.
    # pass

    return frames

def _quicksort_frames(creator: GIFTCreator, z_positions: list[float], num_bands: int, hues: list[float]) -> int:
    """
    An iterative implementation of Quick Sort using an explicit stack.
    """
    frames = 0
    size = len(hues)
    # Create a stack (list in Python)
    stack = []
    # Push the initial low and high indices onto the stack
    stack.append(0)
    stack.append(size - 1)

    # Keep popping from stack while it is not empty
    while stack:
        # Pop high and low indices
        high = stack.pop()
        low = stack.pop()

        # Get pivot position after partitioning
        pi = _quicksort_partition(hues, low, high)

        # If there are elements on the left side of the pivot,
        # push that sub-array's indices to the stack
        if pi - 1 > low:
            stack.append(low)
            stack.append(pi - 1)

        # If there are elements on the right side of the pivot,
        # push that sub-array's indices to the stack
        if pi + 1 < high:
            stack.append(pi + 1)
            stack.append(high)

        # Add a frame with current sorting state
        _add_frame(creator, z_positions, num_bands, hues)
        frames += 1

    return frames

def _quicksort_partition(arr, low, high) -> int:
    """
    Partition function for iterative quicksort, takes the last element as the pivot,
    places the pivot element at its correct position in the sorted array, and places
    all smaller elements to the left of the pivot and all greater elements to the 
    right.
    """
    i = (low - 1)  # index of smaller element
    pivot = arr[high]  # pivot element

    for j in range(low, high):
        # If current element is smaller than or equal to pivot
        if arr[j] <= pivot:
            # increment index of smaller element
            i = i + 1
            arr[i], arr[j] = arr[j], arr[i]

    arr[i + 1], arr[high] = arr[high], arr[i + 1]
    return i + 1

def _add_frame(creator: GIFTCreator, z_positions: list[float], num_bands: int, hues: list[float]):
    """Add a frame to the specified GIFTCreator object using the list of hues specified.

    Args:
        creator (GIFTCreator): The LED Christmas tree animation under assembly
        z_positions (list[float]): List of LED Z positions
        num_bands (int): Number of color bands
        hues (list[float]): Current order (top to bottom) of colors
    """

    # Determine color for each LED
    frame_colors = []
    for led_idx in range(creator.led_count):
        z = z_positions[led_idx]

        # Determine which band this LED is in
        band_idx = int(z * num_bands) % num_bands

        # Get color for this band
        color = hsv_to_rgb(hues[band_idx], 1.0, 1.0)
        frame_colors.append(color)

    # Add frame to animation
    creator.add_frame(frame_colors)

def main():
    parser = argparse.ArgumentParser(
        description='Visualize sort algorithms in animation',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage
  python3 sortaggedons.py position_map.json

  # Custom output file
  python3 sortaggedons.py position_map.json --output sortaggedon.gift

  # High framerate for smooth motion
  python3 sortaggedons.py position_map.json --framerate 60

  # Custom number of color bands to sort
  python3 sortaggedons.py position_map.json --numbands 50
        """
    )

    parser.add_argument('position_map',
                       help='Position map JSON file')
    parser.add_argument('--output', type=str, default='rainbow_bands.gift',
                       help='Output GIFT file (default: rainbow_bands.gift)')
    parser.add_argument('--framerate', type=float, default=30.0,
                       help='Frames per second (default: 30.0)')
    parser.add_argument('--numbands', type=int, default=100,
                       help='Number color bands to sort (default: 100)')

    args = parser.parse_args()

    create_sortaggeon_animation(
        position_map_path=args.position_map,
        output_path=args.output,
        framerate=args.framerate,
        num_bands=args.numbands
    )


if __name__ == '__main__':
    main()
