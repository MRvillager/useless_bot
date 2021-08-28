# useless_bot

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
5. Add your bot token to the environmental variable
    - Linux:
        ```bash
        export DISCORD_TOKEN=yourtoken
        export REDDIT_ID=yourclientid
        export REDDIT_SECRET=yourclientsecret
        ```
    - Windows:
        ```bash
        set DISCORD_TOKEN=yourtoken
        set REDDIT_ID=yourclientid
        set REDDIT_SECRET=yourclientsecret
        ```
7. Run the bot using \
   `python -m useless_bot`
   
## Set-up with Docker

```bash
docker run -it --rm \
    --name useless_bot \
    -e DISCORD_TOKEN="yourtoken" \
    -e REDDIT_ID="yourclientid" \
    -e REDDIT_SECRET="yourclientsecret" \
    -v /path/to/data:/bot/data \
    mrvillager/useless_bot
```



## License

Released under [MIT License](LICENSE)
