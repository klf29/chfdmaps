import os 
import urllib 
import re

from google.appengine.api import users
from google.appengine.ext import ndb

import jinja2
import webapp2

import logging
import json
from google.appengine.ext.webapp.mail_handlers import InboundMailHandler
from datetime import datetime, date, time, timedelta

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

class Incident(ndb.Model):
    """Models an individual Incident entry with id, address, and date."""
    incidentid = ndb.StringProperty(indexed=False)
    address = ndb.StringProperty(indexed=False)
    date = ndb.DateTimeProperty(auto_now=True)
    content = ndb.TextProperty(indexed=False)
    sender = ndb.StringProperty(indexed=False)
    subject = ndb.StringProperty(indexed=False)

class Mapviewer(ndb.Model):
    """Models an individual Incident entry with id, address, and date."""
    loginuser = ndb.StringProperty(indexed=True)
    realname = ndb.StringProperty(indexed=False)
    added = ndb.DateTimeProperty(auto_now=True)

def get_incidents(max_inc):
    inc_query = Incident.query().order(-Incident.date)
    incidents = inc_query.fetch(max_inc)
    return incidents

def validate_user(usrobj):
    """Here's how we tell.  
         The user must be logged in.
         Google or another openid provider must be where they've logged in.
         They must have a chfd.net email address or 
            another email address that's been added to our MapViewers database. """
    user = usrobj
    logging.info("chmaps user validation routine ....")
    user = users.get_current_user()
    logging.info("userobj refers to a " + type(user).__name__)
    if not user:
        logging.info("Visited by " + "an unknown person.")
        logging.info("Redirect to: " + users.create_login_url('/'))
        return None
    else:
        logging.info("Visited by user with email address:" +  user.email()  )
        logging.info("_________________________ nickname:" +  user.nickname()  )
        logging.info("_________________________  user-id:" +  user.user_id()  )
        logging.info("________________federated_identity:" +  user.federated_identity()  )
        logging.info("________________federated_provider:" +  user.federated_provider()  )

        ufp = user.federated_provider()
        open_provider_list = [ 'https://www.google.com/accounts/o8/id', 'https://www.google.com/accounts/o8/ud', 'yahoo.com', 'myspace.com', 'aol.com', 'myopenid.com' ]

        if ufp not in open_provider_list:
            logging.info("Rejected login from non-authenticated source: "+ ufp)
            logging.info("Redirect to: " + users.create_login_url('/'))
            return None 

        caller = user.email()
        caller_is_chfd = re.search('@chfd.net$',caller)
        if caller_is_chfd:
            logging.info("OpenID authenticated caller is @chfd.net")
            return caller
        else:
            viewer_query = Mapviewer.query()
            viewer_query = Mapviewer.query(Mapviewer.loginuser == caller)
            mv = viewer_query.get()
            if mv is  None:
                logging.info("Non-CHFD User rejected since absent from the MapViewer auth table")
                logging.info("Redirect to: " + users.create_login_url('/'))
                return None
            logging.info("User found in MapViewer auth table")
            return caller

class MainPage(webapp2.RequestHandler):

    def get(self):

        mypage = "/"
        mytmpl = "index.html"
        template_values = { }

        my_user = users.get_current_user()
        caller = validate_user(my_user)
        if caller is None:
            self.redirect(users.create_login_url(mypage))
        else:
            logging.info(mypage + " page visited by user with email address:" +  caller )
            template = JINJA_ENVIRONMENT.get_template(mytmpl)
            self.response.write(template.render(template_values))

class Mobile(webapp2.RequestHandler):

    def get(self):

        mypage = "/m"
        mytmpl = "mmap.html"
        template_values = { }

        my_user = users.get_current_user()
        caller = validate_user(my_user)
        if caller is None:
            self.redirect(users.create_login_url(mypage))
        else:
            logging.info(mypage + " page visited by user with email address:" +  caller )
            template = JINJA_ENVIRONMENT.get_template(mytmpl)
            self.response.write(template.render(template_values))

