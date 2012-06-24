#!/usr/bin/env python
from flask import Flask,render_template,request,session
from flaskext.kvsession import KVSessionExtension
from simplekv.memory import DictStore
import database

DEBUG = True

app = Flask(__name__)
app.secret_key = 'ssshhhh!'


store = DictStore()
KVSessionExtension(store,app)

@app.route('/')
def index():
	if 'uid' in session:
		uid = session['uid']
		user = database.get_user(uid)
		return render_template('userhome.html',user=user)
    return 'Whatever'

@app.route('/sessiontest')
def sessiontest():
	if not 'count' in session:
		session['count'] = 1
	session['count'] = session['count']  + 1
	return 'Session Count:' + str(session['count'])

@app.route('/signup')
def signup(methods=['GET','POST']):
	if request.method == 'GET':
		return render_template('signup.html')
	
	else: # POST
	    return 'sign me up'

if __name__ == '__main__':
    app.run(debug=DEBUG)
