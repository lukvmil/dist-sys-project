from .room import RoomModel

from mongoengine import Document
from mongoengine.fields import *

class UserModel(Document):
    name = StringField()
    password = StringField()
    location = ReferenceField(RoomModel)
    # inventory = ListField(ReferenceField())