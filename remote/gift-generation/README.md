# GIFT Animation Generation

Tools for creating GIFT (Geometric Interactive Format for Trees) animation files.

## Overview

The GIFT format is a simple frame-based animation system:
- **Format**: CSV file with metadata header
- **Structure**: Each row contains `frame_id, R_1, G_1, B_1, R_2, G_2, B_2, ...`
- **Playback**: Simple sequential playback, no runtime calculations needed
- **Generation**: Uses 3D position maps to create spatially-aware animations

## Components

### gift_creator.py

Python library for creating GIFT animation files.

**Key Classes:**
- `GIFTCreator`: Main class for building animations
- `LEDPosition`: 3D position data for an LED

**Basic Usage:**
```python
from gift_creator import GIFTCreator, hsv_to_rgb

# Create animation (LED count will be inferred from position map)
creator = GIFTCreator(framerate=30)

# Load position map - LED count automatically inferred
creator.load_position_map('position_map.json')

# Add frames
for frame_idx in range(100):
    colors = []
    for led_idx in range(creator.led_count):
        # Calculate color for this LED
        r, g, b = hsv_to_rgb(frame_idx * 3.6, 1.0, 1.0)
        colors.append((r, g, b))
    creator.add_frame(colors)

# Export
creator.export('my_animation.gift', loop=True)
```

**Alternative: Specify LED count directly (without position map):**
```python
# If you don't need position data, specify LED count directly
creator = GIFTCreator(led_count=200, framerate=30)
# No need to load position map
```

**Methods:**
- `load_position_map(filepath)`: Load LED 3D positions from JSON
  - Automatically infers LED count from position map
  - Detects unmapped LEDs (those at position 0,0,0) and marks them for blackout
- `add_frame(colors)`: Add single frame with list of (R, G, B) tuples
  - Automatically forces unmapped LEDs to black (0,0,0) regardless of input
- `add_frames(frames)`: Add multiple frames at once
- `export(filepath, loop=True)`: Write GIFT file
- `get_positions_array()`: Get positions as numpy array
- `get_positions_by_z()`: Get LEDs sorted by Z (height)
- `is_mapped(led_index)`: Check if an LED has valid position mapping

**Utilities:**
- `hsv_to_rgb(h, s, v)`: Convert HSV (h: 0-360, s/v: 0-1) to RGB (0-255)

### Unmapped LED Handling

LEDs that failed during triangulation are assigned position `[0.0, 0.0, 0.0]` (the origin). GIFTCreator automatically detects these unmapped LEDs when loading a position map and forces them to black `(0, 0, 0)` in all animation frames.

**Behavior:**
- When `load_position_map()` is called, LEDs at position (0,0,0) are marked as unmapped
- Warning message displayed showing count of unmapped LEDs
- All unmapped LEDs are automatically set to black in every frame
- This happens regardless of what colors are provided to `add_frame()`

**Example:**
```python
creator = GIFTCreator(framerate=30)
creator.load_position_map('position_map.json')
# If LEDs 5, 12, 37 failed triangulation:
# ⚠ Warning: 3 unmapped LED(s) detected (will be set to black in animations)
#   Unmapped LEDs: [5, 12, 37]

# Add frame with all LEDs red
colors = [(255, 0, 0)] * creator.led_count
creator.add_frame(colors)
# LEDs 5, 12, 37 will be black in the animation, regardless of input
```

### example_rainbow_bands.py

Example animation: Rainbow-colored bands falling down the Z-axis.

**Usage:**
```bash
# Basic usage
python3 example_rainbow_bands.py position_map.json

# Custom output and settings
python3 example_rainbow_bands.py position_map.json \
  --output rainbow.gift \
  --duration 20 \
  --framerate 60 \
  --speed 2.0
```

**Parameters:**
- `position_map`: Path to position map JSON file (required)
- `--output`: Output GIFT file path (default: `rainbow_bands.gift`)
- `--duration`: Animation duration in seconds (default: 10.0)
- `--framerate`: Frames per second (default: 30.0)
- `--speed`: Speed multiplier for falling motion (default: 1.0)
- `--led-count`: Number of LEDs (default: 200)

