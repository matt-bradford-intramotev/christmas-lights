# Remote Control Tools

Tools for controlling the Raspberry Pi LED system from a remote machine.

## Status

🚧 **To Be Implemented**

## Planned Features

- Send commands to Pi over network
- Upload .gift files to Pi
- Start/stop animations remotely
- List available animations
- Monitor Pi status
- Schedule animations

## Architecture (Planned)

### Pi Side
- HTTP/WebSocket server running on Pi
- REST API for control commands
- File upload endpoint
- Status reporting

### Remote Side
- CLI tool for remote control
- Python library for programmatic control
- Optional web interface

## Design Considerations

- Network reliability (reconnection, timeouts)
- Authentication/security
- Discovery mechanism (find Pi on network)
- Bandwidth efficiency
- Compatibility with different network configurations

## Example Usage (Conceptual)

```bash
# Upload an animation
lights-remote upload my_animation.gift

# List animations on Pi
lights-remote list

# Play an animation
lights-remote play my_animation.gift

# Stop current animation
lights-remote stop

# Check status
lights-remote status
```

## Documentation

See [../docs/DEVELOPMENT_PLAN.md](../docs/DEVELOPMENT_PLAN.md) for implementation roadmap.
