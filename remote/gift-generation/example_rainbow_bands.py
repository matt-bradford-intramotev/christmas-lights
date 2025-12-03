#!/usr/bin/env python3
"""
Rainbow Bands Animation Example

Creates a GIFT animation with 7 rainbow-colored bands that fall down
the Z-axis with periodic boundary conditions.

The tree is divided into 7 equal bands along Z, each assigned a rainbow color.
The bands move downward over time, wrapping around at the bottom.
"""

import argparse
import numpy as np
from pathlib import Path
from gift_creator import GIFTCreator, hsv_to_rgb


def create_rainbow_bands_animation(
    position_map_path: str,
    output_path: str,
    duration: float = 10.0,
    framerate: float = 30.0,
    speed: float = 1.0
):
    """
    Create rainbow bands animation.

    Args:
        position_map_path: Path to position map JSON
        output_path: Output .gift file path
        duration: Animation duration in seconds
        framerate: Frames per second
        speed: Speed multiplier (higher = faster falling)
    """
    print("Creating Rainbow Bands Animation")
    print("=" * 60)
    print(f"Position map: {position_map_path}")
    print(f"Output: {output_path}")
    print(f"Duration: {duration}s @ {framerate}fps")
    print(f"Speed: {speed}x")
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

    # Define 7 rainbow colors (HSV hues evenly spaced)
    # Red, Orange, Yellow, Green, Cyan, Blue, Violet
    rainbow_hues = [0, 30, 60, 120, 180, 240, 300]
    rainbow_colors = [hsv_to_rgb(h, 1.0, 1.0) for h in rainbow_hues]
    num_bands = len(rainbow_colors)

    print(f"Rainbow bands ({num_bands} colors):")
    for i, (hue, color) in enumerate(zip(rainbow_hues, rainbow_colors)):
        print(f"  Band {i}: Hue {hue:3d}° -> RGB{color}")
    print()

    # Calculate frames
    num_frames = int(duration * framerate)
    print(f"Generating {num_frames} frames...")

    frames_generated = 0
    for frame_idx in range(num_frames):
        # Calculate time offset for this frame
        t = frame_idx / framerate

        # Offset for band positions (moves downward with periodic boundary)
        # We want the bands to cycle through completely during the animation
        # Number of complete cycles = speed
        cycles = speed * t / duration
        z_offset = cycles * z_range

        # Determine color for each LED
        frame_colors = []
        for led_idx in range(creator.led_count):
            z = z_positions[led_idx]

            # Normalize Z position to [0, 1] within the range
            z_norm = (z - z_min) / z_range

            # Add offset (moves bands down)
            # Subtract offset because positive Z is up, and we want bands to fall down
            z_animated = z_norm - (z_offset / z_range)

            # Apply periodic boundary conditions
            z_animated = z_animated % 1.0

            # Determine which band this LED is in
            band_idx = int(z_animated * num_bands) % num_bands

            # Get color for this band
            color = rainbow_colors[band_idx]
            frame_colors.append(color)

        # Add frame to animation
        creator.add_frame(frame_colors)
        frames_generated += 1

        # Progress indicator
        if (frame_idx + 1) % 30 == 0 or frame_idx == num_frames - 1:
            progress = (frame_idx + 1) / num_frames * 100
            print(f"  Progress: {progress:5.1f}% ({frame_idx + 1}/{num_frames} frames)")

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


def main():
    parser = argparse.ArgumentParser(
        description='Create rainbow bands falling animation',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage
  python3 example_rainbow_bands.py position_map.json

  # Custom output file
  python3 example_rainbow_bands.py position_map.json --output rainbow.gift

  # Longer, faster animation
  python3 example_rainbow_bands.py position_map.json --duration 20 --speed 2.0

  # High framerate for smooth motion
  python3 example_rainbow_bands.py position_map.json --framerate 60
        """
    )

    parser.add_argument('position_map',
                       help='Position map JSON file')
    parser.add_argument('--output', type=str, default='rainbow_bands.gift',
                       help='Output GIFT file (default: rainbow_bands.gift)')
    parser.add_argument('--duration', type=float, default=10.0,
                       help='Animation duration in seconds (default: 10.0)')
    parser.add_argument('--framerate', type=float, default=30.0,
                       help='Frames per second (default: 30.0)')
    parser.add_argument('--speed', type=float, default=1.0,
                       help='Speed multiplier - higher = faster falling (default: 1.0)')

    args = parser.parse_args()

    create_rainbow_bands_animation(
        position_map_path=args.position_map,
        output_path=args.output,
        duration=args.duration,
        framerate=args.framerate,
        speed=args.speed
    )


if __name__ == '__main__':
    main()
