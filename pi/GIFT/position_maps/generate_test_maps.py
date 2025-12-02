#!/usr/bin/env python3
"""
Generate test position map files for LED installations.

This script creates various test position maps that can be used for
development and testing before physical measurements are available.
"""

import json
import math
from datetime import date
from pathlib import Path


def generate_linear(count, spacing=0.05, output_file="test_linear.json"):
    """Generate a linear strip position map."""
    positions = [[i * spacing, 0.0, 0.0] for i in range(count)]

    data = {
        "version": "0.1.0",
        "metadata": {
            "name": f"Linear Test Strip - {count} LEDs",
            "led_count": count,
            "created": str(date.today()),
            "units": "meters",
            "origin": "left end of strip",
            "description": f"Simple linear arrangement, {spacing}m spacing"
        },
        "positions": positions
    }

    with open(output_file, 'w') as f:
        json.dump(data, f, indent=2)
    print(f"Generated {output_file}")


def generate_circle(count, radius=0.5, output_file="test_circle.json"):
    """Generate a circular arrangement position map."""
    positions = []
    for i in range(count):
        angle = (i / count) * 2 * math.pi
        x = radius * math.cos(angle)
        z = radius * math.sin(angle)
        positions.append([x, 0.0, z])

    data = {
        "version": "0.1.0",
        "metadata": {
            "name": f"Circle Test - {count} LEDs",
            "led_count": count,
            "created": str(date.today()),
            "units": "meters",
            "origin": "center of circle",
            "description": f"Circular arrangement, {radius}m radius"
        },
        "positions": positions
    }

    with open(output_file, 'w') as f:
        json.dump(data, f, indent=2)
    print(f"Generated {output_file}")


def generate_helix(count, radius=0.3, height=2.0, turns=3, output_file="test_helix.json"):
    """Generate a helical/spiral position map (simulates tree wrapping)."""
    positions = []
    for i in range(count):
        t = i / count
        angle = t * turns * 2 * math.pi
        x = radius * math.cos(angle)
        z = radius * math.sin(angle)
        y = t * height
        positions.append([x, y, z])

    data = {
        "version": "0.1.0",
        "metadata": {
            "name": f"Helix Test - {count} LEDs",
            "led_count": count,
            "created": str(date.today()),
            "units": "meters",
            "origin": "base center",
            "description": f"Helical arrangement, {radius}m radius, {height}m height, {turns} turns"
        },
        "positions": positions
    }

    with open(output_file, 'w') as f:
        json.dump(data, f, indent=2)
    print(f"Generated {output_file}")


def generate_cone(count, base_radius=0.5, top_radius=0.1, height=2.0, output_file="test_cone.json"):
    """Generate a conical position map (simulates Christmas tree shape)."""
    positions = []

    # Calculate number of turns based on spacing
    total_length = count * 0.05  # Assume 5cm spacing along spiral
    avg_circumference = math.pi * (base_radius + top_radius)
    turns = total_length / avg_circumference

    for i in range(count):
        t = i / count
        angle = t * turns * 2 * math.pi

        # Interpolate radius from base to top
        radius = base_radius + t * (top_radius - base_radius)

        x = radius * math.cos(angle)
        z = radius * math.sin(angle)
        y = t * height

        positions.append([x, y, z])

    data = {
        "version": "0.1.0",
        "metadata": {
            "name": f"Cone Test - {count} LEDs",
            "led_count": count,
            "created": str(date.today()),
            "units": "meters",
            "origin": "base center",
            "description": f"Conical arrangement (tree-like), base {base_radius}m, top {top_radius}m, height {height}m"
        },
        "positions": positions
    }

    with open(output_file, 'w') as f:
        json.dump(data, f, indent=2)
    print(f"Generated {output_file}")


def generate_random_box(count, size=1.0, output_file="test_random.json"):
    """Generate random positions within a box (for testing spatial algorithms)."""
    import random

    positions = []
    for i in range(count):
        x = (random.random() - 0.5) * size
        y = random.random() * size
        z = (random.random() - 0.5) * size
        positions.append([x, y, z])

    data = {
        "version": "0.1.0",
        "metadata": {
            "name": f"Random Box - {count} LEDs",
            "led_count": count,
            "created": str(date.today()),
            "units": "meters",
            "origin": "center of box",
            "description": f"Random positions in {size}m x {size}m x {size}m box"
        },
        "positions": positions
    }

    with open(output_file, 'w') as f:
        json.dump(data, f, indent=2)
    print(f"Generated {output_file}")


def main():
    """Generate standard test position maps."""
    print("Generating test position maps...")

    # Common test sizes
    generate_linear(50, spacing=0.05, output_file="test_linear_50.json")
    generate_linear(200, spacing=0.05, output_file="test_linear_200.json")

    generate_circle(50, radius=0.5, output_file="test_circle_50.json")
    generate_circle(200, radius=0.5, output_file="test_circle_200.json")

    generate_helix(200, radius=0.3, height=2.0, turns=5, output_file="test_helix_200.json")

    generate_cone(200, base_radius=0.5, top_radius=0.1, height=2.0, output_file="test_cone_200.json")

    generate_random_box(200, size=2.0, output_file="test_random_200.json")

    print("\nTest position maps generated successfully!")
    print("These can be used for testing GIFT animations before measuring actual LED positions.")


if __name__ == '__main__':
    main()
