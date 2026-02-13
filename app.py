import streamlit as st
import pandas as pd
import time

# --- 1. APP CONFIGURATION ---
st.set_page_config(
    page_title="Science Exam App",
    page_icon="🧬",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- 2. HIGH-CONTRAST CSS FOR VISIBILITY ---
css_code = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Hind+Siliguri:wght@400;600&display=swap');
    
    /* Background: Deep Blue for high contrast */
    .stApp {
        background: #0f172a !important;
    }

    /* Force all text inside the app to be readable */
    html, body, [class*="css"] {
        font-family: 'Hind Siliguri', sans-serif;
    }

    /* Hide Streamlit default UI */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* Sticky Timer: Bright Yellow/Red for visibility */
    .sticky-timer {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        background-color: #ffd60a;
        color: #d90429;
        text-align: center;
        padding: 12px;
        font-size: 22px;
        font-weight: bold;
        box-shadow: 0px 4px 10px rgba(0,0,0,0.3);
        z-index: 9999;
        border-bottom: 4px solid #ef233c;
    }

    /* Question Cards: White background with Dark Text */
    .question-card {
        background-color: #ffffff !important;
        padding: 25px;
        border-radius: 15px;
        box-shadow: 0 8px 16px rgba(0,0,0,0.2);
        margin-bottom: 25px;
        border: 1px solid #e2e8f0;
    }

    /* Force Text Color inside cards to be Dark Blue */
    .question-card h1, .question-card h2, .question-card h3, .question-card p, .question-card b {
        color: #1e293b !important;
    }

    /* Question Titles */
    .stMarkdown p {
        color: #ffffff; /* Questions outside cards are white */
        font-size: 18px;
    }
    
    .question-card .stMarkdown p {
        color: #1e293b !important; /* Questions inside cards are dark */
    }

    /* Radio Options: Light Gray background with Dark Text */
    .stRadio label {
        color: #1e293b !important;
        font-weight: 600 !important;
    }
    div[role='radiogroup'] {
        background: #f1f5f9;
        padding: 10px;
        border-radius: 10px;
    }

    /* Fixed Footer - Made by Imran */
    .footer {
        position: fixed;
        left: 0;
        bottom: 0;
        width: 100%;
        background: #1e293b;
        color: #38bdf8;
        text-align: center;
        padding: 15px;
        font-size: 16px;
        font-weight: bold;
        border-top: 4px solid #38bdf8;
        z-index: 9999;
    }

    /* Main Headings */
    h1 { color: #38bdf8 !important; text-align: center; }
</style>
<div class="footer">🚀 Smart Exam System | Made by Imran</div>
"""

st.markdown(css_code, unsafe_allow_html=True)

# --- 3. SESSION STATE ---
if 'exam_started' not in st.session_state: st.session_state.exam_started = False
if 'submitted' not in st.session_state: st.session_state.submitted = False
if 'start_time' not in st.session_state: st.session_state.start_time = None
if 'df' not in st.session_state: st.session_state.df = None

# --- 4. DATA LOADING ---
def load_data(file_obj=None):
    try:
        if file_obj:
            df = pd.read_csv(file_obj)
        else:
            df = pd.read_csv("questions.csv")
        df.columns = [c.strip().title() for c in df.columns]
        required = ["Question", "Option A", "Option B", "Option C", "Option D", "Correct Answer"]
        if all(col in df.columns for col in required):
            return df.sample(frac=1).reset_index(drop=True)
        return None
    except:
        return None

# --- 5. MAIN LOGIC ---

if st.session_state.df is None:
    df_local = load_data()
    if df_local is not None:
        st.session_state.df = df_local
    else:
        st.markdown("<h1>🔬 Science Exam Login</h1>", unsafe_allow_html=True)
        uploaded_file = st.file_uploader("📂 Upload 'questions.csv' to begin", type="csv")
        if uploaded_file:
            st.session_state.df = load_data(uploaded_file)
            st.rerun()

if st.session_state.df is not None:
    df = st.session_state.df
    total_qs = len(df)
    time_limit_secs = total_qs * 60

    if not st.session_state.exam_started and not st.session_state.submitted:
        st.markdown("<h1>🧬 Science Model Test</h1>", unsafe_allow_html=True)
        st.markdown(f"""
        <div class="question-card">
            <h3>📋 Exam Instructions</h3>
            <p>• Total Questions: <b>{total_qs}</b></p>
            <p>• Time Limit: <b>{total_qs} Minutes</b></p>
            <p>• Smart Feature: 1 min per question.</p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("🚀 Start Exam"):
            st.session_state.exam_started = True
            st.session_state.start_time = time.time()
            st.rerun()

    elif st.session_state.exam_started and not st.session_state.submitted:
        elapsed = time.time() - st.session_state.start_time
        remaining = time_limit_secs - elapsed
        
        if remaining <= 0:
            st.session_state.submitted = True
            st.session_state.exam_started = False
            st.rerun()
        
        mins, secs = divmod(int(remaining), 60)
        st.markdown(f'<div class="sticky-timer">⏳ Time Left: {mins:02d}:{secs:02d}</div><div style="margin-top:80px;"></div>', unsafe_allow_html=True)
        
        with st.form("exam_form"):
            user_answers = {}
            for i, row in df.iterrows():
                st.markdown('<div class="question-card">', unsafe_allow_html=True)
                st.markdown(f"<h3 style='color:#1e293b;'>Q{i+1}. {row['Question']}</h3>", unsafe_allow_html=True)
                opts = [str(row['Option A']), str(row['Option B']), str(row['Option C']), str(row['Option D'])]
                user_answers[i] = st.radio("Select Answer:", opts, index=None, key=f"q{i}", label_visibility="collapsed")
                st.markdown('</div>', unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            if st.form_submit_button("✅ Final Submission"):
                st.session_state.user_results = user_answers
                st.session_state.submitted = True
                st.session_state.exam_started = False
                st.rerun()

    elif st.session_state.submitted:
        st.markdown("<h1>📊 Result Dashboard</h1>", unsafe_allow_html=True)
        score = sum(1 for i, r in df.iterrows() if str(st.session_state.user_results.get(i)) == str(r['Correct Answer']))
        perc = (score / total_qs) * 100
        
        st.markdown(f"""
        <div class="question-card" style="text-align:center; border-top: 6px solid #38bdf8;">
            <h2 style="color:#1e293b;">Your Result</h2>
            <h1 style="font-size: 60px; color: #1e293b;">{score} / {total_qs}</h1>
            <p style="font-size: 20px;">Success Rate: <b>{perc:.1f}%</b></p>
        </div>
        """, unsafe_allow_html=True)

        with st.expander("🔍 Detailed Answer Key"):
            for i, row in df.iterrows():
                u = str(st.session_state.user_results.get(i))
                c = str(row['Correct Answer'])
                st.markdown(f"**Q{i+1}: {row['Question']}**")
                if u == c:
                    st.success(f"✅ Your Answer: {u}")
                else:
                    st.error(f"❌ Your Answer: {u if u!='None' else 'Skipped'}")
                    st.info(f"👉 Correct Answer: {c}")
                st.divider()

        if st.button("🔄 Take New Exam"):
            st.session_state.exam_started = False
            st.session_state.submitted = False
            st.session_state.df = None
            st.rerun()
