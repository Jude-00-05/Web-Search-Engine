from flask import Flask, request, jsonify
from search_engine import search

app = Flask(__name__)

@app.route("/search")
def search_api():

    query = request.args.get("q")

    results = search(query)

    return jsonify(results)

if __name__ == "__main__":
    app.run(port=5000)