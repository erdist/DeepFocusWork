from flask import Blueprint, render_template, jsonify, redirect, url_for, request, flash
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from random import sample
import time
import stripe
from .models import User, Plan, Distraction, Employee, MapInfo
from . import db
from datetime import datetime, timedelta
import yagmail
import os
import ast
import base64


# import os
# from flask import Flask, session
# from werkzeug.utils import secure_filename
# from flask_cors import CORS, cross_origin
# import logging

main = Blueprint('main', __name__)

publicKey = 'pk_test_Kl1I2Ljemz7E0gXiwyvdk05O00QCZrnDpW'
secretKey = 'sk_test_Jl46GEDFO6N2pFeLe9zdxnhn0072EwJMQf'

stripe.api_key = secretKey

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.isAdmin is False:
            flash("You are not allowed to do this action.")
            return redirect(url_for('main.profile'))
        return f(*args, **kwargs)
    return decorated_function


def subscription_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.stripeId is None:
            flash("You don't have an active subscription")
            return redirect(url_for('main.profile'))
        else:
            customer = stripe.Customer.retrieve(current_user.stripeId)
            customerSubscription = customer.subscriptions.data[0]
            cancelled_at = customerSubscription.canceled_at
            subscriptionEndTime = datetime.utcfromtimestamp(int(customerSubscription.current_period_end))
            currentTime = datetime.utcnow()
            if datetime.timestamp(currentTime) > datetime.timestamp(subscriptionEndTime):
                flash("Your subscription has expired.")
                return redirect(url_for('main.profile'))
        return f(*args, **kwargs)
    return decorated_function

@main.route('/')
def index():
    return render_template('index.html')


@main.route('/profile')
@login_required
def profile():
    subscriptionStatus = False
    subscriptionEndTime = None
    cancelled_at = None
    if current_user.stripeId is not None:
        subscriptionStatus = True
        customer = stripe.Customer.retrieve(current_user.stripeId)
        customerSubscription = customer.subscriptions.data[0]
        cancelled_at = customerSubscription.canceled_at
        subscriptionEndTime = datetime.utcfromtimestamp(int(customerSubscription.current_period_end))
    if cancelled_at is not None:
        cancelled_at = datetime.fromtimestamp(cancelled_at)
    users = Employee.query.filter_by(employer=current_user.email)
    employees = []
    if users:
        for user in users:
            employees.append({'name': user.name, 'email': user.email, 'lastReportTime': datetime.fromtimestamp(user.lastReportTime)})
    print(employees)
    return render_template('profile.html', name=current_user.name, endTime=subscriptionEndTime,
                           subscriptionStatus=subscriptionStatus, cancelled_at=cancelled_at, employees=employees, reload=time.time())

@main.route('/employee')
def employee():
    return render_template('employee.html', name=current_user.name, reload=time.time())


@main.route('/peekEmployee/<employee>')
def peekEmployee(employee):
    print("Called")
    print(employee)
    linedata = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    distractions = Distraction.query.filter(Distraction.user == employee, Distraction.date > datetime.timestamp(
        datetime.utcnow() - timedelta(days=1)))
    for distraction in distractions:
        hour = int(datetime.strftime(datetime.fromtimestamp(distraction.date), "%H"))
        if hour - 8 < len(linedata):
            linedata[hour - 8] += 1

    piedata = [0, 0, 0, 0, 0]
    distractions = Distraction.query.filter(Distraction.user == employee, Distraction.date > datetime.timestamp(
        datetime.utcnow() - timedelta(days=1)))
    for distraction in distractions:
        if distraction.reason == "Colleague":
            piedata[0] += 1
        elif distraction.reason == "Social":
            piedata[1] += 1
        elif distraction.reason == "Personal":
            piedata[2] += 1
        elif distraction.reason == "Noise":
            piedata[3] += 1
        elif distraction.reason == "Depression":
            piedata[4] += 1
    result = jsonify({'linedata': linedata, 'piedata': piedata})
    return result


