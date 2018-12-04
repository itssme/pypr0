import api
from time import sleep

# Crawl all posts in top that aren't older than one day

pr0 = api.Api()  # create api object

max_date = None
all_posts = api.Posts()  # create a posts object to store all crawled posts in

for posts in pr0.get_items_iterator(promoted=1):  # iterate over top posts
    all_posts.extend(posts)

    if max_date is None:
        max_date = posts.maxDate()

    print("Max: " + str(posts.maxId()))
    print("Min: " + str(posts.minId()))
    sleep(1)

    if max_date - posts.minDate() >= 86400:
        # stop when there is a post that is older than one day
        break

# remove all posts that are older than one day
remove_time = max_date - 86400
filtered_posts = api.Posts()
for post in all_posts:
    if post["created"] > remove_time:
        filtered_posts.append(post)
all_posts = filtered_posts

print("\nfrom: " + str(all_posts.minId()) + " to " + str(all_posts.maxId()))
print("got " + str(len(all_posts)) + " posts")
print("summed votes: " + str(all_posts.sumPoints()) + " points")
print("average points per post: " + str(all_posts.sumPoints() / float(len(all_posts))))
