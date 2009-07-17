import datetime
import re
import markdown

from google.appengine.ext import db
from google.appengine.api import memcache

def slugify(value):
    """
    Adapted from Django's django.template.defaultfilters.slugify.
    """
    import unicodedata
    value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore')
    value = unicode(re.sub('[^\w\s-]', '', value).strip().lower())
    return re.sub('[-\s]+', '-', value)

class Post(db.Model):
    title = db.StringProperty()
    slug = db.StringProperty()
    pub_date = db.DateTimeProperty(auto_now_add=True)
    author = db.UserProperty(auto_current_user_add=True)

    excerpt = db.TextProperty(default=None)
    body = db.TextProperty()

    excerpt_html = db.TextProperty(default=None)
    body_html = db.TextProperty()

    tags = db.StringListProperty()

    def get_absolute_url(self):
        return "/blog/%04d/%02d/%02d/%s" % (self.pub_date.year,
                                            self.pub_date.month,
                                            self.pub_date.day,
                                            self.slug)

    def get_edit_url(self):
        return "/admin/post/edit/%04d/%02d/%02d/%s" % (self.pub_date.year,
                                                       self.pub_date.month,
                                                       self.pub_date.day,
                                                       self.slug)

    def put(self):
        """
        Make sure that the slug is unique for the given date before
        the data is actually saved.
        """

        # Delete the cached archive list if we are saving a new post
        if not self.is_saved():
            memcache.delete('archive_list')

        # Delete the cached tag list whenever a post is created/updated
        memcache.delete('tag_list')

        self.test_for_slug_collision()
        self.populate_html_fields()

        key = super(Post, self).put()
        return key

    def test_for_slug_collision(self):
        # Build the time span to check for slug uniqueness
        start_date = datetime.datetime(self.pub_date.year,
                                       self.pub_date.month,
                                       self.pub_date.day)
        time_delta = datetime.timedelta(days=1)
        end_date = start_date + time_delta

        # Create a query to check for slug uniqueness in the specified time span
        query = Post.all(keys_only=True)
        query.filter('pub_date >= ', start_date)
        query.filter('pub_date < ', end_date)
        query.filter('slug = ', self.slug)

        # Get the number of slug matches
        count = query.count(1)

        # If any slug matches were found then an exception should be raised
        if count == 1:
            raise SlugConstraintViolation(start_date, self.slug)

    def populate_html_fields(self):
        # Setup Markdown with the code highlighter
        md = markdown.Markdown(extensions=['codehilite'])

        # Convert the excerpt and body Markdown into html
        if self.excerpt_html == None and self.excerpt != None:
            self.excerpt_html = md.convert(self.excerpt)
        if self.body_html == None and self.body != None:
            self.body_html = md.convert(self.body)

class SlugConstraintViolation(Exception):
    def __init__(self, date, slug):
        super(SlugConstraintViolation, self).__init__("Slug '%s' is not unique for date '%s'." % (slug, date.date()))