@main.route('/pricing')
def pricing():
    basicPrice = int(getPlan('basic')[0].amount / 100)
    plusPrice = int(getPlan('plus')[0].amount / 100)
    proPrice = int(getPlan('pro')[0].amount / 100)
    return render_template('pricing.html', current_user=current_user, basicPrice=basicPrice, plusPrice=plusPrice,
                           proPrice=proPrice)


@main.route('/unsubscribe')
@admin_required
def unsubscribe():
    customer = stripe.Customer.retrieve(current_user.stripeId)
    customerSubscriptionId = customer.subscriptions.data[0].id
    #stripe.Subscription.delete(customerSubscriptionId)

    stripe.Subscription.modify(
        customerSubscriptionId,
        cancel_at_period_end=True
    )

    employees = Employee.query.filter_by(employer=current_user.email)

    for employee in employees:
        setattr(employee, "isSuspended", True)
        db.session.commit()

    #setattr(current_user, "stripeId", None)
    db.session.commit()
    return redirect(url_for('main.profile'))


def getPlan(planId):
    plan_ = Plan()
    plan = None
    if planId == 'basic':
        plan = (stripe.Plan.retrieve(plan_.basic), 5)
    elif planId == 'plus':
        plan = (stripe.Plan.retrieve(plan_.plus), 25)
    elif planId == 'pro':
        plan = (stripe.Plan.retrieve(plan_.pro), -1)

    return plan




@main.route('/pay/<planName>')
def pay(planName):
    plan = getPlan(planName)[0]
    price = plan.amount

    return render_template('pay.html', price=price / 100, centPrice=price, publicKey=publicKey, planName=planName, currentemail=current_user.email)


@main.route('/paymentProcess/<planId>', methods=['POST'])
def paymentProcess(planId):
    plan = getPlan(planId)[0]
    devicelimit = getPlan(planId)[1]

    customer = stripe.Customer.create(email=request.form['stripeEmail'], source=request.form['stripeToken'])
    subscription = stripe.Subscription.create(
        customer=customer.id,
        items=[
            {
                "plan": plan.id,
            },
        ],
        expand=["latest_invoice.payment_intent"]
    )
    setattr(current_user, "stripeId", customer.id)
    setattr(current_user, "deviceLimit", devicelimit)
    db.session.commit()
    return redirect(url_for('main.profile'))


@main.route('/subscribenewletter')
@login_required
@admin_required
def subscribenewsletter():

    if not current_user.isSubscribedToNewsletter:
        setattr(current_user, "isSubscribedToNewsletter", True)
        db.session.commit()

        emailInstance = yagmail.SMTP('deepfocuswork@gmail.com', 'TestTestTest...777')
        contents = ['You have successfully subscribed to our newsletter.']

        emailInstance.send(current_user.email, 'Subscription to DeepFocusWork\'s newsletter', contents)

    return redirect(url_for('main.admin'))

@main.route('/unsubscribenewletter')
@login_required
@admin_required
def unsubscribenewsletter():
    if current_user.isSubscribedToNewsletter:
        setattr(current_user, "isSubscribedToNewsletter", False)
        db.session.commit()
    return redirect(url_for('main.admin'))

@main.route('/admin')
@login_required
@admin_required
@subscription_required
def admin():
    return render_template('admin.html', name=current_user.name, reload=time.time(), limit=current_user.monthlyDistractionLimit)


