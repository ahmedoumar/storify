import streamlit as st
import openai
from dotenv import load_dotenv
import os
import random
import hashlib
import sqlite3
import requests
from PIL import Image
from io import BytesIO
import base64
import asyncio
import aiohttp
from gtts import gTTS
import tempfile

# Load environment variables
load_dotenv()

# Set up OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")

# Set up database
@st.cache_resource
def get_database_connection():
    conn = sqlite3.connect('storify_users.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (username TEXT PRIMARY KEY, password TEXT)''')
    conn.commit()
    return conn

conn = get_database_connection()

# Function to hash passwords
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Function to verify user
def verify_user(username, password):
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, hash_password(password)))
    return c.fetchone() is not None

# Function to add new user
def add_user(username, password):
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users VALUES (?, ?)", (username, hash_password(password)))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False

# Asynchronous function to generate story
async def generate_story_async(prompt, history, genre, length):
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
    
    async with aiohttp.ClientSession() as session:
        async with session.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {openai.api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": "gpt-4o-mini",
                "messages": messages,
                "max_tokens": length_tokens[length] * 2,
                "n": 1,
                "temperature": 0.8,
            }
        ) as response:
            result = await response.json()
            return result['choices'][0]['message']['content']

# Cached function to generate story
@st.cache_data(ttl=3600)
def generate_story(prompt, history, genre, length):
    input_key = hashlib.md5(f"{prompt}|{history}|{genre}|{length}".encode()).hexdigest()
    
    @st.cache_data(ttl=3600, show_spinner=False)
    def _generate_story(input_key):
        return asyncio.run(generate_story_async(prompt, history, genre, length))

    return _generate_story(input_key)

# Function to edit story
@st.cache_data
def edit_story(original_story, user_edits, genre, length):
    length_tokens = {"Short": 200, "Medium": 500, "Long": 800}
    
    system_message = f"""You are a creative storyteller collaborating with a human writer. 
    Your task is to incorporate the user's edits into the original story, maintaining the {genre.lower()} genre and a length of approximately {length_tokens[length]} words. 
    Ensure the story remains coherent and engaging while respecting the user's creative input."""

    messages = [
        {"role": "system", "content": system_message},
        {"role": "user", "content": f"Original story: {original_story}\n\nUser edits: {user_edits}"}
    ]
    
    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=messages,
        max_tokens=length_tokens[length] * 2,
        n=1,
        temperature=0.8,
    )
    return response.choices[0].message['content']

# Function to generate story ideas
def generate_story_ideas():
    prompts = [
        "A mathematician discovers a formula that predicts the future",
        "An artist's paintings come to life at night",
        "A historian finds a time machine in an ancient artifact",
        "A chef's recipes have magical effects on diners",
        "A botanist discovers a plant that can communicate with humans"
    ]
    return random.choice(prompts)

# Function to generate story image using DALL-E
@st.cache_data
def generate_story_image_dalle(prompt):
    try:
        response = openai.Image.create(
            prompt=prompt,
            n=1,
            size="512x512"
        )
        image_url = response['data'][0]['url']
        image_response = requests.get(image_url)
        img = Image.open(BytesIO(image_response.content))
        return img
    except Exception as e:
        st.error(f"Failed to generate image: {str(e)}")
        return None

# Function to convert PIL Image to base64
def image_to_base64(img):
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode()

# Function to convert base64 to PIL Image
def base64_to_image(base64_string):
    return Image.open(BytesIO(base64.b64decode(base64_string)))

# Function to convert text to speech
def text_to_speech(text, lang='en'):
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_file = os.path.join(temp_dir, "temp.mp3")
        tts = gTTS(text=text, lang=lang, slow=False)
        tts.save(temp_file)
        
        with open(temp_file, "rb") as audio_file:
            audio_bytes = audio_file.read()
    
    return audio_bytes

# Streamlit app
st.title("Storify - Turn anything to a story!")

# User Authentication
if 'username' not in st.session_state:
    st.session_state.username = None

if st.session_state.username is None:
    auth_option = st.radio("Choose an option:", ["Login", "Sign Up"])
    
    if auth_option == "Login":
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            if verify_user(username, password):
                st.session_state.username = username
                st.success("Logged in successfully!")
                st.experimental_rerun()
            else:
                st.error("Invalid username or password")
    else:
        new_username = st.text_input("New Username")
        new_password = st.text_input("New Password", type="password")
        if st.button("Sign Up"):
            if add_user(new_username, new_password):
                st.success("Account created successfully! Please log in.")
            else:
                st.error("Username already exists")

