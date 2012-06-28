import pymongo
import datetime
import bcrypt
DB_SERVER = 'localhost'
DB_PORT = 27017
DB = 'nestor'

class InvalidUserException(Exception):pass
class AuthFailedException(Exception):pass
class UnknownUserException(Exception):pass

class DataStore(object):

	def __init__(self):
		self.con = None

	def connection(self):
		if not self.con:
			self.con = pymongo.Connection(DB_SERVER,DB_PORT)

		return self.con

	def db(self):
		return self.connection()[DB]
	
	def create_user(self,user):
		if not user.get('email'):
			raise  InvalidUserException('Email not provided')
		if not user.get('password'):
			raise InvalidUserException('Password not provided')
		
		user['password'] = bcrypt.hashpw(user['password'],bcrypt.gensalt())
		db = self.db()
		existing_user = db.users.find_one({'email':user['email']})
		if existing_user:
			raise InvalidUserException('Email address already exists')
		
		user['created'] = datetime.datetime.utcnow()
		id = db.users.insert(user)
		return id

	def verify_user(self,email,password):
		db = self.db()
		user = db.users.find_one({'email':email})
		if not user: raise AuthFailedException("No such user")

		pwd = user['password']
		print 'gottz',user,pwd
		if pwd != bcrypt.hashpw(password,pwd):
			raise AuthFailedException('Password mismatch')

		return user
	def update_user_token(self,id,key,secret):
		db = self.db()
		user = db.users.find_one({'_id':id})
		if not user: raise UnknownUserException()
		user['dbkey'] = key
		user['dbsecret'] = secret
		db.users.save(user)
	def get_user(self,id):
		db = self.db()
		return db.users.find_one({'_id':id})

	def get_path_for_user(self,id,path):
		db = self.db()
		return db.paths.find_one({"uid":id,"path":path})
	
	def set_path_for_user(self,id,path,metadata):
		db = self.db()
		path_data = {"uid":id,"path":path,"metadata":metadata}
		db.paths.update({"uid":id,"path":path},path_data,upsert=True)
		return path_data

	def linked_users(self):
		db = self.db()
		return db.users.find({"dbkey":{"$exists":True},"dbsecret":{"$exists":True}} )
		
	def get_document(self,id,file):
		db = self.db()
		x = db.files.find_one({"uid":id,"file":file})
		return x
	
	def update_indexed_time(self,uid,dt=None):
		if not dt:
			dt = datetime.datetime.utcnow()

		d = {}
		d['indexed_time'] = dt
		db = self.db()
		db.users.update({"_id":uid},{"$set":d})
	

	def save_document(self,id,file,indexed=False,modified=None,metadata=None,error=None):
		condition = {"uid":id,"file":file}
		
		modifications = {"indexed":indexed}
		if modified:
			modifications['modified'] = modified
		if metadata:
			modifications['metadata'] = metadata
		if error:
			modifications['error'] = error

		modifications['name'] = os.path.basename(file)

		db = self.db()
		db.files.update(condition,{"$set":modifications},upsert=True)
	
	def index_count(self,id):
		db = self.db()
		return db.files.find({"uid":id,"indexed":True}).count()
	

def get_user(id):
	return DataStore().get_user(id)

def test_add(email,password):
	ds = DataStore()
	user = {'email':email,'password':'abc'}
	return ds.create_user(user)

def test_login(email,password):
	ds = DataStore()
	return ds.verify_user(email,password)