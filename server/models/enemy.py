from mongoengine import Document
from mongoengine.fields import *

class Enemy(Document):
    name = StringField(primary_key=True)
    health = IntField()
    items = ListField(ReferenceField("Item"))