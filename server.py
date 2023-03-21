#!/usr/bin/python3

import hashlib
import time
from flask import Flask, request, session

import serverImpl

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
    return serverImpl.root()

@app.route("/teams")
def teams():
    return serverImpl.teams()

@app.route("/update_teams")
def update_games():
    return serverImpl.update_games()

@app.route("/players")
def players():
    return serverImpl.players()

@app.route("/update_players")
def update_players():
    return serverImpl.update_players()

@app.route("/games")
def games():
    return serverImpl.games()

@app.route("/update_games")
def update_games():
    return serverImpl.update_games

@app.route("/show_games")
def show_games():
    return serverImpl.show_games()

@app.route("/clear")
def clear():
    return serverImpl.clear()


if __name__ == '__main__':
    app.run(debug=True, use_reloader=True)