@main.route('/addDevice', methods=['POST'])
@login_required
@admin_required
@subscription_required
def addDevice():
    email = request.form.get('email')
    name = request.form.get('name')
    password = request.form.get('password')

    deviceCount = Employee.query.filter_by(employer=current_user.email).count()
    deviceLimit = current_user.deviceLimit
    print(deviceLimit, deviceCount)

    if (deviceLimit != -1) and deviceCount >= deviceLimit:
        flash("You have exceeded your device limit.")
        return redirect(url_for('main.admin'))
    employee = Employee.query.filter_by(email=email).first()

    if employee:
        flash("This user is already exists")
        return redirect(url_for('main.admin'))

    new_employee = Employee(email=email,
                            name=name,
                            password=generate_password_hash(password, method='sha256'),
                            lastReportTime=0,
                            employer=current_user.email)

    new_user = User(email=email,
                    name=name,
                    password=generate_password_hash(password, method='sha256'),
                    stripeId=None,
                    deviceLimit=0,
                    isAdmin=False)
    db.session.add(new_user)
    db.session.add(new_employee)
    db.session.commit()

    return redirect(url_for('main.profile'))


@main.route('/deleteDevice/<employee>')
@login_required
@admin_required
def deleteDevice(employee):
    findInEmployee = Employee.query.filter_by(email=employee, employer=current_user.email).first()
    findInUser = User.query.filter_by(email=employee).first()
    if not findInEmployee:
        flash("No such user exists in your employee list.")
        return redirect(url_for('main.profile'))
    distractions = Distraction.query.filter_by(user=employee)
    employeeName = findInEmployee.name
    for distraction in distractions:
        db.session.delete(distraction)
    db.session.delete(findInEmployee)
    db.session.delete(findInUser)
    db.session.commit()
    flash("You have successfully deleted your employee " + employeeName + " along with their distractions.")
    return redirect(url_for('main.profile'))



@main.route('/addDeviceFromDrawMap', methods=['POST'])
@login_required
@admin_required
@subscription_required
def addDeviceFromDrawMap():
    email = request.form.get('email')
    name = request.form.get('name')
    password = request.form.get('password')

    deviceCount = Employee.query.filter_by(employer=current_user.email).count()
    deviceLimit = current_user.deviceLimit

    if (deviceLimit != 1) and deviceCount >= deviceLimit:
        flash("You have exceed your device limit.")
        return jsonify({'err': "You have exceed your device limit."})
    employee = Employee.query.filter_by(email=email).first()

    if employee:
        flash("This user is already exists")
        return jsonify({'err': "This user is already exists"})

    new_employee = Employee(email=email,
                            name=name,
                            password=generate_password_hash(password, method='sha256'),
                            employer=current_user.email)

    new_user = User(email=email,
                    name=name,
                    password=generate_password_hash(password, method='sha256'),
                    stripeId=None,
                    deviceLimit=0,
                    isAdmin=False)
    db.session.add(new_user)
    db.session.add(new_employee)
    db.session.commit()

    return jsonify({"new_user": {
                        "id": new_user.id,
                        "email": email,
                        "name": name,
                        "password": generate_password_hash(password, method='sha256'),
                        "stripeId": None,
                        "deviceLimit": 0,
                        "isAdmin": False
                    }, "new_employee": {
                        "id": new_employee.id,
                        "email": email,
                        "name": name,
                        "password": generate_password_hash(password, method='sha256'),
                        "employer": current_user.email}
                    })


