import hashlib
import sqlite3
from database import get_database_connection

def hash_password(password):
    """
    Hash a password for storing.
    """
    return hashlib.sha256(password.encode()).hexdigest()

def verify_user(username, password):
    """
    Verify a username/password combination.
    """
    conn = get_database_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, hash_password(password)))
    result = c.fetchone()
    c.close()
    return result is not None

def add_user(username, password):
    """
    Add a new user to the database.
    """
    conn = get_database_connection()
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hash_password(password)))
        conn.commit()
        c.close()
        return True
    except sqlite3.IntegrityError:
        # This error is raised if the username already exists
        c.close()
        return False

def change_password(username, new_password):
    """
    Change the password for an existing user.
    """
    conn = get_database_connection()
    c = conn.cursor()
    try:
        c.execute("UPDATE users SET password = ? WHERE username = ?", (hash_password(new_password), username))
        conn.commit()
        c.close()
        return True
    except sqlite3.Error:
        c.close()
        return False

def delete_user(username):
    """
    Delete a user from the database.
    """
    conn = get_database_connection()
    c = conn.cursor()
    try:
        c.execute("DELETE FROM users WHERE username = ?", (username,))
        conn.commit()
        c.close()
        return True
    except sqlite3.Error:
        c.close()
        return False

def user_exists(username):
    """
    Check if a user exists in the database.
    """
    conn = get_database_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username=?", (username,))
    result = c.fetchone()
    c.close()
    return result is not None
