#!/usr/bin/env python3
"""
Icon converter script for ToneGrab.

Converts the SVG icon to various formats needed for different platforms.
Requires: pip install pillow cairosvg
"""

import sys
from pathlib import Path

try:
    from PIL import Image
    import cairosvg
except ImportError:
    print("Error: Required packages not installed")
    print("Please run: pip install pillow cairosvg")
    sys.exit(1)


def svg_to_png(svg_path: Path, output_path: Path, size: int):
    """Convert SVG to PNG at specified size."""
    print(f"Generating {output_path.name} ({size}x{size})...")
    cairosvg.svg2png(
        url=str(svg_path),
        write_to=str(output_path),
        output_width=size,
        output_height=size,
    )


def create_ico(png_path: Path, output_path: Path):
    """Create Windows ICO file with multiple sizes."""
    print(f"Creating {output_path.name}...")
    img = Image.open(png_path)
    
    # ICO files can contain multiple sizes
    sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    
    img.save(
        output_path,
        format='ICO',
        sizes=sizes
    )


def create_icns(png_path: Path, output_path: Path):
    """
    Create macOS ICNS file.
    Note: This requires macOS iconutil or pillow-icns package.
    """
    try:
        from PIL import Image
        # This is a simplified version
        # For full macOS support, use iconutil on macOS
        print(f"Creating {output_path.name}...")
        print("Note: For best results, use iconutil on macOS")
        
        img = Image.open(png_path)
        
        # Create temporary iconset directory
        iconset_dir = output_path.parent / "icon.iconset"
        iconset_dir.mkdir(exist_ok=True)
        
        # macOS required sizes
        sizes = {
            'icon_16x16.png': 16,
            'icon_16x16@2x.png': 32,
            'icon_32x32.png': 32,
            'icon_32x32@2x.png': 64,
            'icon_128x128.png': 128,
            'icon_128x128@2x.png': 256,
            'icon_256x256.png': 256,
            'icon_256x256@2x.png': 512,
            'icon_512x512.png': 512,
            'icon_512x512@2x.png': 1024,
        }
        
        for filename, size in sizes.items():
            icon_path = iconset_dir / filename
            resized = img.resize((size, size), Image.Resampling.LANCZOS)
            resized.save(icon_path, 'PNG')
        
        print(f"Iconset created in {iconset_dir}")
        print("Run this on macOS to create .icns:")
        print(f"  iconutil -c icns {iconset_dir} -o {output_path}")
        
    except Exception as e:
        print(f"Error creating ICNS: {e}")
        print("To create ICNS on macOS, run:")
        print(f"  iconutil -c icns icon.iconset -o {output_path}")


def main():
    """Main conversion function."""
    script_dir = Path(__file__).parent
    icons_dir = script_dir / "icons"
    svg_path = icons_dir / "icon.svg"
    
    if not svg_path.exists():
        print(f"Error: {svg_path} not found")
        sys.exit(1)
    
    print("Converting ToneGrab icon...")
    print(f"Source: {svg_path}")
    
    # Generate PNG files at various sizes
    sizes = [16, 32, 48, 64, 128, 256, 512]
    png_files = {}
    
    for size in sizes:
        output_path = icons_dir / f"icon_{size}.png"
        svg_to_png(svg_path, output_path, size)
        png_files[size] = output_path
    
    # Create main 512px PNG
    main_png = icons_dir / "icon.png"
    if 512 in png_files:
        png_files[512].rename(main_png)
        png_files[512] = main_png
    
    # Create Windows ICO
    ico_path = icons_dir / "icon.ico"
    create_ico(main_png, ico_path)
    
    # Create macOS ICNS
    icns_path = icons_dir / "icon.icns"
    create_icns(main_png, icns_path)
    
    print("\n✅ Icon conversion complete!")
    print(f"\nGenerated files in {icons_dir}:")
    print("  - icon.png (512x512) - Linux/general use")
    print("  - icon.ico - Windows executable")
    print("  - icon.iconset/ - macOS icon source")
    print("  - icon_*.png - Various sizes")
    
    print("\nTo complete macOS icon on macOS:")
    print(f"  cd {icons_dir}")
    print(f"  iconutil -c icns icon.iconset -o icon.icns")


if __name__ == "__main__":
    main()
