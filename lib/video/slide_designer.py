"""
Professional slide designer with multiple templates and visual enhancements
"""

import os
from typing import Dict, Any, List, Tuple
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import textwrap

from lib.logger import create_logger

log = create_logger('SLIDE')

# Video dimensions
VIDEO_WIDTH = 1920
VIDEO_HEIGHT = 1080

# Color schemes
COLOR_SCHEMES = {
    'ocean': {  # Formerly 'tech'
        'bg_start': (15, 23, 42),      # Slate 900
        'bg_end': (30, 41, 59),        # Slate 800
        'primary': (56, 189, 248),     # Sky 400
        'secondary': (148, 163, 184),  # Slate 400
        'accent': (34, 211, 238),      # Cyan 400
        'text_light': (248, 250, 252), # Slate 50
        'text_dark': (100, 116, 139)   # Slate 500
    },
    'minimal': {  # Formerly 'professional'
        'bg_start': (255, 255, 255),
        'bg_end': (241, 245, 249),
        'primary': (37, 99, 235),      # Blue 600
        'secondary': (71, 85, 105),    # Slate 600
        'accent': (249, 115, 22),      # Orange 500
        'text_light': (255, 255, 255),
        'text_dark': (15, 23, 42)
    },
    'midnight': {  # Formerly 'dark'
        'bg_start': (0, 0, 0),
        'bg_end': (23, 23, 23),
        'primary': (168, 85, 247),     # Purple 500
        'secondary': (163, 163, 163),  # Neutral 400
        'accent': (34, 197, 94),       # Green 500
        'text_light': (255, 255, 255),
        'text_dark': (163, 163, 163)
    }
}

def get_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    """Get font with fallback to default"""
    font_names = [
        'segoeui.ttf' if not bold else 'segoeuib.ttf',  # Windows
        'arial.ttf' if not bold else 'arialbd.ttf',
        'Arial.ttf',
        'DejaVuSans.ttf',  # Linux
    ]
    
    for font_name in font_names:
        try:
            return ImageFont.truetype(font_name, size)
        except:
            continue
    
    # Fallback to default
    return ImageFont.load_default()

def create_gradient_background(
    width: int,
    height: int,
    color_start: Tuple[int, int, int],
    color_end: Tuple[int, int, int],
    direction: str = 'vertical'
) -> Image.Image:
    """Create a gradient background"""
    img = Image.new('RGB', (width, height))
    draw = ImageDraw.Draw(img)
    
    if direction == 'vertical':
        for y in range(height):
            ratio = y / height
            r = int(color_start[0] * (1 - ratio) + color_end[0] * ratio)
            g = int(color_start[1] * (1 - ratio) + color_end[1] * ratio)
            b = int(color_start[2] * (1 - ratio) + color_end[2] * ratio)
            draw.line([(0, y), (width, y)], fill=(r, g, b))
    else:  # horizontal
        for x in range(width):
            ratio = x / width
            r = int(color_start[0] * (1 - ratio) + color_end[0] * ratio)
            g = int(color_start[1] * (1 - ratio) + color_end[1] * ratio)
            b = int(color_start[2] * (1 - ratio) + color_end[2] * ratio)
            draw.line([(x, 0), (x, height)], fill=(r, g, b))
    
    return img

def draw_text_with_shadow(
    draw: ImageDraw.ImageDraw,
    position: Tuple[int, int],
    text: str,
    font: ImageFont.FreeTypeFont,
    fill: Tuple[int, int, int],
    shadow_offset: int = 3
):
    """Draw text with shadow for better readability"""
    x, y = position
    # Shadow
    draw.text((x + shadow_offset, y + shadow_offset), text, fill=(0, 0, 0, 100), font=font)
    # Text
    draw.text((x, y), text, fill=fill, font=font)

def wrap_text(text: str, font: ImageFont.FreeTypeFont, max_width: int) -> List[str]:
    """Wrap text to fit within max_width"""
    words = text.split()
    lines = []
    current_line = []
    
    for word in words:
        test_line = ' '.join(current_line + [word])
        bbox = font.getbbox(test_line)
        if bbox[2] - bbox[0] <= max_width:
            current_line.append(word)
        else:
            if current_line:
                lines.append(' '.join(current_line))
            current_line = [word]
    
    if current_line:
        lines.append(' '.join(current_line))
    
    return lines

