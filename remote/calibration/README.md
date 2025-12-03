# Remote Calibration Tools

Tools that run on a remote machine (laptop) to perform camera-based LED position calibration.

## Components

### pi_control.py

Handles communication with Raspberry Pi to control individual LEDs.

**Usage:**
```python
from pi_control import PiController

# Create controller
controller = PiController("192.168.1.100", port=8080)

# Connect
if controller.connect():
    # Light LED 0
    controller.light_led(0, color=(255, 255, 255))

    # Turn off LED 0
    controller.turn_off_led(0)

    # Turn off all LEDs
    controller.all_off()
```

**Test Connection:**
```bash
python3 pi_control.py 192.168.1.100 8080
```

### camera_capture.py

Handles camera operations and LED detection in captured images.

**Usage:**
```python
from camera_capture import CameraCapture, LEDDetection

# Open camera
camera = CameraCapture(camera_id=0)
camera.open()

# Capture frame
frame = camera.capture_frame()

# Detect LED
detection = camera.detect_led(frame, led_index=0)

if not detection.occluded:
    print(f"LED at pixel ({detection.pixel_x}, {detection.pixel_y})")
    print(f"Confidence: {detection.confidence}")
else:
    print(f"LED occluded: {detection.notes}")

camera.close()
```

**Test Camera:**
```bash
python3 camera_capture.py 0  # Use camera 0
```

### capture_session.py

Complete CLI tool for capturing LED positions from a single camera angle.

**Usage:**
```bash
# Basic capture
python3 capture_session.py 192.168.1.100

# With live preview
python3 capture_session.py 192.168.1.100 --preview

# With manual exposure and gain (recommended for consistent results)
python3 capture_session.py 192.168.1.100 --exposure 1250 --gain 75

# Save images and use custom camera
python3 capture_session.py 192.168.1.100 --camera 1 --save-images

# Resume from LED 50 (if interrupted)
python3 capture_session.py 192.168.1.100 --start-led 50 --angle 0

# Full example with all options
python3 capture_session.py 192.168.1.100 \
  --angle 1 \
  --camera 0 \
  --led-count 200 \
  --output ./my_tree_calibration \
  --name "angle_1_front_view" \
  --description "Front view from 2 meters" \
  --exposure 1250 \
  --gain 75 \
  --save-images \
  --preview
```

**Output:**
- `session_angle_N.json` - 2D coordinates for all LEDs from this angle
- `session_angle_N_summary.txt` - Human-readable summary
- `images_angle_N/led_XXX.jpg` - Raw captured images (if --save-images)
- `images_angle_N/led_XXX_filtered.jpg` - Color-filtered images used for detection (if --save-images with color filtering)

## Planned Components

### calibration_ui.py (To Be Implemented)
- Main GUI application
- Coordinates multi-angle capture process
- Displays progress and results
- Exports position maps

### check_calibration.py

Pre-check tool to analyze calibration data quality before triangulation.

**Usage:**
```bash
# Basic check
python3 check_calibration.py ./calibration_data

# Check with stricter requirement
python3 check_calibration.py ./calibration_data --min-detections 5

# Show images for problematic LEDs
python3 check_calibration.py ./calibration_data --show-images

# Quiet mode - only show problems
python3 check_calibration.py ./calibration_data --quiet
```

**Features:**
- Analyzes all session files in calibration directory
- Counts successful detections per LED across all angles
- Identifies LEDs with insufficient views (<4 by default)
- Shows which angles each LED was visible/occluded
- Displays saved images for problematic LEDs (if `--save-images` was used during capture)
- Provides recommendations for improving calibration quality

**Output:**
- Detection quality statistics
- List of problematic LEDs with reasons
- Visual image grid for problematic LEDs (if available)
- Exit code 0 if all good, 1 if problems detected

### triangulation.py

3D position calculation from multiple 2D capture sessions.

**Usage:**
```bash
# Basic usage
python3 triangulation.py ./calibration_data

# With custom parameters
python3 triangulation.py ./calibration_data \
  --output tree_2024.json \
  --name "Main Tree 2024" \
  --camera-distance 2.5 \
  --fov 70 \
  --image-width 1920 \
  --image-height 1080

# Visualize specific LEDs during triangulation (for debugging)
python3 triangulation.py ./calibration_data --visualize-led 0 50 100
```

