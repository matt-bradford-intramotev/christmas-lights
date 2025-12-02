# Position Maps

This directory contains 3D position mapping files for LED installations.

## Files

- `test_linear_50.json` - Simple linear strip for testing (50 LEDs)
- `test_200.json` - To be created for actual 200 LED Christmas tree

## Creating a Position Map

See [../../docs/POSITION_MAPPING.md](../../docs/POSITION_MAPPING.md) for details on the format and creation process.

## Quick Start

1. Copy an existing position map as a template
2. Update the metadata (name, led_count, created date)
3. Measure or calculate your LED positions
4. Fill in the positions array with [x, y, z] coordinates
5. Validate using the visualization tool (when available)

## Coordinate System

- Origin: Base center of tree
- X: Left (-) to Right (+)
- Y: Bottom (-) to Top (+)
- Z: Back (-) to Front (+)
- Units: Meters (by convention)
