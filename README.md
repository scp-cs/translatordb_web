[![Deploy](https://github.com/scp-cs/translatordb_web/actions/workflows/deploy.yml/badge.svg)](https://github.com/scp-cs/translatordb_web/actions/workflows/deploy.yml)
# The SCUTTLE Translator Directory System
Named after [RAISA's famous cautionary tale](https://scp-wiki.wikidot.com/scuttle), SCUTTLE provides a user friendly way for tracking our members' contributions to the translation project.

Details on the scoring system can be found on our [Discord](https://discord.gg/A6U2fCUJs6).

## Features

- Stores translation metadata (name, translator, wiki page, word count and bonus translator points)
- Stores user info (nickname, Wikidot ID, Discord username)
- Automatically fetches nicknames and profile avatars from Discord
- Login using classic credentials or Discord OAuth
- Fully Dockerized

## Planned features

- [ ] Fetching new pages from RSS feeds
- [ ] Note system for moderators
- [ ] A statistics page
- [ ] Automatic word counting (hard >w<)
- [ ] Improve responsivity on mobile and smaller windows

## Installation (manual)
### 1. Clone the repository
```bash
git clone https://github.com/scp-cs/translatordb_web.git
cd translatordb_web
```
### 2. Create a config file
*config.json*
```
{
    "DEBUG": false,
    "SECRET_KEY": "[SECRET KEY USED BY FLASK]",
    "DISCORD_TOKEN": "[YOUR DISCORD APP TOKEN]"
    "DISCORD_CLIENT_SECRET": "[YOUR DISCORD OAUTH SECRET]",
    "DISCORD_CLIENT_ID": [YOUR DISCORD APP ID],
    "DISCORD_REDIRECT_URI": "https://your-app-url.xyz/oauth/callback"
}
```
`DISCORD_TOKEN`, `DISCORD_CLIENT_ID` and `DISCORD_CLIENT_SECRET` can be found on your [Discord Developer Portal](https://discord.com/developers/applications).
> [!NOTE]
> Keep in mind that your redirect URI must *exactly* match one of the URIs entered on the developer portal, even when testing locally. Login attempts will fail otherwise.

`SECRET_KEY` should be a reasonably long random string and never shared with anyone. You can generate one, for example, using the Python `secrets` library:
```python
import secrets
print(secrets.token_urlsafe(24))
```
### 3. Run the app
```bash
python App.py
```

## Installation (Docker)
SCUTTLE is available as a prebuilt container image on [DockerHub](https://hub.docker.com/r/x10102/translatordb)
> [!WARNING]
> If you're running SCUTTLE behind a reverse proxy and communicating over HTTP internally, the environment variable `OAUTHLIB_INSECURE_TRANSPORT` has to be set, any requests to the app will fail otherwise.
```bash
docker run -d -p 8080:8080 -v /your/log/path:/app/translatordb.log -v /your/data/path:/app/data/scp.db -v /your/config/path:/app/config.json:ro --name scuttle x10102/translatordb
```
