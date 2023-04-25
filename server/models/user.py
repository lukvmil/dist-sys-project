from mongoengine import Document
from mongoengine.fields import *

class User(Document):
    name = StringField(primary_key=True)
    password = StringField()
    location = ReferenceField("Room")
    inventory = ListField(ReferenceField("Item"))