**How It Works:**
1. Divides Z-axis into 7 equal bands
2. Assigns rainbow colors to each band (ROYGCBV)
3. Animates bands falling down with periodic wrapping
4. Each LED's color determined by its Z position and time offset

### simulate_gift.py

3D visualization and simulation tool for GIFT animations. Preview what your animation will look like on the actual tree before deploying to hardware.

**Usage:**
```bash
# Interactive visualization
python3 simulate_gift.py animation.gift position_map.json

# Export preview frames
python3 simulate_gift.py animation.gift position_map.json --export-frames ./previews

# Customize visualization
python3 simulate_gift.py animation.gift position_map.json \
  --marker-size 150 \
  --view 45 60 \
  --no-axes
```

**Parameters:**
- `gift_file`: GIFT animation file to simulate (required)
- `position_map`: Position map JSON file (required)
- `--export-frames DIR`: Export preview frames to directory instead of interactive mode
- `--marker-size SIZE`: LED marker size in visualization (default: 100)
- `--view ELEV AZIM`: Initial view angle (elevation, azimuth) (default: 30 45)
- `--no-axes`: Hide coordinate axes

**Interactive Controls:**
- `Space`: Play/Pause animation
- `Left/Right Arrow`: Previous/Next frame
- `L`: Toggle loop mode
- `R`: Reset to frame 0
- `+/-`: Increase/Decrease playback speed
- `Mouse Drag`: Rotate 3D view
- `Mouse Scroll`: Zoom in/out

**Features:**
- Real-time 3D visualization of LED positions with animation colors
- Interactive playback controls
- Variable speed playback
- Frame-by-frame stepping
- Export mode for creating preview images
- Shows animation metadata (frame count, duration, etc.)

## GIFT File Format

### File Structure

```
# GIFT Animation File
# Format: frame_id, R_1, G_1, B_1, R_2, G_2, B_2, ...
# led_count: 200
# frame_count: 300
# framerate: 30.0
# duration: 10.00s
# loop: True
frame_id,R_0,G_0,B_0,R_1,G_1,B_1,R_2,G_2,B_2,...
0,255,0,0,255,0,0,255,0,0,...
1,255,10,0,255,10,0,255,10,0,...
2,255,20,0,255,20,0,255,20,0,...
...
```

### Metadata Fields

- `led_count`: Number of LEDs in the display
- `frame_count`: Total number of frames
- `framerate`: Target playback rate in Hz
- `duration`: Total animation length in seconds
- `loop`: Whether animation should loop

### Data Format

- **CSV format**: Standard comma-separated values
- **Header row**: Column names (`frame_id`, `R_0`, `G_0`, `B_0`, ...)
- **Data rows**: Frame number followed by RGB triplets
- **RGB values**: Integers 0-255

## Creating Custom Animations

### Example: Simple Color Fade

```python
from gift_creator import GIFTCreator

# Create 5-second animation at 30fps with 200 LEDs
creator = GIFTCreator(led_count=200, framerate=30)

num_frames = int(5.0 * 30)  # 150 frames

for frame_idx in range(num_frames):
    # Fade from red to blue
    t = frame_idx / num_frames  # 0.0 to 1.0
    r = int(255 * (1 - t))
    b = int(255 * t)

    # All LEDs same color
    colors = [(r, 0, b)] * creator.led_count
    creator.add_frame(colors)

creator.export('fade_animation.gift')
```

### Example: Spatial Animation Using Positions

```python
from gift_creator import GIFTCreator, hsv_to_rgb
import numpy as np

# LED count will be inferred from position map
creator = GIFTCreator(framerate=30)
creator.load_position_map('position_map.json')

positions = creator.get_positions_array()

for frame_idx in range(300):
    t = frame_idx / 30.0  # Time in seconds
    colors = []

    for led_idx in range(creator.led_count):
        x, y, z = positions[led_idx]

        # Hue based on height, rotating over time
        hue = (z * 360 + t * 60) % 360
        r, g, b = hsv_to_rgb(hue, 1.0, 1.0)
        colors.append((r, g, b))

    creator.add_frame(colors)

creator.export('height_spiral.gift')
```

## Workflow

### 1. Create Position Map