**Parameters:**
- `--camera-distance`: Distance from camera to tree center in meters (default: 2.0)
- `--fov`: Camera horizontal field of view in degrees (default: 60)
- `--image-width/height`: Camera resolution (default: 640x480)
- `--visualize-led`: Show 3D visualization for specific LED indices (space-separated)

**Visualization:**
The `--visualize-led` option displays an interactive 3D plot showing:
- Camera positions around the tree (colored spheres)
- Rays from each camera through the detected LED position (colored lines)
- Estimated 3D LED position (yellow star)
- Distance from LED to each ray (printed to console)

This is useful for debugging triangulation issues or understanding the geometry of your capture setup.

**Coordinate System:**
- X-Y plane is horizontal (where cameras are positioned)
- Z axis is vertical (tree height, "up")
- Origin is at the center of the camera circle at ground level

**Output Normalization:**
The tool automatically normalizes the output coordinates:
- **Height**: Z range scaled to 1.0 (normalized units)
- **X centering**: Shifted so median X = 0
- **Y centering**: Shifted so median Y = 0
- **Z centering**: Shifted so vertical center is at Z = 0
- Original scale factor stored in metadata for reference

This normalization makes position maps portable and independent of the actual physical size of the tree.

**Output:**
- `position_map.json` - Position map in GIFT format (normalized coordinates)
- `position_map.detailed.json` - Extended version with confidence scores

### visualize_positions.py

3D visualization and analysis tool for position maps.

**Usage:**
```bash
# Interactive 3D view
python3 visualize_positions.py position_map.json

# Save to image file
python3 visualize_positions.py position_map.json --save tree_3d.png

# Generate multiple viewpoints
python3 visualize_positions.py position_map.json --multi-view ./views/

# Analysis only (no visualization)
python3 visualize_positions.py position_map.json --no-plot
```

**Features:**
- Interactive 3D rotation
- Color-coded by height
- Statistics: ranges, spacing, gaps
- Multiple viewpoint export

### camera_calibration.py (To Be Implemented)
- Camera intrinsic calibration (focal length, distortion)
- Camera extrinsic calibration (position, orientation)
- Checkerboard pattern detection

## Quick Start

### Prerequisites

Install dependencies:
```bash
pip3 install opencv-python numpy requests
```

### Complete Calibration Workflow

1. **Start Pi Server:**
   ```bash
   # On Raspberry Pi
   sudo python3 pi/calibration/led_control_server.py
   ```

2. **Test Connection (optional but recommended):**
   ```bash
   # On laptop
   python3 remote/calibration/pi_control.py <pi_ip_address>
   ```

3. **Test Camera (optional but recommended):**
   ```bash
   python3 remote/calibration/camera_capture.py 0
   ```

4. **Capture First Angle:**
   ```bash
   # Position camera at angle 0
   python3 capture_session.py <pi_ip_address> --angle 0 --preview

   # This will:
   # - Light each LED (0-199)
   # - Capture image and detect position
   # - Save results to ./calibration_data/session_angle_0.json
   ```

5. **Capture Additional Angles:**
   ```bash
   # Move camera to new position
   python3 capture_session.py <pi_ip_address> --angle 1 --preview

   # Repeat for angle 2, 3, etc.
   python3 capture_session.py <pi_ip_address> --angle 2 --preview
   ```

6. **Check Calibration Quality (recommended):**
   ```bash
   # Verify all LEDs have sufficient detections
   python3 check_calibration.py ./calibration_data --show-images

   # If problems found, re-capture problematic angles
   python3 capture_session.py <pi_ip_address> --angle 0 --start-led 45 --led-count 50
   ```

7. **Triangulate 3D Positions:**
   ```bash
   # Combine all angles to get 3D positions
   python3 triangulation.py ./calibration_data --output tree_positions.json

   # Outputs:
   # - tree_positions.json (position map)
   # - tree_positions.detailed.json (with confidence scores)
   ```

8. **Visualize Results:**
   ```bash
   # Interactive 3D view
   python3 visualize_positions.py tree_positions.json

   # Or save multiple views
   python3 visualize_positions.py tree_positions.json --multi-view ./views/
   ```

9. **Deploy to GIFT System:**
   ```bash
   # Copy position map to Pi
   cp tree_positions.json ../../pi/GIFT/position_maps/

   # Now ready to use in .gift animations!
   ```

## Development Status

