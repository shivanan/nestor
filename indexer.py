#!/usr/bin/env python
import sys
from whoosh.index import create_in
from whoosh.fields import *
import os
import codecs
import reader
import db
import database
import email.utils

def get_schema():
    schema = Schema(filename=TEXT(stored=True),title=TEXT(stored=True),content=TEXT,path=ID(stored=True))
    return schema

def get_index_dir(uid):
    return os.path.join('/Users/shivanan/indices',str(uid))


def parse_date(dts):
    return email.utils.parsedate_tz(dts)

def index_user(id):
    user = database.get_user(id)
    token = db.create_token(user['dbkey'],user['dbsecret'])
    ds = database.DataStore()
    session = db.get_session()
    client = db.get_client(user,session)

    index_path = get_index_dir(id)
    if not os.path.exists(index_path):
        print 'Creating index dir:',index_path
        os.mkdir(index_path)

    ix = create_in(index_path,get_schema())
    writer = ix.writer()
    
    def get_path(p):
        path_data = ds.get_path_for_user(id,p)
        if path_data: 
            print 'returning from db'
            return path_data #TODO - hash
        metadata = client.metadata(p)
        path_data = ds.set_path_for_user(id,p,metadata)
        return path_data

    def index_path(p):
        pd = get_path(p)
        md = pd['metadata']
        directories = [x['path'] for x in md['contents'] if x['is_dir'] ]
        files = [x['path'] for x in md['contents'] if not x['is_dir'] ]
        for f in files:
            index_file(f,f)

        for d in directories:
            index_path(d)

    def index_file(f,title):
        if not fnmatch.fnmatch(f,'*.*'): return

        indexed = False
        last_modified = None
        modified = None

        indexed_data = ds.get_document(id,f)

        if indexed_data:
            last_modified = indexed_data.get('modified')
        
        try:
            file_md = client.metadata(f)
            modified = parse_date(file_md['modified'])
            stale = (not last_modified) or ( (modified - last_modified).total_seconds() > 0 )
            
            if not stale:
                print 'No change',f

            def stream_reader(fr,limit=None):
                if limit:
                    if file_md['bytes'] > limit:
                        print 'skipping due to limit',limit,file_md['bytes']
                        return None
                
                stream,data = client.get_file_and_metadata(fr)
                content = stream.read()
                print 'got metadata,content',f,len(content)
                return content
            
            cd = reader.readtext(f,stream_reader)
            if not cd: 
                cd = ''
            if not type(cd) is unicode:
                cd = reader.unicodify(cd)
            writer.add_document(title=unicode(title),path=unicode(f),filename=unicode(title),content=cd)
            indexed = True
            ds.save_document(id,f,indexed=indexed,modified=modified,metadata=file_md)
        
        except Exception,e:
            print 'skipping',e
            ds.save_document(id,f,indexed=indexed,modified=modified,error=e.message)


    path = get_path('/')
    index_path('/')
    print 'committing',f
    writer.commit()


linked_users = database.DataStore().linked_users()
for user in linked_users:
    index_user(user['_id'])

# if not os.path.exists('dbbind'):
#     os.mkdir('dbbind')
# ix = create_in('dbbind',schema)
# writer = ix.writer()

# client = db.get_client()
# print 'got client'
# def index_file(f,title):
#     if not fnmatch.fnmatch(f,'*.*'): return
#     try:
#         def stream_reader(fr,limit=None):
#             stream,data = client.get_file_and_metadata(fr)
#             if limit:
#                 if data['bytes'] > limit:
#                     print 'skipping due to limit',limit,data['bytes']
#                     return None
#             content = stream.read()
#             print 'got metadata,content',len(content)
#             return content
#         cd = reader.readtext(f,stream_reader)
#         if not cd: 
#             cd = ''
#         if not type(cd) is unicode:
#             cd = reader.unicodify(cd)
#         writer.add_document(title=unicode(title),path=unicode(f),filename=unicode(title),content=cd)
#     except Exception,e:
#         print 'skipping',e
#         return
#         pass

# for root,dirs,files in db.walk(client,'/'):
#     #print 'walking dirs',root,dirs,files
#     for file in files:
#         f = os.path.join(root,file)
#         index_file(f,file)
# writer.commit()
