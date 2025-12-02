# Pi Calibration Tools

Tools that run on the Raspberry Pi to support camera-based LED position calibration.

## LED Control Server

The LED control server provides an HTTP API for remotely controlling individual LEDs during the calibration process.

### Usage

```bash
# Start server with default settings
sudo python3 led_control_server.py

# Custom port and LED count
sudo python3 led_control_server.py --port 8080 --led-count 200

# Custom GPIO pin
sudo python3 led_control_server.py --led-pin 18
```

Note: `sudo` is required for GPIO access.

### API Endpoints

**Health Check:**
```bash
GET /health
Response: {"status": "healthy", "led_count": 200}
```

**Get Status:**
```bash
GET /status
Response: {"status": "ready", "led_count": 200, "current_led": null}
```

**Turn On LED:**
```bash
POST /led/on
Body: {
  "index": 42,
  "color": [255, 255, 255],  # Optional, default white
  "brightness": 255           # Optional, default 255
}
Response: {"status": "ok", "led_index": 42, "color": [255, 255, 255]}
```

**Turn Off LED:**
```bash
POST /led/off
Body: {"index": 42}
Response: {"status": "ok", "led_index": 42}
```

**Turn Off All LEDs:**
```bash
POST /led/all_off
Response: {"status": "ok", "count": 200}
```

### Testing

Test the server using curl:

```bash
# Check if server is running
curl http://raspberrypi.local:8080/health

# Turn on LED 0 (white)
curl -X POST http://raspberrypi.local:8080/led/on \
  -H "Content-Type: application/json" \
  -d '{"index": 0}'

# Turn on LED 10 (red)
curl -X POST http://raspberrypi.local:8080/led/on \
  -H "Content-Type: application/json" \
  -d '{"index": 10, "color": [255, 0, 0]}'

# Turn off all LEDs
curl -X POST http://raspberrypi.local:8080/led/all_off
```

### Auto-Off Feature

The server automatically turns off all LEDs if no command is received for 60 seconds. This prevents LEDs from being left on accidentally.

### Dependencies

- Python 3.7+
- `rpi_ws281x` library
- Flask (`pip3 install flask`)

Install dependencies:
```bash
pip3 install flask rpi_ws281x
```

## Network Setup

### Finding Pi IP Address

On the Pi:
```bash
hostname -I
```

Or use mDNS (if avahi-daemon is running):
```bash
# From remote machine
ping raspberrypi.local
```

### Firewall

Ensure port 8080 is open:
```bash
sudo ufw allow 8080
```

## Integration with Remote Tools

The remote calibration tools (in `remote/calibration/`) communicate with this server to control LEDs during the calibration process.

See [../../docs/CALIBRATION_SYSTEM.md](../../docs/CALIBRATION_SYSTEM.md) for complete workflow.
