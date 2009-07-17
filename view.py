import os
import string
import datetime
from dateutil.relativedelta import *

from google.appengine.ext.webapp import template
from google.appengine.ext import db
from google.appengine.api import memcache
from google.appengine.api import users

import config
from models import blog

def get_archive_list():
    """Return a list of the archive months and their article counts."""
    # Attempt to get a memcache'd copy first
    archive = memcache.get('archive_list')
    if archive is not None:
        return archive

    # Get the date of the oldest post
    query = db.Query(blog.Post)
    query.order('pub_date')
    oldest = query.get()

    # Handle the situation where there are no posts
    if oldest is None:
        memcache.set('archive_list', [])
        return []

    # Create a date delta for moving ahead 1 month
    plus_one_month = relativedelta(months=+1)

    # Calculate the start and end dates for the archive
    start_date = datetime.date(oldest.pub_date.year, oldest.pub_date.month, 1)
    end_date = datetime.date.today()
    end_date = datetime.date(end_date.year, end_date.month, 1) + plus_one_month

    # Loop through each month in the time span and count the number
    # of posts made in that month
    archive = []
    current_date = start_date
    while current_date < end_date:
        next_date = current_date + plus_one_month

        query = db.Query(blog.Post)
        query.filter('pub_date >= ', current_date)
        query.filter('pub_date < ', next_date)

        archive.append({'date': current_date,
                        'count': query.count(1000),
                        'url': '/blog/%04d/%02d' % (current_date.year, current_date.month),
                       })
        current_date = next_date

    memcache.set('archive_list', archive)
    return archive

def get_tag_list():
    """Return a list of the tags and their article counts"""
    # Attempt to get a memcache'd copy first
    tag_list = memcache.get('tag_list')
    if tag_list is not None:
        return tag_list

    # Build a list of tags and their article counts
    tag_list = {}
    query = blog.Post.all()
    for p in query:
        for tag in p.tags:
            if tag in tag_list:
                tag_list[tag] += 1
            else:
                tag_list[tag] = 1

    # Sort the tag dictionary by name into a list
    # and add each tag's URL
    sorted_tag_list = []
    for tag in sorted(tag_list.iterkeys()):
        sorted_tag_list.append({'tag': tag,
                                'count': tag_list[tag],
                                'url': '/blog/tag/%s' % (tag),
                               })

    memcache.set('tag_list', sorted_tag_list)
    return sorted_tag_list

class Page:

    def render(self, handler, template_file, template_values={}):
        """Render a template"""
        archive_list = get_archive_list()
        tag_list = get_tag_list()

        values = {'archive_list': archive_list,
                  'tag_list': tag_list,
                  'user': users.get_current_user(),
                  'user_is_admin': users.is_current_user_admin(),
                 }

        values.update({'settings': config.SETTINGS})
        values.update(template_values)

        template_path = os.path.join(config.APP_ROOT_DIR, template_file)
        handler.response.out.write(template.render(template_path, values))

    def render_paginated_query(self, handler, query, values_name, template_file, template_values={}):
        """Paginate a query and render the requested page"""
        num = config.SETTINGS['items_per_page']
        offset = string.atoi(handler.request.get('offset') or str(0))

        items = query.fetch(num + 1, offset)

        values = {values_name: items}
        if len(items) > num:
            values.update({'next_offset': str(offset + num)})
            items.pop()
        if offset > 0:
            values.update({'prev_offset': str(offset - num)})
        template_values.update(values)

        self.render(handler, template_file, template_values)

    def render_error(self, handler, error):
        """Render an error page"""
        # TODO: Add more error pages for 403, 500, etc.
        valid_errors = [404]

        # If the error code given is not in the list then default to 404
        if error not in valid_errors:
            error = 404

        # Set the error code on the handler
        handler.error(error)

        self.render(handler, 'templates/error/%d.html' % error, {})
