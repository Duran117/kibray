#!/usr/bin/env python3
"""
Generate PWA icons for Kibray
Creates placeholder icons with 'K' logo
"""

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("Installing Pillow...")
    import os
    os.system("pip install Pillow")
    from PIL import Image, ImageDraw, ImageFont

import os

# Create icons directory
icons_dir = '/Users/jesus/Documents/kibray/static/icons'
os.makedirs(icons_dir, exist_ok=True)

# Icon sizes for PWA
sizes = [72, 96, 128, 144, 152, 192, 384, 512]

# Kibray brand colors
BG_COLOR = '#4F46E5'  # Indigo
TEXT_COLOR = '#FFFFFF'  # White

def hex_to_rgb(hex_color):
    """Convert hex color to RGB tuple"""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def create_icon(size):
    """Create a single icon with 'K' letter"""
    # Create image with gradient background
    img = Image.new('RGB', (size, size), hex_to_rgb(BG_COLOR))
    draw = ImageDraw.Draw(img)

    # Try to use a nice font, fallback to default
    try:
        font_size = int(size * 0.6)
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", font_size)
    except OSError:
        font = ImageFont.load_default()

    # Draw 'K' text centered
    text = 'K'
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    x = (size - text_width) / 2 - bbox[0]
    y = (size - text_height) / 2 - bbox[1]

    draw.text((x, y), text, fill=TEXT_COLOR, font=font)

    return img

# Generate icons
print("Generating PWA icons...")
for size in sizes:
    icon = create_icon(size)
    filename = f'icon-{size}x{size}.png'
    filepath = os.path.join(icons_dir, filename)
    icon.save(filepath, 'PNG')
    print(f"✓ Created {filename}")

# Create apple-touch-icon (180x180)
apple_icon = create_icon(180)
apple_icon.save('/Users/jesus/Documents/kibray/static/apple-touch-icon.png', 'PNG')
print("✓ Created apple-touch-icon.png")

# Create favicon (multi-size ico)
favicon_sizes = [16, 32, 48]
favicon_images = [create_icon(s) for s in favicon_sizes]
favicon_images[0].save(
    '/Users/jesus/Documents/kibray/static/favicon.ico',
    format='ICO',
    sizes=[(s, s) for s in favicon_sizes]
)
print("✓ Created favicon.ico")

print("\n✅ All PWA icons generated successfully!")
print(f"📁 Icons location: {icons_dir}")
