import streamlit as st

# Set page config at the very beginning
st.set_page_config(layout="wide")

from auth import verify_user, add_user
from story_generation import generate_story, edit_story, generate_story_ideas
from image_generation import generate_story_image_dalle
from audio_generation import text_to_speech
from utils import image_to_base64, base64_to_image
import time

# Load environment variables and set up OpenAI API key
from dotenv import load_dotenv
import os
import openai

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

def initialize_session_state():
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    if 'story_genre' not in st.session_state:
        st.session_state.story_genre = "Any"
    if 'story_length' not in st.session_state:
        st.session_state.story_length = "Medium"
    if 'story_type' not in st.session_state:
        st.session_state.story_type = "Text"
    if 'username' not in st.session_state:
        st.session_state.username = None
    if 'editing_story' not in st.session_state:
        st.session_state.editing_story = False
    if 'current_story' not in st.session_state:
        st.session_state.current_story = ""

def handle_authentication():
    if st.session_state.username is None:
        auth_option = st.radio("Choose an option:", ["Login", "Sign Up"])
        
        if auth_option == "Login":
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            if st.button("Login"):
                if verify_user(username, password):
                    st.session_state.username = username
                    st.success("Logged in successfully!")
                    st.rerun()
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
            st.rerun()

def sidebar_settings():
    st.sidebar.title("Storify")
    st.sidebar.subheader("Settings")
    st.session_state.story_genre = st.sidebar.selectbox("Genre:", ["Any", "Science Fiction", "Fantasy", "Mystery", "Historical", "Romance"])
    st.session_state.story_length = st.sidebar.radio("Length:", ["Short", "Medium", "Long"])
    st.session_state.story_type = st.sidebar.radio("Type:", ["Text", "Visual", "Audio"])
    
    if st.sidebar.button("Generate Story Idea"):
        idea = generate_story_ideas()
        st.session_state.messages.append({"role": "assistant", "content": f"Here's a story idea: {idea}"})
    
    if st.sidebar.button("Clear Chat"):
        st.session_state.messages = []
        st.session_state.editing_story = False
        st.session_state.current_story = ""
        st.rerun()

def display_chat():
    for i, message in enumerate(st.session_state.messages):
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if 'image' in message:
                st.image(base64_to_image(message['image']), caption="Generated Story Image")
            if 'audio' in message:
                st.audio(message['audio'], format='audio/mp3')
            
            if message['role'] == 'assistant':
                handle_message_actions(i, message)

def handle_message_actions(i, message):
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
            st.rerun()
    with col4:
        if 'audio' not in message and st.button('Listen', key=f"listen_{i}"):
            with st.spinner("Generating audio..."):
                audio_bytes = text_to_speech(message['content'])
                message['audio'] = audio_bytes
            st.audio(message['audio'], format='audio/mp3')
    with col5:
        if 'image' not in message and st.button('Generate Image', key=f"gen_image_{i}"):
            with st.spinner("Generating image..."):
                image = generate_story_image_dalle(message['content'][:1000])
                if image:
                    message['image'] = image_to_base64(image)
                    st.rerun()
                else:
                    st.error("Failed to generate image. Please try again.")

def handle_story_editing():
    st.subheader("Edit your story")
    edited_story = st.text_area("Make your edits here:", value=st.session_state.current_story, height=300)
    if st.button("Submit Edits"):
        with st.spinner("Incorporating your edits..."):
            revised_story = edit_story(st.session_state.current_story, edited_story, st.session_state.story_genre, st.session_state.story_length)
            st.session_state.messages.append({"role": "user", "content": "I made some edits to the story."})
            st.session_state.messages.append({"role": "assistant", "content": revised_story})
            st.session_state.editing_story = False
            st.session_state.current_story = ""
            st.rerun()
    if st.button("Cancel Editing"):
        st.session_state.editing_story = False
        st.session_state.current_story = ""
        st.rerun()

def handle_user_input():
    prompt = st.chat_input("What's your story idea or question?")
    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = ""
            current_word = ""
            for char in generate_story(prompt, st.session_state.messages[:-1], st.session_state.story_genre, st.session_state.story_length):
                if char.isspace() or char in ".,!?;:":
                    if current_word:
                        full_response += current_word + char
                        current_word = ""
                    else:
                        full_response += char
                else:
                    current_word += char
                
                #time.sleep(0.05)
                message_placeholder.markdown(full_response + current_word + "▌")
            
            if current_word:
                full_response += current_word
            
            message_placeholder.markdown(full_response)
            
            new_message = {"role": "assistant", "content": full_response.strip()}
            
            if st.session_state.story_type == "Visual":
                with st.spinner("Generating image..."):
                    image = generate_story_image_dalle(full_response[:1000])
                    if image:
                        new_message["image"] = image_to_base64(image)
                        st.image(image, caption="Generated Story Image")
            elif st.session_state.story_type == "Audio":
                with st.spinner("Generating audio..."):
                    audio_bytes = text_to_speech(full_response)
                    new_message["audio"] = audio_bytes
                    st.audio(audio_bytes, format='audio/mp3')
            
            st.session_state.messages.append(new_message)

def main():
    initialize_session_state()
    handle_authentication()
    
    if st.session_state.username:
        sidebar_settings()
        st.title("Storify Chat")
        if st.session_state.editing_story:
            handle_story_editing()
        else:
            display_chat()
            handle_user_input()

if __name__ == "__main__":
    main()