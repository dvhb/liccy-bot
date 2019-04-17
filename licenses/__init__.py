from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from slackclient import SlackClient
import gitlab
import docker

app = Flask(__name__)
app.config.from_object('config')

sc = SlackClient(app.config.get('SLACK_TOKEN'))
users_list = sc.api_call('users.list')
if users_list['ok']:
    app.config['SLACK_USERS'] = {user['profile'].get('display_name'): user.get('id') for user in users_list['members']}
db = SQLAlchemy(app)

gl = gitlab.Gitlab(app.config.get('GITLAB_URL'), private_token=app.config.get('GITLAB_TOKEN'))
if gl.version()[0] != 'unknown':
    gl.auth()

dc = docker.from_env()

from licenses.main.controllers import main_module
app.register_blueprint(main_module)

db.create_all()
