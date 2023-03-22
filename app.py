import bcrypt
import random
import secrets
import smtplib
import string
import uuid
import pymysql
from datetime import datetime
from email.message import EmailMessage
from email.utils import formataddr
from flask import Flask, render_template, redirect, request
from flask_socketio import SocketIO, emit, join_room
from database import LeetArena

pymysql.install_as_MySQLdb()
app = Flask(__name__)
socketio = SocketIO(app)
socketio.init_app(app, cors_allowed_origins="*")

lobbies = {}

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

@app.route("/game/<lobby_id>", methods=["GET"])
def display_game(lobby_id):
    auth_token = request.cookies.get("auth_token")
    db = LeetArena()
    with db:
        user = db.get_entry("user", auth_token=auth_token)

    if not user or lobby_id not in lobbies:  # No user found or game not found
        return redirect("/")

    game = lobbies[lobby_id]

    return render_template(
        "lobby.html",
        user=user,
        game=game,
        admin=user.entry_id == game["admin"],
        lobby_id=lobby_id
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
    join_code_length = 7
    join_code = ''.join(random.choices(string.ascii_uppercase +
                                       string.digits, k=join_code_length))

    # Create game
    lobbies[join_code] = {
        "started": False,
        "game_mode": None,
        "difficulty": None,
        "language": None,
        "admin": user.entry_id,
        "players": [user.entry_id],
    }

    return redirect(f"/game/{join_code}")


# Game Events

@socketio.on("user-connection-lobby")
def user_connected(data):
    id_lobby = data["lobby_id"]
    id_user = data["user_id"]
    print(f"{id_user} has connected to the lobby: {id_lobby}")
    lobbies[id_lobby]["players"].append(id_user)
    print(lobbies[id_lobby])


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
