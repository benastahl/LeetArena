import os

import bcrypt
import random
import secrets
import string
import uuid
import certifi
import pymysql
import mongoengine
from datetime import datetime
from dotenv import load_dotenv, find_dotenv
from flask import Flask, render_template, redirect, request, session, abort
from flask_socketio import SocketIO, emit, rooms, join_room, close_room, leave_room

pymysql.install_as_MySQLdb()
app = Flask(__name__)
socketio = SocketIO(app)
app.config["SECRET_KEY"] = secrets.token_hex()
socketio.init_app(app, cors_allowed_origins="*")
if not os.getenv("PUBLIC_ACTIVATED"):
    assert load_dotenv(find_dotenv()), "Failed to load environment."
print(os.getenv("MONGO_DB"))
db_url = os.getenv("MONGO_DB")
db = mongoengine.connect(
    host=db_url,
    tlsCAFile=certifi.where()
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


class Users(mongoengine.Document):
    email = mongoengine.StringField()
    username = mongoengine.StringField()
    hashed_password = mongoengine.StringField()
    auth_token = mongoengine.StringField()
    admin = mongoengine.IntField()


# Base

@app.route("/", methods=["GET"])
def display_home():
    auth_token = request.cookies.get("auth_token")

    user = Users.objects(auth_token=auth_token).first()

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

    user = Users.objects(auth_token=auth_token).first()

    if not user:  # No user found or game not found
        return redirect("/")

    room = Rooms.objects(room_code=room_code).first()

    print(room.players)
    return render_template(
        "lobby.html",
        players=room.players,
        user=user,
        room=room,
        admin=room.admin == user.username,
        room_code=room_code,
    )


@app.route("/create-lobby", methods=["POST"])  # Creates lobby and redirects to that lobby.
def create_lobby():
    auth_token = request.cookies.get("auth_token")

    user = Users.objects(auth_token=auth_token).first()

    if not user:
        return redirect("/")

    # Create a lobby with join code
    room_code_length = 7
    room_code = ''.join(random.choices(string.ascii_uppercase +
                                       string.digits, k=room_code_length))

    print("Creating room...")
    Rooms(
        room_code=room_code,
        started=0,
        game_mode=0,
        difficulty=0,
        language=0,
        admin=user.username,
        players=[user.username]
    ).save()
    print("Created room.")
    room = Rooms.objects(room_code=room_code).first()
    print(room.players)

    return redirect(f"/game/{room_code}")


# Game Events

@socketio.on("lobby-user-connected")
def user_connected(data):
    room_code = data["room_code"]
    username = data["username"]
    print(f"{username} has connected to the lobby: {room_code}")

    # Room data
    room = Rooms.objects(room_code=room_code).first()
    join_room(room=room_code)

    # New user connected
    if username not in room.players:
        print(rooms())
        l_new_players = room.players.append(username)
        room.update(players=l_new_players)

        user = Users.objects(username=username).first()
        pfp = "https://c4.wallpaperflare.com/wallpaper/273/268/863/appa-avatar-the-last-airbender-glasses-wallpaper-thumb.jpg"
        emit("lobby-update", {
            "username": username,
            "pfp": pfp,
            "level": "13",
            "admin": user.username == room.admin,

        }, room=room_code)


@socketio.on("lobby-user-disconnected")
def user_disconnected(data):
    room_code = data["room_code"]
    username = data["username"]
    print(f"{username} has disconnected from the lobby: {room_code}")

    # Room data
    room = Rooms.objects(room_code=room_code).first()
    leave_room(room=room_code)
    print(room.players)
    room.update(players=room.players.remove(username))
    emit("lobby-update", {"players": room.players}, room=room_code)


# Authentication


@app.route("/login", methods=["POST"])
def login():
    email = request.form["email"]
    password = request.form["pass"]  # plain text password

    user = Users.objects(email=email).first()
    if not user:
        return render_template(
            "home.html",
            login_error="Email not found.",
        )

    correct_pw = bcrypt.checkpw(bytes(password.encode("utf-8")), user.hashed_password.encode("utf-8"))
    if not correct_pw:
        return render_template(
            "home.html",
            login_error="Incorrect password.",
        )

    auth_token = secrets.token_hex()
    response = redirect("/", 302)
    # Create an auth browser cookie (random letters and numbers) as our authentication
    # token so the user doesn't have to log in every single time.
    response.set_cookie('auth_token', auth_token, max_age=60 * 60 * 24 * 365)  # One year expiration (in seconds)
    user.update(auth_token=auth_token)

    return response


@app.route("/signup", methods=["POST"])
def signup():
    # Collect POST request params from signup
    email = request.form["email"]
    username = request.form["username"]

    # Check if email or username is already in use.
    if Users.objects(email=email).first() or Users.objects(username=username).first():
        render_template(
            "home.html",
            signup_error="Email already in use.",
        )

    # Hash password (hashing means that it is encrypted and impossible to decrypt)
    # We can now only check to see if a plain text input matches the hashed password (bcrypt.checkpw).
    hashed_password = bcrypt.hashpw(bytes(str(request.form["pass"]).encode("utf-8")), bcrypt.gensalt()).decode("utf-8")

    auth_token = secrets.token_hex()

    # Create user.
    Users(
        email=email,
        username=username,
        hashed_password=hashed_password,
        auth_token=auth_token,
        admin=0,
    ).save()

    # Set auth cookie token
    response = redirect("/", 302)

    # Create an auth browser cookie (random letters and numbers) as our authentication
    # token so the user doesn't have to log in every single time.
    response.set_cookie('auth_token', auth_token, max_age=31540000)  # One year expiration (in seconds)

    return response


if __name__ == '__main__':
    socketio.run(app, debug=True, port=5555, allow_unsafe_werkzeug=True)
