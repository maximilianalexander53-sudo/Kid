import streamlit as st
import requests
import sqlite3
import pandas as pd
from datetime import datetime
import json
import os
import time
import urllib.parse
import asyncio
import edge_tts
from moviepy.editor import ImageClip, AudioFileClip
from PIL import Image, ImageDraw, ImageEnhance

# --- إعدادات الصفحة ---
st.set_page_config(
    page_title="AI Executive Agent - قردوش والإنتاج المرئي",
    page_icon="🐒",
    layout="wide"
)

# --- 1. إدارة قاعدة البيانات (SQLite) ---
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

# --- 2. محركات الصوت والصورة ---
def generate_ai_voice_edge(text, voice_code, output_path="temp_voice.mp3"):
    """توليد صوت مجاني عالي الجودة عبر Edge TTS"""
    async def _main():
        communicate = edge_tts.Communicate(text, voice_code)
        await communicate.save(output_path)
    asyncio.run(_main())
    return output_path

def generate_elevenlabs_cloned_voice(text, api_key, voice_id, output_path="temp_voice.mp3"):
    """توليد صوت استنساخ شخصي عبر ElevenLabs API"""
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

def create_did_talking_qardoush(image_url, voice_script, api_key, voice_id="ar-MA-JamalNeural", output_mp4="qardoush_video.mp4"):
    """تحريك شخصية قردوش وجعلها تتكلم بالذكاء الاصطناعي (D-ID)"""
    url = "https://api.d-id.com/talks"
    headers = {
        "Authorization": f"Basic {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "source_url": image_url,
        "script": {
            "type": "text",
            "subtitles": "false",
            "provider": {
                "type": "microsoft",
                "voice_id": voice_id
            },
            "input": voice_script
        }
    }
    
    response = requests.post(url, json=payload, headers=headers)
    if response.status_code != 201:
        raise Exception(f"خطأ في الاتصال بـ D-ID: {response.text}")
        
    talk_id = response.json().get("id")
    status_url = f"https://api.d-id.com/talks/{talk_id}"
    
    # انتظار اكتمال رندر الفيديو
    for _ in range(35):
        time.sleep(3)
        res = requests.get(status_url, headers=headers)
        if res.status_code == 200:
            data = res.json()
            if data.get("status") == "done":
                result_url = data.get("result_url")
                video_res = requests.get(result_url)
                with open(output_mp4, "wb") as f:
                    f.write(video_res.content)
                return output_mp4
            elif data.get("status") == "error":
                raise Exception("فشلت عملية تحريك الشخصية من المصدر.")
                
    raise Exception("استغرق التوليد وقتاً أطول من المتوقع، يرجى المحاولة لاحقاً.")

def fetch_illustrative_image(topic_text, width=1080, height=1920):
    """توليد خلفية توضيحية للفيديوهات العادية"""
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
        
    enhancer = ImageEnhance.Brightness(img)
    img = enhancer.enhance(0.5)
    
    draw = ImageDraw.Draw(img)
    draw.rectangle([40, 100, width-40, 280], fill=(0, 0, 0, 180), outline=(59, 130, 246), width=5)
    draw.text((80, 160), "BREAKING NEWS / تغطية خاصة", fill=(239, 68, 68))
    
    img.save(bg_path)
    return bg_path

def generate_standard_video(audio_path, title_text, target_duration=30, output_mp4="generated_video.mp4"):
    """رندر ومونتاج الفيديو الإخباري العادي"""
    bg_path = fetch_illustrative_image(title_text)
    audio_clip = AudioFileClip(audio_path)
    
    if audio_clip.duration > target_duration:
        audio_clip = audio_clip.subclip(0, target_duration)
        
    video_clip = ImageClip(bg_path).set_duration(target_duration)
    video_clip = video_clip.set_audio(audio_clip)
    
    video_clip.write_videofile(output_mp4, fps=24, codec='libx264', audio_codec='aac', verbose=False, logger=None)
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

# --- الواجهة الرئيسية للبرنامج ---
st.title("🤖 AI Executive Agent")
st.caption("نظام صناعة الفيديوهات بالذكاء الاصطناعي وشخصيات الرسوم المتحركة")

