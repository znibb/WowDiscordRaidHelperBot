# WowDiscordRaidHelperBot
For convenient automation of interactions with Google Sheets.

## Setup
### File setup
1. Create a project directory, e.g. `cd ~ && mkdir WowDiscordRaidHelperBot && cd WowDiscordRaidHelperBot`
1. Download `docker-compoes.yml` to your docker host, e.g. `wget https://raw.githubusercontent.com/znibb/WowDiscordRaidHelperBot/master/docker-compose.yml`
1. Copy template files, e.g. `cp .env-template .env && cp config.json-template config.json`
1. Copy the channel IDs of the channel where you want the bot to listen to commands and output announcements to `BOT_CMD_CHANNEL_ID` and `BOT_ANNOUNCE_CHANNEL_ID` fields respectively in `.env`

### Discord
1. Go to `http://discordapp.com/developers/applications`
1. Create a new application
1. Go to `Bot` sub menu and create a bot user
1. Copy the bot TOKEN and paste it into the `DISCORD_TOKEN` field in `.env`
1. From the `Bot`sub menu make sure `SERVER MEMBERS INTENT` is enabled
1. Go to `OAuth2` sub menu
1. In `SCOPES` select `bot` and in `BOT PERMISSIONS` select `View Channels`, `Send Message`, `Manage Messages` and `Embed Links`
1. Copy the generated URL and paste it into your web browser of choice
1. Select which server to add bot user to

### Google Sheets
1. Go to `https://console.cloud.google.com/apis/credentials` and log in
1. Create a project
1. Select Credentials -> Create Credentials -> Service account
1. Enter a suitable `Service account name` and `Service account description`, what you name it doesn't matter, it's just what will be shown in access logs later on
1. Click Continue
1. Enter `Editor` under `Select a role`.
1. Click Done
1. Click your newly created Service account in the list and go to the `KEYS` tab
1. Click `ADD KEY` -> `Create new key`
1. Select Key type `JSON` and click `CREATE`
1. You will be prompted to download the created file, save it in the project directory (e.g. `~/WowDiscordRaidHelperBot`) as `google_key.json` (THIS FILE IS SECRET, SHOULD BE HANDLED WITH CARE AND SHOULD NOT BE DISTRIBUTED)
1. Go to the `DETAILS` tab and copy the account email
1. Go to your Google Sheet, click `File->Share` and add the email from last step with editor rights.
1. Copy the URL to your sheet and paste it into the `SPREADSHEET_URL` file in `.env`

### Start the bot
1. From the repo dir, run `docker-compose up -d`

## Usage
The information linking your raids to worksheets resides in `config.json`.