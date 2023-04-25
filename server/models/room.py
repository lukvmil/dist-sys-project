from mongoengine import Document
from mongoengine.fields import *

class Room(Document):
    name = StringField(primary_key=True)
    description = StringField()
    users = ListField(ReferenceField("User"))
