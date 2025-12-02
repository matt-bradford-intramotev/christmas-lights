# Christmas Lights Controller

A comprehensive toolkit for controlling individually addressable LED lights on a Raspberry Pi Zero 2 W, with a focus on 3D spatial light animations for Christmas tree displays.

## Overview

This project provides tools for creating and controlling LED light patterns on WS281x-compatible LED strips. It includes both standalone animation scripts and GIFT (Geometric Interactive Format for Trees), a file-based system for creating complex 3D light shows.

## Hardware

- **Controller**: Raspberry Pi Zero 2 W
- **LEDs**: Individually addressable LED strips (WS281x compatible)
- **Target Setup**: 200 LEDs arranged on a Christmas tree with 3D position mapping

## Project Structure

```
christmas-lights/
├── pi/                      # Tools that run on the Raspberry Pi
│   ├── standalone/          # Individual pattern scripts
│   │   ├── gaussian-envelope-2.py
│   │   └── led_test.py
│   └── GIFT/                # GIFT system components
│       └── (to be implemented)
├── remote/                  # Remote control tools
│   └── (to be implemented)
└── docs/                    # Documentation and specifications
    └── (to be added)
```

## Components

### Standalone Scripts

Located in [pi/standalone/](pi/standalone/), these are individual Python scripts that run self-contained light patterns directly on the Raspberry Pi. Each script can be executed independently to produce a specific visual effect.

**Examples:**
- `gaussian-envelope-2.py` - Moving Gaussian envelope with various color schemes
- `led_test.py` - Basic LED strip testing utility

### GIFT (Geometric Interactive Format for Trees)

A file-based system for creating sophisticated 3D light animations. GIFT is designed to work with spatial mappings of LED positions.

**Key Features:**
- 3D position mapping of each LED in physical space
- `.GIFT` file format for defining timing and position-based animations
- Python class for parsing and executing `.GIFT` files
- Visualization tool for creating and previewing `.GIFT` files

**Status**: To be implemented

### Remote Control Tools

Located in [remote/](remote/), these tools run on a separate machine and allow remote control and management of the LED displays on the Raspberry Pi.

**Status**: To be implemented

## Getting Started

### Prerequisites

**On Raspberry Pi:**
- Python 3.7+
- `rpi-ws281x` library for LED control
- NumPy for mathematical operations

### Running Standalone Scripts

```bash
# On the Raspberry Pi
cd pi/standalone
sudo python3 gaussian-envelope-2.py
```

Note: `sudo` is required for GPIO access on the Raspberry Pi.

### Using GIFT (Coming Soon)

```bash
# Example usage (to be implemented)
cd pi/GIFT
sudo python3 gift_player.py animations/sparkle.gift
```

## Development Roadmap

### Phase 1: Core Infrastructure
- [x] Basic standalone pattern scripts
- [ ] 3D position mapping system
- [ ] GIFT file format specification
- [ ] GIFT parser and player class

### Phase 2: GIFT System
- [ ] Visualization tool for .GIFT creation
- [ ] Library of basic .GIFT animations
- [ ] Position calibration utilities

### Phase 3: Remote Control
- [ ] Remote control interface
- [ ] Network communication protocol
- [ ] Web-based control panel (optional)

### Phase 4: Advanced Features
- [ ] Sound-reactive patterns
- [ ] Multiple simultaneous animations
- [ ] Animation blending and transitions
- [ ] Performance optimization

## GIFT File Format

The `.GIFT` file format is designed to describe light animations in 3D space. Each file contains:

1. **Metadata**: Animation name, duration, frame rate
2. **Position Data**: Reference to or embedded 3D coordinates of each LED
3. **Animation Frames**: Timing and color/brightness data for each LED at each keyframe
4. **Interpolation Rules**: How to transition between keyframes

Detailed specification to be documented in [docs/](docs/).

## Contributing

When contributing to this project:
- Follow existing code style conventions
- Test on actual hardware when possible
- Document any new .GIFT file format features
- Include example animations with new features

## License

To be determined

## Safety Notes

- LED strips can draw significant current; ensure adequate power supply
- Use appropriate voltage levels for your LED strip
- The Raspberry Pi GPIO pins have current limitations
- Always test new patterns at low brightness first
- Be cautious with very fast update rates to avoid overheating

## Resources

- [rpi_ws281x Library](https://github.com/jgarff/rpi_ws281x)
- [WS281x LED Protocol](https://cdn-shop.adafruit.com/datasheets/WS2812B.pdf)
- Raspberry Pi GPIO pinout and PWM capabilities
