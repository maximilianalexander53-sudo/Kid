import streamlit as st
import requests
import sqlite3
import pandas as pd
from datetime import datetime
import json
import os
from gtts import gTTS
from moviepy.editor import ImageClip, AudioFileClip
from PIL import Image, ImageDraw, ImageFont

# --- إعدادات الصفحة ---
st.set_page_config(
    page_title="AI Executive Agent",
    page_icon="🤖",
    layout="wide"
)

# --- 1. قاعدة البيانات ---
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

# --- 2. محرك إنتاج الفيديو والصوت المباشر ---
def generate_video_file(text_voice, title_text, output_mp4="generated_video.mp4"):
    # أ) توليد ملف التعليق الصوتي
    audio_path = "temp_voice.mp3"
    tts = gTTS(text=text_voice, lang='ar')
    tts.save(audio_path)
    
    # ب) إنشاء تصميم خلفية الفيديو (مقاس Shorts 1080x1920)
    img_width, img_height = 1080, 1920
    image = Image.new('RGB', (img_width, img_height), color=(15, 23, 42))
    draw = ImageDraw.Draw(image)
    
    # رسم إطار ديكوري وتصميم
    draw.rectangle([50, 50, img_width-50, img_height-50], outline=(59, 130, 246), width=8)
    draw.text((100, 800), f"📌 {title_text[:30]}...", fill=(255, 255, 255))
    
    bg_path = "temp_bg.png"
    image.save(bg_path)
    
    # ج) تجميع الصوتي والصورة في فيديو محاكاة عبر MoviePy
    audio_clip = AudioFileClip(audio_path)
    video_clip = ImageClip(bg_path).set_duration(audio_clip.duration)
    video_clip = video_clip.set_audio(audio_clip)
    
    video_clip.write_videofile(
        output_mp4,
        fps=24,
        codec='libx264',
        audio_codec='aac',
        verbose=False,
        logger=None
    )
    
    audio_clip.close()
    video_clip.close()
    
    # تنظيف الملفات المؤقتة
    if os.path.exists(audio_path): os.remove(audio_path)
    if os.path.exists(bg_path): os.remove(bg_path)
    
    return output_mp4

# --- 3. محرك Polymarket ---
def fetch_polymarket_events(limit=15):
    url = f"https://gamma-api.polymarket.com/events?limit={limit}&active=true&closed=false"
    try:
        response = requests.get(url, timeout=10)
        return response.json() if response.status_code == 200 else []
    except Exception:
        return []

# --- الواجهة الرئيسية ---
st.title("🤖 AI Executive Agent")
st.caption("نظام التسيير التلقائي وإنتاج المحتوى المباشر")

tab_poly, tab_yt, tab_tasks = st.tabs(["📈 Polymarket Agent", "🎬 YouTube Video Generator", "📋 لوحة المهام"])

# --- TAB 1: POLYMARKET ---
with tab_poly:
    st.subheader("📊 تحليل الفرص والاحتمالات الحية")
    if st.button("🔄 مسح الأسواق وتحديث البيانات الآن", use_container_width=True):
        events = fetch_polymarket_events()
        if events:
            records = []
            for ev in events:
                records.append({
                    "الحدث": ev.get('title', 'N/A'),
                    "التصنيف": ev.get('category', 'عام'),
                    "حجم التداول": f"${float(ev.get('volume', 0)):,.0f}"
                })
            st.dataframe(pd.DataFrame(records), use_container_width=True)
            add_task("مسح أسواق Polymarket", "Polymarket", "مكتمل")

# --- TAB 2: YOUTUBE GENERATOR ---
with tab_yt:
    st.subheader("🎬 محرك إنتاج ومونتاج الفيديو التلقائي")
    
    topic = st.text_input("موضوع الفيديو المطلوب:")
    voice_script = st.text_area("نص التعليق الصوتي (Voiceover) المراد تسجيله في الفيديو:", 
                                value="أهلاً بكم. تطورات جديدة تشهدها منطقة الشرق الأوسط هذا الأسبوع مع تحركات سياسية مكثفة وانعكاسات مباشرة على أسعار الطاقة والأسواق العالمية.", 
                                height=120)
    
    if st.button("🚀 توليد وتصنيع ملف الفيديو (.mp4)", use_container_width=True):
        if topic and voice_script:
            with st.spinner("جاري توليد التعليق الصوتي العربي وتركيب مشاهد الفيديو... (قد يستغرق دقيقة)"):
                try:
                    video_file = generate_video_file(voice_script, topic)
                    
                    st.success("✨ تم إنشاء ملف الفيديو بنجاح!")
                    
                    # عرض الفيديو في الصفحة مع إمكانية التحميل
                    st.video(video_file)
                    
                    with open(video_file, "rb") as file:
                        st.download_button(
                            label="📥 تحميل ملف الفيديو MP4 للهاتف",
                            data=file,
                            file_name=f"{topic[:15]}.mp4",
                            mime="video/mp4",
                            use_container_width=True
                        )
                        
                    add_task(f"إنتاج فيديو MP4: {topic}", "YouTube", "تم الإنتاج بنجاح", f"طول النص: {len(voice_script)} حرف")
                except Exception as e:
                    st.error(f"حدث خطأ أثناء رندر الفيديو: {str(e)}")
        else:
            st.warning("يرجى كتابة الموضوع والنص الصوتي أولاً.")

# --- TAB 3: TASKS ---
with tab_tasks:
    st.subheader("📋 سجل جميع المهام المنفذة")
    st.dataframe(get_all_tasks(), use_container_width=True)