tab_yt, tab_poly, tab_tasks = st.tabs(["🎬 استوديو الفيديوهات و'قردوش'", "📈 Polymarket Agent", "📋 لوحة المهام"])

# --- TAB 1: استوديو الفيديوهات ---
with tab_yt:
    st.subheader("🎯 اختر نوع الإنتاج المطلوب:")
    video_type = st.radio("وضع الإنتاج:", 
                          ["🐒 فيديو متحرك بشخصية 'قردوش' (Talking Avatar)", 
                           "📰 فيديو إخباري عادي (صورة توضيحية + تعليق صوتي)"], 
                          horizontal=True)
    
    st.markdown("---")
    topic = st.text_input("📌 عنوان أو موضوع الفيديو الرئيسي:")
    
    # 🐒 الوضع الأول: شخصية قردوش المتكلمة
    if video_type == "🐒 فيديو متحرك بشخصية 'قردوش' (Talking Avatar)":
        st.info("💡 ستقوم شخصية 'قردوش' بالتحدث وتزامن الشفاه مع الصوت بالدارجة المغربية تلقائياً!")
        
        qardoush_img_url = st.text_input(
            "رابط صورة شخصية 'قردوش' (صورة كرتونية بملامح واضحة):", 
            value="https://img.freepik.com/free-vector/cute-monkey-sitting-cartoon-vector-icon-illustration-animal-nature-icon-concept-isolated-flat_138676-12349.jpg"
        )
        
        did_api_key = st.text_input("مفتاح D-ID API Key:", type="password", help="احصل عليه مجاناً من D-ID.com")
        
        qardoush_script = st.text_area("الكلام الذي سيقوله قردوش:", 
                                       value="السلام عليكم! أنا قردوش، اليوم غادي نناقشو موضوع مهم بزاف فالسوق، تبعو معايا الفيديو حتى للخر!", 
                                       height=100)
        
        qardoush_voice = st.selectbox("نبرة صوت قردوش:", [
            "صوت رجالي مغربي 🇲🇦 (Jamal)",
            "صوت نسائي مغربي 🇲🇦 (Mouna)",
            "صوت فصيح 🇸🇦 (Hamed)"
        ])
        
        voice_code_map = {
            "صوت رجالي مغربي 🇲🇦 (Jamal)": "ar-MA-JamalNeural",
            "صوت نسائي مغربي 🇲🇦 (Mouna)": "ar-MA-MounaNeural",
            "صوت فصيح 🇸🇦 (Hamed)": "ar-SA-HamedNeural"
        }
        
        if st.button("🚀 توليد فيديو قردوش المتكلم (.mp4)", use_container_width=True):
            if topic and qardoush_script and did_api_key and qardoush_img_url:
                with st.spinner("جاري تحريك قردوش وضبط حركة الفم والوجه..."):
                    try:
                        v_code = voice_code_map[qardoush_voice]
                        video_file = create_did_talking_qardoush(qardoush_img_url, qardoush_script, did_api_key, voice_id=v_code)
                        
                        st.success("✨ تم إنشاء فيديو قردوش المتكلم بنجاح!")
                        st.video(video_file)
                        
                        with open(video_file, "rb") as file:
                            st.download_button(
                                label="📥 تحميل فيديو قردوش للهاتف MP4",
                                data=file,
                                file_name=f"Qardoush_{topic[:10]}.mp4",
                                mime="video/mp4",
                                use_container_width=True
                            )
                        add_task(f"إنتاج فيديو قردوش: {topic}", "أنيميشن", "مكتمل")
                    except Exception as e:
                        st.error(f"حدث خطأ: {str(e)}")
            else:
                st.warning("يرجى ملء جميع الخانات (عنوان الفيديو، النص، المفتاح ورابط الصورة).")

    # 📰 الوضع الثاني: فيديو إخباري عادي
    else:
        video_duration = st.slider("⏱️ تحديد مدة الفيديو (بالثواني):", min_value=5, max_value=60, value=30, step=5)
        
        st.write("🎙️ **مصدر التعليق الصوتي:**")
        voice_source = st.radio("اختر طريقة الصوت:", 
                                ["أصوات ذكاء اصطناعي مجانية (Edge TTS)", 
                                 "رفع تسجيلي الصوتي الخاص مجاناً 🎙️", 
                                 "صوتي المستنسخ (ElevenLabs API) 🔑"])
        
        final_audio_path = "temp_voice.mp3"
        ready_to_gen = False
        
        if voice_source == "أصوات ذكاء اصطناعي مجانية (Edge TTS)":
            voice_opts = {
                "صوت رجالي مغربي 🇲🇦 (جمال)": "ar-MA-JamalNeural",
                "صوت نسائي مغربي 🇲🇦 (منى)": "ar-MA-MounaNeural",
                "صوت رجالي فصيح 🇸🇦 (حامد)": "ar-SA-HamedNeural",
                "صوت نسائي فصيح 🇸🇦 (زرياب)": "ar-SA-ZariyahNeural"
            }
            sel_voice = st.selectbox("اختر الصوت:", list(voice_opts.keys()))
            script_text = st.text_area("نص السكربت الصوتي:", value="تطورات عاجلة وشديدة الأهمية فـ الأسواق هاد الأسبوع...", height=100)
            ready_to_gen = True if topic and script_text else False

        elif voice_source == "رفع تسجيلي الصوتي الخاص مجاناً 🎙️":
            up_file = st.file_uploader("ارفع مقطعك الصوتي (MP3/WAV):", type=["mp3", "wav"])
            if up_file:
                with open(final_audio_path, "wb") as f:
                    f.write(up_file.getbuffer())
                st.audio(final_audio_path)
                ready_to_gen = True if topic else False
                
        else:
            eleven_key = st.text_input("مفتاح ElevenLabs API Key:", type="password")
            eleven_id = st.text_input("معرف صوتك المستنسخ (Voice ID):")
            script_text = st.text_area("نص السكربت لنطقه بصوتك:", height=100)
            ready_to_gen = True if topic and script_text and eleven_key and eleven_id else False

        if st.button("🚀 تصنيع الفيديو العادي (.mp4)", use_container_width=True):
            if ready_to_gen:
                with st.spinner("جاري مونتاج الفيديو والصوت..."):
                    try:
                        if voice_source == "أصوات ذكاء اصطناعي مجانية (Edge TTS)":
                            generate_ai_voice_edge(script_text, voice_opts[sel_voice], final_audio_path)
                        elif voice_source == "صوتي المستنسخ (ElevenLabs API) 🔑":
                            generate_elevenlabs_cloned_voice(script_text, eleven_key, eleven_id, final_audio_path)
                            
                        vid_file = generate_standard_video(final_audio_path, topic, target_duration=video_duration)
                        st.success("✨ تم إنشاء الفيديو بنجاح!")
                        st.video(vid_file)
                        
                        with open(vid_file, "rb") as file:
                            st.download_button(
                                label="📥 تحميل الفيديو للهاتف MP4",
                                data=file,
                                file_name=f"{topic[:10]}.mp4",
                                mime="video/mp4",
                                use_container_width=True
                            )
                        add_task(f"إنتاج فيديو عادي: {topic}", "YouTube", "مكتمل")
                    except Exception as e:
                        st.error(f"خطأ أثناء التصنيع: {str(e)}")
            else:
                st.warning("يرجى التأكد من ملء جميع البيانات المطلوبة.")

# --- TAB 2: POLYMARKET ---
with tab_poly:
    st.subheader("📊 تحليل الفرص الأحداث الحية في الأسواق")
    if st.button("🔄 مسح أسواق Polymarket وتحديث البيانات", use_container_width=True):
        events = fetch_polymarket_events()
        if events:
            records = [{
                "الحدث": ev.get('title', 'N/A'),
                "التصنيف": ev.get('category', 'عام'),
                "حجم التداول": f"${float(ev.get('volume', 0)):,.0f}"
            } for ev in events]
            st.dataframe(pd.DataFrame(records), use_container_width=True)
            add_task("مسح أسواق Polymarket", "Polymarket", "مكتمل")
        else:
            st.info("لم يتم العثور على بيانات أو تعذر الاتصال بالمصدر.")

# --- TAB 3: TASKS ---
with tab_tasks:
    st.subheader("📋 سجل جميع المهام المنفذة والعمليات")
    st.dataframe(get_all_tasks(), use_container_width=True)
