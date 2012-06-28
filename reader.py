import sys
import os
import docx
import popen2
import tempfile
def unicodify(txt):
    try:
        return unicode(txt)
    except UnicodeDecodeError:
        chars = [ch for ch in txt if ord(ch)<=126]
        return unicode(''.join(chars))
def stream_to_file(f,stream_reader):
    code,fn = tempfile.mkstemp()
    print 'saving',f,'to',fn

    content = stream_reader(f)
    if not content: return None

    stream = open(fn,'wb')
    stream.write(content)
    stream.close()
    print 'closed it',fn
    return fn
def readpdf(f,stream_reader):
    try:
        f = stream_to_file(f,stream_reader)
        if not f: return None
        print 'reading pdf',f
        stdout,stdin = popen2.popen2(('pdftotext',f,'-'))
        txt = stdout.read()
        stdout.close()
        stdin.close()
        return txt
    except Exception,e:
        sys.stderr.write('Error reading pdf:' + repr(e))
        return None
def readdocx(f,stream_reader):
    f = stream_to_file(f,stream_reader)
    if not f: return None
    d = docx.opendocx(f)
    txt = ''.join(x for x in docx.getdocumenttext(d))
    print 'reading docx',f,txt
    return txt

ExtensionMap = {
        '.docx':readdocx
        ,'.pdf':readpdf
}

def readtext(f,stream_reader):
    image_files = ['.jpg','.png','.psd','.gif','.bmp']
    audio_files = ['.mp3','.wav']
    video_files = ['.wmv','.avi','.mov','.mkv']
    
    base,extension = os.path.splitext(f.lower())
    
    if extension in image_files:
        return None
    if extension in audio_files:
        return None
    if extension in video_files:
        return None

    if extension in ExtensionMap:
        return ExtensionMap[extension](f,stream_reader)
    
    if stream_reader:
        data = stream_reader(f,limit=1024*1024*5)
        return unicodify(data)
    
    try:
        content = codecs.open(f,encoding='utf-8').read()
        return content
    except Exception,e:
        return None
