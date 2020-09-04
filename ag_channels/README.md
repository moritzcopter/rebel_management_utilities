# AG Channels

This file synchronises the phonenumbers of AG's of XR NL registered in AN
with the Telegram broadcast channels for AG's.

Author: Martijn Brehm (mattermost: `@martijn_amsterdam`)
Date: 04/09/2020

## Pre-requisites

Python 3

## Installation

Clone or download repository onto local computer.

```bash
git clone https://github.com/xrnl/rebel_management_utilities.git
```


Install necessary dependencies.

```bash
cd local_group_mapping/ag_channels
pip3 install -r requirements.txt
```

Place required info in `.env` file.

```
api_id_tg=<..>          // (string): the id of the telegram api app created for this script.
api_hash_tg=<..>        // (string): the hash of the telegram api app id for this script.
phone=<..>              // (string): phonenumber of the telegram account used to run the script.
username=<..>           // (string): telegram username of the telegram account used to run the script.
api_key_an=<..>         // (string): api key for action network.
links={"Midden":"","Zuid-Oost":"","Zuid-Holland":"","Noord-Oost":"","Noord-West":""} // (dict): dictionary mapping the five regions to a telegram invite link for the correponding channels.
super_admins=[..]       // (list): list of phonenumbers of admins who receive daily logs.
an_ag_endpoints=[..]    // (list): list of AN endpoints of the different AG forms.
```

## Usage

```bash
python3 ./sync_ag_channels.py
```

The script will run indefinitely. Daily logs of progress are sent, via Telegram, to the phonenumbers in the `super_admins` list in the `.env` file.
