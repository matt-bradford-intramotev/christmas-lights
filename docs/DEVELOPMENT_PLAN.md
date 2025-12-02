# Development Plan

This document outlines the suggested order of implementation for the Christmas Lights project.

## Phase 1: GIFT Foundation

### 1.1 Position Mapping System
- [ ] Create position map JSON schema
- [ ] Write position map validator
- [ ] Create test position maps (procedural generation)
- [ ] Document coordinate system conventions

### 1.2 GIFT File Format
- [ ] Finalize v0.1 specification
- [ ] Create example .gift files
- [ ] Write schema validator
- [ ] Create GIFT file loader class

### 1.3 Basic GIFT Player
- [ ] Implement keyframe parser
- [ ] Implement linear interpolation
- [ ] Integrate with rpi_ws281x hardware control
- [ ] Add timing/synchronization system
- [ ] Test with simple animations

**Deliverable**: Ability to play simple .gift animations on hardware

## Phase 2: Visualization Tool

### 2.1 3D Position Viewer
- [ ] Choose visualization framework (matplotlib/pygame/Qt)
- [ ] Implement 3D LED position rendering
- [ ] Add camera controls (rotate, zoom, pan)
- [ ] Load and display position maps

### 2.2 Animation Preview
- [ ] Integrate GIFT parser
- [ ] Render animation playback in 3D view
- [ ] Add playback controls (play, pause, scrub)
- [ ] Show timeline

### 2.3 GIFT Editor
- [ ] Timeline editor UI
- [ ] Keyframe creation and editing
- [ ] Color picker interface
- [ ] LED selection tools (individual, region, all)
- [ ] Save/export to .gift format

**Deliverable**: Desktop tool for creating and previewing .gift animations

## Phase 3: Remote Control

### 3.1 Pi Service
- [ ] Design control protocol (HTTP/WebSocket/custom)
- [ ] Implement server on Pi
- [ ] API for starting/stopping animations
- [ ] API for listing available .gift files
- [ ] Status reporting

### 3.2 Remote Client
- [ ] CLI tool for remote control
- [ ] File upload capability
- [ ] Animation management (list, start, stop, delete)
- [ ] Status monitoring

### 3.3 Web Interface (Optional)
- [ ] Web-based control panel
- [ ] File browser for .gift files
- [ ] Live preview (if feasible)
- [ ] Animation scheduling

**Deliverable**: Remote control system for Pi from another machine

## Phase 4: Advanced Features

### 4.1 Enhanced Interpolation
- [ ] Ease-in/ease-out functions
- [ ] Bezier curve interpolation
- [ ] Custom interpolation curves

### 4.2 Spatial Effects
- [ ] Wave patterns based on position
- [ ] Particle system
- [ ] Geometric patterns (spheres, planes, etc.)
- [ ] Distance-based effects

### 4.3 Additional Animation Types
- [ ] Function-based animations
- [ ] Procedural effects
- [ ] Animation composition/layering

### 4.4 Sound Reactivity
- [ ] Audio input integration
- [ ] Beat detection
- [ ] Frequency analysis
- [ ] Sound-synchronized animations

**Deliverable**: Advanced animation capabilities

## Phase 5: Polish and Optimization

### 5.1 Performance
- [ ] Profile GIFT player on Pi hardware
- [ ] Optimize critical paths
- [ ] Pre-compile/cache complex calculations
- [ ] Memory usage optimization

### 5.2 Robustness
- [ ] Error handling improvements
- [ ] Recovery from network issues
- [ ] Graceful degradation
- [ ] Extensive testing

### 5.3 Documentation
- [ ] User guide for visualization tool
- [ ] Tutorial for creating .gift files
- [ ] API documentation for remote control
- [ ] Troubleshooting guide

### 5.4 Library of Animations
- [ ] Create collection of example .gift files
- [ ] Classic patterns (twinkle, chase, etc.)
- [ ] Holiday-themed animations
- [ ] Demo animations showcasing features

**Deliverable**: Production-ready system with documentation

## Quick Wins (Can Do Anytime)

- [ ] More standalone pattern scripts
- [ ] LED strip testing utilities
- [ ] Configuration management (LED count, pin, brightness)
- [ ] Systemd service for auto-start
- [ ] Installation/setup scripts
- [ ] Backup/restore for .gift files

## Technical Decisions Needed

Before implementing certain phases, decide on:

1. **Visualization Framework**: matplotlib, pygame, Qt, or web-based?
2. **Remote Protocol**: HTTP REST, WebSocket, gRPC, or custom?
3. **GIFT Format Details**: Finalize initial spec before building player
4. **Python Version**: Minimum version to support?
5. **Dependency Management**: pip, poetry, or conda?

## Testing Strategy

- **Unit Tests**: Parser, interpolation, validation
- **Integration Tests**: Full playback with mock hardware
- **Hardware Tests**: On actual LED strip
- **Performance Tests**: Frame rate, memory usage on Pi Zero 2 W

## Notes

- Start with simplest viable implementation
- Test on hardware early and often
- Keep visualization tool separate from Pi code
- Document as you go
- Prioritize reliability over features
