Doctolib Checker
================

# Install

Make sure you have at least *Python 3.7*

Create virtualenv and install requirements
```
python3 -m venv ~/.virtualenvs/DoctolibChecker
source ~/.virtualenvs/DoctolibChecker/bin/activate
python3 -m pip install -r requirements.txt
```

# Configure Telegram bot

1. Install and configure [Telegram](https://telegram.org/) app
2. Send `/newbot` to @BotFather and give your bot a name and a username
3. Keep the given access token for later
4. Send `/start` (usually by clicking the bottom button) to your bot. You can find it using the username like this : @BotUsername
5. Go to https://api.telegram.org/bot{ACCESS_TOKEN}/getUpdates (replace `{ACCESS_TOKEN}` with the token retrieved previously)
6. Get your `chat.id` finding the block corresponding you
```
    {
      "update_id": 12345,
      "message": {
        "message_id": 38,
        "from": {
          "id": 12345,
          "is_bot": false,
          "first_name": "Sample",
          "username": "sample"
        },
        "chat": {
          "id": 987654321, # <-- HERE
          "first_name": "Sample",
          "username": "sample",
          "type": "private"
        },
        "date": 1621409121,
        "text": "/start",
        "entities": [
          {
            "offset": 0,
            "length": 6,
            "type": "bot_command"
          }
        ]
      }
    },
```

# Launch the script

Go to [Doctolib](https://www.doctolib.fr/) and make a list of center you want to check (ex: "https://www.doctolib.fr/vaccination-covid-19/merignac/centre-de-vaccination-covid-19-pole-militaire-de-vaccination-merignac-pin-galant").

Run
```
# Replace ACCESS_TOKEN and CHAT_ID with info retrieved during previous step
python3 main.py --sites "url1" "url2" ... --telegram-token "ACCESS_TOKEN" --telegram-chat-id "CHAT_ID"
```

⚠️ Please do not decrease the delta between 2 requests, a CF cache of 60 seconds is in place, no need to spam.