@main.route('/pieChartData/<option>')
@login_required
@admin_required
def pieChartData(option):
    users = Employee.query.filter_by(employer=current_user.email)
    colleague = 0
    Social = 0
    Personal = 0
    noise = 0
    depression = 0
    if option == "yearly":
        for user in users:
            colleague += Distraction.query.filter(Distraction.reason == 'Colleague', Distraction.user == user.email, Distraction.date > datetime.timestamp(
                                                        datetime.utcnow() - timedelta(days=365))).count()
            Social += Distraction.query.filter(Distraction.reason == 'Social', Distraction.user == user.email, Distraction.date > datetime.timestamp(
                                                        datetime.utcnow() - timedelta(days=365))).count()
            Personal += Distraction.query.filter(Distraction.reason == 'Personal', Distraction.user == user.email, Distraction.date > datetime.timestamp(
                                                        datetime.utcnow() - timedelta(days=365))).count()
            noise += Distraction.query.filter(Distraction.reason == 'Noise', Distraction.user == user.email, Distraction.date > datetime.timestamp(
                                                        datetime.utcnow() - timedelta(days=365))).count()
            depression += Distraction.query.filter(Distraction.reason == 'Depression', Distraction.user == user.email, Distraction.date > datetime.timestamp(
                                                        datetime.utcnow() - timedelta(days=365))).count()
    elif option == "daily":
        for user in users:
            colleague += Distraction.query.filter(Distraction.reason == 'Colleague', Distraction.user == user.email, Distraction.date > datetime.timestamp(
                                                        datetime.utcnow() - timedelta(days=1))).count()
            Social += Distraction.query.filter(Distraction.reason == 'Social', Distraction.user == user.email, Distraction.date > datetime.timestamp(
                                                        datetime.utcnow() - timedelta(days=1))).count()
            Personal += Distraction.query.filter(Distraction.reason == 'Personal', Distraction.user == user.email, Distraction.date > datetime.timestamp(
                                                        datetime.utcnow() - timedelta(days=1))).count()
            noise += Distraction.query.filter(Distraction.reason == 'Noise', Distraction.user == user.email, Distraction.date > datetime.timestamp(
                                                        datetime.utcnow() - timedelta(days=1))).count()
            depression += Distraction.query.filter(Distraction.reason == 'Depression', Distraction.user == user.email, Distraction.date > datetime.timestamp(
                                                        datetime.utcnow() - timedelta(days=1))).count()
    elif option == "random":
        return jsonify({'data': sample(range(20, 100), 5)})
    result = jsonify({'data': [colleague, Social, Personal, noise, depression]})
    return result

@main.route('/pieChartData/<employee>')
@login_required
def pieChartDataForEmployee(employee):
    id = Employee.query.filter_by(email=employee)

    collegue = Distraction.query.filter_by(Distraction='Colleague', userId=id).count()
    Social = Distraction.query.filter_by(Distraction='Social', userId=id).count()
    Personal = Distraction.query.filter_by(Distraction='Personal', userId=id).count()
    noise = Distraction.query.filter_by(Distraction='Noise', userId=id).count()
    depression = Distraction.query.filter_by(Distraction='Depression', userId=id).count()
    result = jsonify({'data': [collegue, Social, Personal, noise, depression]})
    return result


@main.route('/insertDistraction/<distraction>')
@login_required
def insertDistraction(distraction):
    employee = Employee.query.filter_by(email=current_user.email).first()
    if(employee.isSuspended):
        flash("It seems like your employer needs to refresh their subscription.")
    newDistraction = Distraction(reason=distraction, date=datetime.timestamp(datetime.utcnow()), userId=current_user.id, user=current_user.email, deviceId=current_user.id)

    if datetime.utcnow() - timedelta(minutes=1) < datetime.fromtimestamp(employee.lastReportTime):
        flash("You have to wait a bit. Don't abuse the system. Remaining time:" + str((datetime.fromtimestamp(employee.lastReportTime) + timedelta(minutes=1) - datetime.utcnow()).seconds) + " seconds!")
        return redirect(url_for('main.employee'))
    else:
        setattr(employee, "lastReportTime", newDistraction.date)
        db.session.add(newDistraction)
        db.session.commit()
        flash("You have successfully reported.")
    return redirect(url_for('main.employee'))


@main.route('/totalDistractionCount')
@login_required
@admin_required
def totalDistractionCount():
    users = Employee.query.filter_by(employer=current_user.email)
    count = 0
    for user in users:
        count += Distraction.query.filter_by(user=user.email).count()
    return jsonify({'data': count})


@main.route('/monthlyDistractionCount')
@login_required
@admin_required
def monthlyDistractionCount():
    users = Employee.query.filter_by(employer=current_user.email)
    count = 0
    for user in users:
        distractions = Distraction.query.filter(Distraction.user == user.email, Distraction.date > datetime.timestamp(
            datetime.utcnow() - timedelta(days=30))).count()
        count += distractions
    return jsonify({'data': count})


