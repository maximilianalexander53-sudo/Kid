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
from moviepy.editor import ImageClip, AudioFileClip
from PIL import Image, ImageDraw, ImageEnhance

# --- إعدادات الصفحة ---
st.set_page_config(
    page_title="AI Executive Agent",
    page_icon="🤖",
    layout="wide"
)

# --- 1. قاعدة البيانات (Task Tracker) ---
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

# --- 2. محركات الصوت والصور والفيديو ---
def generate_ai_voice_edge(text, voice_code, output_path="temp_voice.mp3"):
    """توليد تعليق صوتي مجاني عالي الجودة عبر Edge TTS"""
    async def _main():
        communicate = edge_tts.Communicate(text, voice_code)
        await communicate.save(output_path)
    asyncio.run(_main())
    return output_path

def generate_elevenlabs_cloned_voice(text, api_key, voice_id, output_path="temp_voice.mp3"):
    """توليد صوت مستنسخ عبر ElevenLabs API"""
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": api_key
    }
    data = {
        "text": text,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {"stability": 0.5, "similarity_boost": 0.8}
    }
    res = requests.post(url, json=data, headers=headers, timeout=30)
    if res.status_code == 200:
        with open(output_path, "wb") as f:
            f.write(res.content)
        return output_path
    else:
        raise Exception(f"خطأ ElevenLabs: {res.text}")

def fetch_illustrative_image(topic_text, width=1080, height=1920):
    """جلب صورة توضيحية ذكية ومطابقة للموضوع"""
    encoded_prompt = urllib.parse.quote(f"{topic_text} news coverage, HD realistic, cinematic lighting")
    image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width={width}&height={height}&nologo=true"
    
    bg_path = "temp_bg.png"
    try:
        res = requests.get(image_url, timeout=15)
        if res.status_code == 200:
            with open(bg_path, "wb") as f:
                f.write(res.content)
            img = Image.open(bg_path).convert('RGB')
        else:
            img = Image.new('RGB', (width, height), color=(15, 23, 42))
    except Exception:
        img = Image.new('RGB', (width, height), color=(15, 23, 42))
        
    # تعديل السطوع وإضافة تصميم عاجل
    enhancer = ImageEnhance.Brightness(img)
    img = enhancer.enhance(0.5)
    
    draw = ImageDraw.Draw(img)
    draw.rectangle([40, 100, width-40, 280], fill=(0, 0, 0, 180), outline=(59, 130, 246), width=5)
    draw.text((80, 160), "BREAKING NEWS / تغطية خاصة", fill=(239, 68, 68))
    draw.rectangle([40, height-350, width-40, height-100], fill=(0, 0, 0, 200), outline=(255, 255, 255), width=3)
    
    img.save(bg_path)
    return bg_path

def generate_video_file(audio_path, title_text, target_duration=30, output_mp4="generated_video.mp4"):
    """مونتاج وتجميع الفيديو بصيغة MP4"""
    bg_path = fetch_illustrative_image(title_text)
    audio_clip = AudioFileClip(audio_path)
    
    if audio_clip.duration > target_duration:
        audio_clip = audio_clip.subclip(0, target_duration)
        
    video_clip = ImageClip(bg_path).set_duration(target_duration)
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
st.caption("نظام التسيير التلقائي وإنتاج المحتوى المتكامل")

tab_poly, tab_yt, tab_tasks = st.tabs(["📈 Polymarket Agent", "🎬 YouTube Video Generator", "📋 لوحة المهام"])

