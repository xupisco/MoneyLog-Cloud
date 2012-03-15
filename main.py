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

HOST = 'moneylog-cloud.aurelio.net' if not _DEBUG else 'localhost:8087'
MONEYLOG_FOLDER = '/MoneyLog Cloud/'
MONEYLOG_DATA_FOLDER = 'txt/'
MONEYLOG_PLUGINS_FOLDER = 'plugins/'
MONEYLOG_DATA = 'moneylog.txt'
MONEYLOG_CONFIG = 'config.js'
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
            'auth_url': url,
            'file': 'arquivo_salame.txt'
        }
        self.generate('error_charset.html', data)


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
        save = dude.put_file(MONEYLOG_DATA_FOLDER + filename, temp.read(), overwrite=True)
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
            raw_config = open('samples/moneylog_config.js', 'r')
            ml_config = raw_config.read()
            raw_config.close()
            save = dude.put_file(MONEYLOG_CONFIG, ml_config)

        # Data folder exists?
        try:
            dude.file_create_folder(MONEYLOG_DATA_FOLDER)
        except:
            pass

        # Read data directory
        ml_dir = dude.metadata(MONEYLOG_DATA_FOLDER)
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
                ml_data = dude.get_file(MONEYLOG_DATA_FOLDER + basic_file).read()
            except:
                raw_file = open('samples/moneylog_rawdata.txt', 'r')
                ml_data = raw_file.read()
                raw_file.close()
                save = dude.put_file(MONEYLOG_DATA_FOLDER + MONEYLOG_DATA, ml_data)
        
        
        # Read plugins directory
        # First, try to create the folder and a sample plugin
        try:
            dude.file_create_folder(MONEYLOG_PLUGINS_FOLDER)
            raw_plugin = open('samples/moneylog_plugin.js', 'r')
            plugin_sample = raw_plugin.read()
            raw_plugin.close()
            save = dude.put_file(MONEYLOG_PLUGINS_FOLDER + 'sample_plugin.js', plugin_sample)
        except:
            pass

        mlp_dir = dude.metadata(MONEYLOG_PLUGINS_FOLDER)
        mlp_files = ['']
        plugins = ''

        for f in mlp_dir['contents']:
            if "mime_type" in f:
                if f['mime_type'] == "application/javascript":
                    plugins += '\n\n' + dude.get_file(f['path']).read().decode('utf-8')


        config_script = "<script type='text/javascript'>\n%s\n\n%s\n\n// Plugins%s</script>" % (ml_config.decode("utf-8"), ml_files_js, plugins)

        if not reloading:
            try:
                data = {
                    'ml_data': ml_data.decode('utf-8'),
                    'user_config': config_script,
                    'ml_files': ml_files,
                }
                self.generate('moneylog.html', data)
            except:
                self.generate('error_charset.html', { 'file': filename} )
        else:
            self.response.out.write(ml_data.decode('utf-8'))


app = webapp2.WSGIApplication([('/', Main),
                               ('/connect', Connect),
                               ('/login', Login),
                               ('/update', Update)],
                              debug=_DEBUG)
