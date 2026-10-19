import streamlit as st
import sqlite3
import requests
import json
import datetime
import urllib.parse
import phonenumbers
from phonenumbers import carrier, geocoder, timezone
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim

# ----------------- 1. إعدادات الصفحة والتصميم السيبراني -----------------
st.set_page_config(
    page_title="CYBER INTEL // AI OSINT CORE",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
    .stApp { background-color: #050811; color: #e2e8f0; font-family: 'Segoe UI', Roboto, sans-serif; }
    h1, h2, h3 { color: #00f0ff !important; font-weight: 700 !important; }
    .stTextInput > div > div > input {
        background-color: #0a1120 !important;
        color: #00f0ff !important;
        border: 1px solid #1e293b !important;
        border-radius: 8px !important;
        padding: 12px !important;
        font-family: monospace;
    }
    .stButton > button {
        background: linear-gradient(135deg, #0055ff 0%, #00d4ff 100%) !important;
        color: #ffffff !important;
        font-weight: bold !important;
        border-radius: 8px !important;
        padding: 0.6rem 1rem !important;
        border: none !important;
        box-shadow: 0 4px 15px rgba(0, 212, 255, 0.3) !important;
        width: 100% !important;
    }
    .stButton > button:hover { box-shadow: 0 6px 20px rgba(0, 212, 255, 0.6) !important; }
    [data-testid="stSidebar"] { background-color: #03060d !important; border-right: 1px solid #1e293b !important; }
    .metric-box {
        background: rgba(10, 17, 32, 0.7);
        border: 1px solid #1e293b;
        border-left: 4px solid #00f0ff;
        padding: 15px;
        border-radius: 8px;
        margin-bottom: 10px;
    }
    </style>
""", unsafe_allow_html=True)

# ----------------- 2. إدارة قاعدة البيانات (SQLite) -----------------
def init_db():
    conn = sqlite3.connect('osint_master.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS searches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            query_type TEXT,
            query_value TEXT,
            result_data TEXT,
            timestamp TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

def save_to_history(q_type, q_value, data):
    conn = sqlite3.connect('osint_master.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO searches (query_type, query_value, result_data, timestamp) VALUES (?, ?, ?, ?)',
                   (q_type, q_value, json.dumps(data, ensure_ascii=False), str(datetime.datetime.now())[:19]))
    conn.commit()
    conn.close()

# ----------------- 3. الوظائف الذكية وأدوات الاستخبار -----------------

# (أ) البحث الذكي بالاسم واللقب فقط (AI & Linux-Style Dorking/Recon)
def ai_name_recon(full_name):
    # تنظيف الاسم وتوليد السياقات الاحتمالية (Username Variations)
    clean_name = full_name.strip().lower()
    parts = clean_name.split()
    
    if len(parts) < 2:
        return {"error": "المرجو إدخال الاسم واللقب معاً (مثال: Mohamed Alami)"}
    
    first, last = parts[0], parts[-1]
    
    # توليد الأنماط المحتملة لليوزيرز (Usernames)
    usernames = [
        f"{first}{last}",
        f"{first}.{last}",
        f"{first}_{last}",
        f"{last}{first}",
        f"{first[0]}{last}"
    ]
    
    # روابط المنصات الأساسية للفحص التلقائي
    social_profiles = {}
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    
    for u in usernames:
        platforms = {
            "Instagram": f"https://www.instagram.com/{u}/",
            "Facebook": f"https://www.facebook.com/{first}.{last}",
            "Twitter/X": f"https://twitter.com/{u}",
            "GitHub": f"https://github.com/{u}"
        }
        for plat, url in platforms.items():
            if plat not in social_profiles:
                try:
                    res = requests.get(url, headers=headers, timeout=3)
                    if res.status_code == 200 and "Page Not Found" not in res.text:
                        social_profiles[plat] = {"status": "مكتشف ✅", "url": url}
                    else:
                        social_profiles[plat] = {"status": "غير مؤكد ❌", "url": url}
                except:
                    social_profiles[plat] = {"status": "فحص مغلق ⚠️", "url": url}
                    
    # توليد استعلامات البحث المتقدم (Google Dorks) للايميل والمواقع
    encoded_query = urllib.parse.quote(f'"{full_name}"')
    dorks = {
        "بحث عن الإيميلات المحتملة": f"site:hunter.io OR site:rocketreach.co {full_name}",
        "بحث عن المواقع والمدونات": f"intitle:{full_name} filetype:html OR filetype:php",
        "Google Search Direct": f"https://www.google.com/search?q={encoded_query}"
    }
    
    results = {
        "الاسم المستهدف": full_name,
        "الاحتمالات المولدة (Usernames)": usernames,
        "الحسابات الاجتماعية المستخرجة": social_profiles,
        "استعلامات الذكاء الاصطناعي (Dorks)": dorks
    }
    return results

# (ب) تحليل رقم الهاتف والموقع
def check_phone_with_location(phone_number):
    try:
        parsed_number = phonenumbers.parse(phone_number)
        if not phonenumbers.is_valid_number(parsed_number):
            return {"error": "رقم الهاتف غير صالح."}, None, None
        
        country_ar = geocoder.description_for_number(parsed_number, "ar")
        country_en = geocoder.description_for_number(parsed_number, "en")
        operator = carrier.name_for_number(parsed_number, "ar")
        tz = timezone.time_zones_for_number(parsed_number)
        
        geolocator = Nominatim(user_agent="cyber_intel_osint")
        location = geolocator.geocode(country_en)
        lat, lon = (location.latitude, location.longitude) if location else (None, None)
        
        details = {
            "الصلاحية": "صالح ✅",
            "الدولة": country_ar if country_ar else "غير معروف",
            "المشغل": operator if operator else "غير معروف",
            "المنطقة الزمنية": list(tz) if tz else [],
            "Lat/Lon": [lat, lon]
        }
        return details, lat, lon
    except Exception as e:
        return {"error": str(e)}, None, None

# ----------------- 4. واجهة المستخدم الرئيسية -----------------

st.title("🛡️ CYBER INTEL // AI OSINT CORE")
st.markdown("##### نظام الاستخبار الذكي المستوحى من أدوات لينكس (Linux OSINT & AI Recon)")
st.markdown("---")

# القائمة الجانبية (Sidebar)
st.sidebar.title("⚡ LOGS // السجل")
if st.sidebar.button("مسح السجل بالكامل"):
    conn = sqlite3.connect('osint_master.db')
    conn.execute('DELETE FROM searches')
    conn.commit()
    conn.close()
    st.sidebar.success("تم مسح السجل!")

conn = sqlite3.connect('osint_master.db')
cursor = conn.cursor()
cursor.execute('SELECT query_type, query_value, timestamp FROM searches ORDER BY id DESC LIMIT 10')
history = cursor.fetchall()
conn.close()

for item in history:
    st.sidebar.markdown(f"""
    <div class="metric-box">
        <small style="color:#00f0ff">[{item[0]}]</small> <b>{item[1]}</b><br>
        <small style="color:#64748b">⏱️ {item[2]}</small>
    </div>
    """, unsafe_allow_html=True)

# التبويبات الرئيسية
tab1, tab2, tab3 = st.tabs([
    "🤖 البحث الذكي بالاسم واللقب (AI Recon)", 
    "📍 تحديد موقع الرقم (Geo-Phone)", 
    "🔍 البحث المعمق المتقدم"
])

# ----- التبويب الأول: البحث الذكي بالاسم واللقب فقط -----
with tab1:
    st.subheader("🧠 الاستعلام الآلي بالاسم والنسب فقط (AI Social & Web Discovery)")
    st.markdown("أدخل الاسم واللقب، وسيقوم النظام بتوليد خوارزميات البحث وفحص المنصات تلقائياً.")
    
    name_input = st.text_input("أدخل الاسم الكامل (مثال: Mohamed Alami):")
    
    if st.button("بدء الفحص والتحليل الذكي"):
        if name_input:
            with st.spinner("جاري تشغيل خوارزميات البحث واستخراج الحسابات الاجتماعية والإيميلات..."):
                recon_data = ai_name_recon(name_input)
                
                if "error" in recon_data:
                    st.error(recon_data["error"])
                else:
                    save_to_history("AI Name Recon", name_input, recon_data)
                    
                    st.success("تم الانتهاء من التحليل الاستخباري بنجاح!")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown("### 🌐 الحسابات والمنصات المستخرجة")
                        for platform, info in recon_data["الحسابات الاجتماعية المستخرجة"].items():
                            st.markdown(f"- **{platform}**: [{info['status']}]({info['url']})")
                            
                    with col2:
                        st.markdown("### 📧 الإيميلات والمواقع المقترحة")
                        st.write("أبرز اليوزيرز المحتملة:", recon_data["الاحتمالات المولدة (Usernames)"])
                        st.json(recon_data["استعلامات الذكاء الاصطناعي (Dorks)"])
                        
                    st.download_button(
                        label="📥 تحميل تقرير الاستخبارات الكامل (JSON)",
                        data=json.dumps(recon_data, indent=4, ensure_ascii=False),
                        file_name=f"ai_recon_{name_input.replace(' ', '_')}.json",
                        mime="application/json"
                    )
        else:
            st.warning("المرجو إدخال الاسم واللقب أولاً.")

# ----- التبويب الثاني: تحديد موقع الرقم -----
with tab2:
    st.subheader("📱 تحليل بيانات الهاتف والتحديد الجغرافي")
    phone_input = st.text_input("أدخل الرقم مع الرمز الدولي (مثال: +212600000000):")
    
    if st.button("بدء المسح وتحديد الموقع"):
        if phone_input:
            with st.spinner("جاري استعلام التغطية الجغرافية..."):
                details, lat, lon = check_phone_with_location(phone_input)
                if "error" in details:
                    st.error(details["error"])
                else:
                    save_to_history("Geo-Phone", phone_input, details)
                    c1, c2 = st.columns([1, 1.2])
                    with c1:
                        st.success("تم التقرير بنجاح!")
                        st.json(details)
                    with c2:
                        st.subheader("🗺️ الخريطة التفاعلية")
                        if lat and lon:
                            m = folium.Map(location=[lat, lon], zoom_start=6, tiles="CartoDB dark_matter")
                            folium.Marker([lat, lon], popup=f"TARGET: {phone_input}", icon=folium.Icon(color="info", icon="signal", prefix="fa")).add_to(m)
                            st_folium(m, width=500, height=350)
                        else:
                            st.warning("تعذر تحديد الإحداثيات على الخريطة.")
        else:
            st.warning("يرجى إدخال رقم الهاتف.")

# ----- التبويب الثالث: البحث المعمق -----
with tab3:
    st.subheader("🔍 البحث المتقدم عبر محركات الويب")
    st.info("هذا القسم مخصص لتوليد صيغ البحث المتقدمة (Dorks) المعتمدة في اختبارات الاختراق وجمع المعلومات المفتوحة.")
