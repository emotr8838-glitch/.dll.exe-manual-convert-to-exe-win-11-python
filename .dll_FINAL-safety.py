import pygame
import math
import numpy as np
from datetime import datetime
from collections import deque

# Initialize Pygame
pygame.init()
pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)

# Screen settings
WIDTH, HEIGHT = 1280, 720
FPS = 60
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("GDI Effects - Tunnel (30s) -> Scroll (30s) -> Vortex (Loop)")
pygame.mouse.set_visible(False)  # Hide normal cursor
clock = pygame.time.Clock()

# Mouse trail system
mouse_trail = deque(maxlen=50)  # Store last 50 mouse positions with alpha

def generate_bytebeat(duration_ms, formula_type=1):
    """Generate bytebeat audio with different formulas"""
    sample_rate = 44100
    duration_samples = int(sample_rate * duration_ms / 1000.0)
    
    # Bytebeat formulas
    if formula_type == 1:
        def formula(t):
            return ((t >> 8) * ((t | 17) ^ (t & 240)) ^ (t & (t >> 4))) & 255
    elif formula_type == 2:
        def formula(t):
            return (t * ((t >> 7) | (t >> 9)) ^ (t << 3)) & 255
    else:  # formula_type == 3
        def formula(t):
            return (t*((t&4096 if t&4096 else 16)+(1&t>>14) if (t%65536<59392 if t&4096 else False) else (t>>6 if t&4096 else 16)+(1&t>>14))>>(3&(-t>>(2 if t&2048 else 10)))|t>>(4 if t&16384 else (3 if t&4096 else 2))) & 255
    
    # Generate audio samples
    samples = np.zeros(duration_samples, dtype=np.int16)
    for i in range(duration_samples):
        t = int((i * 8) & 0xFFFFFFFF)
        val = formula(t)
        # Convert to signed audio (-128 to 127) then to 16-bit
        samples[i] = (val - 128) * 256
    
    # Create stereo sound (duplicate for both channels)
    stereo_samples = np.column_stack((samples, samples))
    sound = pygame.sndarray.make_sound(stereo_samples)
    return sound

# Pre-generate bytebeat sounds
bytebeat_payload1 = generate_bytebeat(30000, formula_type=1)  # 30 seconds, payload 1
bytebeat_payload2 = generate_bytebeat(4000, formula_type=2)   # 4 seconds, payload 2 (for looping)
bytebeat_payload3 = generate_bytebeat(5000, formula_type=3)   # 5 seconds, payload 3 (for looping)

def draw_error_x(surface, x, y, size=30, color=(255, 0, 0), thickness=3):
    """Draw Windows error X cursor in a circle"""
    # Draw circle
    pygame.draw.circle(surface, color, (x, y), size, 2)
    
    # Draw X inside circle (smaller)
    offset = size // 3
    pygame.draw.line(surface, color, (x - offset, y - offset), (x + offset, y + offset), thickness)
    pygame.draw.line(surface, color, (x + offset, y - offset), (x - offset, y + offset), thickness)

def draw_mouse_trail(surface):
    """Draw mouse trail with fading X cursors"""
    if not mouse_trail:
        return
    
    trail_list = list(mouse_trail)
    for idx, (pos, alpha_val) in enumerate(trail_list):
        # Calculate fade effect
        alpha = int(255 * (idx / len(trail_list)))
        
        # Draw X with fading color (clamped to valid RGB range)
        color = (
            max(0, min(255, int(200 + 55 * math.sin(alpha * 0.02)))),
            max(0, min(255, int(50 + 55 * math.sin(alpha * 0.03)))),
            max(0, min(255, int(150 + 100 * math.sin(alpha * 0.01))))
        )
        
        size = int(12 * (idx / len(trail_list)))
        if size > 1:
            draw_error_x(surface, pos[0], pos[1], size, color, 2)

