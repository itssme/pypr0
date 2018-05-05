import json
import os
from requests import get, post, utils
from api_exceptions import NotLoggedInException

# TODO: implement logging


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

    def json_to_object(self, json_str):
        json_obj = json.loads(json_str)

        for key, value in vars(self).iteritems():
            vars(self)[key] = json_obj[key]

    def to_json(self):
        return json.dumps(vars(self))


class Tag:
    def __init__(self, id=None, post=None, tag=None, confidence=None, json_str=None):
        if json_str is None:
            self.id = id
            self.post = post
            self.tag = tag
            self.confidence = confidence
        elif json_str is not None and id is None:
            self.id = id
            self.post = post
            self.tag = tag
            self.confidence = confidence
            self.json_to_object(json_str)
        else:
            raise Exception("Could not create object. Can't create via json string and normal arguments.")

    def json_to_object(self, json_str):
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

    def items_get(self, item, flag=1, promoted=0, older=True):
        get_type = 'get'
        if older:
            get_type = 'older'
        elif older is not None:
            get_type = 'newer'

        r = get(self.items_url,
                params={get_type: item, 'flags': flag, 'promoted': promoted},
                cookies=self.__login_cookie)
        print r.content.decode("utf-8")
        return 0

    def item_info(self, item, flag=1, promoted=0):
        r = get(self.item_url + "?itemId=" + str(item),
                params={'flags': flag, 'promoted': promoted},
                cookies=self.__login_cookie)
        print r.content.decode("utf-8")
        return 0

    def get_top_image(self, flag=1):
        r = get(self.items_url,
                params={'flags': flag, 'promoted': 1},
                cookies=self.__login_cookie)
        print str(r.json())

    def get_inbox(self):
        r = get("https://pr0gramm.com/api/inbox/all",
                params={},
                cookies=self.__login_cookie)
        content = json.loads(r.content.decode("utf-8"))
        try:
            if content["code"] == 403:
                raise NotLoggedInException()
        except KeyError:
            pass
        return str(content)

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
