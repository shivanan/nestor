#!/usr/bin/env python
from flask import Flask,render_template,request,session,redirect,url_for
from flaskext.kvsession import KVSessionExtension
from simplekv.memory import DictStore
import database
import db
import dropbox

DEBUG = True

app = Flask(__name__)
app.secret_key = 'ssshhhh!'


store = DictStore()
KVSessionExtension(store,app)

@app.route('/')
def index():
	if 'uid' in session:
		uid = session['uid']
		ds = database.DataStore()
		user = ds.get_user(uid)
		return render_template('userhome.html',user=user)
	return redirect(url_for ('login'))


@app.route('/login',methods=['GET','POST'])
def login():
	if request.method == 'GET':
		return render_template('login.html')

	email = request.form['email']
	password = request.form['password']
	try:
		ds = database.DataStore()
		user = ds.verify_user(email,password)
		session['uid'] = user['_id']
		return redirect('/')
	except Exception,e:
		return render_template('login.html',error=e.message,email=email)


@app.route('/signup',methods=['GET','POST'])
def signup():
	if request.method == 'GET':
		return render_template('signup.html')
	
	else:
		email = request.form['email']
		password = request.form['password']
		password2 = request.form['password2']

		error = ''

		try:
			if not email: raise Exception('No email address specified')
			if not password: raise Exception('No password specified')
			if password != password2: raise Exception('Passwords do not match')
			db =  database.DataStore()
			id =db.create_user({"email":email,"password":password})
			session['uid'] = id
			return redirect('/')
		except Exception,e:
			return render_template('signup.html',error=e.message,email=email)

@app.route('/linkaccount',methods=['POST'])
def linkaccount():
	if not 'uid' in session:
		return redirect(url_for('login'))
	dbs = db.get_session()
	req_token,url = db.authapp(dbs,'http://127.0.0.1:5000/linked')
	session['db_req_token'] = req_token.key + '###' + req_token.secret
	return redirect (url)

@app.route('/linked')
def linked():
	if not 'db_req_token' in session:
		raise Exception('No request token found')
	if not 'uid' in session:
		raise Exception('No user found')

	req_token_s = session['db_req_token']
	req_token = dropbox.session.OAuthToken(*req_token_s.split('###'))
	uid = session['uid']
	dbs = db.get_session()
	access_token = dbs.obtain_access_token(req_token)
	print 'access token!!!!',access_token.key,access_token.secret
	ds = database.DataStore()
	ds.update_user_token(uid,access_token.key,access_token.secret)
	return redirect('/')


if __name__ == '__main__':
    app.run(debug=DEBUG)
