from concurrent.futures import ThreadPoolExecutor
import json
from lib.actions_lib.get_nearest_aps import get_nearest_aps
from lib.actions_lib.make_twilio_call_to_aps import make_twilio_call_to_aps
import urllib


def call_to_caretakers(client, twilio_phone, caretakers_number):
    # Call
    def make_call(number):
        call = client.calls.create(
            twiml="<Response><Say>Hello Grandpa's family members!</Say></Response>",
            from_=twilio_phone,
            to=number
        )
        return call

    # Call to 10 numbers at once parallelly
    with ThreadPoolExecutor(max_workers=10) as executor:
        executor.map(make_call, caretakers_number)


def sms_to_caretakers(client, twilio_phone, caretakers_number):
    def send_sms(number):
        sms = client.messages.create(
            body="Hey You, are you getting this message? We are from Immortal Eye 👁️",
            from_=twilio_phone,
            to=number
        )
        return sms

    # Send sms to everyone parallelly
    with ThreadPoolExecutor(max_workers=10) as executor:
        executor.map(send_sms, caretakers_number)


def call_to_aps(location, server_url, client, twilio_phone):
    """Takes location, server_url, client and twilio_phone. Then it looks for nearest APS and gather some user data and call to APS"""

    # Get nearest APS and Call
    aps_number = get_nearest_aps(location)

    # Need more, like name, accurate place name etc etc. to give to cops
    user_data = json.dumps({"location": location})
    user_data_query_string = urllib.parse.quote(user_data)

    # call to aps
    sid = make_twilio_call_to_aps(server_url, user_data_query_string, client, twilio_phone, aps_number)

    return sid
