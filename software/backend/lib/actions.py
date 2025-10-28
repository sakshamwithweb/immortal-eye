from concurrent.futures import ThreadPoolExecutor
import json
from lib.actions_lib.get_nearest_aps import get_nearest_aps
from lib.actions_lib.make_twilio_call_to_aps import make_twilio_call_to_aps
import urllib


def call_to_caretakers(client, twilio_phone, caretakers_number):
    # Call
    def make_call(number):
        call = client.calls.create(
            twiml="<Response><Say>Alert from Immortal Eye! Alert from Immortal Eye! The Elder who appointed you as caretaker is being abused! We have shared the location and the footage in the message you will be getting after this call.</Say></Response>",
            from_=twilio_phone,
            to=number
        )
        return call

    # Call to 10 numbers at once parallelly
    with ThreadPoolExecutor(max_workers=10) as executor:
        executor.map(make_call, caretakers_number)


def sms_to_caretakers(client, twilio_phone, caretakers_number, location, footage_url):
    def send_sms(number):
        sms = client.messages.create(
            body = f"Emergency Alert from Immortal Eye! The elder who appointed you as caretaker is being abused. APS and other caretakers have been notified.\n\nLocation: {location['latitude']}, {location['longitude']}\nFootage (expires in 1 hr): {footage_url}",
            from_=twilio_phone,
            to=number
        )
        return sms

    # Send sms to everyone parallelly
    with ThreadPoolExecutor(max_workers=10) as executor:
        executor.map(send_sms, caretakers_number)


def call_to_aps(location, server_url, client, twilio_phone, video_url):
    """Takes location, server_url, client and twilio_phone. Then it looks for nearest APS and gather some user data and call to APS"""

    # Get nearest APS and Call
    aps_number = get_nearest_aps(location)

    # Need more, like name, accurate place name etc etc. to give to cops
    user_data = json.dumps({"location": location, "video_url": video_url})
    user_data_query_string = urllib.parse.quote(user_data)

    # call to aps
    sid = make_twilio_call_to_aps(server_url, user_data_query_string, client, twilio_phone, aps_number)

    return sid
