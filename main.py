import argparse
import datetime
import time
from concurrent.futures import ThreadPoolExecutor, wait, ALL_COMPLETED

from doctolib import get_available_slots, url_next_call, get_sites_info
from logger import logger
from telegram import telegram_send_message


def check(site_info, bot_token, chat_id):
    available_slots = get_available_slots(site_info)
    message = ""
    if len(available_slots) > 0:
        message += f"[{site_info['name']}]({site_info['site']}) :\n"
        for slot in available_slots:
            message += f"- {slot['date']} - {slot['type']} : {slot['count']} slots\n"

    if message != "":
        logger.info(message)
        if not telegram_send_message(bot_token, chat_id, message):
            logger.error("Failed to send message via Telegram")


def monitor(sites_info, bot_token, chat_id):
    message = "Monitoring :\n"
    for site_info in sites_info:
        message += f"- [{site_info['name']}]({site_info['site']}) => {', '.join(map(lambda visit_motive: visit_motive['name'], site_info['visit_motives']))}\n"
    logger.info(message)
    if not telegram_send_message(bot_token, chat_id, message):
        logger.error("Failed to send message via Telegram")

    with ThreadPoolExecutor(max_workers=4) as pool:
        while True:
            futures = [pool.submit(lambda site: check(site, bot_token, chat_id), site_info) for site_info in sites_info]
            wait(futures, timeout=5, return_when=ALL_COMPLETED)

            lowest_next = min(url_next_call.values())
            now = datetime.datetime.now()
            if now < lowest_next:
                time_to_wait = (lowest_next - now).seconds
                if time_to_wait > 0:
                    logger.info(f"Retrying in {time_to_wait} seconds...")
                    time.sleep(time_to_wait)


def main(args):
    sites_info = get_sites_info(args.sites)
    monitor(sites_info, args.telegram_token, args.telegram_chat_id)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Endless loop to check for appointment availability using API call')
    parser.add_argument('--sites', required=True, nargs='+', type=str,
                        help='List of sites to monitor')
    parser.add_argument('--telegram-token', required=True, type=str,
                        help='Telegram bot token')
    parser.add_argument('--telegram-chat-id', required=True, type=str,
                        help='Your Telegram chat id with the bot')
    args = parser.parse_args()

    main(args)
