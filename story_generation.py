import openai
import random
import asyncio
import aiohttp
import hashlib
import streamlit as st

@st.cache_data(ttl=3600, max_entries=100, show_spinner=False)
def generate_story(prompt, history, genre, length):
    """
    Generate a story based on the given prompt, history, genre, and length.
    This function uses caching to improve performance and reduce API calls.
    """
    input_key = hashlib.md5(f"{prompt}|{history}|{genre}|{length}".encode()).hexdigest()
    
    @st.cache_data(ttl=3600, show_spinner=False)
    def _generate_story(input_key):
        return asyncio.run(generate_story_async(prompt, history, genre, length))

    return _generate_story(input_key)

async def generate_story_async(prompt, history, genre, length):
    """
    Asynchronous function to generate a story using the OpenAI API.
    """
    length_tokens = {"Short": 200, "Medium": 500, "Long": 800}
    
    system_message = f"""You are an innovative educator with a unique ability: you can teach any subject, including languages like Japanese or Urdu, through engaging {genre.lower()} stories. Your role is to act as a teacher/instructor, using storytelling as your primary method of education.

When presented with a topic or question:
1. Craft a narrative that weaves key educational elements into an imaginative story.
2. Ensure your story is not only entertaining but also effectively communicates the intended knowledge or skill.
3. For language learning, incorporate vocabulary, phrases, or grammar points naturally within the story's context.
4. Include brief explanations or 'teaching moments' within or after the story to highlight important points.
5. For follow-up questions or prompts, continue the story or create a related one that builds upon previous learning.
6. Adapt your teaching style to suit different learning preferences and difficulties.

Your stories should be educational, captivating, and tailored to the subject matter, whether it's mathematics, physics, history, art, languages, or any other field. 

Please aim for a story length of approximately {length_tokens[length]} words, balancing narrative and educational content appropriately."""

    messages = [
        {"role": "system", "content": system_message},
        *[{"role": m["role"], "content": m["content"]} for m in history],
        {"role": "user", "content": prompt}
    ]
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {openai.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "gpt-4-1106-preview",
                    "messages": messages,
                    "max_tokens": length_tokens[length] * 2,
                    "n": 1,
                    "temperature": 0.8,
                }
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"API request failed with status {response.status}: {error_text}")
                
                result = await response.json()
                
                if 'choices' not in result or len(result['choices']) == 0:
                    raise Exception(f"Unexpected API response format: {result}")
                
                return result['choices'][0]['message']['content']
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
