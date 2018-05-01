# Api documentation
For clarification when I talk about 'posts' or a 'post object' I do not mean a 'post' as in get/post request.
But a post is just an uploaded image or video.

### Posts

#### Get requests

Example Call:
https://pr0gramm.com/api/items/get?promoted=1&older=2000
<br>
This will return all posts which are older than the post 2000

##### promoted

Setting ``protmoted=1`` in the api get request will get you all posts which have been in top. Promoted is also
an attribute of the returned post. Here it is the number of the post in top, so for example ``promoted=3000``
will mean that this is the three thousandth post in top.

##### older/ newer

In order to specify which posts you want you can user ``older`` and ``newer``. For example
``https://pr0gramm.com/api/items/get?older=25000`` will get you the posts older than the post ``25000``.
If you don't specify wether you want newer or older posts: for example ``https://pr0gramm.com/api/items/get?id=2500000``
you will get the post ``2500000`` and the the newer ones.

#### Post Object

todo

### Getting comments and tags for a post

todo

### Getting info about users

todo

### Login for NSFW/NSFP/NSFL

todo

# Exampels

```python
from api import Api
Api("gamb", "adminadmin", "/tmp")
if Api.login():
    print "wow"
else:
    print "failed to log in"
```