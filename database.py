import sqlite3
import streamlit as st
from contextlib import contextmanager

# Database file name
DB_NAME = 'storify_users.db'

@st.cache_resource
def get_database_connection():
    """
    Create and return a database connection.
    This function is cached to avoid creating multiple connections.
    """
    return sqlite3.connect(DB_NAME, check_same_thread=False)

@contextmanager
def get_cursor():
    """
    Context manager for database operations.
    This ensures that the cursor is properly closed after each operation.
    """
    conn = get_database_connection()
    cursor = conn.cursor()
    try:
        yield cursor
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cursor.close()

def init_db():
    """
    Initialize the database by creating necessary tables if they don't exist.
    """
    with get_cursor() as cursor:
        # Create users table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Create stories table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS stories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            genre TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        ''')

def add_user(username, password_hash):
    """
    Add a new user to the database.
    
    Args:
    username (str): The username of the new user.
    password_hash (str): The hashed password of the new user.
    
    Returns:
    bool: True if the user was successfully added, False otherwise.
    """
    try:
        with get_cursor() as cursor:
            cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", 
                           (username, password_hash))
        return True
    except sqlite3.IntegrityError:
        return False

def get_user(username):
    """
    Retrieve a user from the database.
    
    Args:
    username (str): The username of the user to retrieve.
    
    Returns:
    tuple: A tuple containing the user's information, or None if the user doesn't exist.
    """
    with get_cursor() as cursor:
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        return cursor.fetchone()

def save_story(user_id, title, content, genre):
    """
    Save a new story to the database.
    
    Args:
    user_id (int): The ID of the user who created the story.
    title (str): The title of the story.
    content (str): The content of the story.
    genre (str): The genre of the story.
    
    Returns:
    int: The ID of the newly created story.
    """
    with get_cursor() as cursor:
        cursor.execute("""
        INSERT INTO stories (user_id, title, content, genre)
        VALUES (?, ?, ?, ?)
        """, (user_id, title, content, genre))
        return cursor.lastrowid

def get_user_stories(user_id):
    """
    Retrieve all stories for a given user.
    
    Args:
    user_id (int): The ID of the user whose stories to retrieve.
    
    Returns:
    list: A list of tuples, each containing information about a story.
    """
    with get_cursor() as cursor:
        cursor.execute("SELECT * FROM stories WHERE user_id = ? ORDER BY created_at DESC", (user_id,))
        return cursor.fetchall()

def get_story(story_id):
    """
    Retrieve a specific story from the database.
    
    Args:
    story_id (int): The ID of the story to retrieve.
    
    Returns:
    tuple: A tuple containing the story's information, or None if the story doesn't exist.
    """
    with get_cursor() as cursor:
        cursor.execute("SELECT * FROM stories WHERE id = ?", (story_id,))
        return cursor.fetchone()

def update_story(story_id, title, content, genre):
    """
    Update an existing story in the database.
    
    Args:
    story_id (int): The ID of the story to update.
    title (str): The new title of the story.
    content (str): The new content of the story.
    genre (str): The new genre of the story.
    
    Returns:
    bool: True if the story was successfully updated, False otherwise.
    """
    with get_cursor() as cursor:
        cursor.execute("""
        UPDATE stories
        SET title = ?, content = ?, genre = ?
        WHERE id = ?
        """, (title, content, genre, story_id))
        return cursor.rowcount > 0

def delete_story(story_id):
    """
    Delete a story from the database.
    
    Args:
    story_id (int): The ID of the story to delete.
    
    Returns:
    bool: True if the story was successfully deleted, False otherwise.
    """
    with get_cursor() as cursor:
        cursor.execute("DELETE FROM stories WHERE id = ?", (story_id,))
        return cursor.rowcount > 0

# Initialize the database when this module is imported
init_db()
