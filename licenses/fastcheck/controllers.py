from flask import Blueprint, request, render_template, make_response
from licenses.fastcheck.core import db_fastcheck
from licenses import app
from flask_mail import Mail, Message


fastcheck_module = Blueprint('fastcheck_module', __name__, url_prefix='/')
MANAGERS_EMAIL = app.config.get('MANAGERS_EMAIL')
MAIL_FROM = app.config.get('MAIL_FROM')
MAIL_SUBJECT = app.config.get('MAIL_SUBJECT')
mail = Mail(app)


@fastcheck_module.route('/api/fastcheck/', methods=['POST'])
def api_fastcheck():
    warnings = []
    errors = []
    content = request.get_json()
    for i, lib in enumerate(content):
        result = db_fastcheck(lib.get('License'))
        if result:
            errors.append(lib)
        elif result is None:
            warnings.append(lib)
        else:
            pass

    if len(errors) > 0 or len(warnings) > 0:
        msg = Message(MAIL_SUBJECT, sender=MAIL_FROM, recipients=MANAGERS_EMAIL)
        msg.html = render_template('mail.html', errors=errors, warnings=warnings)
        mail.send(msg)
        return dict(Errors=errors, Warnings=warnings)
    return make_response(dict(), 200)
