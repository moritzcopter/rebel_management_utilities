"""
"""

from telethon import TelegramClient
from telethon.tl.functions.channels import InviteToChannelRequest
from telethon.tl.types import InputPhoneContact
from telethon.tl.functions.contacts import ImportContactsRequest
from telethon.errors import UserIdInvalidError
from telethon.errors.rpcerrorlist import UserNotMutualContactError, FloodWaitError

import phonenumbers

from time import sleep, localtime, time, strftime
from converter import converter
import requests
import json
from dotenv import load_dotenv
import os


regions = ["Midden", "Zuid-Oost", "Zuid-Holland", "Noord-Oost", "Noord-West"]
logs = {}
DEBUG = False # Is this good practice??


def convert_phone_number(phonenumber):
    """
        Parses a phonenumber and returns it in E.164 format (i.e. +31 6 ..).
        When a provided phonenumber has no country code (i.e. 06 12 ..) the
        Dutch country code is assumed and added.

        Params:
        - phonenumber (string) : the given phonenumber. Can be any format.

        Returns:
        - on succes: (string): the phonenumber in E.164 format.
        - on failure: None.
    """
    # Country code was provided and detected.
    try:
        return phonenumbers.format_number(
                phonenumbers.parse(phonenumber),
                phonenumbers.PhoneNumberFormat.E164
        )
    # No country code provided - assume the number is Dutch.
    except phonenumbers.phonenumberutil.NumberParseException as e:
        try:
            return phonenumbers.format_number(
                    phonenumbers.parse(phonenumber, "NL"),
                    phonenumbers.PhoneNumberFormat.E164
            )
        # Invalid number
        except Exception as e:
            return None


def get_all_ags(api_key, an_ag_endpoints):
    """
        Requests a list of all AN users who registered one of the AG forms.
        First requests all responses to the different AN forms where AG's
        are registered. Then requests the data of the people who signed these
        forms; this data contains the AG data.

        Params:
        - api_key (str) : the api key for AN.
        - an_ag_endpoints (list) : a list of endpoints to the AN forms where
                                   AG's are registered.

        Returns:
        - (list) : a list of all the custom fields of the people who signed
                   an AG form. This contains, among others: 'AG_name', 'rep_name',
                   'Municipality', 'phone_number' (of the rep).
    """
    headers = {'OSDI-API-Token': api_key}
    ags = []
    people_endpoints = []

    # Get all the people who signed the 4 AG forms.
    for endpoint in an_ag_endpoints:
        # Loop - every request carries at most 25 entries.
        while True:
            response = requests.get(endpoint, headers=headers)
            status_code = response.status_code
            if status_code != 200:
                raise requests.HTTPError(response=response)
            content = response.json()

            # Get the endoints to the people who signed the form - they hold the AG info.
            people_endpoints += [p["_links"]["osdi:person"]["href"] for p in content["_embedded"]["osdi:submissions"]]
            try:
                endpoint = content['_links']['next']['href']
            except KeyError:  # end querying when there is no more data left
                break

    # Request the AG data from the people who filled in the form.
    for url in list(set(people_endpoints)): # Remove duplicates (because of update form.)
        response = requests.get(url, headers=headers)
        status_code = response.status_code
        if status_code != 200:
            raise requests.HTTPError(response=response)
        content = response.json()

        # Include the rep's name - some people haven't filled this in.
        if "given_name" in content:
            content["custom_fields"].update(({"rep_name" : content["given_name"]}))
        else:
            content["custom_fields"].update(({"rep_name" : "rebel"}))

        # Sometime the AG name is empty - to prevent crashes/try catches.
        if not "AG_name" in content["custom_fields"]:
            content["custom_fields"].update({"AG_name" : ""})
        ags.append(content["custom_fields"])
    return ags


