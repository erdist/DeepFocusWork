from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect

db = SQLAlchemy()  # Initiate our database object


def create_app():
    app = Flask(__name__)

    csrf = CSRFProtect()
    csrf.init_app(app)

    app.config['SECRET_KEY'] = '9OLWxND4o83j4K4iuopO'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://focusapp:TestTestTest...777@deepfocuswork.ceng.metu.edu.tr:8080/testModels'
    app.config['SQLALCHEMY_POOL_RECYCLE'] = 3600
    app.config['RECAPTCHA_USE_SSL'] = False
    app.config['RECAPTCHA_PUBLIC_KEY'] = '6Lc9q9oUAAAAAJg2qNYbG1GdLiZMT_-Cjw_c2zWJ'
    app.config['RECAPTCHA_PRIVATE_KEY'] = '6Lc9q9oUAAAAAJibxFXuB-jvVoJO7SdrtwbXQofL'
    app.config['RECAPTCHA_SITE_KEY'] = '6Lc9q9oUAAAAAJg2qNYbG1GdLiZMT_-Cjw_c2zWJ'
    #app.config['SQLALCHEMY_BINDS'] = {'distraction': 'mysql+pymysql://focusapp:TestTestTest...777@deepfocuswork.ceng.metu.edu.tr:8080/deepfocuswork'}

    db.init_app(app)  # Initiate our app

    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    from .models import User

    @login_manager.user_loader
    def load_user(user_id):
        # since the user_id is just the primary key of our user table, use it in the query for the user
        return User.query.get(int(user_id))

    # Register blueprints
    # Blueprint for auth routes in our app
    from .auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint)

    # Blueprint for non-auth parts of app
    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    return app
