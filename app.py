import streamlit as st
import pandas as pd
import time
from datetime import datetime

# Try importing FPDF for PDF generation
try:
    from fpdf import FPDF
    HAS_PDF_LIB = True
except ImportError:
    HAS_PDF_LIB = False

# --- 1. CONFIGURATION ---
st.set_page_config(
    page_title="FastExam",
    page_icon="⚡",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- 2. FAST UI CSS ---
st.markdown("""
<style>
    /* Global Clean Theme */
    .stApp { background-color: #ffffff; color: #1f1f1f; font-family: 'Segoe UI', sans-serif; }

    /* Sticky Header for Timer & Title */
    .sticky-header {
        position: fixed; top: 0; left: 0; width: 100%;
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(10px);
        border-bottom: 2px solid #e0e0e0;
        padding: 15px 20px;
        z-index: 99999;
        display: flex; justify-content: space-between; align-items: center;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
    }
    .header-title { font-size: 24px; font-weight: 800; color: #000; letter-spacing: -1px; }
    .header-timer { font-size: 20px; font-weight: 600; color: #d93025; font-variant-numeric: tabular-nums; }
    
    /* Spacer to prevent content hiding behind header */
    .header-spacer { height: 80px; }

    /* Question Card Styling */
    .q-container {
        background: #f8f9fa; border: 1px solid #e9ecef;
        padding: 20px; border-radius: 8px; margin-bottom: 25px;
    }
    .q-title { font-weight: 700; font-size: 18px; margin-bottom: 12px; color: #202124; }

    /* Custom Minimal Footer */
    footer { visibility: hidden; }
    .imran-footer {
        text-align: center; padding: 20px; color: #9aa0a6; font-size: 12px;
        border-top: 1px solid #eee; margin-top: 50px;
    }
    
    /* Hide Streamlit elements */
    #MainMenu {visibility: hidden;}
    .stDeployButton {display:none;}
</style>
""", unsafe_allow_html=True)

# --- 3. SMART FUNCTIONS ---

@st.cache_data
def smart_parse_csv(file):
    """Parses CSV intelligently, mapping columns regardless of case."""
    try:
        df = pd.read_csv(file)
        df.columns = [c.strip() for c in df.columns]
        
        # Mapping Dictionary
        col_map = {}
        required = {'Question': ['question', 'q', 'problem'], 
                    'Correct Answer': ['answer', 'correct', 'key', 'ans']}
        
        # Find columns
        lower_cols = {c.lower(): c for c in df.columns}
        
        for std_name, aliases in required.items():
            found = False
            for alias in aliases:
                if alias in lower_cols:
                    col_map[std_name] = lower_cols[alias]
                    found = True
                    break
            if not found: return None # Missing critical column

        # Rename critical columns
        df = df.rename(columns={v: k for k, v in col_map.items()})
        
        # Ensure options exist, fill if missing
        for opt in ['Option A', 'Option B', 'Option C', 'Option D']:
            # Search for options fuzzily
            opt_key = opt.lower()
            if opt_key in lower_cols:
                df = df.rename(columns={lower_cols[opt_key]: opt})
            elif opt not in df.columns:
                df[opt] = None # Create empty if missing
                
        return df
    except:
        return None

def generate_wrong_answers_pdf(results, df):
    """Generates PDF of ONLY wrong answers."""
    if not HAS_PDF_LIB: return None

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=11)
    
    # Title
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, "FastExam - Improvement Report", 0, 1, 'C')
    pdf.ln(5)

    # Filter Wrong Answers
    wrong_items = [(i, res) for i, res in results.items() if not res['is_correct']]
    
    if not wrong_items:
        pdf.set_font("Arial", size=12)
        pdf.cell(0, 10, "Excellent! No incorrect answers to review.", 0, 1)
        return pdf.output(dest='S').encode('latin-1')

    pdf.set_font("Arial", size=10)
    pdf.multi_cell(0, 5, f"Total Incorrect: {len(wrong_items)}")
    pdf.ln(5)

    for idx, (q_idx, res) in enumerate(wrong_items, 1):
        row = df.iloc[q_idx]
        
        # Question
        pdf.set_font("Arial", 'B', 11)
        pdf.multi_cell(0, 6, f"{idx}. {row['Question']}")
        
        # Options
        pdf.set_font("Arial", size=10)
        opts = [f"A) {row.get('Option A','')}", f"B) {row.get('Option B','')}", 
                f"C) {row.get('Option C','')}", f"D) {row.get('Option D','')}"]
        for opt in opts:
            if str(opt).strip() not in ['None', 'nan', '']:
                pdf.cell(0, 5, str(opt), 0, 1)
        
        # Answers
        pdf.ln(2)
        pdf.set_text_color(220, 53, 69) # Red
        pdf.cell(0, 5, f"Your Answer: {res['user_ans']}", 0, 1)
        pdf.set_text_color(40, 167, 69) # Green
        pdf.cell(0, 5, f"Correct Answer: {row['Correct Answer']}", 0, 1)
        
        pdf.set_text_color(0, 0, 0)
        pdf.ln(5)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(5)

    return pdf.output(dest='S').encode('latin-1')

