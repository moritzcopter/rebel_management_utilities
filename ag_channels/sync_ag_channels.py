from telethon import TelegramClient
from telethon.tl.functions.channels import InviteToChannelRequest
from telethon.tl.types import InputPhoneContact
from telethon.tl.functions.contacts import ImportContactsRequest
from telethon.errors import UserIdInvalidError
from telethon.errors.rpcerrorlist import UserNotMutualContactError, FloodWaitError

from time import sleep, localtime, time, strftime
from converter import converter, POSTCODE, MUNICIPALITY, TOWN, PROVINCE, REGION
import requests
import json
from dotenv import load_dotenv
import os

regions = ["Midden", "Zuid-Oost", "Zuid-Holland", "Noord-Oost", "Noord-West"]
logs = {}


def convert_phone_number(phonenumber):
    """
        Replace 06 in phonenumbers with +316, to work with the telegram API.
    """
    if phonenumber[0:2] == "06":
        return "+316" + phonenumber[2:]
    return phonenumber


def get_all_ags(api_key, an_ag_endpoints):
    """
        Requests a list of all AN users who registered one of the AG forms.
        Returns a list of their custom fields. This includes their municipality,
        AG data and phonenumber.
    """
    headers = {'OSDI-API-Token': api_key}
    ags = []
    people_endpoints = []

    # Get all the people who signed the 4 AG forms.
    for endpoint in an_ag_endpoints:
        url = an_ag_endpoints[endpoint]

        # Loop - every request carries at most 25 entries.
        while True:
            response = requests.get(url, headers=headers)
            status_code = response.status_code
            if status_code != 200:
                raise requests.HTTPError(response=response)
            content = response.json()

            # Get the endoints to the people who signed the form - they hold the AG info.
            people_endpoints += [p["_links"]["osdi:person"]["href"] for p in content["_embedded"]["osdi:submissions"]]
            try:
                url = content['_links']['next']['href']
            except KeyError:  # end querying when there is no more data left
                break

    # Request the AG data from the people who filled in the form.
    for url in list(set(people_endpoints)): # Remove duplicates (because of update form.)
        response = requests.get(url, headers=headers)
        status_code = response.status_code
        if status_code != 200:
            raise requests.HTTPError(response=response)
        content = response.json()
        print(".")
        # Try to include the rep's name - some people haven't filled this in.
        try:
            content["custom_fields"].update({"rep_name" : content["given_name"]})
        except KeyError:
            pass
        ags.append(content["custom_fields"])
    return ags


async def sync_channels(api_key, links, super_admins, an_ag_endpoints):
    """
        Syncs the AG reps from Action Network with the Telegram broadcasts.
    """
    ags = get_all_ags(api_key, an_ag_endpoints)

    for region in regions:

        # Get the AG's which should be in this channel.
        ags_region = [convert_phone_number(ag["Phone number"]) for ag in ags if converter(MUNICIPALITY, REGION, ag["Municipality"]) == region]
        ags_in_channel = ["+" + user.phone for user in await client.get_participants(links[region])]

        print(region)
        print(ags_region)
        print(ags_in_channel)
        # Find the people who should be added/removed.
        to_add = [ag for ag in ags_region if ag not in ags_in_channel]

        # Add users and log the result.
        for ag in to_add:
            try:
                new_phonenumber = await add_user(ag, region, links)
                if "+" + new_phonenumber in ags_in_channel: # User was already in channel.
                    logs[region]["update_number"].append(ag)
                else: # User was added.
                    logs[region]["added"].append(ag)
            except UserNotMutualContactError: # User not a mut. contact.
                if not ag in logs[region]["error"]:
                    logs[region]["error"].append(ag)
            except IndexError: # User doesn't have telegram.
                if not ag in logs[region]["no_telegram"]:
                    logs[region]["no_telegram"].append(ag)


async def send_log(admins):
    """
        Sends the current content of 'logs' to the super admins specified in the
        environment variable 'super_admins'. This log contain:
        - the new phonenumbers added to each regional channel;
        - the amount of phonenumbers which don't have telegram;
        - the amount of people which had an errro while adding them.
    """
    message = "Dagelijks log van affiniteitsgroep kanalen:\n"
    for region in regions:
        message += "\n"
        message += region
        message += "\n      Aantal toegevoegd: {}".format(len(logs[region]["added"]))
        message += "\n      Toegevoegd: {}".format(logs[region]["added"])
        message += "\n      Geen telegram: {}".format(logs[region]["no_telegram"])
        message += "\n      Error bij toevoegen: {}".format(logs[region]["error"])

    for admin in admins:
        await client.send_message(admin, message)


