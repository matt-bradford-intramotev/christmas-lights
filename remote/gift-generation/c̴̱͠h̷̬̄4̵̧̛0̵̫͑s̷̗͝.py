import numpy as np
import argparse
import random
import math
from gift_creator import GIFTCreator

FPS = 20
DURATION_SECONDS = 30
CHAOS_LEVEL = 3.0

COLORS = {
    'toxic_green': (10, 255, 10),
    'cyber_green': (0, 255, 50),
    'dark_green': (0, 100, 0),
    'bright_lime': (50, 255, 0),
    'pale_green': (150, 255, 150),
    'matrix_green': (0, 200, 20),
    'forest_green': (0, 60, 0),
    'neon_green': (0, 255, 0),
    'faded_green': (40, 120, 40),
    'radioactive': (80, 255, 0),
    'deep_green': (0, 40, 0),
    'flash_green': (200, 255, 200),
}

ALL_COLORS = list(COLORS.values())
BG_COLOR = (0, 20, 0)

class EffectScheduler:
    def __init__(self, total_frames):
        self.total_frames = total_frames
        self.current_effect = None
        self.effect_end_frame = 0
        self.cooldown_until = 0
        self.effects = [
            ('chaos_wave', 25, 50),
            ('data_streams', 30, 60),
            ('glitch_blocks', 20, 45),
            ('explosion', 15, 30),
            ('strobe_burst', 8, 18),
            ('screen_tear', 12, 28),
            ('scanline_sweep', 25, 50),
            ('bit_crush', 20, 40),
            ('color_corrupt', 25, 50),
            ('static_takeover', 15, 35),
            ('rainbow_glitch', 25, 45),
            ('binary_flash', 20, 40),
            ('seizure_mode', 10, 20),
            ('corrupt_cascade', 25, 50),
            ('digital_meltdown', 20, 40),
            ('hack_attack', 30, 60),
        ]
    
    def get_active_effect(self, frame):
        if self.current_effect and frame < self.effect_end_frame:
            return self.current_effect
        
        if frame < self.cooldown_until:
            return None
        
        effect_name, min_dur, max_dur = random.choice(self.effects)
        duration = random.randint(min_dur, max_dur)
        
        self.current_effect = effect_name
        self.effect_end_frame = frame + duration
        self.cooldown_until = self.effect_end_frame + random.randint(5, 15)
        
        return self.current_effect

class GlobalChaos:
    def __init__(self):
        self.interference_active = False
        self.interference_type = None
        self.interference_frames = 0
        
    def update(self, frame):
        if not self.interference_active and random.random() < 0.08 * CHAOS_LEVEL:
            self.interference_active = True
            self.interference_type = random.choice([
                'color_spike', 'random_pixels', 'brightness_surge', 
                'dim_surge', 'invert_flash', 'white_noise_burst'
            ])
            self.interference_frames = random.randint(2, 8)
        
        if self.interference_active:
            self.interference_frames -= 1
            if self.interference_frames <= 0:
                self.interference_active = False
    
    def apply(self, colors, positions, frame, t):
        result = []
        for i, (r, g, b) in enumerate(colors):
            if random.random() < 0.03 * CHAOS_LEVEL:
                pop_color = random.choice(ALL_COLORS)
                r = int(r * 0.3 + pop_color[0] * 0.7)
                g = int(g * 0.3 + pop_color[1] * 0.7)
                b = int(b * 0.3 + pop_color[2] * 0.7)
            
            if random.random() < 0.005 * CHAOS_LEVEL:
                r, g, b = 0, 0, 0
            
            if random.random() < 0.005 * CHAOS_LEVEL:
                r, g, b = 200, 255, 200
            
            result.append((r, g, b))
        
        if self.interference_active:
            result = self._apply_interference(result, positions, frame, t)
        
        return result
    
    def _apply_interference(self, colors, positions, frame, t):
        result = []
        for i, (r, g, b) in enumerate(colors):
            if self.interference_type == 'color_spike':
                spike_color = random.choice(ALL_COLORS)
                r = int(r * 0.5 + spike_color[0] * 0.5)
                g = int(g * 0.5 + spike_color[1] * 0.5)
                b = int(b * 0.5 + spike_color[2] * 0.5)
            
            elif self.interference_type == 'random_pixels':
                if random.random() < 0.4:
                    r = 0
                    g = random.randint(0, 255)
                    b = 0
            
            elif self.interference_type == 'brightness_surge':
                mult = random.uniform(1.5, 3.0)
                r = min(255, int(r * mult))
                g = min(255, int(g * mult))
                b = min(255, int(b * mult))
            
            elif self.interference_type == 'dim_surge':
                r, g, b = 0, int(g * 0.2), 0
            
            elif self.interference_type == 'invert_flash':
                r, g, b = 0, 255 - g, 0
            
            elif self.interference_type == 'white_noise_burst':
                noise = random.randint(-100, 100)
                r = 0
                g = max(0, min(255, g + noise))
                b = 0
            
            result.append((r, g, b))
        
        return result

