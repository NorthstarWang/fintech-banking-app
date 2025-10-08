class SessionManager:
    def __init__(self):
        self.session = None

    def create_session(self, session: str):
        self.session = session

    def set_session(self, session: str):
        self.session = session

    def get_session(self):
        return self.session

    def clear_session(self, session_id: str):
        self.session = None

session_manager = SessionManager()
