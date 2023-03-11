from flask import Flask, render_template, redirect, request

#  TODO: friend system
#  TODO: timed challenges
#  TODO: different difficulty daily challenges
#    #13005A         #00337C          #1C82AD           #03C988
# rgb(19, 0, 90) rgb(0, 51, 124) rgb(28, 130, 173) rgb(3, 201, 136)

app = Flask(__name__)

@app.route("/lobby", methods=["GET"])
def display_lobby():
    return render_template("lobby.html",
                           user=False
                           )


@app.route("/start-game", methods=["POST"])
def start_game():
    print("Hello")
    print(request.form)
    for form in request.form:
        print(form)
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
        user=False
    )


@app.route("/test", methods=["GET"])
def display_test():
    return render_template(
        "test.html",
        user=False
    )


if __name__ == '__main__':
    app.run(port=5555, debug=True)
