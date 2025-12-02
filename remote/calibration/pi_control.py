#!/usr/bin/env python3
"""
Pi Control Module

Handles communication with Raspberry Pi to control individual LEDs
during the calibration process.
"""

import requests
from typing import Optional, Tuple
import time


class PiController:
    """Controls LED lighting on Raspberry Pi via HTTP API."""

    def __init__(self, pi_ip: str, port: int = 8080, timeout: int = 5):
        """
        Initialize Pi controller.

        Args:
            pi_ip: IP address of Raspberry Pi
            port: HTTP server port on Pi
            timeout: Request timeout in seconds
        """
        self.pi_ip = pi_ip
        self.port = port
        self.timeout = timeout
        self.base_url = f"http://{pi_ip}:{port}"
        self._connected = False

    def connect(self) -> bool:
        """
        Test connection to Pi.

        Returns:
            True if Pi is reachable and responding
        """
        try:
            response = requests.get(
                f"{self.base_url}/health",
                timeout=self.timeout
            )
            if response.status_code == 200:
                data = response.json()
                self._connected = data.get("status") == "healthy"
                return self._connected
            return False
        except requests.exceptions.RequestException as e:
            print(f"Connection error: {e}")
            return False

    def light_led(
        self,
        index: int,
        color: Tuple[int, int, int] = (255, 255, 255),
        brightness: int = 255
    ) -> bool:
        """
        Light up a specific LED.

        Args:
            index: LED index (0-based)
            color: RGB color tuple (0-255 each)
            brightness: Overall brightness (0-255)

        Returns:
            True if successful
        """
        try:
            response = requests.post(
                f"{self.base_url}/led/on",
                json={
                    "index": index,
                    "color": list(color),
                    "brightness": brightness
                },
                timeout=self.timeout
            )
            return response.status_code == 200
        except requests.exceptions.RequestException as e:
            print(f"Error lighting LED {index}: {e}")
            return False

    def turn_off_led(self, index: int) -> bool:
        """
        Turn off a specific LED.

        Args:
            index: LED index (0-based)

        Returns:
            True if successful
        """
        try:
            response = requests.post(
                f"{self.base_url}/led/off",
                json={"index": index},
                timeout=self.timeout
            )
            return response.status_code == 200
        except requests.exceptions.RequestException as e:
            print(f"Error turning off LED {index}: {e}")
            return False

    def all_off(self) -> bool:
        """
        Turn off all LEDs.

        Returns:
            True if successful
        """
        try:
            response = requests.post(
                f"{self.base_url}/led/all_off",
                timeout=self.timeout
            )
            return response.status_code == 200
        except requests.exceptions.RequestException as e:
            print(f"Error turning off all LEDs: {e}")
            return False

    def get_status(self) -> Optional[dict]:
        """
        Get current Pi status.

        Returns:
            Status dictionary or None if error
        """
        try:
            response = requests.get(
                f"{self.base_url}/status",
                timeout=self.timeout
            )
            if response.status_code == 200:
                return response.json()
            return None
        except requests.exceptions.RequestException as e:
            print(f"Error getting status: {e}")
            return None

    @property
    def is_connected(self) -> bool:
        """Check if controller is connected."""
        return self._connected


def test_connection(pi_ip: str, port: int = 8080):
    """Test Pi connection and basic LED control."""
    print(f"Testing connection to {pi_ip}:{port}...")

    controller = PiController(pi_ip, port)

    # Test connection
    if not controller.connect():
        print("❌ Failed to connect to Pi")
        return False

    print("✓ Connected to Pi")

    # Get status
    status = controller.get_status()
    if status:
        print(f"✓ Pi Status: {status}")
    else:
        print("⚠ Could not get Pi status")

    # Test LED control
    print("\nTesting LED control (LED 0)...")

    # Turn on
    if controller.light_led(0, color=(255, 0, 0)):
        print("✓ LED 0 turned on (red)")
        time.sleep(1)
    else:
        print("❌ Failed to turn on LED 0")
        return False

    # Turn off
    if controller.turn_off_led(0):
        print("✓ LED 0 turned off")
    else:
        print("❌ Failed to turn off LED 0")
        return False

    # All off
    if controller.all_off():
        print("✓ All LEDs turned off")
    else:
        print("❌ Failed to turn off all LEDs")

    print("\n✓ All tests passed!")
    return True


if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        print("Usage: python3 pi_control.py <pi_ip_address> [port]")
        print("Example: python3 pi_control.py 192.168.1.100 8080")
        sys.exit(1)

    pi_ip = sys.argv[1]
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 8080

    test_connection(pi_ip, port)
