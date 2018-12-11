import json
import os
from requests import get, post, utils
from api_exceptions import NotLoggedInException


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

            for key, item in json_obj_user.iteritems():
                self[key] = item

        elif json_obj is not None:
            json_obj_user = json_obj["user"]
            for key, item in json_obj_user.iteritems():
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

            for i in xrange(0, len(items)):
                self.append(Post(json_obj=items[i]))

    def minPromotedId(self):
        return self.min("promoted")

    def maxPromotedId(self):
        return self.max("promoted")

    def sumPoints(self):
        sum = 0
        for post in self:
            sum += (post["up"]-post["down"])
        return sum


class Comments(ApiList):
    def __init__(self, json_str=""):
        super(Comments, self).__init__()

        if json_str != "":
            self.json = json.loads(json_str)
            items = self.json["comments"]

            for i in xrange(0, len(items)):
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

            for i in xrange(0, len(items)):
                self.append(Tag(json_obj=items[i]))


class TagAssignments(list):
    def __init__(self):
        super(TagAssignments, self).__init__()


class Api:
    def __init__(self, username="", password="", tmp_dir="./"):
        self.__password = password
        self.__username = username
        self.__login_cookie = None
        self.__current = -1

        self.tmp_dir = tmp_dir

        self.image_url = 'https://img.pr0gramm.com/'
        self.api_url = 'https://pr0gramm.com/api/'
        self.login_url = 'https://pr0gramm.com/api/user/login/'
        self.profile_comments = self.api_url + "profile/comments"
        self.profile_user = self.api_url + "profile/info"
        self.items_url = self.api_url + 'items/get'
        self.item_url = self.api_url + 'items/info'

        self.logged_in = False
        self.login()

    def __iter__(self):
        self.__current = Post(self.get_newest_image())["id"]
        return self

    def next(self):
        posts = Posts(self.get_items(self.__current))
        try:
            self.__current = posts.minId()
        except IndexError:
            raise StopIteration
        return posts

    @staticmethod
    def calculate_flag(sfw=True, nsfp=False, nsfw=False, nsfl=False):
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

    def get_items(self, item, flag=1, promoted=0, older=True, user=None):
        """
        Gets items from the pr0gramm api

        Parameters
        ----------
        :param item: int or str
                     requested post for example: 2525097
        :param flag: int or str
                     see api.md for details
                     call calculate_flag if you are not sure what flag to use
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

        get_type = 'get'
        if older:
            get_type = 'older'
        elif older is not None:
            get_type = 'newer'

        if user is not None:
            r = get(self.items_url,
                    params={get_type: item, 'flags': flag, 'promoted': promoted},
                    cookies=self.__login_cookie)
        else:
            r = get(self.items_url,
                    params={get_type: item, 'flags': flag, 'promoted': promoted, 'user': user},
                    cookies=self.__login_cookie)

        return r.content.decode('utf-8')

    def get_items_iterator(self, item=-1, flag=1, promoted=0, older=True, user=None):
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

            def next(self):
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

    def get_items_by_tag(self, tags, flag=1, older=-1, newer=-1, promoted=0, user=None):
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
                     call calculate_flag if you are not sure what flag to use
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

        tags = tags.replace(" ", "+")
        if older != -1:
            params = {'older': older, 'flags': flag, 'promoted': promoted, 'tags': tags}
        elif newer != -1:
            params = {'newer': newer, 'flags': flag, 'promoted': promoted, 'tags': tags}
        else:
            params = {'flags': flag, 'promoted': promoted, 'tags': tags}
        if user is not None:
            params["user"] = user

        r = get(self.items_url,
                params=params,
                cookies=self.__login_cookie)

        return r.content.decode('utf-8')

    def get_items_by_tag_iterator(self, tags, flag=1, older=-1, newer=-1, promoted=0, user=None):
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

            def next(self):
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

    def get_item_info(self, item, flag=1):
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
                     call calculate_flag if you are not sure what flag to use
        :return: str
                 json reply from api
        """

        r = get(self.item_url + "?itemId=" + str(item),
                params={'flags': flag},
                cookies=self.__login_cookie)
        return r.content.decode("utf-8")

    def get_user_info(self, user, flag=1):
        """
        Get user info from pr0gramm api
        For example:
          'https://pr0gramm.com/api/profile/info?name=itssme'

        Will return general info about a user

        Parameters
        ----------
        :param user: str
                     username for getting the user info
        :return: str
                 json reply from api
        """

        r = get(self.profile_user + "?user=" + user,
                params={'flags': flag},
                cookies=self.__login_cookie)
        return r.content.decode("utf-8")

    def get_user_comments(self, user, created=-1, older=True, flag=1):
        """
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
        :return: str
                 json reply from api
        """

        if older is None:
            r = get(self.profile_user + "?name=" + user,
                    params={'flags': flag},
                    cookies=self.__login_cookie)
        elif older:
            r = get(self.profile_comments + "?name=" + user,
                    params={'flags': flag, 'before': created},
                    cookies=self.__login_cookie)
        else:
            r = get(self.profile_comments + "?name=" + user,
                    params={'flags': flag, 'after': created},
                    cookies=self.__login_cookie)
        return r.content.decode("utf-8")

    def get_user_comments_iterator(self, user, created=-1, older=True, flag=1):
        class __user_comments_iterator:
            self.__current = -1

            def __init__(self, api, user, created=-1, older=True, flag=1):
                self.created = created
                self.api = api
                self.older = older
                self.user = user
                self.flag = flag

            def __iter__(self):
                if self.created == -1:
                    self.__current = Comments(self.api.get_user_comments(self.user, flag=self.flag,
                                                                         older=None))[0]["created"] + 1
                else:
                    self.__current = self.created

                return self

            def next(self):
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

    def get_newest_image(self, flag=1, promoted=0, user=None):
        """
        Gets the newest post either on /new (promoted=0) or /top (promoted=1)

        Parameters
        ----------
        :param flag: int or str
                     see api.md for details
                     call calculate_flag if you are not sure what flag to use
        :param promoted: int (0 or 1)
                         0 for all posts
                         1 for posts that have been in top
        :param user: str
                     get uploads from one specific user
        :return: str
                 json reply from api
        """
        if user is None:
            r = get(self.items_url,
                    params={'flags': flag, 'promoted': promoted},
                    cookies=self.__login_cookie)
        else:
            r = get(self.items_url,
                    params={'flags': flag, 'promoted': promoted, 'user': user},
                    cookies=self.__login_cookie)
        r = r.content.decode("utf8")
        r = json.dumps(json.loads(r)["items"][0])
        return r

    def get_inbox(self, older=0):
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
        r = ""
        if older <= 0:
            r = get("https://pr0gramm.com/api/inbox/all",
                    params={},
                    cookies=self.__login_cookie)
        else:
            r = get("https://pr0gramm.com/api/inbox/all",
                    params={'older': older},
                    cookies=self.__login_cookie)
        content = json.loads(r.content.decode("utf-8"))
        try:
            if content["code"] == 403:
                raise NotLoggedInException()
        except KeyError:
            pass
        return r.content.decode("utf-8")

    def get_messages_with_user(self, user, older=None):
        """
        Gets messages from a specific user

        Parameters
        ----------
        :param user: str
                     username from the other user
        :param older: int, str
                      messages older than this id will be returned
        :return: json
                 Returns messages from a specified user
        """
        r = ""
        if older is None:
            r = get("https://pr0gramm.com/api/inbox/messages",
                    params={"with": user},
                    cookies=self.__login_cookie)
        else:
            r = get("https://pr0gramm.com/api/inbox/messages",
                    params={"with": user, "older": id},
                    cookies=self.__login_cookie)

        content = json.loads(r.content.decode("utf-8"))
        try:
            if content["code"] == 403:
                raise NotLoggedInException()
        except KeyError:
            pass
        return r.content.decode("utf-8")

    def login(self):
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
                print "already logged in via cookie -> reading file"
                try:
                    with open(cookie_path, "r") as tmp_file:
                        self.__login_cookie = json.loads(tmp_file.read())
                    self.logged_in = True
                    return True
                except IOError:
                    print "Could not open cookie file %s", cookie_path

            print "Logging in via request."
            r = post(self.login_url, data={'name': self.__username, 'password': self.__password})

            if r.json()['success']:
                self.__login_cookie = r.cookies
                try:
                    with open(cookie_path, 'w') as temp_file:
                        temp_file.write(json.dumps(utils.dict_from_cookiejar(r.cookies)))
                except IOError:
                    print 'Could not write cookie file %s', cookie_path
                    self.logged_in = False
                    return False
            else:
                print 'Login not possible.'
                self.logged_in = False
                return False

            self.logged_in = True
            return True