def render_idle(positions, frame, t):
    colors = []
    for i, led in enumerate(positions):
        pulse = 0.3 + 0.2 * math.sin(t * 3 + led.z * 3)
        
        if random.random() < 0.04 * CHAOS_LEVEL:
            pulse += random.uniform(0.3, 0.8)
        
        if random.random() < 0.02 * CHAOS_LEVEL:
            glitch_color = random.choice(ALL_COLORS)
            colors.append((
                int(glitch_color[0] * pulse),
                int(glitch_color[1] * pulse),
                int(glitch_color[2] * pulse)
            ))
        else:
            colors.append((
                int(BG_COLOR[0] * pulse),
                int(BG_COLOR[1] * pulse),
                int(BG_COLOR[2] * pulse)
            ))
    return colors

def render_chaos_wave(positions, frame, t, bounds, state):
    colors = []
    min_z, max_z = bounds['min_z'], bounds['max_z']
    
    if 'waves' not in state:
        state['waves'] = []
    
    if random.random() < 0.25 * CHAOS_LEVEL:
        state['waves'].append({
            'origin_z': random.uniform(min_z, max_z),
            'radius': 0,
            'color': random.choice(ALL_COLORS),
            'speed': random.uniform(1.0, 3.0),
            'thickness': random.uniform(0.08, 0.3),
            'type': random.choice(['ring', 'pulse', 'solid'])
        })
    
    for wave in state['waves']:
        wave['radius'] += wave['speed'] / FPS
        if random.random() < 0.05:
            wave['color'] = random.choice(ALL_COLORS)
    state['waves'] = [w for w in state['waves'] if w['radius'] < 2.5]
    
    for i, led in enumerate(positions):
        r, g, b = 0, 0, 0
        
        for wave in state['waves']:
            dist = abs(led.z - wave['origin_z'])
            
            if wave['type'] == 'ring':
                ring_dist = abs(dist - wave['radius'])
                if ring_dist < wave['thickness']:
                    intensity = 1.0 - (ring_dist / wave['thickness'])
                    intensity *= max(0.2, 1.0 - wave['radius'] / 2.0)
                    r = int(r + wave['color'][0] * intensity)
                    g = int(g + wave['color'][1] * intensity)
                    b = int(b + wave['color'][2] * intensity)
            
            elif wave['type'] == 'pulse':
                pulse_val = math.sin(dist * 15 - wave['radius'] * 8) * 0.5 + 0.5
                if dist < wave['radius']:
                    intensity = pulse_val * max(0.2, 1.0 - wave['radius'] / 2.0)
                    r = int(r + wave['color'][0] * intensity * 0.7)
                    g = int(g + wave['color'][1] * intensity * 0.7)
                    b = int(b + wave['color'][2] * intensity * 0.7)
            
            elif wave['type'] == 'solid':
                if dist < wave['radius']:
                    intensity = 0.8 * max(0.2, 1.0 - wave['radius'] / 2.0)
                    r = int(r + wave['color'][0] * intensity)
                    g = int(g + wave['color'][1] * intensity)
                    b = int(b + wave['color'][2] * intensity)
        
        colors.append((min(255, r), min(255, g), min(255, b)))
    
    return colors

def render_data_streams(positions, frame, t, bounds, state):
    colors = []
    
    if 'streams' not in state:
        state['streams'] = []
        state['sparks'] = []
    
    for _ in range(int(2 * CHAOS_LEVEL)):
        if random.random() < 0.3:
            state['streams'].append({
                'x': random.uniform(bounds['min_x'], bounds['max_x']),
                'y': random.uniform(bounds['min_y'], bounds['max_y']),
                'z': bounds['max_z'] if random.random() < 0.5 else bounds['min_z'],
                'dir': -1 if random.random() < 0.5 else 1,
                'speed': random.uniform(2.0, 5.0),
                'length': random.uniform(0.3, 1.0),
                'color': random.choice(ALL_COLORS),
                'width': random.uniform(0.08, 0.2)
            })
    
    for s in state['streams']:
        s['z'] += s['dir'] * s['speed'] / FPS
        if random.random() < 0.1:
            state['sparks'].append({
                'x': s['x'] + random.uniform(-0.1, 0.1),
                'y': s['y'] + random.uniform(-0.1, 0.1),
                'z': s['z'],
                'vx': random.uniform(-0.5, 0.5),
                'vy': random.uniform(-0.5, 0.5),
                'vz': random.uniform(-0.5, 0.5),
                'color': s['color'],
                'life': random.randint(5, 15)
            })
    
    state['streams'] = [s for s in state['streams'] 
                        if bounds['min_z'] - 1 < s['z'] < bounds['max_z'] + 1]
    
    for spark in state['sparks']:
        spark['x'] += spark['vx'] / FPS
        spark['y'] += spark['vy'] / FPS
        spark['z'] += spark['vz'] / FPS
        spark['life'] -= 1
    state['sparks'] = [s for s in state['sparks'] if s['life'] > 0]
    
    for i, led in enumerate(positions):
        r, g, b = int(BG_COLOR[0] * 0.3), int(BG_COLOR[1] * 0.3), int(BG_COLOR[2] * 0.3)
        
        for s in state['streams']:
            dist_xy = math.sqrt((led.x - s['x'])**2 + (led.y - s['y'])**2)
            if dist_xy < s['width']:
                if s['dir'] > 0:
                    in_trail = s['z'] - s['length'] < led.z < s['z']
                else:
                    in_trail = s['z'] < led.z < s['z'] + s['length']
                
                if in_trail:
                    dist_from_head = abs(led.z - s['z'])
                    intensity = 1.0 - (dist_from_head / s['length'])
                    intensity *= (1.0 - dist_xy / s['width'])
                    flicker = 0.6 + 0.4 * random.random()
                    intensity *= flicker
                    
                    if dist_from_head < 0.05:
                        r = min(255, r + int(200 * intensity))
                        g = min(255, g + int(255 * intensity))
                        b = min(255, b + int(200 * intensity))
                    else:
                        r = int(r + s['color'][0] * intensity)
                        g = int(g + s['color'][1] * intensity)
                        b = int(b + s['color'][2] * intensity)
        
        for spark in state['sparks']:
            dist = math.sqrt((led.x - spark['x'])**2 + (led.y - spark['y'])**2 + (led.z - spark['z'])**2)
            if dist < 0.1:
                intensity = (1.0 - dist / 0.1) * (spark['life'] / 15)
                r = min(255, r + int(spark['color'][0] * intensity))
                g = min(255, g + int(spark['color'][1] * intensity))
                b = min(255, b + int(spark['color'][2] * intensity))
        
        colors.append((min(255, r), min(255, g), min(255, b)))
    
    return colors

