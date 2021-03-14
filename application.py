from flask import Flask
from project import create_app
from celery import Celery
from celery.schedules import crontab
from celery.utils.log import get_task_logger
from project import db
from project.models import User, Employee, Distraction
import yagmail
from datetime import datetime, timedelta
from dateutil import relativedelta

application = create_app()
logger = get_task_logger(__name__)


def make_celery(application):
    # Celery configuration
    application.config['CELERY_BROKER_URL'] = 'redis://localhost:6379/0'
    application.config['CELERY_RESULT_BACKEND'] = 'redis://localhost:6379/0'
    application.config['CELERYBEAT_SCHEDULE'] = {
        # Executes every minute
        'periodic_task-every-minute': {
            'task': 'periodic_task',
            'schedule': crontab(0, 0, day_of_month=1)
        }
    }

    celery = Celery(application.import_name, broker=application.config['CELERY_BROKER_URL'])
    celery.conf.update(application.config)
    TaskBase = celery.Task
    class ContextTask(TaskBase):
        abstract = True
        def __call__(self, *args, **kwargs):
            with application.app_context():
                return TaskBase.__call__(self, *args, **kwargs)
    celery.Task = ContextTask
    return celery

celery = make_celery(application)


@celery.task(name="periodic_task")
def sendMonthlyRawData():
    users = User.query.filter(User.isAdmin is True, User.isSubscribedToNewsletter is True, User.stripeId is not None)

    for user in users:
        contents = []
        employees = Employee.query.filter_by(employer=user.email)
        data = []
        for employee in employees:
            distractions = Distraction.query.filter(Distraction.user == employee.email,
                                                    Distraction.date > datetime.timestamp(datetime.utcnow() + relativedelta.relativedelta(months=-1)))
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
            contents.append(employee.name)
            contents.append("Colleague:" + str(data[0]))
            contents.append("Social:" + str(data[1]))
            contents.append("Personal:" + str(data[2]))
            contents.append("Noise:" + str(data[3]))
            contents.append("Depression:" + str(data[4]))

        emailInstance = yagmail.SMTP('deepfocuswork@gmail.com', 'TestTestTest...777')

        emailInstance.send(user.email, 'Your Monthly Report', contents)
    logger.info("Celery Task executed")


if __name__ == "__main__":
    application.run(debug=True, host='0.0.0.0')
