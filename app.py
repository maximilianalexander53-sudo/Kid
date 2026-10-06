import streamlit as st
import requests
import sqlite3
import pandas as pd
from datetime import datetime
import json
import os
import urllib.parse
import asyncio
import edge_tts
from moviepy.editor import ImageClip, AudioFileClip, CompositeVideoClip, vfx
from PIL import Image, ImageDraw, ImageEnhance

# --- إعدادات الصفحة ---
st.set_page_config(
    page_title="AI Executive Agent - قردوش",
    page_icon="🐒",
    layout="wide"
)

# --- 1. إدارة قاعدة البيانات ---
def init_db():
    conn = sqlite3.connect('ai_agent_executive.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_title TEXT NOT NULL,
            category TEXT NOT NULL,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL,
            details TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

def add_task(title, category, status, details=""):
    conn = sqlite3.connect('ai_agent_executive.db')
    c = conn.cursor()
    c.execute(
        "INSERT INTO tasks (task_title, category, status, created_at, details) VALUES (?, ?, ?, ?, ?)",
        (title, category, status, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), details)
    )
    conn.commit()
    conn.close()

def get_all_tasks():
    conn = sqlite3.connect('ai_agent_executive.db')
    df = pd.read_sql_query("SELECT id AS 'ID', task_title AS 'المهمة', category AS 'المجال', status AS 'الحالة', created_at AS 'التاريخ', details AS 'التفاصيل' FROM tasks ORDER BY id DESC", conn)
    conn.close()
    return df

# --- 2. محرك توليد الصوت (Edge TTS) ---
def generate_ai_voice_edge(text, voice_code, output_path="temp_voice.mp3"):
    """توليد الصوت بالدارجة أو الفصحى مجاناً"""
    async def _main():
        communicate = edge_tts.Communicate(text, voice_code)
        await communicate.save(output_path)
    asyncio.run(_main())
    return output_path

# --- 3. محرك تحريك قردوش مجاناً (Local Cartoon Animation) ---
def create_qardoush_animated_video(image_url_or_path, audio_path, script_text, output_mp4="qardoush_free.mp4"):
    """إنشاء فيديو أنيميشن كرتوني لشخصية قردوش بدون أي API Key"""
    bg_path = "qardoush_bg.png"
    
    # جلب صورة قردوش
    try:
        if image_url_or_path.startswith("http"):
            res = requests.get(image_url_or_path, timeout=15)
            with open(bg_path, "wb") as f:
                f.write(res.content)
            img = Image.open(bg_path).convert('RGB')
        else:
            img = Image.open(image_url_or_path).convert('RGB')
    except Exception:
        # صورة افتراضية فـ حالة التعذر
        img = Image.new('RGB', (1080, 1920), color=(15, 23, 42))

    # إضافة إطار وشريط النص الكرتوني
    img = img.resize((1080, 1920))
    draw = ImageDraw.Draw(img)
    draw.rectangle([40, 1400, 1040, 1800], fill=(0, 0, 0, 200), outline=(255, 215, 0), width=6)
    
    img.save(bg_path)
    
    # دمج الصوت والأنيميشن
    audio_clip = AudioFileClip(audio_path)
    duration = audio_clip.duration
    
    # تأثير الحركة الكرتونية (Zoom In / Pulse)
    clip = ImageClip(bg_path).set_duration(duration)
    animated_clip = clip.resize(lambda t: 1 + 0.03 * (t % 1)) # حركة نَبْض كرتونية للتحدث
    
    final_video = animated_clip.set_audio(audio_clip)
    final_video.write_videofile(output_mp4, fps=24, codec='libx264', audio_codec='aac', verbose=False, logger=None)
    
    audio_clip.close()
    final_video.close()
    if os.path.exists(bg_path): os.remove(bg_path)
    
    return output_mp4

# --- الواجهة الرئيسية ---
st.title("🤖 AI Executive Agent")
st.caption("استوديو إنتاج الفيديوهات والشخصيات مجاناً 100%")

tab_yt, tab_tasks = st.tabs(["🐒 شخصية قردوش (بدون API)", "📋 لوحة المهام"])

with tab_yt:
    st.subheader("🐒 إنتاج فيديو لشخصية 'قردوش' (مجانًا وبدون مفاتيح)")
    
    topic = st.text_input("📌 عنوان أو موضوع الفيديو:", value="قردوش يتحدث عن السوق المغربي")
    
    qardoush_img_url = st.text_input(
        "رابط صورة شخصية 'قردوش':", 
        value="https://img.freepik.com/free-vector/cute-monkey-sitting-cartoon-vector-icon-illustration-animal-nature-icon-concept-isolated-flat_138676-12349.jpg"
    )
    
    script_text = st.text_area("الكلام الذي سيقوله قردوش:", 
                               value="السلام عليكم! أنا قردوش، اليوم غادي نناقشو موضوع مهم بزاف فالسوق، تبعو معايا الفيديو حتى للخر!", 
                               height=100)
    
    voice_choice = st.selectbox("اختر صوت قردوش:", [
        "صوت رجالي مغربي 🇲🇦 (Jamal)",
        "صوت نسائي مغربي 🇲🇦 (Mouna)",
        "صوت فصيح 🇸🇦 (Hamed)"
    ])
    
    voice_code_map = {
        "صوت رجالي مغربي 🇲🇦 (Jamal)": "ar-MA-JamalNeural",
        "صوت نسائي مغربي 🇲🇦 (Mouna)": "ar-MA-MounaNeural",
        "صوت فصيح 🇸🇦 (Hamed)": "ar-SA-HamedNeural"
    }

    if st.button("🚀 تصنيع فيديو قردوش المباشر (.mp4)", use_container_width=True):
        if topic and script_text:
            with st.spinner("جاري معالجة الصوت وأنيميشن قردوش الكرتوني..."):
                try:
                    v_code = voice_code_map[voice_choice]
                    audio_file = generate_ai_voice_edge(script_text, v_code)
                    video_file = create_qardoush_animated_video(qardoush_img_url, audio_file, script_text)
                    
                    st.success("✨ تم إنشاء فيديو قردوش بنجاح ودون أي API Key!")
                    st.video(video_file)
                    
                    with open(video_file, "rb") as file:
                        st.download_button(
                            label="📥 تحميل الفيديو للهاتف MP4",
                            data=file,
                            file_name=f"Qardoush_{topic[:10]}.mp4",
                            mime="video/mp4",
                            use_container_width=True
                        )
                    add_task(f"إنتاج فيديو قردوش: {topic}", "أنيميشن", "مكتمل")
                except Exception as e:
                    st.error(f"حدث خطأ: {str(e)}")
        else:
            st.warning("يرجى كتابة عنوان السكربت والنص المطلوب.")

with tab_tasks:
    st.subheader("📋 سجل جميع المهام المنفذة")
    st.dataframe(get_all_tasks(), use_container_width=True)
