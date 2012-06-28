# Dropbox API wrapper
import os
import dropbox
import webbrowser
import config

#store in ~/.nestor - first line: app_key, second line: app_secret
APP_KEY = ''
APP_SECRET = ''

class NoAccessTokenException(Exception): pass


def loadkeys():
    global APP_KEY,APP_SECRET
    if not APP_KEY or not APP_SECRET:
        APP_KEY,APP_SECRET = config.get_dropbox_keys()
    return APP_KEY,APP_SECRET
def get_session():
    key,secret = loadkeys()
    return dropbox.session.DropboxSession(key,secret,'dropbox')
def get_client(user,session=None):
    if not session:
        session = get_session()
    
    key,secret = user.get('dbkey'),user.get('dbsecret')
    if not key or not secret:
        raise NoAccessTokenException()
    session.set_token(key,secret)
    return dropbox.client.DropboxClient(session)

def authapp(session,url):
    req_token = session.obtain_request_token()
    auth_url = session.build_authorize_url(req_token,url)
    return req_token,auth_url

def walk(client,md):
    md = client.metadata(path)
    directories = [x['path'] for x in md['contents'] if x['is_dir'] ]
    files = [x['path'] for x in md['contents'] if not x['is_dir'] ]
    yield path,directories,files
    for d in directories:
        for _p,_d,_f in walk(client,os.path.join(path,d)):
            yield _p,_d,_f


def create_token(key,secret):
    return dropbox.session.OAuthToken(key,secret)

def get_client_try_auth():
    try:
        client = get_client()
        return client
    except NoAccessTokenException:
        authapp()
        client = get_client()
        return client
