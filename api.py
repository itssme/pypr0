import json
import os
from requests import get, post, utils
from api_exceptions import NotLoggedInException


# TODO: implement logging


class Posts:
    def __init__(self, json_str):
        self.json = json.loads(json_str)
        temp_items = self.json["items"]
        self.items = []
        for elem in temp_items:
            self.items.append(Post(json_str=json.dumps(elem)))
        self.current = -1

    def __repr__(self):
        return json.dumps(self.json)

    def __str__(self):
        return json.dumps(self.json)

    def __getitem__(self, key):
        return self.items[key]

    def __len__(self):
        return len(self.items)

    def __iter__(self):
        return self

    def next(self):
        self.current += 1
        if self.current >= len(self.items):
            raise StopIteration
        else:
            return self.items[self.current]

    def get_items(self):
        return self.items


class Post:
    def __init__(self, id=None, user=None, promoted=None, up=None, down=None, created=None, image=None, thumb=None,
                 fullsize=None, width=None, height=None, audio=None, source=None, flags=None, mark=None, json_str=None):
        self.id = id
        self.user = user
        self.promoted = promoted
        self.up = up
        self.down = down
        self.created = created
        self.image = image
        self.thumb = thumb
        self.fullsize = fullsize
        self.width = width
        self.height = height
        self.audio = audio
        self.source = source
        self.flags = flags
        self.mark = mark

        if json_str is not None:
            self.json_to_object(json_str)

    def __repr__(self):
        return self.to_json()

    def __str__(self):
        return self.to_json()

    def __getitem__(self, key):
        return vars(self)[key]

    def json_to_object(self, json_str):
        json_obj = json.loads(json_str)

        for key, value in vars(self).iteritems():
            vars(self)[key] = json_obj[key]

    def to_json(self):
        return json.dumps(vars(self))


class User:
    def __init__(self, name=None, id=None, registered=None, admin=None, banned=None, bannedUntil=None, mark=None,
                 score=None, tags=None, likes=None, comments=None, followers=None, json_str=None):
        self.name = name
        self.id = id
        self.registered = registered
        self.admin = admin
        self.banned = banned
        self.bannedUntil = bannedUntil
        self.mark = mark
        self.score = score
        self.tags = tags
        self.likes = likes
        self.comments = comments
        self.followers = followers

        if json_str is not None:
            self.json_to_object(json_str)

    def __repr__(self):
        return self.to_json()

    def __str__(self):
        return self.to_json()

    def __getitem__(self, key):
        return vars(self)[key]

    def json_to_object(self, json_str):
        json_obj = json.loads(json_str)

        for key, value in vars(self).iteritems():
            vars(self)[key] = json_obj[key]

    def to_json(self):
        return json.dumps(vars(self))


class Comment:
    def __init__(self, id=None, comment=None, post=None, user=None, parent=None, created=None, up=None, down=None,
                 confidence=None, mark=None, json_str=None):
        self.id = id
        self.comment = comment
        self.post = post
        self.user = user
        self.parent = parent
        self.created = created
        self.up = up
        self.down = down
        self.confidence = confidence
        self.mark = mark

        if json_str is not None:
            self.json_to_object(json_str)

    def __repr__(self):
        return self.to_json()

    def __str__(self):
        return self.to_json()

    def __getitem__(self, key):
        return vars(self)[key]

    def json_to_object(self, json_str):
        json_obj = json.loads(json_str)

        for key, value in vars(self).iteritems():
            vars(self)[key] = json_obj[key]

    def to_json(self):
        return json.dumps(vars(self))


class Tag:
    def __init__(self, id=None, tag=None, confidence=None, json_str=None, json_obj=None):
        self.id = id
        self.tag = tag
        self.confidence = confidence

        if json_str is not None:
            self.json_to_object(json_str)
        elif json_obj is not None:
            self.json_to_object(json_obj=json_obj)

    def __repr__(self):
        return self.to_json()

    def __str__(self):
        return self.to_json()

    def __getitem__(self, key):
        return vars(self)[key]

    def json_to_object(self, json_str="", json_obj=""):
        if json_obj == "":
            json_obj = json.loads(json_str)

        for key, value in vars(self).iteritems():
            vars(self)[key] = json_obj[key]

    def to_json(self):
        return json.dumps(vars(self))


class Api:
    def __init__(self, username="", password="", tmp_dir="./"):
        self.__password = password
        self.__username = username
        self.__login_cookie = None

        self.tmp_dir = tmp_dir

        self.image_url = 'http://img.pr0gramm.com/'
        self.api_url = 'http://pr0gramm.com/api/'
        self.login_url = 'https://pr0gramm.com/api/user/login/'
        self.items_url = self.api_url + 'items/get'
        self.item_url = self.api_url + 'items/info'

        self.login()

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
        return r.content.decode("utf-8")

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