def render_glitch_blocks(positions, frame, t, bounds, state):
    colors = []
    
    if 'blocks' not in state:
        state['blocks'] = []
    
    for _ in range(int(2 * CHAOS_LEVEL)):
        if random.random() < 0.2:
            state['blocks'].append({
                'x': random.uniform(bounds['min_x'], bounds['max_x']),
                'y': random.uniform(bounds['min_y'], bounds['max_y']),
                'z': random.uniform(bounds['min_z'], bounds['max_z']),
                'size': random.uniform(0.1, 0.5),
                'life': random.randint(5, 30),
                'type': random.choice(['solid', 'noise', 'invert', 'strobe', 'rainbow', 'static', 'plasma', 'seizure']),
                'color': random.choice(ALL_COLORS),
                'phase': random.random() * math.pi * 2
            })
    
    for b in state['blocks']:
        b['life'] -= 1
        b['phase'] += 0.3
    state['blocks'] = [b for b in state['blocks'] if b['life'] > 0]
    
    for i, led in enumerate(positions):
        r, g, b = BG_COLOR
        
        for block in state['blocks']:
            if (abs(led.x - block['x']) < block['size'] and
                abs(led.y - block['y']) < block['size'] and
                abs(led.z - block['z']) < block['size']):
                
                if block['type'] == 'solid':
                    r, g, b = block['color']
                elif block['type'] == 'noise':
                    r, b = 0, 0
                    g = random.randint(0, 255)
                elif block['type'] == 'invert':
                    r, b = 0, 0
                    g = 255 - g
                elif block['type'] == 'strobe':
                    if frame % 2 == 0:
                        r, g, b = block['color']
                    else:
                        r, g, b = 0, 0, 0
                elif block['type'] == 'rainbow':
                    val = (block['phase'] + led.z) % 1.0
                    r, b = 0, 0
                    g = int(127 + 127 * math.sin(val * math.pi * 2))
                elif block['type'] == 'static':
                    val = random.randint(0, 255)
                    r, b = 0, 0
                    g = val
                elif block['type'] == 'plasma':
                    val = math.sin(led.x * 10 + block['phase']) * math.cos(led.z * 10 + block['phase'])
                    r, b = 0, 0
                    g = int(127 + 127 * val)
                elif block['type'] == 'seizure':
                    r, b = 0, 0
                    g = random.randint(0, 255)
                break
        
        colors.append((max(0, min(255, r)), max(0, min(255, g)), max(0, min(255, b))))
    
    return colors

