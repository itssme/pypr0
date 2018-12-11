import os
import sqlite3
import threading
import uuid
from multiprocessing import JoinableQueue
from time import sleep


class Manager(threading.Thread):
    def __init__(self, file_name, in_memory=False, sql_file=None):
        threading.Thread.__init__(self)
        self.daemon = True

        self.in_memory = in_memory
        self.file_name = file_name
        self.sql_queue = JoinableQueue()
        self.__results = {}

        if not os.path.isfile(file_name):
            connection = sqlite3.connect(file_name)
            cur = connection.cursor()

            _SQLFILE = ""
            if sql_file is None:
                _HERE = os.path.dirname(os.path.abspath(__file__))
                _SQLFILE = os.path.join(_HERE, "pr0gramm_sqlite.sql")
            else:
                _SQLFILE = sql_file

            sql = open(_SQLFILE)

            sql_str = sql.read()
            sql.close()
            cur.executescript(sql_str)

            cur.close()
            connection.commit()
            connection.close()

        if self.in_memory:
            self.sql_connection = sqlite3.connect(':memory:', check_same_thread=False,
                                                  detect_types=sqlite3.PARSE_DECLTYPES)
            old_db = sqlite3.connect(file_name)
            query = ""
            put_at_end = ""

            # we have to do this because there is a bug in the sqlite.iterdump function when using autoincrement
            for line in old_db.iterdump():
                if '"sqlite_sequence"' in line:
                    put_at_end += line
                else:
                    query += line

            query += put_at_end
            # query = "".join(line for line in old_db.iterdump())
            self.sql_connection.executescript(query)
        else:
            self.sql_connection = sqlite3.connect(file_name, check_same_thread=False,
                                                  detect_types=sqlite3.PARSE_DECLTYPES)

        self.sql_cursor = self.sql_connection.cursor()

        self.start()
        self.thread_running = True

    def safe_to_disk(self):
        # safe in-memory-database to disk
        if self.in_memory:
            self.sql_connection.commit()
            if os.path.isfile(self.file_name):
                os.remove(self.file_name)
            new_db = sqlite3.connect(self.file_name)
            query = "".join(line for line in self.sql_connection.iterdump())
            new_db.executescript(query)
            new_db.close()
        else:
            self.sql_connection.commit()

    def insert(self, *args):
        for i in xrange(0, len(args)):
            type = args[i].__class__.__name__
            if type == 'Post':
                self.insert_post(args[i])
            elif type == 'Posts':
                self.insert_posts(args[i])
            elif type == 'User':
                self.insert_user(args[i])
            elif type == 'Comment':
                self.insert_comment(args[i])
            elif type == "Comments":
                self.insert_comments(args[i])
            elif type == 'Tag':
                self.insert_tag(args[i])
            elif type == "Tags":
                self.insert_tags(args[i])
            elif type == 'CommentAssignment':
                self.insert_comment_assignment(args[i])
            elif type == 'CommentAssignments':
                self.insert_comment_assignments(args[i])
            elif type == "TagAssignment":
                self.insert_tag_assignment(args[i])
            elif type == "TagAssignments":
                self.insert_tag_assignments(args[i])

    def insert_post(self, post):
        statement = "insert into posts values(" + "".join(["?," for key, value in post.iteritems()])[:-1] + ")"
        data = [post["id"], post["user"], post["promoted"], post["up"], post["down"], post["created"], post["image"],
                post["thumb"], post["fullsize"], post["width"], post["height"], post["audio"], post["source"],
                post["flags"], post["mark"], post["deleted"]]
        self.sql_queue.put((statement, data, None))

    def insert_posts(self, posts):
        for post in posts:
            self.insert_post(post)

    def insert_user(self, user):
        statement = "insert into posts values(" + "".join(["?," for key, value in user.iteritems()])[:-1] + ")"
        data = [user["name"], user["id"], user["registered"], user["admin"], user["banned"], user["bannedUntil"],
                user["mark"], user["score"], user["tags"], user["likes"], user["comments"], user["followers"]]
        self.sql_queue.put((statement, data, None))

    def insert_comment(self, comment):
        statement = "insert into comments values(" + "".join(["?," for key, value in comment.iteritems()])[:-1] + ")"
        data = [comment["id"], comment["content"], comment["name"], comment["parent"], comment["created"],
                comment["up"], comment["down"], comment["confidence"], comment["mark"]]
        self.sql_queue.put((statement, data, None))

    def insert_comments(self, comments):
        for comment in comments:
            self.insert_comment(comment)

    def insert_tag(self, tag):
        statement = "insert into tags values(?, ?)"
        data = [None, tag["tag"]]
        self.sql_queue.put((statement, data, None))

    def insert_tags(self, tags):
        for tag in tags:
            self.insert_tag(tag)

    def insert_comment_assignment(self, comment_assignment):
        statement = "insert into comment_assignments values(?, ?)"
        data = [comment_assignment.post, comment_assignment.comment]
        self.sql_queue.put((statement, data, None))

    def insert_comment_assignments(self, comment_assignments):
        for comment_assignment in comment_assignments:
            self.insert_comment_assignment(comment_assignment)

    def insert_tag_assignment(self, tag_assignment):
        statement = "insert into tag_assignments values(?, ?, ?, ?)"
        data = [tag_assignment.post, tag_assignment.id, tag_assignment.tag, tag_assignment.confidence]
        self.sql_queue.put((statement, data, None))

    def insert_tag_assignments(self, tag_assignments):
        for tag_assignment in tag_assignments:
            self.insert_tag_assignment(tag_assignment)

    def insert_tag_assignments(self, tag_assignments):
        for tag_assignment in tag_assignments:
            self.insert_tag_assignment(tag_assignment)

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
            sleep(delay)

    def run(self):
        try:
            for query, values, token in iter(self.sql_queue.get, None):
                try:
                    self.sql_cursor.execute(query, values)
                    self.__results[token] = self.sql_cursor.fetchall()
                    self.sql_queue.task_done()
                except Exception as e:
                    print(str(e))
        except EOFError:
            self.thread_running = False
