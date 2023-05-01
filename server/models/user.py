from mongoengine import Document
from mongoengine.fields import *
from .room import Room

class User(Document):
    name = StringField(primary_key=True)
    password = StringField()
    location = ReferenceField("Room")
    items = ListField(ReferenceField("Item"))

    def move_to(self, room):
        prev_room = self.location
        if prev_room:
            if self in prev_room.users:
                prev_room.users.remove(self)
                prev_room.save()
        
        room.users.append(self)
        room.save()

        self.location = room
        self.save()

    def reset(self):
        start = Room.objects(start=True).first()
        self.move_to(start)
        self.save()

    def logout(self):
        room = self.location
        room.users.remove(self)
        room.save()