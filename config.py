import os

APP_ROOT_DIR = os.path.abspath(os.path.dirname(__file__))

SETTINGS = {
    'title': 'Blog',
    'description': "Google App Engine-Based Blog",
    'author': 'John Doe',
    'email': 'john@example.com',
    'url': 'http://www.example.com',
    'items_per_page': 10,
    # Enable/disable Google Analytics
    # Set to your tracking code (UA-xxxxxx-x), or False to disable
    'google_analytics': False,
    # Enable/disable Disqus-based commenting for posts
    # Set to your Disqus short name, or False to disable
    'disqus': False,
}
