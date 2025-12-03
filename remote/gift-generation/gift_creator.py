#!/usr/bin/env python3
"""
GIFT File Creator

Simple frame-based animation format for LED displays.
Format: CSV with frame_id, R_1, G_1, B_1, R_2, G_2, B_2, ...
"""

import json
import csv
from pathlib import Path
from typing import List, Optional, Tuple
import numpy as np


class LEDPosition:
    """3D position of an LED."""
    def __init__(self, index: int, x: float, y: float, z: float):
        self.index = index
        self.x = x
        self.y = y
        self.z = z


class GIFTCreator:
    """
    Create GIFT animation files.

    GIFT format is a simple frame-based animation:
    - CSV file with metadata header
    - Each row: frame_id, R_1, G_1, B_1, R_2, G_2, B_2, ...
    - RGB values are 0-255 integers
    """

    def __init__(self, led_count: Optional[int] = None, framerate: float = 30.0):
        """
        Initialize GIFT creator.

        Args:
            led_count: Number of LEDs (optional, will be inferred from position map if loaded)
            framerate: Target framerate in Hz
        """
        self.led_count = led_count
        self.framerate = framerate
        self.frames: List[List[Tuple[int, int, int]]] = []
        self.positions: Optional[List[LEDPosition]] = None
        self.unmapped_leds: set = set()  # Track LEDs without valid positions

    def load_position_map(self, filepath: str):
        """
        Load LED position map and infer LED count.

        Detects unmapped LEDs (those at position 0,0,0 or marked as failed in metadata)
        and tracks them so they can be set to black in animations.

        Args:
            filepath: Path to position map JSON file
        """
        with open(filepath, 'r') as f:
            data = json.load(f)

        self.positions = []
        self.unmapped_leds = set()

        # Handle both array format and dict format
        if isinstance(data['positions'], list):
            for idx, pos in enumerate(data['positions']):
                if isinstance(pos, list):
                    self.positions.append(LEDPosition(idx, pos[0], pos[1], pos[2]))
                    # Check if this is an unmapped LED (at origin)
                    if pos[0] == 0.0 and pos[1] == 0.0 and pos[2] == 0.0:
                        self.unmapped_leds.add(idx)
                elif isinstance(pos, dict):
                    self.positions.append(LEDPosition(idx, pos['x'], pos['y'], pos['z']))
                    # Check if this is an unmapped LED (at origin)
                    if pos['x'] == 0.0 and pos['y'] == 0.0 and pos['z'] == 0.0:
                        self.unmapped_leds.add(idx)

        # Set or verify LED count
        if self.led_count is None:
            self.led_count = len(self.positions)
            print(f"✓ Inferred LED count from position map: {self.led_count}")
        elif len(self.positions) != self.led_count:
            print(f"Warning: Position map has {len(self.positions)} LEDs, but creator was initialized with {self.led_count}")
            print(f"  Using position map LED count: {len(self.positions)}")
            self.led_count = len(self.positions)

        # Report unmapped LEDs
        if self.unmapped_leds:
            print(f"⚠ Warning: {len(self.unmapped_leds)} unmapped LED(s) detected (will be set to black in animations)")
            if len(self.unmapped_leds) <= 10:
                print(f"  Unmapped LEDs: {sorted(self.unmapped_leds)}")
            else:
                unmapped_sorted = sorted(self.unmapped_leds)
                print(f"  First 10 unmapped LEDs: {unmapped_sorted[:10]}")
                print(f"  (and {len(self.unmapped_leds) - 10} more...)")

    def add_frame(self, colors: List[Tuple[int, int, int]]):
        """
        Add a frame to the animation.

        Args:
            colors: List of (R, G, B) tuples, one per LED
        """
        if self.led_count is None:
            raise ValueError("LED count not set. Either specify led_count in __init__ or load a position map first.")

        if len(colors) != self.led_count:
            raise ValueError(f"Expected {self.led_count} colors, got {len(colors)}")

        # Validate RGB values
        for i, (r, g, b) in enumerate(colors):
            if not (0 <= r <= 255 and 0 <= g <= 255 and 0 <= b <= 255):
                raise ValueError(f"LED {i}: RGB values must be 0-255, got ({r}, {g}, {b})")

        # Override unmapped LEDs to black
        if self.unmapped_leds:
            colors = list(colors)  # Make mutable copy
            for led_idx in self.unmapped_leds:
                if led_idx < len(colors):
                    colors[led_idx] = (0, 0, 0)

        self.frames.append(colors)

    def add_frames(self, frames: List[List[Tuple[int, int, int]]]):
        """
        Add multiple frames at once.

        Args:
            frames: List of frames, each frame is a list of (R, G, B) tuples
        """
        for frame in frames:
            self.add_frame(frame)

    def export(self, filepath: str, loop: bool = True):
        """
        Export animation to GIFT file.

        Args:
            filepath: Output file path (.gift extension recommended)
            loop: Whether animation should loop
        """
        filepath = Path(filepath)

        with open(filepath, 'w', newline='') as f:
            # Write metadata header
            f.write(f"# GIFT Animation File\n")
            f.write(f"# Format: frame_id, R_1, G_1, B_1, R_2, G_2, B_2, ...\n")
            f.write(f"# led_count: {self.led_count}\n")
            f.write(f"# frame_count: {len(self.frames)}\n")
            f.write(f"# framerate: {self.framerate}\n")
            f.write(f"# duration: {len(self.frames) / self.framerate:.2f}s\n")
            f.write(f"# loop: {loop}\n")

            # Write CSV data
            writer = csv.writer(f)

            # Header row
            header = ['frame_id']
            for i in range(self.led_count):
                header.extend([f'R_{i}', f'G_{i}', f'B_{i}'])
            writer.writerow(header)

            # Data rows
            for frame_id, frame_colors in enumerate(self.frames):
                row = [frame_id]
                for r, g, b in frame_colors:
                    row.extend([r, g, b])
                writer.writerow(row)

        print(f"✓ Exported {len(self.frames)} frames to {filepath}")
        print(f"  LEDs: {self.led_count}")
        print(f"  Duration: {len(self.frames) / self.framerate:.2f}s @ {self.framerate}fps")

    def get_positions_array(self) -> np.ndarray:
        """
        Get LED positions as numpy array.

        Returns:
            Nx3 array of (x, y, z) positions
        """
        if self.positions is None:
            raise ValueError("No position map loaded")

        return np.array([[p.x, p.y, p.z] for p in self.positions])

    def get_positions_by_z(self) -> List[Tuple[int, float]]:
        """
        Get LED indices sorted by Z position.

        Returns:
            List of (led_index, z_position) tuples sorted by z
        """
        if self.positions is None:
            raise ValueError("No position map loaded")

        return sorted([(p.index, p.z) for p in self.positions], key=lambda x: x[1])

    def is_mapped(self, led_index: int) -> bool:
        """
        Check if an LED has a valid position mapping.

        Args:
            led_index: LED index to check

        Returns:
            True if LED has valid position, False if unmapped
        """
        return led_index not in self.unmapped_leds


