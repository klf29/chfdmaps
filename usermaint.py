import os 
import urllib 
import re

from google.appengine.api import users
from google.appengine.ext import ndb

import jinja2
import webapp2

import logging
from datetime import datetime, date, time, timedelta

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

class Mapviewer(ndb.Model):
    """Models an user in a non-chfd domain that can access this application"""
    loginuser = ndb.StringProperty(indexed=True)
    realname = ndb.StringProperty(indexed=False)
    added = ndb.DateTimeProperty(auto_now=True)

def get_mapviewers(max_inc):
    map_viewers_query = Mapviewer.query().order(Mapviewer.loginuser)
    map_viewers  = map_viewers_query.fetch(max_inc)
    return map_viewers


class Showusers (webapp2.RequestHandler):

    def get(self):

        """newrow = Mapviewer(loginuser='meanredfink@gmail.com', realname='Ken Friedman')
        newrow.put()"""

        usrs = get_mapviewers(24)
        for usr in usrs:
            logging.info("Mapviewer: " + usr.loginuser);

        template_values = {
            'mapviewers': usrs,
        }

        logging.info("Showusers visited.")
        template = JINJA_ENVIRONMENT.get_template('showusers.html')
        self.response.write(template.render(template_values))

application = webapp2.WSGIApplication([
    ('/showusers', Showusers),
], debug=True)
