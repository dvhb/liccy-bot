import os

FILES_TO_GET = {
        'backend': {
            'files': ['Pipfile', 'Pipfile.lock', 'requirements.txt'],
            'directories': ['requirements']
            },
        'frontend': {
            'files': ['package.json', 'yarn.lock'],
            },
        }

DEBUG = True

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
SQLALCHEMY_DATABASE_URI = 'sqlite:///{}/licenses.db'.format(os.path.realpath('./db'))
SQLALCHEMY_TRACK_MODIFICATIONS = False

GITLAB_URL = os.getenv('GITLAB_URL')
GITLAB_USER = os.getenv('GITLAB_USER')
GITLAB_TOKEN = os.getenv('GITLAB_TOKEN')
GITLAB_REFERENCE = os.getenv('GITLAB_REFERENCE') if os.getenv('GITLAB_REFERENCE') is not None else 'master'

GITHUB_TOKEN = os.getenv('GITHUB_TOKEN') if os.getenv('GITHUB_TOKEN') is not None else None

SLACK_TOKEN = os.getenv('SLACK_TOKEN')
SLACK_SIGNING_SECRET = os.getenv('SLACK_SIGNING_SECRET')

LAWYERS = os.getenv('LAWYERS').split(',') if os.getenv('LAWYERS') else None
MANAGERS = os.getenv('MANAGERS').split(',') if os.getenv('MANAGERS') else None
MANAGERS_EMAIL = os.getenv('MANAGERS_EMAIL').split(',') if os.getenv('MANAGERS_EMAIL') else None
TAG_SET = os.getenv('TAG_SET').split(',') if os.getenv('TAG_SET') else None

CONFLUENCE_USER = os.getenv('CONFLUENCE_USER') if os.getenv('CONFLUENCE_USER') else None
CONFLUENCE_PASSWORD = os.getenv('CONFLUENCE_PASSWORD') if os.getenv('CONFLUENCE_PASSWORD') else None
CONFLUENCE_URL = os.getenv('CONFLUENCE_URL')
CONFLUENCE_TRANSLATION = os.getenv('CONFLUENCE_TRANSLATION')

MAIL_USERNAME = os.getenv('MAIL_USERNAME')
MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
MAIL_SERVER = os.getenv('MAIL_SERVER')
MAIL_PORT = os.getenv('MAIL_PORT')
MAIL_USE_SSL = os.getenv('MAIL_USE_SSL')
MAIL_FROM = os.getenv('MAIL_FROM')
MAIL_SUBJECT = os.getenv('MAIL_SUBJECT')
