# GIFT Format Specification

**Geometric Interactive Format for Trees** - Version 1.0

## Overview

GIFT is a simple frame-based animation format for LED displays. Unlike real-time generative systems, GIFT files contain pre-rendered animations stored as sequential frames, similar to video files.

## Design Philosophy

- **Simplicity**: CSV-based format, human-readable
- **Performance**: No runtime calculations, just sequential playback
- **Portability**: Position-independent playback (positions used only for generation)
- **Flexibility**: Easy to generate from any programming language

## File Format

### Structure

A GIFT file is a CSV (Comma-Separated Values) file with:
1. Metadata header (comment lines starting with `#`)
2. Column header row
3. Frame data rows

### Example

```csv
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

## Metadata Fields

Metadata is stored in comment lines (starting with `#`) at the beginning of the file.

### Required Fields

- **`led_count`**: Number of LEDs in the display
  - Type: Integer
  - Example: `# led_count: 200`

- **`frame_count`**: Total number of frames
  - Type: Integer
  - Example: `# frame_count: 300`

- **`framerate`**: Target playback rate in Hz (frames per second)
  - Type: Float
  - Example: `# framerate: 30.0`

### Optional Fields

- **`duration`**: Total animation length (calculated: `frame_count / framerate`)
  - Type: Float (seconds)
  - Example: `# duration: 10.00s`

- **`loop`**: Whether the animation should repeat
  - Type: Boolean (`True` or `False`)
  - Default: `True`
  - Example: `# loop: True`

- **`name`**: Human-readable animation name
  - Type: String
  - Example: `# name: Rainbow Bands`

- **`description`**: Animation description
  - Type: String
  - Example: `# description: Seven rainbow-colored bands falling down`

- **`created`**: Creation timestamp
  - Type: ISO 8601 string
  - Example: `# created: 2024-12-15T10:30:00`

- **`generator`**: Software that created the file
  - Type: String
  - Example: `# generator: GIFTCreator 1.0`

## Data Format

### Column Header

The first non-comment line must be a CSV header:
```
frame_id,R_0,G_0,B_0,R_1,G_1,B_1,R_2,G_2,B_2,...,R_N,G_N,B_N
```

Where `N = led_count - 1`.

### Frame Rows

Each subsequent row represents one frame:
```
frame_id,R_0,G_0,B_0,R_1,G_1,B_1,R_2,G_2,B_2,...,R_N,G_N,B_N
```

**Fields:**
- `frame_id`: Sequential frame number (0, 1, 2, ...)
- `R_i`, `G_i`, `B_i`: RGB color values for LED `i` (0-255)

**Example row:**
```
5,255,0,0,0,255,0,0,0,255,128,128,0,255,255,255,...
```
This is frame 5 with:
- LED 0: Red (255, 0, 0)
- LED 1: Green (0, 255, 0)
- LED 2: Blue (0, 0, 255)
- LED 3: Yellow (128, 128, 0)
- LED 4: White (255, 255, 255)
- ...

### RGB Value Constraints

- **Range**: 0-255 (inclusive)
- **Type**: Integer
- **Order**: Red, Green, Blue (standard RGB)

## File Size Calculation

**Formula:**
```
file_size ≈ (frame_count) × (3 × led_count + 1) × 6 bytes
```

**Components:**
- `3 × led_count`: Three values (R, G, B) per LED
- `+ 1`: Frame ID column
- `× 6 bytes`: Average bytes per CSV value (including commas)

**Examples:**
- 10s @ 30fps, 200 LEDs: `300 × 601 × 6 ≈ 1.1 MB`
- 30s @ 30fps, 200 LEDs: `900 × 601 × 6 ≈ 3.3 MB`
- 10s @ 60fps, 200 LEDs: `600 × 601 × 6 ≈ 2.2 MB`

## Playback Behavior

### Frame Timing

The player attempts to maintain the specified framerate:
1. Record frame start time
2. Display frame (set all LED colors)
3. Calculate elapsed time
4. Sleep for `(1/framerate) - elapsed` seconds

### Looping

If `loop: True`:
- Animation repeats from frame 0 after the last frame
- Continues until interrupted (Ctrl+C) or max loops reached

If `loop: False`:
- Animation plays once and stops
- All LEDs remain at their final frame colors

### Speed Control

Players may support speed multipliers:
- `speed = 2.0`: Play at 2× speed (30fps → 60fps effective)
- `speed = 0.5`: Play at half speed (30fps → 15fps effective)

## Creating GIFT Files

### Using Python (GIFTCreator)

```python
from gift_creator import GIFTCreator, hsv_to_rgb

# Create animation (LED count will be inferred from position map)
creator = GIFTCreator(framerate=30)

# Load position map for spatial animations (LED count inferred automatically)
creator.load_position_map('position_map.json')

# Generate frames
for frame_idx in range(300):
    colors = []
    for led_idx in range(creator.led_count):
        # Calculate color for this LED and frame
        hue = (frame_idx * 3.6) % 360
        r, g, b = hsv_to_rgb(hue, 1.0, 1.0)
        colors.append((r, g, b))
    creator.add_frame(colors)

# Export
creator.export('my_animation.gift', loop=True)
```

