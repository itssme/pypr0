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

    def json_to_object(self, json_str="", json_obj=""):
        if json_obj == "":
            json_obj = json.loads(json_str)

        for key, value in self:
            self[key] = json_obj[key]

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
        self.post = post
        self.comment = comment


class Tag(ApiItem):
    def __init__(self, json_str="", json_obj="", tag_assignment=None):
        super(Tag, self).__init__(json_str, json_obj)
        self.tag_assignment = tag_assignment


class TagAssignment:
    def __init__(self, post, tag):
        self.post = post
        self.tag = tag


class Posts(list):
    def __init__(self, json_str=""):
        super(Posts, self).__init__()

        if json_str != "":
            self.json = json.loads(json_str)
            items = self.json["items"]

            for i in range(0, len(items)):
                self.append(Post(json_obj=items[i]))

    def minId(self):
        min = self[0]["id"]
        for elem in self:
            if min > elem["id"]:
                min = elem["id"]
        return min

    def maxId(self):
        max = self[0]["id"]
        for elem in self:
            if max < elem["id"]:
                max = elem["id"]
        return max


class Api:
    def __init__(self, username="", password="", tmp_dir="./"):
        self.__password = password
        self.__username = username
        self.__login_cookie = None
        self.__current = -1

        self.tmp_dir = tmp_dir

        self.image_url = 'http://img.pr0gramm.com/'
        self.api_url = 'http://pr0gramm.com/api/'
        self.login_url = 'https://pr0gramm.com/api/user/login/'
        self.items_url = self.api_url + 'items/get'
        self.item_url = self.api_url + 'items/info'

        self.login()

    def __iter__(self):
        self.__current = Post(self.get_newest_image())["id"]
        return self

    def next(self):
        posts = Posts(self.get_items(self.__current))
        self.__current = posts.minId()
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
        sfw + nsfp = 9
        sfw + nsfp + nsfw = 11
        sfw + nsfp + nsfw + nsfl = 15
        
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

    def get_items(self, item, flag=1, promoted=0, older=True):
        """
        Gets items from the pr0gramm api

        Parameters
        ----------
        :param item: int or str
                     requested post for example: 2525097
        :param flag: int or str
                     TODO
        :param promoted: int 0 or 1
                         0 for all posts
                         1 for posts that have been in top
        :param older: bool or None
                      True for 'older' posts than the item requested
                      False for 'newer' posts
                      None for 'get'
        :return: str
                 json reply from api
        """

        get_type = 'get'
        if older:
            get_type = 'older'
        elif older is not None:
            get_type = 'newer'

        r = get(self.items_url,
                params={get_type: item, 'flags': flag, 'promoted': promoted},
                cookies=self.__login_cookie)

        return r.content.decode('utf-8')

    def get_items_by_tag(self, tags, flag=1, older=0, promoted=0):
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
                     TODO
        :param older: int
                      Specifies the first post that will be returned from the api
                      For example: older=2525097 tags='schmuserkadser' will get
                                   the post '2525097' and all posts after that with the specified tag
        :param promoted: int 0 or 1
                         0 for all posts
                         1 for posts that have been in top
        :return: str
                 json reply from api
        """

        tags = tags.replace(" ", "+")

        if older != 0:
            r = get(self.items_url,
                    params={'older': older, 'flags': flag, 'promoted': promoted, 'tags': tags},
                    cookies=self.__login_cookie)
        else:
            r = get(self.items_url,
                    params={'flags': flag, 'promoted': promoted, 'tags': tags},
                    cookies=self.__login_cookie)

        return r.content.decode('utf-8')

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
                     TODO
        :return: str
                 json reply from api
        """

        r = get(self.item_url + "?itemId=" + str(item),
                params={'flags': flag},
                cookies=self.__login_cookie)
        return r.content.decode("utf-8")

    def get_newest_image(self, flag=1, promoted=0):
        """
        Gets the newest post either on /new (promoted=0) or /top (promoted=1)

        Parameters
        ----------
        :param flag: TODO
        :param promoted: int (0 or 1)
                         0 for all posts
                         1 for posts that have been in top
        :return: str
                 json reply from api
        """
        r = get(self.items_url,
                params={'flags': flag, 'promoted': promoted},
                cookies=self.__login_cookie)
        r = r.content.decode("utf8")
        r = json.dumps(json.loads(r)["items"][0])
        return r

    def get_inbox(self, older=0):
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

    def login(self):
        if self.__password != "" and self.__username != "":
            cookie_path = os.path.join(self.tmp_dir, "cookie.json")

            # TODO re-login after some time -> delete cookie
            if os.path.isfile(cookie_path):
                print "already logged in via cookie -> reading file"
                try:
                    with open(cookie_path, "r") as tmp_file:
                        self.__login_cookie = json.loads(tmp_file.read())
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
                    return False
            else:
                print 'Login not possible. Only SFW images available.'
                return False

            return True
