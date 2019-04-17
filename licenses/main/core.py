from base64 import b64decode
import json
import re
import os
from collections import defaultdict

from urllib.parse import urlparse

from licenses.main.models import LicensesList, Licenses
from licenses.main.controllers import licenses_list
from licenses import app, db, sc, dc, gl

import threading
import time


def get_content(project, item):
    file_info = project.repository_blob(item['id'])
    return b64decode(file_info['content'])


def get_file(project):
    items = project.repository_tree(all=True)
    data = []
    repo_type = ''
    for item in items:
        if item.get('name') == 'requirements' and item.get('type') == 'tree':
            requirements = project.repository_tree(path='requirements')
            for requirement in requirements:
                content = get_content(project, requirement)
                data.append(content.decode('utf-8'))
                repo_type = 'backend'
        elif item.get('name') == 'requirements.txt' and item.get('type') == 'blob':
            content = get_content(project, item)
            data.append(content.decode('utf-8'))
            repo_type = 'backend'
        elif item.get('name') == 'Pipfile' and item.get('type') == 'blob':
            content = get_content(project, item)
            data.append(content.decode('utf-8'))
            repo_type = 'backend_pipfile'
        elif item.get('name') == 'Pipfile.lock' and item.get('type') == 'blob':
            content = get_content(project, item)
            data.append(content.decode('utf-8'))
            repo_type = 'backend_pipfile'
        elif item.get('name') == 'package.json' and item.get('type') == 'blob':
            content = get_content(project, item)
            data.append(content.decode())
            repo_type = 'frontend'
    return repo_type, data


def write_db(project, package_type, packages):
    bad_licenses = defaultdict(list)
    q_black = LicensesList.query.filter_by(license_type=False).all()
    q_none = LicensesList.query.filter_by(license_type=None).all()
    q_all = LicensesList.query.all()
    blacklist = [l.license_name for l in q_black]
    all_licenses_db = [l.license_name for l in q_all]
    all_licenses_none = [l.license_name for l in q_none]
    all_licenses_project = []
    for package, license in packages.items():
        if isinstance(license, list):
            license = ','.join(license)
        if package:
            all_licenses_project.append(license)
            db_item = Licenses(package, license.strip(), package_type, project)
            if not Licenses.query.filter_by(name=package, project=project).scalar():
                db.session.add(db_item)
                db.session.commit()
            else:
                q = Licenses.query.filter_by(name=package, project=project).first()
                q.license = license
                db.session.commit()

            if license in blacklist:
                bad_licenses[project].append({'name': package, 'license': license})

    all_licenses_project1 = set(all_licenses_project)
    for license in all_licenses_project1:
        if license not in all_licenses_db:
            db.session.add(LicensesList(license_name=license, license_type=None))
            db.session.commit()
            validate_license(license)
        elif license in all_licenses_none:
            validate_license(license)

    return bad_licenses


def validate_license(license):
    managers = app.config.get('MANAGERS')
    # send license to managers to validate
    for user in managers:
        user_id = app.config.get('SLACK_USERS').get(user)
        channel = sc.api_call(
                'conversations.open',
                users=user_id
                )
        if channel['ok']:
            attachments = json.dumps(
                    [{
                        "callback_id": "validate_license",
                        "fallback": "Error.",
                        "text": "Approve license " + license,
                        "actions": [{
                            "name": "yes",
                            "text": "Yes!",
                            "type": "button",
                            "value": license
                            },
                            {
                            "name": "no",
                            "text": "No!",
                            "type": "button",
                            "value": license
                            }]
                        }]

                    )
            msg = sc.api_call(
                    'chat.postMessage',
                    channel=channel['channel']['id'],
                    text='Action needed:',
                    attachments=attachments
                    )
            if msg['ok']:
                return True
    return False


def licenses_action(ls, request):
    text = request.form.get('text')
    l_list = licenses_list(ls)
    if not text:
        if ls:
            licenses_message = 'Here are the licenses whitelist: {}'.format(l_list) if l_list else 'Whitelist is empty'
        else:
            licenses_message = 'Here are the licenses blacklist: {}'.format(l_list) if l_list else 'Blacklist is empty'

        return licenses_message
    else:
        action, licenses = text.split(' ')
        for license in licenses.split(','):
            if action == 'add':
                db.session.add(LicensesList(license_name=license, license_type=ls))
            elif action == 'del':
                to_delete = LicensesList.query.filter_by(license_name=license, license_type=ls).first()
                db.session.delete(to_delete)
        db.session.commit()
        return '{} is performed'.format(action.capitalize())


