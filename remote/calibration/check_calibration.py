#!/usr/bin/env python3
"""
Calibration Pre-Check Script

Analyzes calibration session data to identify potential problems before triangulation.
Shows which LEDs have insufficient detections and displays their images if available.
"""

import argparse
import json
from pathlib import Path
from collections import defaultdict
import sys

# Optional imports for image display
try:
    import cv2
    import matplotlib.pyplot as plt
    import numpy as np
    HAS_IMAGE_SUPPORT = True
except ImportError:
    HAS_IMAGE_SUPPORT = False


def load_sessions(calibration_dir):
    """
    Load all calibration session files.

    Returns:
        dict: Map of angle_id -> session_data
    """
    calibration_dir = Path(calibration_dir)
    sessions = {}

    # Find all session files
    session_files = list(calibration_dir.glob("session_angle_*.json"))

    if not session_files:
        print(f"ERROR: No session files found in {calibration_dir}")
        print("Expected files like: session_angle_0.json, session_angle_1.json, etc.")
        return None

    print(f"Found {len(session_files)} session file(s)")

    for session_file in sorted(session_files):
        # Extract angle ID from filename
        try:
            angle_id = int(session_file.stem.split('_')[-1])
        except ValueError:
            print(f"Warning: Could not parse angle ID from {session_file.name}")
            continue

        # Load session data
        with open(session_file, 'r') as f:
            session_data = json.load(f)

        sessions[angle_id] = session_data
        led_count = session_data['session']['led_count']
        det_count = len(session_data['detections'])
        print(f"  Angle {angle_id}: {det_count}/{led_count} LEDs")

    return sessions


def analyze_detections(sessions):
    """
    Analyze detection quality across all sessions.

    Returns:
        dict: LED statistics including detection counts
    """
    # Track detections per LED
    led_detections = defaultdict(list)  # led_index -> [(angle_id, detection), ...]

    for angle_id, session_data in sessions.items():
        for detection in session_data['detections']:
            led_idx = detection['led_index']
            led_detections[led_idx].append((angle_id, detection))

    # Analyze each LED
    led_stats = {}

    # Determine max LED index
    if led_detections:
        max_led_idx = max(led_detections.keys())
    else:
        return {}

    for led_idx in range(max_led_idx + 1):
        detections = led_detections[led_idx]

        # Count successful (non-occluded) detections
        successful = [d for angle_id, d in detections if not d['occluded']]
        occluded = [d for angle_id, d in detections if d['occluded']]

        led_stats[led_idx] = {
            'total_detections': len(detections),
            'successful_detections': len(successful),
            'occluded_detections': len(occluded),
            'angles_detected': [angle_id for angle_id, d in detections if not d['occluded']],
            'angles_occluded': [angle_id for angle_id, d in detections if d['occluded']],
            'detections': detections
        }

    return led_stats


def find_problematic_leds(led_stats, min_detections=4):
    """
    Identify LEDs that may cause problems in triangulation.

    Args:
        led_stats: LED statistics from analyze_detections
        min_detections: Minimum successful detections required

    Returns:
        list: LED indices with insufficient detections
    """
    problematic = []

    for led_idx, stats in led_stats.items():
        if stats['successful_detections'] < min_detections:
            problematic.append(led_idx)

    return sorted(problematic)


def display_led_images(calibration_dir, led_indices, angles):
    """
    Display images for problematic LEDs.

    Args:
        calibration_dir: Path to calibration directory
        led_indices: List of LED indices to display
        angles: List of available angles
    """
    if not HAS_IMAGE_SUPPORT:
        print("\nWARNING: Image display requires opencv-python and matplotlib")
        print("Install with: pip3 install opencv-python matplotlib")
        return

    calibration_dir = Path(calibration_dir)

    # Check which LEDs have images
    leds_with_images = []
    for led_idx in led_indices:
        # Check if any angle has images for this LED
        has_images = False
        for angle in angles:
            image_dir = calibration_dir / f"images_angle_{angle}"
            image_path = image_dir / f"led_{led_idx:03d}.jpg"
            if image_path.exists():
                has_images = True
                break

        if has_images:
            leds_with_images.append(led_idx)

    if not leds_with_images:
        print("\nNo saved images found for problematic LEDs")
        print("Use --save-images during capture to enable image review")
        return

    print(f"\nDisplaying images for {len(leds_with_images)} LED(s) with saved images...")
    print("Close the image window to continue")

    # Display images in a grid
    for led_idx in leds_with_images:
        images = []
        titles = []

        for angle in sorted(angles):
            image_dir = calibration_dir / f"images_angle_{angle}"
            image_path = image_dir / f"led_{led_idx:03d}.jpg"

            if image_path.exists():
                img = cv2.imread(str(image_path))
                if img is not None:
                    # Convert BGR to RGB for matplotlib
                    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                    images.append(img)
                    titles.append(f"Angle {angle}")

        if images:
            # Create figure with subplots
            n_images = len(images)
            cols = min(4, n_images)
            rows = (n_images + cols - 1) // cols

            fig, axes = plt.subplots(rows, cols, figsize=(4*cols, 4*rows))
            fig.suptitle(f"LED {led_idx} - Images from all angles", fontsize=16)

            if n_images == 1:
                axes = [axes]
            else:
                axes = axes.flatten() if n_images > 1 else [axes]

            for i, (img, title) in enumerate(zip(images, titles)):
                axes[i].imshow(img)
                axes[i].set_title(title)
                axes[i].axis('off')

            # Hide unused subplots
            for i in range(n_images, len(axes)):
                axes[i].axis('off')

            plt.tight_layout()
            plt.show()


