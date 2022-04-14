import base64
import io
import json
import os
import tempfile
import time
import warnings
import webbrowser
from typing import List, Union

import requests
from requests import get, post, utils
from pr0gramm.api_exceptions import NotLoggedInException, RateLimitReached
from pr0gramm.items import *
from urllib import parse


# TODO: implement logging


class Api:
    def __init__(self, username: str = "", password: str = "", tmp_dir: str = "./", no_login: bool = False):
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
        if not no_login:
            self.login()
        return

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

        # tags = tags.replace(" ", "+")
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

        # tags = tags.replace(" ", "+")
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
            nonce = self.__get_current_nonce()
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
            nonce = self.__get_current_nonce()
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
            nonce = self.__get_current_nonce()
            r = post(self.api_url + "tags/vote",
                     data={"id": id, "vote": vote, '_nonce': nonce},
                     cookies=self.__login_cookie)
            return r.status_code == 200
        else:
            raise NotLoggedInException()

    def get_captcha(self, tmp_path: str or io.BytesIO = None) -> List[Union[str, requests.Response]]:
        """
        Download a captcha returning the filepath.
        Note: Deleting the captcha later is not handled here!
        :param tmp_path: Path to temporary directory or BytesIO. If None tempdir will be used
        :return: Full path to captcha image file and token [filepath, token].
                 If BytesIO was used for tmp_path the filepath will be None
        """
        if tmp_path is None:
            tmp_path = tempfile.mktemp(suffix=".png")
        if os.path.isdir(tmp_path):
            # Directory, append filename
            tmp_path = os.path.join(tmp_path, "pr0gramm_captcha.png")
        captcha_req = get(self.api_url + "user/captcha")
        token = captcha_req.json()["token"]
        image = captcha_req.json()["captcha"].split("base64,")[-1]
        write_img = open(tmp_path, "wb") if not isinstance(tmp_path, io.BytesIO) else tmp_path
        write_img.write(base64.b64decode(image))
        write_img.close()
        return [tmp_path if isinstance(tmp_path, str) else None, token]

    @staticmethod
    def _prompt_for_captcha(captcha_path: str) -> str:
        """
        Show the captcha and ask the user to solve it.
        Note: Don't call this if you used BytesIO for the captcha. Only if you saved it on disk
        :param captcha_path: Path to the captcha image or io.BytesIO
        :return: User provided captcha response or None if the file does not exist
        """
        # Basic security check
        if not isinstance(captcha_path, str) or not os.path.isfile(captcha_path) or \
                os.path.splitext(captcha_path)[-1] != ".png":
            return None
        # Open Image
        try:
            webbrowser.open(captcha_path)
            print("Your webbrowser or image viewer should open and display the image")
            print("write the correct content of the captcha into the command line:")
        except:
            print("Could not open image")
            print("Open the image '%s' and write the correct content into the command line:" % captcha_path)
        return input("?: ")

    def login(self, cookie_only: bool = False, token: str = None, captcha_content: str = None) -> bool:
        """
        Logs in with a specific account

        Parameters
        ----------
        :param cookie_only: If set to true the function will
                            only use a cookie authentication and don't try
                            to login with username & password
        :param token: If token and captcha_content are set these will be used for login instead of
                      displaying the captcha.
                      Mainly intended for gui programs handling the display on their own
        :param captcha_content: See token
        :return: bool
                 True if login was successful
                 False if login failed
        :raises: NotLoggedInException if username is missing
        """
        user = self.__username if self.__username != "" else "anonymous"
        cookie_path = os.path.join(self.tmp_dir, "%s.json" % user)
        # Check for cookie
        if os.path.isfile(cookie_path):
            print("Already logged in via cookie -> reading file")
            try:
                with open(cookie_path, "r") as tmp_file:
                    self.__login_cookie = json.loads(tmp_file.read())
                self.logged_in = True
            except IOError:
                print("Could not open cookie file %s", cookie_path)
                self.logged_in = False
        if cookie_only:
            return self.logged_in

        if self.__password != "" \
                and self.__username != "" \
                and not cookie_only \
                and not self.logged_in:
            # TODO re-login after some time -> delete cookie
            captcha = None  # Set it to None so it can be checked later if it was downloaded
            if captcha_content is None or token is None:
                # Get the captcha if not provided
                captcha, token = self.get_captcha()
            while not self.logged_in:
                print("Trying to login in via request.")
                try:
                    # Prompt for captcha solving
                    if captcha_content is None or token is None:
                        captcha_content = self._prompt_for_captcha(captcha)
                    r = post(self.login_url, data={'name': self.__username, 'password': self.__password,
                                                   'captcha': captcha_content, 'token': token})

                    if not r.json()["success"]:
                        print("There was an error logging in: " + str(r.json()["error"]))
                    elif r.json().get("code", 0) == 429:  # rate limit reached (tried to log in too often)
                        raise RateLimitReached()
                    else:
                        self.logged_in = True
                except KeyError:
                    continue
            # Delete the captcha
            if captcha is not None:
                try:
                    os.remove(captcha)
                except FileNotFoundError:
                    pass
                except IOError:
                    pass
            if r.json()['success']:
                self.__login_cookie = r.cookies
                try:
                    with open(cookie_path, 'w') as temp_file:
                        temp_file.write(json.dumps(utils.dict_from_cookiejar(r.cookies)))
                    self.logged_in = True
                except IOError:
                    print("Could not write cookie file %s", cookie_path)
                    self.logged_in = False
            else:
                print("Login not possible.")
                self.logged_in = False
            print("Successfully logged in and written cookie file")
            return True

    def __get_current_nonce(self) -> str:
        """
        Returns the current nonce
        :raises: NotLoggedInException
        """
        try:
            nonce = json.loads(parse.unquote(self.__login_cookie["me"]))["id"][0:16]
        except TypeError:
            raise NotLoggedInException()
        if not self.logged_in or nonce is None or nonce == "":
            raise NotLoggedInException()
        return nonce

    def add_tag(self, item: int or Post, tag: Union[str, List[str]]):
        """
        Add a tag to a given post
        :param item: Post ID or Post object
        :param tag: tag to add
        :return: True if the tag could be added else False
        :raises: NotLoggedInException if no valid login is used
        """
        # Note: I'm not sure how to test this function in unittest since a post can only have a tag once and spamming
        # Tags to random posts for testing isn't a real option...
        # So this function was tested manually
        assert item is not None
        assert len(tag) > 0
        data = {
            "_nonce": self.__get_current_nonce(),  # This raises the NotLoggedInException and ensures a valid user is
            # used
            "itemId": item if isinstance(item, int) else item["id"],
            "tags": ",".join(tag) if isinstance(tag, list) else tag
        }
        r = post(url=self.api_url + "tags/add",
                 data=data,
                 cookies=self.__login_cookie
                 )
        return r.status_code == 200

    def delete_item(self, item: int or Post, reason: str, notifyUser: bool = True, days: int = 0, banUser: bool = False):
        """
        Delete a item.
        Note: Normal users can only delete their own posts and cannot ban users so days and banUser
        :param item: id or Post to delete
        :param reason: Reason for the deletion
        :param notifyUser: Notify to user?
        :param days: If banUser is True: For how long?
        :param banUser: Bans the user
        :return: True if the post was deleted else False
        :raises: NotLoggedInException
        """
        # Note: I'm not sure how to test this function in unittest since a post can only be deleted once
        # I don't want do upload a post and later delete it everytime this function is tested
        # So this function was tested manually
        assert item is not None
        assert len(reason) > 0
        data = {
            "_nonce": self.__get_current_nonce(),
            "itemId": item if isinstance(item, int) else item["id"],
            "banUser": banUser,
            "days": days,
            "notifyUser": notifyUser,
            "reason": reason,
            "customReason": ""  # Not used yet
        }
        r = post(url=self.api_url + "items/delete",
                 data=data,
                 cookies=self.__login_cookie
                 )
        return r.status_code == 200

    @property
    def ratelimit(self) -> int:
        """
        Returns the remaining ratelimit (uploads) for the currently logged in user
        :raises: NotLoggedInException
        """
        if not self.logged_in:
            raise NotLoggedInException()
        r = get(url=self.api_url + "items/ratelimited")
        try:
            return r.json()["left"]
        except KeyError:
            raise NotLoggedInException()
        except TypeError:
            return 0
