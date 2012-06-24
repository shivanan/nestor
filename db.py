# Dropbox API wrapper
import os
import dropbox
import webbrowser

#store in ~/.nestor - first line: app_key, second line: app_secret
APP_KEY = ''
APP_SECRET = ''

class NoAccessTokenException(Exception): pass

def get_config_path():
    return os.path.join(os.getenv('HOME'),'.nestor')

def save_access_token(token):
    stream = open(get_access_token_path(),'wb')
    stream.write(token.key + '\n')
    stream.write(token.secret)
    stream.close()

def loadkeys():
    global APP_KEY,APP_SECRET
    if not APP_KEY or not APP_SECRET:
        path = get_config_path()
        lines = open(path).read().splitlines()
        if len(lines) != 2:
            raise Exception('nestor conf expects the app_key and app_secret on separate lines')
        if not APP_KEY:
            APP_KEY = lines[0].strip()
        if not APP_SECRET:
            APP_SECRET = lines[1].strip()
    return APP_KEY,APP_SECRET
def get_session():
    key,secret = loadkeys()
    return dropbox.session.DropboxSession(key,secret,'dropbox')
def get_client(user):
    session = get_session()
    
    key,secret = user.get('dbkey'),user.get('dbsecret')
    if not key or not token:
        raise NoAccessTokenException()
    session.set_token(key,secret)
    return dropbox.client.DropboxClient(session)

def authapp(session,url):
    req_token = session.obtain_request_token()
    auth_url = session.build_authorize_url(req_token,url)
    return req_token,auth_url

def walk(client,path):
    md = client.metadata(path)
    directories = [x['path'] for x in md['contents'] if x['is_dir'] ]
    files = [x['path'] for x in md['contents'] if not x['is_dir'] ]
    yield path,directories,files
    for d in directories:
        for _p,_d,_f in walk(client,os.path.join(path,d)):
            yield _p,_d,_f


def get_client_try_auth():
    try:
        client = get_client()
        return client
    except NoAccessTokenException:
        authapp()
        client = get_client()
        return client
    #session,access_token = authapp()
    #client = dropbox.client.DropboxClient(session)
    #print 'client:',client.account_info()
    #print client.metadata('/')
