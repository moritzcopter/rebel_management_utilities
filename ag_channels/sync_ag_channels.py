"""
TODO:
- documentation ag sheet
- update requirements with new packages ag sheet
- mass update of ag's in sheet, except one-by-one, to bypass request timeout
    both reading and writing.
- only read new ag's from AN, instead of all AG's.
- check if rep is in telegram is not correct (ABE)
- deleted ag's don't dissapear frmo the sheet yet
- AG's that updated but changed reps do not get updated properly - they're seen as two entities.
"""

from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.errors import HttpError

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
import pickle
from dotenv import load_dotenv
import os
import os.path


regions = ["Midden", "Zuid-Oost", "Zuid-Holland", "Noord-Oost", "Noord-West"]
logs = {"added" : [], "no_telegram" : [], "error" : [], "update_number" : []}
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


async def sync_channels(api_key, links, an_ag_endpoints, spreadsheet_id, google):
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
        - spreadsheet_id (string) : id of the used google spreadsheet.
        - google (?) : api object used to make api calls.

    """
    ags = get_all_ags(api_key, an_ag_endpoints)
    ags_formatted = []
    ags_in_telegram_channel = []
    ags_not_in_telegram_channel = []

    # Format list of AG's.
    for ag in ags:
        ag["region"] = converter("municipality", "region", ag["Municipality"])
        if not ag["region"]:
            continue
        ag["telegram"] = True # Will be set to False if AG is not added to channel after this function finishes.
        ag["Phone number"] = convert_phone_number(ag["Phone number"])
        if ag["Phone number"]: # Becomes None if number is invalid.
            ags_formatted.append(ag)


    # Check which formatted AG's are already in telegram channels.
    ags_in_telegram_channel = [
        ag
        for region in regions
        for user in await client.get_participants(links[region]) if user.phone
        for ag in ags_formatted if user.phone in ag["Phone number"]
    ]

    # Add reps to telegram channel.
    for ag in [ag for ag in ags_formatted if ag not in ags_in_telegram_channel]:
        # On succesful add, send welcome message and log.
        try:
            await add_user(ag, links)
            # logs["added"].append(filter_ag(ag))
            await send_invite(ag, links)
        # User doesn't have telegram.
        except IndexError:
            ag["telegram"] = False
            # if not ag in logs["no_telegram"]:
                # logs["no_telegram"].append(filter_ag(ag))
        except Exception as e:
            print("Error when adding rep: {}".format(e))
            # if not ag in logs["error"]:
                # logs["error"].append((filter_ag(ag), e))

    # Update the google sheet.
    update_ags_on_sheet(spreadsheet_id, google, ags_formatted)


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
            message += "\n      Toegevoegd: {}".format(logs["added"])
            message += "\n      Geen telegram: {}".format(logs["no_telegram"])
            message += "\n      Error bij toevoegen: {}".format(logs["error"])
            message += "\n      Update nummer: {}".format(logs["update_number"])
            await client.send_message(admin, message)


async def send_invite(user, links):
    """
        Sends a bilingual message on Telegram to the specified user, telling them
        they've been added to their region's Telegram channel. The message also
        contains a link to the channel, to allow them to add their fellow AG members.

        Assumes a correct phone number to which a Telegram account has been coupled.

        Params:
        - user (dict) : a dictionary of the custom fields of this user on AN.
        - links (dict) : a dictionary which maps the names a region to the
                         invite link of the region's Telegram channel.
    """
    # Format the messages.
    message = "Beste {}, \nJij staat in Action Network geregistreerd als de afgevaardigte/representative van Extinction Rebellion affiniteitsgroep {}. Zojuist ben je toegevoegd aan het officiële telegram kanaal voor affiniteitsgroepen in regio {}. Dit kanaal houdt je up-to-date over alle acties in je regio, en geeft andere informatie die je affiniteitsgroep helpt bij het actie voeren. Door de informatie die hier langs komt in de gaten te houden, en door te geven aan je affiniteitsgroep, weet je alles wat nodig is om in actie te komen met Extinction Rebellion! \nMeer informatie over de kanalen vind je hier: https://xrb.link/hn8LeH2X3 . Mochten ook andere leden van je affiniteitsgroep in het kanaal willen, dan is hier een link waarmee ze toegang krijgen: {} . Mocht jullie groep in meerdere regio's actief zijn, stuur mij dan even een berichtje - ik kan je dan ook in de kanelen voor andere regio's plaatsen. Voor overige vragen kun je mij hier ook via Telegram contacteren.\nLove & Rage Martijn van Extinction Rebellion".format(user["rep_name"], user["AG_name"], user["region"], links[user["region"]])
    message_en = "Dear {},\nYou're registered as the representative of your Extinction Rebellion affinity group {}. If all went well, you were just added to the official information channel for affinity groups in your region: {}. This channel will keep you up to date on all actions in your region, as well as other information that is useful to support your affinity group. By keeping an eye on the information that comes through here, and passing it on to your affinity group, you will know everything you need to come into action with XR!\nMore information about the channels can be found here: https://xrb.link/hn8LeH2X3   If other members of your affinity group also wish to join the channel, here's a link to give them access: {} . If your affinity group is active in mulitple reagions, please send me a message, and I will add you to the channels for the other regions as well. You can also reach me here on telegram for any addition questions!\nLove & Rage Martijn from Extinction Rebellion".format(user["rep_name"], user["AG_name"], user["region"], links[user["region"]])

    # Send them.
    await client.send_message(user["Phone number"], message_en)
    await client.send_message(user["Phone number"], message)


async def add_user(user, links):
    """
        Adds the specified user to the telegram channel of the specified region.
        First adds the user as a contact; this gives permission to add them to
        a channel.

        TODO: remove the user from contacts.

        Params:
        - user (dict) : a dictionary of the custom fields of this user on AN.
        - links (dict) : a dictionary which maps the names a region to the
                         invite link of the region's Telegram channel.
    """
    # Add user to contact. This allows us to add them to the channel
    contact = InputPhoneContact(client_id=0, phone=user["Phone number"], first_name=user["rep_name"], last_name="xr_ag_rep_{}".format(user["region"]))

    # There's strong constraints on making this request.
    while True:
        try:
            result = await client(ImportContactsRequest([contact]))
            break
        except FloodWaitError as e:
            print("Flood errror - waiting: {}".format(e))
            sleep(60)

    # Add them to the correct channel.
    await client(InviteToChannelRequest(links[user["region"]], [result.users[0]]))


def auth_google_api():
    """
        Authorises the google sheets api.

        Returns:
        - () : the object used to make API calls.
    """
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)

    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', ['https://www.googleapis.com/auth/spreadsheets'])
            creds = flow.run_local_server(port=0)

        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    return build('sheets', 'v4', credentials=creds).spreadsheets()


def update_ags_on_sheet(spreadsheet_id, google, ags):
    """
        Writes the given AG's to the sheet. First checks if an AG is already
        on the sheet, if so, updates the data on that row. If not, adds the AG
        at the first empty row.

        Params:
        - .... TODO
    """
    # Get current sheet.
    try:
        current_sheet_data = read_sheet(spreadsheet_id, google)[2:]
    except HttpError as e:
        print("Too many requests to read sheet - waiting 100 sec: {}".format(e))
        sleep(100)
        return

    fields = ["AG_name", "region", "telegram", "Municipality", "rep_name",
              "Phone number", "AG_size", "AG_n_arrestables", "AG_regen_phone",
              "AG_comments"]
    next_row = len(current_sheet_data) + 1
    print(current_sheet_data)

    # Prepare each AG for writing.
    for ag in ags:
        # Fill in empty fields when there's no value prevent errors.
        for field in fields:
            if not field in ag:
                ag[field] = ""
        if ag["rep_name"] == "rebel":
            ag["rep_name"] = ""

        # Format data for request.
        ag_data = [
            ag["AG_name"], ag["region"], ag["telegram"], ag["Municipality"], ag["rep_name"],
            ag["Phone number"], ag["AG_size"], ag["AG_n_arrestables"],
            ag["AG_regen_phone"], ag["AG_comments"], strftime("%b %d %Y %H:%M:%S", localtime(time()))
        ]

        # Place new AG's on a new row; update existing AG's on their existing row.
        ag_already_in_sheet = False
        for i in range(len(current_sheet_data)):
            if ag["AG_name"] == current_sheet_data[i][0]:
                current_sheet_data[i] = ag_data
                ag_already_in_sheet = True
                break
        if not ag_already_in_sheet:
            current_sheet_data.append(ag_data)

    try:
        write_to_sheet(spreadsheet_id, google, current_sheet_data)
    except HttpError as e:
        print("Too many requests to write to sheet - waiting 100 sec: {}".format(e))
        sleep(100)
        return


def read_sheet(spreadsheet_id, google, row=0):
    """
        Returns the content of the entire sheet. If a row number above 0 is
        specified, only returns the contents of that row.
    """
    if row > 0:
        return google.values().get(
            spreadsheetId=spreadsheet_id,
            range="Synced-Action-Network-data!A{}".format(row),
        ).execute().get('values', [])
    return google.values().get(
        spreadsheetId=spreadsheet_id,
        range="Synced-Action-Network-data".format(row),
    ).execute().get('values', [])


def write_to_sheet(spreadsheet_id, google, data, row=3):
    """
        Writes the given data to the used google spreadsheet.

        Params:
        - spreadsheet_id (string) : id of the used google spreadsheet.
        - google (?) : api object used to make api calls.
        - data (list of lists) : inner lists contains entries which will be
                                 written to individual cells in the row, starting
                                 at index 1.
        - row (int) : number of the row to which to start writing. Defaults at 3.

    """
    range = "Synced-Action-Network-data!A{}".format(row)
    body = {
        "range": range,
        "majorDimension": "ROWS",
        "values": data
    }
    google.values().update(
        spreadsheetId=spreadsheet_id,
        range=range,
        valueInputOption="RAW",
        body=body,
    ).execute()



async def main():
    """
        Starts the sync loop. The loop repeats every five minutes.
        Sends a log of the progress to the admins each day.
    """
    # Start-up.
    google = auth_google_api()
    await client.start()
    current_day = int(strftime("%j", localtime(time()))) - 1

    # Get required environment variables.
    api_key = os.getenv("api_key_an")
    links = json.loads(os.getenv("links"))
    super_admins = json.loads(os.getenv("super_admins"))
    an_ag_endpoints = json.loads(os.getenv("an_ag_endpoints"))
    spreadsheet_id = os.getenv("spreadsheet")

    # Sync the channels.
    while True:
        await sync_channels(api_key, links, an_ag_endpoints, spreadsheet_id, google)

        # If it's a new day, log.
        # new_day = int(strftime("%j", localtime(time())))
        # if new_day != current_day:
        #     current_day = new_day
        #     await send_log(super_admins)

        # Loop every 10 minutes.
        sleep(10 * 60)


# Load environment variables.
load_dotenv()

# Set up telegram client and launch sync loop.
client = TelegramClient(os.getenv("username"), os.getenv("api_id_tg"), os.getenv("api_hash_tg"))
with client:
    client.loop.run_until_complete(main())
