# -*- coding: utf-8 -*-
from functools import wraps
from flask import session, redirect, url_for, request

def login_required(f):
	
	@wraps(f)
	def do(*args, **kwargs):
		if 'username' not in session:
			#token = request.cookies.get('auto_login')
			#if token:
			#	userId,token = token.split('_')
			#	user = User.get_user_by_id(userId)
			#	from matrix import app
			#	if user and helper.md5(str(user.id)+user.password+app.config['SECURIY_KEY'])==token:
			#		session['userid']=user.id
			#	else:
			#		return redirect('/logout')
			#else:
			return redirect('/admin/login')
		return f(*args,**kwargs)
	return do