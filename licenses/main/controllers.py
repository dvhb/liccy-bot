from flask import request, make_response, Blueprint
import json
import time
import hmac
import hashlib

from licenses import db, sc, app
from licenses.main.models import LicensesList

main_module = Blueprint('main_module', __name__, url_prefix='/')


def button_action(callback_id, actions):
    if callback_id == 'validate_license':
        action_name = actions[0].get('name')
        action_value = actions[0].get('value')
        q = LicensesList.query.filter_by(license_name=action_value).first()
        if q.license_type is not None:
            return 'already_set'
        else:
            if action_name == 'yes':
                q.license_type = True
                db.session.commit()
                return True
            elif action_name == 'no':
                q.license_type = False
                db.session.commit()
                return False


def licenses_list(ls):
    result = LicensesList.query.filter_by(license_type=ls).all()
    if result:
        return ', '.join([license.license_name for license in result])
    else:
        return ''


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


def request_validate(request):
    request_body = request.get_data()
    timestamp = request.headers['X-Slack-Request-Timestamp']
    if abs(time.time() - float(timestamp)) > 60 * 5:
        return False
    sig_basestring = 'v0:' + timestamp + ':' + request_body.decode('utf-8')
    my_signature = 'v0=' + hmac.new(app.config.get('SLACK_SIGNING_SECRET').encode('utf-8'),
                                    sig_basestring.encode('utf-8'), hashlib.sha256).hexdigest()
    slack_signature = request.headers['X-Slack-Signature']
    if hmac.compare_digest(my_signature, slack_signature):
        return True
    else:
        return False


@main_module.route('/api/licenses/<ls>', methods=['POST'])
def licenses(ls):
    if request_validate(request):
        if ls == 'wls':
            return licenses_action(True, request)
        elif ls == 'bls':
            return licenses_action(False, request)
    else:
        return 'Request is not validated'


@main_module.route('/api/licenses/interactive', methods=['POST'])
def interactive():
    if request_validate(request):
        data = json.loads(request.form.getlist('payload')[0])
        om = data.get('original_message')

        action = button_action(data.get('callback_id'), data.get('actions'))
        if action == 'already_set':
            text = om.get('attachments')[0]['text'] + '\n:exclamation: This license is already defined.'
        elif action:
            text = om.get('attachments')[0]['text'] + '\n:heavy_check_mark: License approved'
        elif not action:
            text = om.get('attachments')[0]['text'] + '\n:heavy_multiplication_x: License rejected'
        channel = data.get('channel')['id']
        attachments = [{"text": text}]
        msg = sc.api_call('chat.update',
                          ts=om['ts'],
                          text=om['text'],
                          channel=channel,
                          attachments=attachments
                          )
        app.logger.info(msg)
        return make_response('', 200)
    else:
        return make_response('Failed', 200)


@app.route('/')
def status():
    return 'ok'


@app.route('/again')
def status2():
    return 'again'
