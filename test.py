from flask import Flask, session, request
import hashlib
import time

app = Flask(__name__)
app.secret_key = 'your_secret_key'

@app.before_request
def before_request():
    if 'user_id' not in session:
        ip = request.remote_addr
        current_time = time.time()
        user_id = hashlib.md5(f'{ip}{current_time}'.encode()).hexdigest()
        session['user_id'] = user_id

@app.route('/')
def index():
    return f'Your user ID is: {session["user_id"]}'

if __name__ == '__main__':
    app.run()
