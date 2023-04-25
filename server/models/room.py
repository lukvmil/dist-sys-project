from mongoengine import Document
from mongoengine.fields import *

class Room(Document):
    description = StringField()
    users = ListField(ReferenceField("User"))
