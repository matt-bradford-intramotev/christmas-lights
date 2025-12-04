#!/usr/bin/env python3
"""
GIFT Animation Simulator

Visualizes GIFT animation files in 3D using LED position maps.
Shows what the animation would look like on the actual tree.
"""

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import List, Tuple, Optional

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.widgets import Button, Slider
from mpl_toolkits.mplot3d import Axes3D


def resolve_gift_path(filename: str) -> Optional[Path]:
    """
    Resolve GIFT file path, checking standard locations.

    Search order:
    1. Exact path as provided
    2. In pi/GIFT/gifts/ directory (if just a filename)

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
        # Navigate to pi/GIFT/gifts from wherever we are
        # Assume project structure: remote/gift-generation or pi/GIFT
        script_dir = Path(__file__).parent
        project_root = script_dir.parent.parent  # Go up to project root
        standard_path = project_root / 'pi' / 'GIFT' / 'gifts' / filename
        if standard_path.exists():
            return standard_path

    return None


def resolve_position_map_path(filename: str) -> Optional[Path]:
    """
    Resolve position map file path, checking standard locations.

    Search order:
    1. Exact path as provided
    2. In remote/calibration/position-maps/ directory (if just a filename)
    3. In pi/GIFT/position_maps/ directory (if just a filename)

    Args:
        filename: Position map filename or path

    Returns:
        Resolved Path object, or None if not found
    """
    path = Path(filename)

    # Try exact path
    if path.exists():
        return path

    # If it's just a filename (no directory), try standard locations
    if path.parent == Path('.'):
        script_dir = Path(__file__).parent
        project_root = script_dir.parent.parent  # Go up to project root

        # Try remote/calibration/position-maps first
        standard_path1 = project_root / 'remote' / 'calibration' / 'position-maps' / filename
        if standard_path1.exists():
            return standard_path1

        # Try pi/GIFT/position_maps as fallback
        standard_path2 = project_root / 'pi' / 'GIFT' / 'position_maps' / filename
        if standard_path2.exists():
            return standard_path2

    return None


class GIFTSimulator:
    """Simulate and visualize GIFT animations."""

    def __init__(self, gift_path: str, position_map_path: str):
        """
        Initialize simulator.

        Args:
            gift_path: Path to .gift animation file
            position_map_path: Path to position map JSON file
        """
        self.gift_path = Path(gift_path)
        self.position_map_path = Path(position_map_path)

        # Animation data
        self.metadata = {}
        self.frames = []
        self.positions = None
        self.led_count = 0

        # Playback state
        self.current_frame = 0
        self.playing = True
        self.speed = 1.0
        self.loop = True

        # Load data
        self._load_position_map()
        self._load_gift_file()

    def _load_position_map(self):
        """Load LED positions from JSON file."""
        print(f"Loading position map: {self.position_map_path}")
        with open(self.position_map_path, 'r') as f:
            data = json.load(f)

        positions_data = data['positions']
        self.positions = np.array(positions_data)
        self.led_count = len(self.positions)

        print(f"✓ Loaded {self.led_count} LED positions")
        print(f"  X range: [{self.positions[:, 0].min():.3f}, {self.positions[:, 0].max():.3f}]")
        print(f"  Y range: [{self.positions[:, 1].min():.3f}, {self.positions[:, 1].max():.3f}]")
        print(f"  Z range: [{self.positions[:, 2].min():.3f}, {self.positions[:, 2].max():.3f}]")

    def _load_gift_file(self):
        """Load GIFT animation file."""
        print(f"\nLoading GIFT file: {self.gift_path}")

        with open(self.gift_path, 'r') as f:
            # Parse metadata from comments
            for line in f:
                line = line.strip()
                if not line.startswith('#'):
                    break
                if ':' in line:
                    # Parse metadata: # key: value
                    parts = line[1:].split(':', 1)
                    if len(parts) == 2:
                        key = parts[0].strip()
                        value = parts[1].strip()
                        self.metadata[key] = value

            # Parse CSV data
            f.seek(0)  # Reset to beginning
            reader = csv.reader(f)

            # Skip comments and get header
            header = None
            for row in reader:
                if not row or (row[0].startswith('#')):
                    continue
                header = row
                break

            if header is None or header[0] != 'frame_id':
                raise ValueError("Invalid GIFT file: missing or invalid header")

            # Read frame data
            for row in reader:
                if not row or row[0].startswith('#'):
                    continue

                frame_id = int(row[0])
                colors = []

                # Parse RGB triplets
                for i in range(1, len(row), 3):
                    if i + 2 < len(row):
                        r = int(row[i])
                        g = int(row[i + 1])
                        b = int(row[i + 2])
                        colors.append((r, g, b))

                self.frames.append(colors)

        # Parse metadata values
        self.loop = self.metadata.get('loop', 'True').lower() == 'true'

        print(f"✓ Loaded {len(self.frames)} frames")
        print(f"  LED count: {self.metadata.get('led_count', 'unknown')}")
        print(f"  Frame count: {self.metadata.get('frame_count', 'unknown')}")
        print(f"  Framerate: {self.metadata.get('framerate', 'unknown')} fps")
        print(f"  Duration: {self.metadata.get('duration', 'unknown')}")
        print(f"  Loop: {self.loop}")

        # Verify LED count matches
        if self.frames:
            frame_led_count = len(self.frames[0])
            if frame_led_count != self.led_count:
                print(f"\n⚠ Warning: Frame has {frame_led_count} LEDs, but position map has {self.led_count}")
                print(f"  Using minimum: {min(frame_led_count, self.led_count)}")
                self.led_count = min(frame_led_count, self.led_count)

    def get_frame_colors(self, frame_idx: int) -> np.ndarray:
        """
        Get colors for a specific frame as RGB array (0-1 range).

        Args:
            frame_idx: Frame index

        Returns:
            Nx3 array of RGB colors (0-1 range)
        """
        if not self.frames:
            return np.zeros((self.led_count, 3))

        frame_idx = frame_idx % len(self.frames)
        colors = self.frames[frame_idx]

        # Convert to numpy array and normalize to 0-1 range
        rgb_array = np.array(colors[:self.led_count], dtype=float) / 255.0
        return rgb_array

    def visualize(self, view_angle: Tuple[float, float] = (30, 45),
                  marker_size: int = 100, show_axes: bool = True):
        """
        Create interactive 3D visualization of animation.

        Args:
            view_angle: Initial view angle (elevation, azimuth)
            marker_size: Size of LED markers
            show_axes: Whether to show coordinate axes
        """
        print(f"\n{'='*60}")
        print("Starting GIFT Simulator")
        print(f"{'='*60}")
        print("Controls:")
        print("  Space:  Play/Pause")
        print("  Left/Right Arrow: Previous/Next frame")
        print("  Mouse:  Rotate view (drag)")
        print("  Scroll: Zoom")
        print(f"{'='*60}\n")

        # Create figure and 3D axis
        fig = plt.figure(figsize=(14, 10))
        ax = fig.add_subplot(111, projection='3d')

        # Initial frame colors
        colors = self.get_frame_colors(0)

        # Create scatter plot
        scatter = ax.scatter(
            self.positions[:, 0],
            self.positions[:, 1],
            self.positions[:, 2],
            c=colors,
            s=marker_size,
            alpha=0.9,
            edgecolors='black',
            linewidths=0.5
        )

        # Optional: Draw LED strip path
        ax.plot(
            self.positions[:, 0],
            self.positions[:, 1],
            self.positions[:, 2],
            'gray',
            alpha=0.15,
            linewidth=0.5
        )

        # Set view
        ax.view_init(elev=view_angle[0], azim=view_angle[1])

        # Labels and title
        ax.set_xlabel('X')
        ax.set_ylabel('Y')
        ax.set_zlabel('Z (height)')

        # Equal aspect ratio
        max_range = np.array([
            self.positions[:, 0].max() - self.positions[:, 0].min(),
            self.positions[:, 1].max() - self.positions[:, 1].min(),
            self.positions[:, 2].max() - self.positions[:, 2].min()
        ]).max() / 2.0

        mid_x = (self.positions[:, 0].max() + self.positions[:, 0].min()) * 0.5
        mid_y = (self.positions[:, 1].max() + self.positions[:, 1].min()) * 0.5
        mid_z = (self.positions[:, 2].max() + self.positions[:, 2].min()) * 0.5

        ax.set_xlim(mid_x - max_range, mid_x + max_range)
        ax.set_ylim(mid_y - max_range, mid_y + max_range)
        ax.set_zlim(mid_z - max_range, mid_z + max_range)

        if not show_axes:
            ax.set_axis_off()

        # Title with frame info
        title = ax.text2D(0.5, 0.95, '', transform=ax.transAxes,
                         ha='center', va='top', fontsize=12, weight='bold')

        # Animation info text
        info_text = ax.text2D(0.02, 0.98, '', transform=ax.transAxes,
                             ha='left', va='top', fontsize=9, family='monospace')

        def update_title():
            """Update title with current frame info."""
            name = self.metadata.get('name', self.gift_path.stem)
            frame_info = f"Frame {self.current_frame + 1}/{len(self.frames)}"

            framerate = float(self.metadata.get('framerate', 30))
            time_pos = self.current_frame / framerate
            duration = len(self.frames) / framerate
            time_info = f"{time_pos:.2f}s / {duration:.2f}s"

            status = "▶ PLAYING" if self.playing else "⏸ PAUSED"

            title.set_text(f"{name}\n{frame_info}  |  {time_info}  |  {status}")

            info_text.set_text(
                f"Speed: {self.speed:.1f}x\n"
                f"Loop: {'ON' if self.loop else 'OFF'}\n"
                f"LEDs: {self.led_count}"
            )

        def update_frame(frame_num):
            """Update visualization for current frame."""
            if self.playing:
                self.current_frame = (self.current_frame + 1) % len(self.frames)
                if not self.loop and self.current_frame == 0:
                    self.playing = False

            colors = self.get_frame_colors(self.current_frame)
            scatter.set_color(colors)
            update_title()
            return scatter,

        # Keyboard controls
        def on_key(event):
            """Handle keyboard events."""
            if event.key == ' ':
                # Toggle play/pause
                self.playing = not self.playing
                update_title()
                fig.canvas.draw_idle()
            elif event.key == 'right':
                # Next frame
                self.current_frame = (self.current_frame + 1) % len(self.frames)
                colors = self.get_frame_colors(self.current_frame)
                scatter.set_color(colors)
                update_title()
                fig.canvas.draw_idle()
            elif event.key == 'left':
                # Previous frame
                self.current_frame = (self.current_frame - 1) % len(self.frames)
                colors = self.get_frame_colors(self.current_frame)
                scatter.set_color(colors)
                update_title()
                fig.canvas.draw_idle()
            elif event.key == 'l':
                # Toggle loop
                self.loop = not self.loop
                update_title()
                fig.canvas.draw_idle()
            elif event.key == 'r':
                # Reset to frame 0
                self.current_frame = 0
                colors = self.get_frame_colors(self.current_frame)
                scatter.set_color(colors)
                update_title()
                fig.canvas.draw_idle()
            elif event.key == '+' or event.key == '=':
                # Increase speed
                self.speed = min(self.speed * 1.5, 10.0)
                update_title()
                fig.canvas.draw_idle()
            elif event.key == '-' or event.key == '_':
                # Decrease speed
                self.speed = max(self.speed / 1.5, 0.1)
                update_title()
                fig.canvas.draw_idle()

        fig.canvas.mpl_connect('key_press_event', on_key)

        # Calculate animation interval based on framerate and speed
        framerate = float(self.metadata.get('framerate', 30))
        base_interval = 1000.0 / framerate  # milliseconds per frame

        def get_interval():
            """Get current animation interval adjusted for speed."""
            return base_interval / self.speed

        # Create animation
        anim = FuncAnimation(
            fig,
            update_frame,
            frames=len(self.frames),
            interval=get_interval(),
            blit=False,
            repeat=True
        )

        update_title()
        plt.tight_layout()
        plt.show()

    def export_preview_frames(self, output_dir: str, frame_indices: Optional[List[int]] = None,
                             view_angles: Optional[List[Tuple[float, float]]] = None):
        """
        Export preview images for specific frames.

        Args:
            output_dir: Directory to save preview images
            frame_indices: List of frame indices to export (default: every 30th frame)
            view_angles: List of (elevation, azimuth) tuples for different views
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        if frame_indices is None:
            # Export every 30th frame by default
            step = max(1, len(self.frames) // 10)
            frame_indices = list(range(0, len(self.frames), step))

        if view_angles is None:
            view_angles = [(30, 45)]  # Single default view

        print(f"\nExporting preview frames to: {output_path}")
        print(f"  Frames: {len(frame_indices)}")
        print(f"  Views: {len(view_angles)}")

        for frame_idx in frame_indices:
            colors = self.get_frame_colors(frame_idx)

            for view_idx, (elev, azim) in enumerate(view_angles):
                fig = plt.figure(figsize=(10, 8))
                ax = fig.add_subplot(111, projection='3d')

                ax.scatter(
                    self.positions[:, 0],
                    self.positions[:, 1],
                    self.positions[:, 2],
                    c=colors,
                    s=100,
                    alpha=0.9,
                    edgecolors='black',
                    linewidths=0.5
                )

                ax.view_init(elev=elev, azim=azim)
                ax.set_xlabel('X')
                ax.set_ylabel('Y')
                ax.set_zlabel('Z (height)')
                ax.set_title(f"{self.gift_path.stem} - Frame {frame_idx}")

                # Equal aspect ratio
                max_range = np.array([
                    self.positions[:, 0].max() - self.positions[:, 0].min(),
                    self.positions[:, 1].max() - self.positions[:, 1].min(),
                    self.positions[:, 2].max() - self.positions[:, 2].min()
                ]).max() / 2.0

                mid_x = (self.positions[:, 0].max() + self.positions[:, 0].min()) * 0.5
                mid_y = (self.positions[:, 1].max() + self.positions[:, 1].min()) * 0.5
                mid_z = (self.positions[:, 2].max() + self.positions[:, 2].min()) * 0.5

                ax.set_xlim(mid_x - max_range, mid_x + max_range)
                ax.set_ylim(mid_y - max_range, mid_y + max_range)
                ax.set_zlim(mid_z - max_range, mid_z + max_range)

                view_suffix = f"_view{view_idx}" if len(view_angles) > 1 else ""
                output_file = output_path / f"frame_{frame_idx:04d}{view_suffix}.png"
                plt.savefig(output_file, dpi=150, bbox_inches='tight')
                plt.close()

                print(f"  Saved: {output_file.name}")


def main():
    parser = argparse.ArgumentParser(
        description='Simulate GIFT animations in 3D',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic simulation
  python3 simulate_gift.py animation.gift position_map.json

  # Export preview frames
  python3 simulate_gift.py animation.gift position_map.json --export-frames ./previews

  # Customize visualization
  python3 simulate_gift.py animation.gift position_map.json \\
    --marker-size 150 \\
    --view 45 60 \\
    --no-axes

Interactive Controls:
  Space:  Play/Pause
  Left/Right Arrow: Previous/Next frame
  L:      Toggle loop
  R:      Reset to frame 0
  +/-:    Increase/Decrease speed
  Mouse:  Rotate view (drag)
  Scroll: Zoom
        """
    )

    parser.add_argument('gift_file',
                       help='GIFT animation file (.gift)')
    parser.add_argument('position_map',
                       help='Position map JSON file')
    parser.add_argument('--export-frames', type=str,
                       help='Export preview frames to directory (instead of interactive visualization)')
    parser.add_argument('--marker-size', type=int, default=100,
                       help='LED marker size (default: 100)')
    parser.add_argument('--view', type=float, nargs=2, default=[30, 45],
                       metavar=('ELEV', 'AZIM'),
                       help='Initial view angle: elevation azimuth (default: 30 45)')
    parser.add_argument('--no-axes', action='store_true',
                       help='Hide coordinate axes')

    args = parser.parse_args()

    # Resolve file paths
    gift_path = resolve_gift_path(args.gift_file)
    if gift_path is None:
        print(f"Error: GIFT file not found: {args.gift_file}")
        print(f"Searched in:")
        print(f"  - {Path(args.gift_file).absolute()}")
        if Path(args.gift_file).parent == Path('.'):
            script_dir = Path(__file__).parent
            project_root = script_dir.parent.parent
            print(f"  - {(project_root / 'pi' / 'GIFT' / 'gifts' / args.gift_file).absolute()}")
        return 1

    position_map_path = resolve_position_map_path(args.position_map)
    if position_map_path is None:
        print(f"Error: Position map not found: {args.position_map}")
        print(f"Searched in:")
        print(f"  - {Path(args.position_map).absolute()}")
        if Path(args.position_map).parent == Path('.'):
            script_dir = Path(__file__).parent
            project_root = script_dir.parent.parent
            print(f"  - {(project_root / 'remote' / 'calibration' / 'position-maps' / args.position_map).absolute()}")
            print(f"  - {(project_root / 'pi' / 'GIFT' / 'position_maps' / args.position_map).absolute()}")
        return 1

    # Create simulator
    simulator = GIFTSimulator(str(gift_path), str(position_map_path))

    if args.export_frames:
        # Export mode
        simulator.export_preview_frames(args.export_frames)
    else:
        # Interactive visualization mode
        simulator.visualize(
            view_angle=tuple(args.view),
            marker_size=args.marker_size,
            show_axes=not args.no_axes
        )


if __name__ == '__main__':
    main()
