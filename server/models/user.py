from mongoengine import Document
from mongoengine.fields import *

class User(Document):
    name = StringField(primary_key=True)
    password = StringField()
    location = ReferenceField("Room")
    inventory = ListField(ReferenceField("Item"))

    def enter_room(self, room):
        self.location = room
        room.users.append(self)
        room.save()
        self.save()

    def logout(self):
        room = self.location
        room.users.remove(self)
        room.save()