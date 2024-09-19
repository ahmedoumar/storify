import streamlit as st
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
                
                if st.session_state.get('show_resend_button', False) and resend_button:
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
        return edited_story
    if st.button("Cancel Editing"):
        return None

def handle_user_input():
    return st.chat_input("What's your story idea or question?")