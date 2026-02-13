import streamlit as st
import pandas as pd
import time
from datetime import datetime

# --- 1. PRO APP CONFIGURATION ---
st.set_page_config(
    page_title="Science Pro Exam",
    page_icon="🎓",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- 2. ADVANCED CSS (Mobile Optimized + Visibility Fix) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Hind+Siliguri:wght@400;600&display=swap');
    
    /* Base Theme */
    .stApp { background-color: #0b0e14 !important; font-family: 'Hind Siliguri', sans-serif; }
    [data-testid="stHeader"], [data-testid="stToolbar"] { display: none; }

    /* Sticky Header & Timer */
    .sticky-header {
        position: fixed; top: 0; left: 0; width: 100%;
        background: #161b22; border-bottom: 3px solid #00d4ff;
        padding: 10px; z-index: 9999; text-align: center;
        box-shadow: 0 4px 12px rgba(0,0,0,0.5);
    }
    .timer-text { color: #ffd60a; font-size: 26px; font-weight: bold; }
    .progress-text { color: #ffffff; font-size: 14px; margin-top: 5px; }

    /* Question Cards */
    .q-card {
        background: #1c2128 !important; border-radius: 12px;
        padding: 20px; margin: 15px 0; border: 1px solid #30363d;
        box-shadow: 0 4px 6px rgba(0,0,0,0.2);
    }
    .q-text { color: #00d4ff !important; font-size: 20px; font-weight: 600; margin-bottom: 15px; }

    /* High Visibility Radio Buttons */
    .stRadio label { color: #e6edf3 !important; font-size: 18px !important; cursor: pointer; }
    div[role='radiogroup'] { background: #2d333b; border-radius: 8px; padding: 10px; border: 1px solid #444c56; }

    /* Performance Dashboard */
    .result-card {
        background: #1c2128; border-radius: 15px; padding: 30px;
        text-align: center; border: 2px solid #00d4ff; margin-bottom: 20px;
    }

    /* Fixed Footer */
    .footer {
        position: fixed; left: 0; bottom: 0; width: 100%;
        background: #161b22; color: #58a6ff; text-align: center;
        padding: 10px; font-size: 14px; font-weight: bold;
        border-top: 2px solid #30363d; z-index: 9999;
    }
</style>
<div class="footer">SSC Science Excellence Portal | Made by Imran</div>
""", unsafe_allow_html=True)

# --- 3. SESSION STATE MANAGEMENT ---
if 'exam_active' not in st.session_state: st.session_state.exam_active = False
if 'submitted' not in st.session_state: st.session_state.submitted = False
if 'start_time' not in st.session_state: st.session_state.start_time = None
if 'user_answers' not in st.session_state: st.session_state.user_answers = {}
if 'df' not in st.session_state: st.session_state.df = None

# --- 4. CORE FUNCTIONS ---
def load_data():
    try:
        # Tries to load existing file, otherwise allows upload
        df = pd.read_csv("questions.csv")
        df.columns = [c.strip().title() for c in df.columns]
        return df # No randomization as requested
    except:
        return None

def force_submit():
    st.session_state.submitted = True
    st.session_state.exam_active = False

# --- 5. APP LOGIC ---

# Data Loading Interface
if st.session_state.df is None:
    df = load_data()
    if df is not None:
        st.session_state.df = df
    else:
        st.markdown("<h1 style='text-align:center; color:#58a6ff;'>🚀 Exam Portal Login</h1>", unsafe_allow_html=True)
        up = st.file_uploader("Upload CSV to initialize", type="csv")
        if up: 
            st.session_state.df = pd.read_csv(up)
            st.rerun()
        st.stop()

df = st.session_state.df
total_questions = len(df)
time_limit = total_questions * 60 # 1 minute per question

# --- PHASE 1: WELCOME SCREEN ---
if not st.session_state.exam_active and not st.session_state.submitted:
    st.markdown(f"""
    <div style='text-align:center;'>
        <h1 style='color:#00d4ff;'>🧬 Science Final Prep</h1>
        <div class='q-card'>
            <p><b>Subject:</b> General Science</p>
            <p><b>Total Marks:</b> {total_questions}</p>
            <p><b>Time Allowed:</b> {total_questions} Minutes</p>
            <p><b>Instructions:</b> Once you start, the timer cannot be paused. 
            If time expires, your answers will be auto-submitted.</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("🚀 CLICK TO START EXAM", use_container_width=True):
        st.session_state.exam_active = True
        st.session_state.start_time = time.time()
        st.session_state.user_answers = {}
        st.rerun()

# --- PHASE 2: ACTIVE EXAM (TIMER FIXED) ---
elif st.session_state.exam_active and not st.session_state.submitted:
    now = time.time()
    elapsed = now - st.session_state.start_time
    remaining = time_limit - elapsed

    # DEBUG: Force Redirection if time ends
    if remaining <= 0:
        force_submit()
        st.rerun()

    # Sticky UI Header
    mins, secs = divmod(int(remaining), 60)
    answered_count = len([v for v in st.session_state.user_answers.values() if v is not None])
    
    st.markdown(f"""
    <div class="sticky-header">
        <div class="timer-text">⏳ {mins:02d}:{secs:02d}</div>
        <div class="progress-text">Progress: {answered_count} / {total_questions} Answered</div>
    </div>
    <div style="margin-top:100px;"></div>
    """, unsafe_allow_html=True)

    # Exam Body
    with st.form("exam_content"):
        for idx, row in df.iterrows():
            st.markdown(f"""<div class='q-card'><div class='q-text'>Q{idx+1}. {row['Question']}</div></div>""", unsafe_allow_html=True)
            opts = [str(row['Option A']), str(row['Option B']), str(row['Option C']), str(row['Option D'])]
            
            # Save answer to state on change
            st.session_state.user_answers[idx] = st.radio(
                f"Choose for Q{idx}", opts, index=None, key=f"rad_{idx}", label_visibility="collapsed"
            )
            st.write("---")
        
        if st.form_submit_button("✅ FINISH & SUBMIT EXAM", use_container_width=True):
            force_submit()
            st.rerun()

    # SMART REFRESH: Keeps the timer moving without getting stuck
    if remaining > 0:
        time.sleep(1)
        st.rerun()

# --- PHASE 3: PROFESSIONAL RESULTS ---
elif st.session_state.submitted:
    st.markdown("<div style='margin-top:30px;'></div>", unsafe_allow_html=True)
    st.markdown("<h1 style='text-align:center; color:#00d4ff;'>📊 Result Summary</h1>", unsafe_allow_html=True)
    
    correct, wrong, skipped = 0, 0, 0
    review_html = ""

    for idx, row in df.iterrows():
        ans = str(st.session_state.user_answers.get(idx))
        truth = str(row['Correct Answer'])
        
        if ans == "None":
            skipped += 1
            status = "⚪ SKIPPED"
        elif ans == truth:
            correct += 1
            status = "✅ CORRECT"
        else:
            wrong += 1
            status = "❌ WRONG"
        
        review_html += f"**Q{idx+1}: {row['Question']}**  \n"
        review_html += f"Status: {status}  \n"
        review_html += f"Your Answer: `{ans}` | Correct: `{truth}`  \n\n---  \n"

    # Grade Calculation
    perc = (correct / total_questions) * 100
    if perc >= 80: grade, g_color = "A+ (Excellent)", "#00ff88"
    elif perc >= 70: grade, g_color = "A (Very Good)", "#aaccff"
    elif perc >= 50: grade, g_color = "B (Pass)", "#ffd60a"
    else: grade, g_color = "F (Fail)", "#ff4b4b"

    st.markdown(f"""
    <div class='result-card'>
        <h1 style='color:{g_color}; font-size:60px;'>{correct} / {total_questions}</h1>
        <p style='font-size:24px;'>Grade: <b>{grade}</b></p>
        <div style='display:flex; justify-content: space-around; margin-top:20px;'>
            <div style='color:#00ff88;'>✅ Correct: {correct}</div>
            <div style='color:#ff4b4b;'>❌ Wrong: {wrong}</div>
            <div style='color:#888;'>⚪ Skipped: {skipped}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if perc >= 80: st.balloons()

    with st.expander("🔍 REVIEW FULL ANSWER KEY"):
        st.markdown(review_html)

    # Smart Feature: Download Report
    report = f"Student Exam Report\nDate: {datetime.now().strftime('%Y-%m-%d')}\nScore: {correct}/{total_questions}\nGrade: {grade}"
    st.download_button("📥 Download Result Card", report, file_name="result.txt")

    if st.button("🔄 RE-ATTEMPT EXAM", use_container_width=True):
        st.session_state.exam_active = False
        st.session_state.submitted = False
        st.session_state.user_answers = {}
        st.rerun()
