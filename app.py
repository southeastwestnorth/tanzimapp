import streamlit as st
import pandas as pd
import time
from datetime import datetime

# Optional: PDF Support
try:
    from fpdf import FPDF
    HAS_PDF = True
except ImportError:
    HAS_PDF = False

# --- 1. CONFIGURATION ---
st.set_page_config(
    page_title="FastExam",
    page_icon="⚡",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- 2. FAST CSS (Sticky Header & Custom Footer) ---
st.markdown("""
<style>
    /* Global Reset */
    .stApp { background-color: #0e1117; font-family: sans-serif; }
    
    /* Hide Default Elements */
    [data-testid="stHeader"], [data-testid="stToolbar"], footer { display: none !important; }

    /* Sticky Timer Header */
    .sticky-header {
        position: fixed; top: 0; left: 0; width: 100%;
        background: #161b22; border-bottom: 2px solid #00d4ff;
        padding: 15px; text-align: center; z-index: 9999;
        box-shadow: 0 4px 12px rgba(0,0,0,0.5);
    }
    .timer-display { font-size: 24px; font-weight: bold; color: #00d4ff; font-family: monospace; }
    
    /* Question Card */
    .q-card {
        background: #1c2128; border: 1px solid #30363d;
        border-radius: 8px; padding: 20px; margin-bottom: 15px;
    }
    .q-text { font-size: 18px; color: #e6edf3; font-weight: 600; margin-bottom: 10px; }
    
    /* Radio Button Customization */
    .stRadio label { color: #8b949e !important; }
    
    /* Custom Footer */
    .imran-footer {
        position: fixed; left: 0; bottom: 0; width: 100%;
        background: #0d1117; color: #484f58; text-align: center;
        padding: 8px; font-size: 12px; border-top: 1px solid #30363d;
        z-index: 9999;
    }
    
    /* Adjust top margin for sticky header */
    .block-container { padding-top: 80px; padding-bottom: 60px; }
</style>
""", unsafe_allow_html=True)

# --- 3. CORE FUNCTIONS ---

def load_data():
    try:
        df = pd.read_csv("questions.csv")
        # Basic cleanup: remove whitespace from column names
        df.columns = [c.strip() for c in df.columns]
        return df
    except FileNotFoundError:
        return None

def generate_pdf(wrong_answers):
    """Generates PDF for WRONG answers only"""
    if not HAS_PDF: return None
    
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    pdf.cell(200, 10, txt="FastExam - Correction Report", ln=True, align='C')
    pdf.ln(10)
    
    for item in wrong_answers:
        # Question
        pdf.set_font("Arial", 'B', 12)
        pdf.multi_cell(0, 10, f"Q: {item['question']}")
        
        # User Answer (Red)
        pdf.set_text_color(200, 50, 50)
        pdf.set_font("Arial", '', 11)
        pdf.cell(0, 8, f"Your Answer: {item['user_ans']}", ln=True)
        
        # Correct Answer (Green)
        pdf.set_text_color(50, 150, 50)
        pdf.cell(0, 8, f"Correct Answer: {item['correct_ans']}", ln=True)
        
        # Reset color and add line
        pdf.set_text_color(0, 0, 0)
        pdf.ln(5)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(5)
        
    return pdf.output(dest='S').encode('latin-1')

# --- 4. APP LOGIC ---

# Initialize State
if 'submitted' not in st.session_state: st.session_state.submitted = False
if 'start_time' not in st.session_state: st.session_state.start_time = None

df = load_data()

# Footer Injection
st.markdown('<div class="imran-footer">Made by Imran</div>', unsafe_allow_html=True)

if df is None:
    st.error("❌ 'questions.csv' not found. Please add the file to the directory.")
    st.stop()

# --- VIEW 1: EXAM ACTIVE ---
if not st.session_state.submitted:
    
    # Start Timer on first load
    if st.session_state.start_time is None:
        st.session_state.start_time = time.time()
    
    # Calculate Time (Javascript Timer for Visuals)
    elapsed = time.time() - st.session_state.start_time
    total_time = len(df) * 60 # 1 minute per question
    remaining = max(0, total_time - elapsed)
    
    # Sticky Header with JS Timer
    st.markdown(f"""
    <div class="sticky-header">
        <div class="timer-display" id="time_disp">00:00</div>
    </div>
    <script>
    var time_left = {remaining};
    function updateTimer() {{
        var m = Math.floor(time_left / 60);
        var s = Math.floor(time_left % 60);
        document.getElementById("time_disp").innerHTML = 
            (m < 10 ? "0"+m : m) + ":" + (s < 10 ? "0"+s : s);
        time_left--;
    }}
    setInterval(updateTimer, 1000);
    </script>
    """, unsafe_allow_html=True)

    st.title("⚡ FastExam")
    st.caption("Scroll down to answer all questions.")

    # Single Form for All Questions
    with st.form("fast_exam_form"):
        user_responses = {}
        
        for index, row in df.iterrows():
            st.markdown(f"""
            <div class="q-card">
                <div class="q-text">{index + 1}. {row['Question']}</div>
            </div>
            """, unsafe_allow_html=True)
            
            options = [str(row['Option A']), str(row['Option B']), str(row['Option C']), str(row['Option D'])]
            
            user_responses[index] = st.radio(
                f"Answer for Q{index+1}", 
                options, 
                index=None, 
                key=f"q_{index}", 
                label_visibility="collapsed"
            )
            st.write("---")
            
        submitted = st.form_submit_button("✅ SUBMIT EXAM", use_container_width=True)
        
        if submitted:
            st.session_state.submitted = True
            st.session_state.responses = user_responses
            st.rerun()

# --- VIEW 2: RESULTS ---
else:
    st.markdown("<div style='margin-top: 50px;'></div>", unsafe_allow_html=True)
    st.title("📊 Results")
    
    score = 0
    wrong_answers_log = []
    
    for index, row in df.iterrows():
        user_ans = st.session_state.responses.get(index)
        correct_ans = str(row['Correct Answer'])
        
        # Basic Clean Comparison
        if str(user_ans).strip() == correct_ans.strip():
            score += 1
        else:
            wrong_answers_log.append({
                "question": row['Question'],
                "user_ans": user_ans if user_ans else "Skipped",
                "correct_ans": correct_ans
            })
            
    percentage = (score / len(df)) * 100
    
    # Score Display
    c1, c2 = st.columns(2)
    c1.metric("Total Score", f"{score} / {len(df)}")
    c2.metric("Percentage", f"{percentage:.1f}%")
    
    if percentage > 70:
        st.success("🎉 Congratulations! Excellent Result.")
        st.balloons()
    else:
        st.warning("Needs Improvement.")

    # PDF Download
    if HAS_PDF and wrong_answers_log:
        pdf_data = generate_pdf(wrong_answers_log)
        st.download_button(
            label="📥 Download Wrong Answers (PDF)",
            data=pdf_data,
            file_name="FastExam_Correction.pdf",
            mime="application/pdf",
            use_container_width=True
        )

    # Detailed List View
    st.subheader("Review")
    for index, row in df.iterrows():
        user_ans = st.session_state.responses.get(index)
        correct_ans = str(row['Correct Answer'])
        is_correct = str(user_ans).strip() == correct_ans.strip()
        
        color = "#238636" if is_correct else "#da3633" # Green/Red
        
        st.markdown(f"""
        <div style="border-left: 4px solid {color}; background: #161b22; padding: 10px; margin-bottom: 10px;">
            <b>Q{index+1}: {row['Question']}</b><br>
            <span style="color:#8b949e; font-size:14px;">You: {user_ans if user_ans else 'Skipped'} | Correct: {correct_ans}</span>
        </div>
        """, unsafe_allow_html=True)
        
    if st.button("🔄 Restart"):
        st.session_state.submitted = False
        st.session_state.start_time = None
        st.rerun()
