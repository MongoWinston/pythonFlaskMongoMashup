# This file contains an example Flask-User application.
# To keep the example simple, we are applying some unusual techniques:
# - Placing everything in one file
# - Using class-based configuration (instead of file-based configuration)
# - Using string-based templates (instead of file-based templates)

from flask import Flask, render_template_string, jsonify, request


from flask_mongoengine import MongoEngine
from flask_user import login_required, UserManager, UserMixin


import logging
from os import environ
from os.path import join, dirname
from flask_cors import CORS
from dotenv import load_dotenv
import uuid
from BooksMgr import BooksMgr


#
# Constants
#
ENV_FILE = '.env'
DEFAULT_MONGODB_URL = 'mongodb://localhost:27017'
DB_NAME = 'bookdata'
COLL_NAME = 'books'
FLASK_ENV_VAR = 'FLASK_ENV'
FLASK_PROD_MODE = 'production'
FLASK_DEV_MODE = 'development'



# Class-based application configuration
class ConfigClass(object):
    """ Flask application config """

    # Flask settings
    SECRET_KEY = 'This is an INSECURE secret!! DO NOT use this in production!!'

    # Flask-MongoEngine settings
    MONGODB_SETTINGS = {
        'db': 'tst_app',
        'host': '<MongoURI>'
    }

    # Flask-User settings
    USER_APP_NAME = "Flask-User MongoDB App"      # Shown in and email templates and page footers
    USER_ENABLE_EMAIL = False      # Disable email authentication
    USER_ENABLE_USERNAME = True    # Enable username authentication
    USER_REQUIRE_RETYPE_PASSWORD = False    # Simplify register form

mongodb_url = environ.get('MONGODB_URL', DEFAULT_MONGODB_URL)
books_mgr = BooksMgr(mongodb_url, DB_NAME, COLL_NAME)

def create_app():
    """ Flask application factory """

    # Setup Flask and load app.config
    app = Flask(__name__)
    app.config.from_object(__name__+'.ConfigClass')

    # Setup Flask-MongoEngine
    db = MongoEngine(app)

    # Define the User document.
    # NB: Make sure to add flask_user UserMixin !!!
    class User(db.Document, UserMixin):
        active = db.BooleanField(default=True)

        # User authentication information
        username = db.StringField(default='')
        password = db.StringField()

        # User information
        first_name = db.StringField(default='')
        last_name = db.StringField(default='')

        # Relationships
        roles = db.ListField(db.StringField(), default=[])

    # Setup Flask-User and specify the User data-model
    user_manager = UserManager(app, db, User)

    # The Home page is accessible to anyone
    @app.route('/')
    def home_page():
        # String-based templates
        return render_template_string("""
            {% extends "flask_user_layout.html" %}
            {% block content %}
                <h2>Home page</h2>
                <p><a href={{ url_for('user.register') }}>Register</a></p>
                <p><a href={{ url_for('user.login') }}>Sign in</a></p>
                <p><a href={{ url_for('home_page') }}>Home page</a> (accessible to anyone)</p>
                <p><a href={{ url_for('member_page') }}>Member page</a> (login required)</p>
                <p><a href={{ url_for('user.logout') }}>Sign out</a></p>
            {% endblock %}
            """)

    # The Members page is only accessible to authenticated users via the @login_required decorator
    @app.route('/members')
    @login_required    # User must be authenticated
    def member_page():
        # String-based templates
        return render_template_string("""
            {% extends "flask_user_layout.html" %}
            {% block content %}
                <h2>Members page</h2>
                <p><a href={{ url_for('user.register') }}>Register</a></p>
                <p><a href={{ url_for('user.login') }}>Sign in</a></p>
                <p><a href={{ url_for('home_page') }}>Home page</a> (accessible to anyone)</p>
                <p><a href={{ url_for('member_page') }}>Member page</a> (login required)</p>
                <p><a href={{ url_for('user.logout') }}>Sign out</a></p>
            {% endblock %}
            """)

    @app.route('/books', methods=['GET', 'POST'])
    @login_required
    def all_books():
        try:
            if request.method == 'POST':
                data = request.get_json()

                if not data:
                    return 'No data provided in client request', 400

                data['id'] = uuid.uuid4().hex

                if books_mgr.create(data):
                    response_object = {'Inserted': {'id': data['id']}}
                else:
                    return 'Record was not inserted', 304
            else:
                response_object = books_mgr.list(request.args.get('skip'), request.args.get('limit'),
                                                 request.args.get('sortdesc'),
                                                 request.args.get('sortasc'))

            return jsonify(response_object)
        except ValueError as ve:
            logging.info(f'Issue with client request: "{ve}"')
            return f'Issue with client request: "{ve}"', 400
        except Exception as ex:
            logging.exception('Internal error processing REST request')
            return f'Internal error on server', 500


    return app


# Start development web server
if __name__=='__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=True)
