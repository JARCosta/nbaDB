#!/usr/bin/python3

import hashlib
import time
from flask import Flask, request, session

import app2

app = Flask(__name__)
app.secret_key = 'your_secret_key'

@app.before_request
def before_request():
    if 'user_id' not in session:
        ip = request.remote_addr
        current_time = time.time()
        user_id = hashlib.md5(f'{ip}{current_time}'.encode()).hexdigest()
        session['user_id'] = user_id

@app.route("/")
def root():
    return app2.root()

@app.route("/teams")
def teams():
    return app2.teams()

@app.route("/update_teams")
def update_games():
    return app2.update_games()

@app.route("/players")
def players():
    return app2.players()

@app.route("/update_players")
def update_players():
    return app2.update_players()

@app.route("/games")
def games():
    return app2.games()

@app.route("/update_games")
def update_games():
    return app2.update_games

@app.route("/show_games")
def show_games():
    return app2.show_games()

@app.route("/clear")
def clear():
    return app2.clear()


if __name__ == '__main__':
    app.run(debug=True, use_reloader=True)

