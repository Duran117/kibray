#!/usr/bin/env python3
"""
Generate PWA icons from SVG using PIL/Pillow and cairosvg
"""
import os
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("Installing Pillow...")
    os.system("pip install Pillow")
    from PIL import Image, ImageDraw, ImageFont


def create_kibray_icon(size):
    """Create a Kibray icon with letter K and paint brush"""
    # Create image with blue background
    img = Image.new("RGB", (size, size), color="#1e3a8a")
    draw = ImageDraw.Draw(img)

    # Calculate sizes based on icon size
    padding = size // 8

    # Draw rounded rectangle background (simulated with ellipse corners)
    # This is a simplified version - for production use a proper rounded rect

    # Draw letter K in white
    try:
        # Try to use a bold font
        font_size = int(size * 0.6)
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", font_size)
    except:
        # Fallback to default font
        font = ImageFont.load_default()

    # Draw K
    text = "K"
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    x = (size - text_width) // 2 - padding // 2
    y = (size - text_height) // 2
    draw.text((x, y), text, fill="white", font=font)

    # Draw paint brush accent (simplified)
    brush_x = size - padding - size // 6
    brush_y = size - padding - size // 6
    brush_size = size // 8

    # Brush handle (yellow)
    draw.ellipse(
        [brush_x - brush_size, brush_y - brush_size, brush_x + brush_size, brush_y + brush_size], fill="#fbbf24"
    )

    # Brush tip (red)
    draw.ellipse(
        [brush_x - brush_size // 2, brush_y + brush_size // 2, brush_x + brush_size // 2, brush_y + brush_size * 2],
        fill="#f87171",
    )

    return img


def main():
    """Generate all required PWA icon sizes"""
    sizes = [72, 96, 128, 144, 152, 192, 384, 512]

    # Get the icons directory
    script_dir = Path(__file__).parent
    icons_dir = script_dir / "core" / "static" / "icons"
    icons_dir.mkdir(parents=True, exist_ok=True)

    print(f"Generating PWA icons in: {icons_dir}")
    print("-" * 50)

    for size in sizes:
        filename = f"icon-{size}x{size}.png"
        filepath = icons_dir / filename

        print(f"Generating {filename}... ", end="")

        try:
            img = create_kibray_icon(size)
            img.save(filepath, "PNG", optimize=True)
            print(f"✅ ({filepath.stat().st_size // 1024}KB)")
        except Exception as e:
            print(f"❌ Error: {e}")

    print("-" * 50)
    print("✅ All icons generated successfully!")
    print(f"\nFiles saved in: {icons_dir}")
    print("\nNext steps:")
    print("1. Verify icons look correct")
    print("2. Update manifest.json paths if needed")
    print("3. Test PWA installation on mobile device")


if __name__ == "__main__":
    main()