- [x] Pi control module
- [x] Camera capture module
- [x] LED detection (brightest pixel)
- [x] Enhanced LED detection (background subtraction, blob detection)
- [x] CLI capture session tool
- [x] **Calibration quality checker**
- [x] **Triangulation module (ready to use!)**
- [x] **3D visualization tool**
- [x] Position map export
- [ ] Calibration UI (optional - CLI tools work well)
- [ ] Advanced camera calibration (optional - simplified method works)

## Camera Setup Tips

### Exposure and Gain Settings
- **Manual exposure is highly recommended** to prevent brightness adaptation between LEDs
- Use `--exposure` and `--gain` parameters together for full control
- **IMPORTANT**: Many cameras lock gain to minimum when you set fixed exposure!
  - Always use `--gain` with `--exposure` for proper brightness
  - Exposure controls shutter speed (light duration)
  - Gain controls sensor sensitivity (amplification)

**Exposure Ranges** (vary drastically by camera):
  - Logarithmic: `-13` to `-1` (common for some webcams)
  - Linear time: `1` to `10000` (microseconds or milliseconds)
  - Abstract: `0` to `255` or `0` to `10000`
  - Your camera may only support a narrow range within these

**Gain Ranges** (more consistent across cameras):
  - Usually: `0` to `100` or `0` to `255`
  - Higher gain = brighter but more noise
  - Start with gain `50` and adjust

**Finding Your Camera's Range:**
1. Run with any value: `--exposure -6` (or `--exposure 100`)
2. Check output for "Before setting" and "After setting" values
3. If "After setting" doesn't match your request, note the actual value
4. Try values around the actual value (e.g., if it shows 1250, try 500, 1000, 1500, 2000)
5. Use `--save-images` on a test run to see which exposure works best

**Example Discovery Process:**
```bash
# Step 1: Find exposure range
python3 capture_session.py 10.0.0.144 --exposure 1250 --start-led 0 --led-count 1 --preview
# Note the "After setting" value

# Step 2: Add gain to brighten image (if too dark with fixed exposure)
python3 capture_session.py 10.0.0.144 --exposure 1250 --gain 50 --start-led 0 --led-count 1 --preview

# Step 3: Adjust gain to get good brightness
python3 capture_session.py 10.0.0.144 --exposure 1250 --gain 25 --start-led 0 --led-count 5 --preview
python3 capture_session.py 10.0.0.144 --exposure 1250 --gain 75 --start-led 0 --led-count 5 --preview
python3 capture_session.py 10.0.0.144 --exposure 1250 --gain 100 --start-led 0 --led-count 5 --preview

# Step 4: Use --save-images to review results
python3 capture_session.py 10.0.0.144 --exposure 1250 --gain 75 --start-led 0 --led-count 10 --save-images
```

- Omit `--exposure` for auto-exposure (not recommended, may vary between LEDs)

### Camera Positioning
- Ensure entire LED installation is visible
- Use tripod for stable capture
- Mark camera positions for repeatability
- Minimum 50° angle separation between views

### LED Detection
- Red LEDs recommended (color filtering rejects ambient white light)
- Green or blue LEDs also work well with color filtering
- White LEDs work best in very dark rooms
- When using --save-images with color filtering, both raw and filtered images are saved for debugging
- Test a few LEDs before running full calibration

## Troubleshooting

**"Failed to connect to Pi"**
- Check Pi IP address
- Verify Pi server is running
- Check firewall/network settings
- Try `ping <pi_ip>` first

**"Failed to open camera"**
- Check camera is connected
- Try different camera_id (0, 1, 2, etc.)
- Close other apps using camera
- Check permissions

**"LED not detected"**
- Increase brightness on Pi
- Adjust `brightness_threshold` in camera_capture.py
- Check camera exposure settings
- Ensure LED is actually lit (test with `pi_control.py`)

**"Ambiguous detection"**
- Multiple LEDs may be lit
- Bright reflections in scene
- Adjust `ambiguity_threshold`
- Use darker background

**Inconsistent detection / exposure problems**
- Set manual exposure with `--exposure` parameter
- Start with `-7` and adjust based on results
- If LEDs are too dim: increase exposure (e.g., `-6`, `-5`)
- If background is too bright: decrease exposure (e.g., `-8`, `-9`)
- Use `--save-images` to review actual captured frames
- Check "Requested vs Actual" exposure in output - if different, camera may not support that range

## Documentation

See [../../docs/CALIBRATION_SYSTEM.md](../../docs/CALIBRATION_SYSTEM.md) for detailed system documentation.