def render_explosion(positions, frame, t, bounds, state):
    colors = []
    
    if 'explosions' not in state:
        state['explosions'] = []
    
    if len(state['explosions']) < 3 or random.random() < 0.15 * CHAOS_LEVEL:
        idx = random.randint(0, len(positions) - 1)
        p = positions[idx]
        state['explosions'].append({
            'x': p.x, 'y': p.y, 'z': p.z,
            'radius': 0,
            'max_radius': random.uniform(0.6, 1.8),
            'speed': random.uniform(2.0, 4.0),
            'color': random.choice([COLORS['toxic_green'], COLORS['bright_lime'], COLORS['flash_green'], COLORS['radioactive']]),
            'ring_color': random.choice(ALL_COLORS),
            'spawn_children': random.random() < 0.3
        })
    
    new_explosions = []
    for e in state['explosions']:
        e['radius'] += e['speed'] / FPS
        
        if e['spawn_children'] and e['radius'] > e['max_radius'] * 0.7 and random.random() < 0.2:
            angle = random.random() * math.pi * 2
            new_explosions.append({
                'x': e['x'] + math.cos(angle) * e['radius'] * 0.5,
                'y': e['y'] + math.sin(angle) * e['radius'] * 0.5,
                'z': e['z'] + random.uniform(-0.2, 0.2),
                'radius': 0,
                'max_radius': e['max_radius'] * 0.6,
                'speed': e['speed'] * 1.2,
                'color': random.choice(ALL_COLORS),
                'ring_color': random.choice(ALL_COLORS),
                'spawn_children': False
            })
            e['spawn_children'] = False
    
    state['explosions'].extend(new_explosions)
    state['explosions'] = [e for e in state['explosions'] if e['radius'] < e['max_radius']]
    
    for i, led in enumerate(positions):
        r, g, b = 0, 0, 0
        
        for exp in state['explosions']:
            dist = math.sqrt((led.x - exp['x'])**2 + (led.y - exp['y'])**2 + (led.z - exp['z'])**2)
            progress = exp['radius'] / exp['max_radius']
            
            ring_width = 0.12
            ring_dist = abs(dist - exp['radius'])
            if ring_dist < ring_width:
                intensity = (1.0 - ring_dist / ring_width) * (1.0 - progress)
                r = int(r + exp['ring_color'][0] * intensity)
                g = int(g + exp['ring_color'][1] * intensity)
                b = int(b + exp['ring_color'][2] * intensity)
            
            if dist < exp['radius'] * 0.9:
                inner_intensity = 0.5 * (1.0 - progress) * (1.0 - dist / (exp['radius'] + 0.01))
                r = int(r + exp['color'][0] * inner_intensity)
                g = int(g + exp['color'][1] * inner_intensity)
                b = int(b + exp['color'][2] * inner_intensity)
            
            if dist < 0.15 and progress < 0.3:
                core_intensity = 1.0 - progress / 0.3
                r = min(255, r + int(255 * core_intensity))
                g = min(255, g + int(255 * core_intensity))
                b = min(255, b + int(255 * core_intensity))
        
        colors.append((min(255, r), min(255, g), min(255, b)))
    
    return colors

