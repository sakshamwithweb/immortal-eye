import json
from lib.actions_lib.get_state_from_coors import get_state_from_coords


def get_nearest_aps(location):
    """takes location then reads data/aps.json to get state, based on coords and find the aps_number then returns"""

    aps_data = []
    with open("data/aps.json", "r") as file:
        aps_data = json.loads(file.read())

    state_name = get_state_from_coords(location.latitude, location.longitude)
    aps_number = (next((state for state in aps_data if state["State"] == state_name), None)).get("aps_no")  # Got APS Number

    return aps_number