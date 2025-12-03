#!/usr/bin/env python3
"""
Capture Session Script

Simple CLI tool to cycle through all LEDs and record their 2D positions
from a single camera angle.
"""

import argparse
import json
import time
from pathlib import Path
from datetime import datetime
from typing import List, Optional
import cv2

from pi_control import PiController
from camera_capture import CameraCapture, LEDDetection


class CaptureSession:
    """Manages a single-angle LED capture session."""

    def __init__(
        self,
        pi_ip: str,
        pi_port: int,
        camera_id: int,
        led_count: int,
        output_dir: str,
        angle_id: int = 0,
        save_images: bool = False,
        settle_time: float = 0.1,
        use_settling_check: bool = True,
        led_color: tuple = (255, 0, 0),  # Default: red
        exposure: float = None,  # None = auto, or manual value
        gain: float = None  # None = auto, or manual value
    ):
        self.pi_controller = PiController(pi_ip, pi_port)
        self.camera = CameraCapture(camera_id, exposure=exposure, gain=gain)
        self.led_count = led_count
        self.output_dir = Path(output_dir)
        self.angle_id = angle_id
        self.save_images = save_images
        self.settle_time = settle_time
        self.use_settling_check = use_settling_check
        self.led_color = led_color
        self.detections: List[LEDDetection] = []

        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)
        if self.save_images:
            self.images_dir = self.output_dir / f"images_angle_{angle_id}"
            self.images_dir.mkdir(exist_ok=True)

    def setup(self) -> bool:
        """Initialize Pi connection and camera."""
        print("Setting up capture session...")

        # Connect to Pi
        print(f"Connecting to Pi at {self.pi_controller.pi_ip}:{self.pi_controller.port}...")
        if not self.pi_controller.connect():
            print("Failed to connect to Pi")
            return False
        print("✓ Connected to Pi")

        # Turn off all LEDs
        self.pi_controller.all_off()

        # Open camera
        print(f"Opening camera {self.camera.camera_id}...")
        if not self.camera.open():
            print("Failed to open camera")
            return False
        print("✓ Camera opened")

        # Wait for camera to stabilize
        print("Warming up camera...")
        for _ in range(5):
            self.camera.capture_frame()
            time.sleep(0.1)

        return True

    def wait_for_led_settling(self, num_frames: int = 3, timeout: float = 1.0) -> bool:
        """
        Wait for LED and camera to settle by checking frame stability.

        Args:
            num_frames: Number of consecutive stable frames required
            timeout: Maximum time to wait in seconds

        Returns:
            True if settled, False if timeout
        """
        start_time = time.time()
        prev_brightness = None
        stable_count = 0

        while (time.time() - start_time) < timeout:
            frame = self.camera.capture_frame()
            if frame is None:
                continue

            # Get max brightness in frame
            import cv2
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            current_brightness = gray.max()

            # Check if brightness has stabilized
            if prev_brightness is not None:
                brightness_change = abs(current_brightness - prev_brightness)
                if brightness_change < 5:  # Less than 5 brightness units change
                    stable_count += 1
                    if stable_count >= num_frames:
                        return True
                else:
                    stable_count = 0

            prev_brightness = current_brightness
            time.sleep(0.03)  # 30ms between checks

        return False  # Timeout

    def capture_led(self, led_index: int, preview: bool = False) -> Optional[LEDDetection]:
        """
        Capture and detect a single LED.

        Args:
            led_index: LED index to capture
            preview: If True, show a preview window

        Returns:
            LEDDetection object or None if failed
        """
        # Turn on LED with specified color
        if not self.pi_controller.light_led(led_index, color=self.led_color):
            print(f"Failed to light LED {led_index}")
            return None

        # Wait for LED and camera to settle
        # Fixed minimum delay for network/LED strip
        time.sleep(self.settle_time)

        # Then check for settling (optional, adds ~100-200ms)
        if self.use_settling_check:
            self.wait_for_led_settling(num_frames=3, timeout=0.5)

        # Capture frame
        frame = self.camera.capture_frame()
        if frame is None:
            print(f"Failed to capture frame for LED {led_index}")
            self.pi_controller.turn_off_led(led_index)
            return None

        # Detect LED with color filtering
        # Request debug image if we're saving images and using color filtering
        use_color_filtering = self.led_color != (255, 255, 255)  # Not white
        request_debug = self.save_images and use_color_filtering

        result = self.camera.detect_led(frame, led_index, led_color=self.led_color,
                                        return_debug_image=request_debug)

        # Unpack result
        if request_debug:
            detection, filtered_gray = result
        else:
            detection = result
            filtered_gray = None

        # Save images if requested
        if self.save_images:
            # Always save raw captured image
            image_path = self.images_dir / f"led_{led_index:03d}.jpg"
            cv2.imwrite(str(image_path), frame)

            # If color filtering was used, also save the filtered grayscale image
            if filtered_gray is not None:
                filtered_path = self.images_dir / f"led_{led_index:03d}_filtered.jpg"
                cv2.imwrite(str(filtered_path), filtered_gray)

        # Show preview if requested
        if preview:
            vis_frame = self.camera.visualize_detection(frame, detection)
            cv2.imshow('LED Detection', vis_frame)
            cv2.waitKey(100)  # Brief pause

        # Turn off LED
        self.pi_controller.turn_off_led(led_index)

        return detection

    def run_capture(self, preview: bool = False, start_led: int = 0) -> bool:
        """
        Run full capture session for all LEDs.

        Args:
            preview: Show live preview window
            start_led: Start from this LED index (for resuming)

        Returns:
            True if successful
        """
        print(f"\nStarting capture for angle {self.angle_id}")
        print(f"Capturing LEDs {start_led} to {self.led_count - 1}")
        print(f"Output directory: {self.output_dir}")
        if self.save_images:
            print(f"Saving images to: {self.images_dir}")
        print()

        successful = 0
        occluded = 0
        failed = 0

        for led_index in range(start_led, self.led_count):
            # Progress indicator
            progress = (led_index + 1) / self.led_count * 100
            print(f"[{progress:5.1f}%] LED {led_index:3d}/{self.led_count}... ", end='', flush=True)

            # Capture LED
            detection = self.capture_led(led_index, preview=preview)

            if detection is None:
                print("FAILED")
                failed += 1
                continue

            # Store detection
            self.detections.append(detection)

            # Report result
            if detection.occluded:
                print(f"OCCLUDED ({detection.notes})")
                occluded += 1
            else:
                print(f"OK - px({detection.pixel_x}, {detection.pixel_y}) conf={detection.confidence:.2f}")
                successful += 1

        # Clean up preview window
        if preview:
            cv2.destroyAllWindows()

        # Summary
        print("\n" + "=" * 60)
        print(f"Capture complete!")
        print(f"  Successful:  {successful:3d} / {self.led_count}")
        print(f"  Occluded:    {occluded:3d} / {self.led_count}")
        print(f"  Failed:      {failed:3d} / {self.led_count}")
        print("=" * 60)

        return failed == 0

    def save_session(self, session_name: str, description: str = ""):
        """
        Save session data to JSON file.

        Args:
            session_name: Name for this session
            description: Optional description
        """
        session_data = {
            "version": "0.1.0",
            "session": {
                "name": session_name,
                "date": datetime.now().isoformat(),
                "led_count": self.led_count,
                "angle_id": self.angle_id,
                "description": description,
                "pi_ip": self.pi_controller.pi_ip,
                "camera_id": self.camera.camera_id
            },
            "detections": [
                {
                    "led_index": d.led_index,
                    "pixel_x": d.pixel_x,
                    "pixel_y": d.pixel_y,
                    "brightness": d.brightness,
                    "occluded": d.occluded,
                    "confidence": d.confidence,
                    "notes": d.notes
                }
                for d in self.detections
            ]
        }

        output_file = self.output_dir / f"session_angle_{self.angle_id}.json"
        with open(output_file, 'w') as f:
            json.dump(session_data, f, indent=2)

        print(f"\n✓ Session data saved to: {output_file}")

        # Also save summary
        summary_file = self.output_dir / f"session_angle_{self.angle_id}_summary.txt"
        with open(summary_file, 'w') as f:
            f.write(f"Capture Session Summary\n")
            f.write(f"{'=' * 60}\n\n")
            f.write(f"Session: {session_name}\n")
            f.write(f"Date: {session_data['session']['date']}\n")
            f.write(f"Angle: {self.angle_id}\n")
            f.write(f"LED Count: {self.led_count}\n\n")

            successful = sum(1 for d in self.detections if not d.occluded)
            occluded = sum(1 for d in self.detections if d.occluded)

            f.write(f"Results:\n")
            f.write(f"  Successful: {successful}\n")
            f.write(f"  Occluded: {occluded}\n\n")

            if occluded > 0:
                f.write(f"Occluded LEDs:\n")
                for d in self.detections:
                    if d.occluded:
                        f.write(f"  LED {d.led_index}: {d.notes}\n")

        print(f"✓ Summary saved to: {summary_file}")

    def cleanup(self):
        """Clean up resources."""
        print("\nCleaning up...")
        self.pi_controller.all_off()
        self.camera.close()
        print("✓ Cleanup complete")