# --- TAB 1: POLYMARKET ---
with tab_poly:
    st.subheader("📊 تحليل الفرص الأحداث والحجم المالي")
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
    st.subheader("🎬 محرك تصنيع الفيديو ومونتاجه التلقائي")
    
    topic = st.text_input("📌 عنوان أو موضوع الفيديو المطلوب:")
    video_duration = st.slider("⏱️ تحديد مدة الفيديو (بالثواني):", min_value=5, max_value=60, value=30, step=5)
    
    st.markdown("---")
    st.write("🎙️ **خيارات الصوت المتاحة:**")
    voice_source = st.radio("اختر طريقة إضافة الصوت:", 
                            ["أصوات ذكاء اصطناعي مجانية (Edge TTS)", 
                             "رفع تسجيلي الصوتي الخاص مجاناً 🎙️", 
                             "صوتي المستنسخ (ElevenLabs API) 🔑"], 
                            horizontal=False)
    
    final_audio_path = "temp_voice.mp3"
    ready_to_generate = False
    
    if voice_source == "أصوات ذكاء اصطناعي مجانية (Edge TTS)":
        voice_options = {
            "صوت رجالي مغربي 🇲🇦 (جمال)": "ar-MA-JamalNeural",
            "صوت نسائي مغربي 🇲🇦 (مطبقة/منى)": "ar-MA-MounaNeural",
            "صوت رجالي فصيح 🇸🇦 (حامد)": "ar-SA-HamedNeural",
            "صوت نسائي فصيح 🇸🇦 (زرياب)": "ar-SA-ZariyahNeural",
            "صوت رجالي مصري 🇪🇬 (شاكر)": "ar-EG-ShakirNeural"
        }
        selected_voice_label = st.selectbox("اختر نبرة الصوت المطلوب:", list(voice_options.keys()))
        selected_voice_code = voice_options[selected_voice_label]
        
        voice_script = st.text_area("نص السكربت (التعليق الصوتي):", 
                                    value="تطورات عاجلة وشديدة الأهمية فـ الشرق الأوسط هاد الأسبوع، متابعة مباشرة للتحركات السياسية وانعكاسها على الأسواق.", 
                                    height=100)
        ready_to_generate = True if topic and voice_script else False

    elif voice_source == "رفع تسجيلي الصوتي الخاص مجاناً 🎙️":
        uploaded_audio = st.file_uploader("ارفع ملف تسجيلك الصوتي من الهاتف (MP3 أو WAV):", type=["mp3", "wav"])
        if uploaded_audio:
            with open(final_audio_path, "wb") as f:
                f.write(uploaded_audio.getbuffer())
            st.audio(final_audio_path)
            ready_to_generate = True if topic else False
            
    else: # ElevenLabs
        st.info("💡 لاستخدام صوتك المستنسخ بدون تسجيل كرر، ضع بيانات حسابك فـ ElevenLabs:")
        eleven_api_key = st.text_input("مفتاح ElevenLabs API Key:", type="password")
        eleven_voice_id = st.text_input("رمز معرّف صوتك (Voice ID):")
        
        voice_script = st.text_area("نص السكربت المراد نطقه بصوتك المستنسخ:", height=100)
        ready_to_generate = True if topic and voice_script and eleven_api_key and eleven_voice_id else False

    st.markdown("---")
    if st.button("🚀 توليد وتصنيع ملف الفيديو (.mp4)", use_container_width=True):
        if ready_to_generate:
            with st.spinner(f"جاري معالجة الصوت واللقطة وتصنيع فيديو بمدة {video_duration} ثانية..."):
                try:
                    if voice_source == "أصوات ذكاء اصطناعي مجانية (Edge TTS)":
                        generate_ai_voice_edge(voice_script, selected_voice_code, final_audio_path)
                    elif voice_source == "صوتي المستنسخ (ElevenLabs API) 🔑":
                        generate_elevenlabs_cloned_voice(voice_script, eleven_api_key, eleven_voice_id, final_audio_path)
                        
                    video_file = generate_video_file(final_audio_path, topic, target_duration=video_duration)
                    
                    st.success("✨ تم إنشاء الفيديو بنجاح!")
                    st.video(video_file)
                    
                    with open(video_file, "rb") as file:
                        st.download_button(
                            label="📥 تحميل ملف الفيديو MP4 للهاتف",
                            data=file,
                            file_name=f"{topic[:15]}.mp4",
                            mime="video/mp4",
                            use_container_width=True
                        )
                        
                    add_task(f"إنتاج فيديو ({video_duration} ثانية): {topic}", "YouTube", "تم الإنتاج بنجاح")
                except Exception as e:
                    st.error(f"حدث خطأ أثناء رندر الفيديو: {str(e)}")
        else:
            st.warning("يرجى ملء كافة الخانات المطلوبة قبل البدء.")

# --- TAB 3: TASKS ---
with tab_tasks:
    st.subheader("📋 سجل جميع المهام المنفذة")
    st.dataframe(get_all_tasks(), use_container_width=True)
