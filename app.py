import streamlit as st
import pandas as pd
import time

# --- 1. APP CONFIGURATION (Must be first) ---
st.set_page_config(
    page_title="Science Exam App",
    page_icon="🧬",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- 2. ADVANCED CSS FOR MOBILE UI & ANIMATIONS ---
st.markdown("""
    <style>
    /* Import Google Font for Bengali */
    @import url('https://fonts.googleapis.com/css2?family=Hind+Siliguri:wght@400;600&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Hind Siliguri', sans-serif;
    }

    /* Background Gradient */
    .stApp {
        background: linear-gradient(to bottom right, #eef2f3, #8e9eab);
    }

    /* Hide Default Streamlit Elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* Sticky Timer at Top */
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

    /* Card Style for Questions */
    .question-card {
        background-color: white;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        margin-bottom: 20px;
        animation: fadeIn 0.5s ease-in;
    }

    /* Animations */
    @keyframes fadeIn {