def create_title_slide(
    slide: Dict[str, Any],
    scheme: str = 'ocean'
) -> Image.Image:
    """Create an engaging title slide"""
    colors = COLOR_SCHEMES.get(scheme, COLOR_SCHEMES['ocean'])
    
    # Gradient background
    img = create_gradient_background(
        VIDEO_WIDTH, VIDEO_HEIGHT,
        colors['bg_start'], colors['bg_end'],
        'vertical'
    )
    draw = ImageDraw.Draw(img)
    
    # Add decorative elements
    # Top accent bar
    draw.rectangle([(0, 0), (VIDEO_WIDTH, 20)], fill=colors['primary'])
    
    # Bottom accent bar
    draw.rectangle([(0, VIDEO_HEIGHT - 20), (VIDEO_WIDTH, VIDEO_HEIGHT)], fill=colors['accent'])
    
    # Large title
    title = slide.get('title', 'Title')
    title_font = get_font(120, bold=True)
    
    # Wrap title if too long
    title_lines = wrap_text(title, title_font, VIDEO_WIDTH - 400)
    
    # Center vertically
    line_height = 140
    total_height = len(title_lines) * line_height
    start_y = (VIDEO_HEIGHT - total_height) // 2
    
    for i, line in enumerate(title_lines):
        bbox = draw.textbbox((0, 0), line, font=title_font)
        text_width = bbox[2] - bbox[0]
        x = (VIDEO_WIDTH - text_width) // 2
        y = start_y + i * line_height
        draw_text_with_shadow(draw, (x, y), line, title_font, colors['text_light'])
    
    # Subtitle if available
    if 'subtitle' in slide or slide.get('bullets'):
        subtitle = slide.get('subtitle', slide.get('bullets', [''])[0])
        subtitle_font = get_font(48)
        subtitle_lines = wrap_text(subtitle, subtitle_font, VIDEO_WIDTH - 600)
        
        y_offset = start_y + total_height + 80
        for line in subtitle_lines[:2]:  # Max 2 lines
            bbox = draw.textbbox((0, 0), line, font=subtitle_font)
            text_width = bbox[2] - bbox[0]
            x = (VIDEO_WIDTH - text_width) // 2
            draw.text((x, y_offset), line, fill=colors['secondary'], font=subtitle_font)
            y_offset += 60
    
    return img

def create_content_slide(
    slide: Dict[str, Any],
    scheme: str = 'ocean'
) -> Image.Image:
    """Create a content slide with bullets"""
    colors = COLOR_SCHEMES.get(scheme, COLOR_SCHEMES['ocean'])
    
    # Gradient background
    img = create_gradient_background(
        VIDEO_WIDTH, VIDEO_HEIGHT,
        colors['bg_start'], colors['bg_end'],
        'vertical'
    )
    draw = ImageDraw.Draw(img)
    
    # Top bar with title
    draw.rectangle([(0, 0), (VIDEO_WIDTH, 150)], fill=colors['primary'])
    
    # Title
    title = slide.get('title', 'Content')
    title_font = get_font(80, bold=True)
    draw_text_with_shadow(draw, (100, 40), title, title_font, colors['text_light'])
    
    # Decorative line
    draw.rectangle([(100, 130), (VIDEO_WIDTH - 100, 135)], fill=colors['accent'])
    
    # Bullets
    bullets = slide.get('bullets', [])
    bullet_font = get_font(52)
    y_offset = 250
    max_bullets = 5
    
    for i, bullet in enumerate(bullets[:max_bullets]):
        # Bullet point circle
        circle_x = 150
        circle_y = y_offset + 25
        draw.ellipse(
            [(circle_x - 15, circle_y - 15), (circle_x + 15, circle_y + 15)],
            fill=colors['accent']
        )
        
        # Bullet text with wrapping
        bullet_lines = wrap_text(bullet, bullet_font, VIDEO_WIDTH - 400)
        
        for j, line in enumerate(bullet_lines[:3]):  # Max 3 lines per bullet
            draw.text(
                (220, y_offset + j * 60),
                line,
                fill=colors['text_light'],
                font=bullet_font
            )
        
        y_offset += max(len(bullet_lines[:3]) * 60 + 40, 120)
        
        if y_offset > VIDEO_HEIGHT - 200:
            break
    
    # Footer decoration
    draw.rectangle([(0, VIDEO_HEIGHT - 10), (VIDEO_WIDTH, VIDEO_HEIGHT)], fill=colors['primary'])
    
    return img

def create_code_slide(
    slide: Dict[str, Any],
    scheme: str = 'midnight'
) -> Image.Image:
    """Create a slide optimized for code snippets"""
    colors = COLOR_SCHEMES['midnight']  # Always use midnight theme for code
    
    # Dark background
    img = Image.new('RGB', (VIDEO_WIDTH, VIDEO_HEIGHT), colors['bg_start'])
    draw = ImageDraw.Draw(img)
    
    # Header
    title = slide.get('title', 'Code Example')
    title_font = get_font(70, bold=True)
    draw.rectangle([(0, 0), (VIDEO_WIDTH, 120)], fill=(23, 23, 23))
    draw_text_with_shadow(draw, (80, 30), title, title_font, colors['primary'])
    
    # Code box
    code_box = [(80, 180), (VIDEO_WIDTH - 80, VIDEO_HEIGHT - 100)]
    draw.rectangle(code_box, fill=(30, 30, 30), outline=colors['primary'], width=3)
    
    # Code content
    bullets = slide.get('bullets', [])
    code_font = get_font(40)
    y_offset = 220
    
    for bullet in bullets[:8]:  # Max 8 lines
        # Add syntax highlighting effect with different colors
        if bullet.strip().startswith('#') or bullet.strip().startswith('//'):
            color = colors['secondary']  # Comments
        elif any(keyword in bullet for keyword in ['def ', 'class ', 'function ', 'const ', 'let ']):
            color = colors['accent']  # Keywords
        else:
            color = colors['text_light']
        
        draw.text((120, y_offset), bullet, fill=color, font=code_font)
        y_offset += 70
    
    return img

