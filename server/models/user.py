from mongoengine import Document
from mongoengine.fields import *
from .room import Room
from .item import Item

class User(Document):
    name = StringField(primary_key=True)
    password = StringField()
    location = ReferenceField("Room")
    health = IntField()
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

    def has(self, i):
        item = Item.objects(pk=i).first()
        if item in self.items:
            return True
        else:
            return False

    def reset(self):
        start = Room.objects(start=True).first()
        self.items = []
        self.move_to(start)
        self.save()

    def logout(self):
        room = self.location
        room.users.remove(self)
        room.save()