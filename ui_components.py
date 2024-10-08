import streamlit as st
import logging
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
from story_generation import generate_story_ideas
from image_generation import generate_story_image_dalle
from audio_generation import text_to_speech
from utils import image_to_base64, base64_to_image
from image_generation import generate_story_image

def handle_authentication():
    if st.session_state.email is None:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            auth_option = st.radio("Choose an option:", ["Login", "Sign Up", "Reset Password"], horizontal=True)
            
            if auth_option == "Login":
                with st.form(key='login_form'):
                    email = st.text_input("Email")
                    password = st.text_input("Password", type="password")
                    col1, col2 = st.columns(2)
                    with col1:
                        login_button = st.form_submit_button("Login", use_container_width=True)
                    with col2:
                        resend_button = st.form_submit_button("Resend Confirmation Email", use_container_width=True)
                
                if login_button:
                    success, message = verify_user(email, password)
                    if success:
                        st.session_state.email = email
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)
                        if "not confirmed" in message.lower():
                            st.session_state.show_resend_button = True
                            st.session_state.unconfirmed_email = email
                
                if st.session_state.get('show_resend_button', False) and resend_button:
                    if user_exists(email):
                        confirmation_token = generate_confirmation_token()
                        try:
                            if store_confirmation_token(email, confirmation_token):
                                send_confirmation_email(email, confirmation_token)
                                st.success("Confirmation email resent. Please check your inbox.")
                                st.session_state.show_confirmation_fields = True
                            else:
                                st.error("Failed to store confirmation token. Please try again.")
                        except Exception as e:
                            logging.error(f"Error in resending confirmation email: {str(e)}")
                            st.error(f"An error occurred: {str(e)}. Please try again.")
                    else:
                        st.error("Email not found. Please sign up first.")
                
                if st.session_state.get('show_confirmation_fields', False):
                    confirmation_token = st.text_input("Enter Confirmation Token")
                    new_password = st.text_input("Set New Password", type="password")
                    confirm_password = st.text_input("Confirm New Password", type="password")
                    if st.button("Confirm Email and Set Password"):
                        if new_password == confirm_password:
                            if confirm_email(st.session_state.unconfirmed_email, confirmation_token):
                                if add_user(st.session_state.unconfirmed_email, new_password):
                                    st.success("Email confirmed and password set successfully! You can now log in.")
                                    st.session_state.show_confirmation_fields = False
                                    st.session_state.show_resend_button = False
                                    st.rerun()
                                else:
                                    st.error("An error occurred while setting your password. Please try again.")
                            else:
                                st.error("Invalid confirmation token. Please check and try again.")
                        else:
                            st.error("Passwords do not match. Please try again.")

            elif auth_option == "Sign Up":
                new_email = st.text_input("Email")
                if 'show_confirmation_fields' not in st.session_state:
                    st.session_state.show_confirmation_fields = False

                if st.button("Send Verification Token", use_container_width=True):
                    if not user_exists(new_email):
                        confirmation_token = generate_confirmation_token()
                        try:
                            logging.info(f"Attempting to store confirmation token for email: {new_email}")
                            token_stored = store_confirmation_token(new_email, confirmation_token)
                            if token_stored:
                                logging.info(f"Confirmation token stored successfully for email: {new_email}")
                                try:
                                    send_confirmation_email(new_email, confirmation_token)
                                    logging.info(f"Confirmation email sent successfully to: {new_email}")
                                    st.success("Verification token sent to your email. Please check and enter it below.")
                                    st.session_state.signup_email = new_email
                                    st.session_state.show_confirmation_fields = True
                                except Exception as e:
                                    logging.error(f"Error sending confirmation email: {str(e)}")
                                    st.error(f"Failed to send confirmation email. Please try again. Error: {str(e)}")
                            else:
                                st.error("Failed to store confirmation token. Please try again.")
                        except Exception as e:
                            logging.error(f"Error in signup process: {str(e)}")
                            st.error(f"An error occurred during signup: {str(e)}. Please try again.")
                    else:
                        st.error("Email already exists. Please login or use a different email.")
                        if st.button("Resend Confirmation Email"):
                            confirmation_token = generate_confirmation_token()
                            try:
                                if store_confirmation_token(new_email, confirmation_token):
                                    send_confirmation_email(new_email, confirmation_token)
                                    st.success("Confirmation email resent. Please check your inbox.")
                                    st.session_state.show_confirmation_fields = True
                                else:
                                    st.error("Failed to store confirmation token. Please try again.")
                            except Exception as e:
                                logging.error(f"Error in resending confirmation email: {str(e)}")
                                st.error(f"An error occurred: {str(e)}. Please try again.")

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
                            st.error("Passwords do not match. Please try again.")

    else:
        st.write(f"Welcome, {st.session_state.email}!")
        if st.button("Logout"):
            st.session_state.email = None
            st.rerun()