@main.route('/setMonthlyLimit', methods=['POST'])
@login_required
@admin_required
def setMonthlyLimit():
    limit = request.form.get('limit')
    user = User.query.filter_by(email=current_user.email).first()
    setattr(user, "monthlyDistractionLimit", limit)
    db.session.commit()
    return redirect(url_for('main.admin'))


@main.route('/lineChartData/<option>')
@login_required
@admin_required
def lineChartData(option):
    print(option)
    users = Employee.query.filter_by(employer=current_user.email)
    data = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    if option == "random":
        return jsonify({'data': sample(range(20, 100), 12)})
    for user in users:
        if option == "yearly":
            distractions = Distraction.query.filter(Distraction.user == user.email, Distraction.date > datetime.timestamp(
                datetime.utcnow() - timedelta(days=365)))
            for distraction in distractions:
                month = int(datetime.strftime(datetime.fromtimestamp(distraction.date), "%m"))
                data[month - 1] += 1
        elif option == "daily":
            distractions = Distraction.query.filter(Distraction.user == user.email,
                                                    Distraction.date > datetime.timestamp(
                                                        datetime.utcnow() - timedelta(days=1)))
            for distraction in distractions:
                hour = int(datetime.strftime(datetime.fromtimestamp(distraction.date), "%H"))
                if hour - 8 < len(data):
                    data[hour - 8] += 1
        elif option == "random":
            print("Girdim")
            print(sample(range(20, 100), 12))
            return jsonify({'data': sample(range(20, 100), 12)})

    result = jsonify({'data': data})
    return result


@main.route('/lineChartDataFor/<employee>')
@login_required
def lineChartDataForEmployee(employee):
    email = Employee.query.filter_by(email=employee)

    count = Distraction.query.filter_by(user=email).count()
    data = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, count]
    result = jsonify({'data': data})
    return result


@main.route('/employeeHourlyLineChartData')
@login_required
def employeeHourlyLineChartData():

    user = Employee.query.filter_by(email=current_user.email).first()
    data = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    distractions = Distraction.query.filter(Distraction.user == user.email, Distraction.date > datetime.timestamp(datetime.utcnow() - timedelta(days=1)))
    for distraction in distractions:
        hour = int(datetime.strftime(datetime.fromtimestamp(distraction.date), "%H"))
        if hour - 8 < len(data) :
            data[hour - 8] +=1

    result = jsonify({'data': data})
    return result


@main.route('/employeeHourlyPieChartData')
@login_required
def employeeHourlyPieChartData():

    user = Employee.query.filter_by(email=current_user.email).first()
    data = [0,0,0,0,0]
    distractions = Distraction.query.filter(Distraction.user == user.email, Distraction.date > datetime.timestamp(
        datetime.utcnow() - timedelta(days=1)))
    for distraction in distractions:
        if distraction.reason == "Colleague":
            data[0] += 1
        elif distraction.reason == "Social":
            data[1] += 1
        elif distraction.reason == "Personal":
            data[2] += 1
        elif distraction.reason == "Noise":
            data[3] += 1
        elif distraction.reason == "Depression":
            data[4] += 1

    result = jsonify({'data': data})
    return result


