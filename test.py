import os
import pymongo
import certifi
from dotenv import load_dotenv, find_dotenv

if not os.getenv("PUBLIC_ACTIVATED"):
    assert load_dotenv(find_dotenv()), "Failed to load environment."

print(os.getenv("MONGO_DB"))
db = pymongo.MongoClient(
    os.getenv("MONGO_DB"),
    tlsCAFile=certifi.where()
)
print(db.list_database_names())

# class Room(db.Document):
#     room_code = mongoengine.StringField()
#     started = mongoengine.IntField()
#     game_mode = mongoengine.IntField()
#     difficulty = mongoengine.IntField()
#     language = mongoengine.IntField()
#     admin = mongoengine.StringField()
#     players = mongoengine.ListField(mongoengine.StringField())
#
#
# if __name__ == '__main__':
#     Room(
#         started=0,
#         game_mode=0,
#         difficulty=0,
#         language=0,
#         admin="yummy",
#         players=["poopy"]
#     ).save()

