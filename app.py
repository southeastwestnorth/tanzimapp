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

# --- 2. ADVANCED CSS FOR MOBILE UI ---
# We use a single variable for CSS to avoid syntax confusion
css_code = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Hind+Siliguri:wght@400;600&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Hind Siliguri', sans-serif;
    }

    .stApp {
        background: linear-gradient(to bottom right, #eef2f3, #8e9eab);
    }

    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    .sticky-timer {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        background-color: #ffffff;
        color: #d90429;
        text-align: center;
        padding: 10px;
        font-size: 20px;
        font-weight: bold;
        box-shadow: 0px 4px 6px rgba(0,0,0,0.1);
        z-index: 9999;
        border-bottom: 3px solid #ef233c;
    }

    .question-card {
        background-color: white;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        margin-bottom: 20px;
    }

    .stRadio > label {
        font-size: 18px;
        font-weight: 600;
        color: #2b2d42;
    }

    .footer {
        position: fixed;
        left: 0;
        bottom: 0;
        width: 100%;
        background: #212529;
        color: white;
        text-align: center;
        padding: 12px;
        font-size: 14px;
        font-weight: bold;
        border-top: 3px solid #4cc9f0;
        z-index: 9999;
    }
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
        uploaded_file = st.file_uploader("📂 Upload 'questions.csv' to begin", type="csv")
        if uploaded_file:
            st.session_state.df = load_data(uploaded_file)
            st.rerun()

if st.session_state.df is not None:
    df = st.session_state.df
    total_qs = len(df)
    time_limit_secs = total_qs * 60

    if not st.session_state.exam_started and not st.session_state.submitted:
        st.markdown("<h1 style='text-align: center;'>🧬 Science MCQ Hub</h1>", unsafe_allow_html=True)
        st.markdown(f"""
        <div class="question-card" style="text-align:center;">
            <h3>📋 Exam Details</h3>
            <p>Questions: {total_qs} | Time: {total_qs} Min</p>
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
        st.markdown(f'<div class="sticky-timer">⏳ {mins:02d}:{secs:02d}</div><div style="margin-top:70px;"></div>', unsafe_allow_html=True)
        st.progress(min(1.0, elapsed / time_limit_secs))

        with st.form("exam_form"):
            user_answers = {}
            for i, row in df.iterrows():
                st.markdown('<div class="question-card">', unsafe_allow_html=True)
                st.markdown(f"**Q{i+1}. {row['Question']}**")
                opts = [str(row['Option A']), str(row['Option B']), str(row['Option C']), str(row['Option D'])]
                user_answers[i] = st.radio("Ans:", opts, index=None, key=f"q{i}", label_visibility="collapsed")
                st.markdown('</div>', unsafe_allow_html=True)
            
            if st.form_submit_button("✅ Submit"):
                st.session_state.user_results = user_answers
                st.session_state.submitted = True
                st.session_state.exam_started = False
                st.rerun()

    elif st.session_state.submitted:
        st.header("📊 Result Dashboard")
        score = sum(1 for i, r in df.iterrows() if str(st.session_state.user_results.get(i)) == str(r['Correct Answer']))
        perc = (score / total_qs) * 100
        
        st.markdown(f"""
        <div class="question-card" style="text-align:center; border-top: 5px solid #4361ee;">
            <h1>{score} / {total_qs}</h1>
            <p>Percentage: {perc:.1f}%</p>
        </div>
        """, unsafe_allow_html=True)

        with st.expander("🔍 View Answer Key"):
            for i, row in df.iterrows():
                u = str(st.session_state.user_results.get(i))
                c = str(row['Correct Answer'])
                st.write(f"**Q{i+1}: {row['Question']}**")
                st.write(f"{'✅' if u==c else '❌'} Your: {u} | Correct: {c}")

        if st.button("🔄 Restart"):
            st.session_state.exam_started = False
            st.session_state.submitted = False
            st.session_state.df = None
            st.rerun()