@main.route('/giveMeARecommendation/<employee>')
@login_required
@admin_required
def recommend(employee):
    result = {'colleagueId': "", 'socialId': "", 'personalId': "", "noiseId1": "", "noiseId2": "", 'depressionId': ""}
    user = Employee.query.filter_by(email=employee).first()
    data = [0, 0, 0, 0, 0]
    distractions = Distraction.query.filter(Distraction.user == user.email, Distraction.date > datetime.timestamp(
        datetime.utcnow() - timedelta(days=1)))
    for distraction in distractions:
        if distraction.reason == "Colleague":
            data[0] += 1
        elif distraction.reason == "Social":
            data[1] += 1
        elif distraction.reason == "Personal":
            data[2] += 1
        elif distraction.reason == "Noise":
            data[3] += 1
        elif distraction.reason == "Depression":
            data[4] += 1

    if data[0] >= 3:
        result['colleagueId'] = "Your employee " + user.name +" is being distracted from their colleagues. You may ask why he/she is getting distracted."
    if data[1] >= 1:
        result['socialId'] = "It looks like your employee didn't left their phone in silent mode. You may apply a silence policy in office except emergency calls."
    if data[2] >= 10:
        result['personalId'] = "This employee seems like he/she is being distracted due to his/her personal needs. This amount of distraction in a day is a bit suspicious."
    if data[3] >= 2:
        result['noiseId1'] = "This employee's working area seems to be noisy. You might consider changing his/her desk."
    if data[3] >= 5:
        result['noiseId2'] = "Your employee is heavily affected by the noise. It might have affected your other employees as well."
    if data[4] >= 1:
        result['depressionId'] = "This one is serious. Your employee is in depression. You should really consider giving them a one-day break."

    return jsonify(result)


@main.route('/heatMap')
@login_required
@admin_required
def heatMap():
    map_query = MapInfo.query.filter_by(userId=current_user.id)
    if map_query.count() > 0:
        map_of_user = map_query.first()
        image_url = map_of_user.imageUrl
        shapes_json = map_of_user.shapesJson.replace('"', "'")
    else:
        image_url = ''
        shapes_json = '[]'
    return render_template('/heatMap/index.html', name=current_user.name, update_interval='3000',
                           image_url=image_url, shapes_json=shapes_json, reload=time.time())

@main.route('/drawMap')
@login_required
@admin_required
def drawMap():
    employee_list = Employee.query.filter_by(employer=current_user.email)
    user_list = []
    for one_employee in employee_list:
        user_of_employee = User.query.filter_by(email=one_employee.email).first()
        an_employee = {
            "userId": user_of_employee.id,
            "name": one_employee.name
        }
        user_list.append(an_employee)
    map_query = MapInfo.query.filter_by(userId=current_user.id)
    if map_query.count() > 0:
        map_of_user = map_query.first()
        image_url = map_of_user.imageUrl
        shapes_json = map_of_user.shapesJson.replace('"', "'")
    else:
        image_url = ''
        shapes_json = '[]'
    return render_template('/drawMap/index.html', name=current_user.name, image_url=image_url,
                           shapes_json=shapes_json, deviceLimit=current_user.deviceLimit, users=user_list)


@main.route('/allData')
def allDataAll():
    allData = Distraction.query.order_by(Distraction.date.asc()).all()
    min = allData[0].date
    max = allData[-1].date
    allDataToReturn = []
    for data in allData:
        oneData = {
            'Distraction': data.reason,
            'date': data.date,
            'deviceID': data.deviceId}
        allDataToReturn.append(oneData)
    return jsonify({'minMax': {'min': min, 'max': max}, 'data': allDataToReturn})

@main.route('/allData/<filter>')
def allData(filter):
    if filter == 'Year':
        allData = Distraction.query.filter(Distraction.date > datetime.timestamp(
        datetime.utcnow() - timedelta(days=365))).order_by(Distraction.date.asc())
    elif filter == 'Month':
        allData = Distraction.query.filter(Distraction.date > datetime.timestamp(
        datetime.utcnow() - timedelta(days=30))).order_by(Distraction.date.asc())
    elif filter == 'Week':
        allData = Distraction.query.filter(Distraction.date > datetime.timestamp(
        datetime.utcnow() - timedelta(days=7))).order_by(Distraction.date.asc())
    elif filter == 'Day':
        allData = Distraction.query.filter(Distraction.date > datetime.timestamp(
        datetime.utcnow() - timedelta(days=1))).order_by(Distraction.date.asc())
    else:
        allData = Distraction.query.order_by(Distraction.date.asc()).all()
    min = allData[0].date
    max = allData[-1].date
    allDataToReturn = []
    for data in allData:
        oneData = {
            'Distraction': data.reason,
            'date': data.date,
            'deviceID': data.deviceId}
        allDataToReturn.append(oneData)
    return jsonify({'minMax': {'min': min, 'max': max}, 'data': allDataToReturn})


