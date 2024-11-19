class InvalidSession(BaseException):
    pass

class ForbiddenSession(BaseException):
    def __init__(self, session_name: str):
        self.session_name = session_name
        super().__init__(f"Session {session_name} got 403 Forbidden error")
