import docx
d = docx.opendocx('/Users/shivanan/Dropbox/go-samrakshanam.docx')
for x in  docx.getdocumenttext(d):
    print x
