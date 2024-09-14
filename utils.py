from PIL import Image
from io import BytesIO
import base64
import re
import streamlit as st

def image_to_base64(img):
    """
    Convert a PIL Image to a base64 encoded string.

    Args:
    img (PIL.Image.Image): The image to convert.

    Returns:
    str: The base64 encoded string of the image.
    """
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode()

def base64_to_image(base64_string):
    """
    Convert a base64 encoded string to a PIL Image.

    Args:
    base64_string (str): The base64 encoded string of the image.

    Returns:
    PIL.Image.Image: The decoded image.
    """
    return Image.open(BytesIO(base64.b64decode(base64_string)))

@st.cache_data
def sanitize_filename(filename):
    """
    Sanitize a filename by removing or replacing invalid characters.

    Args:
    filename (str): The filename to sanitize.

    Returns:
    str: The sanitized filename.
    """
    # Remove any non-word characters (everything except numbers and letters)
    filename = re.sub(r"[^\w\s-]", "", filename.lower())
    # Replace all runs of whitespace with a single dash
    return re.sub(r"\s+", "-", filename).strip("-")

def truncate_text(text, max_length=100):
    """
    Truncate text to a specified maximum length, adding an ellipsis if truncated.

    Args:
    text (str): The text to truncate.
    max_length (int): The maximum length of the truncated text.

    Returns:
    str: The truncated text.
    """
    return (text[:max_length] + '...') if len(text) > max_length else text

def format_time(seconds):
    """
    Format a duration in seconds to a string representation.

    Args:
    seconds (int): The duration in seconds.

    Returns:
    str: A formatted string representation of the duration.
    """
    minutes, secs = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    if hours > 0:
        return f"{hours}h {minutes}m {secs}s"
    elif minutes > 0:
        return f"{minutes}m {secs}s"
    else:
        return f"{secs}s"

@st.cache_data
def count_words(text):
    """
    Count the number of words in a given text.

    Args:
    text (str): The text to count words in.

    Returns:
    int: The number of words in the text.
    """
    return len(text.split())

def generate_filename(title, extension):
    """
    Generate a filename based on the story title and file extension.

    Args:
    title (str): The title of the story.
    extension (str): The file extension (e.g., 'txt', 'mp3').

    Returns:
    str: A sanitized filename with the given extension.
    """
    sanitized_title = sanitize_filename(title)
    return f"{sanitized_title[:50]}.{extension}"

@st.cache_data
def extract_keywords(text, num_keywords=5):
    """
    Extract the most common words from a text as keywords.
    This is a simple implementation and might not be ideal for all use cases.

    Args:
    text (str): The text to extract keywords from.
    num_keywords (int): The number of keywords to extract.

    Returns:
    list: A list of the most common words in the text.
    """
    words = re.findall(r'\w+', text.lower())
    word_counts = {}
    stop_words = set(['the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'])
    
    for word in words:
        if word not in stop_words:
            word_counts[word] = word_counts.get(word, 0) + 1
    
    sorted_words = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)
    return [word for word, count in sorted_words[:num_keywords]]

# You can add more utility functions here as needed
