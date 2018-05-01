import json
import os
from requests import get, post, utils


class Post:
    def __init__(self, id, user, promoted, up, down, created, image, thumb, fullsize, width, height, audio, source, flags, mark):
        self.id = id

    def to_json(self):
        pass


class User:
    def __init__(self, name, id, registered, admin, banned, bannedUntil, mark, score, tags, likes, comments, followers):
        pass

    def to_json(self):
        pass


class Comment:
    def __init__(self, id, comment, post, user, parent, created, up, down, confidence, mark):
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

    def to_json(self):
        return json.dumps({"id": self.id, "comment": self.comment, "post": self.post.id, "user": self.user.name,
                           "parent": self.parent.id, "created": self.created, "up": self.u, "down": self.down,
                           "confidence": self.confidence, "mark": self.mark})


class Tag:
    def __init__(self, id, post, tag, confidence):
        self.id = id
        self.post = post
        self.tag = tag
        self.confidence = confidence

    def to_json(self):
        return json.dumps({"id": self.id, "post": self.post.id, "tag": self.tag, "confidence": self.confidence})


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

    def items_get(self, item, flag=1, promoted=0, older=True):
        r = get(self.items_url + "?get=" + item,
                params={'flags': flag, 'promoted': promoted},
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