def create_summary_slide(
    slide: Dict[str, Any],
    scheme: str = 'minimal'
) -> Image.Image:
    """Create a summary/conclusion slide"""
    colors = COLOR_SCHEMES.get(scheme, COLOR_SCHEMES['minimal'])
    
    # Gradient background
    img = create_gradient_background(
        VIDEO_WIDTH, VIDEO_HEIGHT,
        colors['bg_end'], colors['bg_start'],
        'horizontal'
    )
    draw = ImageDraw.Draw(img)
    
    # Large centered title
    title = slide.get('title', 'Summary')
    title_font = get_font(100, bold=True)
    bbox = draw.textbbox((0, 0), title, font=title_font)
    text_width = bbox[2] - bbox[0]
    draw_text_with_shadow(
        draw,
        ((VIDEO_WIDTH - text_width) // 2, 200),
        title,
        title_font,
        colors['primary']
    )
    
    # Key points in boxes
    bullets = slide.get('bullets', [])
    bullet_font = get_font(48)
    
    if len(bullets) <= 3:
        # Horizontal layout
        box_width = 500
        box_height = 250
        spacing = 50
        total_width = len(bullets) * box_width + (len(bullets) - 1) * spacing
        start_x = (VIDEO_WIDTH - total_width) // 2
        y = 500
        
        for i, bullet in enumerate(bullets[:3]):
            x = start_x + i * (box_width + spacing)
            # Box with rounded corners effect
            draw.rectangle(
                [(x, y), (x + box_width, y + box_height)],
                fill=colors['primary'],
                outline=colors['accent'],
                width=4
            )
            
            # Text centered in box
            lines = wrap_text(bullet, bullet_font, box_width - 40)
            text_y = y + (box_height - len(lines) * 60) // 2
            for line in lines[:3]:
                bbox = draw.textbbox((0, 0), line, font=bullet_font)
                line_width = bbox[2] - bbox[0]
                draw.text(
                    (x + (box_width - line_width) // 2, text_y),
                    line,
                    fill=colors['text_light'],
                    font=bullet_font
                )
                text_y += 60
    else:
        # Vertical list
        y_offset = 450
        for bullet in bullets[:4]:
            draw.rectangle(
                [(200, y_offset), (VIDEO_WIDTH - 200, y_offset + 120)],
                fill=colors['primary'],
                outline=colors['accent'],
                width=3
            )
            draw.text((250, y_offset + 30), f"✓ {bullet}", fill=colors['text_light'], font=bullet_font)
            y_offset += 150
    
    return img

def generate_enhanced_slide(
    slide: Dict[str, Any],
    slide_index: int,
    total_slides: int,
    temp_dir: str,
    scheme: str = 'ocean'
) -> str:
    """
    Generate an enhanced slide image with professional design
    
    Args:
        slide: Slide dict with title, bullets, type
        slide_index: Index of this slide
        total_slides: Total number of slides
        temp_dir: Temporary directory for images
        scheme: Color scheme ('tech', 'professional', 'dark')
    
    Returns:
        Path to generated image
    """
    log.info(f'Generating enhanced slide {slide_index + 1}/{total_slides}')
    
    # Determine slide type
    slide_type = slide.get('type', 'content')
    title_lower = slide.get('title', '').lower()
    
    # Auto-detect slide type from content
    if slide_index == 0 or 'introduction' in title_lower or 'welcome' in title_lower:
        slide_type = 'title'
    elif 'code' in title_lower or 'example' in title_lower or 'implementation' in title_lower:
        slide_type = 'code'
    elif 'summary' in title_lower or 'conclusion' in title_lower or 'recap' in title_lower:
        slide_type = 'summary'
    elif slide_index == total_slides - 1:
        slide_type = 'summary'
    else:
        slide_type = 'content'
    
    # Generate appropriate slide
    if slide_type == 'title':
        img = create_title_slide(slide, scheme)
    elif slide_type == 'code':
        img = create_code_slide(slide, 'midnight')
    elif slide_type == 'summary':
        img = create_summary_slide(slide, scheme)
    else:
        img = create_content_slide(slide, scheme)
    
    # Save image
    image_path = os.path.join(temp_dir, f'slide_{slide_index}.png')
    img.save(image_path, quality=95)
    
    log.info(f'✅ Enhanced slide saved: {image_path} (type: {slide_type})')
    
    return image_path
