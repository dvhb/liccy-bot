from licenses import app, sc
import json


def notify_managers(bad_licenses):
    managers = app.config.get('MANAGERS')
    for user in managers:
        text = ''
        for project, libs in bad_licenses.items():
            if len(libs) > 1:
                text_header = '''
':heavy_multiplication_x: In the project *{project}*
there are some libraries that *are not allowed* for commercial use:\n'''
                text_template = '*{library}* — {license}\n'
                text += text_header.format(project=project)
                for lib in libs:
                    text += text_template.format(library=lib['name'],
                                                 license=lib['license'])
            else:
                text_template = '''
:heavy_multiplication_x: In the project *{project}*
the library *{library}* has license *{license}*\nThis license *is not allowed*
for commercial use'''
                text = text_template.format(project=project,
                                            library=libs[0]['name'],
                                            license=libs[0]['license'])
        user_id = app.config.get('SLACK_USERS').get(user)
        channel = sc.api_call(
                'conversations.open',
                users=user_id
                )
        if channel['ok']:
            msg = sc.api_call(
                    'chat.postMessage',
                    channel=channel['channel']['id'],
                    text=text
                    )
            if msg['ok']:
                return True
        return False


def validate_license(license):
    text_to_lawyer = '''
There\'s a new license that you need to review:\n*{license}*\n\
Is it ok to use it for commercial purposes?
'''.format(license=license)
    lawyers = app.config.get('LAWYERS')
    # send license to managers to validate
    for user in lawyers:
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
                        "text": text_to_lawyer,
                        "actions": [{
                            "name": "yes",
                            "text": "Yes",
                            "type": "button",
                            "value": license
                            },
                            {
                            "name": "no",
                            "text": "No",
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
