import speech_recognition as sr
import platform
from typing import Optional

class VoiceHandler:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = 4000
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.pause_threshold = 0.8
        self.permission_granted = False
    
    def check_microphone_access(self) -> bool:
        """Check if microphone is accessible"""
        try:
            with sr.Microphone() as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.1)
                return True
        except (OSError, AttributeError, sr.RequestError):
            return False
    
    def request_permissions(self) -> bool:
        """Request microphone permissions from the browser"""
        try:
            if self.check_microphone_access():
                self.permission_granted = True
                return True
            return False
        except Exception:
            return False
    
    def listen_for_voice(self, language: str = "mixed") -> str:
        """
        Listen for voice input in specified language.
        language can be: 
        - "ar-SA" for Arabic
        - "en-US" for English
        - "mixed" for both Arabic and English
        """
        if not self.permission_granted and not self.request_permissions():
            return "Error: Please grant microphone permissions to use voice input."
        
        try:
            with sr.Microphone() as source:
                print("Adjusting for ambient noise...")
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
                print("Listening...")
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=10)
                print("Processing speech...")
                
                return self._process_audio(audio, language)
                    
        except sr.RequestError as e:
            return f"Could not request results from speech service: {str(e)}"
        except sr.UnknownValueError:
            return "Could not understand audio. Please speak clearly and try again."
        except sr.WaitTimeoutError:
            return "Listening timed out. Please try again."
        except Exception as e:
            return f"Error: {str(e)}"
    
    def _process_audio(self, audio, language: str) -> str:
        """Process audio input and convert to text"""
        if language in ["ar-SA", "mixed"]:
            try:
                return self.recognizer.recognize_google(audio, language="ar-SA")
            except sr.UnknownValueError:
                if language == "mixed":
                    return self.recognizer.recognize_google(audio, language="en-US")
                raise
        return self.recognizer.recognize_google(audio, language="en-US")