from base64 import b64decode
import json
import re
import os
from collections import defaultdict

from licenses.main.models import LicensesList, Licenses
from licenses.main.dependency import dependency
from licenses import app, db, sc, gl, gh
from licenses.main.slack import notify_managers, validate_license

import threading
import time


SOURCE_ERROR = 'Please, specify source: gitlab or github'


def get_content(source, item):
    if source == 'gitlab':
        return item.decode().decode('utf-8')
    elif source == 'github':
        return b64decode(item.raw_data.get('content')).decode('utf-8')
    else:
        raise Exception(SOURCE_ERROR)


def get_topics(source, project):
    if source == 'gitlab':
        return project.tag_list
    elif source == 'github':
        return project.get_topics()
    else:
        raise Exception(SOURCE_ERROR)


def set_filename(source, filename):
    if source == 'gitlab':
        return filename.file_name
    elif source == 'github':
        return filename.name
    else:
        raise Exception(SOURCE_ERROR)


def get_file_filename(source, project, filename):
    data = None
    if source == 'github':
        try:
            data = project.get_contents(filename)
        # @TODO catch 404 github error
        except Exception:
            pass
    elif source == 'gitlab':
        try:
            data = project.files.get(file_path=filename, ref=app.config.get('GITLAB_REFERENCE'))
        # @TODO catch 404 gitlab error
        except Exception:
            pass
    else:
        raise Exception(SOURCE_ERROR)
    return data


def get_file_directory(source, project, directory):
    data = []
    if source == 'github':
        try:
            data = project.get_contents(directory)
        # @TODO catch 404 github error
        except Exception:
            pass
    elif source == 'gitlab':
        try:
            pre_data = project.repository_tree(path=directory, ref=app.config.get('GITLAB_REFERENCE'))
            if pre_data:
                data = [x.get('path') for x in pre_data]
        # @TODO catch 404 gitlab error
        except Exception:
            pass
    return data


def get_file(source, project):
    result = defaultdict(list)
    data = None

    for project_type, filenames in app.config.get('FILES_TO_GET').items():
        for file_type, filenames_list in filenames.items():
            if file_type == 'files':
                for filename in filenames_list:
                    data = get_file_filename(source, project, filename)
                    if data is not None:
                        result[project_type].append(data)
            if file_type == 'directories':
                for directory in filenames_list:
                    file_list = get_file_directory(source, project, directory)
                    for f in file_list:
                        data = get_file_filename(source, project, f)
                        if data is not None:
                            result[project_type].append(data)
    return result


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

    all_licenses_project_uniq = set(all_licenses_project)
    for license in all_licenses_project_uniq:
        if license not in all_licenses_db:
            db.session.add(LicensesList(license_name=license, license_type=None))
            db.session.commit()
            validate_license(license)
        elif license in all_licenses_none:
            validate_license(license)

    return bad_licenses


def get_projects(source):
    tag_set = set(app.config.get('TAG_SET')) if app.config.get('TAG_SET') is not None else None
    if tag_set is None:
        raise Exception('Please, specify TAG_SET environment variable')
    data = []
    if source == 'gitlab':
        projects = gl.projects.list(all=True)
        for project in projects:
            tags = set(project.tag_list)
            if tag_set.intersection(tags):
                data.append(project)
    elif source == 'github':
        projects = gh.get_user().get_repos()
        for project in projects:
            tags = set(project.get_topics())
            if tag_set.intersection(tags):
                data.append(project)
    else:
        raise Exception(SOURCE_ERROR)
    return data


def write_content(filename, content):
        filename_path = os.path.join(os.getcwd(), 'target', filename)
        with open(filename_path, 'w') as f:
            f.write(content)
            f.close()


def get_licenses(source):
    projects = get_projects(source)
    for project in projects:
        dep_data = get_file(source, project)
        for repo_type, filename in dep_data.items():
            for f in filename:
                write_content(set_filename(source, f), re.sub('-r .*\n', '', get_content(source, f)))
            dependency_list = dependency(repo_type)
            bad_licenses = write_db(get_topics(source, project)[0], repo_type, dependency_list)
            notify_managers(bad_licenses)


class LicensesThreading(object):

    def __init__(self, interval):
        self.interval = interval

        thread = threading.Thread(target=self.run, args=())
        thread.daemon = True
        thread.start()

    def run(self):
        while True:
            if app.config.get('GITLAB_TOKEN') is not None:
                get_licenses('gitlab')
            if app.config.get('GITHUB_TOKEN') is not None:
                get_licenses('github')
            time.sleep(self.interval)
