#!/usr/bin/env python3
"""
GIFT Player

Plays back GIFT animation files on LED hardware.
Requires rpi_ws281x library and must run with sudo for GPIO access.
"""

import csv
import time
import signal
import sys
import argparse
from pathlib import Path
from typing import List, Tuple, Optional

try:
    from rpi_ws281x import PixelStrip, Color
    HAS_LED_HARDWARE = True
except ImportError:
    HAS_LED_HARDWARE = False
    print("Warning: rpi_ws281x not available. Running in simulation mode.")


def resolve_gift_path(filename: str) -> Optional[Path]:
    """
    Resolve GIFT file path, checking standard locations.

    Search order:
    1. Exact path as provided
    2. In pi/GIFT/gifts/ directory (if just a filename)
    3. In current directory

    Args:
        filename: GIFT filename or path

    Returns:
        Resolved Path object, or None if not found
    """
    path = Path(filename)

    # Try exact path
    if path.exists():
        return path

    # If it's just a filename (no directory), try standard location
    if path.parent == Path('.'):
        # Get script directory and navigate to gifts folder
        script_dir = Path(__file__).parent
        standard_path = script_dir / 'gifts' / filename
        if standard_path.exists():
            return standard_path

    return None


class GIFTPlayer:
    """
    GIFT animation player.

    Loads and plays back frame-based animations on LED hardware.
    """

    def __init__(
        self,
        led_count: int = 200,
        led_pin: int = 18,
        led_freq_hz: int = 800000,
        led_dma: int = 10,
        led_brightness: int = 255,
        led_invert: bool = False,
        led_channel: int = 0
    ):
        """
        Initialize GIFT player.

        Args:
            led_count: Number of LEDs
            led_pin: GPIO pin connected to LED strip
            led_freq_hz: LED signal frequency
            led_dma: DMA channel
            led_brightness: Global brightness (0-255)
            led_invert: Invert signal
            led_channel: PWM channel
        """
        self.led_count = led_count
        self.strip = None
        self.simulation_mode = not HAS_LED_HARDWARE

        # Animation data
        self.frames: List[List[Tuple[int, int, int]]] = []
        self.framerate: float = 30.0
        self.loop: bool = True

        # Initialize LED strip
        if not self.simulation_mode:
            self.strip = PixelStrip(
                led_count, led_pin, led_freq_hz, led_dma,
                led_invert, led_brightness, led_channel
            )
            self.strip.begin()
            print(f"✓ LED strip initialized ({led_count} LEDs)")
        else:
            print(f"✓ Simulation mode ({led_count} LEDs)")

        # Setup cleanup handler
        signal.signal(signal.SIGINT, self.cleanup)
        signal.signal(signal.SIGTERM, self.cleanup)

    def load_gift_file(self, filepath: str):
        """
        Load GIFT animation file.

        Args:
            filepath: Path to .gift file
        """
        print(f"Loading GIFT file: {filepath}")

        with open(filepath, 'r') as f:
            # Read metadata from header comments
            for line in f:
                line = line.strip()
                if not line.startswith('#'):
                    break

                # Parse metadata
                if 'framerate:' in line:
                    self.framerate = float(line.split(':')[1].strip())
                elif 'loop:' in line:
                    self.loop = line.split(':')[1].strip().lower() == 'true'

            # Reset file pointer
            f.seek(0)

            # Skip header comments
            while True:
                pos = f.tell()
                line = f.readline()
                if not line.startswith('#'):
                    f.seek(pos)
                    break

            # Read CSV data
            reader = csv.reader(f)
            header = next(reader)  # Skip header row

            # Load frames
            self.frames = []
            for row in reader:
                frame_id = int(row[0])
                colors = []

                # Parse RGB triplets
                for i in range(1, len(row), 3):
                    r = int(row[i])
                    g = int(row[i + 1])
                    b = int(row[i + 2])
                    colors.append((r, g, b))

                self.frames.append(colors)

        print(f"✓ Loaded {len(self.frames)} frames")
        print(f"  Framerate: {self.framerate} fps")
        print(f"  Duration: {len(self.frames) / self.framerate:.2f}s")
        print(f"  Loop: {self.loop}")

    def set_frame(self, frame_colors: List[Tuple[int, int, int]]):
        """
        Display a single frame.

        Args:
            frame_colors: List of (R, G, B) tuples
        """
        if self.simulation_mode:
            # In simulation mode, just return
            return

        for i, (r, g, b) in enumerate(frame_colors):
            if i >= self.led_count:
                break
            # Note: Color() takes GRB order
            self.strip.setPixelColor(i, Color(g, r, b))

        self.strip.show()

    def play(self, speed: float = 1.0, max_loops: Optional[int] = None):
        """
        Play animation.

        Args:
            speed: Speed multiplier (1.0 = normal, 2.0 = 2x speed, 0.5 = half speed)
            max_loops: Maximum number of loops (None = infinite if loop=True)
        """
        if not self.frames:
            print("Error: No frames loaded")
            return

        frame_delay = 1.0 / (self.framerate * speed)
        loop_count = 0

        print()
        print("=" * 60)
        print("Starting playback...")
        print(f"  Frame delay: {frame_delay * 1000:.1f}ms ({self.framerate * speed:.1f} fps)")
        print(f"  Speed: {speed}x")
        if self.loop:
            if max_loops:
                print(f"  Loops: {max_loops}")
            else:
                print(f"  Loops: infinite (Ctrl+C to stop)")
        else:
            print(f"  Loops: once")
        print("=" * 60)
        print()

        try:
            while True:
                loop_count += 1

                # Play all frames
                start_time = time.time()
                for frame_idx, frame_colors in enumerate(self.frames):
                    frame_start = time.time()

                    # Display frame
                    self.set_frame(frame_colors)

                    # Progress indicator (every 30 frames)
                    if (frame_idx + 1) % 30 == 0 or frame_idx == len(self.frames) - 1:
                        elapsed = time.time() - start_time
                        progress = (frame_idx + 1) / len(self.frames) * 100
                        if self.loop:
                            print(f"  Loop {loop_count}: Frame {frame_idx + 1}/{len(self.frames)} ({progress:.0f}%)", end='\r')
                        else:
                            print(f"  Frame {frame_idx + 1}/{len(self.frames)} ({progress:.0f}%)", end='\r')

                    # Wait for next frame
                    elapsed = time.time() - frame_start
                    if elapsed < frame_delay:
                        time.sleep(frame_delay - elapsed)

                print()  # New line after progress indicator

                # Check loop conditions
                if not self.loop:
                    break
                if max_loops and loop_count >= max_loops:
                    break

        except KeyboardInterrupt:
            print("\n\nPlayback interrupted")

        print()
        print("=" * 60)
        print(f"✓ Playback complete ({loop_count} loop(s))")
        print("=" * 60)

    def cleanup(self, signum=None, frame=None):
        """Clean up and turn off LEDs."""
        print("\n\nCleaning up...")

        if not self.simulation_mode and self.strip:
            for i in range(self.led_count):
                self.strip.setPixelColor(i, Color(0, 0, 0))
            self.strip.show()

        print("✓ LEDs turned off")
        sys.exit(0)


