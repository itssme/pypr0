# encoding: utf-8

import json


class ApiItem(dict):
    def __init__(self, json_str: str = "", json_obj: dict = None):
        if json_str:
            super(ApiItem, self).__init__(json.loads(json_str))

        elif json_obj is not None:
            super(ApiItem, self).__init__(json_obj)

    # override print and to str because json uses " and not ' to represent strings
    def __repr__(self):
        return self.to_json()

    def __str__(self):
        return self.to_json()

    def to_json(self):
        return json.dumps(self)


class Post(ApiItem):
    def __init__(self, json_str: str = "", json_obj: dict = None):
        """
        A post in pr0gramm.com

        Parameters
        ----------
        :param json_str: str
                         Json str as returned by api
        :param json_obj: dict
                         Json object, parsed dictionary from json api response
        """
        super(Post, self).__init__(json_str, json_obj)


class User(ApiItem):
    def __init__(self, json_str: str = "", json_obj: dict = None):
        """
        A user profile of pr0gramm.com

        Parameters
        ----------
        :param json_str: str
                         Json str as returned by api
        :param json_obj: dict
                         Json object, parsed dictionary from json api response
        """
        super(User, self).__init__()

        if json_str:
            json_obj = json.loads(json_str)
            json_obj_user = json_obj["user"]

            for key, item in json_obj_user.items():
                self[key] = item

        elif json_obj is not None:
            json_obj_user = json_obj["user"]
            for key, item in json_obj_user.items():
                self[key] = item

        self["tagCount"] = json_obj["tagCount"]
        self["likeCount"] = json_obj["likeCount"]
        self["commentCount"] = json_obj["commentCount"]
        self["followCount"] = json_obj["followCount"]


class CommentAssignment:
    def __init__(self, post: int, comment: int):
        """
        Links a comment to a post

        Parameters
        ----------
        :param post: int
                     id of an post
        :param comment: int
                        id of an comment
        """
        self.post = post
        self.comment = comment


class Comment(ApiItem):
    def __init__(self, json_str: str = "", json_obj: dict = None, comment_assignment: CommentAssignment = None):
        """
        A comment from a post

        Parameters
        ----------
        :param json_str: str
                         Json str as returned by api
        :param json_obj: dict
                         Json object, parsed dictionary from json api response
        :param comment_assignment: :CommentAssignment
                                   Assigns this comment to a post
        """
        super(Comment, self).__init__(json_str, json_obj)
        self.comment_assignment = comment_assignment


class Tag(ApiItem):
    def __init__(self, json_str: str = "", json_obj: dict = None):
        """
        A tag from a post

        Parameters
        ----------
        :param json_str: str
                         Json str as returned by api
        :param json_obj: dict
                         Json object, parsed dictionary from json api response
        """
        super(Tag, self).__init__(json_str, json_obj)


class TagAssignment:
    def __init__(self, post: int, id: int, tag: int, confidence: float):
        """
        Links a tag to a post

        Parameters
        ----------
        :param post: int
                     id of a post
        :param id: int
                    id of a tag
        :param tag: int
                    id of a saved tag in the db
        :param confidence: float
                           confidence of a tag

        """
        self.post = post
        self.id = id
        self.tag = tag
        self.confidence = confidence


class ApiList(list):
    def __init__(self):
        super(ApiList, self).__init__()

    def min(self, attr):
        min = self[0][attr]
        for elem in self:
            if min > elem[attr]:
                min = elem[attr]
        return min

    def max(self, attr):
        max = self[0][attr]
        for elem in self:
            if max < elem[attr]:
                max = elem[attr]
        return max

    def minId(self):
        return self.min("id")

    def maxId(self):
        return self.max("id")

    def minDate(self):
        return self.min("created")

    def maxDate(self):
        return self.max("created")


class Posts(ApiList):
    def __init__(self, json_str: str = ""):
        """
        A list of multiple :Post objects

        Parameters
        ----------
        :param json_str: str
                         Json str containing multiple posts
                         Example:
                            api.get_items_iterator(...) returns a :Posts object
        """
        super(Posts, self).__init__()

        if json_str != "":
            self.json = json.loads(json_str)
            items = self.json["items"]

            for i in range(0, len(items)):
                self.append(Post(json_obj=items[i]))

    def minPromotedId(self):
        return self.min("promoted")

    def maxPromotedId(self):
        return self.max("promoted")

    def sumPoints(self):
        sum = 0
        for post in self:
            sum += (post["up"] - post["down"])
        return sum


class Comments(ApiList):
    def __init__(self, json_str=""):
        """
        A list of multiple :Comment objects

        Parameters
        ----------
        :param json_str: str
                         Json str containing multiple comments
                         Example:
                            api.get_user_comments_iterator(...) returns a :Comments object
        """
        super(Comments, self).__init__()

        if json_str != "":
            self.json = json.loads(json_str)
            items = self.json["comments"]

            for i in range(0, len(items)):
                self.append(Comment(json_obj=items[i]))


class CommentAssignments(list):
    def __init__(self):
        """
        A list of multiple :CommentAssignment objects
        """
        super(CommentAssignments, self).__init__()


class Tags(ApiList):
    def __init__(self, json_str=""):
        """
        A list of multiple :Tag objects

        Parameters
        ----------
        :param json_str: str
                         Json str containing multiple tags
        """
        super(Tags, self).__init__()

        if json_str != "":
            self.json = json.loads(json_str)
            items = self.json["tags"]

            for i in range(0, len(items)):
                self.append(Tag(json_obj=items[i]))


class TagAssignments(list):
    def __init__(self):
        """
        A list of multiple :TagAssignment objects
        """
        super(TagAssignments, self).__init__()