# --- 4. APP LOGIC ---

if 'status' not in st.session_state:
    st.session_state.status = 'UPLOAD' # UPLOAD -> EXAM -> RESULT
    st.session_state.start_time = None
    st.session_state.df = None

# --- PHASE 1: UPLOAD ---
if st.session_state.status == 'UPLOAD':
    st.title("⚡ FastExam Setup")
    
    # Auto-load 'questions.csv' if exists
    try:
        local_df = smart_parse_csv("questions.csv")
        if local_df is not None:
            st.success("✅ 'questions.csv' loaded automatically.")
            st.session_state.df = local_df
    except:
        pass

    # File Uploader
    if st.session_state.df is None:
        up = st.file_uploader("Upload CSV", type=['csv'])
        if up:
            df = smart_parse_csv(up)
            if df is not None:
                st.session_state.df = df
                st.rerun()
            else:
                st.error("Could not parse CSV. Ensure 'Question' and 'Answer' columns exist.")
    
    if st.session_state.df is not None:
        if st.button("Start Exam", type="primary", use_container_width=True):
            st.session_state.status = 'EXAM'
            st.session_state.start_time = time.time()
            st.rerun()

# --- PHASE 2: EXAM (SINGLE PAGE FORM) ---
elif st.session_state.status == 'EXAM':
    df = st.session_state.df
    
    # 1. Sticky Header
    st.markdown(f"""
    <div class="sticky-header">
        <div class="header-title">⚡ FastExam</div>
        <div class="header-timer" id="timer">00:00</div>
    </div>
    <div class="header-spacer"></div>
    <script>
    var start = {st.session_state.start_time};
    setInterval(function() {{
        var now = new Date().getTime() / 1000;
        var diff = Math.floor(now - start);
        var m = Math.floor(diff / 60);
        var s = Math.floor(diff % 60);
        document.getElementById("timer").innerHTML = 
            (m<10?"0"+m:m) + ":" + (s<10?"0"+s:s);
    }}, 1000);
    </script>
    """, unsafe_allow_html=True)

    # 2. Huge Form
    with st.form("exam_form"):
        user_answers = {}
        
        for idx, row in df.iterrows():
            st.markdown(f"""<div class="q-container"><div class="q-title">{idx+1}. {row['Question']}</div>""", unsafe_allow_html=True)
            
            # Clean options
            opts = [str(row.get(c)) for c in ['Option A', 'Option B', 'Option C', 'Option D'] if pd.notna(row.get(c))]
            opts = [o for o in opts if o != 'None']
            
            user_answers[idx] = st.radio(
                "Select Answer", 
                opts, 
                index=None, 
                key=f"q_{idx}", 
                label_visibility="collapsed"
            )
            st.markdown("</div>", unsafe_allow_html=True)
            
        submitted = st.form_submit_button("✅ Submit All Answers", type="primary", use_container_width=True)
        
        if submitted:
            st.session_state.results = user_answers
            st.session_state.status = 'RESULT'
            st.rerun()

# --- PHASE 3: RESULTS & PDF ---
elif st.session_state.status == 'RESULT':
    st.title("📊 Results")
    
    df = st.session_state.df
    answers = st.session_state.results
    
    score = 0
    analysis = {}
    
    # Grading
    for idx, row in df.iterrows():
        u_ans = answers.get(idx)
        c_ans = str(row['Correct Answer']).strip()
        
        # Normalize
        u_str = str(u_ans).strip() if u_ans else "Skipped"
        is_correct = (u_str == c_ans)
        
        if is_correct: score += 1
        
        analysis[idx] = {
            'user_ans': u_str,
            'is_correct': is_correct
        }

    # Display Score
    pct = (score / len(df)) * 100
    color = "green" if pct >= 50 else "red"
    st.markdown(f"""
    <div style="text-align:center; padding: 20px; background:#f0f2f6; border-radius:10px;">
        <h1 style="color:{color}; font-size:40px; margin:0;">{pct:.1f}%</h1>
        <p>Scored {score} out of {len(df)}</p>
    </div>
    """, unsafe_allow_html=True)

    st.write("---")
    
    # PDF Button
    if HAS_PDF_LIB:
        pdf_data = generate_wrong_answers_pdf(analysis, df)
        if pdf_data:
            st.download_button(
                label="📥 Download Wrong Answers (PDF)",
                data=pdf_data,
                file_name="FastExam_Review.pdf",
                mime="application/pdf",
                use_container_width=True,
                type="primary"
            )
    else:
        st.warning("Install 'fpdf' library to enable PDF export.")

    # Reset
    if st.button("Start Over", use_container_width=True):
        st.session_state.status = 'UPLOAD'
        st.session_state.df = None
        st.rerun()

# --- FOOTER ---
st.markdown("<div class='imran-footer'>Made by Imran</div>", unsafe_allow_html=True)
