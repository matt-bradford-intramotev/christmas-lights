import numpy as np
import argparse

# Cloud Settings
CLOUD_THRESHOLD_Z = 0.35
CLOUD_COLOR = (150, 150, 150)
LIGHTNING_CHANCE = 0.01
STRIKE_SPEED = 0.08
STRIKE_RADIUS = 0.06

# Physics
FALL_SPEED = 0.02
SPAWN_RATE = 0.08
DETECTION_RADIUS = 0.07
DROP_LENGTH = 0.15

# Puddle Settings
FLOOR_Z = -0.5              
RISE_SPEED = 0.0002          

# Colors
RAIN_COLOR = (0, 150, 255)  
PUDDLE_COLOR = (0, 30, 200) 

from gift_creator import GIFTCreator

def create_storm_animation(position_map_path, output_path, fps=30):
    creator = GIFTCreator(framerate=fps)
    creator.load_position_map(position_map_path)
    num_leds = creator.led_count
    
    active_drops = []
    active_strikes = []
    water_level = FLOOR_Z
    frame_count = 0

    print(f"Generating lightning storm until water reaches {CLOUD_THRESHOLD_Z}...")

    while water_level < CLOUD_THRESHOLD_Z:
        water_level += RISE_SPEED

        # 1. Spawn Lightning Strikes
        if np.random.random() < LIGHTNING_CHANCE:
            active_strikes.append([np.random.uniform(-0.3, 0.3), np.random.uniform(-0.3, 0.3), CLOUD_THRESHOLD_Z])

        # 2. Update Lightning (Move it down)
        next_strikes = []
        for s in active_strikes:
            s[2] -= STRIKE_SPEED
            if s[2] > water_level:
                next_strikes.append(s)
        active_strikes = next_strikes

        # 3. Spawn Rain Drops
        if np.random.random() < SPAWN_RATE:
            active_drops.append([np.random.uniform(-0.4, 0.4), np.random.uniform(-0.4, 0.4), CLOUD_THRESHOLD_Z])

        # 4. Update Drops
        next_drops = []
        for d in active_drops:
            d[2] -= FALL_SPEED
            if d[2] > water_level:
                next_drops.append(d)
        active_drops = next_drops

        # 5. Render LEDs
        frame_colors = []
        for led_id in range(num_leds):
            led_pos = creator.positions[led_id]
            lx, ly, lz = led_pos.x, led_pos.y, led_pos.z
            
            final_r, final_g, final_b = 0, 0, 0 # Default OFF
            
            is_lit_by_bolt = False
            for sx, sy, sz in active_strikes:
                dist_xy = np.sqrt((lx-sx)**2 + (ly-sy)**2)
                if dist_xy < STRIKE_RADIUS and lz > sz and lz < CLOUD_THRESHOLD_Z:
                    final_r, final_g, final_b = (255, 255, 255)
                    is_lit_by_bolt = True
                    break
            
            if is_lit_by_bolt:
                frame_colors.append((final_r, final_g, final_b))
                continue

            # --- CLOUD LAYER ---
            if lz >= CLOUD_THRESHOLD_Z:
                if len(active_strikes) > 0:
                    flicker = np.random.uniform(0.7, 1.0)
                    final_r, final_g, final_b = [int(c * flicker * 1.5) for c in CLOUD_COLOR]
                else:
                    flicker = np.random.uniform(0.4, 0.6)
                    final_r, final_g, final_b = [int(c * flicker) for c in CLOUD_COLOR]

            # --- PUDDLE LAYER ---
            elif lz <= water_level:
                if (water_level - lz) < 0.04:
                    final_r, final_g, final_b = (100, 180, 255)
                else:
                    final_r, final_g, final_b = PUDDLE_COLOR
            
            # --- RAIN LAYER ---
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
        frame_count += 1

    creator.export(output_path)
    print(f"Exported {frame_count} frames.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("pos_map")
    parser.add_argument("--output", default="effect_rain.gift")
    args = parser.parse_args()
    create_storm_animation(args.pos_map, args.output)