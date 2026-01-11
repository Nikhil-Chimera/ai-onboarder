"""
Complete video generation pipeline
"""

import os
import uuid
from pathlib import Path
from typing import Dict, Any, Callable, Optional
from PIL import Image, ImageDraw, ImageFont

from lib.logger import create_logger
from lib.video.tts import generate_audio
from lib.video.ffmpeg import create_slide_video, concatenate_videos, cleanup_temp_files, ensure_dir

log = create_logger('VGEN')

# Video dimensions
VIDEO_WIDTH = 1920
VIDEO_HEIGHT = 1080

def generate_slide_image(slide: Dict[str, Any], slide_index: int, temp_dir: str) -> Dict[str, str]:
    """
    Generate an image for a slide
    
    For simplicity, we create a text-based slide image.
    In production, you could use Gemini's image generation or DALL-E.
    """
    log.info(f'Generating image for slide {slide_index + 1}')
    
    try:
        # Create a simple slide image with PIL
        img = Image.new('RGB', (VIDEO_WIDTH, VIDEO_HEIGHT), color=(240, 240, 245))
        draw = ImageDraw.Draw(img)
        
        # Try to use a nice font, fall back to default
        try:
            title_font = ImageFont.truetype("arial.ttf", 80)
            bullet_font = ImageFont.truetype("arial.ttf", 48)
        except:
            title_font = ImageFont.load_default()
            bullet_font = ImageFont.load_default()
        
        # Draw title
        title = slide.get('title', 'Slide Title')
        title_bbox = draw.textbbox((0, 0), title, font=title_font)
        title_width = title_bbox[2] - title_bbox[0]
        draw.text(
            ((VIDEO_WIDTH - title_width) // 2, 200),
            title,
            fill=(50, 50, 50),
            font=title_font
        )
        
        # Draw bullets
        bullets = slide.get('bullets', [])
        y_offset = 400
        for bullet in bullets[:4]:  # Max 4 bullets
            bullet_text = f"• {bullet}"
            draw.text((200, y_offset), bullet_text, fill=(80, 80, 80), font=bullet_font)
            y_offset += 100
        
        # Save image
        image_path = os.path.join(temp_dir, f'slide_{slide_index}.png')
        img.save(image_path)
        
        log.info(f'Image saved: {image_path}')
        
        return {'path': image_path}
        
    except Exception as e:
        log.error(f'Image generation failed: {e}')
        raise

def generate_slide_audio(slide: Dict[str, Any], slide_index: int, temp_dir: str) -> Dict[str, Any]:
    """Generate audio for a slide"""
    log.info(f'Generating audio for slide {slide_index + 1}')
    
    voiceover = slide.get('voiceover', '')
    audio_path = os.path.join(temp_dir, f'audio_{slide_index}.mp3')
    
    return generate_audio(voiceover, audio_path)

async def generate_video_async(
    video_id: str,
    storyboard: Dict[str, Any],
    callbacks: Optional[Dict[str, Callable]] = None
) -> Dict[str, Any]:
    """
    Generate a complete video from a storyboard
    
    Args:
        video_id: Unique video ID
        storyboard: Storyboard dict with slides
        callbacks: Optional callbacks for progress updates
        
    Returns:
        Dict with videoUrl and duration
    """
    log.info('=' * 80)
    log.info('VIDEO GENERATION PIPELINE')
    log.info('=' * 80)
    
    callbacks = callbacks or {}
    on_status = callbacks.get('onStatus', lambda msg, progress=None: None)
    on_slide_start = callbacks.get('onSlideStart', lambda idx, total, title: None)
    on_slide_complete = callbacks.get('onSlideComplete', lambda idx, total: None)
    
    # Setup directories
    videos_dir = os.path.join('public', 'videos')
    temp_dir = os.path.join(videos_dir, f'temp-{video_id}')
    
    ensure_dir(videos_dir)
    ensure_dir(temp_dir)
    
    slides = storyboard.get('slides', [])
    total_slides = len(slides)
    
    if total_slides == 0:
        raise ValueError('No slides in storyboard')
    
    log.info(f'Generating video with {total_slides} slides')
    
    try:
        # Phase 1: Generate all assets
        on_status('Generating images and audio...', 5)
        
        all_assets = []
        for i, slide in enumerate(slides):
            log.info(f'Processing slide {i + 1}/{total_slides}')
            
            progress = 5 + int((i / total_slides) * 45)
            on_status(f'Generating slide {i + 1}/{total_slides}', progress)
            
            # Generate image and audio
            image_result = generate_slide_image(slide, i, temp_dir)
            audio_result = generate_slide_audio(slide, i, temp_dir)
            
            all_assets.append((image_result, audio_result))
        
        # Phase 2: Create slide videos
        on_status('Creating slide videos...', 50)
        
        slide_videos = []
        total_duration = 0
        
        for i, (image_result, audio_result) in enumerate(all_assets):
            progress = 50 + int((i / total_slides) * 40)
            on_slide_start(i + 1, total_slides, slides[i].get('title', ''))
            on_status(f'Encoding slide {i + 1}/{total_slides}', progress)
            
            slide_video_path = os.path.join(temp_dir, f'slide_{i}.mp4')
            
            create_slide_video(
                image_result['path'],
                audio_result['path'],
                slide_video_path,
                audio_result['duration']
            )
            
            slide_videos.append(slide_video_path)
            total_duration += audio_result['duration']
            
            on_slide_complete(i + 1, total_slides)
        
        # Phase 3: Concatenate
        on_status('Finalizing video...', 90)
        
        final_video_path = os.path.join(videos_dir, f'{video_id}.mp4')
        concatenate_videos(slide_videos, final_video_path)
        
        on_status('Complete!', 100)
        
        # Cleanup
        cleanup_temp_files(temp_dir)
        
        video_url = f'/videos/{video_id}.mp4'
        
        log.info('=' * 80)
        log.info(f'VIDEO COMPLETE: {video_url}')
        log.info(f'Duration: {total_duration:.1f}s')
        log.info('=' * 80)
        
        return {
            'videoUrl': video_url,
            'duration': total_duration
        }
        
    except Exception as e:
        log.error(f'Video generation failed: {e}')
        cleanup_temp_files(temp_dir)
        raise
