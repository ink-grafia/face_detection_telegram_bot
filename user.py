class user:
    def __init__(self, chat_id: int):
        self.tries: int = 0
        self.chat_id = chat_id
        self.haarcascade = None