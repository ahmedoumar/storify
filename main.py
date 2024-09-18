import streamlit as st
import logging

# Set page config at the very beginning
st.set_page_config(layout="wide")

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
from email_utils import send_confirmation_email
from story_generation import generate_story, edit_story, generate_story_ideas
from image_generation import generate_story_image_dalle
from audio_generation import text_to_speech
from utils import image_to_base64, base64_to_image
from email_utils import send_password_reset_email, send_welcome_email, send_confirmation_email
import time

# Load environment variables and set up OpenAI API key
from dotenv import load_dotenv
import os
import openai

#load_dotenv()
#openai.api_key = os.getenv("OPENAI_API_KEY")

openai.api_key = st.secrets["OPENAI_API_KEY"]

# Set up logging
logging.basicConfig(level=logging.INFO)

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

def handle_authentication():
    if st.session_state.email is None:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            auth_option = st.radio("Choose an option:", ["Login", "Sign Up", "Reset Password"])
            
            if auth_option == "Login":
                email = st.text_input("Email")
                password = st.text_input("Password", type="password")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Login", use_container_width=True):
                        success, message = verify_user(email, password)
                        if success:
                            st.session_state.email = email
                            st.success(message)
                            st.rerun()
                        else:
                            st.error(message)
                            if "not confirmed" in message.lower():
                                st.session_state.show_resend_button = True
                with col2:
                    if st.session_state.get('show_resend_button', False):
                        if st.button("Resend Confirmation Email", use_container_width=True):
                            if user_exists(email):
                                confirmation_token = generate_confirmation_token()
                                try:
                                    if store_confirmation_token(email, confirmation_token):
                                        send_confirmation_email(email, confirmation_token)
                                        st.success("Confirmation email resent. Please check your inbox.")
                                    else:
                                        st.error("Failed to store confirmation token. Please try again.")
                                except Exception as e:
                                    logging.error(f"Error in resending confirmation email: {str(e)}")
                                    st.error(f"An error occurred: {str(e)}. Please try again.")
                            else:
                                st.error("Email not found. Please sign up first.")
                
                # Add confirmation token input field
                if st.session_state.get('show_resend_button', False):
                    confirmation_token = st.text_input("Enter Confirmation Token")
                    if st.button("Confirm Email"):
                        if confirm_email(email, confirmation_token):
                            st.success("Email confirmed successfully! You can now log in.")
                            st.session_state.show_resend_button = False
                            st.rerun()
                        else:
                            st.error("Invalid confirmation token. Please try again.")

            elif auth_option == "Sign Up":
                new_email = st.text_input("Email")
                if 'show_confirmation_fields' not in st.session_state:
                    st.session_state.show_confirmation_fields = False

                if st.button("Send Verification Token", use_container_width=True):
                    if not user_exists(new_email):
                        confirmation_token = generate_confirmation_token()
                        if store_confirmation_token(new_email, confirmation_token):
                            send_confirmation_email(new_email, confirmation_token)
                            st.success("Verification token sent to your email. Please check and enter it below.")
                            st.session_state.signup_email = new_email
                            st.session_state.show_confirmation_fields = True
                        else:
                            st.error("An error occurred. Please try again.")
                    else:
                        st.error("Email already exists. Please login or use a different email.")
                        if st.button("Resend Confirmation Email"):
                            confirmation_token = generate_confirmation_token()
                            if store_confirmation_token(new_email, confirmation_token):
                                send_confirmation_email(new_email, confirmation_token)
                                st.success("Confirmation email resent. Please check your inbox.")
                                st.session_state.show_confirmation_fields = True
                            else:
                                st.error("An error occurred. Please try again.")

                if st.session_state.show_confirmation_fields:
                    confirmation_token = st.text_input("Confirmation Token")
                    password = st.text_input("Password", type="password")
                    confirm_password = st.text_input("Confirm Password", type="password")

                    if st.button("Complete Sign Up", use_container_width=True):
                        if password == confirm_password:
                            if verify_confirmation_token(new_email, confirmation_token):
                                if add_user(new_email, password):
                                    st.success("Account created successfully! You can now log in.")
                                    st.session_state.show_confirmation_fields = False
                                else:
                                    st.error("An error occurred while creating your account. Please try again.")
                            else:
                                st.error("Invalid confirmation token. Please check and try again.")
                        else:
                            st.error("Passwords do not match. Please try again.")

            elif auth_option == "Reset Password":
                email = st.text_input("Enter your email")
                if st.button("Send Reset Link"):
                    if user_exists(email):
                        reset_token = generate_reset_token()
                        if store_reset_token(email, reset_token):
                            send_password_reset_email(email, reset_token)
                            st.success("Password reset link sent to your email. Please check your inbox.")
                        else:
                            st.error("An error occurred. Please try again.")
                    else:
                        st.error("Email not found. Please sign up first.")

                reset_token = st.text_input("Enter Reset Token")
                new_password = st.text_input("New Password", type="password")
                confirm_new_password = st.text_input("Confirm New Password", type="password")

                if st.button("Reset Password"):
                    if new_password == confirm_new_password:
                        if verify_reset_token(email, reset_token):
                            if change_password(email, new_password):
                                clear_reset_token(email)
                                st.success("Password reset successfully. You can now log in with your new password.")
                            else:
                                st.error("An error occurred while resetting your password. Please try again.")
                        else:
                            st.error("Invalid reset token. Please check and try again.")
                    else:
                        st.error("Passwords do not match. Please try again.")

    else:
        st.write(f"Welcome, {st.session_state.email}!")
        if st.button("Logout"):
            st.session_state.email = None
            st.rerun()

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

