import streamlit as st
from typing import Dict, Optional

def render_voice_examples(language_option: str) -> None:
    """Render voice input examples based on language"""
    if language_option == "Arabic":
        st.markdown("""
        جرب أن تقول شيئاً مثل:
        > "أحتاج إلى طلب 500 ريال للمشروع 223 المسمى جامعة أبها لشراء بعض الأدوات"
        """)
    else:
        st.markdown("""
        Try saying something like:
        > "I need to request 500 riyals for project 223 named Abha University to buy some tools"
        """)

def handle_voice_input(voice_handler, language: str, memory_handler, gemini_processor) -> Optional[Dict]:
    """Handle voice input and processing"""
    with st.spinner("Checking microphone access..."):
        if not voice_handler.check_microphone_access():
            st.error("""
            Could not access microphone. Please ensure:
            1. You're using a secure (HTTPS) connection
            2. You've granted microphone permissions in your browser
            3. Your microphone is properly connected and working
            
            Try refreshing the page and allowing microphone access when prompted.
            """)
            return None
    
    with st.spinner("Listening... Please speak clearly"):
        voice_text = voice_handler.listen_for_voice(language)
        
        if voice_text.startswith("Error:"):
            st.error(voice_text)
            return None
        
        if voice_text.startswith("Could not"):
            st.warning(voice_text)
            return None
        
        st.success("Voice captured!")
        st.write("You said:", voice_text)
        
        # Add to memory
        memory_handler.add_interaction(voice_text)
        
        with st.spinner("Processing voice input..."):
            context = memory_handler.get_context()
            details = gemini_processor.extract_request_details(voice_text, context)
            
            if not details:
                st.error("Could not extract request details. Please try again or use manual input.")
                return None
            
            if 'translated_text' in details:
                st.info(f"Translated text: {details['translated_text']}")
            
            if details.get('missing_fields'):
                missing = ", ".join(details['missing_fields'])
                st.warning(f"Please provide the following missing information: {missing}")
            else:
                st.success("Voice input processed! Please verify the details below.")
            
            return details

def render_voice_input(voice_handler, language_option: str, language_mapping: Dict[str, str], 
                      memory_handler, gemini_processor) -> None:
    """Render the voice input section"""
    if not voice_handler.permission_granted:
        st.info("Microphone access is required for voice input. Click below to enable it.")
        if st.button("Enable Microphone Access"):
            if voice_handler.request_permissions():
                st.success("Microphone access granted! You can now use voice input.")
                st.rerun()
            else:
                st.error("""
                Could not access microphone. Please:
                1. Check if your browser blocks microphone access
                2. Allow microphone access in your browser settings
                3. Ensure your microphone is properly connected
                """)
    
    col1, col2, col3 = st.columns([3, 1, 1])
    
    with col1:
        render_voice_examples(language_option)
    
    with col2:
        if st.button("🎤 Start Voice Input"):
            details = handle_voice_input(
                voice_handler, 
                language_mapping[language_option],
                memory_handler,
                gemini_processor
            )
            if details:
                st.session_state['voice_details'] = details
    
    with col3:
        if st.button("🗑️ Clear Memory"):
            memory_handler.clear_memory()
            if 'voice_details' in st.session_state:
                del st.session_state['voice_details']
            st.success("Memory cleared!")