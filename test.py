import os
import mongoengine
from dotenv import load_dotenv, find_dotenv

if not os.getenv("PUBLIC_ACTIVATED"):
    assert load_dotenv(find_dotenv()), "Failed to load environment."

db = mongoengine.connect(
    host=os.getenv("MONGO_DB")
)
print(db.list_database_names())


class Rooms(mongoengine.Document):
    room_code = mongoengine.StringField()
    started = mongoengine.IntField()
    game_mode = mongoengine.IntField()
    difficulty = mongoengine.IntField()
    language = mongoengine.IntField()
    admin = mongoengine.StringField()
    players = mongoengine.ListField(mongoengine.StringField())


if __name__ == '__main__':
    Rooms(
        started=0,
        game_mode=0,
        difficulty=0,
        language=0,
        admin="yummy",
        players=["poopy"]
    ).save()

