# Camera-Based Calibration System

## Overview

The calibration system automatically determines 3D positions of LEDs using computer vision and triangulation from multiple camera viewpoints.

## Architecture

### System Components

```
┌─────────────────────────┐         ┌──────────────────────┐
│   Remote Machine        │         │   Raspberry Pi       │
│   (Laptop)              │◄────────┤   (Zero 2 W)         │
│                         │ Network │                      │
│  ┌──────────────────┐   │         │  ┌────────────────┐  │
│  │ Calibration UI   │   │         │  │ LED Control    │  │
│  │                  │   │         │  │ Server         │  │
│  │ - Capture ctrl   │   │         │  │                │  │
│  │ - Progress view  │   │         │  │ Lights single  │  │
│  │ - Validation     │   │         │  │ LED on command │  │
│  └──────────────────┘   │         │  └────────────────┘  │
│                         │         │          │           │
│  ┌──────────────────┐   │         │          ▼           │
│  │ Camera Capture   │   │         │  ┌────────────────┐  │
│  │                  │   │         │  │ WS281x LEDs    │  │
│  │ - Image capture  │   │         │  │ (200 pixels)   │  │
│  │ - LED detection  │   │         │  └────────────────┘  │
│  │ - Occlusion chk  │   │         │                      │
│  └──────────────────┘   │         └──────────────────────┘
│                         │
│  ┌──────────────────┐   │
│  │ Triangulation    │   │
│  │                  │   │
│  │ - 3D calculation │   │
│  │ - Validation     │   │
│  │ - Export to JSON │   │
│  └──────────────────┘   │
│                         │
│  ┌──────────────────┐   │
│  │ Camera           │   │
│  │ (Webcam/Phone)   │   │
│  └──────────────────┘   │
└─────────────────────────┘
```

## Workflow

### 1. Setup Phase

**Start Pi Server**
```bash
# On Raspberry Pi
cd pi/calibration
sudo python3 led_control_server.py --port 8080
```

**Start Remote Calibration Tool**
```bash
# On laptop
cd remote/calibration
python3 calibration_ui.py
```

**Configuration**
- Enter Pi IP address
- Select camera device
- Set LED count (default: 200)
- Configure capture settings (exposure, brightness threshold)

### 2. Calibration Phase

**For Each Viewing Angle:**

1. Position camera to view LED installation
2. Click "Start Capture Session"
3. Tool iterates through each LED index:
   - Sends command to Pi: `light_led(index)`
   - Waits for LED to stabilize (50-100ms)
   - Captures image from camera
   - Detects brightest pixel → 2D coordinates
   - Checks for occlusion/ambiguity
   - Saves image to `captures/angle_N/led_XXX.jpg` (optional)
   - Updates progress bar
4. Click "Complete Session" when all LEDs captured
5. Move camera to next angle and repeat

**Minimum Requirements:**
- 2 viewing angles (3-5 recommended)
- Each angle should have >50° separation
- Each LED visible from at least 2 angles

### 3. Triangulation Phase

1. Click "Calculate 3D Positions"
2. Tool processes:
   - Loads 2D coordinates from all viewing angles
   - Applies camera calibration (if available)
   - Triangulates 3D position for each LED
   - Validates results:
     - Removes outliers (physically impossible positions)
     - Flags LEDs with insufficient views
     - Checks coordinate reasonableness
3. Displays results in 3D viewer
4. Manual adjustment of problematic LEDs (optional)

### 4. Export Phase

1. Review 3D positions in viewer
2. Click "Export Position Map"
3. Enter metadata (name, description)
4. Save to `pi/GIFT/position_maps/NAME.json`
5. Optionally upload directly to Pi

## Communication Protocol

### Pi LED Control Server

**API Endpoints (HTTP REST):**

```
POST /led/on
Body: {"index": 42, "color": [255, 255, 255], "brightness": 255}
Response: {"status": "ok"}

POST /led/off
Body: {"index": 42}
Response: {"status": "ok"}

POST /led/all_off
Response: {"status": "ok", "count": 200}

GET /status
Response: {"status": "ready", "led_count": 200, "current_led": null}

GET /health
Response: {"status": "healthy"}
```

**Simple Implementation:**
- Flask or FastAPI for HTTP server
- Single LED control using rpi_ws281x
- No authentication (trusted local network)
- Timeout: turn off LED if no command in 60s

### Remote Client

**Pi Control Module (`pi_control.py`):**

```python
class PiController:
    def __init__(self, pi_ip: str, port: int = 8080)
    def connect(self) -> bool
    def light_led(self, index: int, color: tuple = (255, 255, 255)) -> bool
    def turn_off_led(self, index: int) -> bool
    def all_off(self) -> bool
    def check_status(self) -> dict
```

## Image Processing

### LED Detection Algorithm

**Basic Approach (Brightest Pixel):**

```python
def detect_led(image, threshold=200):
    """
    Find LED position in image.

    Args:
        image: numpy array (H, W, 3) RGB image
        threshold: minimum brightness to consider

    Returns:
        (x, y) tuple of LED position, or None if not found
    """
    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)

    # Find brightest pixel
    max_val = gray.max()

    if max_val < threshold:
        return None  # LED not bright enough or occluded

    # Get coordinates of brightest pixel
    y, x = np.unravel_index(gray.argmax(), gray.shape)

    # Optional: check for ambiguity
    # (multiple bright pixels could indicate blooming or multiple LEDs)
    bright_pixels = (gray > max_val * 0.95).sum()
    if bright_pixels > 100:  # Too many bright pixels
        return None  # Ambiguous detection

    return (x, y)
```

