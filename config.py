import os

DEBUG = True

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
SQLALCHEMY_DATABASE_URI = 'sqlite:///{}/licenses.db'.format(os.path.realpath('./db'))
SQLALCHEMY_TRACK_MODIFICATIONS = False

GITLAB_URL = os.getenv('GITLAB_URL')
GITLAB_USER = os.getenv('GITLAB_USER')
GITLAB_TOKEN = os.getenv('GITLAB_TOKEN')

SLACK_TOKEN = os.getenv('SLACK_TOKEN')
SLACK_SIGNING_SECRET = os.getenv('SLACK_SIGNING_SECRET')

LAWYERS = os.getenv('LAWYERS').split(',') if os.getenv('LAWYERS') else None
MANAGERS = os.getenv('MANAGERS').split(',') if os.getenv('MANAGERS') else None
TAG_SET = os.getenv('TAG_SET').split(',') if os.getenv('TAG_SET') else None
