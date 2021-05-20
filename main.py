import argparse
import datetime
import json
import time
from concurrent.futures import ThreadPoolExecutor, wait, ALL_COMPLETED

import requests

from logger import init_logger
from telegram import telegram_send_message

logger = init_logger("doctolib_checker")

headers = {
    "User-Agent": "AvailableVaccineRobot"
}

url_next_call = {}


def get_available_slots(site_info):
    today_date = datetime.datetime.now()
    tomorrow_date = today_date + datetime.timedelta(days=1)
    today = today_date.strftime("%Y-%m-%d")
    tomorrow = tomorrow_date.strftime("%Y-%m-%d")

    available_slots = []
    for visit_motive in site_info["visit_motives"]:
        url = f"https://www.doctolib.fr/availabilities.json?start_date={today}&visit_motive_ids={visit_motive['id']}&agenda_ids={visit_motive['agenda_ids']}&insurance_sector=public&practice_ids={visit_motive['practice_ids']}&destroy_temporary=true&limit=4"

        # Check not to call the same url too frequently
        if url in url_next_call and datetime.datetime.now() < url_next_call[url]:
            continue

        logger.info(f"Checking \"{visit_motive['name']}\" for \"{site_info['name']}\"")
        logger.debug(f"Calling {url}")
        response = requests.get(url, headers=headers)

        # Set next call date
        url_next_call[url] = datetime.datetime.now() + datetime.timedelta(seconds=60)
        if response.status_code == 200:
            decoded = json.loads(response.text)
            availabilities = list(filter(lambda availability: (availability['date'] == today or availability['date'] == tomorrow) and len(availability['slots']) > 0, decoded['availabilities']))
            if len(availabilities) > 0:
                available_slots.extend([{"date": availability["date"], "count": len(availability["slots"]), "type": visit_motive["name"]} for availability in availabilities])
        else:
            logger.error(f"Failed to fetch \"{url}\", code {response.status_code}")
            logger.error(response.text)
    return available_slots


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


def get_sites_info(sites):
    sites_info = []
    for site in sites:
        site = site.split("?")[0]
        encoded_name = site.split("/")[-1]
        url = f"https://www.doctolib.fr/booking/{encoded_name}.json"
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            decoded_response = json.loads(response.text)

            for place in decoded_response["data"]["places"]:
                practice_ids = place["practice_ids"]

                visit_motives = []
                for visit_motive in decoded_response["data"]["visit_motives"]:
                    lower_name = visit_motive["name"].lower()
                    if "1re" in lower_name and ("pfizer" in lower_name or "moderna" in lower_name):
                        corresponding_agendas = list(filter(lambda agenda: visit_motive["id"] in agenda["visit_motive_ids"] and agenda["practice_id"] in practice_ids, decoded_response["data"]["agendas"]))
                        if len(corresponding_agendas) > 0:
                            visit_motives.append({
                                "id": visit_motive["id"],
                                "name": visit_motive["name"],
                                "agenda_ids": "-".join(map(lambda agenda: str(agenda["id"]), corresponding_agendas)),
                                "practice_ids": "-".join(set(map(lambda agenda: str(agenda["practice_id"]), corresponding_agendas)))
                            })

                sites_info.append({
                    "site": site + f"?pid={place['id']}",
                    "name": place["name"],
                    "encoded_name": encoded_name,
                    "visit_motives": visit_motives
                })
        else:
            logger.error(f"Failed to fetch \"{url}\", code {response.status_code}")
            logger.error(response.text)

    return sites_info


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
