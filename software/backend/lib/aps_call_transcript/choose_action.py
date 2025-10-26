import requests


def choose_action(transcript, context, given_data, openai_key):
    """
    AI core: Takes the latest transcript, detects if it's IVR or human,
    and returns TwiML snippet (without <Response>) for the next action. 
    Ultimate goal is to talk to a human and give all the infos..
    """

    prompt = f"""
You are a real-time AI call assistant integrated with Twilio.

Your mission:
- If the other side is an **IVR or bot**, do everything possible to quickly reach a **live human agent**.
  - You can press digits (<Play digits="1"/>, <Play digits="0"/>, etc.),
  - say words (<Say>Representative</Say>, <Say>Operator</Say>, etc.),
  - or wait briefly (<Pause length="3"/>).
  - Be creative and efficient — your goal is to reach a human quickly.
- If the other side is a **human**, respond naturally using the data provided in "given_data", 
  and then communicate this message clearly:
  "There is a grandma in the location I have shared, she is abused by her caretakers."

If the other side sounds like a live person (they introduce themselves or say 'how may I help you'), 
treat them as HUMAN immediately and deliver the message using the given data.

You must return only valid **TwiML command(s)** (e.g., <Say>...</Say>, <Play digits="1"/>, <Pause length="3"/>, <Hangup/>).
Do not include <Response> wrapper, any JSON or Markdown — only the inner TwiML.

Here is the full conversational context so far:
{context}

Here is the user-provided data you can use if asked for information (e.g. name, location, etc.):
{given_data}

Here is the most recent transcript from the call:
"{transcript}"

Be fast, natural, and adaptive. Respond with only TwiML that should be appended next.
"""

    resp = requests.post("https://api.openai.com/v1/chat/completions",
                         json={
                             "model": "gpt-4o-mini",
                             "messages": [{"role": "user", "content": prompt}],
                             "max_tokens": 100,
                             "temperature": 0
                         },
                         headers={"Authorization": f"Bearer {openai_key}"})
    data = resp.json()
    twiml_snippet = data["choices"][0]["message"]["content"].strip()
    print("AI TwiML:", twiml_snippet)
    code = f"{twiml_snippet} <Pause length='30'/>"
    return code