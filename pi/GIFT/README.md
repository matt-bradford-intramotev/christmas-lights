# GIFT System

**Geometric Interactive Format for Trees**

A file-based animation system for 3D LED light displays.

## Status

🚧 **Under Development** - Core components are being designed and implemented.

## Directory Structure

```
GIFT/
├── README.md              # This file
├── position_maps/         # 3D coordinate files for LED positions
│   ├── README.md
│   └── test_linear_50.json
├── animations/            # User-created .gift animation files
├── examples/              # Example .gift files
│   ├── simple_fade.gift
│   └── sparkle.gift
└── (to be added)
    ├── gift_player.py     # Main player class
    ├── gift_parser.py     # File format parser
    └── gift_validator.py  # File validation utility
```

## Quick Start (When Implemented)

```bash
# Play an animation
sudo python3 gift_player.py animations/my_animation.gift

# Validate a .gift file
python3 gift_validator.py animations/my_animation.gift

# Create a position map
# Use the visualization tool on your development machine
```

## Components

### 1. Position Maps
- JSON files defining 3D coordinates of each LED
- See [position_maps/README.md](position_maps/README.md)
- Required for spatial animations

### 2. GIFT Files
- Define animations using keyframes
- Reference a position map
- JSON format with `.gift` extension
- See examples in `examples/` directory

### 3. GIFT Player
- Loads and executes .gift files
- Interpolates between keyframes
- Controls LED hardware via rpi_ws281x

### 4. Visualization Tool
- Desktop application (separate from Pi)
- Create and preview animations
- Export to .gift format

## Documentation

- [GIFT Format Specification](../../docs/GIFT_FORMAT_SPEC.md)
- [Position Mapping Guide](../../docs/POSITION_MAPPING.md)
- [Development Plan](../../docs/DEVELOPMENT_PLAN.md)

## Requirements

- Python 3.7+
- rpi_ws281x library (for playback on Pi)
- numpy
- Position map file for your LED installation

## Usage

See example .gift files in `examples/` directory to understand the format.

The visualization tool (to be developed) will be the primary way to create animations.
