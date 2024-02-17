# Api documentation
For clarification when I talk about 'posts' or a 'post object' I do not mean a 'post' as in get/post request.
But a post is just an uploaded image or video.

### Posts

#### Get requests

Example Call:
https://pr0gramm.com/api/items/get?promoted=1&older=2000
<br>
This will return all posts which are older than the post 2000 and have been in top.

##### promoted

Setting ``protmoted=1`` in the api get request will get you all posts which have been in top. Promoted is also
an attribute of the returned post. Here it is the number of the post in top, so for example ``promoted=3000``
will mean that this is the three thousandth post in top.

##### older/ newer

In order to specify which posts you want you can user ``older`` and ``newer``. For example
``https://pr0gramm.com/api/items/get?older=25000`` will get you the posts older than the post ``25000``.
If you don't specify wether you want newer or older posts: for example ``https://pr0gramm.com/api/items/get?id=2500000``
you will get the post ``2500000`` and the the newer ones.

##### Example response: <br>
https://pr0gramm.com/api/items/get?id=2525097&flags=9
```json
{
  "atEnd": false,
  "atStart": false,
  "error": null,
  "items": [
    {
      "id": 2525097,
      "promoted": 0,
      "up": 197,
      "down": 62,
      "created": 1524733667,
      "deleted": 0,
      "image": "2018\\/04\\/26\\/c6b285ecd87367cb.jpg",
      "thumb": "2018\\/04\\/26\\/c6b285ecd87367cb.jpg",
      "fullsize": "2018\\/04\\/26\\/c6b285ecd87367cb.png",
      "width": 1052,
      "height": 658,
      "audio": false,
      "source": "",
      "flags": 1,
      "user": "itssme",
      "mark": 0
    },
    .
    .
    .
    ],
  "ts": 1526741044,
  "cache": "stream:new:9:id2525097",
  "rt": 6,
  "qc": 3
}
```
---
- `atEnd:bool` <br>
Will be `true` if the requested object is the first one
---
- `atStart:bool` <br>
Will be `true` if the requested object is the newest one
---
- `error:str` <br>
Will contain a message if a faulty request is made <br>
For example if requesting an item that does not exist `error` will be:
`"error"="notFound"` and items will look like `"items"=null`
---
- `item:list` <br>
A list containing `posts`
    - `post:dict` <br>
        - `id:int` <br>
        unique `id` of the post
        - `promoted:int` <br>
        Will be the number of the post in top. For example the post with the id `2559630` is
        the `325927` post which was in top.
        - `up:int` <br>
        Number of upvotes
        - `down:int` <br>
        Number of downvotes
        - `created:int` <br>
        A timestamp fot the creation of the post
        - `deleted:int` <br>
        Default value is 0 <br>
        Will be set to 1 if the post is deleted
        - `image:str` <br>
        Image address for 
        https://img.pr0gramm.com/ <br>
        For example: https://img.pr0gramm.com/2018/05/19/12140f2ac817985f.jpg
        - `thumb:str` <br>
        Thumbnail for a post
        - `fullsize:str` <br>
        Only for high quality images which are not getting displayed by default. <br>
        For example: https://pr0gramm.com/top/2558778 to get the image in full quality click the "+":
        https://full.pr0gramm.com/2018/05/18/a4e8e4ceb473b03a.jpg
        - `width:int` <br>
        Width of the image or video
        - `height:int` <br>
        Height of the image or video
        - `audio:bool` <br>
        True if the video contains audio
        - `source:str` <br>
        A link if the image/video was directly uploaded from another website otherwise an emtpy string
        - `flags:int` <br>
        Flags for sfw/nsfp/nsfw/nsfl/pol
        - `user:str` <br>
        Unique name of the uploader
---
- `mark:int` <br>
---
- `ts:int` <br>
---
- `rt:int` <br>
---
- `qc:int` <br>

#### Post Object

todo

### Getting comments and tags for a post

todo

### Getting info about users

todo

### Login for NSFW/NSFP/NSFL

todo

# Examples

```python
from pr0gramm import *
api = Api("gamb", "adminadmin", "/tmp")
if api.login():
    print("logged in")
else:
    print("failed to log in")
```
