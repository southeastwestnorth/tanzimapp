import streamlit as st
import pandas as pd
import time
import random

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Smart Exam System",
    page_icon="🎓",
    layout="centered"
)

# --- 2. CSS FOR FOOTER & STYLING ---
hide_st_style = """
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
                color: black;
                text-align: center;
                padding: 10px;
                font-size: 14px;
                border-top: 1px solid #ddd;
                z-index: 1000;
            }
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)

footer = """
<div class="footer">
<p>Developed with ❤️ | <b>Made by Imran</b></p>
</div>
"""
st.markdown(footer, unsafe_allow_html=True)

# --- 3. FUNCTIONS ---

@st.cache_data
def load_data():
    """Loads the CSV and randomizes questions."""
    try:
        # Assumes the CSV is in the same folder
        df = pd.read_csv("questions.csv")
        # Randomize the order of questions
        df = df.sample(frac=1).reset_index(drop=True)
        return df
    except FileNotFoundError:
        return None

def reset_exam():
    """Resets the exam state."""
    st.session_state.exam_started = False
    st.session_state.submitted = False
    st.session_state.start_time = None
    st.session_state.answers = {}

# --- 4. SESSION STATE INITIALIZATION ---
if 'exam_started' not in st.session_state:
    st.session_state.exam_started = False
if 'submitted' not in st.session_state:
    st.session_state.submitted = False
if 'answers' not in st.session_state:
    st.session_state.answers = {}

# --- 5. MAIN APP LOGIC ---

st.title("📝 Student Exam Portal")

# Load Data
df = load_data()

if df is None:
    st.error("❌ 'questions.csv' file not found! Please upload it to the folder.")
    st.stop()

total_questions = len(df)
# SMART FEATURE: 1 Minute per Question
exam_duration_sec = total_questions * 60 

# --- A. START SCREEN ---
if not st.session_state.exam_started and not st.session_state.submitted:
    st.info(f"📋 **Total Questions:** {total_questions}")
    st.info(f"⏳ **Time Limit:** {total_questions} Minutes (Auto-calculated)")
    st.warning("⚠️ Once you click start, the timer begins. Do not refresh the page.")
    
    if st.button("🚀 Start Exam"):
        st.session_state.exam_started = True
        st.session_state.start_time = time.time()
        st.rerun()

# --- B. EXAM SCREEN ---
elif st.session_state.exam_started and not st.session_state.submitted:
    
    # Timer Logic
    elapsed_time = time.time() - st.session_state.start_time
    remaining_time = exam_duration_sec - elapsed_time
    
    # Auto-Submit if time runs out
    if remaining_time <= 0:
        st.session_state.submitted = True
        st.session_state.exam_started = False
        st.rerun()
    
    # Sticky Timer Display
    mins, secs = divmod(int(remaining_time), 60)
    timer_color = "red" if remaining_time < 60 else "blue"
    st.markdown(f"### ⏳ Time Left: <span style='color:{timer_color}'>{mins:02d}:{secs:02d}</span>", unsafe_allow_html=True)
    
    # Progress Bar
    progress = (total_questions - len(df)) / total_questions # Simple placeholder
    st.progress(min(1.0, elapsed_time / exam_duration_sec))

    with st.form("exam_form"):
        for index, row in df.iterrows():
            st.markdown(f"**Q{index+1}. {row['question']}**")
            
            # Shuffle options for display only (Smart Feature)
            options = [row['option_1'], row['option_2'], row['option_3'], row['option_4']]
            
            # We use the index as key to store answer
            selected_option = st.radio(
                "Select an option:", 
                options, 
                index=None, 
                key=f"q_{index}", 
                label_visibility="collapsed"
            )
            st.divider()
        
        # Submit Button
        submitted = st.form_submit_button("✅ Submit Exam")
        if submitted:
            st.session_state.submitted = True
            st.session_state.exam_started = False
            st.rerun()

# --- C. RESULTS SCREEN ---
elif st.session_state.submitted:
    st.balloons()
    st.header("📊 Exam Results")
    
    score = 0
    correct_count = 0
    
    # Grading Logic
    for index, row in df.iterrows():
        user_choice = st.session_state.get(f"q_{index}")
        correct_answer = row['answer']
        
        if user_choice == correct_answer:
            score += 1
            correct_count += 1

    # Smart Feature: Calculate Grade
    percentage = (score / total_questions) * 100
    if percentage >= 80:
        grade = "Excellent! 🌟"
        color = "green"
    elif percentage >= 50:
        grade = "Good Job! 👍"
        color = "orange"
    else:
        grade = "Needs Improvement 📚"
        color = "red"

    st.markdown(f"## You Scored: {score} / {total_questions}")
    st.markdown(f"### Percentage: :{color}[{percentage:.2f}%] - {grade}")
    
    # Detailed Review Section
    with st.expander("🔍 View Detailed Answer Key"):
        for index, row in df.iterrows():
            user_choice = st.session_state.get(f"q_{index}")
            correct_answer = row['answer']
            
            st.markdown(f"**Q{index+1}: {row['question']}**")
            
            if user_choice == correct_answer:
                st.success(f"✅ Your Answer: {user_choice}")
            else:
                st.error(f"❌ Your Answer: {user_choice if user_choice else 'Skipped'}")
                st.info(f"👉 Correct Answer: {correct_answer}")
            st.divider()

    if st.button("🔄 Retake Exam"):
        reset_exam()
        st.rerun()
