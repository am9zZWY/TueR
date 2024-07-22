import lzma
import pickle

import duckdb
import flask
from flask import Flask, jsonify, request, Response
from flask_cors import CORS, cross_origin

from preview import load_preview
from rank import rank
from summarize import get_summary_model

# Disable the default flask server banner
flask.cli.show_server_banner = lambda *args: None

PORT = 8000

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

dbcon: duckdb.DuckDBPyConnection = None


def start_server(debug=False, con: duckdb.DuckDBPyConnection = None):
    print("Starting server...")
    global dbcon
    dbcon = con
    app.run(port=PORT, debug=debug, use_reloader=debug)


@app.route("/")
def hello_world():
    return jsonify({"message": "Hello from the server!"})


@app.route("/search")
@cross_origin()
def search():
    query = request.args.get('query', '')

    result = {
        "query": query,
        "spellchecked_query": query,
        "results": [],
    }

    # Return test double results
    results = [
        {
            "id": page_id,
            "title": "Title " + str(page_id),
            "url": "https://www.uni-tuebingen.de",
            "description": "Description " + str(page_id),
            "summary": "Summary " + str(page_id),
            "score": 0.5
        } for page_id in range(100)]
    result["results"] = results

    # Rank documents according to query
    ranking = rank(query)
    result["results"] = ranking

    return jsonify(result)


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


@app.route("/summary/<int:doc_id>")
def summarize(doc_id):
    result = {
        "doc_id": doc_id,
        "url": "",
        "summary": ""
    }

    con = dbcon.cursor()
    blob, link = con.execute("""
        SELECT c.content, d.link
        FROM   documents AS d, crawled AS c
        WHERE  d.id = ?
           AND d.link = c.link
    """, [doc_id]).fetchall()[0]
    con.close()

    # Decompress the blob and get the summary
    soup = pickle.loads(lzma.decompress(blob))
    summarized_text = get_summary_model().summarize_soup(soup, max_words=20)

    result["summary"] = summarized_text
    result["url"] = link

    return jsonify(result)


@app.route("/site-map")
def site_map():
    links = []
    for rule in app.url_map.iter_rules():
        # Skip rules for static files unless you want to include them
        if "static" not in rule.endpoint:
            links.append({"endpoint": rule.endpoint, "methods": list(rule.methods)})
    return jsonify(links)


if __name__ == "__main__":
    dbcon = duckdb.connect("crawlies.db")
    start_server(con=dbcon)
    dbcon.close()
