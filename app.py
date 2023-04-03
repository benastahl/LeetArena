import os

import bcrypt
import random
import secrets
import string
import uuid
import pymysql
import pymongo
from datetime import datetime
from flask import Flask, render_template, redirect, request, session, abort, g
from flask_socketio import SocketIO, emit, join_room, rooms, close_room, leave_room
from database import LeetArena

pymysql.install_as_MySQLdb()
app = Flask(__name__)
socketio = SocketIO(app)
app.config["SECRET_KEY"] = secrets.token_hex()
socketio.init_app(app, cors_allowed_origins="*")
pymongo.MongoClient(

)


class Room(mongoengine.Document):
    room_code = mongoengine.StringField()
    started = mongoengine.IntField()
    game_mode = mongoengine.IntField()
    difficulty = mongoengine.IntField()
    language = mongoengine.IntField()
    admin = mongoengine.StringField()
    players = mongoengine.ListField(mongoengine.StringField())

    def to_json(self):
        return {"room_code": self.room_code,
                "started": self.started,
                "game_mode": self.game_mode,
                "difficulty": self.difficulty,
                "language": self.language,
                "admin": self.started,
                "players": self.players}


# Base

@app.route("/", methods=["GET"])
def display_home():
    auth_token = request.cookies.get("auth_token")
    db = LeetArena()
    with db:
        user = db.get_entry("user", auth_token=auth_token)

    return render_template(
        "home.html",
        user=user,
        login_error=None,
        signup_error=None
    )


# Game

@app.route("/game/<room_code>", methods=["GET"])
def display_game(room_code):
    auth_token = request.cookies.get("auth_token")
    db = LeetArena()
    with db:
        user = db.get_entry("user", auth_token=auth_token)

    if not user:  # No user found or game not found
        return redirect("/")

    room = Room.objects(room_code=room_code).first()

    return render_template(
        "lobby.html",
        user=user,
        room=room,
        admin=room.admin == user.entry_id,
        room_code=room_code,
    )


@app.route("/create-lobby", methods=["POST"])  # Creates lobby and redirects to that lobby.
def create_lobby():
    auth_token = request.cookies.get("auth_token")

    db = LeetArena()
    with db:
        user = db.get_entry("user", auth_token=auth_token)

    if not user:
        return redirect("/")

    # Create a lobby with join code
    room_code_length = 7
    room_code = ''.join(random.choices(string.ascii_uppercase +
                                       string.digits, k=room_code_length))

    print("Creating room...")
    room = Room(
        room_code=room_code,
        started=0,
        game_mode=0,
        difficulty=0,
        language=0,
        admin=user.entry_id,
        players=[user.entry_id]
    )
    room.save()
    print("Created room.")
    room = Room.objects(room_code=room_code).first()
    print(room.players)

    return redirect(f"/game/{room_code}")


# Game Events

@socketio.on("user-connection-lobby")
def user_connected(data):
    id_room = data["lobby_id"]
    id_user = data["user_id"]
    print(f"{id_user} has connected to the lobby: {id_room}")
    join_room(room=id_room)
    room = Room.objects(room_code=id_room).first()

    if id_user not in room.players:
        room.update(players=room.players.append(id_user))
        print("New player:", room.players)
        emit("update-lobby", data=session[id_room], to=id_room)


# Authentication


@app.route("/login", methods=["POST"])
def login():
    email = request.form["email"]
    password = request.form["pass"]  # plain text password

    database = LeetArena()
    with database:
        # login_user returns auth_token of user if email and password correct
        auth_token = database.login_user(email, password)

    if not auth_token:
        return redirect("/?login_error=Email or password not found", 302)

    response = redirect("/", 302)
    # Create an auth browser cookie (random letters and numbers) as our authentication
    # token so the user doesn't have to log in every single time.
    response.set_cookie('auth_token', auth_token, max_age=60 * 60 * 24 * 365)  # One year expiration (in seconds)
    return response


@app.route("/signup", methods=["POST"])
def signup():
    # Collect POST request params from signup
    email = request.form["email"]
    username = request.form["username"]

    # Hash password (hashing means that it is encrypted and impossible to decrypt)
    # We can now only check to see if a plain text input matches the hashed password (bcrypt.checkpw).
    hashed_password = bcrypt.hashpw(bytes(str(request.form["pass"]).encode("utf-8")), bcrypt.gensalt()).decode("utf-8")

    auth_token = secrets.token_hex()

    # Create timestamp of the creation date of the account
    creation_date = int(datetime.timestamp(datetime.now()))

    # Check if email is already in use (get_student returns list of user with that email).
    database = LeetArena()
    with database:
        user = database.get_entry(table_name="user", email=email)

        if user:
            return redirect("/?signup_error=Email is already in use.")

        # Add user to database
        user = database.create_entry(
            table_name="user",
            entry_id=uuid.uuid4(),
            email=email,
            username=username,
            hashed_password=hashed_password,
            auth_token=auth_token,
            creation_date=creation_date,
            admin=0,
        )

    # Set auth cookie token
    response = redirect("/", 302)

    # Create an auth browser cookie (random letters and numbers) as our authentication
    # token so the user doesn't have to log in every single time.
    response.set_cookie('auth_token', auth_token, max_age=31540000)  # One year expiration (in seconds)

    return response


if __name__ == '__main__':
    socketio.run(app, debug=True, port=5555, allow_unsafe_werkzeug=True)