async def sync_channels(api_key, links, an_ag_endpoints):
    """
        Syncs the AG reps from Action Network with the Telegram broadcasts.
        First gets all registered AG's from AN and filters these on the
        five regions. Checks if any of these AG's are not yet in the
        regions corresponding Telegram channel. If so, adds them.

        Logs any made changes to the 'logs' global.

        Params:
        - api_key (str) : the api key for AN.
        - links (dict) : a dictionary which maps the names a region to the
                         invite link of the region's Telegram channel.
        - an_ag_endpoints (list) : a list of endpoints to the AN forms where
                                   AG's are registered.
    """
    ags = get_all_ags(api_key, an_ag_endpoints)

    for region in regions:
        # Get the AGs which are this region.
        ags_registered = [ag for ag in ags if converter("municipality", "region", ag["Municipality"]) == region]

        # Parse these AGs' phonenumbers - remove AGs with invalid numbers.
        ags_invalid_phone = []
        for ag in ags_registered:
            if convert_phone_number(ag["Phone number"]): # Valid number
                ag["Phone number"] = convert_phone_number(ag["Phone number"])
            else: # Invalid number
                ags_registered.remove(ag)
                ags_invalid_phone.append(ag)

        # Get the AGs in this region's Telegram channel.
        ags_in_channel = ["+" + user.phone for user in await client.get_participants(links[region]) if user.phone]

        # Find the people who should be added/removed.
        to_add = [ag for ag in ags_registered if ag["Phone number"] not in ags_in_channel]

        if DEBUG:
            import pprint
            pp = pprint.PrettyPrinter(indent=4)
            print("Region: {}".format(region))
            print("     AG's registed in AN: ")
            pp.pprint([filter_ag(ag) for ag in ags_registered])
            print("     AG's in telegram: ")
            pp.pprint([ag for ag in ags_in_channel])
            print("     AG's that should be added: ")
            pp.pprint([filter_ag(ag) for ag in to_add])
            print("     AG's with invalid phone numbers: ")
            pp.pprint([filter_ag(ag) for ag in ags_invalid_phone])
            print("\n")

        # Add users and log the result.
        for ag in to_add:
            try:
                await add_user(ag, region, links)
                logs[region]["added"].append(filter_ag(ag))
                await send_invite(ag, region, links)
            except IndexError: # User doesn't have telegram.
                if not ag in logs[region]["no_telegram"]:
                    logs[region]["no_telegram"].append(filter_ag(ag))
            except Exception as e:
                if not ag in logs[region]["error"]:
                    logs[region]["error"].append((filter_ag(ag), e))

        # Log invalid phone numbers.
        for ag in ags_invalid_phone:
            logs[region]["update_number"].append(filter(ag))


def filter_ag(ag):
    """
        Removes unnecessary fields from a user dict to allow for clean logs.

        Params:
        - ag (dict) : a dictionary of the custom fields of a user on AN.

        Returns:
        - (dict) : the same dict, but only with the: 'rep_name',
                   'Municipality', 'AG_name' and 'Phone number' fields.
    """
    try:
        return {"AG_name" : ag["AG_name"],
                "Municipality" : ag["Municipality"],
                "rep_name" : ag["rep_name"],
                "Phone number" : ag["Phone number"]}
    except KeyError: # Sometimes, the data isn't complete.
        return ag


async def send_log(admins):
    """
        Sends a Telegram message containing the current logs to
        the admins specified in the environment variable 'super_admins'.

        The log message contains:
        - the new phonenumbers added to each regional channel;
        - phonenumbers which don't have telegram;
        - phonenumbers which gave another error when trying to add them;
        - phonenumbers which have been detected as invalid.

        Params:
        - admins (list) : a list of admins to which to send the logs.
    """
    for admin in admins:
        message = "Log van affiniteitsgroep kanalen:\n"
        await client.send_message(admin, message)

        for region in regions:
            message = "\n"
            message += region
            message += "\n      Toegevoegd: {}".format(logs[region]["added"])
            message += "\n      Geen telegram: {}".format(logs[region]["no_telegram"])
            message += "\n      Error bij toevoegen: {}".format(logs[region]["error"])
            message += "\n      Update nummer: {}".format(logs[region]["update_number"])
            await client.send_message(admin, message)


def clear_logs():
    """
        Clears the 'logs' gloval, and resets it to an empty dict of dicts with
        the used format.
    """
    for region in regions:
        logs[region] = {"added" : [], "no_telegram" : [], "error" : [], "update_number" : []}


