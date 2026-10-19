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

# ----------------- 1. إعدادات الواجهة الخارجية البرمجية (Cyber Matrix UI) -----------------
st.set_page_config(
    page_title="PIRATE_OSINT // DEEP RECON CORE",
    page_icon="🏴‍☠️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# تصميم خارجي برمجي بالكامل بأسلوب الهكرز واللون الأخضر (Matrix Green)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;700&display=swap');
    
    .stApp { 
        background-color: #020503; 
        color: #00ff66; 
        font-family: 'Fira Code', 'Courier New', monospace; 
    }
    
    /* خلفية برمجية متحركة شاشة الـ Matrix */
    body {
        background-image: radial-gradient(rgba(0, 255, 102, 0.05) 1px, transparent 0);
        background-size: 24px 24px;
    }
    
    /* العناوين واللوغو البرمجي */
    h1, h2, h3 { 
        color: #00ff66 !important; 
        font-family: 'Fira Code', monospace !important; 
        font-weight: 700 !important; 
        text-shadow: 0 0 12px rgba(0, 255, 102, 0.6); 
    }
    
    /* مربعات الإدخال الشفافة بالستايل البرمجي */
    .stTextInput > div > div > input, .stTextArea > div > div > textarea {
        background-color: #040c06 !important;
        color: #00ff66 !important;
        border: 1px solid #00ff66 !important;
        border-radius: 4px !important;
        padding: 12px !important;
        font-family: 'Fira Code', monospace !important;
        box-shadow: inset 0 0 5px rgba(0, 255, 102, 0.2);
    }
    .stTextInput > div > div > input:focus {
        box-shadow: 0 0 15px rgba(0, 255, 102, 0.8) !important;
    }

    /* أزرار التنفيذ */
    .stButton > button {
        background: #00ff66 !important;
        color: #020503 !important;
        font-weight: bold !important;
        font-family: 'Fira Code', monospace !important;
        border-radius: 4px !important;
        padding: 0.7rem 1rem !important;
        border: 1px solid #00ff66 !important;
        box-shadow: 0 0 15px rgba(0, 255, 102, 0.4) !important;
        width: 100% !important;
        transition: all 0.3s ease;
    }
    .stButton > button:hover {
        background: #00cc52 !important;
        box-shadow: 0 0 25px rgba(0, 255, 102, 0.9) !important;
        cursor: pointer;
    }

    /* القائمة الجانبية */
    [data-testid="stSidebar"] { 
        background-color: #010402 !important; 
        border-right: 1px solid #00ff66 !important; 
    }
    
    .metric-box {
        background: rgba(4, 12, 6, 0.9);
        border: 1px solid #00ff66;
        border-left: 5px solid #00ff66;
        padding: 10px;
        border-radius: 4px;
        margin-bottom: 8px;
        box-shadow: 0 0 10px rgba(0, 255, 102, 0.1);
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

# ----------------- 3. الأدوات البرمجية المدمجة والبحث المعمق للأرقام -----------------

# (أ) أداة البحث المعمق الشامل لرقم الهاتف (Deep Phone OSINT)
def deep_phone_recon(phone_number):
    try:
        parsed = phonenumbers.parse(phone_number)
        if not phonenumbers.is_valid_number(parsed):
            return {"error": "INVALID_PHONE_FORMAT: أدخل الرقم مع المفتاح الدولي (مثال: +212600000000)"}
        
        national_num = str(parsed.national_number)
        country_code = str(parsed.country_code)
        raw_phone = phone_number.replace("+", "").replace(" ", "")
        local_zero = "0" + national_num if country_code == "212" else national_num
        
        # 1. استخراج مواقع التواصل الاجتماعية المفتوحة المربوطة بالرقم
        social_footprint = {
            "WhatsApp Direct": f"https://wa.me/{raw_phone}",
            "Telegram Direct": f"https://t.me/+{raw_phone}",
            "Truecaller Web": f"https://www.truecaller.com/search/ma/{local_zero}",
            "Facebook Phone Lookup": f"https://www.facebook.com/search/top/?q={raw_phone}",
            "Sync.me Lookup": f"https://sync.me/search/?number={raw_phone}"
        }
        
        # 2. توليد صيغ استعلام أمنية متقدمة (Google Dorks) للبحث عن أي سيت مسجل بيه الرقم
        dork_queries = {
            "فحص تسريبات المستندات والملفات": f'"{raw_phone}" OR "{local_zero}" filetype:pdf OR filetype:xlsx',
            "فحص الإعلانات والدلايل التجارية": f'"{local_zero}" site:avito.ma OR site:marocannonces.com',
            "فحص الحسابات الاجتماعية المفتوحة": f'"{raw_phone}" OR "{local_zero}" site:facebook.com OR site:instagram.com OR site:linkedin.com',
            "فحص قواعد البيانات المفتوحة": f'"{raw_phone}" OR "{local_zero}" "phone" OR "هاتف"'
        }
        
        # 3. جلب بيانات الدولة والمشغل
        country_ar = geocoder.description_for_number(parsed, "ar")
        operator = carrier.name_for_number(parsed, "ar")
        
        return {
            "STATUS": "SUCCESS ✅",
            "PHONE_RAW": phone_number,
            "LOCAL_FORMAT": local_zero,
            "COUNTRY": country_ar if country_ar else "N/A",
            "CARRIER": operator if operator else "N/A",
            "DIRECT_SOCIAL_LINKS": social_footprint,
            "ADVANCED_DORKS": dork_queries
        }
    except Exception as e:
        return {"error": str(e)}

# (ب) أداة البحث الحي في الويب (SerpAPI)
def live_web_search(query, api_key):
    if not api_key:
        return {"error": "المرجو إدخال مفتاح Serper/SerpAPI في القائمة الجانبية."}
    url = "https://google.serper.dev/search"
    payload = json.dumps({"q": query, "gl": "ma"})
    headers = {'X-API-KEY': api_key, 'Content-Type': 'application/json'}
    try:
        response = requests.request("POST", url, headers=headers, data=payload)
        return response.json()
    except Exception as e:
        return {"error": str(e)}

# (ج) أداة فحص المنصات بنظام Sherlock
def sherlock_username_scan(username):
    platforms = {
        "Instagram": f"https://www.instagram.com/{username}/",
        "Facebook": f"https://www.facebook.com/{username}",
        "Twitter/X": f"https://twitter.com/{username}",
        "GitHub": f"https://github.com/{username}",
        "TikTok": f"https://www.tiktok.com/@{username}",
        "Reddit": f"https://www.reddit.com/user/{username}",
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

# (د) أداة Hunter للإيميلات
def hunter_email_intel(first_name, last_name, domain="gmail.com"):
    f, l = first_name.lower().strip(), last_name.lower().strip()
    generated_emails = [
        f"{f}.{l}@{domain}", f"{f}{l}@{domain}", f"{f}_{l}@{domain}",
        f"{f[0]}{l}@{domain}", f"{f}{l[0]}@{domain}"
    ]
    return {email: "[PATTERN_MATCH] 🔍" for email in generated_emails}

# (هـ) التحديد الجغرافي للرقم
def check_phone_with_location(phone_number):
    try:
        parsed_number = phonenumbers.parse(phone_number)
        if not phonenumbers.is_valid_number(parsed_number):
            return {"error": "INVALID_NUMBER"}, None, None
        
        country_ar = geocoder.description_for_number(parsed_number, "ar")
        country_en = geocoder.description_for_number(parsed_number, "en")
        operator = carrier.name_for_number(parsed_number, "ar")
        
        geolocator = Nominatim(user_agent="pirate_osint_core")
        location = geolocator.geocode(country_en)
        lat, lon = (location.latitude, location.longitude) if location else (None, None)
        
        details = {
            "STATUS": "VALID ✅", "COUNTRY": country_ar, "CARRIER": operator, "LAT_LON": [lat, lon]
        }
        return details, lat, lon
    except Exception as e:
        return {"error": str(e)}, None, None

# ----------------- 4. الواجهة البرمجية المتقدمة (Header & Controls) -----------------

# الهيدر البرمجي الخارجي بعلم القراصنة وكود الأخضر
st.markdown("""
    <div style="border: 2px solid #00ff66; padding: 15px; border-radius: 6px; background: rgba(0, 255, 102, 0.03); margin-bottom: 20px;">
        <div style="display: flex; align-items: center; gap: 15px;">
            <span style="font-size: 3.5rem;">🏴‍☠️</span>
            <div>
                <h1 style="margin:0; font-size: 2rem;">PIRATE_INTEL // DEEP_RECON_V3</h1>
                <p style="margin:0; color:#00ff66; opacity: 0.8; font-size: 0.9rem;">
                    [SYSTEM STATUS: ONLINE] | [MODULES: PHONE_DEEP + SHERLOCK + HUNTER + SERP]
                </p>
            </div>
        </div>
    </div>
""", unsafe_allow_html=True)

# القائمة الجانبية
st.sidebar.title("⚙️ SYSTEM_CONFIG")
serper_api_key = st.sidebar.text_input("SERPER_API_KEY (اختياري):", type="password")

st.sidebar.markdown("---")
st.sidebar.title("⚡ EXEC_LOGS")
if st.sidebar.button("CLEAR_ALL_LOGS"):
    conn = sqlite3.connect('pirate_osint.db')
    conn.execute('DELETE FROM searches')
    conn.commit()
    conn.close()
    st.sidebar.success("LOGS_CLEARED!")

conn = sqlite3.connect('pirate_osint.db')
cursor = conn.cursor()
cursor.execute('SELECT query_type, query_value, timestamp FROM searches ORDER BY id DESC LIMIT 8')
history = cursor.fetchall()
conn.close()

for item in history:
    st.sidebar.markdown(f"""
    <div class="metric-box">
        <small style="color:#00ff66">[{item[0]}]</small> <b style="color:#fff;">{item[1]}</b><br>
        <small style="color:#00ff66; opacity:0.6;">⏱️ {item[2]}</small>
    </div>
    """, unsafe_allow_html=True)

# ----------------- 5. التبويبات المتقدمة للموقع -----------------
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📞 1. DEEP_PHONE_SEARCH (البحث المعمق للأرقام)", 
    "🌐 2. LIVE_WEB_SERP (البحث الحي)", 
    "👤 3. SHERLOCK_USERNAMES (فحص المنصات)", 
    "📧 4. HUNTER_EMAILS (استخراج الإيميلات)",
    "📍 5. GEO_MAPPER (الخريطة الجغرافية)"
])

# ----- التبويب 1: أداة البحث المعمق المتقدمة لرقم الهاتف -----
with tab1:
    st.subheader("📞 البحث الاستخباري المعمق عن رقم الهاتف (Deep Phone Recon)")
    st.markdown("أدخل رقم الهاتف لتتبع كافة السيتات، الشبكات الاجتماعية، والإعلانات المتاحة للعموم المربوطة بيه.")
    
    phone_target = st.text_input("أدخل الرقم المستهدف (مثال: +212600000000):")
    
    if st.button("EXECUTE_DEEP_PHONE_RECON"):
        if phone_target:
            with st.spinner("جاري مسح قواعد البيانات المفتوحة وشبكات التواصل..."):
                deep_res = deep_phone_recon(phone_target)
                
                if "error" in deep_res:
                    st.error(deep_res["error"])
                else:
                    save_to_history("Deep Phone", phone_target, deep_res)
                    st.success("DEEP_SCAN_COMPLETE!")
                    
                    c1, c2 = st.columns(2)
                    with c1:
                        st.markdown("### 🌐 الروابط والحسابات الاجتماعية المباشرة")
                        for platform_name, link_url in deep_res["DIRECT_SOCIAL_LINKS"].items():
                            st.markdown(f"- **{platform_name}**: [فتح الرابط المباشر 🔗]({link_url})")
                            
                    with c2:
                        st.markdown("### 🔍 استعلامات كشف الحسابات والسيتات المفتوحة (Google Dorks)")
                        st.json(deep_res["ADVANCED_DORKS"])
                        
                    st.download_button(
                        label="📥 DOWNLOAD_PHONE_INTEL_REPORT (JSON)",
                        data=json.dumps(deep_res, indent=4, ensure_ascii=False),
                        file_name=f"phone_recon_{phone_target}.json",
                        mime="application/json"
                    )
        else:
            st.warning("المرجو إدخال الرقم أولاً.")

# ----- التبويب 2: البحث الحي -----
with tab2:
    st.subheader("🌐 البحث الحي الفوري عبر محركات الويب")
    query_input = st.text_input("أدخل نص البحث:")
    if st.button("RUN_LIVE_SEARCH"):
        if query_input:
            with st.spinner("جاري جلب المعطيات الحية..."):
                search_res = live_web_search(query_input, serper_api_key)
                save_to_history("Live Search", query_input, search_res)
                if "error" in search_res:
                    st.warning(search_res["error"])
                else:
                    st.success("LIVE_RESULTS_FOUND!")
                    if "organic" in search_res:
                        for item in search_res["organic"]:
                            st.markdown(f"### [{item.get('title')}]({item.get('link')})")
                            st.write(item.get('snippet'))
                            st.markdown("---")
                    else:
                        st.json(search_res)
        else:
            st.warning("أدخل نصاً للبحث.")

# ----- التبويب 3: Sherlock -----
with tab3:
    st.subheader("👤 فحص أسماء المستخدمين عبر شبكات التواصل")
    username_input = st.text_input("أدخل اسم المستخدم (Username):")
    if st.button("EXECUTE_SHERLOCK_SCAN"):
        if username_input:
            with st.spinner("جاري فحص الحسابات..."):
                sherlock_res = sherlock_username_scan(username_input)
                save_to_history("Sherlock", username_input, sherlock_res)
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

# ----- التبويب 4: Hunter -----
with tab4:
    st.subheader("📧 توليد الإيميلات الذكية")
    col_f, col_l = st.columns(2)
    with col_f:
        f_name = st.text_input("FIRST_NAME:")
    with col_l:
        l_name = st.text_input("LAST_NAME:")
    domain_input = st.text_input("DOMAIN:", value="gmail.com")
    if st.button("RUN_HUNTER_INTEL"):
        if f_name and l_name:
            hunter_res = hunter_email_intel(f_name, l_name, domain_input)
            save_to_history("Hunter", f"{f_name} {l_name}", hunter_res)
            st.json(hunter_res)
        else:
            st.error("أدخل الاسم والنسب.")

# ----- التبويب 5: الخريطة الجغرافية -----
with tab5:
    st.subheader("📍 التحديد الجغرافي للرقم")
    phone_map_input = st.text_input("أدخل الرقم (+212...):")
    if st.button("RENDER_GEO_MAP"):
        if phone_map_input:
            details, lat, lon = check_phone_with_location(phone_map_input)
            if "error" in details:
                st.error(details["error"])
            else:
                save_to_history("Geo-Phone", phone_map_input, details)
                c1, c2 = st.columns([1, 1.2])
                with c1:
                    st.json(details)
                with c2:
                    if lat and lon:
                        m = folium.Map(location=[lat, lon], zoom_start=6, tiles="CartoDB dark_matter")
                        folium.Marker([lat, lon], popup=f"TARGET: {phone_map_input}", icon=folium.Icon(color="green", icon="terminal", prefix="fa")).add_to(m)
                        st_folium(m, width=500, height=350)
                    else:
                        st.warning("NO_LAT_LON")
        else:
            st.warning("أدخل رقم الهاتف.")
