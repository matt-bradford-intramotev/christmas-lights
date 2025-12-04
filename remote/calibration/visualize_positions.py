#!/usr/bin/env python3
"""
Position Map Visualization

3D visualization tool for viewing and validating LED position maps.
"""

import json
import argparse
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from pathlib import Path
from typing import Optional


def resolve_position_map_path(filename: str) -> Optional[Path]:
    """
    Resolve position map file path, checking standard locations.

    Search order:
    1. Exact path as provided
    2. In position-maps/ subdirectory (if just a filename)

    Args:
        filename: Position map filename or path

    Returns:
        Resolved Path object, or None if not found
    """
    path = Path(filename)

    # Try exact path
    if path.exists():
        return path

    # If it's just a filename (no directory), try standard location
    if path.parent == Path('.'):
        # Try position-maps subdirectory
        script_dir = Path(__file__).parent
        standard_path = script_dir / 'position-maps' / filename
        if standard_path.exists():
            return standard_path

    return None


def load_position_map(filepath):
    """Load position map from JSON file."""
    with open(filepath, 'r') as f:
        data = json.load(f)

    # Handle both array format and dict format
    positions = []
    if isinstance(data['positions'], list):
        for pos in data['positions']:
            if isinstance(pos, list):
                positions.append(pos)
            elif isinstance(pos, dict):
                positions.append([pos['x'], pos['y'], pos['z']])

    return np.array(positions), data.get('metadata', {})


def visualize_positions(positions, metadata, interactive=True, save_path=None):
    """
    Visualize LED positions in 3D.

    Args:
        positions: Nx3 array of (x, y, z) positions
        metadata: Metadata dictionary
        interactive: If True, show interactive plot
        save_path: If provided, save plot to this file
    """
    fig = plt.figure(figsize=(12, 10))
    ax = fig.add_subplot(111, projection='3d')

    # Plot points
    scatter = ax.scatter(
        positions[:, 0],
        positions[:, 1],
        positions[:, 2],
        c=positions[:, 2],  # Color by height (Z)
        cmap='viridis',
        s=20,
        alpha=0.6
    )

    # Connect points in sequence to show LED strip path
    ax.plot(
        positions[:, 0],
        positions[:, 1],
        positions[:, 2],
        'gray',
        alpha=0.2,
        linewidth=0.5
    )

    # Labels
    units = metadata.get('units', 'meters')
    unit_label = f" ({units})" if units != 'normalized' else " (normalized)"
    ax.set_xlabel(f'X{unit_label}')
    ax.set_ylabel(f'Y{unit_label}')
    ax.set_zlabel(f'Z{unit_label}, height')

    # Title with metadata
    title = metadata.get('name', 'LED Positions')
    led_count = metadata.get('led_count', len(positions))
    coordinate_system = metadata.get('coordinate_system', '')
    title_text = f"{title}\n{led_count} LEDs"
    if coordinate_system:
        title_text += f"\n{coordinate_system}"
    ax.set_title(title_text)

    # Color bar
    cbar = plt.colorbar(scatter, ax=ax, pad=0.1)
    height_label = 'Height' if units == 'normalized' else 'Height (m)'
    cbar.set_label(height_label)

    # Equal aspect ratio
    max_range = np.array([
        positions[:, 0].max() - positions[:, 0].min(),
        positions[:, 1].max() - positions[:, 1].min(),
        positions[:, 2].max() - positions[:, 2].min()
    ]).max() / 2.0

    mid_x = (positions[:, 0].max() + positions[:, 0].min()) * 0.5
    mid_y = (positions[:, 1].max() + positions[:, 1].min()) * 0.5
    mid_z = (positions[:, 2].max() + positions[:, 2].min()) * 0.5

    ax.set_xlim(mid_x - max_range, mid_x + max_range)
    ax.set_ylim(mid_y - max_range, mid_y + max_range)
    ax.set_zlim(mid_z - max_range, mid_z + max_range)

    # Add statistics text
    unit_str = '' if units == 'normalized' else ' m'
    stats_text = f"Statistics:\n"
    stats_text += f"X: [{positions[:, 0].min():.3f}, {positions[:, 0].max():.3f}]{unit_str}\n"
    stats_text += f"Y: [{positions[:, 1].min():.3f}, {positions[:, 1].max():.3f}]{unit_str}\n"
    stats_text += f"Z: [{positions[:, 2].min():.3f}, {positions[:, 2].max():.3f}]{unit_str}\n"
    stats_text += f"Total span: {max_range * 2:.3f}{unit_str}"

    plt.figtext(0.02, 0.02, stats_text, fontsize=9, family='monospace')

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"✓ Saved visualization to: {save_path}")

    if interactive:
        plt.show()
    else:
        plt.close()