def main():
    parser = argparse.ArgumentParser(
        description='Play GIFT animation files on LED hardware',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic playback
  sudo python3 gift_player.py animation.gift

  # Play at 2x speed
  sudo python3 gift_player.py animation.gift --speed 2.0

  # Play 5 loops then stop
  sudo python3 gift_player.py animation.gift --max-loops 5

  # Disable looping (play once)
  sudo python3 gift_player.py animation.gift --no-loop

  # Custom brightness
  sudo python3 gift_player.py animation.gift --brightness 128

Note: Requires sudo for GPIO access on Raspberry Pi
        """
    )

    parser.add_argument('gift_file',
                       help='GIFT animation file to play')
    parser.add_argument('--speed', type=float, default=1.0,
                       help='Speed multiplier (default: 1.0)')
    parser.add_argument('--max-loops', type=int, default=None,
                       help='Maximum loops (default: infinite if loop enabled)')
    parser.add_argument('--no-loop', action='store_true',
                       help='Disable looping (play once)')
    parser.add_argument('--brightness', type=int, default=255,
                       help='LED brightness 0-255 (default: 255)')
    parser.add_argument('--led-count', type=int, default=350,
                       help='Number of LEDs (default: 350)')
    parser.add_argument('--led-pin', type=int, default=18,
                       help='GPIO pin (default: 18)')

    args = parser.parse_args()

    # Resolve GIFT file path
    gift_path = resolve_gift_path(args.gift_file)
    if gift_path is None:
        print(f"Error: File not found: {args.gift_file}")
        print(f"Searched in:")
        print(f"  - {Path(args.gift_file).absolute()}")
        if Path(args.gift_file).parent == Path('.'):
            script_dir = Path(__file__).parent
            print(f"  - {(script_dir / 'gifts' / args.gift_file).absolute()}")
        return 1

    # Warn if not running as root (on real hardware)
    if HAS_LED_HARDWARE and os.geteuid() != 0:
        print("Warning: GPIO access requires root privileges")
        print("Please run with sudo: sudo python3 gift_player.py ...")
        return 1

    # Create player
    player = GIFTPlayer(
        led_count=args.led_count,
        led_pin=args.led_pin,
        led_brightness=args.brightness
    )

    # Load animation
    player.load_gift_file(str(gift_path))

    # Override loop setting if requested
    if args.no_loop:
        player.loop = False

    # Play animation
    player.play(speed=args.speed, max_loops=args.max_loops)

    # Cleanup
    player.cleanup()

    return 0


if __name__ == '__main__':
    import os
    sys.exit(main())
