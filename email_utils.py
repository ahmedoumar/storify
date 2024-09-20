import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import toml
import logging

# Load secrets from secrets.toml
secrets = toml.load('.streamlit/secrets.toml')

def send_email(to_email, subject, body):
    """
    Send an email using SMTP.
    """
    # Use secrets for email configuration
    smtp_server = secrets['SMTP_SERVER']
    smtp_port = secrets['SMTP_PORT']
    smtp_username = secrets['SMTP_USERNAME']
    smtp_password = secrets['SMTP_PASSWORD']
    from_email = secrets['FROM_EMAIL']

    message = MIMEMultipart()
    message['From'] = from_email
    message['To'] = to_email
    message['Subject'] = subject

    message.attach(MIMEText(body, 'plain'))

    try:
        logging.info(f"Attempting to connect to SMTP server: {smtp_server}:{smtp_port}")
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            logging.info("SMTP connection established")
            server.ehlo()
            server.starttls()
            server.ehlo()
            logging.info(f"Attempting to login with username: {smtp_username}")
            server.login(smtp_username, smtp_password)
            logging.info("SMTP login successful")
            server.send_message(message)
            logging.info(f"Email sent successfully to {to_email}")
    except smtplib.SMTPException as e:
        logging.error(f"SMTP error occurred: {str(e)}")
        raise
    except Exception as e:
        logging.error(f"Unexpected error in send_email: {str(e)}")
        raise

def send_confirmation_email(to_email, confirmation_token):
    """
    Send a confirmation email to new users.
    """
    subject = "Confirm Your Storify Account"
    body = f"""
    Welcome to Storify! Please confirm your email address by copying the token below:
    
    {confirmation_token}
    
    If you didn't create an account on Storify, please ignore this email.
    
    Best regards,
    The Storify Team
    """
    send_email(to_email, subject, body)

def send_password_reset_email(to_email, reset_token):
    """
    Send a password reset email.
    """
    subject = "Password Reset Request"
    body = f"""
    You have requested to reset your password. Please use the following link to reset your password:
    
    {reset_token}
    
    If you did not request this, please ignore this email.
    """
    send_email(to_email, subject, body)

def send_welcome_email(to_email):
    """
    Send a welcome email to confirmed users.
    """
    subject = "Welcome to Storify!"
    body = """
    Your email has been confirmed, and your Storify account is now active!
    
    Start creating amazing stories today!
    
    Best regards,
    The Storify Team
    """
    send_email(to_email, subject, body)