#!/usr/bin/env python
import sys
from whoosh.index import create_in,open_dir
from whoosh.fields import *
from whoosh.writing import BufferedWriter,IndexWriter
import os
import codecs
import reader
import db
import database
import email.utils
import datetime
import time
import multiprocessing
import config
import dropbox.rest as rest

INDEX_INTERVAL = 60*30

INDEX_PATH = None

def get_schema():
    schema = Schema(filename=TEXT(stored=True),title=TEXT(stored=True),content=TEXT,path=ID(stored=True,unique=True))
    return schema

def get_index_dir(uid):
    global INDEX_PATH
    
    if not INDEX_PATH:
        INDEX_PATH = config.get_index_path()
    
    return os.path.join(INDEX_PATH,str(uid))


#This is supposed to parse whatever string the dropbox api returns for 'modified'
#into a valid datetime.datetime object
def parse_date(dts):
    x = email.utils.parsedate_tz(dts)
    t = email.utils.mktime_tz(x)
    return datetime.datetime.fromtimestamp(time.mktime(x[:9]))

DOCUMENT_EXTENSIONS = [
    '.doc'
    ,'.docx'
    ,'.xls'
    ,'.xlsx'
    ,'.txt'
    ,'.pdf'
]

def isdoc(f):
    b,ext = os.path.splitext(f.lower())

    #Assume that files without any extension (README,REQUIREMENTS,TODO etc...) are text files
    if ext=='': 
        return True
    
    if ext in DOCUMENT_EXTENSIONS: return True



def index_user(id):
    user = database.get_user(id)
    user_email = user['email']
    token = db.create_token(user['dbkey'],user['dbsecret'])
    ds = database.DataStore()
    session = db.get_session()
    client = db.get_client(user,session)

    blacklisted_paths = ['/1Password.agilekeychain']
    ignore_extensions = ['.ppk','.pem','.pgp','.gpg','.ssh']

    index_path = get_index_dir(id)
    ix = None
    if not os.path.exists(index_path):
        print 'Creating index dir:',index_path
        os.mkdir(index_path)
        ix = create_in(index_path,get_schema())
    else:
        ix = open_dir(index_path)
    
    def get_path(p):
        path_data = ds.get_path_for_user(id,p)
        if path_data: 
            print 'returning path from db'
            hash = path_data['metadata']['hash']

            try:
                x = client.metadata(p,hash=hash)
            except rest.ErrorResponse,e:
                if e.status == 304: #Not modified - return last stored metadata
                    return path_data
                else:
                    raise 
        
        metadata = client.metadata(p)
        path_data = ds.set_path_for_user(id,p,metadata)
        return path_data

    def index_path(p):
        print 'Indexing',p
        components = p.strip('/').split('/')
        for b in blacklisted_paths:
            if p.lower().startswith(b.lower()):
                print 'Skipping path',p
                return
        pd = get_path(p)
        md = pd['metadata']
        directories = [x['path'] for x in md['contents'] if x['is_dir'] ]
        files = [x for x in md['contents'] if not x['is_dir'] ]
        for f in files:
            file_path = f['path']
            dir_part,ext = os.path.splitext(file_path.lower())
            if ext in ignore_extensions:
                print 'Ignoring file',file_path
                continue
            
            index_file(f,file_path,os.path.basename(file_path))

        for d in directories:
            index_path(d)

    writer = BufferedWriter(ix)
    def index_file(file_md,f,title):
        if not fnmatch.fnmatch(f,'*.*'): return

        indexed = False
        last_modified = None
        modified = None

        indexed_data = ds.get_document(id,f)

        if indexed_data:
            last_modified = indexed_data.get('modified')
        
        try:
            modified = parse_date(file_md['modified'])
            stale = (not last_modified) or ( (modified - last_modified).total_seconds() > 0 )
            
            if not stale:
                return
            print  '\033[94m','['+user_email+']',f,'haschanges',modified,last_modified,file_md['modified'],'\033[0m'

            def stream_reader(fr,limit=None):
                if limit:
                    if file_md['bytes'] > limit:
                        print 'skipping due to limit',limit,file_md['bytes']
                        return None
                
                stream,data = client.get_file_and_metadata(fr)
                content = stream.read()
                return content
            
            cd = reader.readtext(f,stream_reader)
            if not cd: 
                cd = ''
            if not type(cd) is unicode:
                cd = reader.unicodify(cd)
            writer.update_document(title=unicode(title),path=unicode(f),filename=unicode(title),content=cd)
            print 'commit'
            print 'closed'
            indexed = True
            ds.save_document(id,f,indexed=indexed,modified=modified,metadata=file_md)
        
        except Exception,e:
            print 'skipping',e
            raise e
            ds.save_document(id,f,indexed=indexed,modified=modified,error=e.message)


    index_path('/')
    writer.close()
    print 'committing'
    ds.update_indexed_time(id)


def index_users():
    processes = {}
    while True:
        linked_users = database.DataStore().linked_users()
        for user in linked_users:
            indexed_time = user.get('indexed_time')
            if indexed_time and (  (datetime.datetime.utcnow() - indexed_time).total_seconds() < INDEX_INTERVAL  ):
                continue
            if user['_id'] in processes:
                continue
            
            print "indexing",user
            print '\033[92m','indexing',user,'\033[0m'
            p = multiprocessing.Process(target=index_user, args=(user['_id'],) )
            p.start()
            processes[user['_id']] = p
        

        for uid,p in processes.items():
            if p.is_alive(): continue
            print 'Process for',uid,'no longer active'
            del processes[uid]

        time.sleep(2)


if __name__ == '__main__':
    index_users()