Use the calibration tools to generate a position map:

```bash
cd ../calibration
python3 triangulation.py ./calibration_data --output position_map.json
```

### 2. Generate Animation

Create your animation using the position map:

```bash
cd ../gift-generation
python3 example_rainbow_bands.py ../calibration/position_map.json --output my_animation.gift
```

### 3. Preview Animation (New!)

Visualize your animation in 3D before deploying to hardware:

```bash
python3 simulate_gift.py my_animation.gift ../calibration/position_map.json
```

This opens an interactive 3D viewer where you can:
- Play/pause the animation
- Rotate the view to see from different angles
- Step through frames
- Adjust playback speed
- Verify colors and timing

**Export Preview Frames:**
```bash
python3 simulate_gift.py my_animation.gift ../calibration/position_map.json \
  --export-frames ./preview_images
```

### 4. Transfer to Pi

Copy the GIFT file to your Raspberry Pi:

```bash
scp my_animation.gift pi@<pi_ip>:~/christmas-lights/pi/GIFT/animations/
```

### 5. Play Animation

On the Raspberry Pi, use the GIFT player:

```bash
cd ~/christmas-lights/pi/GIFT
sudo python3 gift_player.py animations/my_animation.gift
```

## Performance Considerations

### File Size

A typical GIFT file size calculation:
- **Formula**: `(frame_count) × (3 × led_count + 1) × ~6 bytes`
- **Example**: 300 frames × 601 values × 6 bytes ≈ 1.1 MB
- **30-second animation** at 30fps with 200 LEDs ≈ 3.3 MB

### Framerate Recommendations

- **Low motion**: 15-20 fps (smaller files, still smooth)
- **Standard**: 30 fps (good balance)
- **High motion**: 60 fps (very smooth, larger files)

### Generation Time

- GIFT generation is fast (usually <1 second for 10s animation)
- Complex spatial calculations may take longer
- Use numpy for vectorized operations when possible

## Tips for Creating Animations

### Color Harmonies

```python
from gift_creator import hsv_to_rgb

# Complementary colors (180° apart)
color1 = hsv_to_rgb(0, 1.0, 1.0)    # Red
color2 = hsv_to_rgb(180, 1.0, 1.0)  # Cyan

# Triadic colors (120° apart)
color1 = hsv_to_rgb(0, 1.0, 1.0)    # Red
color2 = hsv_to_rgb(120, 1.0, 1.0)  # Green
color3 = hsv_to_rgb(240, 1.0, 1.0)  # Blue

# Analogous colors (30° apart)
base = 180
colors = [hsv_to_rgb(base + i * 30, 1.0, 1.0) for i in range(-2, 3)]
```

### Smooth Transitions

Use easing functions for more natural motion:

```python
import math

def ease_in_out(t):
    """Smooth acceleration and deceleration."""
    return t * t * (3 - 2 * t)

def ease_sine(t):
    """Sinusoidal easing."""
    return (math.sin((t - 0.5) * math.pi) + 1) / 2

# Usage
for frame_idx in range(num_frames):
    t_linear = frame_idx / num_frames
    t_eased = ease_in_out(t_linear)
    # Use t_eased for smooth motion
```

### Spatial Patterns

Common spatial animation patterns:
- **Bands**: Divide along one axis (see rainbow_bands example)
- **Waves**: Sine wave based on distance from center
- **Spirals**: Combine height with rotation angle
- **Sparkles**: Random LEDs with decay
- **Fire**: Noise-based upward motion

## Dependencies

**Required:**
- Python 3.7+
- `numpy` for numerical operations
- Standard library: `csv`, `json`, `pathlib`

**Installation:**
```bash
pip3 install numpy
```

## Next Steps

- Implement GIFT player for Raspberry Pi (`pi/GIFT/gift_player.py`)
- Create more example animations
- Add animation composition tools (combine, transition)
- Create GUI animation editor
- Add preview/visualization tool

## See Also

- [Calibration System](../calibration/README.md) - Create position maps
- [Position Mapping](../../docs/POSITION_MAPPING.md) - Position map format
- [GIFT Format Spec](../../docs/GIFT_FORMAT_SPEC.md) - Detailed format documentation