class Recent(webapp2.RequestHandler):

    def get(self):

        mypage = "/recent"
        mytmpl = "recent.html"
        template_values = { }

        my_user = users.get_current_user()
        caller = validate_user(my_user)
        if caller is None:
            self.redirect(users.create_login_url(mypage))
        else:
            logging.info(mypage + " page visited by user with email address:" +  caller )
            incidents = get_incidents(24)
            template_values = { 'incidents': incidents, }
        template = JINJA_ENVIRONMENT.get_template(mytmpl)
        self.response.write(template.render(template_values))

class Dummyuser(webapp2.RequestHandler):

    def get(self):

        newrow = Mapviewer(loginuser='meanredfink@gmail.com', realname='Ken Friedman')
        newrow.put()

        template_values = { }
        template_values = {
            'message': 'dummy user created',
        }

        template = JINJA_ENVIRONMENT.get_template('dummyuser.html')
        self.response.write(template.render(template_values))

class Active(webapp2.RequestHandler):

    def get(self):

        latest = get_incidents(1)[0]
        addr = latest.address

        self.response.headers['Content-Type'] = 'application/json'   
        obj = {
            'destination': addr,
            } 
        self.response.out.write(json.dumps(obj))

class Cleanup(webapp2.RequestHandler):

    def get(self):

        inc_query = Incident.query().order(-Incident.date)
        incidents = inc_query.fetch(20)
        deleted = []

        oldest=datetime.now()-timedelta(minutes=1440)
        logging.info("Purging incidents older than " +  oldest.isoformat() )

        for incident in incidents:
            if incident.date < oldest:
                logging.info("Deleting Incident ID " +  incident.incidentid + " recorded:" + incident.date.isoformat()  )
                deleted.append(incident)
                incident.key.delete()

        template_values = {
            'incidents': deleted,
        }

        template = JINJA_ENVIRONMENT.get_template('cleanup.html')
        self.response.write(template.render(template_values))

class LogSenderHandler(InboundMailHandler):

    def receive(self, mail_message):
        m_sender = mail_message.sender
        m_subject = mail_message.subject
        logging.info("Received a message from: " + m_sender)
        logging.info("The email subject: " + m_subject)
        try:
            logging.info("The email was sent on: " + str(mail_message.date))
        except AttributeError:
            logging.info("The email has no sent date specified!!!")
        valid_senders = [ 'cayugaheightsfire@tompkins-co.org','cayuga.heights.fd@gmail.com','meanredfink@gmail.com','friedman430@gmail.com','ken.friedman@cornell.edu','klf29@cornell.edu','dispatch1@chfd.net','forwarding-noreply@google.com' ]
        if re.search(r'[\w\.-]+@[\w\.-]+',m_sender):
            m_sender = re.search(r'[\w\.-]+@[\w\.-]+',m_sender).group(0)
            if m_sender not in valid_senders:
                raise NameError('UnauthorizedMailSender')
        plaintext_bodies = mail_message.bodies('text/plain')
        for content_type, body in plaintext_bodies:
            decoded_body = body.decode()
            logging.info("Body: " + decoded_body)

            incnum="Cyy-000"
            nature="n/a"
            city="n/a"
            address="n/a"
            try:
                incnum=re.search(r'INCIDENT # *([C\-0123456789]*)',decoded_body).group(1)
                logging.info("Incident: " + incnum)

                nature=re.search(r'Nature: (.*) *Type:',decoded_body).group(1).strip()
                logging.info("Nature: " + nature)

                city=re.search(r'City: (.*)\n',decoded_body).group(1).strip()
                logging.info("City: " + city)

                address=re.search(r'Address: (.*);.*Zone:',decoded_body).group(1) + ' ' + city + ' NY '
                address=re.sub(r'2230 N TRIPHAMMER RD','198 SAVAGE FARM DR',address)
                logging.info("Address: " + address)

                newrow = Incident(incidentid=incnum, address=address, content=decoded_body, sender=m_sender, subject=m_subject)
                newrow.put()
            except AttributeError:
                logging.info("Some attributes were not received")

application = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/m', Mobile),
    ('/recent', Recent),
    ('/latest', Recent),
    ('/active', Active),
    ('/cleanup', Cleanup),
    ('/dummyuser', Dummyuser),
    ('/_ah/mail/nb@.*chfdmaps\.appspotmail\.com', LogSenderHandler) 
], debug=True)