def render_strobe_burst(positions, frame, t, bounds, state):
    colors = []
    
    if 'patterns' not in state:
        state['patterns'] = [
            {'type': random.choice(['full', 'alternate', 'wave', 'random', 'zones']), 
             'color': random.choice(ALL_COLORS)}
            for _ in range(3)
        ]
    
    if random.random() < 0.1:
        idx = random.randint(0, len(state['patterns']) - 1)
        state['patterns'][idx] = {
            'type': random.choice(['full', 'alternate', 'wave', 'random', 'zones']),
            'color': random.choice(ALL_COLORS)
        }
    
    z_range = bounds['max_z'] - bounds['min_z']
    
    for i, led in enumerate(positions):
        r, g, b = 0, 0, 0
        
        for pattern in state['patterns']:
            on = False
            
            if pattern['type'] == 'full':
                on = frame % 2 == 0
            elif pattern['type'] == 'alternate':
                on = (i + frame) % 2 == 0
            elif pattern['type'] == 'wave':
                wave_pos = ((t * 8) % 2.0) - 0.5
                normalized_z = (led.z - bounds['min_z']) / z_range
                on = abs(normalized_z - wave_pos) < 0.15
            elif pattern['type'] == 'random':
                on = random.random() < 0.5
            elif pattern['type'] == 'zones':
                zone = int((led.z - bounds['min_z']) / z_range * 4)
                on = (zone + frame) % 2 == 0
            
            if on:
                r = min(255, r + pattern['color'][0] // 2)
                g = min(255, g + pattern['color'][1] // 2)
                b = min(255, b + pattern['color'][2] // 2)
        
        colors.append((r, g, b))
    
    return colors

def render_screen_tear(positions, frame, t, bounds, state):
    colors = []
    
    if 'tears' not in state:
        state['tears'] = []
    
    if random.random() < 0.2 * CHAOS_LEVEL:
        state['tears'].append({
            'z': random.uniform(bounds['min_z'], bounds['max_z']),
            'height': random.uniform(0.05, 0.25),
            'offset': random.uniform(80, 200) * random.choice([-1, 1]),
            'life': random.randint(3, 15),
            'mode': random.choice(['add', 'sub', 'replace'])
        })
    
    for tear in state['tears']:
        tear['life'] -= 1
        tear['z'] += random.uniform(-0.05, 0.05)
        tear['offset'] += random.uniform(-20, 20)
    state['tears'] = [t for t in state['tears'] if t['life'] > 0]
    
    z_range = bounds['max_z'] - bounds['min_z']
    
    for i, led in enumerate(positions):
        normalized_z = (led.z - bounds['min_z']) / z_range
        
        r = int(COLORS['forest_green'][0] * normalized_z * 0.5)
        g = int(COLORS['forest_green'][1] * normalized_z * 0.5)
        b = int(COLORS['forest_green'][2] * normalized_z * 0.3)
        
        for tear in state['tears']:
            if abs(led.z - tear['z']) < tear['height']:
                offset = int(tear['offset'])
                
                if tear['mode'] == 'add':
                    g = min(255, g + abs(offset))
                elif tear['mode'] == 'sub':
                    g = max(0, g - abs(offset))
                elif tear['mode'] == 'replace':
                    g = abs(offset) % 255
                
                edge_dist = abs(abs(led.z - tear['z']) - tear['height'])
                if edge_dist < 0.02:
                    r, g, b = 150, 255, 150
        
        colors.append((max(0, min(255, r)), max(0, min(255, g)), max(0, min(255, b))))
    
    return colors

def render_scanline_sweep(positions, frame, t, bounds, state):
    colors = []
    
    if 'scanlines' not in state:
        state['scanlines'] = [
            {'z': bounds['min_z'], 'dir': 1, 'speed': 1.5, 'color': COLORS['cyber_green'], 'thickness': 0.08},
            {'z': bounds['max_z'], 'dir': -1, 'speed': 2.0, 'color': COLORS['toxic_green'], 'thickness': 0.06},
            {'z': (bounds['min_z'] + bounds['max_z']) / 2, 'dir': 1, 'speed': 2.5, 'color': COLORS['neon_green'], 'thickness': 0.1},
        ]
    
    for sl in state['scanlines']:
        sl['z'] += sl['dir'] * sl['speed'] / FPS
        if sl['z'] > bounds['max_z']:
            sl['dir'] = -1
            sl['color'] = random.choice(ALL_COLORS)
        elif sl['z'] < bounds['min_z']:
            sl['dir'] = 1
            sl['color'] = random.choice(ALL_COLORS)
    
    for i, led in enumerate(positions):
        r, g, b = int(BG_COLOR[0] * 0.5), int(BG_COLOR[1] * 0.5), int(BG_COLOR[2] * 0.5)
        
        for sl in state['scanlines']:
            dist = abs(led.z - sl['z'])
            
            if dist < sl['thickness']:
                intensity = 1.0 - (dist / sl['thickness'])
                r = min(255, r + int(sl['color'][0] * intensity))
                g = min(255, g + int(sl['color'][1] * intensity))
                b = min(255, b + int(sl['color'][2] * intensity))
            
            trail_dist = (sl['z'] - led.z) * sl['dir']
            if 0 < trail_dist < 0.3:
                trail_intensity = 0.5 * (1.0 - trail_dist / 0.3)
                r = min(255, r + int(sl['color'][0] * trail_intensity))
                g = min(255, g + int(sl['color'][1] * trail_intensity))
                b = min(255, b + int(sl['color'][2] * trail_intensity))
        
        if int(led.z * 40 + t * 10) % 3 == 0:
            r = int(r * 0.6)
            g = int(g * 0.6)
            b = int(b * 0.6)
        
        colors.append((r, g, b))
    
    return colors

def render_bit_crush(positions, frame, t, bounds, state):
    colors = []
    
    if 'bit_depth' not in state:
        state['bit_depth'] = 2
        state['base_colors'] = [random.choice(ALL_COLORS) for _ in range(4)]
        state['transition'] = 0
    
    if random.random() < 0.1:
        state['bit_depth'] = random.choice([2, 3, 4, 6, 8])
    
    state['transition'] = (state['transition'] + 0.05) % 1.0
    if random.random() < 0.02:
        state['base_colors'][random.randint(0, 3)] = random.choice(ALL_COLORS)
    
    levels = state['bit_depth']
    z_range = bounds['max_z'] - bounds['min_z']
    
    for i, led in enumerate(positions):
        normalized_z = (led.z - bounds['min_z']) / z_range
        quantized = int(normalized_z * levels) / levels
        
        color_idx = int(quantized * 3.99)
        base_color = state['base_colors'][color_idx]
        
        r = int(base_color[0] * (0.3 + quantized * 0.7))
        g = int(base_color[1] * (0.3 + quantized * 0.7))
        b = int(base_color[2] * (0.3 + quantized * 0.7))
        
        boundary_dist = abs(normalized_z * levels - round(normalized_z * levels))
        if boundary_dist < 0.1 and random.random() < 0.3:
            r = min(255, r + random.randint(0, 50))
            g = min(255, g + random.randint(50, 150))
            b = min(255, b + random.randint(0, 50))
        
        colors.append((r, g, b))
    
    return colors

def render_color_corrupt(positions, frame, t, bounds, state):
    colors = []
    
    if 'zones' not in state:
        state['zones'] = []
    
    if random.random() < 0.15 * CHAOS_LEVEL:
        state['zones'].append({
            'z': random.uniform(bounds['min_z'], bounds['max_z']),
            'height': random.uniform(0.1, 0.4),
            'effect': random.choice(['dim', 'brighten', 'noise', 'blackout']),
            'life': random.randint(10, 35),
            'intensity': random.uniform(0.5, 1.0)
        })
    
    for zone in state['zones']:
        zone['life'] -= 1
    state['zones'] = [z for z in state['zones'] if z['life'] > 0]
    
    z_range = bounds['max_z'] - bounds['min_z']
    
    for i, led in enumerate(positions):
        normalized_z = (led.z - bounds['min_z']) / z_range
        
        hue_val = (normalized_z + t * 0.2) % 1.0
        r, b = 0, 0
        g = int(100 + 155 * math.sin(hue_val * math.pi * 2))
        
        for zone in state['zones']:
            if abs(led.z - zone['z']) < zone['height']:
                if zone['effect'] == 'dim':
                    g = int(g * 0.3)
                elif zone['effect'] == 'brighten':
                    g = min(255, int(g * 1.5))
                elif zone['effect'] == 'noise':
                    g = random.randint(0, 255)
                elif zone['effect'] == 'blackout':
                    g = 0
        
        colors.append((max(0, min(255, r)), max(0, min(255, g)), max(0, min(255, b))))
    
    return colors

def render_static_takeover(positions, frame, t, bounds, state):
    colors = []
    
    if 'fronts' not in state:
        state['fronts'] = [
            {'z': bounds['min_z'], 'dir': 1, 'speed': random.uniform(1, 2)},
            {'z': bounds['max_z'], 'dir': -1, 'speed': random.uniform(1, 2)},
        ]
        state['static_color'] = random.choice(ALL_COLORS)
    
    for front in state['fronts']:
        front['z'] += front['dir'] * front['speed'] / FPS
        front['z'] += random.uniform(-0.05, 0.05)
        
        if front['z'] > bounds['max_z']:
            front['dir'] = -1
            state['static_color'] = random.choice(ALL_COLORS)
        elif front['z'] < bounds['min_z']:
            front['dir'] = 1
            state['static_color'] = random.choice(ALL_COLORS)
    
    for i, led in enumerate(positions):
        in_static = any(
            (led.z < front['z'] if front['dir'] > 0 else led.z > front['z'])
            for front in state['fronts']
        )
        
        if in_static:
            val = random.randint(50, 255)
            r = int(val * state['static_color'][0] / 255)
            g = int(val * state['static_color'][1] / 255)
            b = int(val * state['static_color'][2] / 255)
        else:
            r, g, b = BG_COLOR
        
        for front in state['fronts']:
            if abs(led.z - front['z']) < 0.08:
                edge_intensity = 1.0 - abs(led.z - front['z']) / 0.08
                r = min(255, r + int(200 * edge_intensity))
                g = min(255, g + int(200 * edge_intensity))
                b = min(255, b + int(200 * edge_intensity))
        
        colors.append((r, g, b))
    
    return colors

def render_rainbow_glitch(positions, frame, t, bounds, state):
    colors = []
    
    if 'offset' not in state:
        state['offset'] = 0
        state['glitch_zones'] = []
    
    if random.random() < 0.15:
        state['offset'] = random.uniform(-2, 2)
    else:
        state['offset'] *= 0.85
    
    if random.random() < 0.1:
        state['glitch_zones'].append({
            'z': random.uniform(bounds['min_z'], bounds['max_z']),
            'height': random.uniform(0.1, 0.3),
            'type': random.choice(['invert', 'freeze', 'noise', 'shift']),
            'life': random.randint(5, 20)
        })
    
    for zone in state['glitch_zones']:
        zone['life'] -= 1
    state['glitch_zones'] = [z for z in state['glitch_zones'] if z['life'] > 0]
    
    z_range = bounds['max_z'] - bounds['min_z']
    
    for i, led in enumerate(positions):
        normalized_z = (led.z - bounds['min_z']) / z_range
        val = (normalized_z + t * 0.5 + state['offset']) % 1.0
        
        r, b = 0, 0
        g = int(255 * (0.5 + 0.5 * math.sin(val * math.pi * 4)))
        
        for zone in state['glitch_zones']:
            if abs(led.z - zone['z']) < zone['height']:
                if zone['type'] == 'invert':
                    g = 255 - g
                elif zone['type'] == 'freeze':
                    g = 128
                elif zone['type'] == 'noise':
                    g = random.randint(0, 255)
                elif zone['type'] == 'shift':
                    g = (g + 128) % 256
        
        if random.random() < 0.05:
            r, g, b = 0, random.randint(0, 255), 0
        
        colors.append((r, g, b))
    
    return colors

def render_binary_flash(positions, frame, t, bounds, state):
    colors = []
    
    if 'patterns' not in state:
        state['patterns'] = [random.choice([0, 1]) for _ in range(len(positions))]
        state['color_on'] = random.choice(ALL_COLORS)
        state['color_off'] = (0, 0, 0)
    
    if frame % 3 == 0:
        shift = random.randint(1, 10)
        state['patterns'] = state['patterns'][shift:] + state['patterns'][:shift]
        
        for _ in range(len(positions) // 5):
            idx = random.randint(0, len(positions) - 1)
            state['patterns'][idx] = 1 - state['patterns'][idx]
        
        if random.random() < 0.2:
            state['color_on'] = random.choice(ALL_COLORS)
    
    for i, led in enumerate(positions):
        if state['patterns'][i % len(state['patterns'])]:
            colors.append(state['color_on'])
        else:
            colors.append(state['color_off'])
    
    return colors

def render_seizure_mode(positions, frame, t, bounds, state):
    colors = []
    
    if 'mode' not in state:
        state['mode'] = 'full_random'
        state['mode_frames'] = 10
    
    state['mode_frames'] -= 1
    if state['mode_frames'] <= 0:
        state['mode'] = random.choice(['full_random', 'color_flash', 'strobe_random', 'zone_chaos'])
        state['mode_frames'] = random.randint(5, 15)
        state['current_color'] = random.choice(ALL_COLORS)
    
    z_range = bounds['max_z'] - bounds['min_z']
    
    for i, led in enumerate(positions):
        if state['mode'] == 'full_random':
            r, b = 0, 0
            g = random.randint(0, 255)
        
        elif state['mode'] == 'color_flash':
            if frame % 2 == 0:
                r, g, b = state['current_color']
            else:
                r, g, b = 0, 0, 0
        
        elif state['mode'] == 'strobe_random':
            if random.random() < 0.5:
                r, g, b = random.choice(ALL_COLORS)
            else:
                r, g, b = 0, 0, 0
        
        elif state['mode'] == 'zone_chaos':
            zone = int((led.z - bounds['min_z']) / z_range * 5)
            if (zone + frame) % 2 == 0:
                r, g, b = random.choice(ALL_COLORS)
            else:
                r, g, b = 0, 0, 0
        
        else:
            r, g, b = 150, 255, 150
        
        colors.append((r, g, b))
    
    return colors

def render_corrupt_cascade(positions, frame, t, bounds, state):
    colors = []
    
    if 'corruption_center' not in state:
        idx = random.randint(0, len(positions) - 1)
        p = positions[idx]
        state['corruption_center'] = (p.x, p.y, p.z)
        state['corruption_radius'] = 0
        state['corruption_type'] = random.choice(['noise', 'color', 'invert'])
        state['base_color'] = random.choice(ALL_COLORS)
    
    state['corruption_radius'] += 1.5 / FPS
    
    if random.random() < 0.03:
        idx = random.randint(0, len(positions) - 1)
        p = positions[idx]
        state['corruption_center'] = (p.x, p.y, p.z)
        state['corruption_radius'] = 0
        state['corruption_type'] = random.choice(['noise', 'color', 'invert'])
        state['base_color'] = random.choice(ALL_COLORS)
    
    cx, cy, cz = state['corruption_center']
    
    for i, led in enumerate(positions):
        dist = math.sqrt((led.x - cx)**2 + (led.y - cy)**2 + (led.z - cz)**2)
        
        if dist < state['corruption_radius']:
            if state['corruption_type'] == 'noise':
                r, b = 0, 0
                g = random.randint(0, 255)
            elif state['corruption_type'] == 'color':
                intensity = random.uniform(0.5, 1.0)
                r = int(state['base_color'][0] * intensity)
                g = int(state['base_color'][1] * intensity)
                b = int(state['base_color'][2] * intensity)
            elif state['corruption_type'] == 'invert':
                r, b = 0, 0
                g = random.randint(200, 255)
        else:
            r, g, b = BG_COLOR
        
        if abs(dist - state['corruption_radius']) < 0.1:
            edge_intensity = 1.0 - abs(dist - state['corruption_radius']) / 0.1
            r = min(255, r + int(255 * edge_intensity))
            g = min(255, g + int(255 * edge_intensity))
            b = min(255, b + int(255 * edge_intensity))
        
        colors.append((r, g, b))
    
    return colors

def render_digital_meltdown(positions, frame, t, bounds, state):
    colors = []
    
    if 'drips' not in state:
        state['drips'] = []
        state['base_pattern'] = [random.choice(ALL_COLORS) for _ in range(20)]
    
    if random.random() < 0.3 * CHAOS_LEVEL:
        state['drips'].append({
            'x': random.uniform(bounds['min_x'], bounds['max_x']),
            'y': random.uniform(bounds['min_y'], bounds['max_y']),
            'z': bounds['max_z'],
            'speed': random.uniform(0.5, 2.0),
            'color': random.choice(ALL_COLORS),
            'width': random.uniform(0.1, 0.25)
        })
    
    for drip in state['drips']:
        drip['z'] -= drip['speed'] / FPS
        drip['speed'] += 0.05
    state['drips'] = [d for d in state['drips'] if d['z'] > bounds['min_z'] - 0.5]
    
    z_range = bounds['max_z'] - bounds['min_z']
    
    for i, led in enumerate(positions):
        stripe_idx = int((led.z - bounds['min_z']) / z_range * 20) % 20
        r, g, b = state['base_pattern'][stripe_idx]
        r, g, b = int(r * 0.3), int(g * 0.3), int(b * 0.3)
        
        for drip in state['drips']:
            dist_xy = math.sqrt((led.x - drip['x'])**2 + (led.y - drip['y'])**2)
            if dist_xy < drip['width']:
                if drip['z'] < led.z < drip['z'] + 0.4:
                    intensity = 1.0 - (led.z - drip['z']) / 0.4
                    intensity *= (1.0 - dist_xy / drip['width'])
                    r = int(r + drip['color'][0] * intensity)
                    g = int(g + drip['color'][1] * intensity)
                    b = int(b + drip['color'][2] * intensity)
        
        colors.append((min(255, r), min(255, g), min(255, b)))
    
    return colors

def render_hack_attack(positions, frame, t, bounds, state):
    colors = []
    
    if 'phase' not in state:
        state['phase'] = 0
        state['warning_flash'] = False
        state['scroll_z'] = bounds['max_z']
        state['hack_progress'] = 0
    
    state['phase'] = (state['phase'] + 1) % 60
    state['warning_flash'] = state['phase'] < 5
    
    state['scroll_z'] -= 1.5 / FPS
    if state['scroll_z'] < bounds['min_z']:
        state['scroll_z'] = bounds['max_z']
    
    state['hack_progress'] = min(1.0, state['hack_progress'] + 0.01)
    
    z_range = bounds['max_z'] - bounds['min_z']
    hack_line = bounds['min_z'] + state['hack_progress'] * z_range
    
    for i, led in enumerate(positions):
        normalized_z = (led.z - bounds['min_z']) / z_range
        
        scroll_intensity = 0.3 * (1 + math.sin((led.z - state['scroll_z']) * 20))
        r = int(COLORS['forest_green'][0] * scroll_intensity * 0.2)
        g = int(COLORS['forest_green'][1] * scroll_intensity * 0.2)
        b = int(COLORS['forest_green'][2] * scroll_intensity * 0.2)
        
        if state['warning_flash'] and normalized_z > 0.8:
            g = min(255, g + 200)
        
        if led.z < hack_line:
            if random.random() < 0.3:
                r, b = 0, 0
                g = random.randint(100, 255)
            else:
                r = int(COLORS['toxic_green'][0] * 0.5)
                g = int(COLORS['toxic_green'][1] * 0.5)
                b = int(COLORS['toxic_green'][2] * 0.5)
        
        if abs(led.z - hack_line) < 0.05:
            r, g, b = 200, 255, 200
        
        if random.random() < 0.02:
            r, g, b = COLORS['toxic_green']
        
        colors.append((min(255, r), min(255, g), min(255, b)))
    
    return colors

EFFECT_RENDERERS = {
    'chaos_wave': render_chaos_wave,
    'data_streams': render_data_streams,
    'glitch_blocks': render_glitch_blocks,
    'explosion': render_explosion,
    'strobe_burst': render_strobe_burst,
    'screen_tear': render_screen_tear,
    'scanline_sweep': render_scanline_sweep,
    'bit_crush': render_bit_crush,
    'color_corrupt': render_color_corrupt,
    'static_takeover': render_static_takeover,
    'rainbow_glitch': render_rainbow_glitch,
    'binary_flash': render_binary_flash,
    'seizure_mode': render_seizure_mode,
    'corrupt_cascade': render_corrupt_cascade,
    'digital_meltdown': render_digital_meltdown,
    'hack_attack': render_hack_attack,
}

def create_ultimate_glitch(position_map_path, output_path):
    creator = GIFTCreator(framerate=FPS)
    creator.load_position_map(position_map_path)
    
    positions = creator.positions
    
    bounds = {
        'min_x': min(p.x for p in positions),
        'max_x': max(p.x for p in positions),
        'min_y': min(p.y for p in positions),
        'max_y': max(p.y for p in positions),
        'min_z': min(p.z for p in positions),
        'max_z': max(p.z for p in positions),
    }
    
    total_frames = int(DURATION_SECONDS * FPS)
    scheduler = EffectScheduler(total_frames)
    global_chaos = GlobalChaos()
    
    effect_states = {}
    current_effect_name = None
    
    for frame_idx in range(total_frames):
        t = frame_idx / FPS
        
        global_chaos.update(frame_idx)
        
        effect_name = scheduler.get_active_effect(frame_idx)
        
        if effect_name != current_effect_name:
            if effect_name:
                effect_states[effect_name] = {}
            current_effect_name = effect_name
        
        if effect_name and effect_name in EFFECT_RENDERERS:
            state = effect_states.get(effect_name, {})
            frame_colors = EFFECT_RENDERERS[effect_name](positions, frame_idx, t, bounds, state)
        else:
            frame_colors = render_idle(positions, frame_idx, t)
        
        frame_colors = global_chaos.apply(frame_colors, positions, frame_idx, t)
        
        frame_colors = [(max(0, min(255, r)), max(0, min(255, g)), max(0, min(255, b))) 
                        for r, g, b in frame_colors]
        
        creator.add_frame(frame_colors)

    creator.export(output_path)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("pos_map")
    parser.add_argument("--output", default="effect_hacker_glitch_green.gift")
    args = parser.parse_args()
    
    create_ultimate_glitch(args.pos_map, args.output)