import base64
import json
import os
import time
import warnings
import webbrowser

import requests
from requests import get, post, utils
from pr0gramm.api_exceptions import NotLoggedInException, RateLimitReached
from urllib import parse


# TODO: implement logging


class ApiItem(dict):
    def __init__(self, json_str="", json_obj=None):
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
    def __init__(self, json_str="", json_obj=""):
        super(Post, self).__init__(json_str, json_obj)


class User(ApiItem):
    def __init__(self, json_str="", json_obj=None):
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


class Comment(ApiItem):
    def __init__(self, json_str="", json_obj="", comment_assignment=None):
        super(Comment, self).__init__(json_str, json_obj)
        self.comment_assignment = comment_assignment


class CommentAssignment:
    def __init__(self, post, comment):
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


class Tag(ApiItem):
    def __init__(self, json_str="", json_obj=""):
        """
        A tag from an post

        Parameters
        ----------
        :param json_str:
        :param json_obj:
        """
        super(Tag, self).__init__(json_str, json_obj)


class TagAssignment:
    def __init__(self, post, id, tag, confidence):
        """
        Links a tag to a post

        Parameters
        ----------
        :param post: int
                     id of an post
        :param id: int
                    id of an tag
        :param tag: int
                    id of an saved tag in the db
        :param confidence: float
                           confidence of an tag

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
    def __init__(self, json_str=""):
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
        super(Comments, self).__init__()

        if json_str != "":
            self.json = json.loads(json_str)
            items = self.json["comments"]

            for i in range(0, len(items)):
                self.append(Comment(json_obj=items[i]))


class CommentAssignments(list):
    def __init__(self):
        super(CommentAssignments, self).__init__()


class Tags(ApiList):
    def __init__(self, json_str=""):
        super(Tags, self).__init__()

        if json_str != "":
            self.json = json.loads(json_str)
            items = self.json["tags"]

            for i in range(0, len(items)):
                self.append(Tag(json_obj=items[i]))


class TagAssignments(list):
    def __init__(self):
        super(TagAssignments, self).__init__()


class Api:
    def __init__(self, username: str = "", password: str = "", tmp_dir: str = "./"):
        self.__password = password
        self.__username = username
        self.__login_cookie = None
        self.__current = -1

        self.tmp_dir = tmp_dir

        self.image_url = "https://img.pr0gramm.com/"
        self.api_url = "https://pr0gramm.com/api/"
        self.login_url = "https://pr0gramm.com/api/user/login/"
        self.profile_comments = self.api_url + "profile/comments"
        self.profile_user = self.api_url + "profile/info"
        self.items_url = self.api_url + "items/get"
        self.item_info_url = self.api_url + "items/info"
        self.inbox_all_url = self.api_url + "inbox/all"
        self.inbox_messages_url = self.api_url + "inbox/messages"

        self.logged_in = False
        self.login()

    def __iter__(self):
        self.__current = Post(self.get_newest_image())["id"]
        return self

    def __next__(self):
        posts = Posts(self.get_items(self.__current))
        try:
            self.__current = posts.minId()
        except IndexError:
            raise StopIteration
        return posts

    @staticmethod
    def calculate_flag(sfw: bool = True, nsfp: bool = False, nsfw: bool = False, nsfl: bool = False) -> int:
        """
        Used to calculate flags for the post requests

        sfw = 1
        nsfw = 2
        sfw + nsfw = 3
        nsfl = 4
        nsfw + nsfl = 6
        sfw + nsfw + nsfl = 7
        nsfp = 8
        sfw + nsfp = 9
        sfw + nsfp + nsfw = 11
        sfw + nsfp + nsfw + nsfl = 15

        Parameters
        ----------
        :param sfw: bool
        :param nsfp: bool
        :param nsfw: bool
        :param nsfl: bool
        :return: Calculated flag for requests
        """
        flag = 0

        flag += 1 if sfw else 0
        flag += 2 if nsfw else 0
        flag += 4 if nsfl else 0
        flag += 8 if nsfp and sfw else 0

        return flag

    @staticmethod
    def __raise_possible_exceptions(r: requests.models.Response):
        """
        Raises exceptions depending on http status code from request

        :param r: response returned by a request
        :return: None
        :raises NotLoggedInException if status code is 403 (forbidden)
        """
        if r.status_code == 403:
            raise NotLoggedInException()

    @staticmethod
    def __set_older_param(params, older, item):
        if older:
            params["older"] = item
        elif older is not None:
            params["newer"] = item

        return params

    def __items_request(self, params) -> str:
        """
        Makes a request to self.items_url

        :param params: dict
                       with url parameters
        :return: str
                 json reply from api
        """
        r = get(self.items_url,
                params=params,
                cookies=self.__login_cookie)

        self.__raise_possible_exceptions(r)

        return r.content.decode('utf-8')

    def get_items(self, item: int or str, flag: int or str = 1, promoted: int = 0,
                  older: bool or None = True, user: str = None) -> str:
        """
        Gets items from the pr0gramm api

        Parameters
        ----------
        :param item: int or str
                     requested post for example: 2525097
        :param flag: int or str
                     see api.md for details
                     call calculate_flag if you are not sure which flag to use
        :param promoted: int 0 or 1
                         0 for all posts
                         1 for posts that have been in top
        :param older: bool or None
                      True for 'older' posts than the item requested
                      False for 'newer' posts
                      None for 'get'
        :param user: str
                     get uploads from one specific user
        :return: str
                 json reply from api
        """

        params = {"flags": flag, "promoted": promoted}

        params = self.__set_older_param(params, older, item)

        if user is not None:
            params["user"] = user

        return self.__items_request(params)

    def get_items_iterator(self, item: int or str = -1, flag: int or str = 1, promoted: int = 0,
                           older: bool or None = True, user: str = None):
        class __items_iterator:
            self.__current = -1

            def __init__(self, api, item, flag=1, promoted=0, older=True, user=None):
                self.item = item
                self.api = api
                self.flag = flag
                self.older = older
                self.promoted = promoted
                self.user = user

            def __iter__(self):
                if self.item == -1:
                    self.__current = Post(self.api.get_newest_image(flag=self.flag, promoted=self.promoted,
                                                                    user=self.user))["id"]
                else:
                    self.__current = self.item

                return self

            def __next__(self):
                posts = Posts(self.api.get_items(self.__current, self.flag, self.promoted, self.older, self.user))
                if self.older:
                    try:
                        if self.promoted == 1:
                            self.__current = posts.minPromotedId()
                        else:
                            self.__current = posts.minId()
                    except IndexError:
                        raise StopIteration
                else:
                    try:
                        if self.promoted == 1:
                            self.__current = posts.maxPromotedId()
                        else:
                            self.__current = posts.maxId()
                    except IndexError:
                        raise StopIteration
                return posts

        return __items_iterator(self, item, flag, promoted, older, user)

    # this function will be removed in a future release and __get_items_by_tag will become this function
    def get_items_by_tag(self, *args, **kwargs):
        if "newer" in kwargs or ("older" in kwargs and type(kwargs["older"]) != bool):
            return self.__drep_get_items_by_tag(*args, **kwargs)
        return self.__get_items_by_tag(*args, **kwargs)

    def __drep_get_items_by_tag(self, tags: str, flag: int or str = 1, older: int = -1, newer: int = -1,
                                promoted: int = 0, user: str = None) -> str:
        """
        Gets items with a specific tag from the pr0gramm api

        Parameters
        ----------
        :param tags: str
                     Search posts by tags
                     Example: 'schmuserkadser blus'
                               Will return all posts with the tags
                               'schmuserkadser' and 'blus'
        :param flag: int or str
                     see api.md for details
                     call calculate_flag if you are not sure which flag to use
        :param older: int
                      Specifies the first post that will be returned from the api
                      For example: older=2525097 tags='schmuserkadser' will get
                                   the post '2525097' and all posts after that with the specified tag
        :param newer: int
                      Specifies the first post that will be returned from the api
                        For example: older=2525097 tags='schmuserkadser' will get
                                   the post '2525097' and all posts newer than '2525097' with the specified tag
        :param promoted: int 0 or 1
                         0 for all posts
                         1 for posts that have been in top
        :param user: str
                     get uploads from one specific user
        :return: str
                 json reply from api
        """

        warnings.warn(
            "passing 'newer' to get_items_by_tag is deprecated, instead pass 'older' as a boolean and pass an 'item' "
            "as id",
            DeprecationWarning
        )

        #tags = tags.replace(" ", "+")
        params = {'flags': flag, 'promoted': promoted, 'tags': tags}

        if older != -1:
            params['older'] = older
        elif newer != -1:
            params['newer'] = newer

        if user is not None:
            params["user"] = user

        return self.__items_request(params)

    def __get_items_by_tag(self, tags: str, flag: int = 1, item: int = None, older: bool or None = True,
                           promoted: int = 0, user: str = None) -> str:
        """
        Gets items with a specific tag from the pr0gramm api

        Parameters
        ----------
        :param tags: str
                     Search posts by tags
                     Example: 'schmuserkadser blus'
                               Will return all posts with the tags
                               'schmuserkadser' and 'blus'
        :param flag: int
                     see api.md for details
                     call calculate_flag if you are not sure which flag to use
        :param item: int or str
                     requested post for example: 2525097
        :param older: bool or None
                      True for 'older' posts than the item requested
                      False for 'newer' posts
                      None for 'get'
        :param promoted: int 0 or 1
                         0 for all posts
                         1 for posts that have been in top
        :param user: str
                     get uploads from one specific user
        :return: str
                 json reply from api
        """

        #tags = tags.replace(" ", "+")
        params = {"flags": flag, "promoted": promoted, "tags": tags}

        params = self.__set_older_param(params, older, item)

        if user is not None:
            params["user"] = user

        return self.__items_request(params)

    def get_items_by_tag_iterator(self, tags: str, flag: int or str = 1, older: int = -1, newer: int = -1,
                                  promoted: int = 0, user: str = None):
        class __items_tag_iterator:
            self.__current = -1

            def __init__(self, tags, api, flag=1, older=0, promoted=0, user=None):
                self.tags = tags
                self.api = api
                self.flag = flag
                self.older = older
                self.newer = newer
                self.promoted = promoted
                self.user = user

            def __iter__(self):
                if older != -1:
                    self.__current = older
                elif newer != -1:
                    self.__current = newer
                else:
                    self.__current = Post(self.api.get_items_by_tag(self.tags, self.flag, self.older, self.promoted,
                                                                    self.user))
                    self.older = 1

                return self

            def __next__(self):
                posts = Posts(self.api.get_items_by_tag(self.tags, flag=self.flag, newer=self.__current,
                                                        promoted=self.promoted, user=self.user))
                if older != -1:
                    try:
                        if self.promoted == 1:
                            self.__current = posts.minPromotedId()
                        else:
                            self.__current = posts.minId()
                    except IndexError:
                        raise StopIteration
                else:
                    try:
                        if self.promoted == 1:
                            self.__current = posts.maxPromotedId()
                        else:
                            self.__current = posts.maxId()
                    except IndexError:
                        raise StopIteration
                return posts

        return __items_tag_iterator(tags, self, flag, older, promoted, user)

    def get_item_info(self, item: int or str, flag: int or str = 1) -> str:
        """
        Get item info from pr0gramm api
        For example:
          'https://pr0gramm.com/api/items/info?itemId=2525097'

        Will return all comments and tags for the specified post

        Parameters
        ----------
        :param item: int or str
                     requested post for example: 2525097
        :param flag: int or str
                     see api.md for details
                     call calculate_flag if you are not sure which flag to use
        :return: str
                 json reply from api
        """

        params = {"itemId": item, "flags": flag}

        r = get(self.item_info_url,
                params=params,
                cookies=self.__login_cookie)

        self.__raise_possible_exceptions(r)

        return r.content.decode('utf-8')

    def get_collection_items(self, collection: str = "favoriten", user: str = None, item: int = None,
                             flag: int or str = 9,
                             older: bool or None = True) -> str:
        """
        Get a collection from pr0gramm api
        For example:
            'https://pr0gramm.com/api/items/get?flags=9&user=itssme&collection=favoriten&self=true'

        Parameters
        ----------
        :param collection: Name of the collection
        :param user: Name of the user the collection belongs to
        :param item: Requested post id, sets the start for the fetched posts
        :param older: bool or None
                      True for 'older' posts than the item requested
                      False for 'newer' posts
                      None for 'get'
        :param flag: int or str
                     see api.md for details
                     call calculate_flag if you are not sure which flag to use
        :return: str
                 json reply from api
        """

        if user is None:
            user = self.__username

        params = {"flags": flag, "user": user, "collection": collection}

        self.__set_older_param(params, older, item)

        return self.__items_request(params)

    def get_collection_items_iterator(self, collection: str = "favoriten", user: str = "", item: int or str = None,
                                      flag: int or str = 9, older: bool or None = True):
        class __collection_items_iterator:
            self.__current = -1

            def __init__(self, api, item, collection: str = "favoriten", flag=1, older=True, user=None):
                self.item = item
                self.api = api
                self.collection = collection
                self.flag = flag
                self.older = older
                self.user = user

            def __iter__(self):
                if self.item is None:
                    self.__current = Posts(self.api.get_collection_items(collection, user, item, flag, older)).maxId()
                else:
                    self.__current = self.item

                return self

            def __next__(self):
                posts = Posts(self.api.get_collection_items(collection, user, self.__current, flag, older))
                if self.older:
                    try:
                        self.__current = posts.minId()
                    except IndexError:
                        raise StopIteration
                else:
                    try:
                        self.__current = posts.maxId()
                    except IndexError:
                        raise StopIteration
                return posts

        return __collection_items_iterator(self, item, collection, flag, older, user)

    def get_user_info(self, user: str, flag: int or str = 1) -> str:
        """
        Get user info from pr0gramm api
        For example:
          'https://pr0gramm.com/api/profile/info?name=itssme'

        Will return general info about a user

        Parameters
        ----------
        :param user: str
                     username for getting the user info
        :param flag: int or str
                     see api.md for details
                     call calculate_flag if you are not sure which flag to use
        :return: str
                 json reply from api
        """

        r = get(self.profile_user + "?user=" + user,
                params={'flags': flag},
                cookies=self.__login_cookie)

        self.__raise_possible_exceptions(r)

        return r.content.decode("utf-8")

    def get_user_comments(self, user: str, created: int = -1, older: bool = True, flag: int = 1) -> str:
        """
        login required
        Get comments
        For example:
          'https://pr0gramm.com/api/profile/comments?name=itssme&before=1528718127'

        Parameters
        ----------
        :param user: str
                     get uploads from one specific user
        :param created: int
                        Date of the comment
        :param older bool
                     None gets the newest comment
                     True gets all comments older than item
                     False gets all comments newer than item
        :param flag: int or str
                     see api.md for details
                     call calculate_flag if you are not sure which flag to use
        :return: str
                 json reply from api
        """

        params = {"name": user, "flags": flag}

        if older:
            params["before"] = created
        elif not older:
            params["after"] = created

        r = get(self.profile_comments,
                params=params,
                cookies=self.__login_cookie)

        self.__raise_possible_exceptions(r)

        return r.content.decode("utf-8")

    def get_user_comments_iterator(self, user: str, created: int = -1, older: bool = True, flag: int or str = 1):
        class __user_comments_iterator:
            self.__current = -1

            def __init__(self, api, user, created=-1, older=True, flag=1):
                self.created = created
                if self.created == -1 and older:
                    self.created = time.time()
                self.api = api
                self.older = older
                self.user = user
                self.flag = flag

            def __iter__(self):
                if self.created == -1:
                    try:
                        self.__current = Comments(self.api.get_user_comments(self.user, flag=self.flag,
                                                                             older=None))[0]["created"] + 1
                    except IndexError:
                        raise NotLoggedInException
                else:
                    self.__current = self.created

                return self

            def __next__(self):
                comments = Comments(self.api.get_user_comments(self.user, self.__current, self.older, self.flag))
                if self.older:
                    try:
                        self.__current = comments.minDate()
                    except IndexError:
                        raise StopIteration
                else:
                    try:
                        self.__current = comments.maxDate()
                    except IndexError:
                        raise StopIteration
                return comments

        return __user_comments_iterator(self, user, created, older, flag)

    def get_newest_image(self, flag: int = 1, promoted: int = 0, user: str = None) -> str:
        """
        Gets the newest post either on /new (promoted=0) or /top (promoted=1)

        Parameters
        ----------
        :param flag: int or str
                     see api.md for details
                     call calculate_flag if you are not sure which flag to use
        :param promoted: int (0 or 1)
                         0 for all posts
                         1 for posts that have been in top
        :param user: str
                     get uploads from one specific user
        :return: str
                 json reply from api
        """

        params = {"flags": flag, "promoted": promoted}

        if user is not None:
            params["user"] = user

        r = self.__items_request(params)
        r = json.dumps(json.loads(r)["items"][0])
        return r

    def get_inbox(self, older: int = -1) -> str:
        """
        login required
        Gets messages from inbox

        Parameters
        ----------
        :param older: int
                      gets the next messages after 'older'
        :return: json
                 Returns messages
        """

        params = {}

        if older != -1:
            params["older"] = older

        r = get(self.inbox_all_url,
                params=params,
                cookies=self.__login_cookie)

        self.__raise_possible_exceptions(r)

        return r.content.decode("utf-8")

    def get_messages_with_user(self, user: str, older: int = None) -> str:
        """
        Gets messages from a specific user

        Parameters
        ----------
        :param user: str
                     username from the other user
        :param older: int
                      messages older than this id will be returned
        :return: str
                 Returns messages from a specified user
        """

        params = {"with": user}

        if older is not None:
            params["older"] = older

        r = get(self.inbox_messages_url,
                params=params,
                cookies=self.__login_cookie)

        self.__raise_possible_exceptions(r)

        return r.content.decode("utf-8")

    def vote_post(self, id: int, vote: int) -> bool:
        """
        Vote for a post with a specific id

        Parameters
        ----------
        :param id: int or str
                   post id that will be voted for
        :param vote: int
                     type of vote:
                        -1 = -
                        0 = unvote (nothing)
                        1 = +
                        2 = add to favorite
        :return: bool
                 returns true if the vote was successful else false
        :raises: NotLoggedInException if user is not logged in
        """
        if self.logged_in:
            nonce = json.loads(parse.unquote(self.__login_cookie["me"]))["id"][0:16]
            r = post(self.api_url + "items/vote",
                     data={"id": id, "vote": vote, '_nonce': nonce},
                     cookies=self.__login_cookie)
            return r.status_code == 200
        else:
            raise NotLoggedInException()

    def vote_comment(self, id: int or str, vote: int or str) -> bool:
        """
        Vote for a comment with a specific id

        Parameters
        ----------
        :param id: int or str
                   comment id that will be voted for
        :param vote: int or str
                     type of vote:
                        -1 = -
                        0 = unvote (nothing)
                        1 = +
                        2 = add to favorite
        :return: bool
                 returns true if the vote was successful else false
        :raises: NotLoggedInException if user is not logged in
        """
        if self.logged_in:
            nonce = json.loads(parse.unquote(self.__login_cookie["me"]))["id"][0:16]
            r = post(self.api_url + "comments/vote",
                     data={"id": id, "vote": vote, '_nonce': nonce},
                     cookies=self.__login_cookie)
            return r.status_code == 200
        else:
            raise NotLoggedInException()

    def vote_tag(self, id: int, vote: int) -> bool:
        """
        Vote for a tag with a specific id

        Parameters
        ----------
        :param id: int or str
                   tag id that will be voted for
        :param vote: int or str
                     type of vote:
                        -1 = -
                        0 = unvote (nothing)
                        1 = +
        :return: bool
                 returns true if the vote was successful else false
        :raises: NotLoggedInException if user is not logged in
        """
        if self.logged_in:
            nonce = json.loads(parse.unquote(self.__login_cookie["me"]))["id"][0:16]
            r = post(self.api_url + "tags/vote",
                     data={"id": id, "vote": vote, '_nonce': nonce},
                     cookies=self.__login_cookie)
            return r.status_code == 200
        else:
            raise NotLoggedInException()

    def login(self) -> bool:
        """
        Logs in with a specific account

        Parameters
        ----------
        :return: bool
                 True if login was successful
                 False if login failed
        """

        if self.__password != "" and self.__username != "":
            cookie_path = os.path.join(self.tmp_dir, "cookie.json")

            # TODO re-login after some time -> delete cookie
            if os.path.isfile(cookie_path):
                print("already logged in via cookie -> reading file")
                try:
                    with open(cookie_path, "r") as tmp_file:
                        self.__login_cookie = json.loads(tmp_file.read())
                    self.logged_in = True
                    return True
                except IOError:
                    print("Could not open cookie file %s", cookie_path)

            r = ""
            logged_in = False
            while not logged_in:
                print("Trying to login in via request.")

                captcha_req = get(self.api_url + "user/captcha")
                token = captcha_req.json()["token"]
                image = captcha_req.json()["captcha"].split("base64,")[-1]
                write_img = open("captcha.png", "wb")
                write_img.write(base64.b64decode(image))
                write_img.close()

                try:
                    webbrowser.open("captcha.png")
                    print("Your webbrowser or image viewer should open and display the image")
                    print("write the correct content of the captcha into the command line:")
                except:
                    print("Could not open image through xdg-open")
                    print("Open the image 'captcha.png' and write the correct content into the command line:")

                captcha = input("?: ")

                r = post(self.login_url, data={'name': self.__username, 'password': self.__password,
                                               'captcha': captcha, 'token': token})

                if not r.json()["success"]:
                    print("There was an error logging in: " + str(r.json()["error"]))
                else:
                    logged_in = True

            try:
                if r.json()["code"] == 429:  # rate limit reached (tried to log in too often)
                    raise RateLimitReached
            except KeyError:
                pass

            if r.json()['success']:
                self.__login_cookie = r.cookies
                try:
                    with open(cookie_path, 'w') as temp_file:
                        temp_file.write(json.dumps(utils.dict_from_cookiejar(r.cookies)))
                except IOError:
                    print('Could not write cookie file %s', cookie_path)
                    self.logged_in = False
                    return False
            else:
                print('Login not possible.')
                self.logged_in = False
                return False

            print("Successfully logged in and written cookie file")
            self.logged_in = True
            return True
