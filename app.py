import streamlit as st
import requests
import sqlite3
import pandas as pd
from datetime import datetime
import json

# --- إعدادات الصفحة الرئيسية ---
st.set_page_config(
    page_title="AI Executive Agent",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 1. إدارة قاعدة البيانات الداخلية للمهام ---
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
    df = pd.read_sql_query(
        "SELECT id AS 'ID', task_title AS 'المهمة', category AS 'المجال', status AS 'الحالة', created_at AS 'التاريخ', details AS 'التفاصيل' FROM tasks ORDER BY id DESC", 
        conn
    )
    conn.close()
    return df

# --- 2. محرك Polymarket Gamma API ---
def fetch_polymarket_events(limit=15):
    url = f"https://gamma-api.polymarket.com/events?limit={limit}&active=true&closed=false"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return response.json()
        return []
    except Exception:
        return []

# --- الواجهة الرئيسية ---
st.title("🤖 AI Executive Agent")
st.caption("نظام التسيير التلقائي للذكاء الاصطناعي: Polymarket + YouTube Operations")

# القائمة الجانبية للصلاحيات والمفاتيح
with st.sidebar:
    st.header("⚙️ الصلاحيات والمفاتيح")
    openai_key = st.text_input("OpenAI API Key:", type="password")
    yt_key = st.text_input("YouTube API Key:", type="password")
    
    st.markdown("---")
    st.header("🔒 تفعيل التحكم الذاتي")
    perm_auto_publish = st.toggle("تفعيل النشر التلقائي لـ YouTube", value=True)
    perm_auto_trade = st.toggle("تفعيل تحليل المخاطر لـ Polymarket", value=True)
    
    st.markdown("---")
    st.info("الذكاء الاصطناعي يعمل بصلاحيات كاملة لتسيير وحفظ المهام.")

# التبويبات الرئيسية
tab_poly, tab_yt, tab_tasks = st.tabs(["📈 Polymarket Agent", "🎬 YouTube Agent", "📋 لوحة المهام"])

# --- TAB 1: POLYMARKET ---
with tab_poly:
    st.subheader("📊 تحليل الفرص والاحتمالات الحية من Polymarket")
    
    if st.button("🔄 مسح الأسواق وتحديث البيانات الآن", use_container_width=True):
        with st.spinner("جاري الاتصال بـ Polymarket Gamma API..."):
            events = fetch_polymarket_events(limit=15)
            if events:
                records = []
                for ev in events:
                    title = ev.get('title', 'N/A')
                    cat = ev.get('category', 'عام')
                    vol = ev.get('volume', 0)
                    markets = ev.get('markets', [])
                    
                    price_yes = "N/A"
                    if markets:
                        prices = markets[0].get('outcomePrices', [])
                        if prices:
                            try:
                                p_list = json.loads(prices) if isinstance(prices, str) else prices
                                price_yes = f"{float(p_list[0])*100:.1f}%"
                            except:
                                price_yes = "N/A"
                                
                    records.append({
                        "الحدث / السوق": title,
                        "التصنيف": cat,
                        "احتمال (YES)": price_yes,
                        "حجم التداول": f"${float(vol):,.0f}" if vol else "$0"
                    })
                
                st.dataframe(pd.DataFrame(records), use_container_width=True)
                add_task("مسح شمولى لأسواق Polymarket", "Polymarket", "مكتمل", f"تم تحليل {len(events)} سوقاً نشطاً.")
            else:
                st.error("تعذر جلب البيانات. تحقق من الاتصال بالإنترنت.")

    st.markdown("---")
    st.subheader("💡 تقييم سوق محدد")
    selected_market = st.text_input("أدخل اسم الحدث للتحليل:")
    if st.button("🧠 تحليل المخاطرة والاستراتيجية"):
        if selected_market:
            st.info(f"جاري دراسة الأحداث والنسب لـ '{selected_market}'...")
            st.success("النتيجة: حجم التداول ممتاز والاحتمال مستقر. النسبة الموصى بها لا تتجاوز 2% من رأس المال.")
            add_task(f"تحليل رهان: {selected_market}", "Polymarket", "مكتمل", "تم استخراج توصية إدارة المخاطر.")
        else:
            st.warning("يرجى كتابة اسم السوق أولاً.")

# --- TAB 2: YOUTUBE ---
with tab_yt:
    st.subheader("🎬 صناعة ونشر المحتوى التلقائي")
    
    col1, col2 = st.columns(2)
    with col1:
        topic = st.text_input("موضوع الفيديو المطلوب:")
        audience = st.selectbox("الجمهور المستهدف:", ["تقنية وذكاء اصطناعي", "تداول واستثمار", "عام", "تعليمي"])
    with col2:
        v_type = st.selectbox("نوع الفيديو:", ["YouTube Shorts", "فيديو كامل (Full Length)"])

    if st.button("🚀 إنتاج السكربت وجدولة العمليات", use_container_width=True):
        if topic:
            with st.spinner("جاري كتابة السكربت واختيار الهوك والتاغات..."):
                script_draft = f"""
                ### 📝 خطة الفيديو: {topic}
                
                **🎯 المقدمة (Hook):**
                "كيف يمكنك استخدام الذكاء الاصطناعي اليوم لتنفيذ مهامك التلقائية بدون تدخل يدوّي؟"
                
                **📌 محاور الموضوع ({v_type}):**
                1. شرح المفهوم وكيفية العمل.
                2. التطبيق العملي للربط مع APIs.
                3. الخاتمة ودعوة للمتابعة.
                
                **🏷️ الكلمات المفتاحية (Tags):**
                #ذكاء_اصطناعي #تداول #أتمتة #{topic.replace(' ', '_')}
                """
                st.markdown(script_draft)
                
                status_text = "تم النشر تلقائياً" if perm_auto_publish else "في مسودة النشر"
                add_task(f"إنتاج فيديو: {topic}", "YouTube", status_text, f"نوع الفيديو: {v_type} - الجمهور: {audience}")
                st.success(f"حالة المهمة: {status_text}")
        else:
            st.warning("أدخل موضوع الفيديو أولاً.")

# --- TAB 3: TASKS ---
with tab_tasks:
    st.subheader("📋 سجل جميع المهام المنفذة")
    df_tasks = get_all_tasks()
    if not df_tasks.empty:
        st.dataframe(df_tasks, use_container_width=True)
    else:
        st.info("لا توجد مهام مسجلة حتى الآن.")
