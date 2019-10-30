from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_fixtures import load_fixtures_from_file
from flask_fixtures.loaders import YAMLLoader
from slackclient import SlackClient
import gitlab
from github import Github
import docker
import os


app = Flask(__name__)
app.config.from_object('config')

if not os.path.exists('./db'):
    os.mkdir('./db')

sc = SlackClient(app.config.get('SLACK_TOKEN'))
users_list = sc.api_call('users.list')
if users_list['ok']:
    app.config['SLACK_USERS'] = {user['profile'].get('display_name'): user.get('id') for user in users_list['members']}
db = SQLAlchemy(app)

gl = gitlab.Gitlab(app.config.get('GITLAB_URL'), private_token=app.config.get('GITLAB_TOKEN'))
if gl.version()[0] != 'unknown':
    gl.auth()

gh = Github(app.config.get('GITHUB_TOKEN'))

dc = docker.from_env()

from licenses.main.controllers import main_module
app.register_blueprint(main_module)

from licenses.fastcheck.controllers import fastcheck_module
app.register_blueprint(fastcheck_module)

db.create_all()
from licenses.main.models import LicensesList

if not db.session.query(LicensesList).first():
    load_fixtures_from_file(db, 'fixtures/licenses.yaml')
else:
    fixtures = YAMLLoader().load('fixtures/licenses.yaml')
    for fixture in fixtures[0].get('records'):
        if db.session.query(LicensesList).filter_by(license_name=fixture.get('license_name')).first() is None:
            new_event = LicensesList(**fixture)
            db.session.add(new_event)
    db.session.commit()
