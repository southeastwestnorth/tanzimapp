import streamlit as st
import pandas as pd
import time
from datetime import datetime
import base64
from io import BytesIO

# Try importing FPDF for PDF generation, handle if missing
try:
    from fpdf import FPDF
    HAS_PDF_LIB = True
except ImportError:
    HAS_PDF_LIB = False

# --- 1. CONFIGURATION & STATE ---
st.set_page_config(
    page_title="Science Pro | CBT Exam",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. ADVANCED CSS (Glassmorphism & Clean UI) ---
st.markdown("""
<style>
    /* Main Background */
    .stApp { background-color: #0e1117; color: #e6edf3; }

    /* Question Card */
    .q-card {
        background: #161b22; border: 1px solid #30363d;
        border-radius: 12px; padding: 30px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3); margin-bottom: 20px;
    }
    .q-header { color: #58a6ff; font-size: 14px; font-weight: bold; letter-spacing: 1px; margin-bottom: 10px; }
    .q-text { font-size: 22px; font-weight: 600; line-height: 1.5; color: #ffffff; margin-bottom: 20px; }

    /* Navigation Buttons */
    .stButton button { border-radius: 8px; font-weight: 600; }
    
    /* Sidebar Palette */
    .palette-grid { display: grid; grid-template-columns: repeat(5, 1fr); gap: 6px; margin-top: 10px; }
    .palette-item {
        padding: 8px; text-align: center; border-radius: 4px; font-size: 12px; font-weight: bold; cursor: default;
        color: white; border: 1px solid rgba(255,255,255,0.1);
    }
    
    /* Status Colors */
    .status-active { border: 2px solid #58a6ff; box-shadow: 0 0 8px #58a6ff; }
    .status-answered { background-color: #238636; }
    .status-review { background-color: #d29922; }
    .status-skipped { background-color: #21262d; }
    
    /* Hide Default Header */
    header[data-testid="stHeader"] {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# --- 3. SMARTER FUNCTIONS ---

def smart_parse_columns(df):
    """
    Intelligently maps CSV columns to required fields regardless of exact casing.
    Returns standardized DataFrame or None if critical columns missing.
    """
    df.columns = [c.strip() for c in df.columns]
    
    # Keyword mapping priority
    mappings = {
        'Question': ['question', 'q', 'query', 'problem'],
        'Option A': ['option a', 'opt a', 'a', '(a)'],
        'Option B': ['option b', 'opt b', 'b', '(b)'],
        'Option C': ['option c', 'opt c', 'c', '(c)'],
        'Option D': ['option d', 'opt d', 'd', '(d)'],
        'Correct Answer': ['correct answer', 'answer', 'ans', 'key', 'solution']
    }
    
    new_cols = {}
    found_cols = {c.lower(): c for c in df.columns}
    
    for standard, keywords in mappings.items():
        match = None
        for k in keywords:
            if k in found_cols:
                match = found_cols[k]
                break
        if match:
            new_cols[standard] = match
    
    # Verify we have at least Question, Answer and 2 Options
    if 'Question' in new_cols and 'Correct Answer' in new_cols:
        # Renaming
        rename_map = {v: k for k, v in new_cols.items()}
        return df.rename(columns=rename_map)
    return None

def generate_error_pdf(results, df):
    """Generates a PDF of WRONG answers only."""
    if not HAS_PDF_LIB:
        return None

    class PDF(FPDF):
        def header(self):
            self.set_font('Arial', 'B', 15)
            self.cell(0, 10, 'Exam Correction Report', 0, 1, 'C')
            self.ln(5)

    pdf = PDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("Arial", size=11)

    wrong_indices = [i for i, r in results.items() if not r['correct']]
    
    if not wrong_indices:
        pdf.cell(0, 10, "Great job! No incorrect answers found.", 0, 1)
        return pdf.output(dest='S').encode('latin-1')

    count = 1
    for idx in wrong_indices:
        row = df.iloc[idx]
        user_ans = results[idx]['user_ans']
        
        pdf.set_font("Arial", 'B', 12)
        # Multi_cell handles text wrapping
        pdf.multi_cell(0, 8, f"{count}. {row['Question']}")
        pdf.ln(2)
        
        pdf.set_font("Arial", size=10)
        pdf.cell(0, 6, f"A) {row.get('Option A', '-')}", 0, 1)
        pdf.cell(0, 6, f"B) {row.get('Option B', '-')}", 0, 1)
        pdf.cell(0, 6, f"C) {row.get('Option C', '-')}", 0, 1)
        pdf.cell(0, 6, f"D) {row.get('Option D', '-')}", 0, 1)
        pdf.ln(2)
        
        pdf.set_text_color(200, 50, 50) # Red
        pdf.cell(0, 6, f"Your Answer: {user_ans}", 0, 1)
        
        pdf.set_text_color(50, 150, 50) # Green
        pdf.cell(0, 6, f"Correct Answer: {row['Correct Answer']}", 0, 1)
        
        pdf.set_text_color(0, 0, 0) # Reset
        pdf.ln(8)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(5)
        count += 1
        
    return pdf.output(dest='S').encode('latin-1')

# --- 4. SESSION MANAGEMENT ---
if 'session' not in st.session_state:
    st.session_state.session = {
        'state': 'SETUP', # SETUP, RUNNING, SUBMITTED
        'df': None,
        'current_q': 0,
        'answers': {}, # {index: answer}
        'marked': set(),
        'start_time': None,
        'duration': 0
    }

S = st.session_state.session

# --- PHASE 1: SETUP & UPLOAD ---
if S['state'] == 'SETUP':
    col1, col2 = st.columns([1, 2], gap="large")
    with col1:
        st.image("https://cdn-icons-png.flaticon.com/512/3069/3069172.png", width=150)
        st.title("Pro Exam Portal")
        st.caption("Advanced CBT System")
    
    with col2:
        st.markdown("### 📂 Load Question Bank")
        
        # 1. Try Local File
        try:
            local_df = pd.read_csv("questions.csv")
            local_df = smart_parse_columns(local_df)
            file_status = "✅ 'questions.csv' found & parsed."
        except:
            local_df = None
            file_status = "⚠️ No local file found."

        # 2. File Uploader
        uploaded_file = st.file_uploader("Or upload your CSV", type="csv")
        
        df = None
        if uploaded_file:
            try:
                raw = pd.read_csv(uploaded_file)
                df = smart_parse_columns(raw)
                if df is None:
                    st.error("CSV must contain 'Question' and 'Correct Answer' columns.")
            except:
                st.error("Invalid CSV file.")
        elif local_df is not None:
            df = local_df

        if df is not None:
            st.success(f"Loaded {len(df)} questions successfully!")
            st.info(f"Parsing Status: Columns identified: {list(df.columns)}")
            
            S['duration'] = st.number_input("Exam Duration (Minutes)", min_value=1, value=len(df), step=1)
            
            if st.button("🚀 START EXAM", type="primary", use_container_width=True):
                S['df'] = df
                S['state'] = 'RUNNING'
                S['start_time'] = time.time()
                st.rerun()

# --- PHASE 2: EXAM INTERFACE ---
elif S['state'] == 'RUNNING':
    
    # Logic: Timer
    elapsed = time.time() - S['start_time']
    remaining = (S['duration'] * 60) - elapsed
    
    if remaining <= 0:
        S['state'] = 'SUBMITTED'
        st.rerun()

    # --- SIDEBAR: NAVIGATION & STATUS ---
    with st.sidebar:
        # JavaScript Timer (No Rerun Loop)
        st.markdown(f"""
        <div style="text-align:center; border:1px solid #30363d; border-radius:8px; padding:10px; background:#0d1117;">
            <div style="font-size:12px; color:#8b949e;">REMAINING TIME</div>
            <div id="timer" style="font-size:24px; font-weight:bold; color:#f2cc60;">--:--</div>
        </div>
        <script>
        var rem = {remaining};
        setInterval(function() {{
            rem--;
            var m = Math.floor(rem / 60);
            var s = Math.floor(rem % 60);
            if (rem >= 0) {{
                document.getElementById("timer").innerHTML = (m<10?"0"+m:m) + ":" + (s<10?"0"+s:s);
            }}
        }}, 1000);
        </script>
        """, unsafe_allow_html=True)

        st.markdown("### 🧭 Question Palette")
        
        # Render Palette
        cols = st.columns(5)
        # Using pure HTML for grid because st.columns inside sidebar loop is slow
        html_grid = '<div class="palette-grid">'
        for i in range(len(S['df'])):
            style = "status-skipped"
            if i == S['current_q']: style = "status-active"
            elif i in S['marked']: style = "status-review"
            elif i in S['answers']: style = "status-answered"
            
            html_grid += f'<div class="palette-item {style}">{i+1}</div>'
        html_grid += '</div>'
        st.markdown(html_grid, unsafe_allow_html=True)
        
        st.markdown("""
        <div style="margin-top:15px; font-size:11px; display:flex; justify-content:space-between; color:#8b949e;">
            <span>🟦 Current</span> <span>🟩 Done</span> <span>🟨 Review</span>
        </div>
        """, unsafe_allow_html=True)
        
        st.write("---")
        if st.button("🏁 Finish Exam", type="primary", use_container_width=True):
            S['state'] = 'SUBMITTED'
            st.rerun()

    # --- MAIN CONTENT: QUESTION CARD ---
    # Progress Bar
    p = len(S['answers']) / len(S['df'])
    st.progress(p, text=f"Progress: {len(S['answers'])}/{len(S['df'])}")

    q_idx = S['current_q']
    row = S['df'].iloc[q_idx]
    
    # Card
    with st.container():
        st.markdown(f"""
        <div class="q-card">
            <div class="q-header">QUESTION {q_idx + 1}</div>
            <div class="q-text">{row['Question']}</div>
        </div>
        """, unsafe_allow_html=True)
        
        # Options
        options = []
        for col in ['Option A', 'Option B', 'Option C', 'Option D']:
            if col in row and pd.notna(row[col]):
                options.append(str(row[col]))
        
        # Handle state of Radio button
        sel_idx = None
        current_ans = S['answers'].get(q_idx)
        if current_ans in options:
            sel_idx = options.index(current_ans)

        val = st.radio(
            "Select Answer:", 
            options, 
            index=sel_idx, 
            key=f"q_radio_{q_idx}",
            label_visibility="collapsed"
        )
        
        # Save Answer immediately
        if val: S['answers'][q_idx] = val

    # --- FOOTER: CONTROLS ---
    col_l, col_m, col_r = st.columns([1, 2, 1])
    
    with col_l:
        if st.button("⬅️ PREV", use_container_width=True, disabled=q_idx==0):
            S['current_q'] -= 1
            st.rerun()
            
    with col_m:
        is_marked = q_idx in S['marked']
        btn_txt = "❌ Unmark Review" if is_marked else "🚩 Mark for Review"
        if st.button(btn_txt, use_container_width=True):
            if is_marked: S['marked'].remove(q_idx)
            else: S['marked'].add(q_idx)
            st.rerun()
            
    with col_r:
        if q_idx < len(S['df']) - 1:
            if st.button("NEXT ➡️", use_container_width=True):
                S['current_q'] += 1
                st.rerun()

# --- PHASE 3: RESULTS & ANALYTICS ---
elif S['state'] == 'SUBMITTED':
    st.title("📊 Exam Results")
    
    correct = 0
    results_detail = {} # Store details for export
    
    # Grading Logic
    for i, row in S['df'].iterrows():
        user = S['answers'].get(i)
        truth = str(row['Correct Answer'])
        
        # Normalize for comparison (trim strings)
        is_right = False
        if user and str(user).strip() == truth.strip():
            is_right = True
            correct += 1
            
        results_detail[i] = {
            'user_ans': user if user else "Skipped",
            'correct': is_right
        }

    total = len(S['df'])
    score_pct = (correct / total) * 100
    
    # 1. Score Cards
    c1, c2, c3 = st.columns(3)
    c1.metric("Score", f"{correct} / {total}")
    c2.metric("Percentage", f"{score_pct:.1f}%")
    
    grade = "F"
    if score_pct >= 80: grade = "A+"
    elif score_pct >= 60: grade = "B"
    elif score_pct >= 40: grade = "C"
    c3.metric("Grade", grade)
    
    if score_pct > 70: st.balloons()

    # 2. PDF EXPORT (Wrong Answers)
    st.write("---")
    st.subheader("📥 Downloads")
    
    if HAS_PDF_LIB:
        col_pdf, col_csv = st.columns(2)
        with col_pdf:
            pdf_bytes = generate_error_pdf(results_detail, S['df'])
            if pdf_bytes:
                st.download_button(
                    label="📄 Download Correction Report (PDF)",
                    data=pdf_bytes,
                    file_name="exam_corrections.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
    else:
        st.warning("Install 'fpdf' (pip install fpdf) to enable PDF exports.")

    # 3. Detailed Review UI
    with st.expander("🔍 View Detailed Analysis"):
        for i, row in S['df'].iterrows():
            res = results_detail[i]
            color = "#238636" if res['correct'] else "#da3633"
            icon = "✅" if res['correct'] else "❌"
            
            st.markdown(f"""
            <div style="border-left: 5px solid {color}; padding-left: 15px; margin-bottom: 15px; background: #161b22; padding: 10px; border-radius: 0 10px 10px 0;">
                <div style="color: #ffffff; font-weight: bold;">{icon} Q{i+1}: {row['Question']}</div>
                <div style="display: flex; gap: 20px; margin-top: 5px; font-size: 14px;">
                    <span style="color: #8b949e;">Your Answer: <b style="color:{color}">{res['user_ans']}</b></span>
                    <span style="color: #8b949e;">Correct: <b>{row['Correct Answer']}</b></span>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
    if st.button("🔄 Start New Exam", use_container_width=True):
        st.session_state.clear()
        st.rerun()
