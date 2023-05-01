from mongoengine import Document
from mongoengine.fields import *

class Room(Document):
    name = StringField(primary_key=True)
    description = StringField()
    start = BooleanField()
    users = ListField(ReferenceField("User"))
    features = ListField(ReferenceField("Feature"))
