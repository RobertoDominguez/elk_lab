from flask import Flask, render_template, request, jsonify
import requests
import json

app = Flask(__name__)

ELASTIC_URL = "http://localhost:9200"
INDEX_NAME = "headhunter_reviews"


@app.route("/")
def home():
    return render_template("index.html")

@app.route("/advanced")
def advanced():
    return render_template("advanced.html")

@app.route("/search", methods=["GET"])
def search():
    query = request.args.get("q", "")
    city = request.args.get("city", "")
    min_rating = request.args.get("min_rating", 0, type=float)
    page = request.args.get("page", 1, type=int)
    size = request.args.get("size", 20, type=int)

    from_ = (page - 1) * size 

    must = []
    if query:
        must.append({
            "multi_match": {
                "query": query,
                "fields": ["positive", "negative", "position", "city"]
            }
        })
    if city:
        must.append({"match": {"city": city}})
    if min_rating > 0:
        must.append({
            "range": {"workplace_rating": {"gte": min_rating}}
        })

    body = {
        "query": {"bool": {"must": must}} if must else {"match_all": {}},
        "from": from_,
        "size": size
    }

    try:
        response = requests.post(
            f"{ELASTIC_URL}/{INDEX_NAME}/_search",
            json=body,
            headers={"Content-Type": "application/json"}
        )
        response.raise_for_status()
        data = response.json()
        hits = data.get("hits", {})
        results = [h["_source"] for h in hits.get("hits", [])]
        total = hits.get("total", {}).get("value", 0)

        return jsonify({
            "results": results,
            "total": total,
            "page": page,
            "size": size
        })
    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 500



@app.route("/search_advanced", methods=["POST"])
def search_advanced():
    try:
        query_body = request.form.get("query", "").strip()

        if not query_body:
            return jsonify({"error": "No query data"}), 400

        body = json.loads(query_body)

        response = requests.post(
            f"{ELASTIC_URL}/{INDEX_NAME}/_search",
            json=body,
            headers={"Content-Type": "application/json"}
        )

        response.raise_for_status()
        data = response.json()
        hits = [hit["_source"] for hit in data.get("hits", {}).get("hits", [])]

        return jsonify(hits)
    except json.JSONDecodeError:
        return jsonify({"error": "Not valid json"}), 400
    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
