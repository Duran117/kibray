#!/usr/bin/env python3#!/usr/bin/env python3

""""""

Generate PWA icons for KibrayGenerate PWA icons from SVG using PIL/Pillow and cairosvg

Creates placeholder icons with 'K' logo"""

"""

from PIL import Image, ImageDraw, ImageFontimport os

import osfrom pathlib import Path



# Create icons directorytry:

icons_dir = '/Users/jesus/Documents/kibray/static/icons'    from PIL import Image, ImageDraw, ImageFont

os.makedirs(icons_dir, exist_ok=True)except ImportError:

    print("Installing Pillow...")

# Icon sizes for PWA    os.system("pip install Pillow")

sizes = [72, 96, 128, 144, 152, 192, 384, 512]    from PIL import Image, ImageDraw, ImageFont



# Brand colors

bg_color = '#1a73e8'  # Kibray bluedef create_kibray_icon(size):

text_color = '#ffffff'  # White    """Create a Kibray icon with letter K and paint brush"""

    # Create image with blue background

def hex_to_rgb(hex_color):    img = Image.new("RGB", (size, size), color="#1e3a8a")

    """Convert hex color to RGB tuple"""    draw = ImageDraw.Draw(img)

    hex_color = hex_color.lstrip('#')

    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))    # Calculate sizes based on icon size

    padding = size // 8

def create_icon(size):

    """Create a simple icon with 'K' letter"""    # Draw rounded rectangle background (simulated with ellipse corners)

    # Create image with blue background    # This is a simplified version - for production use a proper rounded rect

    img = Image.new('RGB', (size, size), hex_to_rgb(bg_color))

    draw = ImageDraw.Draw(img)    # Draw letter K in white

        try:

    # Try to use a nice font, fallback to default        # Try to use a bold font

    try:        font_size = int(size * 0.6)

        # Adjust font size based on icon size        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", font_size)

        font_size = int(size * 0.6)    except:

        font = ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc', font_size)        # Fallback to default font

    except:        font = ImageFont.load_default()

        font = ImageFont.load_default()

        # Draw K

    # Draw 'K' in center    text = "K"

    text = 'K'    bbox = draw.textbbox((0, 0), text, font=font)

        text_width = bbox[2] - bbox[0]

    # Get text bounding box for centering    text_height = bbox[3] - bbox[1]

    bbox = draw.textbbox((0, 0), text, font=font)    x = (size - text_width) // 2 - padding // 2

    text_width = bbox[2] - bbox[0]    y = (size - text_height) // 2

    text_height = bbox[3] - bbox[1]    draw.text((x, y), text, fill="white", font=font)

    

    # Calculate position to center text    # Draw paint brush accent (simplified)

    x = (size - text_width) / 2 - bbox[0]    brush_x = size - padding - size // 6

    y = (size - text_height) / 2 - bbox[1]    brush_y = size - padding - size // 6

        brush_size = size // 8

    # Draw text

    draw.text((x, y), text, fill=hex_to_rgb(text_color), font=font)    # Brush handle (yellow)

        draw.ellipse(

    # Add subtle border        [brush_x - brush_size, brush_y - brush_size, brush_x + brush_size, brush_y + brush_size], fill="#fbbf24"

    border_width = max(1, size // 64)    )

    draw.rectangle(

        [(0, 0), (size-1, size-1)],    # Brush tip (red)

        outline=hex_to_rgb(text_color),    draw.ellipse(

        width=border_width        [brush_x - brush_size // 2, brush_y + brush_size // 2, brush_x + brush_size // 2, brush_y + brush_size * 2],

    )        fill="#f87171",

        )

    # Save icon

    filename = f'icon-{size}x{size}.png'    return img

    filepath = os.path.join(icons_dir, filename)

    img.save(filepath, 'PNG')

    print(f'✅ Created {filename}')def main():

    """Generate all required PWA icon sizes"""

# Generate all icon sizes    sizes = [72, 96, 128, 144, 152, 192, 384, 512]

print('Generating PWA icons...')

for size in sizes:    # Get the icons directory

    create_icon(size)    script_dir = Path(__file__).parent

    icons_dir = script_dir / "core" / "static" / "icons"

# Create apple-touch-icon    icons_dir.mkdir(parents=True, exist_ok=True)

apple_icon = Image.new('RGB', (180, 180), hex_to_rgb(bg_color))

draw = ImageDraw.Draw(apple_icon)    print(f"Generating PWA icons in: {icons_dir}")

try:    print("-" * 50)

    font = ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc', 108)

except:    for size in sizes:

    font = ImageFont.load_default()        filename = f"icon-{size}x{size}.png"

        filepath = icons_dir / filename

text = 'K'

bbox = draw.textbbox((0, 0), text, font=font)        print(f"Generating {filename}... ", end="")

text_width = bbox[2] - bbox[0]

text_height = bbox[3] - bbox[1]        try:

x = (180 - text_width) / 2 - bbox[0]            img = create_kibray_icon(size)

y = (180 - text_height) / 2 - bbox[1]            img.save(filepath, "PNG", optimize=True)

draw.text((x, y), text, fill=hex_to_rgb(text_color), font=font)            print(f"✅ ({filepath.stat().st_size // 1024}KB)")

        except Exception as e:

apple_icon_path = '/Users/jesus/Documents/kibray/static/apple-touch-icon.png'            print(f"❌ Error: {e}")

apple_icon.save(apple_icon_path, 'PNG')

print(f'✅ Created apple-touch-icon.png')    print("-" * 50)

    print("✅ All icons generated successfully!")

# Create favicon.ico (32x32)    print(f"\nFiles saved in: {icons_dir}")

favicon = Image.new('RGB', (32, 32), hex_to_rgb(bg_color))    print("\nNext steps:")

draw = ImageDraw.Draw(favicon)    print("1. Verify icons look correct")

try:    print("2. Update manifest.json paths if needed")

    font = ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc', 20)    print("3. Test PWA installation on mobile device")

except:

    font = ImageFont.load_default()

if __name__ == "__main__":

text = 'K'    main()

bbox = draw.textbbox((0, 0), text, font=font)
text_width = bbox[2] - bbox[0]
text_height = bbox[3] - bbox[1]
x = (32 - text_width) / 2 - bbox[0]
y = (32 - text_height) / 2 - bbox[1]
draw.text((x, y), text, fill=hex_to_rgb(text_color), font=font)

favicon_path = '/Users/jesus/Documents/kibray/static/favicon.ico'
favicon.save(favicon_path, 'ICO')
print(f'✅ Created favicon.ico')

# Create badge icon for notifications
badge = Image.new('RGBA', (72, 72), (*hex_to_rgb(bg_color), 255))
draw = ImageDraw.Draw(badge)
try:
    font = ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc', 44)
except:
    font = ImageFont.load_default()

text = 'K'
bbox = draw.textbbox((0, 0), text, font=font)
text_width = bbox[2] - bbox[0]
text_height = bbox[3] - bbox[1]
x = (72 - text_width) / 2 - bbox[0]
y = (72 - text_height) / 2 - bbox[1]
draw.text((x, y), text, fill=(*hex_to_rgb(text_color), 255), font=font)

badge_path = os.path.join(icons_dir, 'badge-72x72.png')
badge.save(badge_path, 'PNG')
print(f'✅ Created badge-72x72.png')

print('\n🎉 All PWA icons generated successfully!')
print(f'📁 Icons location: {icons_dir}')
