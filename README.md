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
├── pi/                          # Tools that run on the Raspberry Pi
│   ├── standalone/              # Individual pattern scripts
│   │   ├── gaussian-envelope-2.py
│   │   └── led_test.py
│   ├── GIFT/                    # GIFT playback system
│   │   ├── gift_player.py       # Animation player for hardware
│   │   ├── gifts/               # GIFT animation files (.gift)
│   │   └── position_maps/       # LED position maps (JSON)
│   └── calibration/             # Calibration server for position mapping
│       └── led_control_server.py
├── remote/                      # Remote development tools
│   ├── calibration/             # Camera-based position mapping
│   │   ├── position-maps/       # Calibrated position maps
│   │   ├── triangulation.py     # 3D position calculation
│   │   ├── camera_capture.py    # Image capture and LED detection
│   │   └── pi_control.py        # HTTP client for Pi control
│   └── gift-generation/         # GIFT animation creation
│       ├── gift_creator.py      # Animation builder library
│       ├── simulate_gift.py     # 3D visualization and preview
│       └── example_rainbow_bands.py
└── docs/                        # Documentation and specifications
    ├── GIFT_FORMAT_SPEC.md      # GIFT file format specification
    ├── CALIBRATION_SYSTEM.md    # Position mapping system
    └── DEVELOPMENT_PLAN.md      # Project roadmap
```

## Components

### Standalone Scripts

Located in [pi/standalone/](pi/standalone/), these are individual Python scripts that run self-contained light patterns directly on the Raspberry Pi. Each script can be executed independently to produce a specific visual effect.

**Examples:**
- `gaussian-envelope.py` - Moving Gaussian envelope with various color schemes
- `led_test.py` - Basic LED strip testing utility

### GIFT (Geometric Interactive Format for Trees)

A frame-based animation system for creating sophisticated 3D light shows. GIFT separates animation generation (which uses 3D position data) from playback (which just displays pre-rendered frames).

**How It Works:**
1. **Calibration**: Camera-based system maps each LED's 3D position in space
2. **Generation**: Create animations using position data (on development machine)
3. **Simulation**: Preview animations in 3D before deployment
4. **Playback**: Play pre-rendered animations on the Raspberry Pi

**File Format:**
- Simple CSV format: `frame_id, R_1, G_1, B_1, R_2, G_2, B_2, ...`
- Metadata header: LED count, framerate, duration, loop setting
- Position maps separate from animation files (used during generation only)
- No runtime calculations needed for playback

**Key Features:**
- Camera-based 3D position calibration
- Position-aware animation generation
- Interactive 3D preview and simulation
- Simple, efficient playback on Pi Zero 2 W
- Automatic handling of unmapped/failed LEDs

### Remote Control Tools

Located in [remote/](remote/), these tools run on a separate machine to create and manage animations:

**Calibration Tools:**
- Camera-based LED position detection
- Multi-angle triangulation for 3D mapping
- Position map validation and visualization

**Animation Tools:**
- GIFT animation creation with position awareness
- 3D preview and simulation
- Example animation generators

## Getting Started

### Prerequisites

**On Raspberry Pi:**
- Python 3.7+
- `rpi-ws281x` library for LED control
- NumPy for mathematical operations
- Flask (for calibration server)

**On Development Machine (for GIFT creation):**
- Python 3.7+
- NumPy, matplotlib (for visualization)
- OpenCV (for calibration)
- Requests (for Pi communication)

### Running Standalone Scripts

```bash
# On the Raspberry Pi
cd pi/standalone
sudo python3 gaussian-envelope-2.py
```

Note: `sudo` is required for GPIO access on the Raspberry Pi.

### Using GIFT

**On Development Machine:**

```bash
# 1. Calibrate LED positions (one-time setup)
cd remote/calibration
python3 triangulation.py ./calibration_data --output position-maps/tree.json

# 2. Create animation
cd ../gift-generation
python3 example_rainbow_bands.py ../calibration/position-maps/tree.json \
  --output my_animation.gift --duration 10

# 3. Preview animation
python3 simulate_gift.py my_animation.gift ../calibration/position-maps/tree.json

# 4. Transfer to Pi
scp my_animation.gift pi@<pi_ip>:~/christmas-lights/pi/GIFT/gifts/
```

**On Raspberry Pi:**

```bash
cd ~/christmas-lights/pi/GIFT
# Play animation (looks in gifts/ directory by default)
sudo python3 gift_player.py rainbow.gift

# Or with full path
sudo python3 gift_player.py gifts/rainbow.gift

# With options
sudo python3 gift_player.py rainbow.gift --speed 2.0 --brightness 128
```

Note: `sudo` is required for GPIO access on the Raspberry Pi.

## Standard Directories

The project uses standard directories for organization:

- **GIFT animations**: `pi/GIFT/gifts/` - Animation files (.gift)
- **Position maps**: `remote/calibration/position-maps/` - Calibrated 3D positions
- **Example position maps**: `pi/GIFT/position_maps/` - Test/example position data

Tools automatically check these directories when given just a filename.

## GIFT File Format

GIFT uses a simple CSV format for maximum compatibility and ease of generation:

```csv
# GIFT Animation File
# led_count: 200
# frame_count: 300
# framerate: 30.0
# duration: 10.00s
# loop: True
frame_id,R_0,G_0,B_0,R_1,G_1,B_1,R_2,G_2,B_2,...
0,255,0,0,255,0,0,255,0,0,...
1,255,10,0,255,10,0,255,10,0,...
...
```

**Key Characteristics:**
- Frame-based (not keyframe-based) - every frame is explicitly defined
- Position-independent playback (positions used only during generation)
- RGB values 0-255 for each LED at each frame
- Metadata in comment header for player configuration

See [docs/GIFT_FORMAT_SPEC.md](docs/GIFT_FORMAT_SPEC.md) for complete specification.

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