UPLOAD_FOLDER = 'project/static/uploads'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}


@main.route('/upload', methods=['POST'])
@login_required
@admin_required
def fileUpload():
    shapes = request.form["shapes"]
    find_admin = MapInfo.query.filter_by(userId=current_user.id)
    if find_admin.count() == 0:
        image_url = ''
    else:
        image_url = find_admin.first().imageUrl
    if request.form["doesImageExist"] == 'true':
        target = os.path.join(os.getcwd(), UPLOAD_FOLDER, 'uploadedPictures')
        if not os.path.isdir(target):
            os.mkdir(target)
        filename = request.form["filename"]
        if filename != 'null':
            file = base64.b64decode(request.form["base64image"].split(',')[1])
            destination = "/".join([target, current_user.name + "_" + filename])
            with open(destination, "wb+") as f:
                f.write(file)
            image_url = "static/uploads/uploadedPictures/" + current_user.name + "_" + filename
    if find_admin.count() == 0:
        new_admin = MapInfo(userId=current_user.id, imageUrl=image_url, shapesJson=shapes)
        db.session.add(new_admin)
        db.session.commit()
    else:
        find_admin.first().imageUrl = image_url
        find_admin.first().shapesJson = shapes
        db.session.commit()
    return jsonify({"message": "success"})
    

def giveReport(day_number): #if day_number == 7, give report for last 7 days.
    user = Employee.query.filter_by(email=current_user.email).first()
    data = [0,0,0,0,0]
    distractions = Distraction.query.filter(Distraction.user == user.email, Distraction.date > datetime.timestamp(
        datetime.utcnow() - timedelta(days=day_number)))
    for distraction in distractions:
        if distraction.reason == "Colleague":
            data[0] += 1
        elif distraction.reason == "WC":
            data[1] += 1
        elif distraction.reason == "Noise":
            data[2] += 1
        elif distraction.reason == "Drink":
            data[3] += 1
        elif distraction.reason == "Depression":
            data[4] += 1

    maxi = max(data)
    if maxi == data[0]:
        most_reason = "Colleague"
        recommendaton = ("User {} is suffering from his/her collagues. ".format(user) +
                         "Other people distructs him/her a lot. You may consider warn his/her team about this.")
    elif maxi == data[1]:
        most_reason = "WC"
        recommendaton = ("User {} is giving breaks mainly for toilet. Nothing important here.".format(user))
    elif maxi == data[2]:
        most_reason = "Noise"
        recommendaton = ("User {} is sitting a noisy place. ".format(user) +
                        "You may consider finding the source of the noise or change his/her desk.")
    elif maxi == data[3]:
        most_reason = "Drink"
        recommendaton = ("User {} likes to drink a lot. ".format(user) +
                        "Maybe you should present a coffe machine to him/her.")
    else:
        most_reason = "Depression"
        recommendaton = ("Just leave user {} alone for a while. ".format(user) +
                        "He/she is not feeling good these days.")
            
    f = open("report.txt", "w")
    report1 = "User {} distructed {} times in the last {} days. \n".format(user, len(distructions), day_number)
    f.write(report1)
    report2 = "Distruction reasons are these: \n"
    f.write(report2)
    report3 = ["Colleague: {} \n".format(data[0]), "WC: {} \n".format(data[1]), 
               "Noise: {} \n".format(data[2]), "Drink: {} \n".format(data[3]), 
               "Depression: {} \n".format(data[4])]
    f.write(report3)
    f.write(recommendation)
    f.close()

