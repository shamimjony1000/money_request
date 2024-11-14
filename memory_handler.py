class MemoryHandler:
    def __init__(self):
        self.conversation_history = []
        self.max_history = 5  # Keep last 5 interactions
    
    def add_interaction(self, text):
        self.conversation_history.append(text)
        if len(self.conversation_history) > self.max_history:
            self.conversation_history.pop(0)
    
    def get_context(self):
        return " ".join(self.conversation_history)
    
    def clear_memory(self):
        self.conversation_history = []