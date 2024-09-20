import hashlib
import sqlite3
from database import get_database_connection
import secrets
import string
import logging

def hash_password(password):
    """
    Hash a password for storing.
    """
    return hashlib.sha256(password.encode()).hexdigest()

def verify_user(email, password):
    """
    Verify a email/password combination.
    """
    conn = get_database_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE email=?", (email,))
    user = c.fetchone()
    c.close()

    if user is None:
        return False, "User not found"
    
    if user[6] == 0:  # Assuming the 7th column (index 6) is is_confirmed
        return False, "Email not confirmed"
    
    if user[3] != hash_password(password):  # Assuming the 4th column (index 3) is password
        return False, "Incorrect password"
    
    return True, "Login successful"

def add_user(email, password):
    """
    Add a new user to the database with confirmed status.
    """
    conn = get_database_connection()
    c = conn.cursor()
    try:
        c.execute("UPDATE users SET password = ?, is_confirmed = 1, confirmation_token = NULL WHERE email = ?", 
                  (hash_password(password), email))
        conn.commit()
        c.close()
        return True
    except sqlite3.Error:
        c.close()
        return False

def get_confirmation_token(email):
    """
    Retrieve the confirmation token for a given email.
    """
    conn = get_database_connection()
    c = conn.cursor()
    c.execute("SELECT confirmation_token FROM users WHERE email=?", (email,))
    result = c.fetchone()
    c.close()
    return result[0] if result else None

def confirm_email(email, token):
    """
    Confirm a user's email using the confirmation token.
    """
    conn = get_database_connection()
    c = conn.cursor()
    try:
        # Log the input values
        logging.info(f"Attempting to confirm email: {email} with token: {token}")

        # First, check if the email exists
        c.execute("SELECT confirmation_token FROM users WHERE email = ?", (email,))
        result = c.fetchone()
        
        if result is None:
            logging.warning(f"No user found with email {email}")
            return False
        
        stored_token = result[0]
        logging.info(f"Stored token for {email}: {stored_token}")
        
        if stored_token != token:
            logging.warning(f"Token mismatch for {email}. Provided: {token}, Stored: {stored_token}")
            return False
        
        # If tokens match, update the confirmation status
        c.execute("UPDATE users SET is_confirmed = 1, confirmation_token = NULL WHERE email = ?", (email,))
        conn.commit()
        
        result = c.rowcount > 0
        if result:
            logging.info(f"Email confirmed successfully for user {email}")
        else:
            logging.warning(f"Failed to update confirmation status for user {email}")
        
        c.close()
        return result
    except sqlite3.Error as e:
        logging.error(f"Database error during email confirmation: {str(e)}")
        c.close()
        return False

def change_password(email, new_password):
    """
    Change the password for an existing user.
    """
    conn = get_database_connection()
    c = conn.cursor()
    try:
        c.execute("UPDATE users SET password = ? WHERE email = ?", (hash_password(new_password), email))
        conn.commit()
        c.close()
        return True
    except sqlite3.Error:
        c.close()
        return False

def delete_user(email):
    """
    Delete a user from the database.
    """
    conn = get_database_connection()
    c = conn.cursor()
    try:
        c.execute("DELETE FROM users WHERE email = ?", (email,))
        conn.commit()
        c.close()
        return True
    except sqlite3.Error:
        c.close()
        return False

def user_exists(email):
    """
    Check if a user exists in the database.
    """
    conn = get_database_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE email=?", (email,))
    result = c.fetchone()
    c.close()
    return result is not None

def generate_confirmation_token():
    """
    Generate a random token for email confirmation.
    """
    return secrets.token_urlsafe(32)

def generate_reset_token():
    return ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(32))

def store_reset_token(email, token):
    conn = get_database_connection()
    c = conn.cursor()
    try:
        c.execute("UPDATE users SET reset_token = ? WHERE email = ?", (token, email))
        conn.commit()
        c.close()
        return True
    except sqlite3.Error:
        c.close()
        return False

def verify_reset_token(email, token):
    conn = get_database_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE email=? AND reset_token=?", (email, token))
    result = c.fetchone()
    c.close()
    return result is not None

def clear_reset_token(email):
    conn = get_database_connection()
    c = conn.cursor()
    try:
        c.execute("UPDATE users SET reset_token = NULL WHERE email = ?", (email,))
        conn.commit()
        c.close()
        return True
    except sqlite3.Error:
        c.close()
        return False

def store_confirmation_token(email, token):
    """
    Store a confirmation token for a new user.
    """
    try:
        logging.info(f"Attempting to store confirmation token for email: {email}")
        conn = get_database_connection()
        c = conn.cursor()
        
        # Check if the user already exists
        c.execute("SELECT * FROM users WHERE email = ?", (email,))
        existing_user = c.fetchone()
        
        if existing_user:
            logging.info(f"Updating existing user with email: {email}")
            c.execute("UPDATE users SET confirmation_token = ?, is_confirmed = 0 WHERE email = ?", 
                      (token, email))
        else:
            logging.info(f"Inserting new user with email: {email}")
            # Use a placeholder password when creating a new user
            placeholder_password = "PLACEHOLDER_PASSWORD"
            c.execute("INSERT INTO users (email, password, confirmation_token, is_confirmed) VALUES (?, ?, ?, 0)", 
                      (email, placeholder_password, token))
        
        conn.commit()
        logging.info(f"Confirmation token stored successfully for email: {email}")
        return True
    except sqlite3.Error as e:
        logging.error(f"SQLite error in store_confirmation_token: {str(e)}")
        if conn:
            conn.rollback()
        return False
    except Exception as e:
        logging.error(f"Unexpected error in store_confirmation_token: {str(e)}")
        if conn:
            conn.rollback()
        return False

def verify_confirmation_token(email, token):
    """
    Verify the confirmation token for a user.
    """
    conn = get_database_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE email=? AND confirmation_token=?", (email, token))
    result = c.fetchone()
    c.close()
    return result is not None