import numpy as np
import argparse
from gift_creator import GIFTCreator

PATTERN_DURATION = 8.0
TRANSITION_TIME = 2.0
PATTERN_SPEED = 0.25

PALETTE = [
    (70, 130, 180),
    (100, 160, 140),
    (140, 100, 160),
    (180, 140, 100),
]

def lerp_color(c1, c2, t):
    t = max(0, min(1, t))
    return tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))

def smoothstep(edge0, edge1, x):
    t = max(0, min(1, (x - edge0) / (edge1 - edge0)))
    return t * t * (3 - 2 * t)

def get_pattern_intensity(pattern, t, angle, radius, z_norm, max_radius):
    intensity = 0
    color_idx = 0

    if pattern == "spiral":
        spiral_arms = 2
        spiral_tightness = 3.0
        spiral_phase = (angle / (2 * np.pi)) + (z_norm * spiral_tightness) - (t * PATTERN_SPEED)
        spiral_phase = spiral_phase % 1.0
        
        for arm in range(spiral_arms):
            arm_phase = (spiral_phase + arm / spiral_arms) % 1.0
            band_dist = min(arm_phase, 1.0 - arm_phase)
            intensity = max(intensity, smoothstep(0.15, 0.0, band_dist))
        
        color_idx = (z_norm * 2 + t * 0.1) % len(PALETTE)
    
    elif pattern == "rings":
        ring_spacing = 0.2
        ring_width = 0.08
        phase = (z_norm - t * PATTERN_SPEED * 0.5) % ring_spacing
        dist_to_ring = min(phase, ring_spacing - phase)
        
        intensity = smoothstep(ring_width, 0.0, dist_to_ring)
        color_idx = (z_norm * 3 - t * 0.2) % len(PALETTE)
    
    elif pattern == "helix":
        helix_speed = 2.0
        strand_width = 0.12
        
        for strand in range(2):
            target_angle = (z_norm * helix_speed * 2 * np.pi) + (strand * np.pi) - (t * PATTERN_SPEED * 2 * np.pi)
            angle_diff = abs(np.arctan2(np.sin(angle - target_angle), np.cos(angle - target_angle)))
            
            strand_intensity = smoothstep(strand_width * np.pi, 0.0, angle_diff)
            strand_intensity *= (radius / max_radius) ** 0.5
            intensity = max(intensity, strand_intensity)
        
        color_idx = (z_norm * 2 + t * 0.15) % len(PALETTE)
    
    elif pattern == "wave":
        wave_freq = 3.0
        wave_amplitude = 0.15
        target_z = 0.5 + wave_amplitude * np.sin(angle * wave_freq - t * PATTERN_SPEED * 2 * np.pi)
        dist = abs(z_norm - target_z)
        
        intensity = smoothstep(0.1, 0.0, dist)
        color_idx = (angle / (2 * np.pi) + t * 0.1) % len(PALETTE)
    
    elif pattern == "drops":
        num_streams = 8
        stream_width = 0.4
        drop_length = 0.25
        
        for s in range(num_streams):
            stream_angle = (s / num_streams) * 2 * np.pi
            angle_diff = abs(np.arctan2(np.sin(angle - stream_angle), np.cos(angle - stream_angle)))
            
            if angle_diff < stream_width:
                drop_phase = (1.0 - z_norm + t * PATTERN_SPEED + s * 0.13) % 1.0
                
                if drop_phase < drop_length:
                    drop_intensity = smoothstep(0.0, drop_length * 0.5, drop_phase)
                    drop_intensity *= smoothstep(drop_length, drop_length * 0.5, drop_phase)
                    drop_intensity *= smoothstep(stream_width, 0.0, angle_diff)
                    intensity = max(intensity, drop_intensity)
        
        color_idx = (t * 0.05) % len(PALETTE)
    
    elif pattern == "pulse":
        pulse_interval = 2.0
        pulse_speed = 0.6
        ring_width = 0.15
        
        for p in range(3):
            pulse_age = (t + p * pulse_interval / 3) % pulse_interval
            pulse_radius = pulse_age * pulse_speed
            
            dist_3d = np.sqrt(radius**2 + (z_norm - 0.5)**2 * 0.5)
            dist_to_pulse = abs(dist_3d - pulse_radius)
            
            pulse_intensity = smoothstep(ring_width, 0.0, dist_to_pulse)
            pulse_intensity *= smoothstep(pulse_speed * pulse_interval, 0.0, pulse_radius)
            intensity = max(intensity, pulse_intensity)
        
        color_idx = (t * 0.2) % len(PALETTE)
    
    return intensity, color_idx

