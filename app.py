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

# ----------------- 1. إعدادات الصفحة والتصميم (Green Hacker / Pirate Theme) -----------------
st.set_page_config(
    page_title="PIRATE INTEL // HACKER OSINT CORE",
    page_icon="🏴‍☠️",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
    .stApp { background-color: #020408; color: #00ff66; font-family: 'Courier New', Courier, monospace; }
    
    /* اللوغو والعناوين باللون الأخضر البرمجي */
    h1, h2, h3 { color: #00ff66 !important; font-family: 'Courier New', Courier, monospace; font-weight: 700 !important; text-shadow: 0 0 10px rgba(0, 255, 102, 0.4); }
    
    /* مربعات الإدخال بتصميم لغة البرمجة */
    .stTextInput > div > div > input, .stTextArea > div > div > textarea {
        background-color: #050d08 !important;
        color: #00ff66 !important;
        border: 1px solid #00ff66 !important;
        border-radius: 4px !important;
        padding: 12px !important;
        font-family: 'Courier New', Courier, monospace;
    }
    .stTextInput > div > div > input:focus {
        box-shadow: 0 0 15px rgba(0, 255, 102, 0.6) !important;
    }

    /* أزرار التشغيل السيبرانية */
    .stButton > button {
        background: linear-gradient(135deg, #003311 0%, #00ff66 100%) !important;
        color: #020408 !important;
        font-weight: bold !important;
        font-family: 'Courier New', Courier, monospace;
        border-radius: 4px !important;
        padding: 0.6rem 1rem !important;
        border: 1px solid #00ff66 !important;
        box-shadow: 0 0 10px rgba(0, 255, 102, 0.4) !important;
        width: 100% !important;
    }
    .stButton > button:hover {
        background: #00ff66 !important;
        box-shadow: 0 0 20px rgba(0, 255, 102, 0.8) !important;
    }

    /* الشريط الجانبي */
    [data-testid="stSidebar"] { background-color: #010204 !important; border-right: 1px solid #00ff66 !important; }
    
    .metric-box {
        background: rgba(5, 13, 8, 0.8);
        border: 1px solid #00ff66;
        border-left: 4px solid #00ff66;
        padding: 12px;
        border-radius: 4px;
        margin-bottom: 10px;
    }
    </style>
""", unsafe_allow_html=True)

# ----------------- 2. إدارة قاعدة البيانات (SQLite) -----------------
def init_db():
    conn = sqlite3.connect('pirate_osint.db')
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
    conn = sqlite3.connect('pirate_osint.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO searches (query_type, query_value, result_data, timestamp) VALUES (?, ?, ?, ?)',
                   (q_type, q_value, json.dumps(data, ensure_ascii=False), str(datetime.datetime.now())[:19]))
    conn.commit()
    conn.close()

# ----------------- 3. الوظائف والأدوات البرمجية -----------------

def live_web_search(query, api_key):
    if not api_key:
        return {"error": "المرجو إدخال مفتاح Serper/SerpAPI في الشريط الجانبي."}
    url = "https://google.serper.dev/search"
    payload = json.dumps({"q": query, "gl": "ma"})
    headers = {'X-API-KEY': api_key, 'Content-Type': 'application/json'}
    try:
        response = requests.request("POST", url, headers=headers, data=payload)
        return response.json()
    except Exception as e:
        return {"error": str(e)}

def sherlock_username_scan(username):
    platforms = {
        "Instagram": f"https://www.instagram.com/{username}/",
        "Facebook": f"https://www.facebook.com/{username}",
        "Twitter/X": f"https://twitter.com/{username}",
        "GitHub": f"https://github.com/{username}",
        "TikTok": f"https://www.tiktok.com/@{username}",
        "Reddit": f"https://www.reddit.com/user/{username}",
        "Pinterest": f"https://www.pinterest.com/{username}/",
        "Telegram": f"https://t.me/{username}"
    }
    results = {}
    headers = {"User-Agent": "Mozilla/5.0"}
    for plat, url in platforms.items():
        try:
            res = requests.get(url, headers=headers, timeout=3)
            if res.status_code == 200 and "Page Not Found" not in res.text:
                results[plat] = {"status": "[FOUND] ✅", "url": url}
            else:
                results[plat] = {"status": "[NOT_FOUND] ❌", "url": url}
        except:
            results[plat] = {"status": "[ERROR] ⚠️", "url": url}
    return results

def hunter_email_intel(first_name, last_name, domain="gmail.com"):
    f, l = first_name.lower().strip(), last_name.lower().strip()
    generated_emails = [
        f"{f}.{l}@{domain}",
        f"{f}{l}@{domain}",
        f"{f}_{l}@{domain}",
        f"{f[0]}{l}@{domain}",
        f"{f}{l[0]}@{domain}"
    ]
    results = {}
    for email in generated_emails:
        results[email] = "[PATTERN_MATCH] 🔍"
    return results

def check_phone_with_location(phone_number):
    try:
        parsed_number = phonenumbers.parse(phone_number)
        if not phonenumbers.is_valid_number(parsed_number):
            return {"error": "رقم الهاتف غير صالح."}, None, None
        
        country_ar = geocoder.description_for_number(parsed_number, "ar")
        country_en = geocoder.description_for_number(parsed_number, "en")
        operator = carrier.name_for_number(parsed_number, "ar")
        tz = timezone.time_zones_for_number(parsed_number)
        
        geolocator = Nominatim(user_agent="pirate_osint_core")
        location = geolocator.geocode(country_en)
        lat, lon = (location.latitude, location.longitude) if location else (None, None)
        
        details = {
            "الصلاحية": "VALID ✅",
            "الدولة": country_ar if country_ar else "UNKNOWN",
            "المشغل": operator if operator else "UNKNOWN",
            "المنطقة الزمنية": list(tz) if tz else [],
            "Lat/Lon": [lat, lon]
        }
        return details, lat, lon
    except Exception as e:
        return {"error": str(e)}, None, None

# ----------------- 4. واجهة المستخدم (اللوغو الجديد) -----------------

# اللوغو المخصص بعلم القراصنة ولغة البرمجة الخضراء
st.markdown("""
    <div style="display: flex; align-items: center; gap: 15px; background: rgba(0,255,102,0.05); padding: 15px; border: 1px solid #00ff66; border-radius: 6px; margin-bottom: 20px;">
        <span style="font-size: 3rem;">🏴‍☠️</span>
        <div>
            <h1 style="margin: 0; font-size: 1.8rem; color: #00ff66;">PIRATE_INTEL // $ OSINT_CORE</h1>
            <p style="margin: 0; color: #00ff66; font-family: 'Courier New'; opacity: 0.8;">[SYSTEM STATUS: ONLINE] - [MODE: CYBER_PIRATE_RECON]</p>
        </div>
    </div>
""", unsafe_allow_html=True)

# الشريط الجانبي
st.sidebar.title("⚙️ CONFIG // الإعدادات")
serper_api_key = st.sidebar.text_input("Serper API Key (اختياري):", type="password")

st.sidebar.markdown("---")
st.sidebar.title("⚡ EXEC_LOGS // السجل")
if st.sidebar.button("مسح السجل بالكامل"):
    conn = sqlite3.connect('pirate_osint.db')
    conn.execute('DELETE FROM searches')
    conn.commit()
    conn.close()
    st.sidebar.success("تم مسح السجل!")

conn = sqlite3.connect('pirate_osint.db')
cursor = conn.cursor()
cursor.execute('SELECT query_type, query_value, timestamp FROM searches ORDER BY id DESC LIMIT 10')
history = cursor.fetchall()
conn.close()

for item in history:
    st.sidebar.markdown(f"""
    <div class="metric-box">
        <small style="color:#00ff66">[{item[0]}]</small> <b>{item[1]}</b><br>
        <small style="color:#00ff66; opacity:0.6;">⏱️ {item[2]}</small>
    </div>
    """, unsafe_allow_html=True)

# التبويبات الأربعة
tab1, tab2, tab3, tab4 = st.tabs([
    "🌐 1. LIVE_WEB_SEARCH", 
    "👤 2. SHERLOCK_SCAN", 
    "📧 3. HUNTER_EMAILS",
    "📍 4. GEO_PHONE_MAP"
])

with tab1:
    st.subheader("🌐 وحدة البحث الحي الشامل")
    query_input = st.text_input("أدخل اسم الهدف أو العبارة للبحث:")
    if st.button("تنفيذ البحث الحقيقي"):
        if query_input:
            with st.spinner("جاري الاختراق والاستعلام الحي..."):
                search_res = live_web_search(query_input, serper_api_key)
                save_to_history("Live Search", query_input, search_res)
                if "error" in search_res:
                    st.warning(search_res["error"])
                else:
                    st.success("تم جلب النتائج بنجاح!")
                    if "organic" in search_res:
                        for item in search_res["organic"]:
                            st.markdown(f"### [{item.get('title')}]({item.get('link')})")
                            st.write(item.get('snippet'))
                            st.markdown("---")
                    else:
                        st.json(search_res)
        else:
            st.warning("أدخل قيمة للبحث.")

with tab2:
    st.subheader("👤 فحص المنصات الاجتماعية")
    username_input = st.text_input("أدخل اسم المستخدم (Username):")
    if st.button("بدء فحص الحسابات"):
        if username_input:
            with st.spinner("جاري فحص الخوادم والمنصات..."):
                sherlock_res = sherlock_username_scan(username_input)
                save_to_history("Sherlock", username_input, sherlock_res)
                st.success("تم الفحص!")
                cols = st.columns(2)
                idx = 0
                for plat, info in sherlock_res.items():
                    with cols[idx % 2]:
                        if "FOUND" in info["status"]:
                            st.markdown(f"🟢 **{plat}**: [رابط الحساب]({info['url']})")
                        else:
                            st.markdown(f"🔴 **{plat}**: غير موجود")
                    idx += 1
        else:
            st.warning("أدخل اسم المستخدم.")

with tab3:
    st.subheader("📧 استخراج وتوليد الإيميلات")
    col_f, col_l = st.columns(2)
    with col_f:
        f_name = st.text_input("الاسم الأول:")
    with col_l:
        l_name = st.text_input("النسب:")
    domain_input = st.text_input("النطاق (Domain):", value="gmail.com")
    if st.button("توليد الإيميلات الذكية"):
        if f_name and l_name:
            with st.spinner("جاري تحليل الأنماط..."):
                hunter_res = hunter_email_intel(f_name, l_name, domain_input)
                save_to_history("Hunter", f"{f_name} {l_name}", hunter_res)
                st.json(hunter_res)
        else:
            st.error("أدخل الاسم والنسب.")

with tab4:
    st.subheader("📍 تحديد موقع رقم الهاتف")
    phone_input = st.text_input("أدخل الرقم مع رمز الدولة (+212...):")
    if st.button("تحليل الرقم وعرض الخريطة"):
        if phone_input:
            with st.spinner("جاري الاستعلام الجغرافي..."):
                details, lat, lon = check_phone_with_location(phone_input)
                if "error" in details:
                    st.error(details["error"])
                else:
                    save_to_history("Geo-Phone", phone_input, details)
                    c1, c2 = st.columns([1, 1.2])
                    with c1:
                        st.success("التقرير جاهز!")
                        st.json(details)
                    with c2:
                        st.subheader("🗺️ الخريطة السيبرانية")
                        if lat and lon:
                            m = folium.Map(location=[lat, lon], zoom_start=6, tiles="CartoDB dark_matter")
                            folium.Marker([lat, lon], popup=f"TARGET: {phone_input}", icon=folium.Icon(color="green", icon="terminal", prefix="fa")).add_to(m)
                            st_folium(m, width=500, height=350)
                        else:
                            st.warning("تعذر تحديد الإحداثيات.")
        else:
            st.warning("أدخل رقم الهاتف.")
