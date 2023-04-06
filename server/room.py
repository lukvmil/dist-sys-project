from mongoengine import Document
from mongoengine.fields import *

class RoomModel(Document):
    id = StringField(primary_key=True)
    desc = StringField()
    entities = ListField(ReferenceField())
