from flask import Flask, jsonify, request
from flask_cors import CORS, cross_origin

from rank import rank

PORT = 8000
DEBUG = True

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})


@app.route("/")
def hello_world():
    return jsonify({"message": "Hello from TüR!"})


@app.route("/search")
@cross_origin()
def search():
    query = request.args.get('query', '')

    # Rank documents according to query
    ranking = rank(query)
    return jsonify(ranking)


@app.route("/site-map")
def site_map():
    links = []
    for rule in app.url_map.iter_rules():
        # Skip rules for static files unless you want to include them
        if "static" not in rule.endpoint:
            links.append({"endpoint": rule.endpoint, "methods": list(rule.methods)})
    return jsonify(links)


def start_server():
    app.run(port=PORT, debug=DEBUG)


if __name__ == "__main__":
    start_server()
