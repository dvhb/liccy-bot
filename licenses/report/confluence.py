from licenses import app, db
from licenses.main.models import LicensesList, Licenses
from flask import render_template

from urllib.parse import urlparse
import ast
import requests

import threading
import time

CONFLUENCE_USER = app.config.get('CONFLUENCE_USER')
CONFLUENCE_PASSWORD = app.config.get('CONFLUENCE_PASSWORD')
CONFLUENCE_TRANSLATION = app.config.get('CONFLUENCE_TRANSLATION')
CONFLUENCE_URL = app.config.get('CONFLUENCE_URL')
CONFLUENCE_PAGE_NAME = app.config.get('CONFLUENCE_PAGE_NAME')


def confluence():
    # it needs to be a dict
    translation = ast.literal_eval(CONFLUENCE_TRANSLATION)
    project_types = ['backend', 'frontend', 'backend_pipfile']
    project_keys = db.session.query(Licenses.project).distinct().all()
    whitelist = [i.license_name for i in db.session.query(LicensesList).filter_by(license_type=True).all()]
    blacklist = [i.license_name for i in db.session.query(LicensesList).filter_by(license_type=False).all()]

    for key in project_keys:
        space = key[0]
        if translation.get(space) is not None:
            space = translation.get(space)
        create_page(CONFLUENCE_PAGE_NAME, space)
        for ptype in project_types:
            create_page(ptype.title(), space, CONFLUENCE_PAGE_NAME)
            data = table(key[0], ptype, whitelist, blacklist)
            data = data.strip()
            send_to_confluence(data, ptype.title(), space)


def table(project_key, package_type, whitelist, blacklist):
    q = Licenses.query.filter_by(project=project_key, package_type=package_type).all()
    return render_template('confluence_table.html', items=q, whitelist=whitelist, blacklist=blacklist)


def send_to_confluence(data, page, space):
    id, version, title = page_attr(page, space)
    payload = {
            'version': {
                'number': version + 1
                },
            'type': 'page',
            'title': title,
            'body': {
                'storage': {
                    'value': data,
                    'representation': 'storage'
                    }
                }
            }
    url = urlparse(CONFLUENCE_URL + 'content/' + str(id))
    try:
        requests.put(url, data=payload, auth=(CONFLUENCE_USER, CONFLUENCE_PASSWORD))
    except requests.exceptions.RequestException as e:
        print(e)


def page_attr(target_page, space):
    target_page = target_page.replace(' ', '%20')
    url_template = '{c_url}content?title={title}&spaceKey={space}&expand=version,boy.storage'
    url = urlparse(url_template.format(c_url=CONFLUENCE_URL, title=target_page, space=space))
    page = requests.get(url, auth=(CONFLUENCE_USER, CONFLUENCE_PASSWORD))
    page_properties = page.json()[0]
    version = page_properties.get('version')['number']
    id = page_properties.get('id')
    title = page_properties.get('title')
    return id, version, title


def create_page(page, space, parent_page=None):
    url_template = '{c_url}content'
    url = urlparse(url_template.format(c_url=CONFLUENCE_URL))
    if parent_page is not None:
        p_id, p_version, p_title = page_attr(parent_page, space)
        payload = {
            'page': 'page',
            'title': page,
            'ancestors': [{'id': p_id}],
            'space': {'key': space},
        }
    else:
        payload = {
            'type': 'page',
            'title': page,
            'space': {'key': space},
        }
    if page_exist(page, space):
        return True
    try:
        requests.post(url, data=payload, auth=(CONFLUENCE_USER, CONFLUENCE_PASSWORD))
    except requests.exceptions.RequestException as e:
        print(e)


def page_exist(page, space):
    page = page.replace(' ', '%20')
    url_template = '{c_url}content?title={title}&spaceKey={space}&expand=version,boy.storage'
    url = urlparse(url_template.format(c_url=CONFLUENCE_URL, title=page, space=space))
    result = requests.get(url, auth=(CONFLUENCE_USER, CONFLUENCE_PASSWORD))
    if len(result.json()['results']) < 1:
        return False
    return True


class ConfluenceReportThreading(object):

    def __init__(self, interval):
        self.interval = interval

        thread = threading.Thread(target=self.run, args=())
        thread.daemon = True
        thread.start()

    def run(self):

        while True:
            confluence()
            time.sleep(self.interval)
