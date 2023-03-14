import random, string, os, pymysql
from dotenv import load_dotenv, find_dotenv
from flask import Flask, render_template, redirect, request
from flask_sqlalchemy import SQLAlchemy


if not os.getenv("PUBLIC_ACTIVATED"):
    assert load_dotenv(find_dotenv()), "Failed to load environment."

pymysql.install_as_MySQLdb()
db = SQLAlchemy()
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("CLEARDB_YELLOW_URL")
db.init_app(app)


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
        signup_error=None,
    )


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


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, unique=True, nullable=False)
    email = db.Column(db.String)
