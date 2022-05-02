# coding=utf-8
import time
import unittest
from os import remove
from pr0gramm import *
from time import sleep
from pr0gramm.sql_manager import Manager
from pr0gramm.api_exceptions import NotLoggedInException


class Pr0grammApiTests(unittest.TestCase):
    login = False
    USERNAME = ''
    PASSWORD = ''

    def setUp(self):
        """
        Sets up static objects for the api tests.
        Also initializes the api and logs in if LOGIN is set.

        Static objects for testing:
        self.test_user
        self.test_tag
        self.test_posts
        self.test_post
        self.test_comment

        :return: None
        """

        user = '''
            {
              "user": {
                "id": 315478,
                "name": "itssme",
                "registered": 1482019580,
                "score": 17805,
                "mark": 0,
                "admin": 0,
                "banned": 0
              },
              "comments": [
                {
                  "id": 22323926,
                  "up": 3,
                  "down": 3,
                  "content": "O neim, schnell blussern damid sich der kadser nicht umbringern tut :(",
                  "created": 1527762661,
                  "itemId": 2578067,
                  "thumb": "2018\\/05\\/31\\/8cc1c58c8b81cf35.jpg"
                }
              ],
              "commentCount": 208,
              "comments_likes": [
                {
                  "id": 21758945,
                  "up": 69,
                  "down": 0,
                  "content": "test",
                  "created": 1525284576,
                  "ccreated": 1525284576,
                  "itemId": 2534491,
                  "thumb": "2018\\/05\\/02\\/56ca1ba7ac343915.jpg",
                  "userId": 286777,
                  "mark": 0,
                  "name": "JoWo"
                }
              ],
              "commentLikesCount": 12,
              "uploads": [
                {
                  "id": 2578067,
                  "thumb": "2018\\/05\\/31\\/8cc1c58c8b81cf35.jpg"
                }
              ],
              "uploadCount": 65,
              "likesArePublic": true,
              "likes": [
                {
                  "id": 2577703,
                  "thumb": "2018\\/05\\/31\\/4869bff6d0de7145.jpg"
                }
              ],
              "likeCount": 1550,
              "tagCount": 323,
              "badges": [
                {
                  "link": "#top\\/1850207",
                  "image": "benitrat0r-win.png",
                  "description": "Hat 676 Benis gewonnen",
                  "created": 1491083940
                }
              ],
              "followCount": 0,
              "following": false,
              "ts": 1527763240,
              "cache": null,
              "rt": 10,
              "qc": 13
            }
            '''
        self.test_user = User(json_str=user)

        tag = '''
            {
              "id": 22802916,
              "confidence": 0.342372,
              "tag": "schmuserkadser"
            }
            '''
        self.test_tag = Tag(json_str=tag)

        comment = '''
            {
              "id": 25767939,
              "parent": 0,
              "content": "Endlich auch mal Teil von etwas sein",
              "created": 1542542614,
              "up": 2,
              "down": 0,
              "confidence": 0.342372,
              "name": "Doryani",
              "mark": 10
            }'''
        self.test_comment = Comment(comment)

        posts = '''
            {
              "atEnd": true,
              "atStart": true,
              "error": null,
              "items": [
                {
                  "id": 2525097,
                  "promoted": 0,
                  "up": 197,
                  "down": 64,
                  "created": 1524733667,
                  "image": "2018\\/04\\/26\\/c6b285ecd87367cb.jpg",
                  "thumb": "2018\\/04\\/26\\/c6b285ecd87367cb.jpg",
                  "fullsize": "2018\\/04\\/26\\/c6b285ecd87367cb.png",
                  "width": 1052,
                  "height": 658,
                  "audio": false,
                  "source": "",
                  "flags": 1,
                  "user": "itssme",
                  "mark": 0,
                  "userId": 315478,
                  "gift": 0
                },
                {
                  "id": 2546035,
                  "promoted": 0,
                  "up": 139,
                  "down": 46,
                  "created": 1525977077,
                  "image": "2018\\/05\\/10\\/6de84915a0fcc8a3.png",
                  "thumb": "2018\\/05\\/10\\/6de84915a0fcc8a3.jpg",
                  "fullsize": "",
                  "width": 500,
                  "height": 2439,
                  "audio": false,
                  "source": "",
                  "flags": 1,
                  "user": "itssme",
                  "mark": 0,
                  "deleted": 0,
                  "userId": 315478,
                  "gift": 0
                }
              ],
              "ts": 1527768809,
              "cache": "stream:new:9:uitssme:id2525097",
              "rt": 4,
              "qc": 4
            }
            '''
        self.test_posts = Posts(json_str=posts)
        self.test_post = self.test_posts[0]

        self.api = Api(self.USERNAME, self.PASSWORD, "./")

    @classmethod
    def tearDownClass(cls):
        try:
            remove("./%s.json" % cls.USERNAME)
            remove("./pr0gramm.db")
            remove("./pr0gramm.db-journal")
        except PermissionError:
            pass
        except OSError:
            pass

    def test_getUrl(self):
        api = Api("", "", "./doesNotExist")
        assert api.get_items("2504967")

    def test_login1(self):
        if not self.login:
            return

        try:
            self.api.get_inbox()
            assert True
        except NotLoggedInException:
            assert False

    def test_login2(self):
        if not self.login:
            return
        api = Api("", "", "./temp")
        try:
            api.get_inbox()
            assert False
        except NotLoggedInException:
            assert True

    def test_login3(self):
        if not self.login:
            return
        try:
            remove("%s.json" % self.USERNAME)
        except FileNotFoundError:
            pass
        # Login anon
        api = Api("", "", no_login=True)
        img, token = api.get_captcha("tmp.png")
        webbrowser.open(img)
        captcha = input("?: ")
        assert not api.login(token=token, captcha_content=captcha)
        # Now it should raise a not logged in exception
        try:
            api.get_user_comments("itssme")
            assert False
        except NotLoggedInException:
            assert True
        try:
            remove("./tmp.png")
            remove("anonymous.json")
        except FileNotFoundError:
            pass
        api = Api(self.USERNAME, self.PASSWORD, no_login=True)
        img, token = api.get_captcha("tmp.png")
        webbrowser.open(img)
        captcha = input("?: ")
        # Login normally
        assert api.login(token=token, captcha_content=captcha)
        # Login only with cookie
        api = Api(self.USERNAME, "", no_login=True)
        assert api.login(cookie_only=True)
        try:
            remove("%s.json" % self.USERNAME)
        except FileNotFoundError:
            assert False
        return

    def test_inbox1(self):
        if not self.login:
            return

        msg = self.api.get_inbox(older=1)
        assert json.loads(msg)["messages"] == []

    def test_get_items1(self):
        api = Api(tmp_dir="./doesNotExist")
        json_str = api.get_items(2525097, older=None)
        posts_obj = Posts(json_str)
        for elem in posts_obj:
            assert elem["id"]

    # POST OBJECT TESTS

    def test_json_to_post1(self):
        test_post_2 = Post(json_str=self.test_post.to_json())
        test_json_str = test_post_2.to_json()
        obj1 = json.loads(test_json_str)
        obj2 = json.loads(self.test_post.to_json())
        self.assertEqual(obj1, obj2)

    def test_json_to_post2(self):
        json_str = '{"id":2532795,"promoted":0,"up":1,"down":0,"created":1525181290,' \
                   '"image":"2018\/05\/01\/a0ef51790449af5f.mp4","thumb":"2018\/05\/01\/a0ef51790449af5f.jpg",' \
                   '"fullsize":"","width":640,"height":426,"audio":true,' \
                   '"source":"","flags":1,' \
                   '"user":"virtuel","mark":0, "userId": 1, "gift": 0} '
        test_post_2 = Post(json_str=json_str)
        test_json_str = test_post_2.to_json()
        obj1 = json.loads(test_json_str)
        obj2 = json.loads(json_str)
        self.assertEqual(obj1, obj2)

    # POSTS OBJECT TESTS

    def test_posts1(self):
        assert self.test_posts[0]["id"] == 2525097
        assert self.test_posts[1]["id"] == 2546035

        for i in range(0, len(self.test_posts)):
            assert self.test_posts[i]["promoted"] == 0
            assert self.test_posts[i]["user"] == "itssme"

    # USER OBJECT TESTS

    def test_user1(self):
        assert self.test_user["name"] == "itssme"
        assert self.test_user["registered"] == 1482019580

    def test_user2(self):
        try:
            test = self.test_user["doesNotExist"]
            assert False
        except KeyError:
            assert True

    # COMMENT OBJECT TESTS

    # TODO

    # TAG OBJECT TESTS

    def test_tag1(self):
        assert self.test_tag["id"] == 22802916
        assert self.test_tag["tag"] == "schmuserkadser"
        assert self.test_tag["confidence"] == 0.342372

    def test_tag2(self):
        json_str = '{"id": 2, "tag": "kadse", "confidence": 0.5}'
        test_tag2 = Tag(json_str=json_str)
        test_json_str = test_tag2.to_json()
        obj1 = json.loads(test_json_str)
        obj2 = json.loads(json_str)
        self.assertDictEqual(obj1, obj2)

    # OTHER TESTS

    @staticmethod
    def assert_post(l_post):
        assert type(l_post["id"]) is int
        assert type(l_post["promoted"]) is int
        assert type(l_post["userId"]) is int
        assert l_post["userId"] >= 0
        assert type(l_post["up"]) is int
        assert type(l_post["down"]) is int
        assert type(l_post["image"]) is str
        assert type(l_post["thumb"]) is str
        assert type(l_post["fullsize"]) is str
        assert type(l_post["width"]) is int
        assert type(l_post["height"]) is int
        assert type(l_post["audio"]) is bool
        assert type(l_post["source"]) is str
        assert type(l_post["flags"]) is int
        assert 0 <= l_post["flags"] <= 15
        assert type(l_post["user"]) is str
        assert type(l_post["mark"]) is int
        assert type(l_post["gift"]) is int

    @staticmethod
    def assert_comment(comment):
        assert type(comment["id"]) is int
        assert type(comment["up"]) is int
        assert type(comment["down"]) is int
        assert type(comment["content"]) is str
        assert type(comment["created"]) is int
        assert type(comment["itemId"]) is int
        assert type(comment["thumb"]) is str

    def test_search_by_tag(self):
        response = self.api.get_items_by_tag("schmuserkadser")
        posts = Posts(response)

        response_parsed = json.loads(response)
        assert not response_parsed["atEnd"]
        assert response_parsed["atStart"]
        assert response_parsed["error"] is None
        assert len(response_parsed["items"]) > 0

        for i in range(0, 10):
            sleep(0.2)  # avoid 503 errors
            post_info = self.api.get_item_info(posts[i]["id"])
            post_info = json.loads(post_info)

            includes_tag = False
            for j in range(0, len(post_info["tags"])):
                tag = Tag(json_obj=post_info["tags"][j])
                if "schmuserkadser" in tag["tag"].lower():
                    includes_tag = True

                # check tag
                assert type(tag["id"]) is int
                assert type(tag["confidence"]) is float
                assert type(tag["tag"]) is str
                assert len(tag["tag"]) >= 2

            assert includes_tag
            assert type(posts[i]["id"]) is int

    def test_crawl(self):
        id = Post(self.api.get_newest_image())["id"]
        posts = Posts(self.api.get_items(id))

        for i in range(0, 5):
            sleep(0.2)  # avoid 503 errors
            posts.extend(Posts(self.api.get_items(id)))
            id = posts.minId()

        for l_post in posts:
            self.assert_post(l_post)
            assert l_post["created"] > 1600000000

        assert len(posts) > 0

    def test_api_iter(self):
        counter = 0
        all_posts = Posts()
        for posts in self.api:
            all_posts.extend(posts)
            counter += 1
            sleep(0.2)  # avoid 503 errors
            if counter >= 5:
                break
        assert len(all_posts) > 0

    @staticmethod
    def test_calculate_flags():
        assert Api.calculate_flag(sfw=True) == 1
        assert Api.calculate_flag(sfw=False, nsfw=True) == 2
        assert Api.calculate_flag(sfw=False, nsfp=True, nsfl=True) == 4
        assert Api.calculate_flag(sfw=False, nsfp=True, nsfl=True) == 4
        assert Api.calculate_flag(sfw=False, nsfl=True) == 4
        assert Api.calculate_flag(sfw=False, nsfp=True, nsfl=True) == 4
        assert Api.calculate_flag(sfw=False, nsfp=True, nsfw=True, nsfl=True) == 6
        assert Api.calculate_flag(sfw=False, nsfw=True, nsfl=True) == 6
        assert Api.calculate_flag(sfw=True, nsfw=True, nsfl=True) == 7
        assert Api.calculate_flag(sfw=True, nsfp=True) == 9
        assert Api.calculate_flag(sfw=True, nsfp=True, nsfw=True) == 11
        assert Api.calculate_flag(sfw=True, nsfp=True, nsfw=True, nsfl=True) == 15

    def test_database_manager(self):
        manager = Manager("pr0gramm.db")
        manager.insert(self.test_post)
        manager.safe_to_disk()
        assert manager.manual_command("select * from posts;", wait=True)
        manager.safe_to_disk()
        os.remove("pr0gramm.db")

    def test_db_tags(self):
        manager = Manager("pr0gramm.db")
        manager.insert(self.test_tag)
        manager.safe_to_disk()
        result = manager.manual_command("select * from tags;", wait=True)
        assert result[0][0] == 1
        assert result[0][1] == "schmuserkadser"
        manager.safe_to_disk()
        time.sleep(1)
        os.remove("pr0gramm.db")

    def test_db_comments(self):
        manager = Manager("pr0gramm.db")
        manager.insert(self.test_comment)
        manager.safe_to_disk()
        assert manager.manual_command("select * from comments;", wait=True)
        manager.safe_to_disk()
        time.sleep(1)
        os.remove("pr0gramm.db")

    def test_items_by_tag_iterator(self):
        all_posts = Posts()
        for posts in self.api.get_items_by_tag_iterator("SFC"):
            all_posts.extend(posts)
            sleep(0.2)  # avoid 503 errors

        upvotes = 0
        downvotes = 0
        for l_post in all_posts:
            upvotes += l_post["up"]
            downvotes -= l_post["down"]

            self.assert_post(l_post)

        # it is impossible that the sfc gets minus!
        assert upvotes > downvotes

    def test_items_iterator(self):
        all_posts = Posts()
        counter = 0
        for posts in self.api.get_items_iterator(promoted=1):
            if counter >= 5:
                break
            counter += 1
            all_posts.extend(posts)

        assert len(all_posts) > 0

        upvotes = 0
        downvotes = 0
        for l_post in all_posts:
            upvotes += l_post["up"]
            downvotes -= l_post["down"]

            self.assert_post(l_post)

        assert upvotes > 0
        assert (upvotes - downvotes) > 0

    def test_user_comments_iterator(self):
        if self.login:
            all_comments = Comments()
            counter = 0
            for comments in self.api.get_user_comments_iterator("itssme",
                                                                flag=self.api.calculate_flag(sfw=True, nsfp=False,
                                                                                             nsfw=False, nsfl=False)):
                if counter >= 5:
                    break
                counter += 1
                all_comments.extend(comments)

            for comment in all_comments:
                self.assert_comment(comment)

            assert len(all_comments) > 100
            assert counter == 5

    def test_get_message(self):  # this test will only work with my login (circle-ci tests with my login)
        if self.login and self.USERNAME == "itssme":
            messages = json.loads(self.api.get_messages_with_user("froschler"))
            assert len(messages["messages"]) >= 2
            message1 = 1524674144
            message2 = 1524672178
            for msg in messages["messages"]:
                if msg["created"] == message1:
                    assert msg["sent"] == 1
                    assert msg["name"] == "itssme"
                    assert msg["id"] == 2091064
                elif msg["created"] == message2:
                    assert msg["sent"] == 0
                    assert msg["name"] == "froschler"
                    assert msg["id"] == 2091036
                else:
                    assert False

    def test_post_insert(self):
        post = Post(self.api.get_newest_image())

        manager = Manager("pr0gramm.db")
        manager.insert(post)
        manager.safe_to_disk()
        result = manager.manual_command("select count(*) from posts;", wait=True)
        assert result[0][0] == 1
        os.remove("pr0gramm.db")

    def test_ratelimit_nologin(self):
        api = Api()  # DO NOT use the self.api here since it could be logged in!
        try:
            api.ratelimit
            assert False
        except NotLoggedInException:
            assert True
        return

    def test_ratelimit_login(self):
        # Note: This test WILL fail if you uploaded a post before running this test
        if not self.login:
            return
        try:
            assert self.api.ratelimit == 12
        except NotLoggedInException:
            assert False


if __name__ == '__main__':
    # for testing with login call like: USERNAME="itssme" PASSWORD="1234" LOGIN="true" python3 tests.py
    Pr0grammApiTests.login = os.environ.get('LOGIN', Pr0grammApiTests.login)
    Pr0grammApiTests.USERNAME = os.environ.get('USERNAME', Pr0grammApiTests.USERNAME)
    Pr0grammApiTests.PASSWORD = os.environ.get('PASSWORD', Pr0grammApiTests.PASSWORD)

    unittest.main()
