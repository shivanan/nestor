#!/usr/bin/env python
import sys
from whoosh.index import create_in
from whoosh.fields import *
import os
import codecs
import reader
import db

schema = Schema(filename=TEXT(stored=True),title=TEXT(stored=True),content=TEXT,path=ID(stored=True))
if not os.path.exists('dbbind'):
    os.mkdir('dbbind')
ix = create_in('dbbind',schema)
writer = ix.writer()

client = db.get_client()
print 'got client'
def index_file(f,title):
    if not fnmatch.fnmatch(f,'*.*'): return
    try:
        def stream_reader(fr,limit=None):
            stream,data = client.get_file_and_metadata(fr)
            if limit:
                if data['bytes'] > limit:
                    print 'skipping due to limit',limit,data['bytes']
                    return None
            content = stream.read()
            print 'got metadata,content',len(content)
            return content
        cd = reader.readtext(f,stream_reader)
        if not cd: 
            cd = ''
        if not type(cd) is unicode:
            cd = reader.unicodify(cd)
        writer.add_document(title=unicode(title),path=unicode(f),filename=unicode(title),content=cd)
    except Exception,e:
        print 'skipping',e
        return
        pass

for root,dirs,files in db.walk(client,'/'):
    #print 'walking dirs',root,dirs,files
    for file in files:
        f = os.path.join(root,file)
        index_file(f,file)
writer.commit()
