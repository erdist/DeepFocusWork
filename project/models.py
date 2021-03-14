from flask_login import UserMixin
from . import db
from datetime import datetime


class User(db.Model, UserMixin):
	id = db.Column(db.Integer, primary_key=True) # SQLALCHEMY requires primary key
	email = db.Column(db.String(100), unique=True)
	password = db.Column(db.String(100))
	name = db.Column(db.String(1000))
	stripeId = db.Column(db.String(100), unique=True)
	deviceLimit = db.Column(db.Integer, default=0)
	isAdmin = db.Column(db.Boolean, default=False)
	isSubscribedToNewsletter = db.Column(db.Boolean, default=False)
	monthlyDistractionLimit = db.Column(db.Integer, default=0)


class Employee(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	email = db.Column(db.String(100), unique=True)
	password = db.Column(db.String(100))
	name = db.Column(db.String(1000))
	employer = db.Column(db.String(100))
	isSuspended = db.Column(db.Boolean, default=False)
	lastReportTime = db.Column(db.Integer, default=0)


class Plan:
	def __init__(self):
		self.basic = 'plan_GKmJsgshMj2l6Y'
		self.plus = 'plan_GKmKT28IzLO8kJ'
		self.pro = 'plan_GKmKk9OSQRHVpM'
		self.limit = 0


class Distraction(db.Model):
	#__bind_key__ = 'distraction'
	id = db.Column(db.Integer, primary_key=True)
	reason = db.Column(db.String(100))
	reasonDesc = db.Column(db.String(140))
	date = db.Column(db.Integer)
	deviceId = db.Column(db.Integer)
	userId = db.Column(db.Integer)
	user = db.Column(db.String(100), nullable=False)


class Device(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	employeeId = db.Column(db.Integer, unique=True)
	mapId = db.Column(db.Integer)
	deviceLocationX = db.Column(db.Integer)
	deviceLocationY = db.Column(db.Integer)


class MapInfo(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	userId = db.Column(db.Integer)
	imageUrl = db.Column(db.String(100))
	shapesJson = db.Column(db.TEXT)
