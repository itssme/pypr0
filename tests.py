import unittest
import json
import os
from os import remove
from api import Api
from api import Tag
from api import Post
from api import User
from api import Comment
from api import Posts
from time import sleep
from api_exceptions import NotLoggedInException


class Pr0grammApiTests(unittest.TestCase):
    login = False

    def setUp(self):
        self.test_user = User("gamb", 1, 1482019580, 0, 0, 0, 0, 17000, 300, 1000, 100, 0)
        self.test_post = Post(1, self.test_user.name, 1, 1000, 25, 1524594130,
                              '2018/04/24/c6b0faa2c860b4ba.jpg', '2018/04/24/c6b0faa2c860b4ba.jpg',
                              '2018/04/24/c6b0faa2c860b4ba.jpg', 1052, 1051, False, '', 1, 0)
        self.test_tag = Tag(1, 'kadse', 0.5)
        self.test_comment = Comment(1, "Han geblussert", self.test_post.id, self.test_user.name, 0, 1525174308, 4, 1,
                                    0.5, 0)

        self.USERNAME = ""
        self.PASSWORD = ""
        self.api = Api(self.USERNAME, self.PASSWORD, "./")

    def tearDown(self):
        try:
            remove("./cookie.json")
        except OSError:
            pass

    def test_getUrl(self):
        api = Api("", "", "./doesNotExist")
        api.get_items("2504967")
        self.assertTrue(True)

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
            pass
        self.assertTrue(True)

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
                   '"user":"virtuel","mark":0} '
        test_post_2 = Post(json_str=json_str)
        test_json_str = test_post_2.to_json()
        obj1 = json.loads(test_json_str)
        obj2 = json.loads(json_str)
        self.assertEqual(obj1, obj2)

    # USER OBJECT TESTS

    # TODO

    # COMMENT OBJECT TESTS

    # TODO

    # TAG OBJECT TESTS

    def test_to_json_tag(self):
        assert self.test_tag["tag"] == "kadse"
        assert self.test_tag["id"] == 1
        assert self.test_tag["confidence"] == 0.5

    def test_tag1(self):
        json_str = '{"id": 2, "tag": "kadse", "confidence": 0.5}'
        test_tag2 = Tag(json_str=json_str)
        test_json_str = test_tag2.to_json()
        obj1 = json.loads(test_json_str)
        obj2 = json.loads(json_str)
        self.assertEqual(obj1, obj2)

    # OTHER TESTS

    def test_search_by_tag(self):
        response = self.api.get_items_by_tag("schmuserkadser")
        posts = Posts(response)
        for i in range(0, 10):
            sleep(0.2)  # avoid 503 errors
            post_info = self.api.get_item_info(posts[i].id)
            post_info = json.loads(post_info)

            includes_tag = False
            for j in range(0, len(post_info["tags"])):
                tag = Tag(json_obj=post_info["tags"][j])
                if tag.tag.lower() == "schmuserkadser":
                    includes_tag = True
            assert includes_tag


if __name__ == '__main__':
    # for testing with login call like: "LOGIN="true" python tests.py"
    Pr0grammApiTests.login = os.environ.get('LOGIN', Pr0grammApiTests.login)
    unittest.main()