**Enhanced Approach:**
- Blob detection for LED regions
- Sub-pixel accuracy using centroid
- Background subtraction (capture dark frame first)
- HDR or exposure bracketing for varying brightness
- Color filtering if LEDs have distinct color

### Occlusion Detection

Mark LED as occluded if:
- No pixel above brightness threshold
- Multiple bright regions (ambiguous)
- Detected position outside expected range
- Significant change from adjacent LED positions

## Triangulation

### Simplified Triangulation (Uncalibrated)

For quick results without camera calibration:

1. Assume camera positions are known (manually measured)
2. For each LED, have 2D positions from multiple angles
3. Use ray intersection in 3D space
4. Least squares fit if >2 views available

**Limitations:**
- Assumes pinhole camera model
- Ignores lens distortion
- Less accurate but faster to set up

### Full Calibration (Recommended)

**Camera Intrinsic Calibration:**
- Use checkerboard pattern
- OpenCV camera calibration
- Compensates for lens distortion
- Provides focal length, principal point

**Camera Extrinsic Calibration:**
- Determine camera position and orientation for each view
- Use known 3D reference points in scene
- Or use structure-from-motion (SfM) techniques

**Triangulation:**
- Standard DLT (Direct Linear Transform)
- Bundle adjustment for refinement
- RANSAC for outlier rejection

## File Formats

### Capture Session File

Intermediate storage of 2D detections:

```json
{
  "version": "0.1.0",
  "session": {
    "date": "2024-12-01T15:30:00",
    "led_count": 200,
    "camera": "Webcam HD",
    "angle_id": 0,
    "angle_description": "Front view"
  },
  "detections": [
    {
      "led_index": 0,
      "pixel_x": 320,
      "pixel_y": 240,
      "brightness": 255,
      "occluded": false,
      "image_path": "captures/angle_0/led_000.jpg"
    }
  ]
}
```

### Calibration Project File

Multi-angle calibration data:

```json
{
  "version": "0.1.0",
  "project": {
    "name": "Main Tree 2024",
    "created": "2024-12-01",
    "led_count": 200
  },
  "camera_calibration": {
    "fx": 800.0,
    "fy": 800.0,
    "cx": 320.0,
    "cy": 240.0,
    "distortion": [0.1, -0.05, 0, 0, 0]
  },
  "sessions": [
    "angle_0_session.json",
    "angle_1_session.json",
    "angle_2_session.json"
  ],
  "position_map": "output/main_tree_200_2024-12-01.json"
}
```

## Implementation Plan

### Phase 1: Basic Pi Control
- [ ] HTTP server on Pi
- [ ] Single LED control API
- [ ] Test with curl/Postman

### Phase 2: Remote Capture
- [ ] Camera interface
- [ ] LED detection (brightest pixel)
- [ ] Pi communication
- [ ] Iterate through all LEDs
- [ ] Save session data

### Phase 3: Multi-Angle Capture
- [ ] Session management
- [ ] Multiple viewing angles
- [ ] Progress tracking
- [ ] Image saving (optional)

### Phase 4: Triangulation
- [ ] Simple triangulation (uncalibrated)
- [ ] 3D position calculation
- [ ] Validation and outlier detection
- [ ] Export to position map JSON

### Phase 5: UI
- [ ] Basic GUI (tkinter/Qt)
- [ ] Camera preview
- [ ] Capture progress
- [ ] 3D visualization
- [ ] Configuration

### Phase 6: Enhancement
- [ ] Camera calibration
- [ ] Full triangulation with calibration
- [ ] Manual LED adjustment
- [ ] Batch processing
- [ ] Quality metrics

## Testing Strategy

1. **Simulated Testing**: Use synthetic images with known LED positions
2. **Single LED**: Test with one LED, multiple angles, verify 3D position
3. **Small Strip**: Test with 10-20 LEDs before full 200
4. **Validation**: Compare calculated positions with manual measurements
5. **Repeatability**: Multiple calibration runs should give similar results

## Dependencies

**Remote Machine:**
- Python 3.7+
- OpenCV (`opencv-python`)
- NumPy
- Requests (for HTTP communication)
- GUI framework (tkinter/PyQt/Pygame)
- Matplotlib (for 3D visualization)

**Raspberry Pi:**
- Python 3.7+
- `rpi_ws281x`
- Flask or FastAPI
- NumPy

## Common Issues

### LED Not Detected
- Check brightness threshold
- Verify LED is actually lighting up
- Check camera exposure (auto-exposure may cause issues)
- Ensure no other bright objects in view

### Poor Triangulation
- Increase number of viewing angles
- Ensure angles are well-separated
- Check for systematic errors in camera position
- Use camera calibration

### Occlusion
- Some LEDs may be impossible to see from certain angles
- Ensure at least 2 clear views per LED
- May need to manually measure occluded LEDs

## Future Enhancements

- Automatic camera movement (pan-tilt mount)
- Video-based capture (extract frames)
- Real-time 3D preview during capture
- Color-based LED identification
- Support for multiple LED strips
- Cloud processing for heavy computation
