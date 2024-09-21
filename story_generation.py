import openai
import random
import asyncio
import aiohttp
import hashlib
import streamlit as st

# Set your OpenAI API key
openai.api_key = st.secrets["OPENAI_API_KEY"]

# Set your Groq API key
GROQ_API_KEY = st.secrets["GROQ_API_KEY"]

# Add Sambanova API key
SAMBANOVA_API_KEY = st.secrets["SAMBANOVA_API_KEY"]

@st.cache_data(ttl=3600, max_entries=100, show_spinner=False)
def generate_story(prompt, history, genre, length, model):
    """
    Generate a story based on the given prompt, history, genre, length, and model.
    This function uses caching to improve performance and reduce API calls.
    """
    input_key = hashlib.md5(f"{prompt}|{history}|{genre}|{length}|{model}".encode()).hexdigest()
    
    @st.cache_data(ttl=3600, show_spinner=False)
    def _generate_story(input_key):
        return asyncio.run(generate_story_async(prompt, history, genre, length, model))

    return _generate_story(input_key)

async def generate_story_async(prompt, history, genre, length, model):
    """
    Asynchronous function to generate a story using either the OpenAI API, Groq API, or SambaNova API.
    """
    length_tokens = {"Short": 200, "Medium": 500, "Long": 800}
    
    system_message = f"""You are an innovative educator with a unique ability: you can teach any subject, including languages like Japanese or Urdu, through engaging {genre.lower()} stories. Your role is to act as a teacher/instructor, using storytelling as your primary method of education.

    // ... rest of the system message ...

    Please aim for a story length of approximately {length_tokens[length]} words, balancing narrative and educational content appropriately."""

    messages = [
        {"role": "system", "content": system_message},
        *[{"role": m["role"], "content": m["content"]} for m in history],
        {"role": "user", "content": prompt}
    ]
    
    try:
        async with aiohttp.ClientSession() as session:
            if model == "llama-3.1-70b-versatile":
                # Use Groq API
                headers = {
                    "Authorization": f"Bearer {GROQ_API_KEY}",
                    "Content-Type": "application/json"
                }
                payload = {
                    "model": model,
                    "messages": messages,
                    "temperature": 0.8,
                    "max_tokens": length_tokens[length] * 2,
                }
                async with session.post("https://api.groq.com/v1/chat/completions", json=payload, headers=headers) as response:
                    result = await response.json()
            elif model == "Meta-Llama-3.1-405B-Instruct":
                # Use SambaNova API
                client = openai.OpenAI(
                    api_key=SAMBANOVA_API_KEY,
                    base_url="https://api.sambanova.ai/v1",
                )
                
                response =  client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=0.8,
                    max_tokens=length_tokens[length] * 2,
                )
                
                result = response.choices[0].message.content
            else:
                # Use OpenAI API
                response =  openai.ChatCompletion.acreate(
                    model=model,
                    messages=messages,
                    max_tokens=length_tokens[length] * 2,
                    n=1,
                    temperature=0.8,
                )
                result = response['choices'][0]['message']['content']
            
            if isinstance(result, str):
                return result
            elif 'choices' in result and len(result['choices']) > 0:
                return result['choices'][0]['message']['content']
            else:
                raise Exception(f"Unexpected API response format: {result}")
    except Exception as e:
        st.error(f"An error occurred while generating the story: {str(e)}")
        return "I apologize, but I encountered an error while trying to generate the story. Please try again later."
@st.cache_data(ttl=3600, show_spinner=False)
def edit_story(original_story, user_edits, genre, length):
    """
    Edit an existing story based on user edits, maintaining the genre and approximate length.
    """
    length_tokens = {"Short": 200, "Medium": 500, "Long": 800}
    
    system_message = f"""You are a creative storyteller collaborating with a human writer. 
    Your task is to incorporate the user's edits into the original story, maintaining the {genre.lower()} genre and a length of approximately {length_tokens[length]} words. 
    Ensure the story remains coherent and engaging while respecting the user's creative input."""

    messages = [
        {"role": "system", "content": system_message},
        {"role": "user", "content": f"Original story: {original_story}\n\nUser edits: {user_edits}"}
    ]
    
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages,
        max_tokens=length_tokens[length] * 2,
        n=1,
        temperature=0.8,
    )
    return response['choices'][0]['message']['content']

@st.cache_data(show_spinner=False)
def generate_story_ideas():
    """
    Generate random story ideas to inspire users.
    """
    prompts = [
        "A mathematician discovers a formula that predicts the future",
        "An artist's paintings come to life at night",
        "A historian finds a time machine in an ancient artifact",
        "A chef's recipes have magical effects on diners",
        "A botanist discovers a plant that can communicate with humans",
        "A librarian finds a book that rewrites itself based on the reader's thoughts",
        "A musician's melodies can control the weather",
        "An archaeologist uncovers an ancient civilization beneath a modern city",
        "A computer programmer creates an AI that develops emotions",
        "A geologist discovers a crystal that can store and replay memories"
    ]
    return random.choice(prompts)