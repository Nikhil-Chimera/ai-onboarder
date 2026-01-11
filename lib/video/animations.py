"""
Advanced animations for interactive video slides
Creates multiple image frames with motion effects for smooth animations
"""

import os
from typing import Dict, Any, List, Tuple
from PIL import Image, ImageDraw, ImageFont
import math

from lib.logger import create_logger
from lib.video.slide_designer import (
    get_font, COLOR_SCHEMES, VIDEO_WIDTH, VIDEO_HEIGHT,
    create_gradient_background, wrap_text
)

log = create_logger('ANIM')

def ease_out_cubic(t: float) -> float:
    """Easing function for smooth animation"""
    return 1 - pow(1 - t, 3)

def ease_in_out_cubic(t: float) -> float:
    """Easing function for smooth in-out animation"""
    if t < 0.5:
        return 4 * t * t * t
    else:
        return 1 - pow(-2 * t + 2, 3) / 2

def create_animated_title_slide(
    slide: Dict[str, Any],
    frame_count: int,
    temp_dir: str,
    slide_index: int,
    scheme: str = 'ocean'
) -> List[str]:
    """
    Create animated title slide with fade-in and slide-in effects
    
    Args:
        slide: Slide data
        frame_count: Number of frames to generate (24 = 1 second at 24fps)
        temp_dir: Directory for frame images
        slide_index: Index of slide
        scheme: Color scheme
    
    Returns:
        List of frame image paths
    """
    colors = COLOR_SCHEMES.get(scheme, COLOR_SCHEMES['ocean'])
    frame_paths = []
    
    title = slide.get('title', 'Title')
    title_font = get_font(120, bold=True)
    subtitle = slide.get('subtitle', slide.get('bullets', [''])[0] if slide.get('bullets') else '')
    subtitle_font = get_font(48)
    
    for frame in range(frame_count):
        # Progress from 0 to 1
        progress = frame / max(frame_count - 1, 1)
        eased_progress = ease_out_cubic(progress)
        
        # Create base gradient
        img = create_gradient_background(
            VIDEO_WIDTH, VIDEO_HEIGHT,
            colors['bg_start'], colors['bg_end'],
            'vertical'
        )
        draw = ImageDraw.Draw(img, 'RGBA')
        
        # Animated accent bars
        bar_width = int(VIDEO_WIDTH * eased_progress)
        draw.rectangle([(0, 0), (bar_width, 20)], fill=colors['primary'])
        draw.rectangle([(VIDEO_WIDTH - bar_width, VIDEO_HEIGHT - 20), (VIDEO_WIDTH, VIDEO_HEIGHT)], fill=colors['accent'])
        
        # Title animation - slide in from left + fade in
        if progress > 0.1:  # Start after 10%
            title_progress = min((progress - 0.1) / 0.5, 1.0)  # 50% of time for title
            title_eased = ease_out_cubic(title_progress)
            
            # Calculate position
            title_lines = wrap_text(title, title_font, VIDEO_WIDTH - 400)
            line_height = 140
            total_height = len(title_lines) * line_height
            start_y = (VIDEO_HEIGHT - total_height) // 2
            
            # Slide in from left
            offset_x = int(-300 * (1 - title_eased))
            alpha = int(255 * title_eased)
            
            for i, line in enumerate(title_lines):
                bbox = draw.textbbox((0, 0), line, font=title_font)
                text_width = bbox[2] - bbox[0]
                x = (VIDEO_WIDTH - text_width) // 2 + offset_x
                y = start_y + i * line_height
                
                # Create text with alpha
                text_img = Image.new('RGBA', (VIDEO_WIDTH, VIDEO_HEIGHT), (0, 0, 0, 0))
                text_draw = ImageDraw.Draw(text_img)
                
                # Shadow
                text_draw.text((x + 3, y + 3), line, fill=(*[0, 0, 0], alpha // 2), font=title_font)
                # Text
                text_draw.text((x, y), line, fill=(*colors['text_light'], alpha), font=title_font)
                
                img = Image.alpha_composite(img.convert('RGBA'), text_img)
        
        # Subtitle animation - slide in from right + fade in
        if subtitle and progress > 0.4:  # Start after title
            subtitle_progress = min((progress - 0.4) / 0.4, 1.0)
            subtitle_eased = ease_out_cubic(subtitle_progress)
            
            subtitle_lines = wrap_text(subtitle, subtitle_font, VIDEO_WIDTH - 600)
            y_offset = (VIDEO_HEIGHT // 2) + 200
            
            # Slide in from right
            offset_x = int(300 * (1 - subtitle_eased))
            alpha = int(255 * subtitle_eased)
            
            for line in subtitle_lines[:2]:
                bbox = draw.textbbox((0, 0), line, font=subtitle_font)
                text_width = bbox[2] - bbox[0]
                x = (VIDEO_WIDTH - text_width) // 2 + offset_x
                
                text_img = Image.new('RGBA', (VIDEO_WIDTH, VIDEO_HEIGHT), (0, 0, 0, 0))
                text_draw = ImageDraw.Draw(text_img)
                text_draw.text((x, y_offset), line, fill=(*colors['secondary'], alpha), font=subtitle_font)
                img = Image.alpha_composite(img.convert('RGBA'), text_img)
                y_offset += 60
        
        # Save frame
        frame_path = os.path.join(temp_dir, f'slide_{slide_index}_frame_{frame:04d}.png')
        img.convert('RGB').save(frame_path, quality=95)
        frame_paths.append(frame_path)
    
    log.info(f'✅ Generated {len(frame_paths)} animated frames for title slide')
    return frame_paths

def create_animated_content_slide(
    slide: Dict[str, Any],
    frame_count: int,
    temp_dir: str,
    slide_index: int,
    scheme: str = 'ocean'
) -> List[str]:
    """
    Create animated content slide with bullets appearing one by one
    """
    colors = COLOR_SCHEMES.get(scheme, COLOR_SCHEMES['ocean'])
    frame_paths = []
    
    title = slide.get('title', 'Content')
    title_font = get_font(80, bold=True)
    bullets = slide.get('bullets', [])[:5]
    bullet_font = get_font(52)
    
    for frame in range(frame_count):
        progress = frame / max(frame_count - 1, 1)
        
        # Base gradient
        img = create_gradient_background(
            VIDEO_WIDTH, VIDEO_HEIGHT,
            colors['bg_start'], colors['bg_end'],
            'vertical'
        )
        draw = ImageDraw.Draw(img, 'RGBA')
        
        # Top bar - slide in
        bar_progress = min(progress / 0.2, 1.0)  # First 20%
        bar_eased = ease_out_cubic(bar_progress)
        bar_height = int(150 * bar_eased)
        
        draw.rectangle([(0, 0), (VIDEO_WIDTH, bar_height)], fill=colors['primary'])
        
        if bar_progress >= 1.0:
            # Title
            draw.text((100, 40), title, fill=colors['text_light'], font=title_font)
            
            # Animated decorative line
            line_progress = min((progress - 0.2) / 0.1, 1.0)
            line_width = int((VIDEO_WIDTH - 200) * ease_out_cubic(line_progress))
            draw.rectangle([(100, 130), (100 + line_width, 135)], fill=colors['accent'])
        
        # Bullets appear one by one
        if progress > 0.3:
            y_offset = 250
            bullets_progress = (progress - 0.3) / 0.7  # Remaining 70% for bullets
            
            for i, bullet in enumerate(bullets):
                bullet_start = i / len(bullets) if bullets else 0
                bullet_end = (i + 1) / len(bullets) if bullets else 1
                
                if bullets_progress >= bullet_start:
                    # Calculate this bullet's progress
                    bullet_progress = min((bullets_progress - bullet_start) / (bullet_end - bullet_start), 1.0)
                    bullet_eased = ease_out_cubic(bullet_progress)
                    
                    # Slide in from left
                    offset_x = int(-200 * (1 - bullet_eased))
                    alpha = int(255 * bullet_eased)
                    
                    # Bullet circle
                    circle_x = 150 + offset_x
                    circle_y = y_offset + 25
                    
                    # Pulsing effect
                    pulse = math.sin(progress * math.pi * 4 + i) * 3 if bullet_progress >= 1.0 else 0
                    radius = int(15 + pulse)
                    
                    text_img = Image.new('RGBA', (VIDEO_WIDTH, VIDEO_HEIGHT), (0, 0, 0, 0))
                    text_draw = ImageDraw.Draw(text_img)
                    
                    text_draw.ellipse(
                        [(circle_x - radius, circle_y - radius), (circle_x + radius, circle_y + radius)],
                        fill=(*colors['accent'], alpha)
                    )
                    
                    # Bullet text
                    bullet_lines = wrap_text(bullet, bullet_font, VIDEO_WIDTH - 400)
                    for j, line in enumerate(bullet_lines[:3]):
                        text_draw.text(
                            (220 + offset_x, y_offset + j * 60),
                            line,
                            fill=(*colors['text_light'], alpha),
                            font=bullet_font
                        )
                    
                    img = Image.alpha_composite(img.convert('RGBA'), text_img)
                    
                    y_offset += max(len(bullet_lines[:3]) * 60 + 40, 120)
        
        # Bottom bar
        draw.rectangle([(0, VIDEO_HEIGHT - 10), (VIDEO_WIDTH, VIDEO_HEIGHT)], fill=colors['primary'])
        
        # Save frame
        frame_path = os.path.join(temp_dir, f'slide_{slide_index}_frame_{frame:04d}.png')
        img.convert('RGB').save(frame_path, quality=95)
        frame_paths.append(frame_path)
    
    log.info(f'✅ Generated {len(frame_paths)} animated frames for content slide')
    return frame_paths

def create_animated_summary_slide(
    slide: Dict[str, Any],
    frame_count: int,
    temp_dir: str,
    slide_index: int,
    scheme: str = 'minimal'
) -> List[str]:
    """
    Create animated summary slide with boxes zooming in
    """
    colors = COLOR_SCHEMES.get(scheme, COLOR_SCHEMES['minimal'])
    frame_paths = []
    
    title = slide.get('title', 'Summary')
    title_font = get_font(100, bold=True)
    bullets = slide.get('bullets', [])[:3]
    bullet_font = get_font(48)
    
    for frame in range(frame_count):
        progress = frame / max(frame_count - 1, 1)
        
        # Base gradient
        img = create_gradient_background(
            VIDEO_WIDTH, VIDEO_HEIGHT,
            colors['bg_end'], colors['bg_start'],
            'horizontal'
        )
        draw = ImageDraw.Draw(img, 'RGBA')
        
        # Title fade + scale in
        if progress > 0.1:
            title_progress = min((progress - 0.1) / 0.3, 1.0)
            title_eased = ease_out_cubic(title_progress)
            
            scale = 0.5 + 0.5 * title_eased
            alpha = int(255 * title_eased)
            
            # Scale font (approximate by changing size)
            scaled_size = int(100 * scale)
            scaled_font = get_font(scaled_size, bold=True)
            
            bbox = draw.textbbox((0, 0), title, font=scaled_font)
            text_width = bbox[2] - bbox[0]
            
            text_img = Image.new('RGBA', (VIDEO_WIDTH, VIDEO_HEIGHT), (0, 0, 0, 0))
            text_draw = ImageDraw.Draw(text_img)
            text_draw.text(
                ((VIDEO_WIDTH - text_width) // 2, 200),
                title,
                fill=(*colors['primary'], alpha),
                font=scaled_font
            )
            img = Image.alpha_composite(img.convert('RGBA'), text_img)
        
        # Boxes zoom in
        if bullets and progress > 0.4:
            box_width = 500
            box_height = 250
            spacing = 50
            total_width = len(bullets) * box_width + (len(bullets) - 1) * spacing
            start_x = (VIDEO_WIDTH - total_width) // 2
            y = 500
            
            for i, bullet in enumerate(bullets):
                box_start = 0.4 + i * 0.15
                if progress >= box_start:
                    box_progress = min((progress - box_start) / 0.2, 1.0)
                    box_eased = ease_out_cubic(box_progress)
                    
                    x = start_x + i * (box_width + spacing)
                    
                    # Zoom from center
                    scale = 0.3 + 0.7 * box_eased
                    alpha = int(255 * box_eased)
                    
                    scaled_width = int(box_width * scale)
                    scaled_height = int(box_height * scale)
                    
                    # Center the scaled box
                    box_x = x + (box_width - scaled_width) // 2
                    box_y = y + (box_height - scaled_height) // 2
                    
                    text_img = Image.new('RGBA', (VIDEO_WIDTH, VIDEO_HEIGHT), (0, 0, 0, 0))
                    text_draw = ImageDraw.Draw(text_img)
                    
                    # Box
                    text_draw.rectangle(
                        [(box_x, box_y), (box_x + scaled_width, box_y + scaled_height)],
                        fill=(*colors['primary'], alpha),
                        outline=(*colors['accent'], alpha),
                        width=4
                    )
                    
                    # Text (if box is large enough)
                    if scale > 0.6:
                        lines = wrap_text(bullet, bullet_font, scaled_width - 40)
                        text_y = box_y + (scaled_height - len(lines) * 60) // 2
                        for line in lines[:3]:
                            bbox = text_draw.textbbox((0, 0), line, font=bullet_font)
                            line_width = bbox[2] - bbox[0]
                            text_draw.text(
                                (box_x + (scaled_width - line_width) // 2, text_y),
                                line,
                                fill=(*colors['text_light'], alpha),
                                font=bullet_font
                            )
                            text_y += 60
                    
                    img = Image.alpha_composite(img.convert('RGBA'), text_img)
        
        # Save frame
        frame_path = os.path.join(temp_dir, f'slide_{slide_index}_frame_{frame:04d}.png')
        img.convert('RGB').save(frame_path, quality=95)
        frame_paths.append(frame_path)
    
    log.info(f'✅ Generated {len(frame_paths)} animated frames for summary slide')
    return frame_paths

def generate_animated_slide(
    slide: Dict[str, Any],
    slide_index: int,
    total_slides: int,
    temp_dir: str,
    fps: int = 24,
    duration: float = 1.0,  # Reduced from 3.0 to 1.0 second for cost savings
    scheme: str = 'ocean'
) -> List[str]:
    """
    Generate animated frames for a slide
    
    Args:
        slide: Slide data
        slide_index: Index of this slide
        total_slides: Total number of slides
        temp_dir: Temporary directory
        fps: Frames per second
        duration: Animation duration in seconds
        scheme: Color scheme
    
    Returns:
        List of frame image paths
    """
    frame_count = int(fps * duration)
    
    # Determine slide type
    slide_type = slide.get('type', 'content')
    title_lower = slide.get('title', '').lower()
    
    if slide_index == 0 or 'introduction' in title_lower or 'welcome' in title_lower:
        slide_type = 'title'
    elif 'summary' in title_lower or 'conclusion' in title_lower or slide_index == total_slides - 1:
        slide_type = 'summary'
    else:
        slide_type = 'content'
    
    log.info(f'Generating animated {slide_type} slide {slide_index + 1}/{total_slides} ({frame_count} frames)')
    
    # Generate frames based on type
    if slide_type == 'title':
        return create_animated_title_slide(slide, frame_count, temp_dir, slide_index, scheme)
    elif slide_type == 'summary':
        return create_animated_summary_slide(slide, frame_count, temp_dir, slide_index, scheme)
    else:
        return create_animated_content_slide(slide, frame_count, temp_dir, slide_index, scheme)
