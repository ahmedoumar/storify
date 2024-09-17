import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def send_email(to_email, subject, body):
    """
    Send an email using SMTP.
    """
    # Use environment variables for email configuration
    smtp_server = os.getenv('SMTP_SERVER')
    smtp_port = int(os.getenv('SMTP_PORT', 587))
    smtp_username = os.getenv('SMTP_USERNAME')
    smtp_password = os.getenv('SMTP_PASSWORD')
    from_email = os.getenv('FROM_EMAIL')

    message = MIMEMultipart()
    message['From'] = from_email
    message['To'] = to_email
    message['Subject'] = subject

    message.attach(MIMEText(body, 'plain'))

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.ehlo()  # Can be omitted
            server.starttls()
            server.ehlo()  # Can be omitted
            server.login(smtp_username, smtp_password)
            server.send_message(message)
            print(f"Email sent successfully to {to_email}")
    except Exception as e:
        print(f"Failed to send email: {str(e)}")
        raise

def send_confirmation_email(to_email, confirmation_token):
    """
    Send a confirmation email to new users.
    """
    subject = "Confirm Your Storify Account"
    body = f"""
    Welcome to Storify! Please confirm your email address by clicking the link below:
    
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