# Position Mapping System

## Overview

The position mapping system stores the 3D spatial coordinates of each LED in the physical installation. This allows GIFT animations to use position-based effects.

## Format

Position maps are stored as JSON files with a `.json` extension.

### Basic Structure

```json
{
  "version": "0.1.0",
  "metadata": {
    "name": "Main Christmas Tree 2024",
    "led_count": 200,
    "created": "2024-12-01",
    "units": "meters",
    "origin": "base center of tree"
  },
  "positions": [
    {"id": 0, "x": 0.0, "y": 0.0, "z": 0.0},
    {"id": 1, "x": 0.05, "y": 0.0, "z": 0.02},
    {"id": 2, "x": 0.03, "y": 0.08, "z": 0.01}
  ]
}
```

### Alternative Format (Array-based)

For simpler editing, positions can be stored as arrays:

```json
{
  "version": "0.1.0",
  "metadata": {
    "name": "Main Christmas Tree 2024",
    "led_count": 200,
    "units": "meters"
  },
  "positions": [
    [0.0, 0.0, 0.0],
    [0.05, 0.0, 0.02],
    [0.03, 0.08, 0.01]
  ]
}
```

## Coordinate System

### Convention
- **Origin**: Base center of tree (or installation-specific reference point)
- **X axis**: Left (-) to Right (+) when facing tree
- **Y axis**: Bottom (-) to Top (+)
- **Z axis**: Back (-) to Front (+) when facing tree
- **Units**: Meters (configurable in metadata)

### Coordinate Handedness
Right-handed coordinate system (standard for 3D graphics)

## Creating Position Maps

### Camera-Based Calibration (Primary Method)

The recommended approach uses automated camera-based triangulation to determine LED positions in 3D space.

#### Overview
1. Remote machine (laptop) with camera pointed at LED installation
2. Pi lights up one LED at a time on command
3. Remote machine captures image and locates LED (brightest pixel)
4. Process repeats for all LEDs from multiple viewing angles
5. 3D positions calculated via triangulation from multiple 2D views

#### Requirements
- Camera (webcam, phone, or dedicated camera)
- Multiple viewing angles (minimum 2, more is better)
- Remote machine with Python and image processing libraries
- Network connection between remote machine and Pi

#### Process

**Step 1: Setup**
- Position camera at first viewing angle
- Ensure entire LED installation is visible
- Note camera position/angle for reference
- Establish network connection to Pi

**Step 2: Capture from First Angle**
- Remote machine commands Pi to light LED index 0
- Capture image and detect LED location (brightest pixel)
- Check for occlusion (LED not visible or ambiguous)
- Optionally save image for reference
- Repeat for all LED indices (0-199)
- Store 2D coordinates for each LED from this viewpoint

**Step 3: Repeat from Additional Angles**
- Move camera to new position
- Repeat Step 2 from this angle
- Minimum 2 angles required, 3-5 recommended for accuracy

**Step 4: Triangulation**
- Use 2D coordinates from multiple views
- Apply camera calibration (intrinsic/extrinsic parameters)
- Triangulate 3D position for each LED
- Validate results (check for outliers, physically impossible positions)

**Step 5: Export**
- Convert 3D positions to position map JSON format
- Save to `pi/GIFT/position_maps/`
- Validate with visualization tool

#### Occlusion Handling

LEDs may be occluded (hidden) from certain camera angles:
- Detect occlusion: no bright pixel found, or ambiguous detection
- Mark LED as occluded for this viewpoint
- Require LED to be visible from at least 2 angles for triangulation
- Flag LEDs with insufficient views for manual review

#### Calibration Tool Architecture

The calibration system consists of:

**Remote Side** (`remote/calibration/`):
- `calibration_ui.py` - Main GUI application
- `camera_capture.py` - Image capture and LED detection
- `triangulation.py` - 3D position calculation
- `pi_control.py` - Communication with Pi to control LEDs
- `camera_calibration.py` - Camera calibration utilities

**Pi Side** (`pi/calibration/`):
- `led_control_server.py` - Receives commands to light specific LEDs
- Simple HTTP/socket server listening for LED index commands

See [Calibration Tool Documentation](CALIBRATION_SYSTEM.md) for detailed implementation.

### Manual Method (Fallback)
1. Create JSON file with template structure
2. Physically measure LED positions with ruler/tape measure
3. Enter coordinates manually
4. Validate with visualization tool

### Procedural Generation (Testing Only)
For testing, generate positions mathematically:

```python
# Example: Spiral pattern
import json
import math

positions = []
for i in range(200):
    angle = i * 0.2
    radius = 0.3 + (i / 200) * 0.2
    height = (i / 200) * 2.0

    x = radius * math.cos(angle)
    z = radius * math.sin(angle)
    y = height

    positions.append([x, y, z])

# Save to JSON file
```

## Usage in GIFT System

The GIFT player class will:
1. Load the position map specified in the .gift file
2. Build a lookup table: LED index → (x, y, z) position
3. Use positions for spatial calculations during playback

## Validation

Position maps should be validated for:
- Correct LED count (matches hardware configuration)
- All LED indices present (0 to N-1)
- No duplicate indices
- Reasonable coordinate ranges (sanity check)
- Valid metadata fields

## Storage Location

Position maps should be stored in:
```
pi/GIFT/position_maps/
```

Multiple maps can be created for different installations or tree configurations.

## File Naming Convention

```
<name>_<led_count>_<date>.json
```

Examples:
- `main_tree_200_2024-12-01.json`
- `window_display_150_2024-11-15.json`
- `test_spiral_50_2024-12-05.json`

## Future Enhancements

- Support for multiple LED strips with separate coordinate systems
- LED grouping/segmentation (e.g., "all LEDs on front of tree")
- Metadata for LED orientation/normal vectors
- Color calibration data per LED
- Physical connection mapping (which controller pin)
