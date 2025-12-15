#!/usr/bin/env python3
"""
Visualize classic and not-so-classic sort algorithms as horizontal bands,

Creates a GIFT animation visualizing classic (etc) sort algorithms on colored bands
along the Z-axis with periodic boundary conditions.

The num_bands param specifies the number of horizontal bands to divide the tree into,
each assigned an HSV hue (i.e. color) within the range 0-360.  Frames are generated of
each step of each algorithm sorting the bands from randomized order to ascending per
their HSV value.

Inspiration, sadly no sound support on the tree:
https://www.youtube.com/watch?v=kPRA0W1kECg

Algorithms demonstrated: bubble, selection, insertion, merge, gnome, quick, cocktail, radixlsd
"""

__author__ = "Matt Bradford, Ben West, the bot army"
__copyright__ = "Copyright (C) 2025 Intramotev"
__license__ = "All rights reserved"
__version__ = "0.1"

import argparse
import numpy as np
import math
from pathlib import Path
from gift_creator import GIFTCreator, hsv_to_rgb


def create_sortaggeon_animation(
    position_map_path: str,
    output_path: str,
    framerate: float = 45.0,
    num_bands: int = 100,
    sort_algos: list[str] = []
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

    # Demonstrate all algorithms by default
    _sort_algos = ['bubble', 'selection', 'insertion', 'merge', 'gnome', 'quick', 'cocktail', 'radixlsd'] if len(sort_algos) == 0 else sort_algos

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
    for a in _sort_algos:
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

            case "gnome":
                print("Starting gnome sort")
                frames = _gnomesort_frames(creator, z_positions, num_bands, sorted_hues)
                print(f"Gnome sort generated {frames} frames")

            case "quick":
                print("Starting quick sort")
                frames = _quicksort_frames(creator, z_positions, num_bands, sorted_hues)
                print(f"Quick sort generated {frames} frames")

            case "cocktail":
                print("Starting cocktail shaker sort")
                frames = _cocktailsort_frames(creator, z_positions, num_bands, sorted_hues)
                print(f"Cocktail shaker sort generated {frames} frames")

            case "radixlsd":
                print("Starting radix LSD sort")
                frames = _radixlsdsort_frames(creator, z_positions, num_bands, sorted_hues)
                print(f"Radix LSD sort generated {frames} frames")

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

def _bubblesort_frames(
    creator: GIFTCreator,
    z_positions: list[float],
    num_bands: int,
    hues: list[float]
) -> int:
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
                _add_frame(creator, z_positions, num_bands, hues, [j])
                frames += 1
        if not swapped:
            break
    return frames

def _selectionsort_frames(
    creator: GIFTCreator,
    z_positions: list[float],
    num_bands: int,
    hues: list[float]
) -> int:
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

                # For visualization, add a frame marking this band white
                _add_frame(creator, z_positions, num_bands, hues, [j])
                frames += 1

        # Swap
        hues[i], hues[min_index] = hues[min_index], hues[i]
        # Add a frame with current sorting state
        _add_frame(creator, z_positions, num_bands, hues)
        frames += 1

    return frames

def _insertionsort_frames(
    creator: GIFTCreator,
    z_positions: list[float],
    num_bands: int,
    hues: list[float]
) -> int:
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

            # Add a frame with current sorting state, highlighting key band
            _add_frame(creator, z_positions, num_bands, hues, [j])
            frames += 1
            j -= 1

        hues[j+1] = key

    return frames

def _mergesort_frames(
    creator: GIFTCreator,
    z_positions: list[float],
    num_bands: int,
    hues: list[float]
) -> int:
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
            
            # Merge the two sub-arrays hues[left_start...mid] and hues[mid+1...right_end]          
            n1 = mid - left_start + 1
            n2 = right_end - mid
            
            # Create temporary arrays
            L = [0] * n1
            R = [0] * n2
            
            # Copy data to temp arrays L[] and R[]
            for i in range(n1):
                L[i] = hues[left_start + i]
            for j in range(n2):
                R[j] = hues[mid + 1 + j]
                
            # Merge the temporary arrays back into arr[left...right]
            i = 0  # Initial index of first sub-array
            j = 0  # Initial index of second sub-array
            k = left_start # Initial index of merged sub-array

            while i < n1 and j < n2:
                if L[i] <= R[j]:
                    hues[k] = L[i]
                    i += 1
                else:
                    hues[k] = R[j]
                    j += 1

                # Add a frame with current sorting state
                _add_frame(creator, z_positions, num_bands, hues, [k])
                frames += 1

                k += 1

            # Copy the remaining elements of L[], if any
            while i < n1:
                hues[k] = L[i]

                # Add a frame with current sorting state
                _add_frame(creator, z_positions, num_bands, hues, [k])
                frames += 1

                i += 1
                k += 1

            # Copy the remaining elements of R[], if any
            while j < n2:
                hues[k] = R[j]

                # Add a frame with current sorting state
                _add_frame(creator, z_positions, num_bands, hues, [k])
                frames += 1

                j += 1
                k += 1

        # Double the sub-array size for the next pass
        size *= 2
    return frames

def _gnomesort_frames(
    creator: GIFTCreator,
    z_positions: list[float],
    num_bands: int,
    hues: list[float]
) -> int:
    """
    Sorts an array by element value using the Gnome Sort algorithm.
    """
    frames = 0

    n = len(hues)
    index = 0
    while index < n:
        if index == 0:
            index += 1
        elif hues[index] >= hues[index - 1]:
            index += 1
        else:
            # Swap elements and move backward
            hues[index], hues[index - 1] = hues[index - 1], hues[index]

            # Add a frame with current sorting state
            _add_frame(creator, z_positions, num_bands, hues, [index])
            frames += 1

            index -= 1
    return frames

def _quicksort_frames(
    creator: GIFTCreator,
    z_positions: list[float],
    num_bands: int,
    hues: list[float]
) -> int:
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

        # Partitioning for iterative quicksort, takes the last element as the pivot,
        # places the pivot element at its correct position in the sorted array, and places
        # all smaller elements to the left of the pivot and all greater elements to the 
        # right.
        i = (low - 1)  # index of smaller element
        pivot = hues[high]  # pivot element

        for j in range(low, high):
            # If current element is smaller than or equal to pivot
            if hues[j] <= pivot:
                # increment index of smaller element
                i = i + 1
                hues[i], hues[j] = hues[j], hues[i]

                # Add a frame with current sorting state
                _add_frame(creator, z_positions, num_bands, hues, [i, j])
                frames += 1

        hues[i + 1], hues[high] = hues[high], hues[i + 1]
        pi = i + 1

        # Add a frame with current sorting state
        _add_frame(creator, z_positions, num_bands, hues)
        frames += 1

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

    return frames

def _cocktailsort_frames(
    creator: GIFTCreator,
    z_positions: list[float],
    num_bands: int,
    hues: list[float]
) -> int:
    """
    Sorts an array using the Cocktail Shaker Sort algorithm.
    """
    frames = 0

    n = len(hues)
    swapped = True
    start = 0
    end = n - 1

    while swapped:
        # Reset the swapped flag to False for the next iteration
        swapped = False

        # --- Forward Pass (left to right) ---
        # This pass moves the largest unsorted element to its correct position at the end
        for i in range(start, end):
            if hues[i] > hues[i + 1]:
                hues[i], hues[i + 1] = hues[i + 1], hues[i]  # Swap elements
                swapped = True

                # Add a frame with current sorting state
                _add_frame(creator, z_positions, num_bands, hues, [i])
                frames += 1

        # If no elements were swapped in the forward pass, the array is sorted
        if not swapped:
            break

        # Decrease the end boundary as the largest element is now in place
        end -= 1

        # --- Backward Pass (right to left) ---
        # Reset the swapped flag for the backward pass
        swapped = False
        # This pass moves the smallest unsorted element to its correct position at the beginning
        for i in range(end - 1, start - 1, -1):
            if hues[i] > hues[i + 1]:
                hues[i], hues[i + 1] = hues[i + 1], hues[i]  # Swap elements
                swapped = True

                # Add a frame with current sorting state
                _add_frame(creator, z_positions, num_bands, hues, [i])
                frames += 1

        # Increase the start boundary as the smallest element is now in place
        start += 1
    
    return frames

def _radixlsdsort_frames(
    creator: GIFTCreator,
    z_positions: list[float],
    num_bands: int,
    hues: list[float]
) -> int:
    """
    Sorts an array using the Radix LSD sort algorithm.
    """
    frames = 0
    n = len(hues)

    # Find the maximum number to know the number of digits
    max_val = max(hues)

    # Do counting sort for every digit. Note that instead of 
    # passing the digit number, exp is passed. exp is 10^i 
    # where i is the current digit number (1, 10, 100, ...).
    exp = 1
    while max_val // exp > 0:

        output = [0] * n
        count = [0] * 10  # Base 10 for decimal numbers

        # Store count of occurrences in count[]
        for i in range(n):
            index = hues[i] // exp
            digit = int(index % 10)
            count[digit] += 1

        # Change count[i] so that count[i] now contains actual
        # position of this digit in output[]
        for i in range(1, 10):
            count[i] += count[i - 1]

        # Build the output array
        i = n - 1
        while i >= 0:
            index = hues[i] // exp
            digit = int(index % 10)
            output[count[digit] - 1] = hues[i]
            count[digit] -= 1
            i -= 1

        # Copy the output array to arr[], so that arr now
        # contains sorted numbers according to current digit
        for i in range(n):
            hues[i] = output[i]

            # Add a frame with current sorting state
            _add_frame(creator, z_positions, num_bands, hues, [i])
            frames += 1

        exp *= 10
    
    return frames

def _add_frame(
    creator: GIFTCreator,
    z_positions: list[float],
    num_bands: int,
    hues: list[float],
    highlights: list[int] = []
):
    """Add a frame to the specified GIFTCreator object using the list of hues specified.

    Args:
        creator (GIFTCreator): The LED Christmas tree animation under assembly
        z_positions (list[float]): List of LED Z positions
        num_bands (int): Number of color bands
        hues (list[float]): Current order (top to bottom) of colors
        highlights (list[int]): Indices in hues to instead mark white for highlight
    """

    # Determine color for each LED
    frame_colors = []

    z_min = z_positions.min()
    z_max = z_positions.max()
    z_range = z_max - z_min

    for led_idx in range(creator.led_count):
        z = z_positions[led_idx]

        # Normalize Z position to [0, 1] within the range
        z_norm = (z - z_min) / z_range

        # Determine which band this LED is in
        band_idx = int(z_norm * num_bands) % num_bands

        # Get color for this band, or mark white if highlighted
        color = hsv_to_rgb(0, 0, 1.0) if band_idx in highlights else hsv_to_rgb(hues[band_idx], 1.0, 1.0)
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

  # Specify a subset of sort algorithms to visualize
  python3 sortaggedons.py position_map.json --sort_algos quick cocktail
        """
    )

    parser.add_argument('position_map',
                       help='Position map JSON file')
    parser.add_argument('--output', type=str, default='rainbow_bands.gift',
                       help='Output GIFT file (default: rainbow_bands.gift)')
    parser.add_argument('--framerate', type=float, default=45.0,
                       help='Frames per second (default: 45.0)')
    parser.add_argument('--numbands', type=int, default=100,
                       help='Number color bands to sort (default: 100)')
    parser.add_argument('--sort_algos', nargs='+', default=[],
                       help='Space-separated list of sort algorithms (supported: bubble selection insertion merge gnome quick cocktail radixlsd - default: ALL OF THEM!!)')

    args = parser.parse_args()

    create_sortaggeon_animation(
        position_map_path=args.position_map,
        output_path=args.output,
        framerate=args.framerate,
        num_bands=args.numbands,
        sort_algos=args.sort_algos
    )


if __name__ == '__main__':
    main()
