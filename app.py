import streamlit as st
import pandas as pd
import time

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Science Exam Portal",
    page_icon="🔬",
    layout="centered"
)

# --- 2. SMART STYLING (Fixed Footer "Made by Imran") ---
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .footer {
        position: fixed;
        left: 0;
        bottom: 0;
        width: 100%;
        background-color: #f1f1f1;
        color: #333;
        text-align: center;
        padding: 10px;
        font-weight: bold;
        border-top: 2px solid #007bff;
        z-index: 100;
    }
    .stRadio > label {
        font-size: 18px;
        font-weight: bold;
        color: #1E3A8A;
    }
    </style>
    <div class="footer">
        Developed for Students | Made by Imran
    </div>
    """, unsafe_allow_html=True)

# --- 3. DATA LOADING ---
@st.cache_data
def load_exam_data():
    try:
        # Loading CSV - Ensure your file is named 'questions.csv'
        df = pd.read_csv("questions.csv")
        # Shuffle questions for every new session to prevent cheating
        return df.sample(frac=1).reset_index(drop=True)
    except Exception as e:
        st.error(f"Error loading CSV: {e}")
        return None

# --- 4. SESSION INITIALIZATION ---
if 'exam_started' not in st.session_state:
    st.session_state.exam_started = False
if 'submitted' not in st.session_state:
    st.session_state.submitted = False
if 'start_time' not in st.session_state:
    st.session_state.start_time = None

df = load_exam_data()

# --- 5. APP LOGIC ---

if df is not None:
    total_qs = len(df)
    time_limit_secs = total_qs * 60  # SMART FEATURE: 1 Min per Question

    st.title("🧪 Science Model Test")
    
    # --- START PAGE ---
    if not st.session_state.exam_started and not st.session_state.submitted:
        st.write(f"### Welcome to the Exam!")
        st.info(f"📋 Total Questions: {total_qs}")
        st.info(f"⏳ Total Time: {total_qs} Minutes")
        
        if st.button("🚀 Start Exam Now"):
            st.session_state.exam_started = True
            st.session_state.start_time = time.time()
            st.rerun()

    # --- EXAM PAGE ---
    elif st.session_state.exam_started and not st.session_state.submitted:
        # Calculate Time
        elapsed = time.time() - st.session_state.start_time
        remaining = time_limit_secs - elapsed
        
        # Auto-Submit on Timer End
        if remaining <= 0:
            st.session_state.submitted = True
            st.session_state.exam_started = False
            st.rerun()

        # Display Timer
        mins, secs = divmod(int(remaining), 60)
        st.sidebar.metric("⏳ Time Remaining", f"{mins:02d}:{secs:02d}")
        
        # Exam Form
        with st.form("exam_form"):
            user_answers = {}
            for i, row in df.iterrows():
                st.markdown(f"#### Q{i+1}. {row['Question']}")
                options = [row['Option A'], row['Option B'], row['Option C'], row['Option D']]
                
                # Capture answer
                user_answers[i] = st.radio(
                    f"Select for {i}", 
                    options, 
                    index=None, 
                    key=f"q{i}", 
                    label_visibility="collapsed"
                )
                st.write("---")
            
            submit_btn = st.form_submit_button("Submit Exam")
            if submit_btn:
                st.session_state.user_results = user_answers
                st.session_state.submitted = True
                st.session_state.exam_started = False
                st.rerun()

    # --- RESULT PAGE ---
    elif st.session_state.submitted:
        st.header("📊 Exam Result")
        
        score = 0
        results_data = st.session_state.get('user_results', {})

        for i, row in df.iterrows():
            if results_data.get(i) == row['Correct Answer']:
                score += 1
        
        # Smart Features: Grade Calculation
        perc = (score / total_qs) * 100
        st.subheader(f"Your Score: {score} / {total_qs} ({perc:.1f}%)")
        
        if perc >= 80: st.success("Grade: Excellent! 🌟")
        elif perc >= 40: st.warning("Grade: Passed 👍")
        else: st.error("Grade: Fail - Needs more practice 📚")

        # Detailed Review
        with st.expander("🔍 View Correct Answers"):
            for i, row in df.iterrows():
                u_ans = results_data.get(i)
                c_ans = row['Correct Answer']
                st.write(f"**Q{i+1}: {row['Question']}**")
                if u_ans == c_ans:
                    st.write(f"✅ Correct: {c_ans}")
                else:
                    st.write(f"❌ Your Answer: {u_ans}")
                    st.write(f"✅ Right Answer: {c_ans}")
                st.write("---")
        
        if st.button("Retry Exam"):
            st.session_state.exam_started = False
            st.session_state.submitted = False
            st.rerun()
