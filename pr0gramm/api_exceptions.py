class NotLoggedInException(Exception):
    def __init___(self):
        Exception.__init__(self, "You have to be logged in to do this")


class RateLimitReached(Exception):
    def __init___(self):
        Exception.__init__(self, "You tried to log in too often")
