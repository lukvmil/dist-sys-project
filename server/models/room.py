from mongoengine import Document
from mongoengine.fields import *

class RoomModel(Document):
    desc = StringField()
    # entities = ListField(ReferenceField())
