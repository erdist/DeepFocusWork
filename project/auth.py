from flask import Blueprint, render_template, redirect, url_for, request, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required
from .models import User, Employee
from . import db
import re

auth = Blueprint('auth', __name__)


@auth.route('/login')
def login():
    return render_template('login.html')


@auth.route('/login', methods=['POST'])
def login_post():
    email = request.form.get('email')
    password = request.form.get('password')

    remember = True if request.form.get('remember') else False  # Remember Me feature

    user = User.query.filter_by(email=email).first()  # Find the user in Database
    reCaptchaResponse = request.form.get('g-recaptcha-response')

    #	if not reCaptchaResponse :
    #		flash('Fill Recaptcha')
    #		return redirect(url_for('auth.login'))

    if not user:
        flash('No such email exist.')
        return redirect(url_for('auth.login'))
    if not check_password_hash(user.password, password):
        flash('Wrong password.')
        return redirect(url_for('auth.login'))

    if user.isAdmin == False:
        employee = Employee.query.filter_by(email=email).first()

        if employee.isSuspended:
            flash('Your account is suspended.')
            return redirect(url_for('auth.login'))

    login_user(user, remember=remember)  # Login the user with Flask_login loginmanager

    return redirect(url_for('main.profile'))


@auth.route('/signup')
def signup():
    return render_template('signup.html')


@auth.route('/signup', methods=['POST'])
def signup_post():
    email = request.form.get('email')
    name = request.form.get('name')
    password = request.form.get('password')
    reCaptchaResponse = request.form.get('g-recaptcha-response')
    user = User.query.filter_by(email=email).first()  # If returns User, this means user with the email already exists.

    #	if not reCaptchaResponse :
    #		flash('Fill Recaptcha')
    #		return redirect(url_for('auth.login'))

    if user:  # if user is found redirect to signup page
        flash('User with this email already exists!')  # Warn User
        return redirect(url_for('auth.signup'))

    # Password Control
    if len(password) < 8:
        flash('Enter a password at least 8 characters.')
        return redirect(url_for('auth.signup'))
    uppercases = re.findall('([A-Z])', password)
    lowercases = re.findall('([a-z])', password)
    nums = re.findall('([0-9])', password)
    if len(uppercases) == 0 or len(lowercases) == 0 or len(nums) == 0:
        flash('Enter a password with following conditions: At least 1 uppercase, 1 lowercase and 1 numeric value')
        return redirect(url_for('auth.signup'))
    # Otherwise create user with generated password
    new_user = User(email=email, name=name, password=generate_password_hash(password, method='sha256'), stripeId=None, isAdmin=True, monthlyDistractionLimit=0)

    # Add the new user to database
    db.session.add(new_user)
    db.session.commit()

    flash("successfulLogin")

    return redirect(url_for('auth.login'))  # Redirect to login page


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))