def create_multiple_views(positions, metadata, output_dir):
    """Create multiple viewpoint visualizations."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Get units
    units = metadata.get('units', 'meters')
    unit_label = f" ({units})" if units != 'normalized' else " (normalized)"

    viewpoints = [
        ('front', 0, 0),
        ('side', 90, 0),
        ('top', 0, 90),
        ('isometric', 45, 30)
    ]

    for name, azim, elev in viewpoints:
        fig = plt.figure(figsize=(10, 8))
        ax = fig.add_subplot(111, projection='3d')

        scatter = ax.scatter(
            positions[:, 0],
            positions[:, 1],
            positions[:, 2],
            c=positions[:, 2],  # Color by Z (height)
            cmap='viridis',
            s=20,
            alpha=0.6
        )

        ax.plot(
            positions[:, 0],
            positions[:, 1],
            positions[:, 2],
            'gray',
            alpha=0.2,
            linewidth=0.5
        )

        ax.set_xlabel(f'X{unit_label}')
        ax.set_ylabel(f'Y{unit_label}')
        ax.set_zlabel(f'Z{unit_label}, height')
        ax.set_title(f"{metadata.get('name', 'LEDs')} - {name.title()} View")

        ax.view_init(elev=elev, azim=azim)

        height_label = 'Height' if units == 'normalized' else 'Height (m)'
        plt.colorbar(scatter, ax=ax, label=height_label)

        output_file = output_dir / f"view_{name}.png"
        plt.savefig(output_file, dpi=150, bbox_inches='tight')
        plt.close()

        print(f"  Saved {name} view: {output_file}")


def analyze_positions(positions, metadata):
    """Print detailed analysis of positions."""
    print("\n" + "=" * 60)
    print("Position Map Analysis")
    print("=" * 60)

    # Get units
    units = metadata.get('units', 'meters')
    unit_str = '' if units == 'normalized' else ' m'

    print("\nMetadata:")
    for key, value in metadata.items():
        if key == 'normalization':
            print(f"  {key}:")
            for norm_key, norm_value in value.items():
                print(f"    {norm_key}: {norm_value}")
        else:
            print(f"  {key}: {value}")

    print(f"\nPosition Statistics:")
    print(f"  Number of LEDs: {len(positions)}")
    print(f"  X range: [{positions[:, 0].min():.3f}, {positions[:, 0].max():.3f}]{unit_str}")
    print(f"  Y range: [{positions[:, 1].min():.3f}, {positions[:, 1].max():.3f}]{unit_str}")
    print(f"  Z range: [{positions[:, 2].min():.3f}, {positions[:, 2].max():.3f}]{unit_str} (height)")

    # Calculate distances between consecutive LEDs
    distances = np.linalg.norm(np.diff(positions, axis=0), axis=1)
    print(f"\nLED Spacing:")
    print(f"  Mean distance: {distances.mean():.3f}{unit_str}")
    print(f"  Std dev:       {distances.std():.3f}{unit_str}")
    print(f"  Min distance:  {distances.min():.3f}{unit_str}")
    print(f"  Max distance:  {distances.max():.3f}{unit_str}")

    # Find outliers (unusually large gaps)
    outlier_threshold = distances.mean() + 3 * distances.std()
    outliers = np.where(distances > outlier_threshold)[0]
    if len(outliers) > 0:
        print(f"\nWarning: {len(outliers)} large gaps detected:")
        for idx in outliers[:10]:  # Show first 10
            print(f"  Between LED {idx} and {idx+1}: {distances[idx]:.3f}{unit_str}")

    # Calculate total path length
    total_length = distances.sum()
    print(f"\nTotal LED strip length: {total_length:.2f}{unit_str}")

    # Bounding box
    bbox_size = positions.max(axis=0) - positions.min(axis=0)
    print(f"\nBounding box size:")
    print(f"  Width (X):  {bbox_size[0]:.2f}{unit_str}")
    print(f"  Depth (Y):  {bbox_size[1]:.2f}{unit_str}")
    print(f"  Height (Z): {bbox_size[2]:.2f}{unit_str}")


def main():
    parser = argparse.ArgumentParser(
        description='Visualize LED position maps in 3D',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive visualization
  python3 visualize_positions.py position_map.json

  # Save to file
  python3 visualize_positions.py position_map.json --save positions_3d.png

  # Generate multiple views
  python3 visualize_positions.py position_map.json --multi-view ./views/

  # Analysis only (no plot)
  python3 visualize_positions.py position_map.json --no-plot
        """
    )

    parser.add_argument('position_map',
                       help='Position map JSON file')
    parser.add_argument('--save', type=str,
                       help='Save plot to file instead of showing')
    parser.add_argument('--multi-view', type=str,
                       help='Generate multiple viewpoint images in specified directory')
    parser.add_argument('--no-plot', action='store_true',
                       help='Analysis only, do not show plot')

    args = parser.parse_args()

    # Resolve position map path
    position_map_path = resolve_position_map_path(args.position_map)
    if position_map_path is None:
        print(f"Error: Position map not found: {args.position_map}")
        print(f"Searched in:")
        print(f"  - {Path(args.position_map).absolute()}")
        if Path(args.position_map).parent == Path('.'):
            script_dir = Path(__file__).parent
            print(f"  - {(script_dir / 'position-maps' / args.position_map).absolute()}")
        return 1

    # Load position map
    print(f"Loading position map: {position_map_path}")
    positions, metadata = load_position_map(str(position_map_path))
    print(f"Loaded {len(positions)} LED positions")

    # Analyze
    analyze_positions(positions, metadata)

    # Visualize
    if not args.no_plot:
        if args.multi_view:
            print(f"\nGenerating multiple views...")
            create_multiple_views(positions, metadata, args.multi_view)
        else:
            print(f"\nGenerating visualization...")
            visualize_positions(
                positions,
                metadata,
                interactive=(args.save is None),
                save_path=args.save
            )


if __name__ == '__main__':
    main()
