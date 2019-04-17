# Verify lincenses bot

Bot to verify licenses in project's  dependency librarys.


## Installation

### Install app on the server
1. Clone this repo
2. There is docker-compose.yaml file in the root folder, you need to define environment varilbles first (see below)
3. After that you can simpy run `docker-compose up -d` and application will start listening on port 8082

### Install slack app
This app verify licenses through slack app, so you need to build your own app, following this guide: <https://api.slack.com/slack-apps#creating_apps>

Important things:
1. You should create a bot user in your slack app. All the messages will be sent from that bot user
2. Create two slash commands: `/whitelist_licenses` and `/blacklist_licenses` with request url `https://your.server.ip.address:8082/api/licenses/wls` and `https://your.ip.address:8082/api/licenses/bls` respectively. With those commands you can edit lists with "good" and "bad" licenses: the ones that fit your needs and the ones which don't.
3. In the Interactive Components menu you should add Request url as `https://your.server.ip.address:8082/api/licenses/interactive`
4. Install app in your workspace
5. After that you need to set Bot User OAuth Access Token as SLACK_TOKEN (you can find it in OAuth & Permissions menu) and Signing Secet as SLACK_SIGNING_SECRET 


### Setup your gitlab instance
You need to tag your repos with project keys, if for example there is frontend and backend repos for the project, you should tag that repos with one TAG, after that you should set TAG_SET variable with tag list.

## Necessary environment variable 


* GITLAB_URL=https://gitlab.url
* GITLAB_TOKEN=gitlab_token
* SLACK_TOKEN=slack_token
* SLACK_SIGNING_SECRET=slack_secret
* MANAGERS=user1,user2 (users who will verify licenses)
* TAG_SET=project1,project2 (project tags)
