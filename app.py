import streamlit as st
import requests
import sqlite3
import pandas as pd
from datetime import datetime
import time
import base64

# --- إعدادات الصفحة ---
st.set_page_config(
    page_title="استوديو قردوش وعسيلة الناطق (AI Talking Avatar)",
    page_icon="🐒",
    layout="wide"
)

# --- 1. إدارة قاعدة البيانات (SQLite) ---
def init_db():
    conn = sqlite3.connect('qardoush_studio.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS videos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            character_name TEXT NOT NULL,
            script_text TEXT NOT NULL,
            video_url TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

init_db()

def save_video_project(title, char_name, script_text, video_url):
    conn = sqlite3.connect('qardoush_studio.db')
    c = conn.cursor()
    c.execute(
        "INSERT INTO videos (title, character_name, script_text, video_url, created_at) VALUES (?, ?, ?, ?, ?)",
        (title, char_name, script_text, video_url, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    )
    conn.commit()
    conn.close()

def get_projects():
    conn = sqlite3.connect('qardoush_studio.db')
    df = pd.read_sql_query(
        "SELECT id AS 'المعرف', title AS 'عنوان المقطع', character_name AS 'الشخصية', script_text AS 'النص المكتوب', video_url AS 'رابط الفيديو', created_at AS 'تاريخ الإنتاج' FROM videos ORDER BY id DESC", 
        conn
    )
    conn.close()
    return df

# --- 2. دالة رفع الصورة تلقائياً من التليفون ---
def upload_image_to_imgbb(uploaded_file):
    api_key = "6d702677d167013ac92e1069b2d35442"
    url = "https://api.imgbb.com/1/upload"
    base64_image = base64.b64encode(uploaded_file.getvalue()).decode
