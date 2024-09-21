import openai
import requests
from PIL import Image
from io import BytesIO
import streamlit as st
from diffusers import StableDiffusionPipeline, DPMSolverMultistepScheduler
import torch
from openai import OpenAI

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

@st.cache_data(show_spinner=False)
def generate_story_image_dalle(prompt, size="1024x1024"):
    """
    Generate an image using DALL-E based on the given prompt.
    
    Args:
    prompt (str): The text prompt to generate the image from.
    size (str): The size of the image to generate. Options are "256x256", "512x512", or "1024x1024".
    
    Returns:
    PIL.Image.Image or None: The generated image as a PIL Image object, or None if generation failed.
    """
    try:
        # DALL-E 3 only supports "1024x1024", "1792x1024", or "1024x1792"
        if size not in ["1024x1024", "1792x1024", "1024x1792"]:
            size = "1024x1024"  # Default to 1024x1024 if an unsupported size is provided
        
        response = client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size=size,
            quality="standard",
            n=1,
        )

        image_url = response.data[0].url
        image_response = requests.get(image_url)
        image = Image.open(BytesIO(image_response.content))
        return image
    except Exception as e:
        st.error(f"An error occurred while generating the image: {str(e)}")
        return None

def preprocess_prompt(story_content, max_length=1000):
    """
    Preprocess the story content to create a suitable prompt for image generation.
    
    Args:
    story_content (str): The full story content.
    max_length (int): The maximum length of the prompt.
    
    Returns:
    str: A preprocessed prompt suitable for image generation.
    """
    # Extract the first few sentences (adjust as needed)
    sentences = story_content.split('.')[:3]
    shortened_content = '. '.join(sentences)
    
    # Create a prompt focusing on visual elements
    prompt = f"Create an image that captures the essence of this story: {shortened_content}"
    
    # Ensure the prompt doesn't exceed the max length
    if len(prompt) > max_length:
        prompt = prompt[:max_length-3] + "..."
    
    return prompt

@st.cache_resource
def load_stable_diffusion_model(model_id):
    pipe = StableDiffusionPipeline.from_pretrained(model_id, torch_dtype=torch.float16)
    pipe.scheduler = DPMSolverMultistepScheduler.from_config(pipe.scheduler.config)
    pipe = pipe.to("cuda" if torch.cuda.is_available() else "cpu")
    return pipe

@st.cache_data(show_spinner=False)
def generate_story_image_stable_diffusion(prompt, size=(512, 512), model_id="stabilityai/stable-diffusion-2-1"):
    """
    Generate an image using Stable Diffusion based on the given prompt.
    
    Args:
    prompt (str): The text prompt to generate the image from.
    size (tuple): The size of the image to generate.
    model_id (str): The Hugging Face model ID for the Stable Diffusion model.
    
    Returns:
    PIL.Image.Image or None: The generated image as a PIL Image object, or None if generation failed.
    """
    try:
        pipe = load_stable_diffusion_model(model_id)
        image = pipe(prompt, height=size[1], width=size[0]).images[0]
        return image
    except Exception as e:
        st.error(f"Failed to generate image with Stable Diffusion: {str(e)}")
        return None

@st.cache_data(show_spinner=False)
def generate_story_image(story_content, size=(512, 512), model="dalle"):
    """
    Generate an image based on the story content using the specified model.
    
    Args:
    story_content (str): The full story content.
    size (tuple): The size of the image to generate.
    model (str): The model to use for image generation ("dalle" or a Stable Diffusion model ID).
    
    Returns:
    PIL.Image.Image or None: The generated image as a PIL Image object, or None if generation failed.
    """
    prompt = preprocess_prompt(story_content)
    
    if model == "dalle":
        return generate_story_image_dalle(prompt, f"{size[0]}x{size[1]}")
    elif model.startswith("stabilityai/") or model.startswith("runwayml/"):
        return generate_story_image_stable_diffusion(prompt, size, model_id=model)
    else:
        st.error(f"Unknown model: {model}")
        return None

def resize_image(image, max_size=(800, 600)):
    """
    Resize an image while maintaining its aspect ratio.
    
    Args:
    image (PIL.Image.Image): The image to resize.
    max_size (tuple): The maximum width and height of the resized image.
    
    Returns:
    PIL.Image.Image: The resized image.
    """
    image.thumbnail(max_size, Image.LANCZOS)
    return image

def apply_watermark(image, watermark_text="Generated by Storify"):
    """
    Apply a text watermark to an image.
    
    Args:
    image (PIL.Image.Image): The image to watermark.
    watermark_text (str): The text to use as a watermark.
    
    Returns:
    PIL.Image.Image: The watermarked image.
    """
    from PIL import ImageDraw, ImageFont
    
    draw = ImageDraw.Draw(image)
    width, height = image.size
    
    # You may need to adjust this path to where your font file is located
    try:
        font = ImageFont.truetype("arial.ttf", 20)
    except IOError:
        font = ImageFont.load_default()
    
    textwidth, textheight = draw.textsize(watermark_text, font)
    
    margin = 10
    x = width - textwidth - margin
    y = height - textheight - margin
    
    draw.text((x, y), watermark_text, font=font, fill=(255, 255, 255, 128))
    
    return image
