# GIFT Player

Playback system for GIFT (Geometric Interactive Format for Trees) animation files on Raspberry Pi LED hardware.

## Overview

The GIFT player reads pre-generated animation files and plays them back on WS281x LED strips. It provides:
- Simple frame-by-frame playback
- Speed control
- Looping support
- Graceful shutdown with LED cleanup
- Simulation mode for testing without hardware

## Requirements

### Hardware
- Raspberry Pi (tested on Pi Zero 2 W)
- WS281x LED strip (WS2812B, WS2811, etc.)
- GPIO pin 18 (default, configurable)

### Software
- Python 3.7+
- `rpi_ws281x` library

### Installation

```bash
# Install system dependencies
sudo apt-get update
sudo apt-get install python3-pip

# Install rpi_ws281x
pip3 install rpi_ws281x

# Or build from source for latest version
git clone https://github.com/jgarff/rpi_ws281x.git
cd rpi_ws281x
sudo pip3 install .
```

## Usage

### Basic Playback

```bash
# Play animation (requires sudo for GPIO)
sudo python3 gift_player.py animations/rainbow_bands.gift
```

### Command-Line Options

```bash
# Play at 2x speed
sudo python3 gift_player.py animation.gift --speed 2.0

# Play at half speed (slower, smoother)
sudo python3 gift_player.py animation.gift --speed 0.5

# Play 5 loops then stop
sudo python3 gift_player.py animation.gift --max-loops 5

# Play once (disable looping)
sudo python3 gift_player.py animation.gift --no-loop

# Custom brightness (0-255)
sudo python3 gift_player.py animation.gift --brightness 128

# Different LED count
sudo python3 gift_player.py animation.gift --led-count 350

# Different GPIO pin
sudo python3 gift_player.py animation.gift --led-pin 12
```

### Full Options

```
usage: gift_player.py [-h] [--speed SPEED] [--max-loops MAX_LOOPS]
                      [--no-loop] [--brightness BRIGHTNESS]
                      [--led-count LED_COUNT] [--led-pin LED_PIN]
                      gift_file

Arguments:
  gift_file              GIFT animation file to play

Options:
  --speed SPEED          Speed multiplier (default: 1.0)
  --max-loops MAX_LOOPS  Maximum loops (default: infinite)
  --no-loop              Disable looping (play once)
  --brightness BRIGHTNESS LED brightness 0-255 (default: 255)
  --led-count LED_COUNT  Number of LEDs (default: 200)
  --led-pin LED_PIN      GPIO pin (default: 18)
```

## File Organization

Recommended directory structure:

```
pi/GIFT/
├── gift_player.py          # Player script
├── animations/             # GIFT animation files
│   ├── rainbow_bands.gift
│   ├── sparkle.gift
│   └── ...
└── position_maps/          # LED position data (for reference)
    ├── tree_2024.json
    └── ...
```

## Creating Animations

Animations are created using the GIFT generation tools:

```bash
# On your laptop/desktop (not on Pi)
cd remote/gift-generation

# Create rainbow bands animation
python3 example_rainbow_bands.py position_map.json --output rainbow.gift

# Copy to Pi
scp rainbow.gift pi@<pi_ip>:~/christmas-lights/pi/GIFT/animations/
```

See [remote/gift-generation/README.md](../../remote/gift-generation/README.md) for details on creating custom animations.

## Performance

### Framerate

The player maintains timing by:
1. Recording frame start time
2. Displaying the frame
3. Sleeping for remaining time

**Typical performance:**
- 30 fps: Reliable on Pi Zero 2 W
- 60 fps: Possible for simple animations
- Frame timing accuracy: ±1-2ms

### CPU Usage

- **During playback**: 5-15% on Pi Zero 2 W
- **Idle (waiting)**: <1%
- **CSV parsing**: Brief spike at load time

### Memory Usage

- **Player overhead**: ~10-20 MB
- **Frame data**: ~600 bytes per frame (for 200 LEDs)
- **Example**: 300 frames ≈ 180 KB

## Troubleshooting

### "Permission denied" or GPIO errors

The player needs root access for GPIO control:
```bash
sudo python3 gift_player.py animation.gift
```

### "No frames loaded"

Check that the GIFT file is valid:
- Must be CSV format
- Must have metadata header
- Must have at least one frame row

### Animation too fast/slow

Adjust speed multiplier:
```bash
# Slower
sudo python3 gift_player.py animation.gift --speed 0.5

# Faster
sudo python3 gift_player.py animation.gift --speed 2.0
```

### LEDs stay on after exit

The player includes cleanup handlers for:
- Ctrl+C (SIGINT)
- Kill signal (SIGTERM)
- Normal exit

If LEDs remain on, manually turn them off:
```bash
cd ../standalone
sudo python3 all_off.py
```

### Wrong number of LEDs

Specify LED count:
```bash
sudo python3 gift_player.py animation.gift --led-count 350
```

### Simulation Mode

If `rpi_ws281x` is not installed, the player runs in simulation mode:
- No actual LED output
- Useful for testing file loading and timing
- Shows progress indicators

## Safety Notes

### Brightness Control

- Default brightness: 255 (100%)
- Start with lower brightness for testing: `--brightness 50`
- Full brightness on many LEDs draws significant current
- Ensure adequate power supply

### Power Supply

For 200 LEDs:
- **Peak draw**: ~12A at full white (60mA per LED)
- **Typical draw**: 2-6A for colored animations
- Use appropriate power supply (5V, sufficient amperage)

### Cleanup

The player always turns off LEDs on exit:
- Normal completion
- User interrupt (Ctrl+C)
- Kill signal
- Python exception

## Advanced Usage

### Running at Boot

Create systemd service (`/etc/systemd/system/gift-player.service`):

```ini
[Unit]
Description=GIFT Animation Player
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/home/pi/christmas-lights/pi/GIFT
ExecStart=/usr/bin/python3 gift_player.py animations/default.gift
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable gift-player
sudo systemctl start gift-player
```

### Playlist Mode

Create a simple playlist script:

```bash
#!/bin/bash
# playlist.sh

while true; do
    sudo python3 gift_player.py animations/rainbow.gift --max-loops 2
    sudo python3 gift_player.py animations/sparkle.gift --max-loops 2
    sudo python3 gift_player.py animations/spiral.gift --max-loops 2
done
```

### Remote Control

Combine with network control:
```bash
# Simple HTTP server (separate script)
while true; do
    animation=$(nc -l 8080)
    sudo python3 gift_player.py "animations/${animation}.gift"
done
```

## Development

### Testing Without Hardware

The player detects if `rpi_ws281x` is unavailable and enters simulation mode:

```bash
# On laptop/desktop (no hardware)
python3 gift_player.py test.gift
```

This allows testing:
- File loading
- Frame parsing
- Timing logic
- Playback flow

### Adding Features

Common enhancement ideas:
- Brightness automation (time-based dimming)
- Sound reactive (FFT-based speed control)
- Network control protocol
- Web interface
- Animation transitions/crossfading
- Pattern scheduling

## See Also

- [GIFT Generation Tools](../../remote/gift-generation/README.md) - Create animations
- [GIFT Format Spec](../../docs/GIFT_FORMAT_SPEC.md) - File format details
- [Calibration System](../../remote/calibration/README.md) - Create position maps
- [Standalone Scripts](../standalone/) - Alternative direct control