def print_report(sessions, led_stats, problematic_leds, min_detections):
    """Print detailed analysis report."""
    print("\n" + "=" * 70)
    print("CALIBRATION PRE-CHECK REPORT")
    print("=" * 70)

    # Overall statistics
    num_angles = len(sessions)
    num_leds = len(led_stats)

    print(f"\nSession Overview:")
    print(f"  Number of angles:        {num_angles}")
    print(f"  Total LEDs:              {num_leds}")
    print(f"  Minimum detections:      {min_detections} (for good triangulation)")

    # Detection quality summary
    fully_detected = sum(1 for s in led_stats.values() if s['successful_detections'] >= num_angles)
    good_detections = sum(1 for s in led_stats.values() if s['successful_detections'] >= min_detections)
    poor_detections = len(problematic_leds)

    print(f"\nDetection Quality:")
    print(f"  Perfect (all angles):    {fully_detected} LEDs")
    print(f"  Good (≥{min_detections} angles):       {good_detections} LEDs")
    print(f"  Poor (<{min_detections} angles):       {poor_detections} LEDs")

    # Problematic LEDs
    if problematic_leds:
        print(f"\n⚠ WARNING: {len(problematic_leds)} LED(s) with insufficient detections!")
        print(f"\nThese LEDs may fail triangulation or have poor position accuracy:")
        print()

        for led_idx in problematic_leds:
            stats = led_stats[led_idx]
            successful = stats['successful_detections']
            occluded = stats['occluded_detections']
            total = stats['total_detections']

            print(f"  LED {led_idx:3d}: {successful} successful, {occluded} occluded, {total - successful - occluded} missing")

            if stats['angles_detected']:
                print(f"           Visible from angles: {stats['angles_detected']}")
            if stats['angles_occluded']:
                print(f"           Occluded at angles:  {stats['angles_occluded']}")

            # Show occlusion reasons if available
            for angle_id, detection in stats['detections']:
                if detection['occluded'] and detection.get('notes'):
                    print(f"           Angle {angle_id}: {detection['notes']}")
            print()

        print("Recommendations:")
        print("  1. Review images for these LEDs (if available)")
        print("  2. Consider re-capturing problematic angles")
        print("  3. Ensure LEDs are visible and not blocked")
        print("  4. Check for ambient light interference")
    else:
        print(f"\n✓ All LEDs have sufficient detections ({min_detections}+ angles)")
        print("  Ready for triangulation!")

    # Missing LEDs
    if num_leds > 0:
        max_expected = max(led_stats.keys()) + 1
        missing_leds = [i for i in range(max_expected) if i not in led_stats]

        if missing_leds:
            print(f"\n⚠ WARNING: {len(missing_leds)} LED(s) have NO detections at all:")
            if len(missing_leds) <= 20:
                print(f"  Missing LED indices: {missing_leds}")
            else:
                print(f"  First 20 missing: {missing_leds[:20]}")
                print(f"  (and {len(missing_leds) - 20} more...)")

    print("\n" + "=" * 70)


def main():
    parser = argparse.ArgumentParser(
        description='Check calibration data quality before triangulation',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic check
  python3 check_calibration.py ./calibration_data

  # Check with stricter requirement (5 angles)
  python3 check_calibration.py ./calibration_data --min-detections 5

  # Check and display problematic LED images
  python3 check_calibration.py ./calibration_data --show-images

  # Only show images, no detailed report
  python3 check_calibration.py ./calibration_data --show-images --quiet
        """
    )

    parser.add_argument('calibration_dir',
                       help='Directory containing session_angle_*.json files')
    parser.add_argument('--min-detections', type=int, default=4,
                       help='Minimum successful detections required (default: 4)')
    parser.add_argument('--show-images', action='store_true',
                       help='Display images for problematic LEDs')
    parser.add_argument('--quiet', action='store_true',
                       help='Minimal output, only show problems')

    args = parser.parse_args()

    # Load session data
    if not args.quiet:
        print("Loading calibration sessions...")

    sessions = load_sessions(args.calibration_dir)
    if sessions is None:
        return 1

    # Analyze detections
    if not args.quiet:
        print("\nAnalyzing LED detections...")

    led_stats = analyze_detections(sessions)

    if not led_stats:
        print("ERROR: No LED detection data found")
        return 1

    # Find problematic LEDs
    problematic_leds = find_problematic_leds(led_stats, args.min_detections)

    # Print report
    if not args.quiet:
        print_report(sessions, led_stats, problematic_leds, args.min_detections)
    else:
        if problematic_leds:
            print(f"⚠ {len(problematic_leds)} LED(s) with <{args.min_detections} detections: {problematic_leds[:20]}")
        else:
            print(f"✓ All LEDs have ≥{args.min_detections} detections")

    # Display images if requested
    if args.show_images and problematic_leds:
        angles = sorted(sessions.keys())
        display_led_images(args.calibration_dir, problematic_leds, angles)

    # Return error code if there are problems
    return 1 if problematic_leds else 0


if __name__ == '__main__':
    sys.exit(main())
