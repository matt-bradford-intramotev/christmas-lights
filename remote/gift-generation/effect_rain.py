import numpy as np
import argparse

# Cloud & Lightning
CLOUD_THRESHOLD_Z = 0.4         # Z-level where the cloud starts
CLOUD_COLOR = (220, 220, 220)   # Bright White/Gray
LIGHTNING_CHANCE = 0.4          # Chance of a flash per frame

# Physics
FALL_SPEED = 0.03               # Speed of falling drops
SPAWN_RATE = 0.10               # Drops per frame
DETECTION_RADIUS = 0.07         # Thickness of the drop
DROP_LENGTH = 0.15              # Length of the trail

# Puddle Settings
FLOOR_Z = -0.5              
CEILING_Z = 0.45            

# Colors
RAIN_COLOR = (0, 150, 255)  
PUDDLE_COLOR = (0, 30, 200) 
GLOW_INTENSITY = 0.05       
# -----------------------------

from gift_creator import GIFTCreator

def create_storm_animation(position_map_path, output_path, duration=20, fps=30):
    creator = GIFTCreator(framerate=fps)
    creator.load_position_map(position_map_path)
    num_leds = creator.led_count
    total_frames = int(duration * fps)
    
    active_drops = []
    
    dist_to_travel = CEILING_Z - FLOOR_Z
    puddle_speed = dist_to_travel / total_frames

    print(f"Generating {total_frames} frames for a {duration}s perfect loop...")

    for f in range(total_frames):
        # 1. Update Water Level based on current frame
        water_level = FLOOR_Z + (f * puddle_speed)

        # 2. Spawn Rain Drops from the cloud
        if np.random.random() < SPAWN_RATE:
            active_drops.append([np.random.uniform(-0.4, 0.4), np.random.uniform(-0.4, 0.4), CLOUD_THRESHOLD_Z])

        # 3. Update Drops (Remove if they hit the rising water)
        next_drops = []
        for d in active_drops:
            d[2] -= FALL_SPEED
            if d[2] > water_level:
                next_drops.append(d)
        active_drops = next_drops

        # 4. Lightning Logic
        is_lightning = np.random.random() < LIGHTNING_CHANCE

        # 5. Render LEDs
        frame_colors = []
        for led_id in range(num_leds):
            led_pos = creator.positions[led_id]
            lx, ly, lz = led_pos.x, led_pos.y, led_pos.z
            
            final_r, final_g, final_b = [int(c * GLOW_INTENSITY) for c in RAIN_COLOR]
            
            # CLOUD LAYER
            if lz >= CLOUD_THRESHOLD_Z:
                if is_lightning:
                    final_r, final_g, final_b = (255, 255, 255)
                else:
                    flicker = np.random.uniform(0.8, 1.0)
                    final_r, final_g, final_b = [int(c * flicker) for c in CLOUD_COLOR]

            # PUDDLE LAYER
            elif lz <= water_level:
                if (water_level - lz) < 0.04:
                    final_r, final_g, final_b = (100, 180, 255)
                else:
                    final_r, final_g, final_b = PUDDLE_COLOR
            
            # RAIN LAYER
            else:
                for dx, dy, dz in active_drops:
                    dist_xy = np.sqrt((lx-dx)**2 + (ly-dy)**2)
                    if dist_xy < DETECTION_RADIUS and lz <= dz and lz > (dz - DROP_LENGTH):
                        factor = (1.0 - (dz - lz) / DROP_LENGTH)
                        final_r = max(final_r, int(RAIN_COLOR[0] * factor))
                        final_g = max(final_g, int(RAIN_COLOR[1] * factor))
                        final_b = max(final_b, int(RAIN_COLOR[2] * factor))

            frame_colors.append((final_r, final_g, final_b))
            
        creator.add_frame(frame_colors)

    creator.export(output_path)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("pos_map")
    parser.add_argument("--output", default="effect_rain.gift")
    parser.add_argument("--duration", type=int, default=30)
    args = parser.parse_args()
    create_storm_animation(args.pos_map, args.output, args.duration)