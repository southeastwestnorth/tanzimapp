import streamlit as st
import pandas as pd
import time

# --- 1. APP CONFIGURATION ---
st.set_page_config(
    page_title="Science Exam Pro",
    page_icon="🧬",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- 2. DARK MODE CSS (Ensures 100% Visibility) ---
css_code = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Hind+Siliguri:wght@400;600&display=swap');
    
    /* 1. Global Background & Font */
    .stApp {
        background-color: #0e1117 !important;
        font-family: 'Hind Siliguri', sans-serif;
    }

    /* 2. Hide Streamlit Branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* 3. Sticky Timer: Neon Yellow/Red for Contrast */
    .sticky-timer {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        background-color: #ffd60a;
        color: #000000;
        text-align: center;
        padding: 12px;
        font-size: 22px;
        font-weight: bold;
        box-shadow: 0px 4px 15px rgba(0,0,0,0.5);
        z-index: 9999;
        border-bottom: 4px solid #ef233c;
    }

    /* 4. Question Cards: Darker Gray with Neon Border */
    .question-card {
        background-color: #1a1c23 !important;
        padding: 20px;
        border-radius: 12px;
        margin-bottom: 20px;
        border-left: 5px solid #00d4ff;
        box-shadow: 0 4px 10px rgba(0,0,0,0.3);
    }

    /* 5. FORCE TEXT VISIBILITY (The most important part) */
    /* Force Questions and Headings to be Pure White */
    h1, h2, h3, p, span, label {
        color: #ffffff !important;
    }

    /* Questions specifically inside cards */
    .question-card h3, .question-card p {
        color: #00d4ff !important; /* Neon Blue for the Question text */
        font-weight: bold;
    }

    /* 6. Radio Button (Answer) Visibility */
    /* This makes the options bright white on dark gray background */
    .stRadio label {
        color: #ffffff !important;
        font-size: 18px !important;
        padding: 8px !important;
    }
    
    /* Dark background for the option group */
    div[role='radiogroup'] {
        background: #252932;
        border-radius: 8px;
        padding: 5px;
    }

    /* 7. Action Buttons */
    .stButton > button {
        background-color: #00d4ff !important;
        color: #000000 !important;
        font-weight: bold !important;
        border-radius: 50px !important;
        height: 50px;
        width: 100%;
        border: none;
    }

    /* 8. Fixed Footer - Made by Imran */
    .footer {
        position: fixed;
        left: 0;
        bottom: 0;
        width: 100%;
        background: #1a1c23;
        color: #00d4ff;
        text-align: center;
        padding: 12px;
        font-size: 14px;
        font-weight: bold;
        border-top: 3px solid #00d4ff;
        z-index: 9999;
    }
</style>
<div class="footer">Developed for Smart Students | Made by Imran</div>
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
        st.markdown("<h1 style='text-align:center;'>🔬 Science Exam Login</h1>", unsafe_allow_html=True)
        uploaded_file = st.file_uploader("📂 Upload 'questions.csv' to begin", type="csv")
        if uploaded_file:
            st.session_state.df = load_data(uploaded_file)
            st.rerun()

if st.session_state.df is not None:
    df = st.session_state.df
    total_qs = len(df)
    time_limit_secs = total_qs * 60

    if not st.session_state.exam_started and not st.session_state.submitted:
        st.markdown("<h1 style='text-align:center;'>🧬 Science Model Test</h1>", unsafe_allow_html=True)
        st.markdown(f"""
        <div class="question-card">
            <h2 style='text-align:center; color:#00d4ff !important;'>📋 Instructions</h2>
            <p style='text-align:center;'>• Total Questions: <b>{total_qs}</b></p>
            <p style='text-align:center;'>• Total Time: <b>{total_qs} Minutes</b></p>
            <p style='text-align:center;'>• Auto-Submit feature enabled.</p>
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
        # Sticky Timer at top
        st.markdown(f'<div class="sticky-timer">⏳ {mins:02d}:{secs:02d} Remaining</div><div style="margin-top:80px;"></div>', unsafe_allow_html=True)
        
        with st.form("exam_form"):
            user_answers = {}
            for i, row in df.iterrows():
                st.markdown(f'<div class="question-card"><h3>Q{i+1}. {row["Question"]}</h3></div>', unsafe_allow_html=True)
                opts = [str(row['Option A']), str(row['Option B']), str(row['Option C']), str(row['Option D'])]
                user_answers[i] = st.radio("Select Answer:", opts, index=None, key=f"q{i}", label_visibility="collapsed")
                st.write("---")
            
            if st.form_submit_button("✅ Submit All Answers"):
                st.session_state.user_results = user_answers
                st.session_state.submitted = True
                st.session_state.exam_started = False
                st.rerun()

    elif st.session_state.submitted:
        st.markdown("<h1 style='text-align:center;'>📊 Result Dashboard</h1>", unsafe_allow_html=True)
        score = sum(1 for i, r in df.iterrows() if str(st.session_state.user_results.get(i)) == str(r['Correct Answer']))
        perc = (score / total_qs) * 100
        
        st.markdown(f"""
        <div class="question-card" style="text-align:center; border-left: none; border-top: 5px solid #00d4ff;">
            <h2 style='color:#ffffff !important;'>Your Score</h2>
            <h1 style="font-size: 65px; color: #00d4ff !important;">{score} / {total_qs}</h1>
            <p style='font-size:18px;'>Success Rate: <b>{perc:.1f}%</b></p>
        </div>
        """, unsafe_allow_html=True)

        with st.expander("🔍 Detailed Answer Key"):
            for i, row in df.iterrows():
                u = str(st.session_state.user_results.get(i))
                c = str(row['Correct Answer'])
                st.markdown(f"**Q{i+1}: {row['Question']}**")
                if u == c:
                    st.success(f"✅ Correct: {u}")
                else:
                    st.error(f"❌ Your Answer: {u if u!='None' else 'Skipped'}")
                    st.info(f"👉 Right Answer: {c}")
                st.divider()

        if st.button("🔄 Try Again"):
            st.session_state.exam_started = False
            st.session_state.submitted = False
            st.session_state.df = None
            st.rerun()
