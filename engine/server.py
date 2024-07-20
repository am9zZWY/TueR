import flask
from flask import Flask, jsonify, request, Response
from flask_cors import CORS, cross_origin

<<<<<<< HEAD
from rank import rank
=======
from custom_db import get_page_by_id
from preview import load_preview
from rank import rank
from summarize import get_summary_model

# Disable the default flask server banner
flask.cli.show_server_banner = lambda *args: None
>>>>>>> master

PORT = 8000

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})


def start_server(debug=False):
    print("Starting server...")
    app.run(port=PORT, debug=debug, use_reloader=debug)


@app.route("/")
def hello_world():
    return jsonify({"message": "Hello from TüR!"})


@app.route("/search")
@cross_origin()
def search():
    query = request.args.get('query', '')

    # Return dummy results
    """
    results = [
        {
            "id": page_id,
            "title": "Title " + str(page_id),
            "url": "https://www.uni-tuebingen.de",
            "description": "Description " + str(page_id),
            "summary": "Summary " + str(page_id),
            "score": 0.5
        } for page_id in range(100)]
    return jsonify(results)
    """

    # Rank documents according to query
    ranking = rank(query)
    return jsonify(ranking)


@app.route("/preview")
async def preview():
    """
    Get a preview of the page by requesting the URL and returning the full HTML content
    including CSS and JavaScript
    Returns:
        A Response containing the full HTML content with inlined CSS and JavaScript
    """

    url = request.args.get('url', '')
    if not url:
        return Response("No URL provided", status=400)

    soup = await load_preview(url)
    return Response(str(soup), mimetype='text/html')


@app.route("/summarize/<int:page_id>")
def summarize(page_id):
    # Get the document by ID
    doc = get_page_by_id(page_id)
    if doc.empty:
        return Response("Document not found", status=404)

    # Get the text from the document
    text = doc['text'].values[0]
    summarized_text = get_summary_model().summarize(text)
    return jsonify({"summary": summarized_text})


@app.route("/site-map")
def site_map():
    links = []
    for rule in app.url_map.iter_rules():
        # Skip rules for static files unless you want to include them
        if "static" not in rule.endpoint:
            links.append({"endpoint": rule.endpoint, "methods": list(rule.methods)})
    return jsonify(links)


if __name__ == "__main__":
    start_server()
