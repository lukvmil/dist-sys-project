import json
from models import *

from mongoengine import connect; connect('dungeon')

WORLD_DIRECTORY = "default_world"
ROOMS_FILE = "rooms.json"

def load_rooms():
    file = WORLD_DIRECTORY + "/" + ROOMS_FILE
    f = open(file, "r")
    rooms = json.load(f)

    for r in rooms:
        room = Room.from_json(json.dumps(r))
        room.save(force_insert=True)

if __name__ == "__main__":
    load_rooms()