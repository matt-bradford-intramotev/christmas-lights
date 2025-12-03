# GIFT Simulator

3D visualization and preview tool for GIFT animation files.

## Overview

The GIFT simulator allows you to preview animations in 3D before deploying them to the actual hardware. It reads GIFT animation files and position maps, then displays an interactive 3D visualization showing exactly how the animation will look on the tree.

## Quick Start

```bash
# Interactive visualization
python3 simulate_gift.py animation.gift position_map.json

# Export preview frames
python3 simulate_gift.py animation.gift position_map.json --export-frames ./previews
```

## Features

### Interactive 3D Visualization
- Real-time playback of GIFT animations
- 3D scatter plot with LED positions colored according to animation frames
- Smooth rotation and zoom controls
- Displays LED strip path as gray lines

### Playback Controls
- **Space**: Play/Pause
- **Left/Right Arrow**: Previous/Next frame (manual stepping)
- **L**: Toggle loop mode on/off
- **R**: Reset to frame 0
- **+/-**: Increase/Decrease playback speed
- **Mouse Drag**: Rotate 3D view
- **Mouse Scroll**: Zoom in/out

### Information Display
- Current frame number and total frames
- Time position and duration
- Playback status (playing/paused)
- Playback speed multiplier
- Loop status
- LED count
- Animation name and metadata

### Export Mode
Export preview images for specific frames:

```bash
python3 simulate_gift.py animation.gift position_map.json \
  --export-frames ./preview_images
```

By default, exports every 30th frame. Creates PNG images showing the animation at different time points.

## Command-Line Options

```
usage: simulate_gift.py [-h] [--export-frames DIR] [--marker-size SIZE]
                        [--view ELEV AZIM] [--no-axes]
                        gift_file position_map

positional arguments:
  gift_file              GIFT animation file (.gift)
  position_map           Position map JSON file

optional arguments:
  -h, --help             Show help message
  --export-frames DIR    Export preview frames to directory
  --marker-size SIZE     LED marker size (default: 100)
  --view ELEV AZIM       Initial view angle (default: 30 45)
  --no-axes              Hide coordinate axes
```

## Examples

### Basic Visualization
```bash
python3 simulate_gift.py rainbow_bands.gift position_map.json
```

### Custom View and Larger Markers
```bash
python3 simulate_gift.py rainbow_bands.gift position_map.json \
  --marker-size 150 \
  --view 45 60
```

### Export Preview Frames
```bash
python3 simulate_gift.py rainbow_bands.gift position_map.json \
  --export-frames ./previews
```

### Clean View (No Axes)
```bash
python3 simulate_gift.py rainbow_bands.gift position_map.json --no-axes
```

## Technical Details

### Color Handling
- Reads RGB values from GIFT CSV (0-255 range)
- Converts to matplotlib color format (0-1 range)
- Displays colors exactly as they will appear on LEDs

### LED Count Mismatch
If the GIFT file and position map have different LED counts:
- Uses the minimum of the two
- Shows a warning message
- Continues simulation with available data

### Performance
- Optimized for smooth playback up to 60fps
- Handles animations with hundreds of frames
- Interactive controls remain responsive during playback

### Supported GIFT Features
- All metadata fields (led_count, frame_count, framerate, duration, loop)
- Variable frame rates
- Looping and non-looping animations
- Custom animation names

## Workflow Integration

The simulator fits into the GIFT creation workflow:

1. **Calibrate**: Use camera calibration to create position map
2. **Generate**: Create GIFT animation using GIFTCreator
3. **Simulate**: Preview animation with simulator ← **NEW STEP**
4. **Iterate**: Adjust parameters and regenerate if needed
5. **Deploy**: Transfer to Raspberry Pi and play on actual hardware

## Dependencies

Required Python packages:
- `numpy`: Numerical operations
- `matplotlib`: 3D visualization and animation

Install with:
```bash
pip3 install numpy matplotlib
```

## Troubleshooting

### "No display found" Error
If running on a headless server, use export mode instead:
```bash
python3 simulate_gift.py animation.gift position_map.json \
  --export-frames ./previews
```

### Slow Playback
- Reduce marker size: `--marker-size 50`
- Close other applications
- Reduce frame rate when generating GIFT file

### Animation Too Fast/Slow
Use playback speed controls:
- Press `+` to speed up
- Press `-` to slow down
- Or regenerate GIFT file with different framerate

## See Also

- [GIFT Format Specification](../../docs/GIFT_FORMAT_SPEC.md)
- [GIFTCreator Documentation](README.md)
- [Example Animations](examples/)
