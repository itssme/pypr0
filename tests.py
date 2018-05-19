import unittest
import json
from api import Api
from api import Tag
from api import Post
from api import User
from api import Comment
from api import Posts
from api_exceptions import NotLoggedInException


class Pr0grammApiTests(unittest.TestCase):
    def setUp(self):
        self.test_user = User("gamb", 1, 1482019580, 0, 0, 0, 0, 17000, 300, 1000, 100, 0)
        self.test_post = Post(1, self.test_user.name, 1, 1000, 25, 1524594130,
                              '2018/04/24/c6b0faa2c860b4ba.jpg', '2018/04/24/c6b0faa2c860b4ba.jpg',
                              '2018/04/24/c6b0faa2c860b4ba.jpg', 1052, 1051, False, '', 1, 0)
        self.test_tag = Tag(1, self.test_post.id, 'kadse', 0.5)
        self.test_comment = Comment(1, "Han geblussert", self.test_post.id, self.test_user.name, 0, 1525174308, 4, 1,
                                    0.5, 0)

        # for testing with login
        self.USERNAME = ""
        self.PASSWORD = ""

    def test_getUrl(self):
        api = Api("", "", "./temp")
        api.items_get("2504967", )
        self.assertTrue(True)

    def test_login1(self):
        api = Api(self.USERNAME, self.PASSWORD, "./temp")
        try:
            api.get_inbox()
            assert True
        except NotLoggedInException:
            assert False

    def test_login2(self):
        api = Api("", "", "./temp")
        try:
            api.get_inbox()
            assert False
        except NotLoggedInException:
            assert True

    def test_items_get1(self):
        api = Api(tmp_dir="./temp")
        json_str = api.items_get(2525097, older=None)
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
        self.assertTrue(self.test_tag.to_json() == '{"post": 1, "tag": "kadse", "id": 1, "confidence": 0.5}')

    def test_tag1(self):
        json_str = '{"id": 2, "post": 2, "tag": "kadse", "confidence": 0.5}'
        test_tag2 = Tag(json_str=json_str)
        test_json_str = test_tag2.to_json()
        obj1 = json.loads(test_json_str)
        obj2 = json.loads(json_str)
        self.assertEqual(obj1, obj2)


if __name__ == '__main__':
    unittest.main()
