#!/usr/bin/env python3

import time
import numpy as np
from rpi_ws281x import PixelStrip, Color
import signal
import sys

# LED strip configuration:
LED_COUNT = 200          # Number of LED pixels
LED_PIN = 18             # GPIO pin connected to the pixels (must support PWM)
LED_FREQ_HZ = 800000     # LED signal frequency in hertz (usually 800khz)
LED_DMA = 10             # DMA channel to use for generating signal
LED_BRIGHTNESS = 51      # Set to 0 for darkest and 255 for brightest (51 ≈ 0.2 * 255)
LED_INVERT = False       # True to invert the signal
LED_CHANNEL = 0          # Set to '1' for GPIOs 13, 19, 41, 45 or 53

# Create PixelStrip object
strip = PixelStrip(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL)

def cleanup(signum=None, frame=None):
    """Clean up and turn off all LEDs on exit"""
    print("\nCleaning up...")
    for i in range(strip.numPixels()):
        strip.setPixelColor(i, Color(0, 0, 0))
    strip.show()
    print("LEDs turned off. Exiting.")
    sys.exit(0)

def gaussian_white(width, num_pixels, sleep_time):
    """Moving Gaussian envelope with white light"""
    ii = 0
    inds = np.arange(num_pixels)
    
    try:
        while True:
            values = (255 * np.exp(-np.square((inds - ii) % num_pixels) / width)).astype(np.uint8)
            for ind in inds:
                # Convert numpy int to Python int
                strip.setPixelColor(int(ind), Color(int(values[ind]), int(values[ind]), int(values[ind])))
            strip.show()
            ii += 1
            time.sleep(sleep_time)
    except KeyboardInterrupt:
        cleanup()

def gaussian_redgreen(width, num_pixels, sleep_time):
    """Moving Gaussian envelope with red and green lights 180 degrees apart"""
    ii = 0
    inds = np.arange(num_pixels)
    
    try:
        while True:
            values_red = (255 * np.exp(-np.square((inds - ii) % num_pixels) / width)).astype(np.uint8)
            values_green = (255 * np.exp(-np.square((inds - (ii + num_pixels // 2)) % num_pixels) / width)).astype(np.uint8)
            
            for ind in inds:
                # Convert numpy int to Python int
                strip.setPixelColor(int(ind), Color(int(values_red[ind]), int(values_green[ind]), 0))
            strip.show()
            ii += 1
            time.sleep(sleep_time)
    except KeyboardInterrupt:
        cleanup()

def main():
    # Set up signal handlers for clean exit
    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)
    
    # Initialize the library (must be called once before other functions)
    strip.begin()
    
    # Parameters
    width = 500
    sleep_time = 0.00001
    
    print("Starting Gaussian envelope animation...")
    print("Press Ctrl-C to exit")
    
    # Choose which animation to run
    # gaussian_white(width, LED_COUNT, sleep_time)
    gaussian_redgreen(width, LED_COUNT, sleep_time)

if __name__ == '__main__':
    main()