def draw_tunnel_frame(surface, time):
    """Draw screen tunnel effect"""
    surface.fill((0, 0, 0))
    
    center_x = WIDTH // 2
    center_y = HEIGHT // 2
    
    # Create tunnel rings
    num_rings = 40
    max_radius = max(WIDTH, HEIGHT) / 2 + 200
    
    for ring_idx in range(num_rings):
        # Calculate ring properties
        progress = (ring_idx - time * 2) % num_rings / num_rings
        radius = max_radius * (1 - progress)
        
        if radius < 5:
            continue
        
        # Color cycling based on ring depth
        hue = (time * 0.5 + ring_idx * 0.1) % 360
        color_val = int(128 + 127 * math.sin(hue * math.pi / 180))
        r = int(128 + 127 * math.sin(hue * math.pi / 180 + 0))
        g = int(128 + 127 * math.sin(hue * math.pi / 180 + 2.094))
        b = int(128 + 127 * math.sin(hue * math.pi / 180 + 4.188))
        
        # Brightness based on distance
        brightness = int(255 * progress)
        color = (
            min(255, max(0, r)),
            min(255, max(0, g)),
            min(255, max(0, b))
        )
        
        # Draw circle
        if radius > 0:
            pygame.draw.circle(surface, color, (center_x, center_y), int(radius), 2)
    
    # Draw rotating rectangles for additional tunnel effect
    for rect_idx in range(12):
        angle = time * 0.03 + rect_idx * (2 * math.pi / 12)
        scale = 0.5 + 0.5 * math.sin(time * 0.02 + rect_idx)
        
        rect_size_x = WIDTH * scale
        rect_size_y = HEIGHT * scale
        
        hue = (time * 0.3 + rect_idx * 30) % 360
        color = (
            int(128 + 127 * math.sin(hue * math.pi / 180)),
            int(128 + 127 * math.sin((hue + 120) * math.pi / 180)),
            int(128 + 127 * math.sin((hue + 240) * math.pi / 180))
        )
        
        # Create rotated rectangle points
        corner_x = rect_size_x / 2
        corner_y = rect_size_y / 2
        
        corners = [
            (-corner_x, -corner_y),
            (corner_x, -corner_y),
            (corner_x, corner_y),
            (-corner_x, corner_y)
        ]
        
        rotated_corners = []
        for x, y in corners:
            rx = x * math.cos(angle) - y * math.sin(angle)
            ry = x * math.sin(angle) + y * math.cos(angle)
            rotated_corners.append((center_x + rx, center_y + ry))
        
        pygame.draw.polygon(surface, color, rotated_corners, 1)
    
    # Draw pulsing rings at center
    for pulse_idx in range(5):
        pulse_radius = 20 + pulse_idx * 15
        pulse_time = (time * 0.05 - pulse_idx * 0.5) % 1.0
        pulse_alpha = int(255 * (1 - pulse_time))
        
        if pulse_alpha > 0:
            color = (pulse_alpha, pulse_alpha // 2, pulse_alpha)
            pygame.draw.circle(surface, color, (center_x, center_y), int(pulse_radius), 2)
    
    # Add scanline effect
    line_spacing = 10
    line_offset = int(time * 5) % line_spacing
    for y in range(line_offset, HEIGHT, line_spacing):
        alpha = int(50)
        pygame.draw.line(surface, (alpha, alpha // 3, alpha), (0, y), (WIDTH, y), 1)
    
    # Draw spiral tunnel
    color_spiral = (
        int(200 + 55 * math.sin(time * 0.03)),
        int(150 + 105 * math.cos(time * 0.02)),
        int(100 + 155 * math.sin(time * 0.04))
    )
    
    for i in range(100):
        angle = (6 * math.pi * i / 100.0)
        spiral_angle = angle + time * 0.02
        spiral_radius = 50 + angle * 30 / (6 * math.pi)
        
        x = int(center_x + spiral_radius * math.cos(spiral_angle))
        y = int(center_y + spiral_radius * math.sin(spiral_angle))
        
        if i > 0:
            prev_angle = (6 * math.pi * (i-1) / 100.0)
            prev_spiral_angle = prev_angle + time * 0.02
            prev_spiral_radius = 50 + prev_angle * 30 / (6 * math.pi)
            
            prev_x = int(center_x + prev_spiral_radius * math.cos(prev_spiral_angle))
            prev_y = int(center_y + prev_spiral_radius * math.sin(prev_spiral_angle))
            
            pygame.draw.line(surface, color_spiral, (prev_x, prev_y), (x, y), 2)

def draw_scroll_frame(surface, time):
    """Draw screen scroll effect"""
    surface.fill((5, 5, 10))
    
    # Horizontal scrolling lines
    line_height = 20
    scroll_offset = int(time * 100) % line_height
    
    for y in range(-line_height, HEIGHT + line_height, line_height):
        scroll_y = y + scroll_offset
        
        # Animated gradient color
        color = (
            int(100 + 100 * math.sin(time * 0.02 + y * 0.01)),
            int(150 + 100 * math.cos(time * 0.03 + y * 0.01)),
            int(200 + 50 * math.sin(time * 0.04 + y * 0.02))
        )
        
        pygame.draw.line(surface, color, (0, scroll_y), (WIDTH, scroll_y), 3)
    
    # Vertical scrolling columns
    col_width = 30
    scroll_offset_x = int(time * 80) % col_width
    
    for x in range(-col_width, WIDTH + col_width, col_width):
        scroll_x = x + scroll_offset_x
        
        # Animated gradient color
        color = (
            int(100 + 100 * math.cos(time * 0.025 + x * 0.01)),
            int(100 + 100 * math.sin(time * 0.035 + x * 0.01)),
            int(150 + 100 * math.cos(time * 0.045 + x * 0.02))
        )
        
        pygame.draw.line(surface, color, (scroll_x, 0), (scroll_x, HEIGHT), 2)
    
    # Diagonal scanning effect
    for i in range(0, HEIGHT + WIDTH, 50):
        diag_offset = int(time * 60) % 50
        x_start = i - HEIGHT + diag_offset
        y_start = 0
        x_end = i + diag_offset
        y_end = HEIGHT
        
        color = (
            int(150 + 50 * math.sin(time * 0.02 + i * 0.01)),
            int(100 + 50 * math.cos(time * 0.03 + i * 0.01)),
            int(200 + 50 * math.sin(time * 0.04 + i * 0.01))
        )
        
        pygame.draw.line(surface, color, (x_start, y_start), (x_end, y_end), 1)
    
    # Center pulsing rectangle
    center_x, center_y = WIDTH // 2, HEIGHT // 2
    pulse = int(100 + 50 * math.sin(time * 0.03))
    
    rect = pygame.Rect(center_x - pulse, center_y - pulse // 2, pulse * 2, pulse)
    pygame.draw.rect(surface, (200, 100, 150), rect, 3)

def draw_prismatic_vortex(surface, time):
    """Draw prismatic vortex effect with rotating shapes"""
    surface.fill((10, 5, 20))
    
    center_x, center_y = WIDTH // 2, HEIGHT // 2
    
    # Draw rotating star burst
    for star_idx in range(16):
        angle = time * 0.1 + star_idx * (2 * math.pi / 16)
        
        # Multiple rings of stars
        for ring in range(3):
            radius = 80 + ring * 60
            x = center_x + radius * math.cos(angle)
            y = center_y + radius * math.sin(angle)
            
            color = (
                max(0, min(255, int(100 + 100 * math.sin(time * 0.02 + star_idx + ring * 0.5)))),
                max(0, min(255, int(150 + 100 * math.cos(time * 0.03 + star_idx + ring * 0.5)))),
                max(0, min(255, int(200 + 50 * math.sin(time * 0.04 + star_idx + ring * 0.5))))
            )
            
            pygame.draw.circle(surface, color, (int(x), int(y)), 5)
    
    # Draw radiating energy beams
    for beam_idx in range(12):
        angle = time * 0.08 + beam_idx * (2 * math.pi / 12)
        end_x = center_x + max(WIDTH, HEIGHT) * math.cos(angle)
        end_y = center_y + max(WIDTH, HEIGHT) * math.sin(angle)
        
        color = (
            max(0, min(255, int(100 + 155 * math.sin(time * 0.03 + beam_idx * 0.5)))),
            max(0, min(255, int(50 + 155 * math.cos(time * 0.02 + beam_idx * 0.5)))),
            max(0, min(255, int(200 + 55 * math.sin(time * 0.04 + beam_idx * 0.5))))
        )
        
        pygame.draw.line(surface, color, (center_x, center_y), (int(end_x), int(end_y)), 2)
    
    # Draw rotating polygons
    for poly_idx in range(6):
        angle_offset = time * (0.05 + poly_idx * 0.01) + poly_idx * (2 * math.pi / 6)
        poly_radius = 150
        
        points = []
        sides = 5 + poly_idx % 2
        for side in range(sides):
            vertex_angle = angle_offset + side * (2 * math.pi / sides)
            px = center_x + poly_radius * math.cos(vertex_angle)
            py = center_y + poly_radius * math.sin(vertex_angle)
            points.append((int(px), int(py)))
        
        color = (
            max(0, min(255, int(150 + 100 * math.sin(time * 0.02 + poly_idx * 0.8)))),
            max(0, min(255, int(100 + 100 * math.cos(time * 0.025 + poly_idx * 0.8)))),
            max(0, min(255, int(200 + 55 * math.sin(time * 0.035 + poly_idx * 0.8))))
        )
        
        if len(points) > 2:
            pygame.draw.polygon(surface, color, points, 2)
    
    # Center pulsing orb
    orb_size = int(30 + 20 * math.sin(time * 0.05))
    orb_color = (
        max(0, min(255, int(255 - 100 * math.sin(time * 0.03)))),
        max(0, min(255, int(200 - 100 * math.cos(time * 0.02)))),
        max(0, min(255, int(100 + 155 * math.sin(time * 0.04))))
    )
    pygame.draw.circle(surface, orb_color, (center_x, center_y), orb_size)
    pygame.draw.circle(surface, (255, 255, 255), (center_x, center_y), orb_size, 2)
    
    # Orbiting particles
    for particle_idx in range(20):
        particle_angle = time * 0.15 + particle_idx * (2 * math.pi / 20)
        particle_radius = 100 + 50 * math.sin(time * 0.02 + particle_idx * 0.3)
        
        px = center_x + particle_radius * math.cos(particle_angle)
        py = center_y + particle_radius * math.sin(particle_angle)
        
        particle_color = (
            max(0, min(255, int(100 + 155 * math.sin(time * 0.03 + particle_idx * 0.5)))),
            max(0, min(255, int(150 + 100 * math.cos(time * 0.025 + particle_idx * 0.5)))),
            max(0, min(255, int(50 + 200 * math.sin(time * 0.04 + particle_idx * 0.5))))
        )
        
        pygame.draw.circle(surface, particle_color, (int(px), int(py)), 3)

def draw_bluescreen(surface, time):
    """Draw Windows BSOD (Blue Screen of Death) effect"""
    surface.fill((0, 0, 170))  # Classic Windows blue
    
    # Draw warning symbol (triangle with exclamation)
    center_x, center_y = WIDTH // 2, HEIGHT // 2
    
    # Draw warning triangle
    triangle_points = [
        (center_x, center_y - 80),
        (center_x - 60, center_y + 60),
        (center_x + 60, center_y + 60)
    ]
    pygame.draw.polygon(surface, (255, 255, 255), triangle_points, 5)
    
    # Draw exclamation mark inside triangle
    font_large = pygame.font.Font(None, 100)
    exclamation = font_large.render("!", True, (0, 0, 170))
    surface.blit(exclamation, (center_x - exclamation.get_width() // 2, center_y - 50))
    
    # Draw error text
    font = pygame.font.Font(None, 28)
    error_texts = [
        "A critical error has occurred",
        "",
        "Please restart your computer",
        "",
        "If you continue to see this error message,",
        "contact your system administrator",
        "",
        "DRIVER_IRQL_NOT_LESS_OR_EQUAL",
        f"*** STOP: 0x000000D1 (0x{int(time * 1000) % 256:08x}, 0x{int(time * 2000) % 256:08x}, 0x{int(time * 3000) % 256:08x}, 0x{int(time * 4000) % 256:08x})"
    ]
    
    y_offset = center_y + 150
    for text in error_texts:
        if text:
            rendered_text = font.render(text, True, (255, 255, 255))
            surface.blit(rendered_text, (50, y_offset))
        y_offset += 40
    
    # Blinking effect
    if int(time * 2) % 2 == 0:
        # Draw flickering scanlines
        for i in range(0, HEIGHT, 10):
            pygame.draw.line(surface, (0, 0, 100), (0, i), (WIDTH, i), 2)
    
    # Bottom status text
    status_text = font.render("Press any key to continue...", True, (255, 255, 255))
    surface.blit(status_text, (50, HEIGHT - 60))

# Main loop
running = True
start_time = datetime.now()
payload_phase = 1  # Track which payload phase we're in

# Start with payload 1
bytebeat_payload1.play()

try:
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
        
        # Calculate time in seconds
        elapsed = (datetime.now() - start_time).total_seconds()
        
        # Get mouse position and add to trail
        mouse_pos = pygame.mouse.get_pos()
        mouse_trail.append((mouse_pos, 255))
        
        # Switch payloads at time milestones
        if elapsed >= 60 and payload_phase == 2:
            payload_phase = 3
            pygame.mixer.stop()
            bytebeat_payload3.play(-1)  # Loop payload 3
        elif elapsed >= 30 and payload_phase == 1:
            payload_phase = 2
            pygame.mixer.stop()
            bytebeat_payload2.play(-1)  # Loop payload 2
        
        # Draw appropriate effect based on time
        if elapsed < 30:
            draw_tunnel_frame(screen, elapsed)
        elif elapsed < 60:
            draw_scroll_frame(screen, elapsed - 30)
        elif elapsed < 100:
            draw_prismatic_vortex(screen, elapsed - 60)
        else:
            draw_bluescreen(screen, elapsed - 100)
        
        # Draw mouse trail (but not on bluescreen)
        if elapsed < 100:
            draw_mouse_trail(screen)
        
        # Update display
        pygame.display.flip()
        clock.tick(FPS)

finally:
    pygame.mouse.set_visible(True)  # Show cursor again
    pygame.mixer.stop()
    pygame.quit()
    print("GDI Effects closed.")