def clear_logs():
    """
        Clears the 'logs' var, and resets it to an empty dict of dicts with the
        used format.
    """
    for region in regions:
        logs[region] = {"added" : [], "no_telegram" : [], "error" : [], "update_number" : []}


async def send_invite(user, region, links):
    """
        Sends a bilingual message to the specified 'user' to invite them to the
        AG rep telegram channel corresponding to the 'region' specified.
    """
    message = "Hoi, \nJij staat in Action Network geregistreerd als de afgevaartdige/representative van je Extinction Rebellion affiniteitsgroep. Zojuist ben je (als het goed is) toegevoegd aan het officiële telegram kanaal voor affiniteitsgroepen in regio {}. Dit kanaal houdt je up-to-date over alle acties in je regio, en geeft andere informatie die je affiniteitsgroep helpt bij het actie voeren. Door de informatie die hier langs komt in de gaten te houden, en door te geven aan je affiniteitsgroep, weet je alles wat nodig is om in actie te komen met Extinction Rebellion! \nMeer informatie over de kanalen vind je hier: tinyurl.com/ag-kanalen . Mochten ook andere leden van je affiniteitsgroep in het kanaal willen, dan is hier een link waarmee ze toegang krijgen: {} . Mocht jullie groep in meerdere regio's actief zijn, stuur mij dan even een berichte - ik kan je dan ook in de kanelen voor andere regio's plaatsen. Voor overige vragen kun je mij hier ook via Telegram contacteren.\nLove & Rage Martijn van Extinction Rebellion".format(region, links[region])
    message_en = "Hi,\nYou're registered as the representative of your Extinction Rebellion affinity group through Action Network. If all went well, you were just added to the official information channel for affinity groups in your region: {}. This channel will keep you up to date on all actions in your region, as well as other information that is useful to support your affinity group. By keeping an eye on the information that comes through here, and passing it on to your affinity group, you will know everything you need to come into action with XR!\nMore information about the channels can be found here: tinyurl.com/ag-kanalen   If other members of your affinity group also wish to join the channel, here's a link to give them access: {} . If your affinity group is active in mulitple reagions, please send me a message, and I will add you to the channels for the other regions as well. You can also reach me here on telegram for any addition questions!\nLove & Rage Martijn from Extinction Rebellion".format(region, links[region])
    try:
        await client.send_message(user, message)
        await client.send_message(user, message_en)
    except UserIdInvalidError and ValueError as e:
        print("Invalid phonenumber - either the AG rep has not installed telegram, or the phone number is invalid. User: {}    Error: '{}'".format(user, e))


async def add_user(user, region, links):
    # Add user to contact. This allows us to add them to the channel
    contact = InputPhoneContact(client_id=0, phone=user, first_name="xr_ag_rep", last_name="{}".format(region))
    try:
        result = await client(ImportContactsRequest([contact]))
    except FloodWaitError as e:
        sleep(5 * 60)
        return

    # Add them to the correct channel.
    await client(InviteToChannelRequest(links[region], [result.users[0]]))

    # # Send them a welcome message.
    # await send_invite(user, region, links)
    # Return the phonenumber parsed by Telegram; this always has the format
    # 316...  In AN there is no standard format.
    # the input format
    return result.users[0].phone


async def rem_user(user, region):
    try:
        await client.kick_participant(region_data[region]["link"], user)
    except UserIdInvalidError and ValueError as e:
        print("Error when removing {} from {}: '{}'".format(user, e))


async def main():
    # Start-up.
    await client.start()
    current_day = int(strftime("%j", localtime(time()))) - 1

    # Get required environment variables.
    api_key = os.getenv("api_key_an")
    links = json.loads(os.getenv("links"))
    super_admins = os.getenv("super_admins")
    an_ag_endpoints = json.loads(os.getenv("an_ag_endpoints"))
    admins = json.loads(os.getenv("super_admins"))

    # This sets up the log dict structure.
    clear_logs()

    # Sync the channels.
    while True:
        await sync_channels(api_key, links, super_admins, an_ag_endpoints)

        # If it's a new day, log.
        new_day = int(strftime("%j", localtime(time())))
        if new_day != current_day:
            current_day = new_day
            await send_log(admins)
            clear_logs()

        # Loop every 5 minutes.
        sleep(5 * 60)


# Load environment variables.
load_dotenv()

# Set up telegram client and launch sync loop.
client = TelegramClient(os.getenv("username"), os.getenv("api_id_tg"), os.getenv("api_hash_tg"))
with client:
    client.loop.run_until_complete(main())
