import os
import sqlite3
import threading
import uuid
from multiprocessing import JoinableQueue


class Manager(threading.Thread):
    def __init__(self, file_name):
        threading.Thread.__init__(self)
        self.daemon = True

        self.file_name = file_name
        self.sql_queue = JoinableQueue()
        self.__results = {}

        if not os.path.isfile(file_name):
            connection = sqlite3.connect(file_name)
            cur = connection.cursor()

            sql = open("pr0gramm_sqlite.sql")
            sql_str = sql.read()
            sql.close()
            cur.executescript(sql_str)

            cur.close()
            connection.commit()
            connection.close()

        self.sql_connection = sqlite3.connect(':memory:', check_same_thread=False, detect_types=sqlite3.PARSE_DECLTYPES)
        old_db = sqlite3.connect(file_name)
        query = "".join(line for line in old_db.iterdump())
        self.sql_connection.executescript(query)

        self.sql_cursor = self.sql_connection.cursor()

        self.start()
        self.thread_running = True

    # safe in-memory-database to disk
    def safe_to_disk(self):
        if os.path.isfile(self.file_name):
            os.remove(self.file_name)
        new_db = sqlite3.connect(self.file_name)
        query = "".join(line for line in self.sql_connection.iterdump())
        new_db.executescript(query)
        new_db.close()

    def insert(self, *args):
        for i in range(0, len(args)):
            type = args[i].__class__.__name__
            if type == 'Post':
                self.insert_post(args[i])
            elif type == 'Posts':
                self.insert_posts(args[i])
            elif type == 'User':
                self.insert_user(args[i])
            elif type == 'Comment':
                print("comment")
                self.insert_comment(args[i])
            elif type == 'Tag':
                self.insert_tag(args[i])
            elif type == 'CommentAssignment':
                self.insert_comment_assignment(args[i])
            elif type == "TagAssignment":
                self.insert_tag_assignment(args[i])

    def insert_post(self, post):
        statement = "insert into posts values(" + "".join(["?," for key, value in post.iteritems()])[:-1] + ")"
        data = [post["id"], post["user"], post["promoted"], post["up"], post["down"], post["created"], post["image"],
                post["thumb"], post["fullsize"], post["width"], post["height"], post["audio"], post["source"],
                post["flags"], post["mark"]]
        self.sql_queue.put((statement, data, None))

    def insert_posts(self, posts):
        for post in posts:
            self.insert_post(post)

    def insert_user(self, user):
        pass

    def insert_comment(self, comment):
        statement = "insert into comments values(" + "".join(["?," for key, value in comment.iteritems()])[:-1] + ")"
        data = [comment["id"], comment["content"], comment["name"], comment["parent"], comment["created"],
                comment["up"], comment["down"], comment["confidence"], comment["mark"]]
        self.sql_queue.put((statement, data, None))

    def insert_tag(self, tag):
        statement = "insert into tags values(" + "".join(["?," for key, value in tag.iteritems()])[:-1] + ")"
        data = [tag["id"], tag["confidence"], tag["tag"]]
        self.sql_queue.put((statement, data, None))

    def insert_comment_assignment(self, comment_assignment):
        pass

    def insert_tag_assignment(self, tag_assignment):
        pass

    def manual_command(self, statement, values=[], wait=False):
        token = uuid.uuid4() if wait else None
        self.sql_queue.put((statement, values, token))
        delay = .001

        while wait:
            if token in self.__results:
                result = self.__results[token]
                del self.__results[token]
                return result

            if delay < 8:
                delay += delay

    def run(self):
        for query, values, token in iter(self.sql_queue.get, None):
            print("Executing: " + query + "\n" + str(values) + "\nwith token: " + str(token))
            self.sql_cursor.execute(query, values)
            self.__results[token] = self.sql_cursor.fetchall()
            self.sql_queue.task_done()
