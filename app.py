import streamlit as st
import pandas as pd
from database import Database
from voice_handler import VoiceHandler
from gemini_processor import GeminiProcessor
from memory_handler import MemoryHandler
from voice_input import render_voice_input
import os
from dotenv import load_dotenv

load_dotenv()

# Initialize components
try:
    db = Database()
    voice_handler = VoiceHandler()
    gemini_processor = GeminiProcessor()
    if 'memory_handler' not in st.session_state:
        st.session_state.memory_handler = MemoryHandler()
except Exception as e:
    st.error(f"Error initializing components: {str(e)}")
    st.stop()

def validate_request(project_number, project_name, amount, reason):
    if not project_number or not project_name or not amount or not reason:
        missing_fields = []
        if not project_number: missing_fields.append("project number")
        if not project_name: missing_fields.append("project name")
        if not amount: missing_fields.append("amount")
        if not reason: missing_fields.append("reason")
        return False, f"Please provide the following missing information: {', '.join(missing_fields)}"
    return True, ""

def render_text_input(language_option):
    """Render the text input section"""
    if language_option == "Arabic":
        st.markdown("""
        أدخل طلبك في شكل نص. مثال:
        > "أحتاج إلى طلب 500 ريال للمشروع 223 المسمى جامعة أبها لشراء بعض الأدوات"
        """)
    else:
        st.markdown("""
        Enter your request in text format. Example:
        > "I need to request 500 riyals for project 223 named Abha University to buy some tools"
        """)
    
    text_input = st.text_area("Enter your request:", height=100)
    col1, col2 = st.columns([1, 4])
    
    with col1:
        if st.button("Process Text"):
            if text_input:
                with st.spinner("Processing text input..."):
                    context = st.session_state.memory_handler.get_context()
                    details = gemini_processor.extract_request_details(text_input, context)
                    if details:
                        st.session_state['voice_details'] = details
                        if 'translated_text' in details:
                            st.info(f"Translated text: {details['translated_text']}")
                        if details.get('missing_fields'):
                            missing = ", ".join(details['missing_fields'])
                            st.warning(f"Please provide the following missing information: {missing}")
                        else:
                            st.success("Text processed! Please verify the details below.")
                    else:
                        st.error("Could not extract request details. Please try again.")
            else:
                st.warning("Please enter some text first.")

st.title("AI Agent Money Request System")
st.markdown("---")

# Language Selection
if 'language' not in st.session_state:
    st.session_state.language = "en-US"  # Default to English

st.sidebar.title("Settings")
language_option = st.sidebar.selectbox(
    "Select Input Language",
    options=["English", "Arabic", "Mixed (Arabic/English)"],
    index=0,
    key="language_select"
)

# Map selection to language codes
language_mapping = {
    "English": "en-US",
    "Arabic": "ar-SA",
    "Mixed (Arabic/English)": "mixed"
}

# Input Method Tabs
tab1, tab2 = st.tabs(["Voice Input", "Text Input"])

# Voice Input Tab
with tab1:
    render_voice_input(
        voice_handler,
        language_option,
        language_mapping,
        st.session_state.memory_handler,
        gemini_processor
    )

# Text Input Tab
with tab2:
    render_text_input(language_option)

# Show conversation history
if st.session_state.memory_handler.conversation_history:
    with st.expander("Previous Inputs"):
        for i, text in enumerate(st.session_state.memory_handler.conversation_history, 1):
            st.text(f"{i}. {text}")

# Input form
st.markdown("---")
st.subheader("Submit Money Request")
with st.form("request_form"):
    voice_details = st.session_state.get('voice_details', {})
    
    project_number = st.text_input("Project Number", value=voice_details.get('project_number', ''))
    project_name = st.text_input("Project Name", value=voice_details.get('project_name', ''))
    amount = st.number_input("Amount (in riyals)", 
                           value=float(voice_details.get('amount', 0)),
                           min_value=0.0, 
                           step=100.0)
    reason = st.text_input("Reason for Request", value=voice_details.get('reason', ''))
    
    col1, col2 = st.columns(2)
    with col1:
        submitted = st.form_submit_button("Submit Request")
    with col2:
        confirmed = st.form_submit_button("Confirm & Save")

if submitted:
    is_valid, message = validate_request(project_number, project_name, amount, reason)
    if is_valid:
        st.session_state.show_confirmation = True
        confirmation_text = f"""
        Please review the following request and click 'Confirm & Save' to proceed:
        
        - Project Number: {project_number}
        - Project Name: {project_name}
        - Amount: {amount} riyals
        - Reason: {reason}
        """
        st.info(confirmation_text)
    else:
        st.error(message)

if confirmed:
    is_valid, message = validate_request(project_number, project_name, amount, reason)
    if is_valid:
        try:
            original_text = voice_details.get('original_text', '') if 'voice_details' in st.session_state else ''
            db.add_request(project_number, project_name, amount, reason, original_text)
            st.success("Request successfully added to the database!")
            if 'voice_details' in st.session_state:
                del st.session_state['voice_details']
            st.session_state.show_confirmation = False
            st.session_state.memory_handler.clear_memory()
        except Exception as e:
            st.error(f"Error saving request: {str(e)}")
    else:
        st.error(message)

# Display existing requests
st.markdown("---")
st.subheader("Existing Requests")
try:
    requests = db.get_all_requests()
    if requests:
        df = pd.DataFrame(requests)
        # Reorder columns to show original text
        columns = ['timestamp', 'project_number', 'project_name', 'amount', 'reason', 'original_text']
        df = df[columns]
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No requests submitted yet.")
except Exception as e:
    st.error(f"Error loading requests: {str(e)}")