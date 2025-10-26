from twilio.twiml.voice_response import VoiceResponse, Start

def make_twilio_call_to_aps(server_url, user_data_query_string, client, twilio_phone, aps_number):
    response = VoiceResponse()
    start = Start()
    start.transcription(
        status_callback_url=f'{server_url}/transcript?user_data={user_data_query_string}',
        track='inbound_track'
    )
    response.append(start)
    response.pause(30) # To keep it alive or else it wil just follow things then close

    call = client.calls.create(
        twiml=str(response),
        from_=twilio_phone,
        to=aps_number
    )
    return call.sid