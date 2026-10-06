import streamlit as st
import requests
import sqlite3
import pandas as pd
from datetime import datetime
import time

# --- 1. إعدادات الصفحة والتصميم ---
st.set_page_config(
    page_title="استوديو فيديوهات قردوش وعسيلة",
    page_icon="🐒",
    layout="wide"
)

# --- 2. إعداد قاعدة البيانات (SQLite) ---
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
        "SELECT id AS 'المعرف', title AS 'عنوان المقطع', character_name AS 'الشخصية', script_text AS 'النص', video_url AS 'رابط الفيديو', created_at AS 'تاريخ الإنتاج' FROM videos ORDER BY id DESC", 
        conn
    )
    conn.close()
    return df

# --- 3. محرك التحريك والتوليد (D-ID Lip-Sync API) ---
def generate_talking_character(image_url, script_text, voice_id, api_key):
    url = "https://api.d-id.com/talks"
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "authorization": f"Basic {api_key}"
    }
    payload = {
        "script": {
            "type": "text",
            "subtitles": "false",
            "provider": {"type": "microsoft", "voice_id": voice_id},
            "input": script_text
        },
        "config": {"fluent": "true", "pad_audio": "0.0", "stitch": True},
        "source_url": image_url
    }
    
    response = requests.post(url, json=payload, headers=headers)
    if response.status_code not in [200, 201]:
        raise Exception(f"خطأ في الاتصال بالخدمة: {response.text}")
        
    talk_id = response.json().get("id")
    status_url = f"https://api.d-id.com/talks/{talk_id}"
    
    for _ in range(50):
        time.sleep(3)
        status_res = requests.get(status_url, headers=headers).json()
        if status_res.get("status") == "done":
            return status_res.get("result_url")
        elif status_res.get("status") == "error":
            raise Exception(f"فشل التوليد: {status_res}")
            
    raise Exception("استغرق التوليد وقتاً أطول من المتوقع.")

# --- 4. واجهة التطبيق الرئيسية ---
st.title("🐒 منصة إنتاج فيديوهات 'قردوش وعسيلة'")
st.caption("تطبيق مخصص لتوليد مقاطع فيديو متحركة بالذكاء الاصطناعي وبالدارجة المغربية")

# القائمة الجانبية المفتاح
st.sidebar.header("⚙️ الإعدادات والمفتاح")
api_key_input = st.sidebar.text_input("D-ID API Key:", type="password")

# التبويبات الرئيسية
tab_create, tab_history = st.tabs(["🎬 إنتاج مقطع جديد", "📁 الأرشيف والمشاريع"])

with tab_create:
    st.subheader("1️⃣ معلومات الشخصية والصورة")
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🐒 قردوش")
        qardoush_img = st.text_input("رابط صورة قردوش:", value="https://i.ibb.co/L5QG7C9/qardoush-maroccan.jpg", key="q_img")
        qardoush_voice = st.selectbox("صوت قردوش:", ["صوت رجالي مغربي 🇲🇦 (Jamal)", "صوت رجالي فصيح 🇸🇦 (Hamed)"], key="q_v")
        
    with col2:
        st.markdown("### 🦧 عسيلة")
        aseela_img = st.text_input("رابط صورة عسيلة:", value="https://i.ibb.co/V3Kx82M/aseela-maroccan.jpg", key="a_img")
        aseela_voice = st.selectbox("صوت عسيلة:", ["صوت نسائي مغربي 🇲🇦 (Mouna)", "صوت نسائي فصيح 🇸🇦 (Zariyah)"], key="a_v")

    st.markdown("---")
    st.subheader("2️⃣ السيناريو والحوار بالدارجة")
    video_title = st.text_input("عنوان الحلقة:", value="حلقة جديدة: قردوش وعسيلة")
    
    col_t1, col_t2 = st.columns(2)
    with col_t1:
        script_q = st.text_area("نص كلام قردوش:", value="السلام عليكم أ با الحباب! اليوم غادي نعود لكم قصة جديدة...", height=100)
    with col_t2:
        script_a = st.text_area("نص كلام عسيلة:", value="وا قردوش! وياك ما عاوتاني مشيتي كتقلب على المشاكل فـ الدرب؟", height=100)

    voice_map = {
        "صوت رجالي مغربي 🇲🇦 (Jamal)": "ar-MA-JamalNeural",
        "صوت نسائي مغربي 🇲🇦 (Mouna)": "ar-MA-MounaNeural",
        "صوت رجالي فصيح 🇸🇦 (Hamed)": "ar-SA-HamedNeural",
        "صوت نسائي فصيح 🇸🇦 (Zariyah)": "ar-SA-ZariyahNeural"
    }

    st.markdown("---")
    st.subheader("3️⃣ التوليد والتحريك")
    selected_char = st.radio("اختر الشخصية اللي بغيتي تحركها فـ هاد المقطع:", ["قردوش", "عسيلة"], horizontal=True)

    if st.button("🚀 بدء توليد الفيديو (.mp4)", use_container_width=True):
        if not api_key_input:
            st.error("⚠️ عفاك دخل D-ID API Key فـ القائمة الجانبية الأول.")
        else:
            with st.spinner("جاري تحريك الشفاه والوجه بذكاء اصطناعي..."):
                try:
                    if selected_char == "قردوش":
                        c_name, img, script, voice = "قردوش", qardoush_img, script_q, voice_map[qardoush_voice]
                    else:
                        c_name, img, script, voice = "عسيلة", aseela_img, script_a, voice_map[aseela_voice]
                        
                    url = generate_talking_character(img, script, voice, api_key_input)
                    st.success(f"✅ تم توليد فيديو {c_name} بنجاح!")
                    st.video(url)
                    save_video_project(video_title, c_name, script, url)
                except Exception as e:
                    st.error(f"❌ وقع خطأ: {str(e)}")

with tab_history:
    st.subheader("📁 الفيديوهات المحفوظة سابقاً")
    df = get_projects()
    if not df.empty:
        st.dataframe(df, use_container_width=True)
    else:
        st.info("ما كاين حتى فيديو محفوظ حالياً.")
