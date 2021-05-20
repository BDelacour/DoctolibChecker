import urllib.parse

import requests


def telegram_send_message(bot_token, chat_id, message):
    encoded_message = urllib.parse.quote_plus(message)
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage?chat_id={chat_id}&parse_mode=Markdown&text={encoded_message}"
    return requests.get(url).status_code == 200

