import unittest
from api import Api
from api import Tag
from api import Post
from api import User


class Pr0grammApiTests(unittest.TestCase):
    def setUp(self):
        self.test_user = User("gamb", 1, 1482019580, 0, 0, 0, 0, 17000, 300, 1000, 100, 0)
        self.test_post = Post(1, self.test_user, 1, 1000, 25, 1524594130,
                         '2018/04/24/c6b0faa2c860b4ba.jpg', '2018/04/24/c6b0faa2c860b4ba.jpg',
                         '2018/04/24/c6b0faa2c860b4ba.jpg', 1052, 1051, False, '', 1, 0)
        self.test_tag = Tag(1, self.test_post, 'kadse', 0.5)

    def test_getUrl(self):
        api = Api("", "", "./temp")
        api.items_get("2504967", )
        self.assertTrue(True)

    def test_to_json_tag(self):
        print self.test_tag.to_json()
        self.assertTrue(self.test_tag.to_json() == '{"post": 1, "tag": "kadse", "id": 1, "confidence": 0.5}')


if __name__ == '__main__':
    unittest.main()
