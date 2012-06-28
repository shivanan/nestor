import ConfigParser
import os

##########################################################
# Config File Format:
#
#  [dropbox]
#  key = ssshhhhh
#  secret = sshhhhhh
#
#  [index]
#  path = /path/to/index/root/directory
#
##########################################################

def cfg():
	p = ConfigParser.ConfigParser()
	p.read(['nestor.conf',os.path.expanduser('~/.nestor')])
	return p

def get_dropbox_keys():
	c = cfg()
	key = c.get('dropbox','key')
	secret = c.get('dropbox','secret')
	return key,secret

def get_index_path():
	c = cfg()
	return c.get('index','path')

