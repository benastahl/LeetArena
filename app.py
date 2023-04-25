import os
import bcrypt
import random
import secrets
import string
import uuid
import certifi
import pymysql
import mongoengine
import logging
from datetime import datetime
from dotenv import load_dotenv, find_dotenv
from flask import Flask, render_template, redirect, request
from flask_socketio import SocketIO, emit, rooms, join_room, close_room, leave_room

logging.getLogger('socketio').setLevel(logging.CRITICAL)
logging.getLogger('werkzeug').setLevel(logging.ERROR)
logging.getLogger('engineio').setLevel(logging.CRITICAL)

pymysql.install_as_MySQLdb()
app = Flask(__name__)
socketio = SocketIO(app)
app.config["SECRET_KEY"] = secrets.token_hex()
socketio.init_app(app, cors_allowed_origins="*")
if not os.getenv("PUBLIC_ACTIVATED"):
    assert load_dotenv(find_dotenv()), "Failed to load environment."

db_url = os.getenv("MONGO_DB")
db = mongoengine.connect(
    host=db_url,
    tlsCAFile=certifi.where()
)


class Rooms(mongoengine.Document):
    room_code = mongoengine.StringField()
    started = mongoengine.IntField()
    game_mode = mongoengine.StringField()
    game_difficulty = mongoengine.StringField()
    game_lang = mongoengine.StringField()
    admin = mongoengine.StringField()
    players = mongoengine.ListField(mongoengine.StringField())


class Users(mongoengine.Document):
    email = mongoengine.StringField()
    username = mongoengine.StringField()
    hashed_password = mongoengine.StringField()
    auth_token = mongoengine.StringField()
    admin = mongoengine.IntField()


Rooms.objects(started=0).delete()
Rooms.objects(started=1).delete()


# Base

@app.route("/", methods=["GET"])
def display_home():
    auth_token = request.cookies.get("auth_token")

    user = Users.objects(auth_token=auth_token).first()
    start_mode = {True: "create-lobby-container", False: "signup-form-container"}.get(bool(user))

    # Renders home.
    return render_template(
        "home.html",
        user=user,
        start_mode=start_mode
    )


# Game

@app.route("/game/<room_code>", methods=["GET"])
def display_game(room_code):
    auth_token = request.cookies.get("auth_token")  # Collects auth token from browser cookies.

    # Collects user and room data from db.
    user = Users.objects(auth_token=auth_token).first()
    room = Rooms.objects(room_code=room_code).first()

    if not room:  # No user found or game not found.
        return redirect("/?error=The room you tried to join was not found.")
    if not user:  # User session expired or attempted to join game without being logged in.
        return redirect("/?error=Login before you can join a lobby.")

    # Render game if the game has started.
    if room.started:
        if user.username not in room.players:  # Redirects if room has already started and player is not enrolled in game.
            return redirect("/?error=The game you are trying to join has started.")
        prompt = \
"""\
function foo(items) {
    let x = "All this is syntax highlighted";
    return x;
}
"""
        # Renders the game.
        return render_template(
            "arena.html",
            room_code=room_code,
            room=room,
            user=user,
            question="Please answer this question.",
            prompt=prompt
        )

    # Default rendering of the lobby.
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

    print(f"Creating room {room_code}...")
    # Creates room db entry and saves.
    Rooms(
        room_code=room_code,
        started=0,
        game_mode=request.form.get("game-mode"),
        game_difficulty=request.form.get("game-difficulty"),
        game_lang=request.form.get("game-language"),
        admin=user.username,
        players=[]
    ).save()
    print(f"Created room {room_code}")

    return redirect(f"/game/{room_code}")


# Game Events


@socketio.on("join")
def user_joined(data):
    username = data['username']
    room_code = data['room']
    print(f"{username} has joined the game ({room_code}).")

    room = Rooms.objects(room_code=room_code).first()
    if not room:
        emit("room-closed", room=room_code)
        close_room(room=room_code)
        return

    # Join Socket Room. Allows you to emit signals to players in one room/lobby
    # We join the room here because if a user refreshed, we want their socket to reconnect
    # to the room to receive signals.
    join_room(room=room_code)

    # Makes sure that the player is not already in the room.
    if username in room.players:
        return

    print(f""
          f"New Lobby Connection\n"
          f"----------------------\n"
          f"User: {username}\n"
          f"Room: {room_code}\n"
          f"Players: {room.players}\n"
          f"")

    # Adds player to the player list in database.
    room.players.append(username)
    room.update(players=room.players)
    room.save()

    # Signals players in the room to update player list.
    emit("user-joined", {
        "username": username,
        "pfp": "https://c4.wallpaperflare.com/wallpaper/553/304/895/avatar-the-last-airbender-appa-glasses-wallpaper-preview.jpg",
        "level": "13",
        "admin": room.admin == username,
    },
         room=room_code,
         )


@socketio.on("leave")
def user_left(data):
    username = data['username']
    room_code = data['room']
    print(f"{username} has left the game ({room_code}).")

    room = Rooms.objects(room_code=room_code).first()

    if username == room.admin or not room:  # The admin has left the lobby.
        print("Admin has left the game. Closing lobby...")
        emit("room-closed", room=room_code)
        close_room(room=room_code)
        if room:
            room.delete()
        return

    # Removes player's socket connection from room.
    leave_room(room=room_code)

    if username in room.players:
        room.players.remove(username)
        room.update(players=room.players)
        room.save()
        print(f"Players remaining: {room.players} ({rooms()})")

        print("Emitting user left...")
        emit("user-left", {"username": username}, room=room_code)


@socketio.on("start-game")
def start_game(data):
    auth_token = data.get("auth")

    # Validates user.
    user = Users.objects(auth_token=auth_token).first()

    # Collect game start data from post request.
    room_code = data.get("room_code")

    # Collects room data.
    room = Rooms.objects(room_code=room_code).first()
    if not room:
        emit("room-closed", room=room_code)
        close_room(room=room_code)
        return

    # Makes sure that the user sending the signal is the admin of the game.
    if room.admin != user.username:
        return

    print(f"{user.username} (admin) is starting the game {room_code}...")
    # Update room database data
    room.update(started=1)

    # Notify players that game was started. Signal will trigger JS to
    # reload page and render game html.
    emit("game-started", room=room_code)


# Authentication


@app.route("/login", methods=["POST"])
def login():
    email = request.form["email"]
    password = request.form["pass"]  # plain text password

    # Checks to see if the email has an account already.
    user = Users.objects(email=email).first()
    if not user:
        return render_template(
            "home.html",
            login_error="Email not found.",
        )

    # Password checker. Checks hashed (true) password to (entered) plain text password.
    correct_pw = bcrypt.checkpw(bytes(password.encode("utf-8")), user.hashed_password.encode("utf-8"))
    if not correct_pw:
        return render_template(
            "home.html",
            login_error="Incorrect password.",
        )

    # Create an auth browser cookie (random letters and numbers) as our authentication
    # token so the user doesn't have to log in every single time.
    auth_token = secrets.token_hex()
    response = redirect("/", 302)
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
        return render_template(
            "home.html",
            signup_error="Email or username already in use.",
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


@app.route("/logout", methods=["GET"])
def logout():
    # Remove auth token cookie
    response = redirect("/", 302)
    response.set_cookie("auth_token", "", expires=0)

    return response


@app.route("/test", methods=["GET"])
def test():
    return render_template("test.html")


if __name__ == '__main__':
    socketio.run(app, debug=True, port=5555, allow_unsafe_werkzeug=True)
