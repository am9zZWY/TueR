from flask import Flask, jsonify, request

from rank import rank

app = Flask(__name__)


@app.route("/")
def hello_world():
    return jsonify({"message": "Hello from Engine!"})


@app.route("/search")
def search():
    query = request.args.get('query', '')

    # Rank documents according to query
    ranking = rank(query)

    return jsonify({"results": ranking})


@app.route("/site-map")
def site_map():
    links = []
    for rule in app.url_map.iter_rules():
        # Skip rules for static files unless you want to include them
        if "static" not in rule.endpoint:
            links.append({"endpoint": rule.endpoint, "methods": list(rule.methods)})
    return jsonify(links)


if __name__ == "__main__":
    app.run(debug=True)
