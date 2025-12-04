#!/usr/bin/env python3
"""
Triangulation Module

Converts 2D LED detections from multiple camera angles into 3D positions.
Uses a simplified triangulation approach without full camera calibration.
"""

import json
import argparse
import numpy as np
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass

# Optional matplotlib for visualization
try:
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d import Axes3D
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False


@dataclass
class Detection2D:
    """2D detection from a single camera angle."""
    led_index: int
    angle_id: int
    pixel_x: float
    pixel_y: float
    occluded: bool
    confidence: float


@dataclass
class Position3D:
    """3D position of an LED."""
    led_index: int
    x: float
    y: float
    z: float
    confidence: float
    num_views: int
    detections: List[Detection2D]


class SimplifiedTriangulator:
    """
    Simplified triangulation without camera calibration.

    Assumes:
    - Cameras are positioned at equal distances around the tree
    - Tree is roughly centered at origin
    - Z-axis is vertical (up)
    - X-Y plane is horizontal
    - Cameras look toward center from their angle
    """

    def __init__(
        self,
        camera_distance: float = 2.0,
        image_width: int = 640,
        image_height: int = 480,
        fov_horizontal: float = 60.0
    ):
        """
        Initialize triangulator.

        Args:
            camera_distance: Distance from camera to tree center (meters)
            image_width: Camera image width in pixels
            image_height: Camera image height in pixels
            fov_horizontal: Camera horizontal field of view (degrees)
        """
        self.camera_distance = camera_distance
        self.image_width = image_width
        self.image_height = image_height
        self.fov_horizontal = np.deg2rad(fov_horizontal)

        # Calculate focal length from FOV
        self.focal_length = (image_width / 2.0) / np.tan(self.fov_horizontal / 2.0)

    def pixel_to_ray(
        self,
        pixel_x: float,
        pixel_y: float,
        camera_angle: float
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Convert pixel coordinates to 3D ray.

        Args:
            pixel_x: X pixel coordinate
            pixel_y: Y pixel coordinate
            camera_angle: Camera angle in degrees (0, 90, 180, 270)

        Returns:
            ray_origin: 3D point where ray starts (camera position)
            ray_direction: 3D normalized direction vector
        """
        # Convert camera angle to radians
        angle_rad = np.deg2rad(camera_angle)

        # Camera position in X-Y plane (horizontal), looking at origin
        # Z=0 is ground level (cameras at same height)
        camera_pos = np.array([
            self.camera_distance * np.cos(angle_rad),
            self.camera_distance * np.sin(angle_rad),
            0.0  # All cameras at ground level (Z=0)
        ])

        # Convert pixel to normalized image coordinates (-1 to 1)
        # Center of image is (image_width/2, image_height/2)
        norm_x = (pixel_x - self.image_width / 2.0) / (self.image_width / 2.0)
        norm_y = -(pixel_y - self.image_height / 2.0) / (self.image_height / 2.0)  # Flip Y

        # Calculate ray direction in camera space
        # Camera looks toward origin, with local coordinates:
        #   local +X is right, local +Y is up, local -Z is forward
        ray_camera = np.array([
            norm_x * np.tan(self.fov_horizontal / 2.0),
            norm_y * np.tan(self.fov_horizontal / 2.0) * (self.image_height / self.image_width),
            -1.0  # Camera looks in -Z direction in its local space
        ])
        ray_camera = ray_camera / np.linalg.norm(ray_camera)

        # Rotate ray to world space
        # World: X-Y plane is horizontal, Z is up
        # Camera rotates around Z axis by angle θ
        cos_a = np.cos(angle_rad)
        sin_a = np.sin(angle_rad)

        # Rotation matrix to transform camera local coordinates to world coordinates
        # Camera at angle θ around Z axis has:
        #   local +X (right) -> world (-sin(θ), cos(θ), 0)
        #   local +Y (up) -> world (0, 0, 1)
        #   local -Z (forward toward origin) -> world (-cos(θ), -sin(θ), 0)
        ray_world = np.array([
            -ray_camera[0] * sin_a + ray_camera[2] * cos_a,
            ray_camera[0] * cos_a + ray_camera[2] * sin_a,
            ray_camera[1]
        ])
        ray_world = ray_world / np.linalg.norm(ray_world)

        return camera_pos, ray_world

    def triangulate_rays(
        self,
        rays: List[Tuple[np.ndarray, np.ndarray]]
    ) -> Tuple[np.ndarray, float]:
        """
        Find best 3D point that minimizes distance to all rays.

        Uses least-squares method to find point closest to all rays.

        Args:
            rays: List of (origin, direction) tuples

        Returns:
            position: 3D position
            residual: Average distance from point to rays (quality metric)
        """
        if len(rays) < 2:
            return np.array([0.0, 0.0, 0.0]), float('inf')

        # Solve using least squares
        # For each ray: point = origin + t * direction
        # Find point P that minimizes distance to all rays

        A = []
        b = []

        for origin, direction in rays:
            # For each ray, add constraints
            # (I - d*d^T) * P = (I - d*d^T) * origin
            # where d is the direction unit vector
            I = np.eye(3)
            ddT = np.outer(direction, direction)
            A_i = I - ddT
            b_i = A_i @ origin

            A.append(A_i)
            b.append(b_i)

        A = np.vstack(A)
        b = np.concatenate(b)

        # Solve least squares
        try:
            position, residuals, rank, s = np.linalg.lstsq(A, b, rcond=None)
            residual = np.sqrt(residuals[0] / len(rays)) if len(residuals) > 0 else 0.0
        except np.linalg.LinAlgError:
            position = np.array([0.0, 0.0, 0.0])
            residual = float('inf')

        return position, residual

    def triangulate_led(
        self,
        detections: List[Detection2D]
    ) -> Optional[Position3D]:
        """
        Triangulate 3D position from multiple 2D detections.

        Args:
            detections: List of 2D detections from different angles

        Returns:
            Position3D object or None if insufficient data
        """
        # Filter out occluded detections
        valid_detections = [d for d in detections if not d.occluded]

        if len(valid_detections) < 2:
            return None

        # Convert detections to rays
        rays = []
        for det in valid_detections:
            origin, direction = self.pixel_to_ray(
                det.pixel_x,
                det.pixel_y,
                det.angle_id
            )
            rays.append((origin, direction))

        # Triangulate
        position, residual = self.triangulate_rays(rays)

        # Calculate confidence based on number of views and residual
        confidence = len(valid_detections) / len(detections)
        confidence *= np.exp(-residual)  # Reduce confidence for high residual

        return Position3D(
            led_index=detections[0].led_index if detections else -1,
            x=float(position[0]),
            y=float(position[1]),
            z=float(position[2]),
            confidence=float(confidence),
            num_views=len(valid_detections),
            detections=detections
        )

    def visualize_led_triangulation(
        self,
        detections: List[Detection2D],
        position: Optional[Position3D] = None
    ):
        """
        Visualize the triangulation process for a single LED.

        Shows camera positions, rays from each detection, and the estimated 3D position.

        Args:
            detections: List of 2D detections from different angles
            position: Optional pre-calculated Position3D (will calculate if not provided)
        """
        if not HAS_MATPLOTLIB:
            print("ERROR: Visualization requires matplotlib")
            print("Install with: pip3 install matplotlib")
            return

        # Calculate position if not provided
        if position is None:
            position = self.triangulate_led(detections)
            if position is None:
                print("ERROR: Insufficient detections for triangulation")
                return

        # Filter to valid detections only
        valid_detections = [d for d in detections if not d.occluded]

        # Create figure
        fig = plt.figure(figsize=(12, 10))
        ax = fig.add_subplot(111, projection='3d')

        # Plot camera positions and rays
        camera_positions = []
        ray_colors = ['red', 'blue', 'green', 'purple', 'orange', 'cyan', 'magenta', 'yellow']

        for i, det in enumerate(valid_detections):
            # Get ray
            origin, direction = self.pixel_to_ray(
                det.pixel_x,
                det.pixel_y,
                det.angle_id
            )

            camera_positions.append(origin)

            # Plot camera position
            color = ray_colors[i % len(ray_colors)]
            ax.scatter(origin[0], origin[1], origin[2],
                      c=color, marker='o', s=200,
                      label=f'Camera angle {det.angle_id}°', alpha=0.8)

            # Plot ray from camera toward LED
            # Extend ray to go past the estimated position
            ray_length = np.linalg.norm(position.x - origin[0]) * 1.5
            ray_end = origin + direction * ray_length

            ax.plot([origin[0], ray_end[0]],
                   [origin[1], ray_end[1]],
                   [origin[2], ray_end[2]],
                   color=color, linewidth=2, alpha=0.6)

        # Plot estimated LED position
        ax.scatter(position.x, position.y, position.z,
                  c='yellow', marker='*', s=500,
                  edgecolors='black', linewidths=2,
                  label=f'LED {position.led_index} (estimated)', zorder=100)

        # Plot origin
        ax.scatter(0, 0, 0, c='gray', marker='x', s=100, label='Origin')

        # Calculate and display residual for each ray
        for i, det in enumerate(valid_detections):
            origin, direction = self.pixel_to_ray(det.pixel_x, det.pixel_y, det.angle_id)
            led_pos = np.array([position.x, position.y, position.z])

            # Distance from LED to ray
            to_led = led_pos - origin
            projection = np.dot(to_led, direction)
            closest_point = origin + projection * direction
            distance = np.linalg.norm(led_pos - closest_point)

            print(f"  Angle {det.angle_id:3d}°: ray distance = {distance:.4f}m")

        # Set labels and title
        ax.set_xlabel('X (meters)')
        ax.set_ylabel('Y (meters)')
        ax.set_zlabel('Z (meters, up)')
        ax.set_title(f'LED {position.led_index} Triangulation\n'
                    f'Position: ({position.x:.3f}, {position.y:.3f}, {position.z:.3f})\n'
                    f'Confidence: {position.confidence:.3f} | Views: {position.num_views}')

        # Set equal aspect ratio
        camera_pos_array = np.array(camera_positions)
        all_points = np.vstack([camera_pos_array, [[position.x, position.y, position.z]]])

        max_range = np.abs(all_points).max()
        ax.set_xlim([-max_range, max_range])
        ax.set_ylim([-max_range, max_range])
        ax.set_zlim([-max_range, max_range])

        ax.legend(loc='upper left', fontsize=8)

        # Add grid
        ax.grid(True, alpha=0.3)

        plt.tight_layout()
        plt.show()


class TriangulationProcessor:
    """Process multiple capture sessions and triangulate all LEDs."""

    def __init__(self, calibration_dir: Path):
        """
        Initialize processor.

        Args:
            calibration_dir: Directory containing session JSON files
        """
        self.calibration_dir = Path(calibration_dir)
        self.sessions = {}
        self.led_count = 0

    def load_sessions(self):
        """Load all session JSON files from calibration directory."""
        session_files = sorted(self.calibration_dir.glob("session_angle_*.json"))

        if not session_files:
            raise FileNotFoundError(f"No session files found in {self.calibration_dir}")

        print(f"Loading {len(session_files)} session files...")

        for session_file in session_files:
            with open(session_file, 'r') as f:
                data = json.load(f)

            angle_id = data['session']['angle_id']
            self.sessions[angle_id] = data

            # Update LED count
            if data['session']['led_count'] > self.led_count:
                self.led_count = data['session']['led_count']

            print(f"  Loaded angle {angle_id}: {len(data['detections'])} detections")

        print(f"Total angles: {len(self.sessions)}")
        print(f"LED count: {self.led_count}")

    def build_detection_map(self) -> Dict[int, List[Detection2D]]:
        """
        Build map of LED index to list of detections from all angles.

        Returns:
            Dictionary mapping LED index to list of Detection2D objects
        """
        detection_map = {}

        for angle_id, session_data in self.sessions.items():
            for det_data in session_data['detections']:
                led_idx = det_data['led_index']

                detection = Detection2D(
                    led_index=led_idx,
                    angle_id=angle_id,
                    pixel_x=det_data['pixel_x'],
                    pixel_y=det_data['pixel_y'],
                    occluded=det_data['occluded'],
                    confidence=det_data.get('confidence', 1.0)
                )

                if led_idx not in detection_map:
                    detection_map[led_idx] = []

                detection_map[led_idx].append(detection)

        return detection_map

    def triangulate_all(
        self,
        triangulator: SimplifiedTriangulator,
        visualize_leds: Optional[List[int]] = None
    ) -> List[Position3D]:
        """
        Triangulate all LEDs.

        Args:
            triangulator: Triangulator instance
            visualize_leds: Optional list of LED indices to visualize

        Returns:
            List of Position3D objects
        """
        detection_map = self.build_detection_map()

        positions = []
        failed_count = 0

        print(f"\nTriangulating {len(detection_map)} LEDs...")

        for led_idx in sorted(detection_map.keys()):
            detections = detection_map[led_idx]

            position = triangulator.triangulate_led(detections)

            if position is not None:
                position.led_index = led_idx
                positions.append(position)

                # Visualize if requested
                if visualize_leds is not None and led_idx in visualize_leds:
                    print(f"\nVisualizing LED {led_idx}:")
                    triangulator.visualize_led_triangulation(detections, position)
            else:
                failed_count += 1
                print(f"  Warning: LED {led_idx} failed triangulation (insufficient views)")

        print(f"Successfully triangulated: {len(positions)}/{len(detection_map)}")
        print(f"Failed: {failed_count}")

        return positions

    def export_position_map(
        self,
        positions: List[Position3D],
        output_file: Path,
        name: str = "Calibrated Tree"
    ):
        """
        Export positions to position map JSON format.

        Normalizes coordinates:
        - Height (Z range) = 1.0
        - Z axis centered at 0
        - X and Y axes centered on median values

        Args:
            positions: List of Position3D objects
            output_file: Output file path
            name: Name for this position map
        """
        from datetime import date

        # Sort by LED index
        positions = sorted(positions, key=lambda p: p.led_index)

        # Calculate normalization parameters
        if positions:
            # Get all positions as arrays
            x_vals = np.array([p.x for p in positions])
            y_vals = np.array([p.y for p in positions])
            z_vals = np.array([p.z for p in positions])

            # Calculate centering offsets
            median_x = np.median(x_vals)
            median_y = np.median(y_vals)
            z_min = z_vals.min()
            z_max = z_vals.max()
            z_center = (z_min + z_max) / 2.0
            z_range = z_max - z_min

            # Avoid division by zero
            if z_range < 1e-6:
                z_range = 1.0

            print(f"\nNormalizing coordinates:")
            print(f"  X offset (median):  {median_x:.3f} m")
            print(f"  Y offset (median):  {median_y:.3f} m")
            print(f"  Z offset (center):  {z_center:.3f} m")
            print(f"  Scale factor (1/height): {1.0/z_range:.3f}")
            print(f"  Original height: {z_range:.3f} m")

            # Normalize all positions
            for pos in positions:
                pos.x = (pos.x - median_x) / z_range
                pos.y = (pos.y - median_y) / z_range
                pos.z = (pos.z - z_center) / z_range

            print(f"\nNormalized ranges:")
            x_vals_norm = np.array([p.x for p in positions])
            y_vals_norm = np.array([p.y for p in positions])
            z_vals_norm = np.array([p.z for p in positions])
            print(f"  X: [{x_vals_norm.min():.3f}, {x_vals_norm.max():.3f}]")
            print(f"  Y: [{y_vals_norm.min():.3f}, {y_vals_norm.max():.3f}]")
            print(f"  Z: [{z_vals_norm.min():.3f}, {z_vals_norm.max():.3f}] (height = {z_vals_norm.max() - z_vals_norm.min():.3f})")
        else:
            median_x = median_y = z_center = 0.0
            z_range = 1.0

        # Find the maximum LED index to determine array size
        if positions:
            max_led_idx = max(p.led_index for p in positions)
            actual_led_count = max_led_idx + 1
        else:
            actual_led_count = 0

        # Create position lookup
        position_dict = {p.led_index: p for p in positions}

        # Build position map with proper index alignment
        # Use [0, 0, 0] for LEDs that failed triangulation
        position_array = []
        missing_leds = []

        for led_idx in range(actual_led_count):
            if led_idx in position_dict:
                pos = position_dict[led_idx]
                position_array.append([pos.x, pos.y, pos.z])
            else:
                position_array.append([0.0, 0.0, 0.0])
                missing_leds.append(led_idx)

        # Build position map
        position_map = {
            "version": "0.1.0",
            "metadata": {
                "name": name,
                "led_count": actual_led_count,
                "created": str(date.today()),
                "units": "normalized",
                "coordinate_system": "X-Y horizontal, Z vertical (up)",
                "normalization": {
                    "height": 1.0,
                    "x_centered_on": "median",
                    "y_centered_on": "median",
                    "z_centered_on": "vertical_center",
                    "original_height_meters": float(z_range),
                    "scale_factor": float(1.0 / z_range)
                },
                "origin": "centered (median X, median Y, vertical center Z)",
                "method": "simplified_triangulation",
                "num_angles": len(self.sessions),
                "angles": sorted(self.sessions.keys()),
                "successful_leds": len(positions),
                "failed_leds": len(missing_leds)
            },
            "positions": position_array
        }

        if missing_leds:
            position_map["metadata"]["missing_led_indices"] = missing_leds[:20]  # First 20
            if len(missing_leds) > 20:
                position_map["metadata"]["missing_led_count_truncated"] = True

        # Save to file
        with open(output_file, 'w') as f:
            json.dump(position_map, f, indent=2)

        print(f"\n✓ Position map saved to: {output_file}")

        if missing_leds:
            print(f"⚠ Warning: {len(missing_leds)} LEDs have placeholder positions [0,0,0]")
            print(f"   These LEDs failed triangulation (occluded or insufficient views)")
            if len(missing_leds) <= 10:
                print(f"   Missing LED indices: {missing_leds}")
            else:
                print(f"   First 10 missing: {missing_leds[:10]}")

        # Also save detailed version with confidence scores
        detailed_file = output_file.with_suffix('.detailed.json')
        detailed_map = position_map.copy()
        detailed_map["positions"] = [
            {
                "id": pos.led_index,
                "x": pos.x,
                "y": pos.y,
                "z": pos.z,
                "confidence": pos.confidence,
                "num_views": pos.num_views
            }
            for pos in positions
        ]

        with open(detailed_file, 'w') as f:
            json.dump(detailed_map, f, indent=2)

        print(f"✓ Detailed map saved to: {detailed_file}")


def main():
    parser = argparse.ArgumentParser(
        description='Triangulate 3D positions from multiple 2D capture sessions',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage
  python3 triangulation.py ./calibration_data

  # Specify output file and camera parameters
  python3 triangulation.py ./calibration_data \\
    --output ./tree_positions.json \\
    --name "Main Tree 2024" \\
    --camera-distance 2.5 \\
    --fov 70

  # Adjust for different image resolution
  python3 triangulation.py ./calibration_data \\
    --image-width 1920 \\
    --image-height 1080

  # Visualize specific LEDs during triangulation
  python3 triangulation.py ./calibration_data --visualize-led 0 50 100
        """
    )

    parser.add_argument('calibration_dir',
                       help='Directory containing session_angle_*.json files')
    parser.add_argument('--output', type=str,
                       default='position-maps/position_map.json',
                       help='Output position map file (default: position-maps/position_map.json)')
    parser.add_argument('--name', type=str,
                       default='Calibrated Tree',
                       help='Name for position map (default: "Calibrated Tree")')
    parser.add_argument('--camera-distance', type=float,
                       default=2.0,
                       help='Distance from camera to tree center in meters (default: 2.0)')
    parser.add_argument('--image-width', type=int,
                       default=640,
                       help='Camera image width in pixels (default: 640)')
    parser.add_argument('--image-height', type=int,
                       default=480,
                       help='Camera image height in pixels (default: 480)')
    parser.add_argument('--fov', type=float,
                       default=60.0,
                       help='Camera horizontal field of view in degrees (default: 60)')
    parser.add_argument('--visualize-led', type=int, nargs='+',
                       help='Visualize triangulation for specific LED index(es). '
                            'Shows camera positions, rays, and estimated 3D position. '
                            'Example: --visualize-led 0 50 100')

    args = parser.parse_args()

    print("=" * 60)
    print("3D Position Triangulation")
    print("=" * 60)
    print(f"Calibration dir: {args.calibration_dir}")
    print(f"Output file:     {args.output}")
    print(f"Camera distance: {args.camera_distance}m")
    print(f"Image size:      {args.image_width}x{args.image_height}")
    print(f"FOV:             {args.fov}°")
    if args.visualize_led:
        print(f"Visualize LEDs:  {args.visualize_led}")
    print("=" * 60)

    # Check matplotlib if visualization requested
    if args.visualize_led and not HAS_MATPLOTLIB:
        print("\nERROR: Visualization requires matplotlib")
        print("Install with: pip3 install matplotlib")
        return 1

    # Load sessions
    processor = TriangulationProcessor(args.calibration_dir)
    processor.load_sessions()

    # Create triangulator
    triangulator = SimplifiedTriangulator(
        camera_distance=args.camera_distance,
        image_width=args.image_width,
        image_height=args.image_height,
        fov_horizontal=args.fov
    )

    # Triangulate all LEDs
    positions = processor.triangulate_all(triangulator, visualize_leds=args.visualize_led)

    # Print statistics (before normalization)
    if positions:
        positions_arr = np.array([[p.x, p.y, p.z] for p in positions])
        print("\nRaw Position Statistics (meters):")
        print(f"  X range: [{positions_arr[:, 0].min():.3f}, {positions_arr[:, 0].max():.3f}] m")
        print(f"  Y range: [{positions_arr[:, 1].min():.3f}, {positions_arr[:, 1].max():.3f}] m")
        print(f"  Z range: [{positions_arr[:, 2].min():.3f}, {positions_arr[:, 2].max():.3f}] m (height)")

        confidences = [p.confidence for p in positions]
        print(f"\nConfidence Statistics:")
        print(f"  Mean: {np.mean(confidences):.3f}")
        print(f"  Min:  {np.min(confidences):.3f}")
        print(f"  Max:  {np.max(confidences):.3f}")

    # Export
    output_path = Path(args.output)
    processor.export_position_map(positions, output_path, args.name)

    print("\n✓ Triangulation complete!")
    print(f"\nNext steps:")
    print(f"  1. Visualize: python3 visualize_positions.py {output_path}")
    print(f"  2. Copy to GIFT: cp {output_path} ../../pi/GIFT/position_maps/")


if __name__ == '__main__':
    main()
