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

# --- 2. دالة رفع الصورة تلقائياً من التليفون إلى رابط مباشر ---
def upload_image_to_imgbb(uploaded_file):
    api_key = "6d702677d167013ac92e1069b2d35442"  # مفتاح مجاني لرفع الصور
    url = "https://api.imgbb.com/1/upload"
    base64_image = base64.b64encode(uploaded_file.getvalue()).decode('utf-8')
    payload = {
        "key": api_key,
        "image": base64_image
    }
    res = requests.post(url, data=payload)
    if res.status_code == 200:
        return res.json()["data"]["url"]
    else:
        raise Exception("فشل رفع الصورة من التليفون، حاول اختيار صورة أخرى.")

# --- 3. محرك تحريك الوجه والعينين والشفاه (D-ID Lip-Sync Engine) ---
def generate_talking_animated_character(image_url, script_text, voice_id, api_key):
    """توليد فيديو حي للشخصية بتحريك العينين والوجه وتزامن حركة الشفاه"""
    url = "https://api.d-id.com/talks"
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "authorization": f"Basic {api_key}"
    }
    
    # إعدادات تحريك الوجه الكامل (تنشيط حركة العينين والشفاه والتعابير)
    payload = {
        "script": {
            "type": "text",
            "subtitles": "false",
            "provider": {
                "type": "microsoft",
                "voice_id": voice_id
            },
            "input": script_text
        },
        "config": {
            "fluent": "true",
            "pad_audio": "0.0",
            "stitch": True
        },
        "source_url": image_url
    }
    
    response = requests.post(url, json=payload, headers=headers)
    if response.status_code not in [200, 201]:
        raise Exception(f"خطأ من سيرفر التحريك: {response.text}")
        
    res_data = response.json()
    talk_id = res_data.get("id")
    status_url = f"https://api.d-id.com/talks/{talk_id}"
    
    # الانتظار حتى معالجة حركة الوجه والعينين
    for _ in range(60):
        time.sleep(3)
        status_res = requests.get(status_url, headers=headers).json()
        status = status_res.get("status")
        
        if status == "done":
            return status_res.get("result_url")
        elif status == "error":
            raise Exception(f"فشل توليد التحريك: {status_res}")
            
    raise Exception("استغرق التحريك وقتاً أطول من المتوقع، أعد المحاولة.")

# --- 4. واجهة التطبيق الرئيسية ---
st.title("🐒 استوديو تحريك شخصيات 'قردوش وعسيلة'")
st.caption("إنتاج فيديوهات ناطقة ومتحركة بالذكاء الاصطناعي (تحريك العيون، الوجه، والشفاه بالدارجة)")

# القائمة الجانبية لإدخال المفتاح
st.sidebar.header("🔑 إعدادات الخدمة")
api_key_input = st.sidebar.text_input(
    "D-ID API Key:", 
    type="password",
    help="احصل على المفتاح مجاناً من studio.d-id.com وانسخه هنا."
)

tab_create, tab_library = st.tabs(["🎬 إنشاء فيديو متحرك", "📁 أرشيف الفيديوهات"])

