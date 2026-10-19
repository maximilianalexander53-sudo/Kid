import streamlit as st
import sqlite3
import requests
import json
import datetime
import re
import phonenumbers
from phonenumbers import carrier, geocoder, timezone
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim

# ----------------- 1. إعدادات الصفحة والتصميم -----------------
st.set_page_config(
    page_title="Ultimate OSINT & Intelligence Platform",
    page_icon="🕵️‍♂️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# تصميم مظلم احترافي (Terminal / OSINT Style)
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: #ffffff; }
    .stTextInput > div > div > input { background-color: #161b22; color: #58a6ff; border: 1px solid #30363d; }
    .stButton > button { background-color: #238636; color: white; font-weight: bold; border-radius: 6px; width: 100%; border: none; }
    .stButton > button:hover { background-color: #2ea043; }
    .css-1r6slb0, .css-12w0qpk { background-color: #161b22; }
    </style>
""", unsafe_allow_html=True)

# ----------------- 2. إدارة قاعدة البيانات (Database) -----------------
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

# ----------------- 3. الوظائف البرمجية المتقدمة -----------------

# (أ) تحديد موقع وبيانات رقم الهاتف
def check_phone_with_location(phone_number):
    try:
        parsed_number = phonenumbers.parse(phone_number)
        if not phonenumbers.is_valid_number(parsed_number):
            return {"error": "رقم الهاتف غير صالح. تأكد من إدخال فتح الخط الدولي (مثال: +212600000000)"}, None, None
        
        country_ar = geocoder.description_for_number(parsed_number, "ar")
        country_en = geocoder.description_for_number(parsed_number, "en")
        operator = carrier.name_for_number(parsed_number, "ar")
        tz = timezone.time_zones_for_number(parsed_number)
        
        # تحويل اسم الدولة لإحداثيات
        geolocator = Nominatim(user_agent="osint_ultimate_platform")
        location = geolocator.geocode(country_en)
        
        lat, lon = None, None
        if location:
            lat, lon = location.latitude, location.longitude
        
        details = {
            "الصلاحية": "صالح ✅",
            "الدولة / المنطقة": country_ar if country_ar else "غير معروف",
            "المشغل / الشركة": operator if operator else "غير معروف",
            "المنطقة الزمنية": list(tz) if tz else [],
            "خط العرض (Lat)": lat,
            "خط الطول (Lon)": lon
        }
        return details, lat, lon
    except Exception as e:
        return {"error": str(e)}, None, None

# (ب) فحص اسم المستخدم فـ مواقع التواصل
def check_username(username):
    platforms = {
        "GitHub": f"https://github.com/{username}",
        "Twitter/X": f"https://twitter.com/{username}",
        "Instagram": f"https://www.instagram.com/{username}/",
        "TikTok": f"https://www.tiktok.com/@{username}",
        "Pinterest": f"https://www.pinterest.com/{username}/",
        "Reddit": f"https://www.reddit.com/user/{username}"
    }
    results = {}
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    for platform, url in platforms.items():
        try:
            res = requests.get(url, headers=headers, timeout=4)
            if res.status_code == 200:
                results[platform] = {"status": "موجود ✅", "url": url}
            else:
                results[platform] = {"status": "غير موجود ❌", "url": url}
        except:
            results[platform] = {"status": "خطأ فالاتصال ⚠️", "url": url}
    return results

# (ج) البحث المعمق بالاسم والموقع
def deep_person_search(name, location):
    # بناء استعلامات بحث متقدمة (Google Dorks)
    dorks = [
        f'"{name}" "{location}" ("+212" OR "06" OR "07" OR "05")',
        f'"{name}" "{location}" filetype:pdf OR filetype:docx',
        f'"{name}" site:facebook.com OR site:linkedin.com OR site:instagram.com'
    ]
    return {
        "الاسم الاستعلامي": name,
        "الموقع الميندي": location,
        "استعلام الأرقام المفتوحة": dorks[0],
        "استعلام الملفات العامة": dorks[1],
        "استعلام السجلات الاجتماعية": dorks[2],
        "توجيه": "يمكنك نسخ أي من استعلامات Dork المتقدمة أعلاه واستخدامها مباشرة في محرك البحث للوصول للسجلات المتاحة علنياً."
    }

# ----------------- 4. الواجهة الرئيسية والتفاعلية -----------------

st.title("🛡️ Ultimate OSINT & Intelligence Platform")
st.markdown("منصة شاملة لجمع وتحليل المعطيات المفتوحة، تحديد المواقع الجغرافية، وفحص الحسابات.")

# القائمة الجانبية (Sidebar)
st.sidebar.title("🗂️ سجل العمليات")
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
    st.sidebar.text(f"[{item[0]}] {item[1]}\n⏱️ {item[2]}")

# التبويبات الرئيسية (Tabs)
tab1, tab2, tab3 = st.tabs([
    "📍 تحديد موقع الرقم (Geo-Phone)", 
    "🔎 البحث المعمق بالاسم والموقع", 
    "👤 فحص الحسابات (Username)"
])

# ----- التبويب الأول: الرقم والخريطة -----
with tab1:
    st.subheader("📱 تحليل رقم الهاتف وتحديد موقعه الجغرافي")
    phone_input = st.text_input("أدخل الرقم مع رمز الدولة (مثال: +212600000000 أو +33600000000):")
    
    if st.button("بدء تحليل الرقم والتحديد الميداني"):
        if phone_input:
            with st.spinner("جاري الاتصال بالأقمار الاصطناعية وقواعد بيانات التغطية..."):
                details, lat, lon = check_phone_with_location(phone_input)
                
                if "error" in details:
                    st.error(details["error"])
                else:
                    save_to_history("Phone Geo", phone_input, details)
                    
                    c1, c2 = st.columns([1, 1.2])
                    with c1:
                        st.success("تم تحليل بيانات الخط بنجاح!")
                        st.json(details)
                        st.download_button(
                            label="📥 تحميل التقرير (JSON)",
                            data=json.dumps(details, indent=4, ensure_ascii=False),
                            file_name=f"report_phone_{phone_input}.json",
                            mime="application/json"
                        )
                    with c2:
                        st.subheader("🗺️ خريطة الموقع الجغرافي")
                        if lat and lon:
                            m = folium.Map(location=[lat, lon], zoom_start=6, tiles="CartoDB dark_matter")
                            folium.Marker(
                                [lat, lon],
                                popup=f"الرقم: {phone_input}",
                                tooltip=f"المنطقة: {details.get('الدولة / المنطقة')}",
                                icon=folium.Icon(color="green", icon="phone", prefix="fa")
                            ).add_to(m)
                            st_folium(m, width=500, height=350)
                        else:
                            st.warning("تعذر تحديد الإحداثيات على الخريطة.")
        else:
            st.warning("يرجى إدخال الرقم.")

# ----- التبويب الثاني: البحث المعمق بالاسم والموقع -----
with tab2:
    st.subheader("🕵️‍♂️ البحث المعمق عن شخص بالاسم والموقع الجغرافي")
    col_a, col_b = st.columns(2)
    with col_a:
        p_name = st.text_input("اسم الشخص الكامل (مثال: أسامة العلمي):")
    with col_b:
        p_loc = st.text_input("الموقع أو المدينة (مثال: أكادير / أولاد تايمة):")
        
    if st.button("توليد استعلامات البحث المعمق"):
        if p_name and p_loc:
            with st.spinner("جاري صياغة خوارزميات البحث المتقدم..."):
                res_deep = deep_person_search(p_name, p_loc)
                save_to_history("Deep Search", f"{p_name} ({p_loc})", res_deep)
                
                st.success("تم إنشاء روابط وتراكيب البحث المتقدمة بنجاح!")
                st.json(res_deep)
                
                st.info("💡 **تلميح:** يمكنك نسخ الاستعلامات أعلاه ووضعها فـ Google للحصول على أي أرقام أو مستندات مفتوحة للعموم.")
        else:
            st.error("المرجو إدخال الاسم والموقع معاً.")

# ----- التبويب الثالث: فحص الحسابات -----
with tab3:
    st.subheader("👤 فحص اسم المستخدم عبر الشبكات الاجتماعية")
    u_input = st.text_input("أدخل اسم المستخدم (Username):")
    
    if st.button("فحص المنصات العالمية"):
        if u_input:
            with st.spinner("جاري فحص الخوادم والمنصات..."):
                u_res = check_username(u_input)
                save_to_history("Username", u_input, u_res)
                
                st.success("تم الفحص بنجاح!")
                cols = st.columns(2)
                idx = 0
                for platform, val in u_res.items():
                    with cols[idx % 2]:
                        if val["status"] == "موجود ✅":
                            st.markdown(f"🟢 **{platform}**: [زيارة الحساب]({val['url']})")
                        else:
                            st.markdown(f"🔴 **{platform}**: غير موجود")
                    idx += 1
        else:
            st.warning("يرجى إدخال اسم المستخدم.")
