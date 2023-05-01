import json
from models import *

from mongoengine import connect

db = connect('dungeon')

WORLD_FILE = "world.json"

def load_rooms():
    file = WORLD_FILE
    f = open(file, "r")
    rooms = json.load(f)


    for r in rooms:
        features = r.pop("features", None)

        room = Room.from_json(json.dumps(r))

        print(r)

        if features:
            for f in features:
                feature = Feature.from_json(json.dumps(f))
                feature.save(force_insert=True)
                room.features.append(feature)

        room.save(force_insert=True)

if __name__ == "__main__":
    db.drop_database('dungeon')
    load_rooms()
    # load_features()