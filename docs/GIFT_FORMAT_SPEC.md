# GIFT File Format Specification

**Version**: 0.1.0 (Draft)
**Status**: Design Phase

## Overview

The GIFT (Geometric Interactive Format for Trees) file format defines animations for individually addressable LED lights in 3D space. This specification is under active development.

## Design Goals

- Human-readable and editable
- Support for 3D spatial coordinates
- Keyframe-based animation with interpolation
- Extensible for future features
- Efficient enough for Raspberry Pi Zero 2 W playback

## File Format

GIFT files use JSON format with a `.gift` extension.

### Basic Structure

```json
{
  "version": "0.1.0",
  "metadata": {
    "name": "Sparkle Animation",
    "author": "Your Name",
    "description": "Random sparkling lights",
    "duration": 10.0,
    "fps": 30
  },
  "position_map": "default_tree.json",
  "animation": {
    "type": "keyframe",
    "keyframes": [
      {
        "time": 0.0,
        "lights": [
          {"id": 0, "color": [255, 0, 0], "brightness": 1.0},
          {"id": 1, "color": [0, 255, 0], "brightness": 0.5}
        ]
      },
      {
        "time": 1.0,
        "lights": [
          {"id": 0, "color": [0, 0, 255], "brightness": 0.0},
          {"id": 1, "color": [255, 255, 0], "brightness": 1.0}
        ]
      }
    ],
    "interpolation": "linear"
  }
}
```

## Field Definitions

### Top Level

- `version` (string, required): GIFT format version
- `metadata` (object, required): Animation metadata
- `position_map` (string, required): Path to position mapping file
- `animation` (object, required): Animation definition

### Metadata Object

- `name` (string): Human-readable animation name
- `author` (string): Creator attribution
- `description` (string): Animation description
- `duration` (number): Total animation length in seconds
- `fps` (number): Target frames per second for playback

### Animation Object

- `type` (string): Animation type (currently only "keyframe")
- `keyframes` (array): Array of keyframe objects
- `interpolation` (string): Interpolation method between keyframes
  - `"linear"`: Linear interpolation
  - `"ease"`: Ease in/out
  - `"step"`: No interpolation (instant change)

### Keyframe Object

- `time` (number): Time in seconds from animation start
- `lights` (array): Array of light state objects

### Light State Object

- `id` (number): LED index (0-based)
- `color` (array): RGB color values [R, G, B] (0-255)
- `brightness` (number): Brightness multiplier (0.0-1.0)

## Alternative Format Ideas

### Option 1: Spatial Rules (Future)
Instead of per-LED keyframes, define rules based on position:

```json
{
  "animation": {
    "type": "spatial",
    "rules": [
      {
        "time": 0.0,
        "effect": "wave",
        "parameters": {
          "direction": [0, 0, 1],
          "wavelength": 0.5,
          "speed": 1.0,
          "color": [255, 100, 0]
        }
      }
    ]
  }
}
```

### Option 2: Function-Based (Future)
Define animations using mathematical functions:

```json
{
  "animation": {
    "type": "function",
    "functions": [
      {
        "variable": "brightness",
        "expression": "sin(2*pi*t*freq) * exp(-dist_from_point([0,1,0])/width)",
        "parameters": {"freq": 2.0, "width": 0.3}
      }
    ]
  }
}
```

## Open Questions

1. **Compression**: Should we support compressed keyframe data for large animations?
2. **Embedded vs Referenced**: Should position maps be embeddable in .gift files?
3. **Loop Points**: How to specify repeating sections?
4. **Layers**: Support for multiple simultaneous effects?
5. **Triggers**: Event-based animation changes?
6. **Color Spaces**: Support HSV in addition to RGB?

## Implementation Notes

- Parser should validate version compatibility
- Missing LEDs in keyframes inherit from previous keyframe
- Time values should be sorted; parser may sort on load
- Color values should be clamped to 0-255
- Brightness values should be clamped to 0.0-1.0

## Future Extensions

- Sound synchronization markers
- Interactive triggers (button press, sensor input)
- Multi-strip support
- Animation blending/crossfade
- Procedural generation parameters

## Version History

- **0.1.0** (Draft): Initial specification
