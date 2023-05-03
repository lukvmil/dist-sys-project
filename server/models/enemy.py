from mongoengine import Document
from mongoengine.fields import *

class Enemy(Document):
    name = StringField(primary_key=True)
    tag = StringField()
    placement = StringField()
    description = StringField()
    health = IntField()
    item = ReferenceField("Item")
    accuracy = IntField()
    damage = IntField()
    dead = BooleanField()

    def kill(self, room):
        room.enemies.remove(self)
        room.items.append(self.item)
        room.save()
        self.dead = True
        self.save()