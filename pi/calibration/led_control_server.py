#!/usr/bin/env python3
"""
LED Control Server for Calibration

Simple HTTP server that receives commands to light individual LEDs.
Runs on Raspberry Pi during calibration process.
"""

import argparse
import signal
import sys
from flask import Flask, request, jsonify
from rpi_ws281x import PixelStrip, Color
import threading
import time

# LED strip configuration
LED_COUNT = 350          # Number of LED pixels
LED_PIN = 18             # GPIO pin connected to the pixels
LED_FREQ_HZ = 800000     # LED signal frequency in hertz
LED_DMA = 10             # DMA channel to use
LED_BRIGHTNESS = 255     # Full brightness for calibration
LED_INVERT = False       # True to invert the signal
LED_CHANNEL = 0          # Set to '1' for GPIOs 13, 19, 41, 45 or 53

# Global LED strip instance
strip = None
current_led = None
auto_off_timer = None

# Flask app
app = Flask(__name__)


def init_strip():
    """Initialize LED strip."""
    global strip
    strip = PixelStrip(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA,
                      LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL)
    strip.begin()
    all_off()
    print(f"LED strip initialized: {LED_COUNT} LEDs")


def all_off():
    """Turn off all LEDs."""
    global current_led
    if strip:
        for i in range(strip.numPixels()):
            strip.setPixelColor(i, Color(0, 0, 0))
        strip.show()
        current_led = None


def cleanup(signum=None, frame=None):
    """Clean up and turn off all LEDs on exit."""
    print("\nCleaning up...")
    all_off()
    print("LEDs turned off. Exiting.")
    sys.exit(0)


def auto_off_timeout():
    """Automatic timeout to turn off LEDs if no commands received."""
    global auto_off_timer
    if auto_off_timer:
        auto_off_timer.cancel()

    def timeout_handler():
        print("Auto-off timeout triggered")
        all_off()

    auto_off_timer = threading.Timer(60.0, timeout_handler)
    auto_off_timer.daemon = True
    auto_off_timer.start()


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({
        "status": "healthy",
        "led_count": LED_COUNT
    })


@app.route('/status', methods=['GET'])
def status():
    """Get current server status."""
    return jsonify({
        "status": "ready",
        "led_count": LED_COUNT,
        "current_led": current_led
    })


@app.route('/led/on', methods=['POST'])
def led_on():
    """
    Turn on a specific LED.

    Request body:
    {
        "index": 42,
        "color": [255, 255, 255],  # RGB, optional, default white
        "brightness": 255           # 0-255, optional, default 255
    }
    """
    global current_led

    data = request.get_json()

    if not data or 'index' not in data:
        return jsonify({"error": "Missing 'index' in request"}), 400

    led_index = data['index']

    # Validate index
    if not isinstance(led_index, int) or led_index < 0 or led_index >= LED_COUNT:
        return jsonify({"error": f"Invalid LED index: {led_index}"}), 400

    # Get color (default white)
    color = data.get('color', [255, 255, 255])
    if not isinstance(color, list) or len(color) != 3:
        return jsonify({"error": "Color must be [R, G, B] array"}), 400

    r, g, b = color

    # Get brightness (default 255)
    brightness = data.get('brightness', 255)
    if not isinstance(brightness, int) or brightness < 0 or brightness > 255:
        return jsonify({"error": "Brightness must be 0-255"}), 400

    # Apply brightness to color
    r = int(r * brightness / 255)
    g = int(g * brightness / 255)
    b = int(b * brightness / 255)

    # Turn off previous LED
    if current_led is not None and current_led != led_index:
        strip.setPixelColor(current_led, Color(0, 0, 0))

    # Turn on requested LED (note: Color uses GRB order)
    strip.setPixelColor(led_index, Color(g, r, b))
    strip.show()

    current_led = led_index

    # Reset auto-off timer
    auto_off_timeout()

    print(f"LED {led_index} turned on: RGB({r}, {g}, {b})")

    return jsonify({
        "status": "ok",
        "led_index": led_index,
        "color": [r, g, b]
    })


@app.route('/led/off', methods=['POST'])
def led_off():
    """
    Turn off a specific LED.

    Request body:
    {
        "index": 42
    }
    """
    global current_led

    data = request.get_json()

    if not data or 'index' not in data:
        return jsonify({"error": "Missing 'index' in request"}), 400

    led_index = data['index']

    # Validate index
    if not isinstance(led_index, int) or led_index < 0 or led_index >= LED_COUNT:
        return jsonify({"error": f"Invalid LED index: {led_index}"}), 400

    # Turn off LED
    strip.setPixelColor(led_index, Color(0, 0, 0))
    strip.show()

    if current_led == led_index:
        current_led = None

    print(f"LED {led_index} turned off")

    return jsonify({
        "status": "ok",
        "led_index": led_index
    })


@app.route('/led/all_off', methods=['POST'])
def led_all_off():
    """Turn off all LEDs."""
    all_off()
    print("All LEDs turned off")

    return jsonify({
        "status": "ok",
        "count": LED_COUNT
    })


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='LED Control Server for Calibration')
    parser.add_argument('--port', type=int, default=8080,
                       help='HTTP server port (default: 8080)')
    parser.add_argument('--host', type=str, default='0.0.0.0',
                       help='HTTP server host (default: 0.0.0.0)')
    parser.add_argument('--led-count', type=int, default=200,
                       help='Number of LEDs (default: 200)')
    parser.add_argument('--led-pin', type=int, default=18,
                       help='GPIO pin (default: 18)')

    args = parser.parse_args()

    # Update LED configuration from args
    global LED_COUNT, LED_PIN
    LED_COUNT = args.led_count
    LED_PIN = args.led_pin

    # Set up signal handlers for clean exit
    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)

    # Initialize LED strip
    print("Initializing LED strip...")
    init_strip()

    # Start auto-off timer
    auto_off_timeout()

    # Start Flask server
    print(f"\nLED Control Server starting on {args.host}:{args.port}")
    print(f"LED Configuration: {LED_COUNT} LEDs on GPIO {LED_PIN}")
    print("Press Ctrl-C to exit\n")

    try:
        app.run(host=args.host, port=args.port, debug=False, threaded=True)
    finally:
        cleanup()


if __name__ == '__main__':
    main()
