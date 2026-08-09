class ApiError(Exception):
    def __init__(self, status_code: int, code: str, safe_message: str) -> None:
        super().__init__(safe_message)
        self.status_code = status_code
        self.code = code
        self.safe_message = safe_message
