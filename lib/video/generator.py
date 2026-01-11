"""
Complete video generation pipeline with enhanced slide designs and animations
"""

import os
import uuid
from pathlib import Path
from typing import Dict, Any, Callable, Optional

from lib.logger import create_logger
from lib.video.tts import generate_audio
from lib.video.ffmpeg import create_video_from_frames, concatenate_videos, cleanup_temp_files, ensure_dir
from lib.video.animations import generate_animated_slide

log = create_logger('VGEN')

def generate_slide_image(
    slide: Dict[str, Any],
    slide_index: int,
    total_slides: int,
    temp_dir: str,
    color_scheme: str = 'ocean',
    animated: bool = False,  # Changed default to False for static slides
    fps: int = 24
) -> Dict[str, Any]:
    """
    Generate slide image - now defaults to STATIC for proper audio sync
    
    Args:
        slide: Slide dict with title, bullets, type
        slide_index: Index of this slide
        total_slides: Total number of slides
        temp_dir: Temporary directory for images
        color_scheme: Color scheme ('ocean', 'minimal', 'midnight')
        animated: Whether to create animations (False for proper sync)
        fps: Frames per second for animations
    
    Returns:
        Dict with frame paths or single image path
    """
    try:
        if animated:
            # Generate animated frames (1 second of animation)
            frame_paths = generate_animated_slide(
                slide=slide,
                slide_index=slide_index,
                total_slides=total_slides,
                temp_dir=temp_dir,
                fps=fps,
                duration=1.0,  # Short animation
                scheme=color_scheme
            )
            
            # Return pattern for FFmpeg
            frame_pattern = os.path.join(temp_dir, f'slide_{slide_index}_frame_%04d.png')
            
            return {
                'animated': True,
                'frame_pattern': frame_pattern,
                'frame_count': len(frame_paths),
                'fps': fps
            }
        else:
            # Fallback to static image
            from lib.video.slide_designer import generate_enhanced_slide
            image_path = generate_enhanced_slide(
                slide=slide,
                slide_index=slide_index,
                total_slides=total_slides,
                temp_dir=temp_dir,
                scheme=color_scheme
            )
            return {'animated': False, 'path': image_path}
        
    except Exception as e:
        log.error(f'Slide generation failed: {e}')
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
    callbacks: Optional[Dict[str, Callable]] = None,
    color_scheme: str = 'ocean'
) -> Dict[str, Any]:
    """
    Generate a complete video from a storyboard
    
    Args:
        video_id: Unique video ID
        storyboard: Storyboard dict with slides
        callbacks: Optional callbacks for progress updates
        color_scheme: Visual theme ('tech', 'professional', 'dark')
        
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
            
            # Generate STATIC slide and audio for perfect sync
            image_result = generate_slide_image(
                slide, i, total_slides, temp_dir,
                color_scheme=color_scheme,
                animated=False,  # Use static slides for proper audio sync
                fps=24
            )
            audio_result = generate_slide_audio(slide, i, temp_dir)
            
            all_assets.append((image_result, audio_result))
        
        # Phase 2: Create slide videos with static images matched to audio
        on_status('Creating slide videos...', 50)
        
        slide_videos = []
        total_duration = 0
        
        for i, (image_result, audio_result) in enumerate(all_assets):
            progress = 50 + int((i / total_slides) * 40)
            on_slide_start(i + 1, total_slides, slides[i].get('title', ''))
            on_status(f'Encoding slide {i + 1}/{total_slides}', progress)
            
            slide_video_path = os.path.join(temp_dir, f'slide_{i}.mp4')
            
            if image_result.get('animated'):
                # Create video from animated frames
                create_video_from_frames(
                    image_result['frame_pattern'],
                    audio_result['path'],
                    slide_video_path,
                    fps=image_result['fps'],
                    audio_duration=audio_result['duration']
                )
            else:
                # Fallback to static image
                from lib.video.ffmpeg import create_slide_video
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
