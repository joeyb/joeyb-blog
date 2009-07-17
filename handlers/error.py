from google.appengine.ext import webapp

import view

class Error404Handler(webapp.RequestHandler):

    def get(self):
        page = view.Page()
        page.render_error(self, 404)
