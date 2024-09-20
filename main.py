import streamlit as st
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Set page config at the very beginning, before any other imports or operations
st.set_page_config(layout="wide")

import logging
from database import get_database_connection, close_database_connection

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

from auth import (
    verify_user, 
    store_confirmation_token, 
    generate_confirmation_token,
    user_exists,
    confirm_email,
    verify_confirmation_token,
    add_user,
    generate_reset_token,
    store_reset_token,
    verify_reset_token,
    change_password,
    clear_reset_token
)
from email_utils import send_confirmation_email, send_password_reset_email, send_welcome_email
from story_generation import generate_story, edit_story, generate_story_ideas
from image_generation import generate_story_image_dalle
from audio_generation import text_to_speech
from utils import image_to_base64, base64_to_image
import time

# Load environment variables and set up OpenAI API key
from dotenv import load_dotenv
import os
import openai

openai.api_key = st.secrets["OPENAI_API_KEY"]

# ... (rest of the code remains the same)

def initialize_session_state():
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    if 'story_genre' not in st.session_state:
        st.session_state.story_genre = "Any"
    if 'story_length' not in st.session_state:
        st.session_state.story_length = "Medium"
    if 'story_type' not in st.session_state:
        st.session_state.story_type = "Text"
    if 'email' not in st.session_state:
        st.session_state.email = None
    if 'editing_story' not in st.session_state:
        st.session_state.editing_story = False
    if 'current_story' not in st.session_state:
        st.session_state.current_story = ""
    if 'reset_token' not in st.session_state:
        st.session_state.reset_token = None

def handle_email_confirmation():
    if 'token' in st.query_params and 'email' in st.query_params:
        token = st.query_params['token'][0]
        email = st.query_params['email'][0]
        
        if confirm_email(email, token):
            st.success("Email confirmed successfully! You can now log in.")
            send_welcome_email(email)
        else:
            st.error("Invalid or expired confirmation token.")
        
        # Clear the query parameters
        st.experimental_set_query_params()

def handle_password_reset():
    # Remove this function as its functionality is now integrated into handle_authentication()
    pass

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
            
            with st.spinner("Running..."):
                for char in generate_story(prompt, st.session_state.messages[:-1], st.session_state.story_genre, st.session_state.story_length):
                    if char.isspace() or char in ".,!?;:":
                        if current_word:
                            full_response += current_word + char
                            current_word = ""
                        else:
                            full_response += char
                    else:
                        current_word += char
                    
                    time.sleep(0.00005)
                    message_placeholder.markdown(full_response + current_word + "▌")
            
            if current_word:
                full_response += current_word
            
            message_placeholder.markdown(full_response)
            
            new_message = {"role": "assistant", "content": full_response.strip()}
            
            if st.session_state.story_type == "Visual":
                with st.spinner("Running..."):
                    image = generate_story_image_dalle(full_response[:1000])
                    if image:
                        new_message["image"] = image_to_base64(image)
                        st.image(image, caption="Generated Story Image")
            elif st.session_state.story_type == "Audio":
                with st.spinner("Generating audio..."):
                    audio_bytes = text_to_speech(full_response)
                    if audio_bytes:
                        new_message["audio"] = audio_bytes
                        st.audio(audio_bytes, format='audio/wav')
                    else:
                        st.error("Failed to generate audio. Please try again.")
            
            st.session_state.messages.append(new_message)

def main():
    try:
        # Ensure database connection is established
        get_database_connection()
        
        initialize_session_state()
        handle_email_confirmation()
        from ui_components import handle_authentication, sidebar_settings, display_chat

        handle_authentication()
        
        if st.session_state.email:
            sidebar_settings()
            st.title("Storify Chat")
            if st.session_state.editing_story:
                handle_story_editing()
            else:
                display_chat()
                handle_user_input()
    except Exception as e:
        st.error(f"An unexpected error occurred: {str(e)}")
        logging.exception("Unexpected error in main function")
    finally:
        # We're not closing the connection here anymore
        pass

if __name__ == "__main__":
    main()