**Alternative: Without position map (specify LED count directly):**
```python
# If you don't need spatial positioning, specify LED count
creator = GIFTCreator(led_count=200, framerate=30)
# ... add frames ...
creator.export('my_animation.gift')
```

### Manual Creation

You can create GIFT files with any tool that writes CSV:

```python
import csv

with open('animation.gift', 'w', newline='') as f:
    # Write metadata
    f.write('# GIFT Animation File\n')
    f.write('# led_count: 200\n')
    f.write('# frame_count: 100\n')
    f.write('# framerate: 30.0\n')
    f.write('# loop: True\n')

    # Write CSV
    writer = csv.writer(f)

    # Header
    header = ['frame_id']
    for i in range(200):
        header.extend([f'R_{i}', f'G_{i}', f'B_{i}'])
    writer.writerow(header)

    # Frames
    for frame in range(100):
        row = [frame]
        for led in range(200):
            # All red
            row.extend([255, 0, 0])
        writer.writerow(row)
```

## Position Maps

While position maps are not stored in GIFT files, they are typically used during generation for spatial animations.

### Position Map Format

Position maps are separate JSON files:

```json
{
  "version": "1.0",
  "metadata": {
    "led_count": 200,
    "units": "normalized",
    "coordinate_system": "X-Y horizontal, Z vertical (up)"
  },
  "positions": [
    [0.1, 0.2, 0.3],
    [0.4, 0.5, 0.6],
    ...
  ]
}
```

### Coordinate System

- **X-Y plane**: Horizontal
- **Z axis**: Vertical (up)
- **Units**: Typically normalized (height = 1.0)
- **Origin**: Center of the display

### Unmapped LEDs

LEDs that fail during camera-based triangulation are assigned position `[0.0, 0.0, 0.0]` (the origin). When creating animations:

- **GIFTCreator behavior**: Automatically detects unmapped LEDs and forces them to black `(0, 0, 0)` in all frames
- **Detection**: Any LED at exactly position (0, 0, 0) is considered unmapped
- **Result**: Unmapped LEDs will appear off/dark in all animations regardless of spatial calculations

This ensures that LEDs with invalid position data don't display incorrect colors during spatial animations.

## Validation

### Required Checks

1. **File format**: Valid CSV
2. **Metadata**: Required fields present
3. **LED count**: Consistent across metadata and data
4. **Frame count**: Matches number of data rows
5. **RGB values**: All in range 0-255
6. **Frame IDs**: Sequential starting from 0

### Optional Checks

1. **Column count**: `1 + (3 × led_count)`
2. **Frame timing**: Reasonable framerate (1-120 fps typical)
3. **File size**: Expected size matches actual

## Compatibility

### Version 1.0

The current specification. Players should:
- Support all required metadata fields
- Gracefully handle missing optional fields (use defaults)
- Ignore unknown metadata fields
- Support standard CSV parsing rules

### Future Versions

Potential extensions:
- Compression (e.g., run-length encoding)
- Brightness keyframes
- Palette-based encoding
- Interpolation hints
- Segment markers for transitions

## Implementation Notes

### CSV Parsing

- Use standard CSV library/parser
- Handle varying line endings (LF, CRLF)
- Support quoted fields (though not typically needed)

### Memory Considerations

For large animations:
- **Streaming**: Read frames one at a time
- **Caching**: Keep recent frames in memory
- **Compression**: Store compressed, decompress on-the-fly

### Performance Tips

- **Batch writes**: Buffer multiple frames before writing
- **Pre-allocation**: Allocate color arrays once, reuse
- **Integer operations**: Avoid floating-point where possible

## Examples

### Simple All-Red Animation

```csv
# GIFT Animation File
# led_count: 3
# frame_count: 3
# framerate: 30.0
# loop: True
frame_id,R_0,G_0,B_0,R_1,G_1,B_1,R_2,G_2,B_2
0,255,0,0,255,0,0,255,0,0
1,255,0,0,255,0,0,255,0,0
2,255,0,0,255,0,0,255,0,0
```

### Rainbow Fade

```csv
# GIFT Animation File
# led_count: 2
# frame_count: 3
# framerate: 30.0
# loop: True
frame_id,R_0,G_0,B_0,R_1,G_1,B_1
0,255,0,0,255,0,0
1,0,255,0,0,255,0
2,0,0,255,0,0,255
```

## Tools

### Generation
- [GIFTCreator](../remote/gift-generation/gift_creator.py) - Python library
- [Example Generator](../remote/gift-generation/example_rainbow_bands.py) - Rainbow bands

### Simulation & Preview
- [GIFT Simulator](../remote/gift-generation/simulate_gift.py) - 3D visualization and preview tool
  - Interactive playback with 3D visualization
  - Frame-by-frame stepping
  - Export preview images
  - Verify animations before deployment

### Playback
- [GIFT Player](../pi/GIFT/gift_player.py) - Raspberry Pi player

### Utilities
- Position map tools in [calibration system](../remote/calibration/)

## See Also

- [GIFTCreator Documentation](../remote/gift-generation/README.md)
- [GIFT Player Documentation](../pi/GIFT/README.md)
- [Position Mapping Guide](POSITION_MAPPING.md)
- [Calibration System](../remote/calibration/README.md)
