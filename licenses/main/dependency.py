import json
import os
import glob
from licenses import dc


def dependency(repo_type):
    if repo_type == 'backend':
        return dependency_backend()
    elif repo_type == 'frontend':
        return dependency_frontend()
    else:
        pass


def dependency_backend():
    license_data = {}
    volume = {os.path.join(os.getcwd(), 'target'): {'bind': '/app/target', 'mode': 'rw'}}
    image = dc.images.build(path='./docker', dockerfile='Dockerfile-back', tag='licenses-back')
    container = dc.containers.run(image[0].tags[0], detach=True, volumes=volume,
                                  name='license-check-backend')

    if os.path.exists(os.path.join(os.getcwd(), 'target', 'Pipfile')):
        try:
            container.exec_run('pip install pipenv')
            container.exec_run('pipenv install --system')
        except Exception:
            raise Exception
    else:
        for filename in glob.glob('*.txt'):
            try:
                command = 'pip install -r {}'.format(filename)
                container.exec_run(command)
            except Exception:
                raise Exception

    status, licenses = container.exec_run('python ./get-licenses.py')
    licenses = licenses.decode().split('\n')
    for license in licenses:
        lic = license.split(':')
        if len(lic) > 1:
            license_data[lic[0]] = lic[1]
    for filename in glob.glob(os.path.join(os.getcwd(), 'target', '*')):
        if not filename.endswith('get-licenses.py'):
            os.remove(filename)
    container.remove(force=True)
    return license_data


def dependency_frontend():
    license_data = {}
    volume = {os.path.join(os.getcwd(), 'target'): {'bind': '/app/target', 'mode': 'rw'}}
    image = dc.images.build(path='./docker', dockerfile='Dockerfile-front', tag='licenses-front')
    container = dc.containers.run(image[0].tags[0], detach=True, volumes=volume,
                                  name='license-check-front')
    try:
        container.exec_run('npm install -g')
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
