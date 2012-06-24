#!/usr/bin/env python
import sys
from whoosh.index import create_in,open_dir
from whoosh.fields import *
from whoosh.query import *
from whoosh.qparser import QueryParser,MultifieldParser
import os
import codecs

schema = Schema(filename=TEXT(stored=True),title=TEXT(stored=True),content=TEXT,path=ID(stored=True))
ix = open_dir('dbbind')
print ix.schema
with ix.searcher() as searcher:
    print searcher.doc_count()
    query = MultifieldParser(['content','title'],ix.schema).parse(unicode(sys.argv[1]))
    r = searcher.search(query,terms=True)
    for x in r:
        print x
        #text = codecs.open(x['path'],encoding='utf-8').read()
        #print x.highlights('content',text=text)
        print ' '
