"""
FFmpeg video generation utilities
"""

import os
import subprocess
from pathlib import Path
from typing import List
import imageio_ffmpeg

from lib.logger import create_logger

log = create_logger('FFMPEG')

# Get ffmpeg executable from imageio-ffmpeg
FFMPEG_EXE = imageio_ffmpeg.get_ffmpeg_exe()

# Verify FFmpeg is accessible
if not os.path.exists(FFMPEG_EXE):
    log.error(f'FFmpeg not found at: {FFMPEG_EXE}')
    raise FileNotFoundError(f'FFmpeg executable not found: {FFMPEG_EXE}')
else:
    log.info(f'FFmpeg found at: {FFMPEG_EXE}')

def ensure_dir(directory: str):
    """Ensure directory exists"""
    Path(directory).mkdir(parents=True, exist_ok=True)

def create_slide_video(image_path: str, audio_path: str, output_path: str, audio_duration: float):
    """
    Create a video from an image and audio
    
    Args:
        image_path: Path to slide image
        audio_path: Path to audio file
        output_path: Path for output video
        audio_duration: Duration of audio in seconds
    """
    log.info(f'Creating slide video: {audio_duration:.1f}s')
    log.info(f'Image: {image_path} (exists: {os.path.exists(image_path)})')
    log.info(f'Audio: {audio_path} (exists: {os.path.exists(audio_path)})')
    
    # Validate inputs
    if not os.path.exists(image_path):
        raise FileNotFoundError(f'Image file not found: {image_path}')
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f'Audio file not found: {audio_path}')
    
    try:
        # Ensure output directory exists
        output_dir = os.path.dirname(output_path)
        if output_dir:
            ensure_dir(output_dir)
        
        # FFmpeg command to create video from image + audio
        command = [
            FFMPEG_EXE,
            '-loop', '1',
            '-i', image_path,
            '-i', audio_path,
            '-c:v', 'libx264',
            '-tune', 'stillimage',
            '-c:a', 'aac',
            '-b:a', '192k',
            '-pix_fmt', 'yuv420p',
            '-shortest',
            '-t', str(audio_duration),
            '-y',  # Overwrite output file
            output_path
        ]
        
        log.info(f'Running FFmpeg command: {" ".join(command[:3])}...')
        
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode != 0:
            log.error(f'FFmpeg error: {result.stderr}')
            raise RuntimeError(f'FFmpeg failed: {result.stderr}')
        
        # Verify output was created
        if not os.path.exists(output_path):
            raise FileNotFoundError(f'Output video not created: {output_path}')
        
        log.info(f'✅ Slide video created: {output_path}')
        
    except subprocess.TimeoutExpired:
        log.error('FFmpeg timeout')
        raise RuntimeError('Video creation timed out')
    except Exception as e:
        log.error(f'Video creation failed: {e}')
        import traceback
        traceback.print_exc()
        raise

def concatenate_videos(video_paths: List[str], output_path: str):
    """
    Concatenate multiple videos into one
    
    Args:
        video_paths: List of video file paths
        output_path: Path for final concatenated video
    """
    log.info(f'Concatenating {len(video_paths)} videos')
    
    try:
        # Create concat file
        concat_file = output_path + '.txt'
        with open(concat_file, 'w') as f:
            for video_path in video_paths:
                f.write(f"file '{os.path.abspath(video_path)}'\n")
        
        # FFmpeg concat command
        command = [
            FFMPEG_EXE,
            '-f', 'concat',
            '-safe', '0',
            '-i', concat_file,
            '-c', 'copy',
            '-y',
            output_path
        ]
        
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=300
        )
        
        if result.returncode != 0:
            log.error(f'FFmpeg concat error: {result.stderr}')
            raise RuntimeError(f'Video concatenation failed: {result.stderr}')
        
        # Clean up concat file
        os.remove(concat_file)
        
        log.info(f'Videos concatenated: {output_path}')
        
    except subprocess.TimeoutExpired:
        log.error('FFmpeg concat timeout')
        raise RuntimeError('Video concatenation timed out')
    except Exception as e:
        log.error(f'Concatenation failed: {e}')
        raise

def cleanup_temp_files(temp_dir: str):
    """Clean up temporary files"""
    import shutil
    try:
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
            log.info(f'Cleaned up temp directory: {temp_dir}')
    except Exception as e:
        log.warning(f'Cleanup failed: {e}')
