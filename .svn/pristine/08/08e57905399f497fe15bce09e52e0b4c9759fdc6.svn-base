# -*- coding: utf-8 -*- 
from flask_sqlalchemy import SQLAlchemy
from flask import Flask

app = Flask(__name__)
app.debug = True
app.secret_key = '514h4wyzj2mhy4k1j30yx34xxwlwiii4wl2ijy1h'

from setting import MYSQL_USER,MYSQL_PASS,MYSQL_HOST_M,MYSQL_HOST_S,MYSQL_PORT,MYSQL_DB
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://%s:%s@%s:%s/%s?charset=utf8' % (MYSQL_USER,MYSQL_PASS,MYSQL_HOST_M,MYSQL_PORT,MYSQL_DB)
app.config['UPLOAD_FOLDER'] = 'chartnet/static/fileupload'

class nullpool_SQLAlchemy(SQLAlchemy):
	def apply_driver_hacks(self, app, info, options):
		super(nullpool_SQLAlchemy, self).apply_driver_hacks(app, info, options)
		from sqlalchemy.pool import NullPool
		options['poolclass'] = NullPool
		del options['pool_size']

db = nullpool_SQLAlchemy(app)
import view