def sidebar_settings():
    st.sidebar.title("Storify")
    st.sidebar.subheader("Settings")
    st.session_state.story_genre = st.sidebar.selectbox("Genre:", ["Any", "Science Fiction", "Fantasy", "Mystery", "Historical", "Romance"], key="genre_select")
    st.session_state.story_length = st.sidebar.radio("Length:", ["Short", "Medium", "Long"], key="length_radio")
    st.session_state.story_type = st.sidebar.radio("Type:", ["Text", "Visual", "Audio"], key="type_radio")
    
    # Add model selection for text generation
    text_models = {
        "GPT-4": "gpt-4-1106-preview",
        "GPT-3.5 Turbo": "gpt-3.5-turbo",
        "Meta Llama 70B": "llama-3.1-70b-versatile",
        "Meta-Llama-3.1-405B-Instruct": "Meta-Llama-3.1-405B-Instruct"  # Added new model
    }
    st.session_state.text_model = st.sidebar.selectbox("Text Generation Model:", list(text_models.keys()), key="text_model_select")
    st.session_state.text_model_id = text_models[st.session_state.text_model]
    
    if st.session_state.story_type == "Visual":
        image_models = {
            "DALL-E": "dalle",
            "Stable Diffusion v1.5": "runwayml/stable-diffusion-v1-5",
            "Stable Diffusion v2.1": "stabilityai/stable-diffusion-2-1",
            "Stable Diffusion XL": "stabilityai/stable-diffusion-xl-base-1.0"
        }
        st.session_state.image_model = st.sidebar.selectbox("Image Generation Model:", list(image_models.keys()), key="image_model_select")
        st.session_state.image_model_id = image_models[st.session_state.image_model]
    
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
        st.button('👍', key=f"action_{i}_1", help="Like this response")
    with col2:
        st.button('👎', key=f"action_{i}_2", help="Dislike this response")
    with col3:
        if st.button('Edit', key=f"action_{i}_3", help="Edit this story"):
            st.session_state.editing_story = True
            st.session_state.current_story = message['content']
            st.rerun()
    with col4:
        if 'audio' not in message:
            if st.button('Listen', key=f"action_{i}_4", help="Convert to speech"):
                with st.spinner("Generating audio..."):
                    audio_bytes = text_to_speech(message['content'])
                    if audio_bytes:
                        message['audio'] = audio_bytes
                        st.audio(audio_bytes, format='audio/wav')
                    else:
                        st.error("Failed to generate audio. Please try again.")
        
        if 'image' not in message:
            if st.button('Image', key=f"action_{i}_5", help="Generate image"):
                with st.spinner("Generating image..."):
                    image = generate_story_image(message['content'][:1000], model=st.session_state.image_model_id)
                    if image:
                        message['image'] = image_to_base64(image)
                        st.rerun()
                    else:
                        st.error("Failed to generate image. Please try again.")

def handle_story_editing():
    st.subheader("Edit your story")
    edited_story = st.text_area("Make your edits here:", value=st.session_state.current_story, height=300)
    if st.button("Submit Edits"):
        return edited_story
    if st.button("Cancel Editing"):
        return None

def handle_user_input():
    return st.chat_input("What's your story idea or question?")