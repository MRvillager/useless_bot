# useless_bot
[![ci](https://github.com/MRvillager/useless_bot/actions/workflows/ci.yml/badge.svg)](https://github.com/MRvillager/useless_bot/actions/workflows/ci.yml)

A personal bot for Discord using [discord.py](https://github.com/MRvillager/discord.py). \
This is a self-hosted bot, so you will need to host and maintain your own instance.

## Features

- Bank
- Games (blackjack)
- Send a message to the system channel when someone leaves the server
- Create roles with custom names using the command `-roles`
- Reddit posts in your Discord server

## Set-up

1. Clone this repo: \
   `git clone https://github.com/MRvillager/useless_bot.git`
2. Install the dependencies: \
   `pip install -r requirements.txt`
3. Create your bot here https://discord.com/developers/applications and get your token
4. Create your application https://www.reddit.com/prefs/apps and get your client id and client secret
5. Start your lavalink server https://github.com/freyacodes/Lavalink
6. Add your bot token to the environmental variable
    - Linux:
        ```bash
        export DISCORD_TOKEN=yourtoken
        export REDDIT_ID=yourclientid
        export REDDIT_SECRET=yourclientsecret
        export LAVALINK_HOST=127.0.0.1
        export LAVALINK_PORT=2333
        export LAVALINK_PASSWORD=youshallnotpass
        ```
    - Windows:
        ```bash
        set DISCORD_TOKEN=yourtoken
        set REDDIT_ID=yourclientid
        set REDDIT_SECRET=yourclientsecret
        set LAVALINK_HOST=127.0.0.1
        set LAVALINK_PORT=2333
        set LAVALINK_PASSWORD=youshallnotpass
        ```
7. Run the bot using \
   `python -m useless_bot`

## Set-up with Docker

```bash
sudo docker run -it --rm \
    --name lavalink \
    --net=bridge \
    fredboat/lavalink

sudo docker run -it --rm \
    --name useless_bot \
    --net=bridge \
    -e DISCORD_TOKEN="yourtoken" \
    -e REDDIT_ID="yourclientid" \
    -e REDDIT_SECRET="yourclientsecret" \
    -e LAVALINK_HOST=$(sudo docker inspect lavalink | jq '.[].NetworkSettings.Networks.bridge.IPAddress') \
    -e LAVALINK_PORT="2333" \
    -e LAVALINK_PASSWORD="youshallnotpass" \
    -v /path/to/data:/bot/data \
    ghcr.io/mrvillager/useless_bot:latest
```

## License

Released under [MIT License](LICENSE)
