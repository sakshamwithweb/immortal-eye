def update_call_with_twiml(call_sid, twiml, client):
    return client.calls(call_sid).update(twiml=f"<Response>{twiml}</Response>")