def hsv_to_rgb(h: float, s: float, v: float) -> Tuple[int, int, int]:
    """
    Convert HSV to RGB.

    Args:
        h: Hue (0-360)
        s: Saturation (0-1)
        v: Value (0-1)

    Returns:
        (R, G, B) tuple with values 0-255
    """
    h = h % 360
    c = v * s
    x = c * (1 - abs((h / 60) % 2 - 1))
    m = v - c

    if h < 60:
        r, g, b = c, x, 0
    elif h < 120:
        r, g, b = x, c, 0
    elif h < 180:
        r, g, b = 0, c, x
    elif h < 240:
        r, g, b = 0, x, c
    elif h < 300:
        r, g, b = x, 0, c
    else:
        r, g, b = c, 0, x

    return (
        int((r + m) * 255),
        int((g + m) * 255),
        int((b + m) * 255)
    )


if __name__ == '__main__':
    # Example usage
    print("GIFT Creator Library")
    print("Import this module to create GIFT animations")
    print()
    print("Example:")
    print("  from gift_creator import GIFTCreator, hsv_to_rgb")
    print("  creator = GIFTCreator(framerate=30)")
    print("  creator.load_position_map('position_map.json')  # LED count inferred")
    print("  # Add frames...")
    print("  creator.export('animation.gift')")