def get_gitlab_projects():
    tag_set = set(app.config.get('TAG_SET')) if app.config.get('TAG_SET') is not None else [None]
    data = []
    if gl.version()[0] == 'Unknown':
        return None
    projects = gl.projects.list(all=True)
    for project in projects:
        tags = set(project.tag_list)
        if tag_set.intersection(tags):
            data.append(project)
    return data


def write_content(filename, content):
        filename_path = os.path.join(os.getcwd(), 'target', filename)
        with open(filename_path, 'w') as f:
            f.write(content)
            f.close()


def get_licenses():
    projects = get_gitlab_projects()
    for project in projects:
        repo_type, content_list = get_file(project)
        if len(content_list) > 1:
            write_content('Pipfile', re.sub('-r .*\n', '', content_list[0]))
            write_content('Pipfile.lock', re.sub('-r .*\n', '', content_list[1]))
            write_db(project.tag_list[0], 'backend_pipfile', requirements_backend_pipfile())
        content = '\n'.join(content_list)
        # Remove -r ./filename.txt lines
        content = re.sub('-r .*\n', '', content)
        hostname = urlparse(app.config.get('GITLAB_URL')).netloc
        content = re.sub('.*' + hostname + '.*', '', content)
        if repo_type == 'backend':
            filename = os.path.join(os.getcwd(), 'target', 'requirements.txt')
            with open(filename, 'w') as f:
                f.write(content)
                f.close()
            write_db(project.tag_list[0], repo_type, requirements_backend())
        elif repo_type == 'frontend':
            filename = os.path.join(os.getcwd(), 'target', 'package.json')
            with open(filename, 'w') as f:
                f.write(content)
                f.close()
            write_db(project.tag_list[0], repo_type, requirements_frontend())


def requirements_frontend():
    license_data = {}
    volume = {os.path.join(os.getcwd(), 'target'): {'bind': '/app/target', 'mode': 'rw'}}
    image = dc.images.build(path='/app/docker', dockerfile='Dockerfile-front', tag='licenses-front')
    container = dc.containers.run(image[0].tags[0], detach=True, volumes=volume,
                                  name='license-check-front')
    try:
        container.exec_run('yarn install --no-lockfile')
        container.exec_run('npm install -g license-checker')
    except Exception:
        return Exception

    status, packages = container.exec_run('license-checker --json')
    packages_json = None
    if packages is not None and b'Found error' not in packages:
        packages_json = json.loads(packages.decode())
        for package, properties in packages_json.items():
            license = properties.get('licenses')
            package_name = package.split('@')[0]
            license_data[package_name] = license
    container.exec_run('rm -rf node_modules/')
    container.exec_run('rm package.json')
    container.remove(force=True)
    return license_data


def requirements_backend():
    license_data = {}
    volume = {os.path.join(os.getcwd(), 'target'): {'bind': '/app/target', 'mode': 'rw'}}
    image = dc.images.build(path='/app/docker', dockerfile='Dockerfile-back', tag='licenses-back')
    container = dc.containers.run(image[0].tags[0], detach=True, volumes=volume,
                                  name='license-check-backend')
    try:
        container.exec_run('pip install -r requirements.txt')
    except Exception:
        return Exception

    status, licenses = container.exec_run('python ./get-licenses.py')
    licenses = licenses.decode().split('\n')
    for license in licenses:
        lic = license.split(':')
        if len(lic) > 1:
            license_data[lic[0]] = lic[1]
    container.exec_run('rm requirements.txt')
    container.remove(force=True)
    return license_data


def requirements_backend_pipfile():
    license_data = {}
    volume = {os.path.join('/app/target'): {'bind': '/app/target', 'mode': 'rw'}}
    image = dc.images.build(path='/app/docker', dockerfile='Dockerfile-back', tag='licenses-back')
    container = dc.containers.run(image[0].tags[0], detach=True, volumes=volume,
                                  name='license-check-backend')
    try:
        container.exec_run('pip install pipenv')
        container.exec_run('pipenv install --system')
    except Exception:
        return Exception
    status, licenses = container.exec_run('python ./get-licenses.py')
    licenses = licenses.decode().split('\n')
    for license in licenses:
        lic = license.split(':')
        if len(lic) > 1:
            license_data[lic[0]] = lic[1]
    container.exec_run('rm Pipfile*')
    container.remove(force=True)
    return license_data


class LicensesThreading(object):

    def __init__(self, interval):
        self.interval = interval

        thread = threading.Thread(target=self.run, args=())
        thread.daemon = True
        thread.start()

    def run(self):

        while True:
            get_licenses()
            time.sleep(self.interval)