else:
    st.write(f"Welcome, {st.session_state.username}!")
    if st.button("Logout"):
        st.session_state.username = None
        st.experimental_rerun()

    # Initialize session state variables
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "story_genre" not in st.session_state:
        st.session_state.story_genre = "Any"
    if "story_length" not in st.session_state:
        st.session_state.story_length = "Medium"
    if "story_type" not in st.session_state:
        st.session_state.story_type = "Text"
    if "editing_story" not in st.session_state:
        st.session_state.editing_story = False
    if "current_story" not in st.session_state:
        st.session_state.current_story = ""

    # Sidebar for settings
    with st.sidebar:
        st.subheader("Story Settings")
        st.session_state.story_genre = st.selectbox("Choose a genre:", ["Any", "Science Fiction", "Fantasy", "Mystery", "Historical", "Romance"])
        st.session_state.story_length = st.radio("Story length:", ["Short", "Medium", "Long"])
        st.session_state.story_type = st.radio("Story type:", ["Text", "Visual", "Audio"])
        
        if st.button("Generate Story Idea"):
            st.session_state.story_idea = generate_story_ideas()
        
        if st.button("Clear Chat History"):
            st.session_state.messages = []
            st.session_state.editing_story = False
            st.session_state.current_story = ""
            st.experimental_rerun()

    # Display chat messages
    for i, message in enumerate(st.session_state.messages):
        st.markdown(f"**{message['role'].title()}:**")
        st.markdown(message['content'])
        
        if 'image' in message:
            st.image(base64_to_image(message['image']), caption="Generated Story Image")
        
        if 'audio' in message:
            st.audio(message['audio'], format='audio/mp3')
        
        # Add thumbs up/down buttons and edit button for assistant messages
        if message['role'] == 'assistant':
            col1, col2, col3, col4, col5 = st.columns([1,1,1,1,4])
            with col1:
                if st.button('👍', key=f"thumbs_up_{i}"):
                    st.success("Thanks for your feedback!")
            with col2:
                if st.button('👎', key=f"thumbs_down_{i}"):
                    st.error("We'll try to improve!")
            with col3:
                if st.button('Edit', key=f"edit_{i}"):
                    st.session_state.editing_story = True
                    st.session_state.current_story = message['content']
                    st.experimental_rerun()
            with col4:
                if 'audio' not in message and st.button('Listen', key=f"listen_{i}"):
                    with st.spinner("Generating audio..."):
                        audio_bytes = text_to_speech(message['content'])
                        message['audio'] = audio_bytes
                    st.audio(message['audio'], format='audio/mp3')
            with col5:
                if 'image' not in message and st.button('Generate Image', key=f"gen_image_{i}"):
                    with st.spinner("Generating image..."):
                        image = generate_story_image_dalle(message['content'][:1000])  # Use first 1000 chars as prompt
                        if image:
                            message['image'] = image_to_base64(image)
                            st.experimental_rerun()
                        else:
                            st.error("Failed to generate image. Please try again.")
        
        st.markdown("---")  # Add a separator between messages

    # Collaborative storytelling
    if st.session_state.editing_story:
        st.subheader("Edit your story")
        edited_story = st.text_area("Make your edits here:", value=st.session_state.current_story, height=300)
        if st.button("Submit Edits"):
            with st.spinner("Incorporating your edits..."):
                revised_story = edit_story(st.session_state.current_story, edited_story, st.session_state.story_genre, st.session_state.story_length)
                st.session_state.messages.append({"role": "user", "content": "I made some edits to the story."})
                st.session_state.messages.append({"role": "assistant", "content": revised_story})
                st.session_state.editing_story = False
                st.session_state.current_story = ""
                st.experimental_rerun()
        if st.button("Cancel Editing"):
            st.session_state.editing_story = False
            st.session_state.current_story = ""
            st.experimental_rerun()
    else:
        # User input for new story
        if 'story_idea' in st.session_state:
            st.write(f"Story idea: {st.session_state.story_idea}")
        prompt = st.text_input("Enter your story prompt or follow-up question:", key="user_input")
        if st.button("Storify"):
            if prompt:
                # Add user message to chat history
                st.session_state.messages.append({"role": "user", "content": prompt})
                
                # Generate and display story
                with st.spinner("Creating your story..."):
                    story = generate_story(prompt, st.session_state.messages[:-1], st.session_state.story_genre, st.session_state.story_length)
                    new_message = {"role": "assistant", "content": story}
                    
                    if st.session_state.story_type == "Visual":
                        image = generate_story_image_dalle(story[:1000])  # Use first 1000 chars of the story as prompt
                        if image:
                            new_message["image"] = image_to_base64(image)
                    elif st.session_state.story_type == "Audio":
                        audio_bytes = text_to_speech(story)
                        new_message["audio"] = audio_bytes
                    
                    st.session_state.messages.append(new_message)
                
                # Rerun the script to update the chat history
                st.experimental_rerun()

    # Download story button
    if st.session_state.messages:
        story_text = "\n\n".join([f"{m['role'].title()}: {m['content']}" for m in st.session_state.messages])
        st.download_button(
            label="Download Story",
            data=story_text,
            file_name="my_story.txt",
            mime="text/plain"
        )