#!/usr/bin/python3

import hashlib
import time
from flask import Flask, request, session
import domain

app = Flask(__name__, template_folder='domain', static_folder='domain/static')
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
    return domain.root.get_main_page()

@app.route("/teams")
def teams():
    return domain.teams.get_list()

@app.route("/update_teams")
def update_teams():
    return domain.teams.update()

@app.route("/players")
def players():
    return domain.players.get_list()

@app.route("/update_players")
def update_players():
    return domain.players.update()

@app.route("/games")
def games():
    return domain.games.get_list()

@app.route("/update_games")
def update_games():
    return domain.games.update()

@app.route("/show_games")
def show_games():
    return domain.games.show()

@app.route("/clear")
def clear():
    return domain.root.clear()


if __name__ == '__main__':
    app.run(debug=True, use_reloader=True)

