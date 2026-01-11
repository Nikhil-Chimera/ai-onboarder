"""
Text-to-Speech module using gTTS
"""

import os
from pathlib import Path
from gtts import gTTS
import imageio_ffmpeg

from lib.logger import create_logger

log = create_logger('TTS')

# Configure ffmpeg path
FFMPEG_EXE = imageio_ffmpeg.get_ffmpeg_exe()
log.info(f'Using FFmpeg at: {FFMPEG_EXE}')

# Import AudioSegment after setting environment
os.environ['IMAGEIO_FFMPEG_EXE'] = FFMPEG_EXE
from pydub import AudioSegment
AudioSegment.converter = FFMPEG_EXE
AudioSegment.ffmpeg = FFMPEG_EXE

# For pydub, we need to suppress the ffprobe warning since we only use ffmpeg
import warnings
warnings.filterwarnings('ignore', message='Couldn\'t find ffprobe')

def generate_audio(text: str, output_path: str, lang: str = 'en') -> dict:
    """
    Generate audio from text using Google Text-to-Speech
    
    Args:
        text: Text to convert to speech
        output_path: Path to save audio file
        lang: Language code (default: 'en')
        
    Returns:
        Dict with path and duration
    """
    log.info(f'Generating audio: {len(text)} characters')
    
    try:
        # Ensure output directory exists
        output_dir = os.path.dirname(output_path)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
        
        # Generate speech
        tts = gTTS(text=text, lang=lang, slow=False)
        tts.save(output_path)
        log.info(f'Audio saved to: {output_path}')
        
        # Small delay to ensure file is fully written
        import time
        time.sleep(0.1)
        
        # Verify file exists
        if not os.path.exists(output_path):
            raise FileNotFoundError(f'Audio file not created: {output_path}')
        
        # Get file size to ensure it's not empty
        file_size = os.path.getsize(output_path)
        if file_size == 0:
            raise ValueError(f'Audio file is empty: {output_path}')
        log.info(f'Audio file size: {file_size} bytes')
        
        # Get duration - use estimation if pydub fails
        try:
            audio = AudioSegment.from_mp3(output_path)
            duration_seconds = len(audio) / 1000.0  # Convert ms to seconds
            log.info(f'Audio generated: {duration_seconds:.1f}s')
        except Exception as e:
            log.warning(f'Could not get audio duration with pydub: {e}, estimating...')
            # Estimate duration based on text length (roughly 150 words per minute)
            words = len(text.split())
            duration_seconds = max(3.0, (words / 150) * 60)  # Minimum 3 seconds
            log.info(f'Estimated duration: {duration_seconds:.1f}s')
        
        return {
            'path': output_path,
            'duration': duration_seconds
        }
        
    except Exception as e:
        log.error(f'Audio generation failed: {e}')
        import traceback
        traceback.print_exc()
        raise
