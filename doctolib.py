import datetime
import json
from urllib.parse import urlparse

import requests

from logger import logger

headers = {
    "User-Agent": "AvailableVaccineRobot"
}
url_next_call = {}


def _is_valid_availability(domain, availability):
    if domain == "www.doctolib.fr":
        today_date = datetime.datetime.now()
        tomorrow_date = today_date + datetime.timedelta(days=1)
        today = today_date.strftime("%Y-%m-%d")
        tomorrow = tomorrow_date.strftime("%Y-%m-%d")
        return (availability['date'] == today or availability['date'] == tomorrow) and len(availability['slots']) > 0
    if domain == "www.doctolib.de":
        return len(availability['slots']) > 0


def get_available_slots(site_info):
    today_date = datetime.datetime.now()
    today = today_date.strftime("%Y-%m-%d")

    available_slots = []
    for visit_motive in site_info["visit_motives"]:
        url = f"{site_info['base_url']}/availabilities.json?start_date={today}&visit_motive_ids={visit_motive['id']}&agenda_ids={visit_motive['agenda_ids']}&insurance_sector=public&practice_ids={visit_motive['practice_ids']}&destroy_temporary=true&limit=4"

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
            availabilities = list(filter(lambda availability: _is_valid_availability(site_info["domain"], availability), decoded['availabilities']))
            if len(availabilities) > 0:
                available_slots.extend([{"date": availability["date"], "count": len(availability["slots"]), "type": visit_motive["name"]} for availability in availabilities])
        else:
            logger.error(f"Failed to fetch \"{url}\", code {response.status_code}")
            logger.error(response.text)
    return available_slots


def _is_valid_visit_motive(domain, visit_motive):
    if domain == "www.doctolib.fr":
        lower_name = visit_motive["name"].lower()
        return "1re" in lower_name and ("pfizer" in lower_name or "moderna" in lower_name)
    if domain == "www.doctolib.de":
        return True


def get_sites_info(sites):
    sites_info = []
    for site in sites:
        parsed_url = urlparse(site)

        domain = parsed_url.netloc
        base_url = f"{parsed_url.scheme}://{domain}"
        encoded_name = parsed_url.path.split("/")[-1]
        url = f"{base_url}/booking/{encoded_name}.json"
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            decoded_response = json.loads(response.text)

            for place in decoded_response["data"]["places"]:
                practice_ids = place["practice_ids"]

                visit_motives = []
                for visit_motive in decoded_response["data"]["visit_motives"]:
                    if _is_valid_visit_motive(domain, visit_motive):
                        corresponding_agendas = list(filter(lambda agenda: visit_motive["id"] in agenda["visit_motive_ids"] and agenda["practice_id"] in practice_ids, decoded_response["data"]["agendas"]))
                        if len(corresponding_agendas) > 0:
                            visit_motives.append({
                                "id": visit_motive["id"],
                                "name": visit_motive["name"],
                                "agenda_ids": "-".join(map(lambda agenda: str(agenda["id"]), corresponding_agendas)),
                                "practice_ids": "-".join(set(map(lambda agenda: str(agenda["practice_id"]), corresponding_agendas)))
                            })

                sites_info.append({
                    "site": f"{base_url}{parsed_url.path}?pid={place['id']}",
                    "base_url": base_url,
                    "domain": domain,
                    "name": place["name"],
                    "encoded_name": encoded_name,
                    "visit_motives": visit_motives
                })
        else:
            logger.error(f"Failed to fetch \"{url}\", code {response.status_code}")
            logger.error(response.text)

    return sites_info
