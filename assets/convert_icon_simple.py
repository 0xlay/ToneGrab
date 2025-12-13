#!/usr/bin/env python3
"""
Simple icon generator for ToneGrab using PIL only.
Creates icons without requiring Cairo dependencies.
"""

import sys
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("Error: Pillow not installed")
    print("Please run: pip install pillow")
    sys.exit(1)


def create_icon_image(size: int) -> Image.Image:
    """Create icon using PIL drawing primitives."""
    # Create image with transparency
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Scale factor
    scale = size / 512
    
    # Background circles
    center = size // 2
    radius_outer = int(240 * scale)
    radius_inner = int(230 * scale)
    
    # Draw outer circle (dark background)
    draw.ellipse(
        [(center - radius_outer, center - radius_outer),
         (center + radius_outer, center + radius_outer)],
        fill=(26, 26, 26, 255)
    )
    
    # Draw inner circle
    draw.ellipse(
        [(center - radius_inner, center - radius_inner),
         (center + radius_inner, center + radius_inner)],
        fill=(45, 45, 45, 255)
    )
    
    # Draw sound waves (simplified as horizontal arcs)
    wave_color_start = (74, 158, 255)  # Blue
    wave_color_end = (0, 102, 204)  # Darker blue
    
    # Three wave lines
    wave_positions = [0.39, 0.5, 0.61]  # Relative positions
    wave_widths = [int(16 * scale), int(20 * scale), int(16 * scale)]
    
    for i, (pos, width) in enumerate(zip(wave_positions, wave_widths)):
        y = int(size * pos)
        
        # Interpolate color
        t = i / 2
        color = tuple(int(a + (b - a) * t) for a, b in zip(wave_color_start, wave_color_end))
        
        # Draw wave as curved line (approximated with multiple segments)
        wave_start = int(size * 0.29)
        wave_end = int(size * 0.68)
        wave_amplitude = int(30 * scale)
        
        points = []
        for x in range(wave_start, wave_end, max(1, int(5 * scale))):
            # Simple sine-like curve
            progress = (x - wave_start) / (wave_end - wave_start)
            y_offset = int(wave_amplitude * (0.5 - abs(progress - 0.5)))
            points.append((x, y + y_offset))
        
        if len(points) > 1:
            draw.line(points, fill=color, width=width, joint='curve')
    
    # Draw download arrow
    arrow_x = center
    arrow_y = int(size * 0.685)
    
    arrow_color = (102, 255, 102)  # Green
    
    # Arrow shaft
    shaft_width = int(24 * scale)
    shaft_height = int(80 * scale)
    shaft_radius = int(4 * scale)
    
    draw.rounded_rectangle(
        [(arrow_x - shaft_width // 2, arrow_y - shaft_height),
         (arrow_x + shaft_width // 2, arrow_y + int(20 * scale))],
        radius=shaft_radius,
        fill=arrow_color
    )
    
    # Arrow head (triangle)
    arrow_head_size = int(40 * scale)
    arrow_head_y = arrow_y + int(20 * scale)
    
    draw.polygon(
        [
            (arrow_x - arrow_head_size, arrow_head_y),
            (arrow_x, arrow_head_y + arrow_head_size),
            (arrow_x + arrow_head_size, arrow_head_y)
        ],
        fill=arrow_color
    )
    
    # Outer ring accent
    ring_width = int(4 * scale)
    draw.ellipse(
        [(center - radius_outer + ring_width, center - radius_outer + ring_width),
         (center + radius_outer - ring_width, center + radius_outer - ring_width)],
        outline=(74, 158, 255, 128),
        width=ring_width
    )
    
    return img


def create_ico(base_img: Image.Image, output_path: Path):
    """Create Windows ICO file with multiple sizes."""
    print(f"Creating {output_path.name}...")
    sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    base_img.save(output_path, format='ICO', sizes=sizes)


def main():
    """Main function."""
    script_dir = Path(__file__).parent
    icons_dir = script_dir / "icons"
    icons_dir.mkdir(exist_ok=True)
    
    print("Generating ToneGrab icons using PIL...")
    
    # Generate PNG files at various sizes
    sizes = [16, 32, 48, 64, 128, 256, 512]
    
    for size in sizes:
        print(f"Generating icon_{size}.png ({size}x{size})...")
        img = create_icon_image(size)
        output_path = icons_dir / f"icon_{size}.png"
        img.save(output_path, 'PNG')
    
    # Create main 512px PNG
    main_png = icons_dir / "icon.png"
    print(f"Creating {main_png.name} (512x512)...")
    img_512 = create_icon_image(512)
    img_512.save(main_png, 'PNG')
    
    # Create Windows ICO
    ico_path = icons_dir / "icon.ico"
    create_ico(img_512, ico_path)
    
    print("\n✅ Icon generation complete!")
    print(f"\nGenerated files in {icons_dir}:")
    print("  - icon.png (512x512) - Linux/general use")
    print("  - icon.ico - Windows executable")
    print("  - icon_*.png - Various sizes (16-512)")
    
    print("\nFor macOS .icns file:")
    print("  1. Copy icon_*.png files to icon.iconset/ directory")
    print("  2. Run on macOS: iconutil -c icns icon.iconset -o icon.icns")
    print("\nOr use online converter: https://convertio.co/png-icns/")


if __name__ == "__main__":
    main()
