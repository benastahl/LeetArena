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
from database import LeetArena

pymysql.install_as_MySQLdb()
app = Flask(__name__)


def send_email(sender_name, recipient, subject, body):  #  TODO: UPDATE WITH NEW EMAIL
    em = EmailMessage()
    em["From"] = formataddr((sender_name, "athleats.wayland@gmail.com"))
    em["To"] = recipient
    em["Subject"] = subject
    em.set_content(body)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login("athleats.wayland@gmail.com", "")
        smtp.sendmail("athleats.wayland@gmail.com", recipient, em.as_string())


@app.route("/lobby/<lobby_id>", methods=["GET"])
def display_lobby():
    return render_template("lobby.html",
                           user=False
                           )


@app.route("/create-lobby", methods=["POST"])
def create_lobby():
    join_code_length = 7
    join_code = ''.join(random.choices(string.ascii_uppercase +
                                       string.digits, k=join_code_length))
    return redirect(f"/lobby/{join_code}")


@app.route("/start-game", methods=["POST"])
def start_game():
    return redirect("/lobby")


@app.route("/duel", methods=["GET"])
def display_duel():
    return render_template("duel.html",
                           user=False,
                           )


@app.route("/", methods=["GET"])
def display_home():
    return render_template(
        "home.html",
        user=False,
        login_error=None,
        signup_error=None
    )


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


@app.route("/test", methods=["GET"])
def display_test():
    return render_template(
        "test.html",
        user=False
    )


if __name__ == '__main__':
    app.run(port=5555, debug=True)

#  TODO: friend system
#  TODO: timed challenges
#  TODO: different difficulty daily challenges

