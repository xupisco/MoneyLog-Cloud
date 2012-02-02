# -*- coding: utf-8 -*-

# MoneyLog Box app, by Me!

import os
_DEBUG = os.environ['SERVER_SOFTWARE'].startswith('Dev')

import webapp2, urllib, json
import jinja2 # Template engine

from conf import *

from Cookie import SimpleCookie
from dropbox import session, client

from google.appengine.api import users

env = jinja2.Environment(loader = jinja2.FileSystemLoader('templates'))

APP_KEY = DB_APPKEY # in conf.py
APP_SECRET = DB_APPSECRET # in conf.py
ACCESS_TYPE = 'app_folder' # should be 'dropbox' or 'app_folder' as configured for your app

HOST = 'moneylog-cloud.appspot.com' if not _DEBUG else 'localhost:8087'
MONEYLOG_FOLDER = '/MoneyLog Cloud/'
MONEYLOG_DATA = 'moneylog.txt'
MONEYLOG_CONFIG = 'js/config.js'
TOKEN_STORE = {}

def get_session():
    return session.DropboxSession(APP_KEY, APP_SECRET, ACCESS_TYPE)

def get_client(access_token):
    sess = get_session()
    sess.set_token(access_token.key, access_token.secret)
    return client.DropboxClient(sess)


class CoreHandler(webapp2.RequestHandler):
    def set_cookie(self, key, value):
        cookies = SimpleCookie(self.request.headers.get('Cookie'))
        cookies[key] = value
        self.response.headers.add_header("Set-Cookie", str(cookies))

    def get_cookie(self, key):
        in_cookies = SimpleCookie()
        request_cookies = self.request.headers.get('Cookie')
        if request_cookies:
            in_cookies.load(request_cookies)
            val = in_cookies.get(key)
            return val.value if val else None
        return None

    def generate(self, template_name, template_values={}):
        values = {
            'request': self.request,
            'user': users.GetCurrentUser(),
            'login_url': users.CreateLoginURL(self.request.uri),
            'logout_url': users.CreateLogoutURL('http://' + self.request.host + '/'),
            'application_name': 'MoneyLog Cloud',
            'debug': self.request.get('debug', False),
        }
    
        values.update(template_values)
        template = env.get_template(template_name)
        self.response.out.write(template.render(values, debug=_DEBUG))


class Login(CoreHandler):
    def get(self):
        sess = get_session()
        request_token = sess.obtain_request_token()
        TOKEN_STORE[request_token.key] = request_token

        callback = "http://%s/connect" % (HOST)
        url = sess.build_authorize_url(request_token, oauth_callback=callback)
        data = {
            'auth_url': url
        }
        self.generate('login.html', data)


class Connect(CoreHandler):
    def get(self):
        request_token_key = self.request.get('oauth_token')
        if not request_token_key:
            self.redirect("/login")

        sess = get_session()
        request_token = TOKEN_STORE[request_token_key]
        access_token = sess.obtain_access_token(request_token)
        TOKEN_STORE[access_token.key] = access_token

        self.set_cookie('access_token_key', access_token.key)
        return self.redirect('/')

    def post(self):
        pass


class QuickAdd(CoreHandler):
    def post(self):
        access_token_key = self.get_cookie('access_token_key')
        access_token = TOKEN_STORE.get(access_token_key)
        if not access_token:
            return self.redirect('/login')

        import tempfile

        dude = get_client(access_token)
        data = self.request.get('data')
        filename = self.request.get('filename')

        f = dude.get_file(filename).read()

        temp = tempfile.TemporaryFile()
        temp.write("%s\n%s" % (f, data.encode('utf-8')))
        temp.seek(0)
        save = dude.put_file(filename, temp.read(), overwrite=True)
        temp.close()

        self.response.headers["Content-Type"] = "text/plain"
        self.response.out.write(json.dumps([{'status': 'success'}]))


class Update(CoreHandler):
    def post(self):
        access_token_key = self.get_cookie('access_token_key')
        access_token = TOKEN_STORE.get(access_token_key)
        if not access_token:
            return self.redirect('/login')

        import tempfile

        dude = get_client(access_token)
        data = self.request.get('data')
        filename = self.request.get('filename')
        
        #ml_data = dude.get_file(MONEYLOG_DATA)

        temp = tempfile.TemporaryFile()
        temp.write(data.encode('utf-8'))
        temp.seek(0)
        save = dude.put_file(filename, temp.read(), overwrite=True)
        temp.close()

        self.response.headers["Content-Type"] = "text/plain"
        self.response.out.write(json.dumps([{'status': 'success'}]))



class Main(CoreHandler):
    def get(self):
        access_token_key = self.get_cookie('access_token_key')
        access_token = TOKEN_STORE.get(access_token_key)
        if not access_token:
            return self.redirect('/login')
        
        dude = get_client(access_token)
        reloading = self.request.get('reloading', False)
        filename = self.request.get('filename', '*')

        # Load or create user config
        try:
            ml_config = dude.get_file(MONEYLOG_CONFIG).read()
        except:
            raw_config = open('moneylog_config.js', 'r')
            ml_config = raw_config.read()
            raw_config.close()
            save = dude.put_file(MONEYLOG_CONFIG, ml_config)

        # Read directory
        ml_dir = dude.metadata('')
        ml_files = ['*']
        txt = ''

        for f in ml_dir['contents']:
            if "mime_type" in f:
                if f['mime_type'] == "text/plain":
                    ml_files.append(f['path'][f['path'].rfind("/")+1:])

        if len(ml_files) > 2:
            ml_files_js = "dataFiles = ['%s']" % "', '".join(ml_files)
        else:
            if len(ml_files) == 1:
                ml_files_js = 'dataFiles = [\'%s\']' % MONEYLOG_DATA
            else:
                ml_files_js = 'dataFiles = [\'%s\']' % ml_files[1]
                filename = ml_files[1]

        # Read selected file or all
        if filename == "*" and len(ml_files) > 2:
            for f in ml_dir['contents']:
                if "mime_type" in f:
                    if f['mime_type'] == "text/plain":
                        txt += '\n' + dude.get_file(f['path']).read()
            ml_data = txt
        else:
            try:
                basic_file = MONEYLOG_DATA if filename == "*" else filename
                ml_data = dude.get_file(basic_file).read()
            except:
                raw_file = open('moneylog_rawdata.txt', 'r')
                ml_data = raw_file.read()
                raw_file.close()
                save = dude.put_file(MONEYLOG_DATA, ml_data)
        
        config_script = "<script type='text/javascript'>\n%s\n\n%s\n</script>" % (ml_config.decode("utf-8"), ml_files_js)

        if not reloading:
            data = {
                'ml_data': ml_data.decode('utf-8'),
                'user_config': config_script,
                'ml_files': ml_files,
            }
            self.generate('moneylog.html', data)
        else:
            self.response.out.write(ml_data.decode('utf-8'))


app = webapp2.WSGIApplication([('/', Main),
                               ('/connect', Connect),
                               ('/login', Login),
                               ('/update', Update),
                               ('/quickadd', QuickAdd)],
                              debug=_DEBUG)
