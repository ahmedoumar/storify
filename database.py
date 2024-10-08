import sqlite3
import streamlit as st
import os
import logging
from contextlib import contextmanager
from threading import Lock, get_ident  # Add this import
import threading
# Database file name
DB_NAME = 'storify_users.db'

# Connection pool
connection_pool = {}
connection_pool_lock = Lock()

@st.cache_resource
def get_database_connection():
    thread_id = get_ident()
    with connection_pool_lock:
        if thread_id not in connection_pool:
            try:
                conn = sqlite3.connect(DB_NAME, check_same_thread=False)
                logging.info(f"Successfully connected to database: {DB_NAME}")
                create_tables_if_not_exist(conn)
                connection_pool[thread_id] = conn
            except sqlite3.Error as e:
                logging.error(f"Error connecting to database: {str(e)}")
                raise
        return connection_pool[thread_id]

def close_database_connection():
    thread_id = threading.get_ident()
    with connection_pool_lock:
        if thread_id in connection_pool:
            connection_pool[thread_id].close()
            del connection_pool[thread_id]

def create_tables_if_not_exist(conn):
    cursor = conn.cursor()
    try:
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE,
            password TEXT,
            confirmation_token TEXT,
            is_confirmed INTEGER DEFAULT 0,
            reset_token TEXT
        )
        ''')
        conn.commit()
        logging.info("Users table created or already exists")
    except sqlite3.Error as e:
        logging.error(f"Error creating users table: {str(e)}")
        raise
    finally:
        cursor.close()

@contextmanager
def get_cursor():
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
    with get_cursor() as cursor:
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            email TEXT UNIQUE,
            password TEXT NOT NULL,
            reset_token TEXT,
            confirmation_token TEXT,
            is_confirmed INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
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

def migrate_database():
    with get_cursor() as cursor:
        # Check existing columns
        cursor.execute("PRAGMA table_info(users)")
        columns = {column[1] for column in cursor.fetchall()}
        
        # If the table is empty or doesn't have the expected structure, recreate it
        if not columns or 'id' not in columns:
            cursor.execute("DROP TABLE IF EXISTS users")
            cursor.execute('''
            CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE,
                email TEXT UNIQUE,
                password TEXT NOT NULL,
                reset_token TEXT,
                confirmation_token TEXT,
                is_confirmed INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')
        else:
            # Add missing columns if necessary
            if 'email' not in columns:
                cursor.execute("ALTER TABLE users ADD COLUMN email TEXT UNIQUE")
            if 'confirmation_token' not in columns:
                cursor.execute("ALTER TABLE users ADD COLUMN confirmation_token TEXT")
            if 'is_confirmed' not in columns:
                cursor.execute("ALTER TABLE users ADD COLUMN is_confirmed INTEGER DEFAULT 0")

def add_user(email, password):
    with get_cursor() as cursor:
        try:
            cursor.execute("INSERT INTO users (email, password) VALUES (?, ?)", (email, password))
            return True
        except sqlite3.IntegrityError:
            return False

def get_user(email):
    with get_cursor() as cursor:
        cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
        return cursor.fetchone()

def save_story(user_id, title, content, genre):
    with get_cursor() as cursor:
        cursor.execute("""
        INSERT INTO stories (user_id, title, content, genre)
        VALUES (?, ?, ?, ?)
        """, (user_id, title, content, genre))
        return cursor.lastrowid

def get_user_stories(user_id):
    with get_cursor() as cursor:
        cursor.execute("SELECT * FROM stories WHERE user_id = ? ORDER BY created_at DESC", (user_id,))
        return cursor.fetchall()

def get_story(story_id):
    with get_cursor() as cursor:
        cursor.execute("SELECT * FROM stories WHERE id = ?", (story_id,))
        return cursor.fetchone()

def update_story(story_id, title, content, genre):
    with get_cursor() as cursor:
        cursor.execute("""
        UPDATE stories
        SET title = ?, content = ?, genre = ?
        WHERE id = ?
        """, (title, content, genre, story_id))
        return cursor.rowcount > 0

def delete_story(story_id):
    with get_cursor() as cursor:
        cursor.execute("DELETE FROM stories WHERE id = ?", (story_id,))
        return cursor.rowcount > 0

# Initialize the database and perform migrations
init_db()
migrate_database()