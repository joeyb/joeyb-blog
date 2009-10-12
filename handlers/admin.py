import datetime

from google.appengine.ext import webapp
from google.appengine.api import memcache

from models import blog
import view

class CreatePostHandler(webapp.RequestHandler):

    def get(self):
        page = view.Page()
        page.render(self, 'templates/admin/post_form.html')

    def post(self):
        new_post = blog.Post()
        new_post.title = self.request.get('title')
        new_post.body = self.request.get('body')

        slug = self.request.get('slug').strip()
        if slug == '':
            slug = blog.slugify(new_post.title)
        new_post.slug = slug

        excerpt = self.request.get('excerpt').strip()
        if excerpt == '':
            excerpt = None
        new_post.excerpt = excerpt

        new_post.tags = self.request.get('tags').split()

        if self.request.get('submit') == 'Submit':
            new_post.put()
            self.redirect(new_post.get_absolute_url())
        else:
            new_post.populate_html_fields()
            template_values = {
                'post': new_post,
                }
            page = view.Page()
            page.render(self, 'templates/admin/post_form.html', template_values)

class EditPostHandler(webapp.RequestHandler):

    def get(self, year, month, day, slug):
        year = int(year)
        month = int(month)
        day = int(day)

        # Build the time span to check for the given slug
        start_date = datetime.datetime(year, month, day)
        time_delta = datetime.timedelta(days=1)
        end_date = start_date + time_delta

        # Create a query to check for slug uniqueness in the specified time span
        query = blog.Post.all()
        query.filter('pub_date >= ', start_date)
        query.filter('pub_date < ', end_date)
        query.filter('slug = ', slug)

        post = query.get()

        if post == None:
            page = view.Page()
            page.render_error(self, 404)
        else:
            action_url = post.get_edit_url()

            template_values = {
                'action': action_url,
                'post': post,
                }

            page = view.Page()
            page.render(self, 'templates/admin/post_form.html', template_values)

    def post(self, year, month, day, slug):
        year = int(year)
        month = int(month)
        day = int(day)

        # Build the time span to check for the given slug
        start_date = datetime.datetime(year, month, day)
        time_delta = datetime.timedelta(days=1)
        end_date = start_date + time_delta

        # Create a query to check for slug uniqueness in the specified time span
        query = blog.Post.all()
        query.filter('pub_date >= ', start_date)
        query.filter('pub_date < ', end_date)
        query.filter('slug = ', slug)

        post = query.get()

        if post == None:
            page = view.Page()
            page.render_error(self, 404)
        else:
            action_url = post.get_edit_url()
            post.title = self.request.get('title')
            post.body = self.request.get('body')

            slug = self.request.get('slug').strip()
            if slug == '':
                slug = blog.slugify(post.title)
            post.slug = slug

            excerpt = self.request.get('excerpt').strip()
            if excerpt == '':
                excerpt = None
            post.excerpt = excerpt

            post.tags = self.request.get('tags').split()

            if self.request.get('submit') == 'Submit':
                post.put()
                self.redirect(post.get_absolute_url())
            else:
                post.populate_html_fields()
                template_values = {
                    'action': action_url,
                    'post': post,
                }
                page = view.Page()
                page.render(self, 'templates/admin/post_form.html', template_values)

class ClearCacheHandler(webapp.RequestHandler):

    def get(self):
        memcache.flush_all()