def main():
    parser = argparse.ArgumentParser(
        description='Capture LED positions from a single camera angle',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic capture
  python3 capture_session.py 192.168.1.100

  # With preview window
  python3 capture_session.py 192.168.1.100 --preview

  # Save images and use custom camera
  python3 capture_session.py 192.168.1.100 --camera 1 --save-images

  # Resume from LED 50
  python3 capture_session.py 192.168.1.100 --start-led 50
        """
    )

    parser.add_argument('pi_ip', help='IP address of Raspberry Pi')
    parser.add_argument('--pi-port', type=int, default=8080,
                       help='Pi HTTP server port (default: 8080)')
    parser.add_argument('--camera', type=int, default=0,
                       help='Camera device ID (default: 0)')
    parser.add_argument('--led-count', type=int, default=200,
                       help='Number of LEDs (default: 200)')
    parser.add_argument('--angle', type=int, default=0,
                       help='Angle ID for this capture (default: 0)')
    parser.add_argument('--output', type=str, default='./calibration_data',
                       help='Output directory (default: ./calibration_data)')
    parser.add_argument('--name', type=str, default='',
                       help='Session name (default: auto-generated)')
    parser.add_argument('--description', type=str, default='',
                       help='Session description')
    parser.add_argument('--save-images', action='store_true',
                       help='Save captured images')
    parser.add_argument('--preview', action='store_true',
                       help='Show live preview window')
    parser.add_argument('--start-led', type=int, default=0,
                       help='Start from this LED index (for resuming)')
    parser.add_argument('--settle-time', type=float, default=0.1,
                       help='Initial settle time in seconds (default: 0.1)')
    parser.add_argument('--no-settling-check', action='store_true',
                       help='Disable dynamic settling check (faster but less accurate)')
    parser.add_argument('--led-color', type=str, default='red',
                       help='LED color: red, green, blue, white (default: red)')
    parser.add_argument('--exposure', type=float, default=None,
                       help='Manual camera exposure (None for auto). Range varies by camera: '
                            'try -6, 100, or 1000. Check output to see what camera accepts.')
    parser.add_argument('--gain', type=float, default=None,
                       help='Manual camera gain/ISO (None for auto). Usually 0-100 or 0-255. '
                            'Higher gain = brighter image. Use with --exposure for full control.')

    args = parser.parse_args()

    # Parse LED color
    color_map = {
        'red': (255, 0, 0),
        'green': (0, 255, 0),
        'blue': (0, 0, 255),
        'white': (255, 255, 255),
        'r': (255, 0, 0),
        'g': (0, 255, 0),
        'b': (0, 0, 255),
        'w': (255, 255, 255)
    }
    led_color = color_map.get(args.led_color.lower(), (255, 0, 0))

    # Generate session name if not provided
    if not args.name:
        args.name = f"capture_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    print("=" * 60)
    print("LED Position Capture Session")
    print("=" * 60)
    print(f"Pi IP:        {args.pi_ip}:{args.pi_port}")
    print(f"Camera:       {args.camera}")
    print(f"LED Count:    {args.led_count}")
    print(f"Angle ID:     {args.angle}")
    print(f"LED Color:    {args.led_color} {led_color}")
    print(f"Exposure:     {args.exposure if args.exposure is not None else 'Auto'}")
    print(f"Gain:         {args.gain if args.gain is not None else 'Auto'}")
    print(f"Session Name: {args.name}")
    print(f"Output Dir:   {args.output}")
    print("=" * 60)
    print()

    # Create session
    session = CaptureSession(
        pi_ip=args.pi_ip,
        pi_port=args.pi_port,
        camera_id=args.camera,
        led_count=args.led_count,
        output_dir=args.output,
        angle_id=args.angle,
        save_images=args.save_images,
        settle_time=args.settle_time,
        use_settling_check=not args.no_settling_check,
        led_color=led_color,
        exposure=args.exposure,
        gain=args.gain
    )

    try:
        # Setup
        if not session.setup():
            print("\nSetup failed")
            return 1

        input("\nReady to start capture. Press Enter to begin...")

        # Run capture
        success = session.run_capture(
            preview=args.preview,
            start_led=args.start_led
        )

        # Save results
        session.save_session(args.name, args.description)

        return 0 if success else 1

    except KeyboardInterrupt:
        print("\n\n⚠ Capture interrupted by user")
        if len(session.detections) > 0:
            print(f"Captured {len(session.detections)} LEDs so far")
            save = input("Save partial results? (y/n): ")
            if save.lower() == 'y':
                session.save_session(args.name + "_partial", "Interrupted capture")
        return 1

    finally:
        session.cleanup()


if __name__ == '__main__':
    import sys
    sys.exit(main())