def create_random_patterns(position_map_path, output_path, fps=30, duration=60):
    creator = GIFTCreator(framerate=fps)
    creator.load_position_map(position_map_path)
    num_leds = creator.led_count
    
    positions = [(creator.positions[i].x, creator.positions[i].y, creator.positions[i].z) 
                 for i in range(num_leds)]
    
    z_min = min(p[2] for p in positions)
    z_max = max(p[2] for p in positions)
    z_range = z_max - z_min if z_max > z_min else 1.0
    
    led_data = []
    for lx, ly, lz in positions:
        angle = np.arctan2(ly, lx)
        radius = np.sqrt(lx**2 + ly**2)
        z_norm = (lz - z_min) / z_range
        led_data.append((angle, radius, z_norm))
    
    max_radius = max(d[1] for d in led_data)
    
    all_patterns = ["spiral", "rings", "helix", "wave", "drops", "pulse"]
    
    num_patterns_needed = int(np.ceil(duration / PATTERN_DURATION)) + 1
    pattern_sequence = []
    last_pattern = None
    
    for _ in range(num_patterns_needed):
        available = [p for p in all_patterns if p != last_pattern]
        chosen = np.random.choice(available)
        pattern_sequence.append(chosen)
        last_pattern = chosen
    
    print(f"Pattern sequence: {' → '.join(pattern_sequence[:8])}...")
    
    total_frames = fps * duration
    print(f"Generating {duration}s random patterns ({total_frames} frames)...")

    for frame in range(total_frames):
        t = frame / fps
        
        pattern_idx = t / PATTERN_DURATION
        current_pattern_num = int(pattern_idx)
        time_in_pattern = (pattern_idx - current_pattern_num) * PATTERN_DURATION
        
        current_pattern = pattern_sequence[current_pattern_num % len(pattern_sequence)]
        next_pattern = pattern_sequence[(current_pattern_num + 1) % len(pattern_sequence)]
        
        if time_in_pattern > (PATTERN_DURATION - TRANSITION_TIME):
            blend = (time_in_pattern - (PATTERN_DURATION - TRANSITION_TIME)) / TRANSITION_TIME
            blend = smoothstep(0, 1, blend)
        else:
            blend = 0.0
        
        frame_colors = []
        
        for angle, radius, z_norm in led_data:
            intensity1, color_idx1 = get_pattern_intensity(
                current_pattern, t, angle, radius, z_norm, max_radius)
            
            if blend > 0.01:
                intensity2, color_idx2 = get_pattern_intensity(
                    next_pattern, t, angle, radius, z_norm, max_radius)
                
                intensity = intensity1 * (1 - blend) + intensity2 * blend
                color_idx = color_idx1 * (1 - blend) + color_idx2 * blend
            else:
                intensity = intensity1
                color_idx = color_idx1
            
            if intensity > 0.01:
                idx1 = int(color_idx) % len(PALETTE)
                idx2 = (idx1 + 1) % len(PALETTE)
                color_blend = color_idx - int(color_idx)
                
                base_color = lerp_color(PALETTE[idx1], PALETTE[idx2], color_blend)
                final_r = int(base_color[0] * intensity)
                final_g = int(base_color[1] * intensity)
                final_b = int(base_color[2] * intensity)
            else:
                final_r, final_g, final_b = 0, 0, 0
            
            frame_colors.append((final_r, final_g, final_b))
        
        creator.add_frame(frame_colors)
        
        if frame % (fps * 10) == 0:
            print(f"  {frame // fps}s / {duration}s - {current_pattern}")

    creator.export(output_path)
    print(f"Exported to {output_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("pos_map")
    parser.add_argument("--output", default="effect_random_patterns.gift")
    parser.add_argument("--duration", type=int, default=60)
    parser.add_argument("--fps", type=int, default=30)
    parser.add_argument("--pattern-time", type=float, default=8.0)
    parser.add_argument("--speed", type=float, default=0.25)
    args = parser.parse_args()
    
    PATTERN_SPEED = args.speed
    PATTERN_DURATION = args.pattern_time
    
    create_random_patterns(args.pos_map, args.output, fps=args.fps, duration=args.duration)