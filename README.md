# Liccy Bot

Liccy bot makes sure the license you use in a project is ok for commercial purposes. 

Once a day the bot scans all of your repos in Gitlab and collects integrated libraries. The list of libraries is formed based on `requirement.txt` file in requirements directory or `package.json` that the bot gets from the project root. 

For each library the bot defines the license and looks for it in the table. If the license is there, the bot checks if it is ok to use it. If it is, the bot verifies the next one. If it isn’t, it sends a Slack message to responsible person from MANAGERS variable. If the license is not listed in the table, bot sends another Slack message to lawyer from LAWYER variable and asks if this license is ok. In case it is, bot adds it to the table. If it isn’t, it also gets listed in the table and upon verification the bot will send a notification to Slack.

![scheme](https://dvhb.com/check_my_licenses_scheme.png)

## Installation
### Install app on the server
* Clone this repo.
* There is `docker-compose.yaml` file in the root folder, you need to define environment variables first (see below).
* After that you can simply run `docker-compose up -d` and application will start listening on port 8082.

### Install slack app
This app verifies licenses through Slack, so you need to create your own Slack app, following [Slack API guide](https://api.slack.com/slack-apps#creating_apps).
Note:
* You should create a bot user in your Slack app. All the messages will be sent from that bot user.
* Create two slash commands: `/whitelist_licenses` and `/blacklist_licenses` with request url `https://your.server.ip.address:8082/api/licenses/wls` and `https://your.ip.address:8082/api/licenses/bls` respectively. With those commands, you can edit lists with “good” and “bad” licenses: the ones that fit your needs and the ones which don't.
* In the Interactive Components menu, you should add Request url as `https://your.server.ip.address:8082/api/licenses/interactive`
* Install the app to your workspace.
* After that, you need to set Bot User OAuth Access Token as `SLACK_TOKEN` (you can find it in OAuth & Permissions menu) and Signing Secret as `SLACK_SIGNING_SECRET`.
## Setup your Gitlab instance

You need to tag your repos with project keys, if for example there is frontend and backend repos for the project, you should tag that repos with one TAG, after that you should set TAG_SET variable with tag list.

If there are a few separate repos for one project (e.g. frontend and backend), tag them with project keys. Tag the repos with one TAG and then set a TAG_SET variable with the tag list.

### Necessary environment variable
- GITLAB_URL=https://gitlab.url
- GITLAB_TOKEN=gitlab_token
- GITHUB_TOKEN=github_token
- SLACK_TOKEN=slack_token
- SLACK_SIGNING_SECRET=slack_secret
- LAWYERS=user1,user2 (users who will verify licenses)
- MANAGERS=user1,user2 (users who will get notifications about bad licenses)
- TAG_SET=project1,project2 (project tags)