def sidebar_settings():
    st.sidebar.title("Storify")
    st.sidebar.subheader("Settings")
    st.session_state.story_genre = st.sidebar.selectbox("Genre:", ["Any", "Science Fiction", "Fantasy", "Mystery", "Historical", "Romance"])
    st.session_state.story_length = st.sidebar.radio("Length:", ["Short", "Medium", "Long"])
    st.session_state.story_type = st.sidebar.radio("Type:", ["Text", "Visual", "Audio"])
    
    st.sidebar.markdown("### Accessibility")
    font_size = st.sidebar.slider("Font Size", min_value=12, max_value=24, value=16)
    st.markdown(f"<style>body {{font-size: {font_size}px;}}</style>", unsafe_allow_html=True)
    
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
                st.image(base64_to_image(message['image']), caption="Generated Story Image", use_column_width=True)
            if 'audio' in message:
                st.audio(message['audio'], format='audio/mp3')
            
            if message['role'] == 'assistant':
                handle_message_actions(i, message)

def handle_message_actions(i, message):
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.button('👍', key=f"thumbs_up_{i}", help="Like this response")
    with col2:
        st.button('👎', key=f"thumbs_down_{i}", help="Dislike this response")
    with col3:
        if st.button('Edit', key=f"edit_{i}", help="Edit this story"):
            st.session_state.editing_story = True
            st.session_state.current_story = message['content']
            st.rerun()
    with col4:
        if 'audio' not in message:
            if st.button('Listen', key=f"listen_{i}", help="Convert to speech"):
                with st.spinner("Generating audio..."):
                    audio_bytes = text_to_speech(message['content'])
                    if audio_bytes:
                        message['audio'] = audio_bytes
                        st.audio(audio_bytes, format='audio/wav')
                    else:
                        st.error("Failed to generate audio. Please try again.")
        if 'image' not in message:
            if st.button('Image', key=f"gen_image_{i}", help="Generate image"):
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
        initialize_session_state()
        handle_email_confirmation()
        handle_password_reset()
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
        logging.error(f"Unexpected error: {str(e)}", exc_info=True)

if __name__ == "__main__":
    main()