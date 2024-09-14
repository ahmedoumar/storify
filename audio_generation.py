from gtts import gTTS
import tempfile
import os
import streamlit as st
from pydub import AudioSegment
import io

@st.cache_data
def text_to_speech(text, lang='en', slow=False):
    """
    Convert text to speech using Google Text-to-Speech API.
    
    Args:
    text (str): The text to convert to speech.
    lang (str): The language of the text (default is English).
    slow (bool): Whether to speak slowly (default is False).
    
    Returns:
    bytes: The audio data as bytes.
    """
    try:
        tts = gTTS(text=text, lang=lang, slow=slow)
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_file:
            tts.save(temp_file.name)
            temp_file_path = temp_file.name
        
        with open(temp_file_path, "rb") as audio_file:
            audio_bytes = audio_file.read()
        
        os.unlink(temp_file_path)
        
        return audio_bytes
    except Exception as e:
        st.error(f"Failed to generate audio: {str(e)}")
        return None

def split_text(text, max_length=5000):
    """
    Split long text into smaller chunks that fit within gTTS character limit.
    
    Args:
    text (str): The text to split.
    max_length (int): The maximum length of each chunk.
    
    Returns:
    list: A list of text chunks.
    """
    words = text.split()
    chunks = []
    current_chunk = []

    for word in words:
        if len(' '.join(current_chunk + [word])) <= max_length:
            current_chunk.append(word)
        else:
            chunks.append(' '.join(current_chunk))
            current_chunk = [word]

    if current_chunk:
        chunks.append(' '.join(current_chunk))

    return chunks

@st.cache_data
def generate_audio_for_story(story_text, lang='en'):
    """
    Generate audio for a complete story, handling long texts by splitting them.
    
    Args:
    story_text (str): The complete story text.
    lang (str): The language of the text.
    
    Returns:
    bytes: The complete audio data as bytes.
    """
    chunks = split_text(story_text)
    audio_segments = []

    for chunk in chunks:
        audio_bytes = text_to_speech(chunk, lang)
        if audio_bytes:
            audio_segment = AudioSegment.from_mp3(io.BytesIO(audio_bytes))
            audio_segments.append(audio_segment)

    if audio_segments:
        combined_audio = sum(audio_segments)
        buffer = io.BytesIO()
        combined_audio.export(buffer, format="mp3")
        return buffer.getvalue()
    else:
        return None

def detect_language(text):
    """
    Detect the language of the given text.
    This is a placeholder function. You might want to use a more sophisticated
    language detection library like langdetect or google-cloud-translate.
    
    Args:
    text (str): The text to detect the language for.
    
    Returns:
    str: The detected language code.
    """
    # This is a very basic detection. In a real application, you'd want to use
    # a more robust method.
    if any('\u4e00' <= char <= '\u9fff' for char in text):
        return 'zh-cn'  # Chinese
    elif any('\u3040' <= char <= '\u30ff' for char in text):
        return 'ja'  # Japanese
    elif any('\uac00' <= char <= '\ud7a3' for char in text):
        return 'ko'  # Korean
    # Add more language checks as needed
    else:
        return 'en'  # Default to English

def adjust_speech_rate(audio_segment, speed_factor=1.0):
    """
    Adjust the speech rate of an audio segment.
    
    Args:
    audio_segment (AudioSegment): The audio segment to adjust.
    speed_factor (float): The factor by which to adjust the speed. 
                          1.0 is normal speed, 0.5 is half speed, 2.0 is double speed.
    
    Returns:
    AudioSegment: The speed-adjusted audio segment.
    """
    return audio_segment.speedup(playback_speed=speed_factor)

# You can add more audio processing functions here as needed
