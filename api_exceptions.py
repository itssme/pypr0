class NotLoggedInException(Exception):
    def __init___(self):
        Exception.__init__(self, "You have to be logged in to do this")