with tab_create:
    st.subheader("1️⃣ تحميل صور الشخصيات من التليفون (Galerie)")
    
    col_q, col_a = st.columns(2)
    
    with col_q:
        st.markdown("### 🐒 شخصية قردوش")
        file_qardoush = st.file_uploader("اختر صورة قردوش من التليفون:", type=["jpg", "jpeg", "png"], key="q_file")
        url_qardoush_fallback = st.text_input("أو ضع رابط صورة قردوش:", value="https://i.ibb.co/L5QG7C9/qardoush-maroccan.jpg", key="q_url")
        qardoush_voice = st.selectbox(
            "صوت قردوش:",
            ["صوت رجالي مغربي 🇲🇦 (Jamal)", "صوت رجالي فصيح 🇸🇦 (Hamed)"],
            key="q_v"
        )
        
    with col_a:
        st.markdown("### 🦧 شخصية عسيلة")
        file_aseela = st.file_uploader("اختر صورة عسيلة من التليفون:", type=["jpg", "jpeg", "png"], key="a_file")
        url_aseela_fallback = st.text_input("أو ضع رابط صورة عسيلة:", value="https://i.ibb.co/V3Kx82M/aseela-maroccan.jpg", key="a_url")
        aseela_voice = st.selectbox(
            "صوت عسيلة:",
            ["صوت نسائي مغربي 🇲🇦 (Mouna)", "صوت نسائي فصيح 🇸🇦 (Zariyah)"],
            key="a_v"
        )

    st.markdown("---")
    st.subheader("2️⃣ كتابة السيناريو والحوار بالدارجة")
    
    video_title = st.text_input("📌 عنوان المقطع:", value="حلقة جديدة: حكايات قردوش وعسيلة")
    
    col_s1, col_s2 = st.columns(2)
    
    with col_s1:
        script_qardoush = st.text_area(
            "💬 كلام قردوش بالدارجة:",
            value="السلام عليكم أ با الحباب! اليوم خاصني نعود لكم على واحد الأسطورة كاين فـ الدرب... راه أسطورة فـ الحلاقة!",
            height=120
        )
        
    with col_s2:
        script_aseela = st.text_area(
            "💬 كلام عسيلة بالدارجة:",
            value="ويلي أ قردوش! وياك ما عاوتاني مشيتي عنده وحسقتي ليه راسك؟ راه قلت ليك داك السيد كيزرب على بنادم!",
            height=120
        )

    voice_map = {
        "صوت رجالي مغربي 🇲🇦 (Jamal)": "ar-MA-JamalNeural",
        "صوت نسائي مغربي 🇲🇦 (Mouna)": "ar-MA-MounaNeural",
        "صوت رجالي فصيح 🇸🇦 (Hamed)": "ar-SA-HamedNeural",
        "صوت نسائي فصيح 🇸🇦 (Zariyah)": "ar-SA-ZariyahNeural"
    }

    st.markdown("---")
    st.subheader("3️⃣ اختيار الشخصية وبدء التوليد الحي")
    
    target_character = st.radio("اختر الشخصية التي تريد تحريكها في هذا المقطع:", ["قردوش", "عسيلة"], horizontal=True)
    
    if st.button("🚀 بدء توليد الفيديو الناطق والمتحرك (.mp4)", use_container_width=True):
        if not api_key_input:
            st.error("⚠️ يرجى أدخال D-ID API Key في القائمة الجانبية أولاً.")
        else:
            with st.spinner("جاري رفع الصورة وتحريك العينين والوجه والشفتين بالذكاء الاصطناعي..."):
                try:
                    if target_character == "قردوش":
                        char_name = "قردوش"
                        script = script_qardoush
                        voice = voice_map[qardoush_voice]
                        # التأكد من مصدر الصورة (رفع من المعرض أو الرابط)
                        if file_qardoush is not None:
                            img_url = upload_image_to_imgbb(file_qardoush)
                        else:
                            img_url = url_qardoush_fallback
                    else:
                        char_name = "عسيلة"
                        script = script_aseela
                        voice = voice_map[aseela_voice]
                        if file_aseela is not None:
                            img_url = upload_image_to_imgbb(file_aseela)
                        else:
                            img_url = url_aseela_fallback
                        
                    # توليد الفيديو الناطق
                    final_video_url = generate_talking_animated_character(
                        image_url=img_url,
                        script_text=script,
                        voice_id=voice,
                        api_key=api_key_input
                    )
                    
                    st.success(f"✨ تم إنتاج فيديو {char_name} بنجاح! الشخصية كتحرك عينينها وفمها بانسجام.")
                    st.video(final_video_url)
                    
                    # حفظ المقطع في الأرشيف
                    save_video_project(video_title, char_name, script, final_video_url)
                    
                except Exception as e:
                    st.error(f"❌ حدث خطأ: {str(e)}")

with tab_library:
    st.subheader("📁 أرشيف الفيديوهات والمشاريع المسجلة")
    df_videos = get_projects()
    if not df_videos.empty:
        st.dataframe(df_videos, use_container_width=True)
    else:
        st.info("لا توجد مشاريع مسجلة بعد في الأرشيف.")
