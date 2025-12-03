#!/usr/bin/env python3
"""
Camera Capture Module

Handles camera operations and LED detection in captured images.
"""

import cv2
import numpy as np
from typing import Optional, Tuple
from dataclasses import dataclass


@dataclass
class LEDDetection:
    """Result of LED detection in an image."""
    led_index: int
    pixel_x: int
    pixel_y: int
    brightness: int
    occluded: bool
    confidence: float = 1.0
    notes: str = ""


class CameraCapture:
    """Manages camera and LED detection."""

    def __init__(self, camera_id: int = 0):
        """
        Initialize camera capture.

        Args:
            camera_id: Camera device ID (0 for default webcam)
        """
        self.camera_id = camera_id
        self.cap = None
        self.brightness_threshold = 200
        self.ambiguity_threshold = 100  # Max bright pixels for clear detection

    def open(self) -> bool:
        """
        Open camera device.

        Returns:
            True if camera opened successfully
        """
        self.cap = cv2.VideoCapture(self.camera_id)
        if not self.cap.isOpened():
            print(f"Failed to open camera {self.camera_id}")
            return False

        # Set camera properties for better LED detection
        self.cap.set(cv2.CAP_PROP_AUTOFOCUS, 0)  # Disable autofocus
        self.cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0)  # Disable auto-exposure

        return True

    def close(self):
        """Release camera device."""
        if self.cap:
            self.cap.release()
            self.cap = None

    def capture_frame(self) -> Optional[np.ndarray]:
        """
        Capture a single frame from camera.

        Returns:
            Image as numpy array (H, W, 3) or None if error
        """
        if not self.cap or not self.cap.isOpened():
            print("Camera not opened")
            return None

        ret, frame = self.cap.read()
        if not ret:
            print("Failed to capture frame")
            return None

        return frame

    def detect_led(
        self,
        image: np.ndarray,
        led_index: int,
        led_color: tuple = None,
        return_debug_image: bool = False
    ):
        """
        Detect LED position in captured image.

        Uses brightest pixel method with occlusion checking.
        Optionally filters by LED color to reject ambient light.

        Args:
            image: Input image (H, W, 3) BGR format
            led_index: Index of LED being detected
            led_color: Optional RGB tuple for color filtering (e.g., (255, 0, 0) for red)
            return_debug_image: If True, return tuple of (detection, processed_gray_image)

        Returns:
            LEDDetection object, or tuple of (LEDDetection, gray_image) if return_debug_image=True
        """
        # Apply color filtering if LED color is specified
        if led_color is not None:
            # Convert RGB to BGR for OpenCV
            b, g, r = led_color[2], led_color[1], led_color[0]

            # Extract color channel based on dominant color
            # This helps reject ambient white light
            if r > g and r > b:  # Red LED
                # Red channel minus average of others
                gray = image[:, :, 2].astype(np.float32) - (image[:, :, 0].astype(np.float32) + image[:, :, 1].astype(np.float32)) / 2
                gray = np.clip(gray, 0, 255).astype(np.uint8)
            elif g > r and g > b:  # Green LED
                gray = image[:, :, 1].astype(np.float32) - (image[:, :, 0].astype(np.float32) + image[:, :, 2].astype(np.float32)) / 2
                gray = np.clip(gray, 0, 255).astype(np.uint8)
            elif b > r and b > g:  # Blue LED
                gray = image[:, :, 0].astype(np.float32) - (image[:, :, 1].astype(np.float32) + image[:, :, 2].astype(np.float32)) / 2
                gray = np.clip(gray, 0, 255).astype(np.uint8)
            else:  # White or mixed - use standard grayscale
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            # No color filtering - use standard grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Find maximum brightness
        max_val = gray.max()

        # Check if LED is bright enough
        if max_val < self.brightness_threshold:
            detection = LEDDetection(
                led_index=led_index,
                pixel_x=0,
                pixel_y=0,
                brightness=int(max_val),
                occluded=True,
                confidence=0.0,
                notes="Below brightness threshold"
            )
            return (detection, gray) if return_debug_image else detection

        # Get coordinates of brightest pixel
        y, x = np.unravel_index(gray.argmax(), gray.shape)

        # Check for ambiguity (multiple bright regions)
        bright_mask = gray > (max_val * 0.95)
        bright_pixel_count = bright_mask.sum()

        if bright_pixel_count > self.ambiguity_threshold:
            detection = LEDDetection(
                led_index=led_index,
                pixel_x=int(x),
                pixel_y=int(y),
                brightness=int(max_val),
                occluded=True,
                confidence=0.5,
                notes=f"Ambiguous detection: {bright_pixel_count} bright pixels"
            )
            return (detection, gray) if return_debug_image else detection

        # Calculate confidence based on how isolated the bright spot is
        confidence = 1.0 - (bright_pixel_count / self.ambiguity_threshold)
        confidence = max(0.0, min(1.0, confidence))

        detection = LEDDetection(
            led_index=led_index,
            pixel_x=int(x),
            pixel_y=int(y),
            brightness=int(max_val),
            occluded=False,
            confidence=confidence
        )
        return (detection, gray) if return_debug_image else detection

    def detect_led_enhanced(
        self,
        image: np.ndarray,
        led_index: int,
        background: Optional[np.ndarray] = None
    ) -> LEDDetection:
        """
        Enhanced LED detection with background subtraction.

        Args:
            image: Input image with LED lit
            led_index: Index of LED being detected
            background: Optional background image (no LEDs lit)

        Returns:
            LEDDetection object with results
        """
        # If background provided, subtract it
        if background is not None:
            # Ensure same dtype
            img_float = image.astype(np.float32)
            bg_float = background.astype(np.float32)

            # Subtract and clip
            diff = img_float - bg_float
            diff = np.clip(diff, 0, 255).astype(np.uint8)

            # Use difference for detection
            gray = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
        else:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Apply Gaussian blur to reduce noise
        gray = cv2.GaussianBlur(gray, (5, 5), 0)

        # Continue with standard detection
        max_val = gray.max()

        if max_val < self.brightness_threshold:
            return LEDDetection(
                led_index=led_index,
                pixel_x=0,
                pixel_y=0,
                brightness=int(max_val),
                occluded=True,
                confidence=0.0,
                notes="Below brightness threshold (enhanced)"
            )

        # Find brightest region using blob detection
        _, thresh = cv2.threshold(gray, int(max_val * 0.9), 255, cv2.THRESH_BINARY)

        # Find contours
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if len(contours) == 0:
            y, x = np.unravel_index(gray.argmax(), gray.shape)
            return LEDDetection(
                led_index=led_index,
                pixel_x=int(x),
                pixel_y=int(y),
                brightness=int(max_val),
                occluded=False,
                confidence=0.8
            )

        # Find largest contour
        largest_contour = max(contours, key=cv2.contourArea)

        # Calculate centroid for sub-pixel accuracy
        M = cv2.moments(largest_contour)
        if M["m00"] > 0:
            cx = M["m10"] / M["m00"]
            cy = M["m01"] / M["m00"]
        else:
            y, x = np.unravel_index(gray.argmax(), gray.shape)
            cx, cy = x, y

        # Check for multiple bright regions
        confidence = 1.0 if len(contours) == 1 else 1.0 / len(contours)

        return LEDDetection(
            led_index=led_index,
            pixel_x=int(cx),
            pixel_y=int(cy),
            brightness=int(max_val),
            occluded=False,
            confidence=confidence,
            notes=f"Enhanced detection, {len(contours)} regions"
        )

    def visualize_detection(
        self,
        image: np.ndarray,
        detection: LEDDetection
    ) -> np.ndarray:
        """
        Draw detection result on image for visualization.

        Args:
            image: Input image
            detection: Detection result

        Returns:
            Image with detection visualized
        """
        vis = image.copy()

        if not detection.occluded:
            # Draw crosshair at detected position
            x, y = detection.pixel_x, detection.pixel_y
            color = (0, 255, 0) if detection.confidence > 0.8 else (0, 255, 255)
            cv2.drawMarker(vis, (x, y), color, cv2.MARKER_CROSS, 20, 2)

            # Draw circle
            cv2.circle(vis, (x, y), 10, color, 2)

            # Add text info
            text = f"LED {detection.led_index}: ({x}, {y}) conf={detection.confidence:.2f}"
            cv2.putText(vis, text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        else:
            # Indicate occlusion
            text = f"LED {detection.led_index}: OCCLUDED - {detection.notes}"
            cv2.putText(vis, text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

        return vis


def test_camera(camera_id: int = 0):
    """Test camera capture and display live feed."""
    print(f"Testing camera {camera_id}...")

    camera = CameraCapture(camera_id)

    if not camera.open():
        print("Failed to open camera")
        return

    print("Camera opened successfully")
    print("Press 'q' to quit, 's' to save frame")

    frame_count = 0

    while True:
        frame = camera.capture_frame()
        if frame is None:
            break

        # Display frame
        cv2.imshow('Camera Test', frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('s'):
            filename = f"test_frame_{frame_count:03d}.jpg"
            cv2.imwrite(filename, frame)
            print(f"Saved {filename}")
            frame_count += 1

    camera.close()
    cv2.destroyAllWindows()
    print("Camera test complete")


if __name__ == '__main__':
    import sys

    camera_id = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    test_camera(camera_id)