async def send_invite(user, region, links):
    """
        Sends a bilingual message on Telegram to the specified user, telling them
        they've been added to their region's Telegram channel. The message also
        contains a link to the channel, to allow them to add their fellow AG members.

        Assumes a correct phone number to which a Telegram account has been coupled.

        Params:
        - user (dict) : a dictionary of the custom fields of this user on AN.
        - region (str) : the name of the region this person lives in.
        - links (dict) : a dictionary which maps the names a region to the
                         invite link of the region's Telegram channel.
    """
    # Format the messages.
    message = "Beste {}, \nJij staat in Action Network geregistreerd als de afgevaardigte/representative van Extinction Rebellion affiniteitsgroep {}. Zojuist ben je toegevoegd aan het officiële telegram kanaal voor affiniteitsgroepen in regio {}. Dit kanaal houdt je up-to-date over alle acties in je regio, en geeft andere informatie die je affiniteitsgroep helpt bij het actie voeren. Door de informatie die hier langs komt in de gaten te houden, en door te geven aan je affiniteitsgroep, weet je alles wat nodig is om in actie te komen met Extinction Rebellion! \nMeer informatie over de kanalen vind je hier: https://xrb.link/hn8LeH2X3 . Mochten ook andere leden van je affiniteitsgroep in het kanaal willen, dan is hier een link waarmee ze toegang krijgen: {} . Mocht jullie groep in meerdere regio's actief zijn, stuur mij dan even een berichtje - ik kan je dan ook in de kanelen voor andere regio's plaatsen. Voor overige vragen kun je mij hier ook via Telegram contacteren.\nLove & Rage Martijn van Extinction Rebellion".format(user["rep_name"], user["AG_name"], region, links[region])
    message_en = "Dear {},\nYou're registered as the representative of your Extinction Rebellion affinity group {}. If all went well, you were just added to the official information channel for affinity groups in your region: {}. This channel will keep you up to date on all actions in your region, as well as other information that is useful to support your affinity group. By keeping an eye on the information that comes through here, and passing it on to your affinity group, you will know everything you need to come into action with XR!\nMore information about the channels can be found here: https://xrb.link/hn8LeH2X3   If other members of your affinity group also wish to join the channel, here's a link to give them access: {} . If your affinity group is active in mulitple reagions, please send me a message, and I will add you to the channels for the other regions as well. You can also reach me here on telegram for any addition questions!\nLove & Rage Martijn from Extinction Rebellion".format(user["rep_name"], user["AG_name"], region, links[region])

    # Send them.
    await client.send_message(user["Phone number"], message_en)
    await client.send_message(user["Phone number"], message)


async def add_user(user, region, links):
    """
        Adds the specified user to the telegram channel of the specified region.
        First adds the user as a contact; this gives permission to add them to
        a channel.

        TODO: remove the user from contacts.

        Params:
        - user (dict) : a dictionary of the custom fields of this user on AN.
        - region (str) : the name of the region this person lives in.
        - links (dict) : a dictionary which maps the names a region to the
                         invite link of the region's Telegram channel.
    """
    # Add user to contact. This allows us to add them to the channel
    contact = InputPhoneContact(client_id=0, phone=user["Phone number"], first_name=user["rep_name"], last_name="xr_ag_rep_{}".format(region))

    # There's strong constraints on making this request.
    while True:
        try:
            result = await client(ImportContactsRequest([contact]))
            break
        except FloodWaitError as e:
            print("Flood errror - waiting: {}".format(e))
            sleep(60)

    # Add them to the correct channel.
    await client(InviteToChannelRequest(links[region], [result.users[0]]))


async def main():
    """
        Starts the sync loop. The loop repeats every five minutes.
        Sends a log of the progress to the admins each day.
    """
    # Start-up.
    await client.start()
    current_day = int(strftime("%j", localtime(time()))) - 1

    # Get required environment variables.
    api_key = os.getenv("api_key_an")
    links = json.loads(os.getenv("links"))
    super_admins = json.loads(os.getenv("super_admins"))
    an_ag_endpoints = json.loads(os.getenv("an_ag_endpoints"))

    # This sets up the log dict structure.
    clear_logs()

    # Sync the channels.
    while True:
        await sync_channels(api_key, links, an_ag_endpoints)

        # If it's a new day, log.
        new_day = int(strftime("%j", localtime(time())))
        if new_day != current_day:
            current_day = new_day
            await send_log(super_admins)
            clear_logs()

        # Loop every 5 minutes.
        sleep(5 * 60)


# Load environment variables.
load_dotenv()

# Set up telegram client and launch sync loop.
client = TelegramClient(os.getenv("username"), os.getenv("api_id_tg"), os.getenv("api_hash_tg"))
with client:
    client.loop.run_until_complete(main())
