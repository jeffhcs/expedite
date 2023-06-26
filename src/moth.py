import time
from flask import Flask, request
from gevent.pywsgi import WSGIServer
import redis
import json
import hashlib
from flask_cors import CORS, cross_origin
from f import format_state

r = redis.Redis(host='localhost', port=6379, db=0)

app = Flask(__name__)
cors = CORS(app)

@app.route('/get_state', methods=['GET'])
def get_state():
    store = r.get('current_state')
    if store:
        response = json.loads(store)
        # a, b, id = format_state(response)
        # return {
        #     "a": a,
        #     "b": b,
        #     "id": id
        # }
        return response
    return {}

@app.route('/respond_prompt', methods=['POST'])
def respond_prompt():
    data = request.get_json()
    prompt_id = data["id"]
    response = data["response"]

    r.set(prompt_id, response)
    return data

def get_response(prompt):
    prompt_id = get_prompt_id(prompt)
    while True:
        response = r.get(prompt_id)
        print(f"Waiting for user: {prompt_id}")
        if response:
            r.set(prompt_id, "")
            return response.decode('utf-8')
        time.sleep(1)

def get_prompt_id(input_string):
    hash_object = hashlib.sha256()
    hash_object.update(input_string.encode())
    hash_hex = hash_object.hexdigest()

    return hash_hex


def set_redis(state):
    r.set("current_state", json.dumps(state))

if __name__ == '__main__':
    http_server = WSGIServer(('0.0.0.0', 8080), app)
    http_server.serve_forever()