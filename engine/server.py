from flask import Flask, jsonify, request

app = Flask(__name__)


@app.route("/")
def hello_world():
    return jsonify({"message": "Hello from Engine!"})


@app.route("/search")
def search():
    query = request.args.get('query', '')

    dummy_results = [
        {"title": "First search result", "url": "http://example.com/first", "score": 0.9,
         "summary": "This is the first search result"},
        {"title": "Second search result", "url": "http://example.com/second", "score": 0.8,
         "summary": "This is the second search result"},
        {"title": query, "url": "http://example.com/third",
         "score": 0.7, "summary": "This is the third search result"},
    ]
    return jsonify({"results": dummy_results})


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
